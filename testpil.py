#!/usr/bin/env
import subprocess, os, sys, shutil
from PIL import Image
import imagehash
from eyecatchingutil import MetaImage
from eyecatchingutil import ImageComparator

def main():
    print('Working....')
    image1 = MetaImage("b.jpg")
    image2 = MetaImage("a.jpg")
    # image1.image.show()
    # image2.image.show()

    recursive_check("a.jpg", "b.jpg")



def recursive_check(image1, image2):
    img1 = MetaImage(image1)
    img2 = MetaImage(image2)
    c = ImageComparator(img1, img2)
    if c.hamming_diff() > 0:
        (a1, a2) = img1.divide()
        (b1, b2) = img2.divide()
        if a1 != None or b1 != None:
            recursive_check(a1, b1)
        if a2 != None or b2 != None:
            recursive_check(a2, b2)
    else:
        img2.delete()



if __name__ == '__main__':
    main()
