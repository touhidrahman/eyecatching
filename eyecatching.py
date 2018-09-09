import subprocess
import os
import sys
import shutil
import imagehash
import click
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

@cli.command()
@click.argument('image1')
@click.argument('image2')
@click.argument('edge')
@pass_controller
def test(controller, image1, image2, edge):
    controller.compare_linear(image1, image2, edge, "ahash", 10)

##########################################################################
#                            LINEAR METHOD                               #
##########################################################################
@cli.command()
@click.argument('url')
@click.option('--block-size',
            default=20,
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
    - Test two screenshots using block comparison
    """

    validate_command_inputs(url)

    if block_size < 8:
        print("Factor is too small! Please use a value above 8")
        exit()

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
    controller.set_images()
    # normalize_images
    controller.normalize_images(controller.ref.imagename, controller.com.imagename)
    # start compare process
    output = controller.compare_linear()

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
    - Test two screenshots using recursive approach
    """

    validate_command_inputs(url)

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
    controller.set_images()
    # normalize_images
    controller.normalize_images(controller.ref.imagename, controller.com.imagename)
    # Start divide and compare with initial bounding box
    controller.divide_recursive(controller.ref.image.getbbox(), 0)

    controller.save_output(controller.ref.image, "recursive")

    print("Eyecathing process completed.")
    controller.ref.image.show()

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
    - Get screenshot of the given webpage URL
    """
    validate_command_inputs(url)

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
    - Test two images with given method
    """
    if block_size < 8:
        print("Factor is too small! Please use a value above 8")
        exit()

    print('Eyecatching is working....')

    controller.algorithm = algorithm
    controller.block_size = block_size
    controller.output_id = output_id
    controller.threshold = threshold

    # get screenshots
    controller.set_images(image1, image2)
    # normalize_images
    controller.normalize_images(controller.ref.imagename, controller.com.imagename)
    # start compare process
    if method == "linear":
        output = controller.compare_linear()
        output.show()
    if method == "recursive":
        coords = controller.ref.image.getbbox()
        controller.divide_recursive(coords, 0)
        controller.save_output(controller.ref.image, method)
        controller.ref.image.show()
        print("Done:\tNumber of blocks dissimilar: {0}".format(controller._rec_count))
        print("Done:\tAverage dissimilarity: {0:.2f}%".format(round(controller._rec_total_diff / controller._rec_count, 2)))

    print("Eyecathing process completed.")

##########################################################################
#                         NORMALIZE IMAGES                               #
##########################################################################
@cli.command()
@click.argument("image1")
@click.argument("image2")
@pass_controller
def normalize(controller, image1, image2):
    """
    - Make 2 images equal height by adding white background to the smaller image
    """
    controller.normalize_images(image1, image2)

##########################################################################
#                              FIRST RUN                                 #
##########################################################################
@cli.command()
def firstrun():
    """
    - Install required dependencies of eyecatching
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
    - Remove all input and output files
    """
    for f in os.listdir("."):
        if f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".png"):
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


def validate_command_inputs(url):
    if url is None:
        print("Argument <URL> missing! Please input a valid URL.")
        exit()

    if is_valid_url(url) == False:
        print("Invalid URL! Please input a valid URL.")
        exit()

