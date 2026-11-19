import sys, torch, numpy as np
from PIL import Image
from spandrel import ModelLoader
torch.set_num_threads(4)
m = ModelLoader().load_from_file('/home/user/media/models/anime6b.pth').eval()
for src in sys.argv[1:]:
    im = Image.open(src).convert('RGB')
    x = torch.from_numpy(np.asarray(im)).permute(2,0,1).float().div(255).unsqueeze(0)
    with torch.no_grad(): y = m(x)
    out = Image.fromarray((y.squeeze(0).permute(1,2,0).clamp(0,1).numpy()*255).round().astype(np.uint8))
    dst = src.rsplit('.',1)[0] + '_x4.png'; out.save(dst); print(dst, out.size)
