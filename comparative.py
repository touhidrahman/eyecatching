from PIL import Image
import imagehash

def main():
    a = Image.open('flower_and_water.jpg')
    b = Image.open('flower_and_water1.jpg')
    c = Image.open('Schlossgarten.jpg')
    
    hasha_a = imagehash.average_hash(a)
    hasha_d = imagehash.dhash(a)
    hasha_p = imagehash.phash(a)
    hasha_w = imagehash.whash(a)
    
    hashb_a = imagehash.average_hash(b)
    hashb_d = imagehash.dhash(b)
    hashb_p = imagehash.phash(b)
    hashb_w = imagehash.whash(b)
    
    hashc_a = imagehash.average_hash(c)
    hashc_d = imagehash.dhash(c)
    hashc_p = imagehash.phash(c)
    hashc_w = imagehash.whash(c)

    ab_a = hasha_a - hashb_a
    ab_d = hasha_d - hashb_d
    ab_p = hasha_p - hashb_p
    ab_w = hasha_w - hashb_w

    ac_a = hasha_a - hashc_a
    ac_d = hasha_d - hashc_d
    ac_p = hasha_p - hashc_p
    ac_w = hasha_w - hashc_w

    print("a vs b - aHash: " + str(ab_a))
    print("a vs b - dHash: " + str(ab_d))
    print("a vs b - pHash: " + str(ab_p))
    print("a vs b - wHash: " + str(ab_w))

    print("a vs c - aHash: " + str(ac_a))
    print("a vs c - dHash: " + str(ac_d))
    print("a vs c - pHash: " + str(ac_p))
    print("a vs c - wHash: " + str(ac_w))

if __name__ == '__main__':
    main()