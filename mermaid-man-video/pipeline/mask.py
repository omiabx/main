import sys
from rembg import remove, new_session
from PIL import Image
s = new_session('birefnet-general')
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
m = remove(im, session=s, only_mask=True)
m.save(dst); print(dst, m.size)
