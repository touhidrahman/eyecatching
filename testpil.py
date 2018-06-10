#!/usr/bin/env
import os, sys
from PIL import Image

def main():
    # size = wd, ht = 100, 100

    # image1 = Image.new( "RGB", size, "rgb(104, 33, 204)" )
    # image2 = Image.open("OUT/output2.png").convert("RGB")

    # blend = Image.blend(image1, image2, 0.7)
    # blend.show()

    # # print (os.getcwd())
    # # os.mkdir('OUT')
    # # blend.save("OUT/output2.png")

    # # image2.show()
    # # image2.paste("rgba(104, 33, 204, 0)", (0, 0, wd, ht))

    # # image2.show()

    # del image1, image2

    for y in range (0, 2500, 100):
        for x in range (0, 1300, 100):
            print((x, y))

if (__name__ == "__main__"):
    main()