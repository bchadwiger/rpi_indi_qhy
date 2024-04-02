import os
import numpy as np
import argparse
from astropy.io import fits
from PIL import Image



if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='transform_image.py',
                                     description='Debayers and transforms raw fits image to png')
    parser.add_argument('path', help='Path to the image to transform')
    args = parser.parse_args()

    if not args.path.endswith('.fit'):
        raise ValueError('Path {path} is not fits image')

    img = fits.getdata(args.path) / (2**16 - 1) * (2**8 - 1)
    img = img.astype('uint8')
    print(img.shape)
    print(img.dtype)
    print(np.max(img))
    print(np.min(img))
    imgR =  img[::2,::2]
    imgB =  img[1::2, 1::2]
    imgG1 = img[1::2, ::2]
    imgG2 = img[::2, 1::2]
    imgRGB = np.stack([imgR, imgG1, imgB], axis=2)
    print(f'imgRGB.shape: {imgRGB.shape}')
    im = Image.fromarray(imgRGB)
    im.save('out.png')
