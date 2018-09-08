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
@click.argument('t', default="test")
@pass_controller
def test(controller, t):
    print(controller.image_chrome.name)
    c = ChromeScreenshot()
    c.take_shot_puppeteer(t)


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
@pass_controller
def linear(
    controller,
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

    validate_command_inputs(url, algorithm)

    if factor < 8:
        print("Factor is too small! Please use a value above 8")
        exit()

    print('Eyecatching is working....')

    controller.get_screenshot(url)

    # extend images to cut precisely
    print("Info: \tExtending images with white canvas to work with block size")
    controller.image_chrome.extend_image(factor)
    controller.image_firefox.extend_image(factor)

    # slice to tiles
    controller.tile_image(controller.image_chrome.imagename, factor)
    controller.tile_image(controller.image_firefox.imagename, factor)

    if ref_browser == "chrome":
        ref_img = controller.image_chrome.imagename
        comp_img = controller.image_firefox.imagename
    if ref_browser == "firefox":
        ref_img = controller.image_firefox.imagename
        comp_img = controller.image_chrome.imagename

    # join slices
    output = controller.remake_image(ref_img, comp_img, algorithm)

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

    validate_command_inputs(url, algorithm)

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

    if has_firefox:
        ff = FirefoxScreenshot()
        ff.take_shot(url)
    
    if has_chrome:
        ch = ChromeScreenshot()
        ch.take_shot_puppeteer(url)


@cli.command()
def normalize_images():
    """
    - Make 2 images equal height
    """
    pass


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


def validate_command_inputs(url, algorithm):
    if url is None:
        print("Argument <URL> missing! Please input a valid URL.")
        exit()

    if is_valid_url(url) == False:
        print("Invalid URL! Please input a valid URL.")
        exit()

