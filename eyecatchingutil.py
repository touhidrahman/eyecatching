import subprocess
import os
import sys
import shutil
import imagehash
import click
from PIL import Image
from urllib.parse import urlparse


class MetaImage:

    def __init__(self, imagename, path = os.getcwd()):
        self.imagename = imagename
        self.prefix = self.get_prefix()
        self.path = path
        self.image = Image.open(imagename)

        self.size = self.image.size
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.ext = self.imagename.split(".")[1]

        namebits = self.imagename.split("_") # A_0_0_100_100_.png
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
        return (
            self.left, self.top,
            self.right, self.bottom
        )

    def left_half(self):
        return (
            self.left, self.top,
            int(self.width/2), self.height
        )

    def right_half(self):
        return (
            int(self.width/2), self.top,
            self.width, self.height
        )

    def top_half(self):
        return (
            self.left, self.top,
            self.width, int(self.height/2)
        )

    def bottom_half(self):
        return (
            self.left, int(self.height/2), 
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

    def format_name(self, coords = None):
        if (coords != None):
            (t, l, b, r) = coords
        else:
            (t, l, b, r) = (self.top, self.left, self.bottom, self.right)

        return "{0}_{1}_{2}_{3}_{4}_.{5}".format(
            self.prefix, t, l, b, r, self.ext
        )

    def save(self):
        self.image.save(self.format_name())

    def delete(self):
        del self.image
        os.remove(self.imagename)

    def crop(self, coordinates):
        img = self.image.crop(coordinates)
        filename = self.format_name(coordinates)
        img.save(filename)

    def save_top_half(self):
        self.crop(self.top_half())

    def save_bottom_half(self):
        self.crop(self.bottom_half())

    def save_left_half(self):
        self.crop(self.left_half())

    def save_right_half(self):
        self.crop(self.right_half())

    def save_first_half(self):
        self.crop(self.first_half())

    def save_second_half(self):
        self.crop(self.second_half())





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
        print(switcher[algorithm]())
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