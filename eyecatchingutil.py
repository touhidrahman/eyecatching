import subprocess
import os
import sys
import shutil
import imagehash
import click
from PIL import Image
from urllib.parse import urlparse

class MetaImage:

    def __init__(self, imagename):
        self.imagename = imagename
        namebits = self.imagename.split("_") # A_0_0_100_100_.png
        self.prefix = self.get_prefix()
        if len(namebits) == 1:
            self.path = os.getcwd()
            self.image = Image.open(imagename)
        else:
            self.path = "{0}/{1}".format(
                os.getcwd(), self.prefix
            )
            self.image = Image.open(self.path + '/' + self.imagename)

        self.size = self.image.size
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.ext = self.imagename.split(".")[1]
        if len(namebits) > 1:
            self.left       = int(namebits[1])
            self.top        = int(namebits[2])
            self.right      = int(namebits[3])
            self.bottom     = int(namebits[4])
        else:
            self.left = 0
            self.top = 0
            self.right = self.width
            self.bottom = self.height

    def get_prefix(self):
        raw_prefix = self.imagename.split(".")[0]
        prefix = raw_prefix.split("_")[0]
        return prefix
    
    def get_size(self):
        return self.image.size

    def get_coordinates(self):
        return (
            self.left,  self.top,
            self.right, self.bottom
        )

    def left_half(self):
        return (
            self.left,          self.top,
            int(self.width/2),  self.height
        )

    def right_half(self):
        return (
            int(self.width/2),  self.top,
            self.width,         self.height
        )

    def top_half(self):
        return (
            self.left,  self.top,
            self.width, int(self.height/2)
        )

    def bottom_half(self):
        return (
            self.left,  int(self.height/2), 
            self.width, self.height
        )

    def is_landscape(self):
        return self.width > self.height

    def is_potrait(self):
        return self.height > self.width

    def first_half(self):
        if self.is_landscape():
            return self.left_half()
        if self.is_potrait():
            return self.top_half()

    def second_half(self):
        if self.is_landscape():
            return self.right_half()
        if self.is_potrait():
            return self.bottom_half()

    def format_name(self):
        return "{0}_{1}_{2}_{3}_{4}_.{5}".format(
            self.prefix, 
            self.top, 
            self.left,
            self.bottom, 
            self.right, 
            self.ext
        )

    def format_name_with_dir(self):
        return "{0}/{1}".format(
            self.prefix, self.format_name()
        )

    def save(self):
        name_with_dir = "{0}/{1}".format(
            self.prefix, self.format_name()
        )
        self.image.save(name_with_dir)



class MetaImage2:
    def __init__(self, img, name):
        self.img = img
        self.name = name
        self.width, self.height = self.img.size

    # Takes image co-ordinates
    def blend_image(self, patch_coords, diff):
        (x1, y1, x2, y2) = patch_coords
        # Crop the image with given co-ordinates
        img_slice = self.img.crop( (x1, y1, x2, y2) )
        opacity = diff / 100 + 0.3  # thus it will be 0.3>opacity<0.93
        img_bottom = img_slice.convert("RGB")
        img_top = Image.new("RGB", img_slice.size, "salmon")
        blended_img = Image.blend(img_bottom, img_top, opacity)
        return blended_img
    
    # Pasting blended part to original image
    def paste_patch(self, paste_img, x1, y1):
        self.img.paste(paste_img, (x1, y1))

    # Saving the Reconstructed Image
    def save_output(self):
        self.img.save("output_recursive.png")


class ImageComparator:

    def __init__(self, image1: MetaImage, image2: MetaImage):
        self.image1 = image1
        self.image2 = image2

    def is_similar(self, algorithm = "ahash"):
        switcher = {
            'ahash': self.is_similar_a_hash,
            'phash': self.is_similar_p_hash,
            'dhash': self.is_similar_d_hash
        }
        return switcher[algorithm]()

    def hamming_diff(self, algorithm = "ahash"):
        switcher = {
            'ahash': self.hamming_diff_a_hash,
            'phash': self.hamming_diff_p_hash,
            'dhash': self.hamming_diff_d_hash
        }
        return switcher[algorithm]()

    def is_similar_a_hash(self):
        return self.image1.a_hash() == self.image2.a_hash()

    def is_similar_p_hash(self):
        return self.image1.p_hash() == self.image2.p_hash()

    def is_similar_d_hash(self):
        return self.image1.d_hash() == self.image2.d_hash()

    def hamming_diff_a_hash(self):
        return abs(self.image1.a_hash() - self.image2.a_hash())

    def hamming_diff_p_hash(self):
        return abs(self.image1.p_hash() - self.image2.p_hash())

    def hamming_diff_d_hash(self):
        return abs(self.image1.d_hash() - self.image2.d_hash())



class Coordinates:
    def __init__(self, l, t, r, b):
        self.x1 = l
        self.y1 = t
        self.x2 = r
        self.y2 = b
        self.width = abs(r - l)
        self.height = abs(b - t)
        mid_x = int(abs(t - b) / 2)
        mid_y = int(abs(l - r) / 2)
        self.mid_x = mid_x if (self.width % 2) == 0 else mid_x + 1
        self.mid_y = mid_y if (self.height % 2) == 0 else mid_y + 1

    def as_tuple(self):
        return (
            self.x1, self.y1,
            self.x2, self.y2
        )

    def add_to_right(self, pixels: int):
        return (
            self.x1,            self.y1,
            self.x2 + pixels,   self.y2
        )

    def add_to_bottom(self, pixels: int):
        return (
            self.x1,        self.y1,
            self.x2,        self.y2 + pixels 
        )

    def left_half(self):
        return (
            self.x1,                self.y1,
            self.x1 + self.mid_x,   self.y2
        )

    def right_half(self):
        return (
            self.x1 + self.mid_x,   self.y1,
            self.x2,                self.y2
        )

    def top_half(self):
        return (
            self.x1,        self.y1,
            self.x2,        self.y1 + self.mid_y
        )

    def bottom_half(self):
        return (
            self.x1,        self.y1 + self.mid_y,
            self.x2,        self.y2
        )

    def is_potrait(self):
        return abs(self.x2 - self.x1) <= abs(self.y2 - self.y1)

    def is_landscape(self):
        return abs(self.x2 - self.x1) >= abs(self.y2 - self.y1)

    def first_half(self):
        if self.is_landscape():
            return self.left_half()
        if self.is_potrait():
            return self.top_half()

    def second_half(self):
        if self.is_landscape():
            return self.right_half()
        if self.is_potrait():
            return self.bottom_half()





class BrowserScreenshot:

    width = 1280
    height = 0
    ext = '.png'

    def __init__(self, name):
        self.name = name
        self.imagename = name + self.ext

    def size(self):
        return (self.width, self.height)

    def remove_pixels_right(self, pixels:int):
        """
        Subtract given pixels from right side of the image 
        and replace the original file.
        Used to remove scrollbar pixels.
        """
        img = Image.open(self.imagename)
        w, h = img.size
        c = Coordinates(0, 0, w, h)
        newimg = img.crop(c.add_to_right(-pixels))
        img.close()
        os.remove(self.imagename)
        newimg.save(self.imagename)
        self.height = newimg.size[1]
        print("Info: \tRemoved {0} pixels from the right side of image {1}".format(pixels, self.imagename))

    def extend_image(self, factor: int):
        """
        Extend the image to be equally divisible by factor
        """
        img = Image.open(self.imagename)
        wd, ht = img.size
        img.close()
        ex_wd = factor - (wd % factor)
        ex_ht = factor - (ht % factor)

        if ex_ht != factor:
            ex_ht_str = "0x{0}".format(ex_ht)
            subprocess.call(["convert",
                            self.imagename,
                            "-gravity",
                            "south",
                            "-splice",
                            ex_ht_str,
                            self.imagename])
            print("Info: \tExtended {0} pixels at the bottom of image {1}".format(ex_ht, self.imagename))

        if ex_wd != factor:
            ex_wd_str = "{0}x0".format(ex_wd)
            subprocess.call(["convert",
                            self.imagename,
                            "-gravity",
                            "east",
                            "-splice",
                            ex_wd_str,
                            self.imagename])
            print("Info: \tExtended {0} pixels at the right of image {1}".format(ex_wd, self.imagename))


class FirefoxScreenshot(BrowserScreenshot):
    def __init__(self):
        super().__init__('firefox')

    def take_shot(self, url, height = 0):
        """
        Take screenshot using Firefox
        """
        print("Info: \tGetting screenshot from Firefox browser")
        window_size = "--window-size={0}".format(self.width + 10)
        subprocess.call(["firefox",
                        "-screenshot",
                        window_size,
                        url])
        # rename the output file
        os.rename("screenshot.png", self.imagename)
        # remove the scrolbar 
        self.remove_pixels_right(10)
        print("Info: \tSaved screenshot from Firefox with name {0}".format(self.imagename))
        print("Info: \tInitial image size: {0} x {1}".format(self.width, self.height))

class ChromeScreenshot(BrowserScreenshot):
    def __init__(self):
        super().__init__('chrome')

    def take_shot(self, url, height):
        """
        Take screenshot using Chrome
        """
        print("Info: \tGetting screenshot from Chrome browser")
        # chrome expects full viewport size
        self.height = height
        window_size = "--window-size={0},{1}".format(self.width, self.height)
        subprocess.call(["/opt/google/chrome/chrome",
                            "--headless",
                            "--hide-scrollbars",
                            window_size,
                            "--screenshot",
                            url])
        os.rename("screenshot.png", self.imagename)
        print("Info: \tSaved screenshot from Chrome with name {0}".format(self.imagename))
        print("Info: \tInitial image size: {0} x {1}".format(self.width, self.height))

    def take_shot_puppeteer(self, url):
        subprocess.call(["node",
                        "puppeteer.js",
                        url,
                        str(self.width)])
        os.rename("screenshot.png", self.imagename)
        self.height = Image.open(self.imagename).size[1]
        print("Info: \tSaved screenshot from Chrome with name {0}".format(self.imagename))
        print("Info: \tInitial image size: {0} x {1}".format(self.width, self.height))        



class Controller:

    outputname = "output.png"

    def __init__(self):
        self.image_chrome = ChromeScreenshot()
        self.image_firefox = FirefoxScreenshot()

    def tile_image(self, filename: str, edge: int):
        """
        Slice image into tiles with meaningful naming
        and move them into a directory named as original image
        """
        counter = 0
        img = MetaImage(filename)

        # remove directory if already exists
        if os.path.isdir(img.prefix):
            shutil.rmtree(img.prefix)

        os.mkdir(img.prefix)

        print("Info: \tSlicing image {0} into {1} x {1} pixel tiles".format(filename, edge))

        for x in range(0, img.width, edge):
            for y in range(0, img.height, edge):
                coords = (x, y, x + edge, y + edge)
                cropped_img = img.image.crop(coords)
                cropped_filename = "{0}/{0}_{1}_{2}_{3}_{4}_.{5}".format(
                    img.prefix,
                    x,
                    y,
                    x + edge,
                    y + edge,
                    img.ext
                )
                cropped_img.save(cropped_filename)
                counter = counter + 1
                del cropped_img

        print("Info: \tGenerated {0} images in directory {1}".format(counter, img.prefix))

    def mark_image(self, image: str, opacity: float, color:str = "salmon"):
        """
        Mask image with a color
        """
        img_bottom = Image.open(image).convert("RGB")
        img_top = Image.new("RGB", img_bottom.size, color)
        blended = Image.blend(img_bottom, img_top, opacity)
        blended.save(image)

        del img_bottom, img_top, blended

    def compare_tiles(self, ref_dir, compare_dir, algorithm):
        """
        Compares tiles and marks different tiles in comparing directory
        """
        path = os.getcwd() + "/" + compare_dir

        for tile in os.listdir(path):
            tile_ref_img = ref_dir + "/" + tile.replace(compare_dir, ref_dir)
            tile_com_img = compare_dir + "/" + tile
            hash_diff = self.get_hash_diff(tile_ref_img, tile_com_img, algorithm)

            opacity = 0
            if hash_diff >= 20 and hash_diff < 39:
                opacity = 0.3
            if hash_diff >= 40 and hash_diff < 49:
                opacity = 0.4
            if hash_diff >= 50 and hash_diff < 59:
                opacity = 0.5
            if hash_diff >= 60:
                opacity = 0.6

            # opacity = hash_diff / 100

            if opacity != 0:
                self.mark_image(tile_com_img, opacity)

    def remake_image(self, ref_img, compare_img, algorithm):
        print("Info: \tMarking visual differences from reference image...")
        r_img = MetaImage(ref_img)
        c_img = MetaImage(compare_img)
        canvas = Image.new("RGB", c_img.size, "white")
        dir_ref = r_img.prefix
        dir_com = c_img.prefix
        path = os.getcwd() + "/" + dir_com

        self.compare_tiles(dir_ref, dir_com, algorithm)

        for filename in os.listdir(path):
            slice = MetaImage(filename)
            canvas.paste(slice.image, slice.get_coordinates())
            del slice

        saving_name = "output_{0}_{1}_{2}.png".format(ref_img, compare_img, algorithm)
        canvas.save(saving_name)
        print("Info: \tResulted file saved as {0}".format(saving_name))
        return canvas

    def get_hash_diff(self, image1, image2, algorithm):
        """
        Get the hamming distance of two images
        """
        switcher = {
            'ahash': imagehash.average_hash,
            'phash': imagehash.phash,
            'dhash': imagehash.dhash,
            'whash': imagehash.whash,
        }
        img1 = Image.open(image1)
        img2 = Image.open(image2)
        hash1 = switcher[algorithm](img1)
        hash2 = switcher[algorithm](img2)
        del img1, img2
        return abs(hash1 - hash2)

    def get_screenshot(self, url):
        self.image_firefox.take_shot(url)
        self.image_chrome.take_shot_puppeteer(url)





class RecursiveController:

    threshold = 8
    algorithm = "ahash"

    def __init__(self):
        self.image_chrome = ChromeScreenshot()
        self.image_firefox = FirefoxScreenshot()
        self.ref_image = MetaImage2(Image.open(self.image_chrome.imagename), "A")
        self.com_image = MetaImage2(Image.open(self.image_firefox.imagename), "B")
        self.count = 0
        self.switcher = {
            'ahash': self.a_hash,
            'dhash': self.d_hash,
            'phash': self.p_hash,
            'whash': self.w_hash
        }

    # Methods for selecting given hashing algorithm by switcher
    def a_hash(self, img):
        return imagehash.average_hash(img)
    def d_hash(self, img):
        return imagehash.dhash(img)
    def p_hash(self, img):
        return imagehash.phash(img)
    def w_hash(self, img):
        return imagehash.whash(img)

    def compare(self, patch_coords):
        """
        Compares two image slice with given co-ordinates
        """
        x1, y1, x2, y2 = patch_coords

        ref_img_slice = self.ref_image.img.crop(patch_coords)
        com_img_slice = self.com_image.img.crop(patch_coords)

        hash_a =  self.switcher[self.algorithm](ref_img_slice)
        hash_b =  self.switcher[self.algorithm](com_img_slice)
        diff =  hash_b - hash_a

        if diff == 0:
            # Two images are similar by hash, check their pixel's color
            color1 = ref_img_slice.getpixel((2,3))
            color2 = com_img_slice.getpixel((2,3))
            # Images are similar by hash, but not similar by color
            if color1 != color2:
                blend_img = self.ref_image.blend_image(patch_coords, diff)
                self.ref_image.paste_patch(blend_img, x1, y1)
                # Increase dissimilar portion count
                self.count = self.count+1      
                return
        else:
            # go inside and compare again
            self.divide(patch_coords, diff)
            return

    # Take image co-ordinates as parameter
    def divide(self, initial_coords, diff):
        (x1, y1, x2, y2) = initial_coords
        coords = Coordinates(x1, y1, x2, y2)

        # return and save if image is less than 8px
        if coords.width <= self.threshold or coords.height <= self.threshold:  
            blend_img = self.ref_image.blend_image(initial_coords, diff)
            self.ref_image.paste_patch(blend_img, x1, y1)
            # Increase dissimilar portion count
            self.count = self.count+1      
            return
        # Divide the image with larger side
        else: 
            self.compare(coords.first_half())
            self.compare(coords.second_half())
            return
