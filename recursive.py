from PIL import Image
import imagehash
import os
import shutil
import click

class Picture:
    def __init__(self, img, name):
        self.img = img
        self.name = name
        self.width, self.height = self.img.size

    # blendImage Method
    # Takes image co-ordinates
    # Now, just blend the image "B" and return
    def blendImage(self, x1, y1, x2, y2, diff):
        # Crop the image with given co-ordinates
        img1 = self.img.crop( (x1, y1, x2, y2) )
        opacity = diff/100 + 0.3 # thus it will be 0.3>opacity<0.93
        img_bottom = img1.convert("RGB")
        img_top = Image.new("RGB", img1.size, "salmon")
        blended_img = Image.blend(img_bottom, img_top, opacity)
        return blended_img
    
    # Pasting blended part to original image
    def reconstruction(self, paste_img, x1, y1):
        self.img.paste(paste_img, (x1, y1))

    # Saving the Reconstructed Image
    def saveToReconstruct(self):
        self.img.save("reconstruct.png")
    

#Main class
class Main:
    # Constructor method
    # Initially load both images
    # Call Picture class with loaded image
    # Take a count varible for counting dissimilar image portions
    def __init__(self, ref, com, algorithm):
        self.img_a = Picture(Image.open(ref), "A")
        self.img_b = Picture(Image.open(com), "B")
        self.count = 0
        self.algorithm = algorithm
        self.switcher = {
            'ahash': self.a_hash,
            'dhash': self.d_hash,
            'phash': self.p_hash,
            'whash': self.w_hash
        }

    # Methods for selecting given hashing algorithm by switcher
    def a_hash(self, img):
        return imagehash.average_hash(img)
    def d_hash(self, img):
        return imagehash.dhash(img)
    def p_hash(self, img):
        return imagehash.phash(img)
    def w_hash(self, img):
        return imagehash.whash(img)

    # compare method
    # Compares two image portions with given co-ordinates
    def compare(self, x1, y1, x2, y2):
         # At first crop the image portions
        a1_img = self.img_a.img.crop( (x1, y1, x2, y2) )
        b1_img = self.img_b.img.crop( (x1, y1, x2, y2) )

        hash_a =  self.switcher[self.algorithm](a1_img)
        hash_b =  self.switcher[self.algorithm](b1_img)
        diff =  hash_b-hash_a

        if diff == 0:
            # Two images are similar by hash
            # Now check their pixel's color
            color1 = a1_img.getpixel((2,3))
            color2 = b1_img.getpixel((2,3))
            if color1 == color2:
                # Two imeages color is also same
                return
            else:
                # Pixel's color is not same
                # Images are similar by hash, but not similar by color
                # So, Save
                blend_img = self.img_a.blendImage(x1, y1, x2, y2, diff)
                # Blending the second image part
                self.img_a.reconstruction(blend_img, x1, y1)
                # Increase dissimilar portion count
                self.count = self.count+1      
                return

        else: 
            self.divide(x1, y1, x2, y2, diff)
            return

    # divide method
    # Take image co-ordinates as parameter
    def divide(self, x1, y1, x2, y2, diff):   
        # First, find out width and height of image
        width = x2-x1
        height = y2-y1

        # return and save if image is less than 8px
        if width<=8 or height<=8:  
            # print(diff)
            blend_img = self.img_a.blendImage(x1, y1, x2, y2, diff)
            # Blending the second image part
            self.img_a.reconstruction(blend_img, x1, y1)
            # Increase dissimilar portion count
            self.count = self.count+1      
            return
        # Divide the image with larger side
        elif width>=height:
            # int() is used just to convert 1.0 to 1
            portion = int(width/2) if (width%2)==0 else int((width)/2)+1
            # Calculate co-ordinates of two image portion
            co_or_1 = [x1, y1, x1+portion, y2]
            co_or_2 = [x1+portion+1, y1, x2, y2]
        else: 
            # int() is used just to convert 1.0 to 1
            portion = int(height/2) if (height%2)==0 else int((height)/2)+1
            # Calculate co-ordinates of two image portion
            co_or_1 = [x1, y1, x2, y1+portion]
            co_or_2 = [x1, y1+portion+1, x2, y2]

        # Calling compare method with image co-ordinates as arguments
        self.compare(co_or_1[0], co_or_1[1], co_or_1[2], co_or_1[3])
        self.compare(co_or_2[0], co_or_2[1], co_or_2[2], co_or_2[3])
        return



@click.command()
@click.option('--ref', help='The reference image')
@click.option('--com', help='Image to compare')
@click.argument('algorithm', nargs=1)
def start(ref, com, algorithm):
    click.echo('You have selected %s algorithm.' %algorithm)
    # Making an object of Main class
    init = Main(ref, com, algorithm)
    # Calling divide method of init Object with image co-ordinates
    init.divide(0, 0, init.img_a.width, init.img_a.height, 0)
    # Calling method for Saving the Reconstructed Image
    init.img_a.saveToReconstruct()
    # Printing output and showing reconstructed image
    print(str(init.count) + " dissimilar image parts detected.")
    print("Reconstruct image has saved to current folder.")
    print("Now see the reconstructed image...")
    init.img_a.img.show()


# Starting the program by calling main method
if __name__ == '__main__':
    start()