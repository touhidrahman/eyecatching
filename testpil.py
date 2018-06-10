#!/usr/bin/env

from PIL import Image

def main():
    size = wd, ht = 100, 100

    image1 = Image.new( "RGB", size, "rgb(104, 33, 204)" )
    image2 = Image.open("C.png").convert("RGB")

    Image.blend(image1, image2, 0.7).show()

    # image2.show()
    # image2.paste("rgba(104, 33, 204, 0)", (0, 0, wd, ht))

    # image2.show()

    del image1, image2

if (__name__ == "__main__"):
    main()