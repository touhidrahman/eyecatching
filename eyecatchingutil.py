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
            self.x1eft       = int(namebits[1])
            self.y1op        = int(namebits[2])
            self.x2ight      = int(namebits[3])
            self.y2ottom     = int(namebits[4])
        else:
            self.x1eft = 0
            self.y1op = 0
            self.x2ight = self.width
            self.y2ottom = self.height

    def get_prefix(self):
        raw_prefix = self.imagename.split(".")[0]
        prefix = raw_prefix.split("_")[0]
        return prefix
    
    def get_size(self):
        return self.image.size

    def get_coordinates(self):
        return (
            self.x1eft, self.y1op,
            self.x2ight, self.y2ottom
        )

    def left_half(self):
        return (
            self.x1eft, self.y1op,
            int(self.width/2), self.height
        )

    def right_half(self):
        return (
            int(self.width/2), self.y1op,
            self.width, self.height
        )

    def top_half(self):
        return (
            self.x1eft, self.y1op,
            self.width, int(self.height/2)
        )

    def bottom_half(self):
        return (
            self.x1eft, int(self.height/2), 
            self.width, self.height
        )

    def is_landscape(self):
        return self.width > self.height

    def is_potrait(self):
        return self.height > self.width

    def first_half(self):
        if self.is_landscape():
            return self.x1eft_half()
        if self.is_potrait():
            return self.y1op_half()

    def second_half(self):
        if self.is_landscape():
            return self.x2ight_half()
        if self.is_potrait():
            return self.y2ottom_half()

    def format_name(self):
        return "{0}_{1}_{2}_{3}_{4}_.{5}".format(
            self.prefix, 
            self.y1op, 
            self.x1eft,
            self.y2ottom, 
            self.x2ight, 
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

    LIMIT = 8

    def __init__(self, imagename, path = os.getcwd()):
        self.imagename = imagename
        self.prefix = self.get_prefix()
        self.path = path
        self.image = Image.open(imagename)

        self.size = self.image.size
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.ext = self.imagename.split(".")[1]

        self.actual_coords = Coordinates(0, 0, self.width, self.height)

        namebits = self.imagename.split("_") # A_0_0_100_100_.png
        # following coords are relative to original image
        if len(namebits) > 1:
            _l = int(namebits[1])
            _t = int(namebits[2])
            _r = int(namebits[3])
            _b = int(namebits[4])
            self.virtual_coords = Coordinates(_l, _t, _r, _b)
        else:
            self.virtual_coords = self.actual_coords

    def a_hash(self):
        return imagehash.average_hash(self.image)

    def p_hash(self):
        return imagehash.phash(self.image)

    def d_hash(self):
        return imagehash.dhash(self.image)

    def get_prefix(self):
        raw_prefix = self.imagename.split(".")[0]
        prefix = raw_prefix.split("_")[0]
        return prefix

    def coordinates(self):
        return self.actual_coords.as_tuple()

    def relative_coordinates(self):
        return self.virtual_coords.as_tuple()

    def is_landscape(self):
        return self.width > self.height

    def is_potrait(self):
        return self.height > self.width

    def format_name(self, coords = None):
        if (coords != None):
            (l, t, r, b) = coords
        else:
            (l, t, r, b) = self.virtual_coords.as_tuple()

        return "{0}_{1}_{2}_{3}_{4}_.{5}".format(
            self.prefix, l, t, r, b, self.ext
        )

    def save(self):
        self.image.save(self.format_name())

    def delete(self):
        del self.image
        os.remove(self.imagename)

    def crop(self, crop_coords, naming_coords):
        img = self.image.crop(crop_coords)
        filename = self.format_name(naming_coords)
        if os.path.isfile(filename):
            os.remove(filename)
        img.save(filename)

    def save_top_half(self):
        actual = self.actual_coords.top_half()
        virtual = self.virtual_coords.top_half()
        self.crop(actual, virtual)

    def save_bottom_half(self):
        actual = self.actual_coords.bottom_half()
        virtual = self.virtual_coords.bottom_half()
        self.crop(actual, virtual)

    def save_left_half(self):
        actual = self.actual_coords.left_half()
        virtual = self.virtual_coords.left_half()
        self.crop(actual, virtual)

    def save_right_half(self):
        actual = self.actual_coords.right_half()
        virtual = self.virtual_coords.right_half()
        self.crop(actual, virtual)

    def save_first_half(self):
        actual = self.actual_coords.first_half()
        virtual = self.virtual_coords.first_half()
        self.crop(actual, virtual)

    def save_second_half(self):
        actual = self.actual_coords.second_half()
        virtual = self.virtual_coords.second_half()
        self.crop(actual, virtual)

    def divide(self):
        bigger = self.height
        if self.width > self.height:
            bigger = self.width

        if bigger >= MetaImage2.LIMIT * 2:
            self.save_first_half()
            self.save_second_half()
            return (
                self.format_name(self.virtual_coords.first_half()),
                self.format_name(self.virtual_coords.second_half())
                )

        return (None, None)





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
        mid_x = int(abs(t - b) / 2)
        mid_y = int(abs(l - r) / 2)
        if mid_x % 2 == 0:
            self.mid_x = mid_x
        else:
            self.mid_x = mid_x + 1
        if mid_y % 2 == 0:
            self.mid_y = mid_y
        else:
            self.mid_y = mid_y + 1

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
            self.x1,    self.y1,
            self.mid_x, self.y2
        )

    def right_half(self):
        return (
            self.mid_x, self.y1,
            self.x2,     self.y2
        )

    def top_half(self):
        return (
            self.x1,     self.y1,
            self.x2,     self.mid_y
        )

    def bottom_half(self):
        return (
            self.x1,     self.mid_y,
            self.x2,     self.y2
        )

    # def distance_x(self, c: Coordinates):
    #     return abs(self.x1 - c.l)

    # def distance_y(self, c: Coordinates):
    #     return abs(self.y1 - c.t)

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
        newimg = img.crop(c.add_to_bottom(-pixels))
        img.close()
        newimg.save(self.imagename)
        self.height = newimg.size[0]
# TODO:
        print("Removed {0} pixels from the right side of image {1}".format(pixels, self.imagename))



class FirefoxScreenshot(BrowserScreenshot):
    def __init__(self):
        super().__init__('firefox')

    def take(self, url):
        """ Take screenshot using Firefox """
        window_size = "--window-size={0}".format(self.width + 10)
        subprocess.call(["firefox",
                        "-screenshot",
                        window_size,
                        url])
        # rename the output file
        os.rename("screenshot.png", self.imagename)
        # remove the scrolbar 
        self.remove_pixels_right(10)
        print("Saved screenshot from Firefox with name {0}".format(self.imagename))


class ChromeScreenshot(BrowserScreenshot):
    def __init__(self):
        super().__init__('chrome')

    def take(self, url, height):
        """ Take screenshot using Chrome """
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
        print("Saved screenshot from Chrome with name {0}".format(self.imagename))
