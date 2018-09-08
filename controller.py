import subprocess
import os
import sys
import shutil
import imagehash
from PIL import Image
from urllib.parse import urlparse
from eyecatchingutil import MetaImage
from eyecatchingutil import FirefoxScreenshot
from eyecatchingutil import ChromeScreenshot
from eyecatchingutil import Coordinates


class Controller:

    outputname = "output.png"
    threshold = 8
    algorithm = "ahash"
    ref_image = None
    com_image = None

    def __init__(self):
        self.image_chrome = ChromeScreenshot()
        self.image_firefox = FirefoxScreenshot()

        
        self.count = 0


    def compare_recursive(self, patch_coords):
        """
        Compares two image slice with given coordinates
        """
        # Methods for selecting given hashing algorithm by switcher
        switcher = {
            'ahash': imagehash.average_hash,
            'phash': imagehash.phash,
            'dhash': imagehash.dhash,
            'whash': imagehash.whash,
        }

        x1, y1, x2, y2 = patch_coords

        ref_img_slice = self.ref_image.crop(patch_coords)
        com_img_slice = self.com_image.crop(patch_coords)

        hash_a =  switcher[self.algorithm](ref_img_slice)
        hash_b =  switcher[self.algorithm](com_img_slice)
        diff =  abs(hash_b - hash_a)

        if diff == 0:
            # Two images are similar by hash, check their pixel's color
            color1 = ref_img_slice.getpixel((2,3))
            color2 = com_img_slice.getpixel((2,3))
            # Images are similar by hash, but not similar by color
            if color1 != color2:
                blend_img = self.blend_image_recursive(self.ref_image, patch_coords, diff)
                self.ref_image.paste(blend_img, (x1, y1))
                # Increase dissimilar portion count
                self.count += 1      
                return
        else:
            # go inside and compare again
            self.divide_recursive(patch_coords, diff)
            return


    def divide_recursive(self, initial_coords, diff):
        (x1, y1, x2, y2) = initial_coords
        coords = Coordinates(x1, y1, x2, y2)

        # return and save if image is less than 8px
        if coords.width <= self.threshold or coords.height <= self.threshold:  
            blend_img = self.blend_image_recursive(self.ref_image, initial_coords, diff)
            self.ref_image.paste(blend_img, (x1, y1))
            self.count = self.count+1      
            return
        # Divide the image with larger side
        else: 
            self.compare_recursive(coords.first_half())
            self.compare_recursive(coords.second_half())
            return


    def save_output(self, image_obj, name):
        image_obj.save(name)

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


    def blend_image_recursive(self, orig_image, patch_coords, diff):
        (x1, y1, x2, y2) = patch_coords
        # Crop the image with given co-ordinates
        img_slice = orig_image.crop( (x1, y1, x2, y2) )
        opacity = diff / 100 + 0.3  # thus it will be 0.3>opacity<0.93
        img_bottom = img_slice.convert("RGB")
        img_top = Image.new("RGB", img_slice.size, "salmon")
        blended_img = Image.blend(img_bottom, img_top, opacity)
        return blended_img

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

        output_name = "output_linear_{0}_{1}_{2}.{3}".format(
            dir_ref,
            dir_com,
            algorithm,
            r_img.ext
            )
        canvas.save(output_name)
        print("Info: \tResulted file saved as {0}".format(output_name))
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

