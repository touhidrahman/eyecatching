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

    if ref_browser == "chrome":
        ref_image = controller.image_chrome
        com_image = controller.image_firefox
    if ref_browser == "firefox":
        ref_image = controller.image_firefox
        com_image = controller.image_chrome

    # get screenshots
    controller.get_screenshot(url)
    # normalize_images
    controller.normalize_images(ref_image.imagename, com_image.imagename)
    # start compare process
    output = controller.compare_linear(
        ref_image.imagename,
        com_image.imagename,
        block_size,
        algorithm,
        threshold
        )

    output_name = "output_lin_{0}_{1}_{2}_{3}.{4}".format(
        output_id,
        ref_image.name,
        com_image.name,
        algorithm,
        ref_image.ext
    )
    output.save(output_name)

    print("Eyecathing process completed.")
    output.show()


@cli.command()
@click.argument('url')
@click.option('--threshold',
            default=8,
            help="Edge of smallest block size, px. \nLower value means more accurate. Min: 8\n(Default: 8)")
@click.option('--algorithm',
            default="ahash",
            help="Perceptual hashing algorithm to be used. \n(Default: ahash) \nAvailable: ahash, phash, dhash, whash")
@click.option('--ref-browser',
            default="chrome",
            help="Reference browser \n(Default: chrome) \nAvailable: chrome, firefox")
@click.option('--output', help="Add an identifier to the output file.")
@click.option('--width',
            default=1280,
            help="Viewport width, px. \n(Default: 1280)")
@pass_controller
def recursive(
    controller,
    url,
    algorithm,
    ref_browser,
    output,
    threshold,
    width
    ):
    """
    - Test two screenshots using recursive approach
    """

    validate_command_inputs(url)

    print('Eyecatching is working....')

    controller.get_screenshot(url)

    controller.algorithm = algorithm
    controller.threshold = threshold

    # TODO: change Image.open to MetaImage
    if ref_browser == "chrome":
        controller.ref_image = Image.open(controller.image_chrome.imagename)
        controller.com_image = Image.open(controller.image_firefox.imagename)
    if ref_browser == "firefox":
        controller.ref_image = Image.open(controller.image_chrome.imagename)
        controller.com_image = Image.open(controller.image_firefox.imagename)

    # Start divide and compare with initial bounding box
    controller.divide_recursive(controller.ref_image.getbbox(), 0)

    output_name = "output_recursive_{0}_{1}_{2}.{3}".format(
        controller.image_chrome.name,
        controller.image_firefox.name,
        controller.algorithm,
        controller.image_chrome.ext
    )
    controller.save_output(controller.ref_image, output_name)

    print("Eyecathing process completed.")
    controller.ref_image.show()


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
        ff.take_shot(url)
    
    if has_chrome:
        ch = ChromeScreenshot()
        ch.take_shot_puppeteer(url)


@cli.command()
@click.argument("image1")
@click.argument("image2")
@pass_controller
def normalize(controller, image1, image2):
    """
    - Make 2 images equal height by adding white background to the smaller image
    """
    controller.normalize_images(image1, image2)

@cli.command()
def firstrun():
    """
    - Install required dependencies of eyecatching
    """
    subprocess.call([
        "npm", "install"
    ])


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

