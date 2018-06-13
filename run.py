import subprocess, os, sys, shutil
from PIL import Image
import imagehash

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
    

    
def tileImage(filename, edge):
    """
    Slice image into tiles with meaningful naming
    and move them into Prefixed directory
    """
    wd, ht = getImageSize(filename)
    img = Image.open(filename)
    prefix = filename.split('.')[0]
    extension = filename.split('.')[1]
    counter = 0

    if (os.path.isdir(prefix)):
        shutil.rmtree(prefix)
    os.mkdir(prefix)
    print("Slicing image {0} into {1} x {1} pixel tiles".format(filename, edge))
    for x in range(0, wd, edge):
        for y in range(0, ht, edge):
            croppedImg = img.crop((x, y, x+edge, y+edge))
            cFilename = "{0}/{0}_{1}_{2}.{3}".format(
                    prefix, x, y, extension
                )
            croppedImg.save(cFilename)
            counter = counter + 1
            del croppedImg
    print("Generated {0} images in directory {1}".format(counter, prefix))


def blendImage(baseImage, opacity):
    """
    Mask image with a color
    """
    size = getImageSize(baseImage)
    image1 = Image.new("RGB", size, "salmon")
    image2 = Image.open(baseImage).convert("RGB")
    blended = Image.blend(image1, image2, opacity)
    blended.save(baseImage)

    del image1, image2, blended


def remakeImage(refImage, compareImage):
    size = getImageSize(refImage)
    canvas = Image.new("RGB", size, "white")
    dirA = refImage.split('.')[0]
    dirB = compareImage.split('.')[0]
    pathA = os.getcwd() + "/" + dirA
    pathB = os.getcwd() + "/" + dirB

    for filename in os.listdir(pathA):
        filenameA = dirA + "/" + filename
        filenameB = dirB + "/" + filename.replace(dirA, dirB)
        # print(filenameA, filenameB)
        # print(getHashDiff(filenameA, filenameB))
        hashDiff = getHashDiff(filenameA, filenameB)

        if (hashDiff <= 30):
            blendImage(filenameA, 0.1)
        elif (hashDiff <= 40):
            blendImage(filenameA, 0.2)
        elif (hashDiff <= 50):
            blendImage(filenameA, 0.3)
        elif (hashDiff <= 60):
            blendImage(filenameA, 0.4)
        elif (hashDiff <= 70):
            blendImage(filenameA, 0.5)
        else:
            blendImage(filenameA, 0.6)

        prefix, x, yy = filename.split('_')
        y = yy.split(".")[0]
        img = Image.open(filenameA)
        canvas.paste(img, (int(x), int(y)))
        del img

    canvas.save("output.png")


def getHashDiff(image1, image2):
    img1 = Image.open(image1)
    img2 = Image.open(image2)
    hash1 = imagehash.average_hash(img1)
    hash2 = imagehash.average_hash(img2)
    print((hash1, hash2))
    del img1, img2
    return abs(hash1 - hash2)

def main():
    print('Working....')
    
    url = "http://angular.io"
    factor = 10
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
    tileImage(imageChrome, factor)
    tileImage(imageFirefox, factor)

    # join slices
    remakeImage(imageChrome, imageFirefox)


def test():
    # tileImage("A.png", 400)
    remakeImage("A.png", "B.png")


if (__name__ == "__main__"):
    # main()
    test()
