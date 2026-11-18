"""Makes the seven TIFF variants used to test TIFF decoding (needs: pip install tifffile imagecodecs pillow numpy).
Usage: python3 make_test_tiffs.py some_photo.jpg out_folder"""
import sys, os, numpy as np, tifffile
from PIL import Image
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
im = np.asarray(Image.open(src).convert('RGB')); im16 = im.astype(np.uint16) * 257
v = {'8bit-uncompressed.tif': (im, {}), '8bit-lzw-predictor.tif': (im, dict(compression='lzw', predictor=2)), '8bit-zip.tif': (im, dict(compression='zlib')),
     '16bit-uncompressed.tif': (im16, {}), '16bit-zip-predictor.tif': (im16, dict(compression='zlib', predictor=2)), '16bit-lzw-tiled.tif': (im16, dict(compression='lzw', tile=(256, 256)))}
for n, (d, kw) in v.items(): tifffile.imwrite(os.path.join(out, n), d, photometric='rgb', **kw)
with tifffile.TiffWriter(os.path.join(out, '16bit-with-thumbnail.tif')) as tw:   # like raw-converter exports: full image plus a thumbnail page
    tw.write(im16, photometric='rgb', compression='lzw', predictor=2); tw.write(np.asarray(Image.fromarray(im).resize((160, 108))), photometric='rgb', subfiletype=1)
print('made', len(v) + 1, 'TIFFs in', out)
