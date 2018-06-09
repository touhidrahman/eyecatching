import subprocess

import struct
import imghdr

def getImageSize(fname):
    '''
    Determine the image type of fhandle and return its size.
    '''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0) # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception: #IGNORE:W0703
                return
        else:
            return
        return width, height
    
    

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
        windowSize = "--window-size={0},{1}".format(imageSize['width'], imageSize['height'])
        subprocess.call(["/opt/google/chrome/chrome", "--headless", "--hide-scrollbars", windowSize, "--screenshot", url])
        
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
    wd = getImageSize(image)[0]
    ht = getImageSize(image)[1]
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
    
    
    
def main():
    print('Working....')
    
    url = "http://neon.kde.org"
    factor = 100
    imageSize = {'width': 1280}
    
    getScreenshot('firefox', url, imageSize, "A.png")
    
    # get viewport height from firefox image
    imageSize['height'] = getImageSize("A.png")[1]
    
    getScreenshot('chrome', url, imageSize, "B.png")

    print("Resulted image size is {0} x {1}".format(imageSize['width'], imageSize['height']))
    
    # entend images to cut precisely
    extendImage("A.png", factor)
    extendImage("B.png", factor)
    
    # slice to tiles
    sliceImage("A.png", factor)
    sliceImage("B.png", factor)


if (__name__ == "__main__"):
    main()
