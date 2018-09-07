import subprocess
import os
import sys
import shutil
import imagehash
import click
from PIL import Image
from urllib.parse import urlparse
from eyecatchingutil import MetaImage
from eyecatchingutil import BrowserScreenshot
from eyecatchingutil import FirefoxScreenshot
from eyecatchingutil import ChromeScreenshot



class Container:
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

        saving_name = "output" + "_" + compare_img
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
        # pass the height got from firefox
        self.image_chrome.take_shot(url, self.image_firefox.height)

pass_container = click.make_pass_decorator(Container, ensure = True)

@click.group()
@pass_container
def cli(container):
    """
    Tests the frontend of a website/webapp by comparing screenshots
    captured from different browsers (at present Chrome and Firefox).

        $ eyecatching linear <URL> [--option value]\n
        $ eyecatching recur <URL> [--option value]

    For example:

        $ eyecatching linear http://example.com

    """
    pass

@cli.command()
@click.argument('t', default="test")
@pass_container
def test(container, t):
    print(container.image_chrome.name)
    c = ChromeScreenshot()
    c.take_shot(t, 1280)


@cli.command()
@click.argument('url')
@click.option('--factor',
            default=20,
            help="Tile block size, px. \n(Default: 20)")
@click.option('--algorithm',
            default="ahash",
            help="Perceptual hashing algorithm to be used. \n(Default: ahash) \nAvailable: ahash, phash, dhash, whash")
@click.option('--ref-browser',
            default="chrome",
            help="Reference browser \n(Default: chrome) \nAvailable: chrome, firefox")
@click.option('--output', help="Name for the output file.")
@click.option('--width',
            default=1280,
            help="Viewport width, px. \n(Default: 1280)")
@pass_container
def linear(
    container,
    url,
    factor,
    algorithm,
    ref_browser,
    output,
    width,
    ):
    """
    - Test two screenshots using linear approach
    """

    if url == "":
        print("Argument <URL> missing! Please input a valid URL.")
        exit()

    if is_valid_url(url) == False:
        print("Invalid URL! Please input a valid URL.")
        exit()

    if factor < 8:
        print("Factor is too small! Please use a value above 8")
        exit()

    print('Eyecatching is working....')

    container.get_screenshot(url)

    # extend images to cut precisely
    print("Info: \tExtending images with white canvas to work with block size")
    container.image_chrome.extend_image(factor)
    container.image_firefox.extend_image(factor)

    # slice to tiles
    container.tile_image(container.image_chrome.imagename, factor)
    container.tile_image(container.image_firefox.imagename, factor)

    if ref_browser == "chrome":
        ref_img = container.image_chrome.imagename
        comp_img = container.image_firefox.imagename
    if ref_browser == "firefox":
        ref_img = container.image_firefox.imagename
        comp_img = container.image_chrome.imagename

    # join slices
    output = container.remake_image(ref_img, comp_img, algorithm)

    print("Eyecathing process completed.")
    output.show()


@cli.command()
def recursive():
    pass

def get_image_size(filename):
    """
    Get image size
    """
    img = Image.open(filename)
    size = img.size     # (wd, ht)
    del img
    return size

@cli.command()
@click.argument('url')
@click.option('--browser',
            default="chrome, firefox",
            help="Browser to be used. \n(Default: chrome, firefox)")
@click.option('--width',
            default=1280,
            help="Viewport width, px. \n(Default: 1280)")
@click.option('--height',
            help="Viewport height, px. Only required for Chrome")
def screenshot(
    url,
    width,
    height = 0,
    browser = "chrome, firefox",
    ):
    """
    - Get screenshot of the given webpage URL
    """
    if url is None:
        print("Argument <URL> missing! Please input a valid URL.")
        exit()
    
    if is_valid_url(url) == False:
        print("Invalid URL! Please input a valid URL.")
        exit()

    if browser != "":
        list = browser.split(",")
        browsers = []
        for it in list:
            browsers.append(it.strip().lower())
        has_firefox = "firefox" in browsers
        has_chrome = "chrome" in browsers
    else:
        print("Error: \tNo browser provided!")
        exit()

    ht = height

    if has_firefox:
        ff = FirefoxScreenshot()
        ff.take_shot(url)

    if ht is None or ht == 0:
        ht = ff.height
    
    if has_chrome:
        if ht:
            ch = ChromeScreenshot()
            ch.take_shot(url, ht)
        else:
            print("Error: \tNo value for height given for Chrome")
            exit()










@cli.command()
def reset(images = []):
    """
    - Remove old output files
    """
    for image in images:
        directory = image.split('.')[0]
        if (os.path.exists(directory)):
            shutil.rmtree(directory)
        os.remove(image)

    for filename in os.listdir("."):
        if filename.startswith("output"):
            os.remove(filename)

    print('All previous outputs removed.')


def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme and result.netloc and result.path
    except:
        return False





