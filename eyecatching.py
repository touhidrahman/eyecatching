import subprocess
import os
import sys
import shutil
import imagehash
import click
import time
from PIL import Image
from urllib.parse import urlparse
from controller import Controller
from eyecatchingutil import MetaImage
from eyecatchingutil import FirefoxScreenshot
from eyecatchingutil import ChromeScreenshot

pass_controller = click.make_pass_decorator(Controller, ensure = True)

@click.group()
@pass_controller
def cli(controller):
    """
    Tests the frontend of a website/webapp by comparing screenshots
    captured from different browsers (at present Chrome and Firefox).

        $ eyecatching linear <URL> [--option value]\n
        $ eyecatching recursive <URL> [--option value]

    For example:

        $ eyecatching linear http://example.com

    """
    pass


##########################################################################
#                            LINEAR METHOD                               #
##########################################################################
@cli.command()
@click.argument('url')
@click.option('--block-size',
            default=10,
            help="Tile block size, px. \n(Default: 20)")
@click.option('--algorithm',
            default="ahash",
            help="Perceptual hashing algorithm to be used. \n(Default: ahash) \nAvailable: ahash, phash, dhash, whash")
@click.option('--ref-browser',
            default="chrome",
            help="Reference browser \n(Default: chrome) \nAvailable: chrome, firefox")
@click.option('--output-id',
            default="_",
            help="An identifieable name to be added in the output file.")
@click.option('--width',
            default=1280,
            help="Viewport width, px. \n(Default: 1280)")
@click.option('--threshold',
            default=10,
            help="Hamming distance or threshold to consider a block dissimilar. \n(Default: 10) \tAvailable: 0 - 63")
@pass_controller
def linear(
    controller,
    url,
    block_size,
    algorithm,
    ref_browser,
    output_id,
    width,
    threshold
    ):
    """
    Test two screenshots using block comparison
    """

    validate_url(url)
    validate_width(width)
    validate_block_size(block_size, width)
    validate_threshold(threshold)

    print('Eyecatching is working....')

    controller.algorithm = algorithm
    controller.width = width
    controller.url = url
    controller.block_size = block_size
    controller.output_id = output_id
    controller.threshold = threshold

    if ref_browser == "chrome":
        controller.ref_screenshot = ChromeScreenshot()
        controller.com_screenshot = FirefoxScreenshot()
    if ref_browser == "firefox":
        controller.ref_screenshot = FirefoxScreenshot()
        controller.com_screenshot = ChromeScreenshot()

    # get screenshots
    controller.get_screenshot(url)
    # start compare process
    output = controller.linear(
        controller.ref_screenshot.imagename,
        controller.com_screenshot.imagename,
    )

    print("Eyecathing process completed.")
    output.show()

##########################################################################
#                         RECURSIVE METHOD                               #
##########################################################################
@cli.command()
@click.argument('url')
@click.option('--threshold',
            default=10,
            help="Hamming distance or threshold to consider a block dissimilar. \n(Default: 10) \tAvailable: 0 - 63")
@click.option('--algorithm',
            default="ahash",
            help="Perceptual hashing algorithm to be used. \n(Default: ahash) \nAvailable: ahash, phash, dhash, whash")
@click.option('--ref-browser',
            default="chrome",
            help="Reference browser \n(Default: chrome) \nAvailable: chrome, firefox")
@click.option('--output-id',
            default="_",
            help="An identifieable name to be added in the output file.")
@click.option('--width',
            default=1280,
            help="Viewport width, px. \n(Default: 1280)")
@click.option('--block-size',
            default=8,
            help="Smallest block size to reach recursively, px. \nLower value means more accurate but more time consuming. Min: 8\n(Default: 8)")
@pass_controller
def recursive(
    controller,
    url,
    algorithm,
    ref_browser,
    output_id,
    threshold,
    block_size,
    width
    ):
    """
    Test two screenshots using recursive approach
    """

    validate_url(url)
    validate_width(width)
    validate_block_size(block_size, width)
    validate_threshold(threshold)

    print('Eyecatching is working....')

    controller.algorithm = algorithm
    controller.width = width
    controller.url = url
    controller.output_id = output_id
    controller.threshold = threshold
    controller.block_size = block_size

    if ref_browser == "chrome":
        controller.ref_screenshot = ChromeScreenshot()
        controller.com_screenshot = FirefoxScreenshot()
    if ref_browser == "firefox":
        controller.ref_screenshot = FirefoxScreenshot()
        controller.com_screenshot = ChromeScreenshot()

    # get screenshots
    controller.get_screenshot(url)
    output = controller.recursive(
        controller.ref_screenshot.imagename,
        controller.com_screenshot.imagename,
    )

    output.show()

    print("Eyecathing process completed.")



##########################################################################
#                          GET SCREENSHOT                                #
##########################################################################
@cli.command()
@click.argument('url')
@click.option('--browser',
            default="chrome, firefox",
            help="Browser to be used. \n(Default: chrome, firefox)")
@click.option('--width',
            default=1280,
            help="Viewport width, px. \n(Default: 1280)")
def screenshot(
    url,
    width,
    browser = "chrome, firefox",
    ):
    """
    Get screenshot of the given webpage URL
    """
    validate_url(url)
    validate_width(width)

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

    if has_firefox:
        ff = FirefoxScreenshot()
        ff.width = width
        ff.take_shot(url)
    
    if has_chrome:
        ch = ChromeScreenshot()
        ch.width = width
        ch.take_shot(url)

##########################################################################
#                           MANUAL COMPARE                               #
##########################################################################
@cli.command()
@click.argument('method')
@click.argument('image1')
@click.argument('image2')
@click.option('--block-size',
            default=10,
            help="Tile block size, px. \n(Default: 10)")
@click.option('--algorithm',
            default="ahash",
            help="Perceptual hashing algorithm to be used. \n(Default: ahash) \nAvailable: ahash, phash, dhash, whash")
@click.option('--output-id',
            default="_",
            help="An identifieable name to be added in the output file.")
@click.option('--threshold',
            default=10,
            help="Hamming distance or threshold to consider a block dissimilar. \n(Default: 10) \tAvailable: 0 - 63")
@pass_controller
def compare(
    controller,
    method,
    image1,
    image2,
    block_size,
    algorithm,
    output_id,
    threshold
    ):
    """
    Test two images with given method
    """
    validate_threshold(threshold)
    validate_block_size(block_size, Image.open(image1).width)
    
    print('Eyecatching is working....')

    controller.algorithm = algorithm
    controller.output_id = output_id
    controller.threshold = threshold
    controller.block_size = block_size

    # start compare process
    if method == "linear":
        output = controller.linear(image1, image2)
    if method == "recursive":
        output = controller.recursive(image1, image2)
        
    output.show()

    print("Eyecathing process completed.")

##########################################################################
#                             SHIFT DETECT                               #
##########################################################################
@cli.command()
@click.argument("image1")
@click.argument("image2")
@click.option('--output-id',
            default="_",
            help="An identifieable name to be added in the output file.")
@pass_controller
def shift(controller, image1, image2, output_id):
    """
    Detect shift of objects between two images
    """
    controller.output_id = output_id
    output = controller.detect_shift(image1, image2)
    output.show()

##########################################################################
#                         NORMALIZE IMAGES                               #
##########################################################################
@cli.command()
@click.argument("image1")
@click.argument("image2")
@pass_controller
def normalize(controller, image1, image2):
    """
    Make 2 images equal height by adding white background to the smaller image
    """
    controller.normalize_images(image1, image2)

##########################################################################
#                              FIRST RUN                                 #
##########################################################################
@cli.command()
def firstrun():
    """
    Install required dependencies of eyecatching
    """
    subprocess.call([
        "npm", "install"
    ])

##########################################################################
#                              RESET COMMAND                             #
##########################################################################
@cli.command()
def reset():
    """
    Remove all input and output files
    """
    for f in os.listdir("."):
        if (f.endswith(".jpg")
        or f.endswith(".jpeg")
        or f.endswith(".png")
        or f.endswith(".avi")):
            os.remove(f)
            folder = f.split(".")[0]
            if os.path.exists(folder):
                shutil.rmtree(folder)
    print('All input/output images and directories removed.')


def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme and result.netloc and result.path
    except:
        return False


def validate_url(url):
    if url is None:
        print("Argument <URL> missing! Please input a valid URL.")
        exit()

    if is_valid_url(url) == False:
        print("Invalid URL! Please input a valid URL.")
        exit()

def validate_width(width):
    w = int(width) if type(width) is str else width
        
    if w < 1:
        print("Error: \tWidth is too small! Please use a value between 0 - 3000.")
    elif w > 3000:
        print("Error: \tWidth is too big! Please use a value between 0 - 3000.")
    else:
        return

    print("Error:\tExiting...")
    exit()

def validate_threshold(threshold):
    t = int(threshold) if type(threshold) is str else threshold

    if t < 1:
        print("Error: \tThreshold is too small! Please use a value between 0 - 63")
    elif t > 3000:
        print("Error: \tThreshold is too big! Please use a value between 0 - 63")
    else:
        return

    print("Error:\tExiting...")
    exit()

def validate_block_size(value, width):
    v = int(value) if type(value) is str else value

    if v < 1:
        print("Error: \tBlock size is too small! Please use a value between 8 - {0}".format(width))
    elif v > 3000:
        print("Error: \tBlock size is too big! Please use a value between 8 - {0}".format(width))
    else:
        return

    print("Error:\tExiting...")
    exit()
