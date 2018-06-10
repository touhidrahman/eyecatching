import subprocess
from PIL import Image

def getImageSize(filename):
    """
    Get image size
    """
    img = Image.open(filename)
    size = wd, ht = img.size
    del img
    return size

def getScreenshot(browser, url, imageSize, imageName):
    """
    Get screenshot of the given webpage
    """
    defaultName = "screenshot.png"
    
    def firefox(url, imageSize):
        windowSize = "--window-size={0}".format(imageSize['width'] + 10)
        subprocess.call(["firefox", "-screenshot", windowSize, url])
        # remove the scrolbar 
        chopFromRight(defaultName, 10)
    
    def chrome(url, imageSize):
        windowSize = "--window-size={0},{1}".format(
            imageSize['width'], imageSize['height']
        )
        subprocess.call(["/opt/google/chrome/chrome",
                        "--headless",
                        "--hide-scrollbars",
                        windowSize,
                        "--screenshot",
                        url])
        
    switcher = {'firefox': firefox, 'chrome': chrome}
    switcher[browser](url, imageSize)
    # rename picture
    subprocess.call(["mv", defaultName, imageName])
    print("Saved screenshot from {0} with name {1}".format(browser, imageName))


def chopFromRight(image, pixels):
    """
    Subtract given pixels from right side of the image 
    and replace the original file
    """
    px = "{0}x0".format(pixels)
    subprocess.call(["convert", image, "-gravity", "East", "-chop", px, image])
    print("Removed {0} pixels from the right side of image {1}".format(pixels, image))


def extendImage(image, factor):
    """
    Extend the image to be equally divisible by factor
    """
    wd, ht = getImageSize(image)
    exWd = factor - (wd % factor)
    exHt = factor - (ht % factor)

    if (exHt != factor):
        exH = "0x{0}".format(exHt)
        subprocess.call(["convert", image, "-gravity", "south", "-splice", exH, image])
        print("Extended {0} pixels at the bottom of image {1}".format(exHt, image))
    if (exWd != factor):
        exW = "{0}x0".format(exWd)
        subprocess.call(["convert", image, "-gravity", "east", "-splice", exW, image])
        print("Extended {0} pixels at the right of image {1}".format(exWd, image))
    
    
def sliceImage(image, edge):
    """
    Slice image into tiles with meaningful naming
    and move them into Prefixed directory
    """
    print("Slicing {0}, this may take a while...".format(image))
    
    prefix = image.split('.')[0]
    extension = image.split('.')[1]
    cmd = ["convert",
            image,
            "-crop",
            "{0}x{0}".format(edge),     # 100x100
            "-set",
            "filename:tile",    # Imagemagick Fn that renames tiles 
            "%[fx:page.x/{0}+1]_%[fx:page.y/{0}+1]".format(edge),
            "{0}/{0}_%[filename:tile].{1}".format(prefix, extension)]
    
    subprocess.call(["rm", "-rf", prefix])
    subprocess.call(["mkdir", prefix])
    subprocess.call(cmd)
    
    print("Sliced image {0} into {1} x {1} tiles".format(image, edge))
    
    
def blendImage(baseImage):
    """
    Mask image with a color
    """
    size = getImageSize(baseImage)
    image1 = Image.new("RGB", size, "salmon")
    image2 = Image.open(baseImage).convert("RGB")
    blended = Image.blend(image1, image2, 0.7)

    del image1, image2


def main():
    print('Working....')
    
    url = "http://neon.kde.org"
    factor = 100
    imageSize = {'width': 1280}
    imageChrome = "A.png"
    imageFirefox = "B.png"
    
    getScreenshot('firefox', url, imageSize, imageFirefox)
    
    # get viewport height from firefox image
    imageSize['height'] = Image.open(imageFirefox).size[1]
    
    getScreenshot('chrome', url, imageSize, imageChrome)

    print("Resulted image size is {0} x {1}".format(imageSize['width'], imageSize['height']))
    
    # entend images to cut precisely
    extendImage(imageChrome, factor)
    extendImage(imageFirefox, factor)
    
    # slice to tiles
    sliceImage(imageChrome, factor)
    sliceImage(imageFirefox, factor)


if (__name__ == "__main__"):
    main()
