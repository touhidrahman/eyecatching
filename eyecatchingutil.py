import subprocess
import os
import sys
import shutil
import imagehash
import click
from PIL import Image
from urllib.parse import urlparse


class MetaImage:

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

        if bigger >= MetaImage.LIMIT * 2:
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
        self.l = l
        self.t = t
        self.r = r
        self.b = b
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
            self.l, self.t,
            self.r, self.b
        )

    def shift_horizontally(self, pixels: int):
        self.l += pixels
        self.r += pixels
        return (
            self.l, self.t,
            self.r, self.b
        )

    def shift_vertically(self, pixels: int):
        self.t += pixels
        self.b += pixels
        return (
            self.l, self.t,
            self.r, self.b 
        )

    def left_half(self):
        return (
            self.l,     self.t,
            self.mid_x, self.b
        )

    def right_half(self):
        return (
            self.mid_x, self.t,
            self.r,     self.b
        )

    def top_half(self):
        return (
            self.l,     self.t,
            self.r,     self.mid_y
        )

    def bottom_half(self):
        return (
            self.l,     self.mid_y,
            self.r,     self.b
        )

    # def distance_x(self, c: Coordinates):
    #     return abs(self.l - c.l)

    # def distance_y(self, c: Coordinates):
    #     return abs(self.t - c.t)

    def is_potrait(self):
        return abs(self.r - self.l) <= abs(self.b - self.t)

    def is_landscape(self):
        return abs(self.r - self.l) >= abs(self.b - self.t)

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