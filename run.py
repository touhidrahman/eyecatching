import subprocess, os, sys, shutil
from PIL import Image
import imagehash


def get_image_size(filename):
    """
    Get image size
    """
    img = Image.open(filename)
    size = img.size
    del img
    return size


def get_screenshot(browser, url, imageSize, imageName):
    """
    Get screenshot of the given webpage
    """
    default_name = "screenshot.png"

    def firefox(url, image_size):
        windowSize = "--window-size={0}".format(image_size['width'] + 10)
        subprocess.call(["firefox", "-screenshot", windowSize, url])
        # remove the scrolbar 
        remove_pixels_right(default_name, 10)

    def chrome(url, image_size):
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
    switcher[browser](url, imageSize)
    # rename picture
    subprocess.call(["mv", default_name, imageName])
    print("Saved screenshot from {0} with name {1}".format(browser, imageName))


def remove_pixels_right(image, pixels):
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
        subprocess.call(["convert", image, "-gravity", "south", "-splice", ex_ht_str, image])
        print("Extended {0} pixels at the bottom of image {1}".format(ex_ht, image))

    if ex_wd != factor:
        ex_wd_str = "{0}x0".format(ex_wd)
        subprocess.call(["convert", image, "-gravity", "east", "-splice", ex_wd_str, image])
        print("Extended {0} pixels at the right of image {1}".format(ex_wd, image))


def tile_image(filename: str, edge: int):
    """
    Slice image into tiles with meaningful naming
    and move them into Prefixed directory
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
    blended = Image.blend(img_top, img_bottom, opacity)
    blended.save(image)

    del img_bottom, img_top, blended


def compare_tiles(ref_dir, compare_dir):
    """
    Compares tiles and marks different tiles in comparing directory
    """
    path = os.getcwd() + "/" + compare_dir

    # clean up directory, only image files should exist

    for tile in os.listdir(path):
        tile_ref_img = ref_dir + "/" + tile.replace(compare_dir, ref_dir)
        tile_com_img = compare_dir + "/" + tile
        hash_diff = get_hash_diff(tile_ref_img, tile_com_img)

        # print((tile_ref_img, tile_com_img))

        if hash_diff >= 30 and hash_diff < 39:
            mark_image(tile_com_img, 0.1)
        elif hash_diff >= 40 and hash_diff < 49:
            mark_image(tile_com_img, 0.2)
        elif hash_diff >= 50 and hash_diff < 59:
            mark_image(tile_com_img, 0.3)
        elif hash_diff >= 60 and hash_diff < 69:
            mark_image(tile_com_img, 0.4)
        else:
            mark_image(tile_com_img, 0.5)


def remake_image(ref_img, compare_img):
    print("Marking visual differences from reference image...")
    size = get_image_size(ref_img)
    canvas = Image.new("RGB", size, "white")
    dir_ref = ref_img.split('.')[0]
    dir_com = compare_img.split('.')[0]
    path = os.getcwd() + "/" + dir_com

    compare_tiles(dir_ref, dir_com)

    for filename in os.listdir(path):
        img_tile = dir_com + "/" + filename
        prefix, x, yy = filename.split('_')
        y = yy.split(".")[0]
        img = Image.open(img_tile)
        # print(filename)
        canvas.paste(img, (int(x), int(y)))
        del img

    saving_name = "output" + "_" + compare_img
    canvas.save(saving_name)
    print("Resulted file saved as {0}".format(saving_name))


def get_hash_diff(image1, image2):
    img1 = Image.open(image1)
    img2 = Image.open(image2)
    hash1 = imagehash.dhash(img1)
    hash2 = imagehash.dhash(img2)
    del img1, img2
    return abs(hash1 - hash2)


def main():
    print('Working....')

    url = "http://angular.io"
    factor = 20
    image_size = {'width': 1280}
    image_chrome = "A.png"
    image_firefox = "B.png"

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

    # join slices
    remake_image(image_chrome, image_firefox)

    print("Done.")


def test():
    # tileImage("A.png", 400)
    remake_image("A.png", "B.png")


if __name__ == "__main__":
    main()
    # test()
