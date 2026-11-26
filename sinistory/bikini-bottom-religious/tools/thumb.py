import sys, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-main/097e55d9-3f75-5e8f-88d6-04e1d361aa0f/scratchpad/tools')
from sinistory import font, paper_tag, RED, INK
from PIL import Image, ImageDraw, ImageFilter, ImageChops

T = '/tmp/claude-0/-home-user-main/097e55d9-3f75-5e8f-88d6-04e1d361aa0f/scratchpad/thumb/'
TW, TH = 1280, 720
ROBE, ROBE_SH, LINE, ROPE = (232, 222, 196), (196, 184, 156), (38, 30, 26), (128, 88, 46)

def bg():
    yy, xx = np.mgrid[0:TH, 0:TW]
    r = np.sqrt(((xx - TW / 2) / (TW * .6)) ** 2 + ((yy - TH * .45) / (TH * .7)) ** 2).clip(0, 1) ** 1.5
    img = np.array((26, 32, 50))[None, None] * (1 - r[..., None]) + np.array((9, 11, 20))[None, None] * r[..., None]
    beam = np.zeros((TH, TW)); half = 70 + (yy / TH) * 420
    beam = np.clip(1 - np.abs(xx - TW / 2) / half, 0, 1) ** 1.3 * (0.35 + 0.65 * (1 - yy / TH) ** .8)
    img = img * (1 - beam[..., None] * .75) + np.array((255, 214, 120))[None, None] * beam[..., None] * .75
    img += np.random.default_rng(1).normal(0, 3, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

def trident(cx, top, h):
    L = Image.new('RGBA', (TW, TH), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    gold, edge = (255, 205, 70, 255), (120, 78, 10, 255); s = h / 300
    shaft = [(cx - 9 * s, top + 120 * s), (cx + 9 * s, top + 120 * s), (cx + 9 * s, top + h), (cx - 9 * s, top + h)]
    cross = [(cx - 95 * s, top + 105 * s), (cx + 95 * s, top + 105 * s), (cx + 95 * s, top + 132 * s), (cx - 95 * s, top + 132 * s)]
    def prong(x0, lean):
        return [(x0 - 10 * s, top + 120 * s), (x0 + 10 * s, top + 120 * s), (x0 + 10 * s + lean, top + 30 * s), (x0 + lean, top), (x0 - 10 * s + lean, top + 30 * s)]
    shapes = [shaft, cross, prong(cx - 85 * s, -8 * s), prong(cx, 0), prong(cx + 85 * s, 8 * s)]
    glow = Image.new('RGBA', (TW, TH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for p in shapes: gd.polygon(p, fill=(255, 220, 120, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    for p in shapes: d.polygon(p, fill=gold, outline=edge, width=max(2, int(4 * s)))
    d.line([(cx - 3 * s, top + 140 * s), (cx - 3 * s, top + h - 10 * s)], fill=(255, 240, 170, 255), width=max(1, int(4 * s)))
    return glow, L

def robed(cut, robe_top, x0, x1, hem_extra, flare=.12, belt=.42, sleeve=None):
    """Draw a plain hooded-free robe over the lower body of a cut-out. Coordinates are in the cut's pixels."""
    w, h = cut.size; H2 = h + hem_extra
    out = Image.new('RGBA', (w + 80, H2 + 20), (0, 0, 0, 0)); ox = 40; out.alpha_composite(cut, (ox, 0))
    d = ImageDraw.Draw(out)
    bw = x1 - x0; fl = bw * flare
    poly = [(ox + x0, robe_top), (ox + x1, robe_top), (ox + x1 + fl, H2), (ox + x0 - fl, H2)]
    # rounded shoulders
    d.polygon(poly, fill=ROBE + (255,), outline=LINE + (255,))
    d.pieslice([ox + x0, robe_top - bw * .05, ox + x1, robe_top + bw * .05], 180, 360, fill=ROBE + (255,), outline=LINE + (255,), width=5)
    d.rectangle([ox + x0 + 3, robe_top - 2, ox + x1 - 3, robe_top + bw * .05], fill=ROBE + (255,))
    d.line([poly[0], poly[3]], fill=LINE + (255,), width=6); d.line([poly[1], poly[2]], fill=LINE + (255,), width=6); d.line([poly[3], poly[2]], fill=LINE + (255,), width=6)
    # neckline V and folds
    mx = ox + (x0 + x1) / 2
    d.line([(mx - bw * .12, robe_top - bw * .03), (mx, robe_top + bw * .13), (mx + bw * .12, robe_top - bw * .03)], fill=LINE + (255,), width=5)
    for f in (-.22, .05, .28):
        xf = mx + bw * f; d.line([(xf, robe_top + (H2 - robe_top) * (belt + .1)), (xf + bw * f * .25, H2 - 8)], fill=ROBE_SH + (255,), width=7)
    # rope belt + knot
    yb = robe_top + (H2 - robe_top) * belt
    d.line([(ox + x0 - fl * belt + 2, yb), (ox + x1 + fl * belt - 2, yb)], fill=ROPE + (255,), width=13)
    d.line([(mx + bw * .12, yb), (mx + bw * .15, yb + (H2 - robe_top) * .3)], fill=ROPE + (255,), width=10)
    d.line([(mx + bw * .12, yb), (mx + bw * .03, yb + (H2 - robe_top) * .26)], fill=ROPE + (255,), width=10)
    d.ellipse([mx + bw * .08, yb - 13, mx + bw * .17, yb + 13], fill=ROPE + (255,))
    return out

def shadowed(im, off=(10, 14), blur=12, a=150):
    sh = Image.new('RGBA', (im.width + 60, im.height + 60), (0, 0, 0, 0))
    m = im.getchannel('A').point(lambda v: int(v * a / 255)); blk = Image.new('RGBA', im.size, (0, 0, 0, 255)); blk.putalpha(m)
    sh.alpha_composite(blk, (30 + off[0], 30 + off[1])); sh = sh.filter(ImageFilter.GaussianBlur(blur)); sh.alpha_composite(im, (30, 30)); return sh

def place(base, im, x, y_bottom, height):
    s = height / im.height; im = im.resize((int(im.width * s), int(height)), Image.LANCZOS); im = shadowed(im)
    base.alpha_composite(im, (int(x - 30), int(y_bottom - im.height + 30)))

def make(variant, out):
    b = bg(); glow, tri = trident(TW // 2 + 10, 14 if variant == 'A' else 18, 300)
    b.alpha_composite(glow); b.alpha_composite(glow); b.alpha_composite(tri)
    krabs = robed(Image.open(T + 'krabs_cut.png').convert('RGBA'), 432, 222, 618, 60, flare=.08, belt=.42)
    sb = robed(Image.open(T + 'sb_cut.png').convert('RGBA'), 258, 8, 250, 240, flare=.10, belt=.30)
    pat = robed(Image.open(T + 'pat_cut.png').convert('RGBA'), 252, 32, 252, 220, flare=.10, belt=.34)
    if variant == 'A':
        place(b, krabs, -40, 905, 640); place(b, sb, 600, 930, 690); place(b, pat, 880, 960, 800)
        tag = paper_tag('THEY PRAY TO HIM', 92).rotate(-3, resample=Image.BICUBIC, expand=True)
        s = 600 / tag.width; tag = tag.resize((600, int(tag.height * s)), Image.LANCZOS); b.alpha_composite(tag, (8, 6))
        d = ImageDraw.Draw(b); d.line([(560, 120), (600, 128), (548, 128)], fill=RED, width=0)
        d.line([(568, 150), (630, 118)], fill=RED + (255,), width=10); d.polygon([(642, 112), (612, 112), (628, 136)], fill=RED + (255,))
    else:
        place(b, krabs, -30, 930, 680); place(b, sb, 610, 950, 720); place(b, pat, 880, 990, 840)
    b = b.convert('RGB'); b.save(out, quality=92, optimize=True); return out

if __name__ == '__main__':
    print(make('A', T + 'thumb_A.jpg')); print(make('B', T + 'thumb_B.jpg'))
