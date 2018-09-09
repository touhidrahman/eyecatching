import subprocess
import os
import sys
import shutil
import imagehash
from PIL import Image
from urllib.parse import urlparse

class MetaImage:

    def __init__(self, imagename):
        self.imagename = imagename
        self.prefix = imagename.split(".")[0].split("_")[0]
        self.image = Image.open(self.imagename)
        self.size = self.image.size
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.name = self.imagename.split(".")[0]
        self.ext = self.imagename.split(".")[1]
        l, t, r, b = self.image.getbbox()
        self.coordinates = Coordinates(l, t, r, b)

    def get_coordinates(self):
        return self.coordinates.as_tuple()

    def get_cropped(self, coordinates):
        if isinstance(coordinates, Coordinates):
            coords = coordinates.as_tuple()
        else:
            coords = coordinates
        return self.image.crop(coords)

    def left_half(self):
        return self.image.crop(self.coordinates.left_half())

    def right_half(self):
        return self.image.crop(self.coordinates.right_half())

    def top_half(self):
        return self.image.crop(self.coordinates.top_half())

    def bottom_half(self):
        return self.image.crop(self.coordinates.bottom_half())

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

    def save(self, name = None):
        if name is None:
            self.image.save(self.imagename)
        else:
            self.image.save(name)



class Coordinates:
    def __init__(self, l, t, r, b):
        self.x1 = l
        self.y1 = t
        self.x2 = r
        self.y2 = b

        self.width = abs(self.x1 - self.x2)
        self.height = abs(self.y1 - self.y2)
        mid_x = int(self.width / 2)
        mid_y = int(self.height / 2)
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



class ImageComparator:

    def __init__(self, image1: Image.Image, image2: Image.Image):
        self.image1 = image1
        self.image2 = image2

    def is_similar(self, algorithm = "ahash"):
        switcher = {
            'ahash': self.is_similar_a_hash,
            'phash': self.is_similar_p_hash,
            'dhash': self.is_similar_d_hash,
            'whash': self.is_similar_w_hash,
        }
        return switcher[algorithm]()

    def hamming_diff(self, algorithm = "ahash"):
        switcher = {
            'ahash': self.hamming_diff_a_hash,
            'phash': self.hamming_diff_p_hash,
            'dhash': self.hamming_diff_d_hash,
            'whash': self.hamming_diff_w_hash
        }
        return switcher[algorithm]()

    def hash_diff(self, algorithm = "ahash"):
        return self.hamming_diff(algorithm)

    def hash_diff_percent(self, algorithm = "ahash"):
        return 100 * self.hamming_diff(algorithm) / 64

    def is_similar_by_color(self):
        # take a random pixel
        color1 = self.image1.getpixel((2,3))
        color2 = self.image2.getpixel((2,3))
        return color1 == color2

    def is_similar_a_hash(self):
        return imagehash.average_hash(self.image1) == imagehash.average_hash(self.image2)

    def is_similar_p_hash(self):
        return imagehash.phash(self.image1) == imagehash.phash(self.image2)

    def is_similar_d_hash(self):
        return imagehash.dhash(self.image1) == imagehash.dhash(self.image2)

    def is_similar_w_hash(self):
        return imagehash.whash(self.image1) == imagehash.whash(self.image2)

    def hamming_diff_a_hash(self):
        return abs(imagehash.average_hash(self.image1) - imagehash.average_hash(self.image2))

    def hamming_diff_p_hash(self):
        return abs(imagehash.phash(self.image1) - imagehash.phash(self.image2))

    def hamming_diff_d_hash(self):
        return abs(imagehash.dhash(self.image1) - imagehash.dhash(self.image2))

    def hamming_diff_w_hash(self):
        return abs(imagehash.whash(self.image1) - imagehash.whash(self.image2))





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
        # add 10 px for scrollbar
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

    def take_shot_commandline(self, url, height):
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

    def take_shot(self, url):
        """
        Take screenshot using Puppeteer
        """
        print("Info: \tGetting screenshot from Chrome browser")
        # set width to class
        subprocess.call(["node",
                        "puppeteer.js",
                        url,
                        str(self.width)])
        os.rename("screenshot.png", self.imagename)
        self.height = Image.open(self.imagename).size[1]
        print("Info: \tSaved screenshot from Chrome with name {0}".format(self.imagename))
        print("Info: \tInitial image size: {0} x {1}".format(self.width, self.height))        


