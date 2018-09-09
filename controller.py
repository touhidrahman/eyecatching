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
from eyecatchingutil import ImageComparator


class Controller:

    output_id = "_"
    block_size = 20
    width = 1280
    threshold = 8
    algorithm = "ahash"
    ref = None
    com = None
    ref_screenshot = None
    com_screenshot = None
    url = None

    def __init__(self):
        self.count = 0 # used for recursive operations
        self.paste_coords = []

    def compare_rec(self, coordinates, diff):
        l, t, r, b = coordinates
        coords = Coordinates(l, t, r, b)
        first = coords.first_half()
        second = coords.second_half()

        if self.count > 0 and diff == 0:
            return

        # initial step, divide first
        if self.count == 0:  
            self.compare_rec(first, diff)
            self.compare_rec(second, diff)
            self.count += 1
            return
        # else check if the patch is smaller than block size
        # and is different
        if diff > 0 and (coords.width <= self.block_size or coords.height <= self.block_size):
            self.paste_coords.append(coords.as_tuple())
            return

        # else go inside and compare
        ref_slice = self.ref.get_cropped(coords.as_tuple())
        com_slice = self.com.get_cropped(coords.as_tuple())

        ic = ImageComparator(ref_slice, com_slice)
        diff = ic.hamming_diff(self.algorithm)

        if diff > 0:
            self.compare_rec(first, diff)
            self.compare_rec(second, diff)
            self.count += 1
            return


    def divide_rec(self, coordinates):
        l, t, r, b = coordinates
        coords = Coordinates(l, t, r, b)
        
        if coords.width <= self.block_size or coords.height <= self.block_size:
            return False
        else:
            self.compare_rec(coords.first_half())
            self.compare_rec(coords.second_half())
            return True

    def compare_recursive(self, patch_coords):
        """
        Compares two image slice with given coordinates
        """
        x1, y1, x2, y2 = patch_coords
        ref_img_slice = self.ref.image.crop(patch_coords)
        com_img_slice = self.com.image.crop(patch_coords)

        ic = ImageComparator(ref_img_slice, com_img_slice)
        diff = ic.hamming_diff(self.algorithm)

        if diff <= self.threshold and ic.is_similar_by_color() == False:
            blended = self.blend_image_recursive(self.ref.image, patch_coords, diff) #TODO:
            self.ref.image.paste(blended, (x1, y1))
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
        if coords.width <= self.block_size or coords.height <= self.block_size:
            blended = self.blend_image_recursive(self.ref.image, initial_coords, diff)
            self.ref.image.paste(blended, (x1, y1))
            self.count += 1
            return
        # Divide the image with larger side
        else: 
            self.compare_recursive(coords.first_half())
            self.compare_recursive(coords.second_half())
            return

    def blend_image_recursive(self, image_obj, coords, diff):
        patch = image_obj.crop(coords)
        opacity = diff / 100 + 0.3 # TODO:
        img1 = patch.convert("RGB")
        img2 = Image.new("RGB", patch.size, "salmon")
        blended = Image.blend(img1, img2, opacity)
        return blended

    def save_output(self, image_obj:Image.Image, methodname:str):
        method = methodname[:3]
        output_name = "output_{0}_{1}_{2}_{3}_{4}.{5}".format(
            method,
            self.output_id,
            self.ref.name,
            self.com.name,
            self.algorithm,
            self.ref.ext
        )
        image_obj.save(output_name)
        print("Done: \tOutput saved as: {0}.".format(output_name))

    def compare_linear(self):
        counter = 0
        counter_problem = 0
        total_diff = 0
        edge = int(self.block_size)

        for x in range(0, self.com.image.width, edge):
            for y in range(0, self.com.image.height, edge):
                coords = (x, y, x + edge, y + edge)
                ref_tile = self.ref.get_cropped(coords)
                com_tile = self.com.get_cropped(coords)
                # compare with ref tile
                ic = ImageComparator(ref_tile, com_tile)
                hash_diff =  ic.hash_diff(self.algorithm)
                hash_diff_percent = ic.hash_diff_percent(self.algorithm)
                # get an opacity value between 0 - 1
                opacity = hash_diff_percent / 100

                if hash_diff >= self.threshold:
                    blended = self.blend_image(ref_tile, opacity)
                    self.ref.image.paste(blended, coords)
                    counter_problem += 1

                del ref_tile, com_tile
                total_diff += hash_diff_percent
                counter += 1

        self.save_output(self.ref.image, "linear")

        print("Done: \tTotal blocks compared: {0}.".format(counter))
        print("Done: \tNumber of blocks with dissimilarity: {0}".format(counter_problem))
        print("Done: \tAverage dissimilarity {0:.2f}%.".format(round(total_diff / counter, 2)))
        
        return self.ref.image

    def blend_image(self, image_obj, opacity, color = "salmon"):
        img1 = image_obj.convert("RGB")
        img2 = Image.new("RGB", img1.size, color)
        return Image.blend(img1, img2, opacity)

    def get_screenshot(self, url):
        self.ref_screenshot.width = self.width
        self.com_screenshot.width = self.width
        self.ref_screenshot.take_shot(url)
        self.com_screenshot.take_shot(url)

    def set_images(self, ref_imagename = None, com_imagename = None):
        if ref_imagename is None:
            self.ref = MetaImage(self.ref_screenshot.imagename)
        else:
            self.ref = MetaImage(ref_imagename)

        if com_imagename is None:
            self.com = MetaImage(self.com_screenshot.imagename)
        else:
            self.com = MetaImage(com_imagename)

    def normalize_images(self, image1, image2):
        """
        Make 2 images equal height by adding white background to the smaller image
        """
        img1 = MetaImage(image1)
        img2 = MetaImage(image2)

        if img1.size == img2.size:
            print("Info: \tImage sizes are already equal")
            return

        print("Info: \t{0} image size: {1}x{2}".format(image1, img1.width, img1.height))
        print("Info: \t{0} image size: {1}x{2}".format(image2, img2.width, img2.height))
        print("Work:\tMaking both image size equal (as larger image)")

        bigger_ht = img1.height if (img1.height >= img2.height) else img2.height
        bigger_wd = img1.width if (img1.width >= img2.width) else img2.width
        
        newimg = Image.new("RGB", (bigger_wd, bigger_ht), "white")
        # which one is smaller
        if img1.size == (bigger_wd, bigger_ht):
            newimg.paste(img2.image)
            newimg.save(image2)
        else:
            newimg.paste(img1.image)
            newimg.save(image1)

        print("Done: \t{0} and {1} both are now {2}x{3} pixels.".format(
            image1, image2, bigger_wd, bigger_ht
        ))