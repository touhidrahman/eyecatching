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
    output_id = "_"
    block_size = 20
    width = 1280
    threshold = 8
    algorithm = "ahash"
    ref_image = None
    com_image = None
    url = None

    def __init__(self):
        self.image_chrome = ChromeScreenshot()
        self.image_firefox = FirefoxScreenshot()

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

    def compare_linear(self, ref_imagename, com_imagename, block_size, algorithm, threshold):
        ref_image = MetaImage(ref_imagename)
        com_image = MetaImage(com_imagename)
        counter = 0
        counter_problem = 0
        total_diff = 0
        edge = int(block_size)

        for x in range(0, com_image.width, edge):
            for y in range(0, com_image.height, edge):
                coords = (x, y, x + edge, y + edge)
                ref_tile = ref_image.image.crop(coords)
                com_tile = com_image.image.crop(coords)
                # compare with ref tile
                hash_diff =  self.get_hash_diff(ref_tile, com_tile, algorithm)
                hash_diff_percent = 100 * hash_diff / 64
                # get an opacity value between 0 - 1
                opacity = hash_diff_percent / 100

                if hash_diff >= threshold:
                    img_bottom = ref_tile.convert("RGB")
                    img_top = Image.new("RGB", img_bottom.size, "salmon")
                    blended = Image.blend(img_bottom, img_top, opacity)
                    ref_image.image.paste(blended, coords)
                    counter_problem += 1

                del ref_tile, com_tile
                total_diff += hash_diff_percent
                counter += 1

        print("Done: \tTotal blocks compared: {0}.".format(counter))
        print("Done: \tNumber of blocks with dissimilarity: {0}".format(counter_problem))
        print("Done: \tAverage dissimilarity {0:.2f}%.".format(round(total_diff / counter, 2)))
        # ref_image.image.show()
        return ref_image.image

    def blend_image_recursive(self, orig_image, patch_coords, diff):
        (x1, y1, x2, y2) = patch_coords
        # Crop the image with given co-ordinates
        img_slice = orig_image.crop( (x1, y1, x2, y2) )
        opacity = diff / 100 + 0.3  # thus it will be 0.3>opacity<0.93
        img_bottom = img_slice.convert("RGB")
        img_top = Image.new("RGB", img_slice.size, "salmon")
        blended_img = Image.blend(img_bottom, img_top, opacity)
        return blended_img

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
        hash1 = switcher[algorithm](image1)
        hash2 = switcher[algorithm](image2)
        return abs(hash1 - hash2)

    def get_screenshot(self, url):
        self.image_firefox.take_shot(url)
        self.image_chrome.take_shot_puppeteer(url)

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
        print("Working:\tMaking both image size equal (as larger image)")

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