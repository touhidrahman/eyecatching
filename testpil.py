#!/usr/bin/env
import subprocess, os, sys, shutil
from PIL import Image
import imagehash
from eyecatchingutil import MetaImage
from eyecatchingutil import ImageComparator

def main():
    print('Working....')

    image_chrome = "chrome.png"
    image_firefox = "firefox.png"
    ext = image_chrome.split('.')[1]
    prefix1 = image_chrome.split('.')[0]
    prefix2 = image_firefox.split('.')[0]

    for prefix in [prefix1, prefix2]:
        if os.path.isdir(prefix):
            shutil.rmtree(prefix)
        os.mkdir(prefix)

    # divide image
    img1_cr, img2_cr, name1_cr, name2_cr = divide_image(image_chrome)
    img1_ff, img2_ff, name1_ff, name2_ff = divide_image(image_firefox)
    # compare images 
    diff1 = get_hash_diff_pil(img1_cr, img1_ff, 'avg')
    diff2 = get_hash_diff_pil(img2_cr, img2_ff, 'avg')
    # save
    if diff1 > 0:
        img1_cr.save(make_name(prefix1, name1_cr, ext))
        img1_ff.save(make_name(prefix1, name2_cr, ext))
    if diff2 > 0:
        img2_cr.save(make_name(prefix2, name1_ff, ext))
        img2_ff.save(make_name(prefix2, name2_ff, ext))

    print("Done.")



def recursive_check(image1, image2):
    # if both image are same, abort further check
    diff = get_hash_diff_pil(image1, image2, 'avg')
    if diff == 0:
        return
    
    # otherwise keep on checking until the image is min px
    wd, ht = image1.size
    bigger = wd
    if ht > wd:
        bigger = ht

    ir1, ir2, nr1, nr2 = divide_image(image1)
    ic1, ic2, nc1, nc2 = divide_image(image2)
    prefix1 = ir1.split("_")[0]
    prefix2 = ic1.split("_")[0]
    ext = ir1.split(".")[1]
    if (bigger > 7):
        recursive_check(ir1, ic1)
        recursive_check(ir2, ic2)
    else:
        ir1.save(make_name(prefix1, nr1, ext))
        ir2.save(make_name(prefix1, nr2, ext))
        ic1.save(make_name(prefix2, nc1, ext))
        ic2.save(make_name(prefix2, nc2, ext))
        del ir1, ir2, ic1, ic2


def is_equal(image1, image2):
    return get_hash_diff_pil(image1, image2) == 0


def check_inside(image1, image2):
    if (get_hash_diff_pil(image1, image2) > 0):
        pass
    pass

def get_hash_diff_pil(image1, image2, algorithm):
    """
    Get the hamming distance of two images
    """
    switcher = {
        'avg': imagehash.average_hash,
        'phash': imagehash.phash,
        'dhash': imagehash.dhash
    }
    hash1 = switcher[algorithm](image1)
    hash2 = switcher[algorithm](image2)
    return abs(hash1 - hash2)

def divide_image(imagefile):
    """
    Divides an image into two along the large axis
    and return the files as PIL object as tuple
    """
    img = MetaImage(imagefile)

    if (img.width % 2 == 0) and (img.height % 2 == 0):
        half1 = img.image.crop(img.first_half())
        half2 = img.image.crop(img.second_half())
        half1.save(img.prefix, img.first_half(), img.ext)
        half2.save(img.prefix, img.second_half(), img.ext)

        # return (c1_img, c2_img, pos1, pos2)
    else:
        print("Image size is not even, cannot divide. Exiting...")
        return (None, None, None, None)


def test():
    image1 = MetaImage("c.jpg")
    image2 = MetaImage("a.jpg")
    # image1.image.show()
    # image2.image.show()

    c1 = ImageComparator(image1, image2)
    # print(c1.is_similar("dhash"))
    # print(c1.is_similar_d_hash())
    print(c1.hamming_diff("phash"))

if __name__ == '__main__':
    # main()
    test()