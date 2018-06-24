import subprocess, os, sys, shutil
from PIL import Image
import imagehash
import click

@click.command()
@click.argument('url')
@click.option('--factor', default=20,
            help="Tile block size, px. \n(Default: 20)") # TODO: add warning and allow min 8
@click.option('--viewport-width', default=1280,
            help="Viewport width, px. (Default: 1280)")
@click.option('--algorithm', default="avg",
            help="Perceptual hashing algorithm to be used.\n(Default: avg) Available: avg, phash, dhash")
@click.option('--ref-browser', default="chrome",
            help="Reference browser (Default: chrome) Available: chrome, firefox")
@click.option('--output', help="Name for the output file.")
@click.option('--reset', is_flag=True, help="Remove all previous outputs.")
def main(
    url,
    factor,
    viewport_width,
    algorithm,
    ref_browser,
    output,
    reset):
    """
    Tests the frontend of a website/webapp by comparing screenshots
    captured from different browsers (at present Chrome and Firefox).

    $ eyecatching <URL> [--option value]

    For example:

    $ eyecatching http://example.com

    """

    print('Working....')

    image_size = {'width': viewport_width}
    image_chrome = "chrome.png"
    image_firefox = "firefox.png"

    # On reset command remove all previous files and exit
    if reset:
        remove_old_files([image_chrome, image_firefox])
        exit()

    get_screenshot('firefox', url, image_size, image_firefox)

    # get viewport height from firefox image
    image_size['height'] = Image.open(image_firefox).size[1]

    get_screenshot('chrome', url, image_size, image_chrome)

    print("Resulted image size is {0} x {1}".format(image_size['width'], image_size['height']))

    # extend images to cut precisely
    extend_image(image_chrome, factor)
    extend_image(image_firefox, factor)

    # slice to tiles
    tile_image(image_chrome, factor)
    tile_image(image_firefox, factor)

    if ref_browser == "chrome":
        ref_img = image_chrome
        comp_img = image_firefox
    if ref_browser == "firefox":
        ref_img = image_firefox
        comp_img = image_chrome

    # join slices
    remake_image(ref_img, comp_img, algorithm)

    print("Done.")


def get_image_size(filename):
    """
    Get image size
    """
    img = Image.open(filename)
    size = img.size
    del img
    return size


def get_screenshot(browser, url, image_size, image_name):
    """
    Get screenshot of the given webpage
    """
    default_name = "screenshot.png"

    def firefox(url, image_size):
        # add 10px for scrollbar
        window_size = "--window-size={0}".format(image_size['width'] + 10)
        subprocess.call(["firefox",
                        "-screenshot",
                        window_size,
                        url])
        # remove the scrolbar 
        remove_pixels_right(default_name, 10)

    def chrome(url, image_size):
        # chrome expects full viewport size
        window_size = "--window-size={0},{1}".format(
            image_size['width'], image_size['height']
        )
        subprocess.call(["/opt/google/chrome/chrome",
                         "--headless",
                         "--hide-scrollbars",
                         window_size,
                         "--screenshot",
                         url])

    switcher = {
        'firefox': firefox,
        'chrome': chrome
    }
    switcher[browser](url, image_size)
    # rename picture
    os.rename(default_name, image_name)
    print("Saved screenshot from {0} with name {1}".format(browser, image_name))


def remove_pixels_right(image: str, pixels: int):
    """
    Subtract given pixels from right side of the image 
    and replace the original file.
    Used to remove scrollbar pixels.
    """
    px = "{0}x0".format(pixels)
    subprocess.call(["convert", image, "-gravity", "East", "-chop", px, image])
    print("Removed {0} pixels from the right side of image {1}".format(pixels, image))


def extend_image(image: str, factor: int):
    """
    Extend the image to be equally divisible by factor
    :type image: str
    :type factor: int
    """
    wd, ht = get_image_size(image)
    ex_wd = factor - (wd % factor)
    ex_ht = factor - (ht % factor)

    if ex_ht != factor:
        ex_ht_str = "0x{0}".format(ex_ht)
        subprocess.call(["convert",
                        image,
                        "-gravity", "south",
                        "-splice",
                        ex_ht_str,
                        image])
        print("Extended {0} pixels at the bottom of image {1}".format(ex_ht, image))

    if ex_wd != factor:
        ex_wd_str = "{0}x0".format(ex_wd)
        subprocess.call(["convert",
                        image,
                        "-gravity",
                        "east",
                        "-splice",
                        ex_wd_str,
                        image])
        print("Extended {0} pixels at the right of image {1}".format(ex_wd, image))


def tile_image(filename: str, edge: int):
    """
    Slice image into tiles with meaningful naming
    and move them into same name directory
    """
    wd, ht = get_image_size(filename)
    img = Image.open(filename)
    prefix = filename.split('.')[0]
    extension = filename.split('.')[1]
    counter = 0

    if os.path.isdir(prefix):
        shutil.rmtree(prefix)

    os.mkdir(prefix)

    print("Slicing image {0} into {1} x {1} pixel tiles".format(filename, edge))

    for x in range(0, wd, edge):
        for y in range(0, ht, edge):
            cropped_img = img.crop((x, y, x + edge, y + edge))
            cropped_filename = "{0}/{0}_{1}_{2}.{3}".format(
                prefix, x, y, extension
            )  # this format helps saving inside subdirectory
            cropped_img.save(cropped_filename)
            counter = counter + 1
            del cropped_img

    print("Generated {0} images in directory {1}".format(counter, prefix))


def mark_image(image: str, opacity: float):
    """
    Mask image with a color
    """
    img_bottom = Image.open(image).convert("RGB")
    img_top = Image.new("RGB", img_bottom.size, "salmon")
    blended = Image.blend(img_bottom, img_top, opacity)
    blended.save(image)

    del img_bottom, img_top, blended


def compare_tiles(ref_dir, compare_dir, algorithm):
    """
    Compares tiles and marks different tiles in comparing directory
    """
    path = os.getcwd() + "/" + compare_dir

    for tile in os.listdir(path):
        tile_ref_img = ref_dir + "/" + tile.replace(compare_dir, ref_dir)
        tile_com_img = compare_dir + "/" + tile
        hash_diff = get_hash_diff(tile_ref_img, tile_com_img, algorithm)

        opacity = 0
        if hash_diff >= 30 and hash_diff < 39:
            opacity = 0.3
        if hash_diff >= 40 and hash_diff < 49:
            opacity = 0.4
        if hash_diff >= 50 and hash_diff < 59:
            opacity = 0.5
        if hash_diff >= 60 and hash_diff < 69:
            opacity = 0.6
        if hash_diff >= 70:
            opacity = 0.7

        if opacity != 0:
            mark_image(tile_com_img, opacity)


def remake_image(ref_img, compare_img, algorithm):
    print("Marking visual differences from reference image...")
    size = get_image_size(ref_img)
    canvas = Image.new("RGB", size, "white")
    dir_ref = ref_img.split('.')[0]
    dir_com = compare_img.split('.')[0]
    path = os.getcwd() + "/" + dir_com

    compare_tiles(dir_ref, dir_com, algorithm)

    for filename in os.listdir(path):
        img_tile = dir_com + "/" + filename
        prefix, x, yy = filename.split('_')
        y = yy.split(".")[0]
        img = Image.open(img_tile)
        canvas.paste(img, (int(x), int(y)))
        del img

    saving_name = "output" + "_" + compare_img
    canvas.save(saving_name)
    print("Resulted file saved as {0}".format(saving_name))


def get_hash_diff(image1, image2, algorithm):
    """
    Get the hamming distance of two images
    """
    switcher = {
        'avg': imagehash.average_hash,
        'phash': imagehash.phash,
        'dhash': imagehash.dhash
    }
    img1 = Image.open(image1)
    img2 = Image.open(image2)
    hash1 = switcher[algorithm](img1)
    hash2 = switcher[algorithm](img2)
    del img1, img2
    return abs(hash1 - hash2)


def remove_old_files(images):
    """
    Remove old output files
    """
    for image in images:
        shutil.rmtree(image.split('.')[0])
        os.remove(image)

    for filename in os.listdir("."):
        if filename.startswith("output"):
            os.remove(filename)

    print('All previous outputs removed.')
