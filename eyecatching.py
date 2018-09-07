import subprocess
import os
import sys
import shutil
import imagehash
import click
from PIL import Image
from urllib.parse import urlparse
from eyecatchingutil import Container
from eyecatchingutil import MetaImage
from eyecatchingutil import MetaImage3
from eyecatchingutil import BrowserScreenshot
from eyecatchingutil import FirefoxScreenshot
from eyecatchingutil import ChromeScreenshot

pass_container = click.make_pass_decorator(Container, ensure = True)

@click.group()
@pass_container
def cli(container):
    """
    Tests the frontend of a website/webapp by comparing screenshots
    captured from different browsers (at present Chrome and Firefox).

        $ eyecatching linear <URL> [--option value]\n
        $ eyecatching recursive <URL> [--option value]

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
@pass_container
def recursive(container):
    class RecursiveController:
        def __init__(self, ref, com, algorithm):
            self.img_a = MetaImage3(Image.open(ref), "A")
            self.img_b = MetaImage3(Image.open(com), "B")
            self.count = 0
            self.algorithm = algorithm
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

        # compare method
        # Compares two image portions with given co-ordinates
        def compare(self, x1, y1, x2, y2):
            # At first crop the image portions
            a1_img = self.img_a.img.crop( (x1, y1, x2, y2) )
            b1_img = self.img_b.img.crop( (x1, y1, x2, y2) )

            hash_a =  self.switcher[self.algorithm](a1_img)
            hash_b =  self.switcher[self.algorithm](b1_img)
            diff =  hash_b-hash_a

            if diff == 0:
                # Two images are similar by hash
                # Now check their pixel's color
                color1 = a1_img.getpixel((2,3))
                color2 = b1_img.getpixel((2,3))
                if color1 == color2:
                    # Two imeages color is also same
                    return
                else:
                    # Pixel's color is not same
                    # Images are similar by hash, but not similar by color
                    # So, Save
                    blend_img = self.img_a.blendImage(x1, y1, x2, y2, diff)
                    # Blending the second image part
                    self.img_a.reconstruction(blend_img, x1, y1)
                    # Increase dissimilar portion count
                    self.count = self.count+1      
                    return

            else: 
                self.divide(x1, y1, x2, y2, diff)
                return

        # divide method
        # Take image co-ordinates as parameter
        def divide(self, x1, y1, x2, y2, diff):   
            # First, find out width and height of image
            width = x2-x1
            height = y2-y1

            # return and save if image is less than 8px
            if width<=8 or height<=8:  
                # print(diff)
                blend_img = self.img_a.blendImage(x1, y1, x2, y2, diff)
                # Blending the second image part
                self.img_a.reconstruction(blend_img, x1, y1)
                # Increase dissimilar portion count
                self.count = self.count+1      
                return
            # Divide the image with larger side
            elif width>=height:
                # int() is used just to convert 1.0 to 1
                portion = int(width/2) if (width%2)==0 else int((width)/2)+1
                # Calculate co-ordinates of two image portion
                co_or_1 = [x1, y1, x1+portion, y2]
                co_or_2 = [x1+portion+1, y1, x2, y2]
            else: 
                # int() is used just to convert 1.0 to 1
                portion = int(height/2) if (height%2)==0 else int((height)/2)+1
                # Calculate co-ordinates of two image portion
                co_or_1 = [x1, y1, x2, y1+portion]
                co_or_2 = [x1, y1+portion+1, x2, y2]

            # Calling compare method with image co-ordinates as arguments
            self.compare(co_or_1[0], co_or_1[1], co_or_1[2], co_or_1[3])
            self.compare(co_or_2[0], co_or_2[1], co_or_2[2], co_or_2[3])
            return

    controller = RecursiveController("chrome.png", "firefox.png", "phash")
    # Calling divide method of init Object with image co-ordinates
    controller.divide(0, 0, controller.img_a.width, controller.img_a.height, 0)
    controller.img_a.saveToReconstruct()
    controller.img_a.img.show()


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
        ht = ff.height
    
    if has_chrome:
        if ht:
            ch = ChromeScreenshot()
            ch.take_shot(url, ht)
        else:
            print("Error: \tNo value for height given for Chrome")
            exit()










@cli.command()
def reset():
    """
    - Remove old output files
    """
    for f in os.listdir("."):
        if f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".png"):
            os.remove(f)
            if os.path.exists(f):
                shutil.rmtree(f.split(".")[0])
            if f.startswith("output"):
                os.remove(f)
    print('All input/output images and directories removed.')


def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme and result.netloc and result.path
    except:
        return False





