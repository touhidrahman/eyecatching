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
        return self.imagename.split(".")[0].split("_")[0]
    
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




class ImageComparator:

    def __init__(self, image1: MetaImage, image2: MetaImage):
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
            'dhash': self.hamming_diff_d_hash
        }
        return switcher[algorithm]()

    def is_similar_a_hash(self):
        return self.image1.a_hash() == self.image2.a_hash()

    def is_similar_p_hash(self):
        return self.image1.p_hash() == self.image2.p_hash()

    def is_similar_d_hash(self):
        return self.image1.d_hash() == self.image2.d_hash()

    def is_similar_w_hash(self):
        return self.image1.w_hash() == self.image2.w_hash()

    def hamming_diff_a_hash(self):
        return abs(self.image1.a_hash() - self.image2.a_hash())

    def hamming_diff_p_hash(self):
        return abs(self.image1.p_hash() - self.image2.p_hash())

    def hamming_diff_d_hash(self):
        return abs(self.image1.d_hash() - self.image2.d_hash())

    def hamming_diff_w_hash(self):
        return abs(self.image1.w_hash() - self.image2.w_hash())



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
        """
        Take screenshot using Puppeteer
        """
        print("Info: \tGetting screenshot from Chrome browser")
        subprocess.call(["node",
                        "puppeteer.js",
                        url,
                        str(self.width)])
        os.rename("screenshot.png", self.imagename)
        self.height = Image.open(self.imagename).size[1]
        print("Info: \tSaved screenshot from Chrome with name {0}".format(self.imagename))
        print("Info: \tInitial image size: {0} x {1}".format(self.width, self.height))        


