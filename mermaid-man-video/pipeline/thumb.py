"""Thumbnail builder: real episode frame, cut-out + sticker outline, bold condensed text."""
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageEnhance

W, H = 1280, 720
F = '/home/user/media/fonts/'
FR = '/home/user/media/frames/'


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def background(src, tint=(10, 20, 60)):
    bg = cover(Image.open(src).convert('RGB'), W, H).filter(ImageFilter.GaussianBlur(14))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    bg = Image.blend(bg, Image.new('RGB', (W, H), tint), 0.35)
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W * 0.42) / (W * 0.75)) ** 2 + ((yy - H * 0.5) / (H * 0.8)) ** 2)
    v = np.clip(1.15 - d, 0.25, 1.0)[..., None]
    arr = (np.asarray(bg).astype(np.float32) * v).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert('RGBA')


def sticker(cut, keep_box, scale, outline=14):
    """cut: RGBA cut-out. keep_box: region (in cut px) to keep (drops stray bits)."""
    a = cut.split()[3]
    m = Image.new('L', cut.size, 0)
    m.paste(a.crop(keep_box), keep_box[:2])
    a = m.point(lambda v: 255 if v > 110 else 0)
    cut = cut.copy(); cut.putalpha(a)
    cut = cut.crop(cut.getbbox())
    cut = cut.resize((round(cut.width * scale), round(cut.height * scale)), Image.LANCZOS)
    pad = outline * 3
    c = Image.new('RGBA', (cut.width + pad * 2, cut.height + pad * 2), (0, 0, 0, 0))
    c.paste(cut, (pad, pad), cut)
    al = c.split()[3]
    ring = al.filter(ImageFilter.MaxFilter(outline * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    shadow = al.filter(ImageFilter.MaxFilter(outline * 2 + 1)).filter(ImageFilter.GaussianBlur(18))
    out = Image.new('RGBA', c.size, (0, 0, 0, 0))
    out.paste(Image.new('RGBA', c.size, (0, 0, 0, 255)), (10, 14), shadow.point(lambda v: v * 0.85))
    out.paste(Image.new('RGBA', c.size, (255, 255, 255, 255)), (0, 0), ring)
    out.alpha_composite(c)
    return out, pad


def spot(bg, c, r, col):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / r
    a = (np.clip(1 - d, 0, 1) ** 2 * 150).astype(np.uint8)
    L = Image.new('RGBA', (W, H), col + (0,)); L.putalpha(Image.fromarray(a))
    bg.alpha_composite(L)


def tape(w, h, angle, seed=3):
    random.seed(seed); np.random.seed(seed)
    base = np.zeros((h, w, 4), np.float32)
    g = 150 + np.random.randn(h, w) * 9
    g += np.linspace(18, -22, h)[:, None]          # sheen top->bottom
    for _ in range(6):                               # creases
        x0 = random.randrange(w); sl = random.uniform(-0.6, 0.6)
        for y in range(h):
            x = int(x0 + sl * y)
            if 0 <= x < w - 3: g[y, x:x + 3] += random.choice([-26, 22])
    for _ in range(40):                              # fibre streaks
        y = random.randrange(h); g[y:y + 1, :] += random.uniform(-14, 14)
    base[..., 0] = g; base[..., 1] = g + 2; base[..., 2] = g + 6; base[..., 3] = 255
    t = Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGBA')
    # torn ends
    m = Image.new('L', (w, h), 255); d = ImageDraw.Draw(m)
    for side in (0, 1):
        pts = []
        for y in range(0, h + 6, 6):
            x = random.randint(0, 9)
            pts.append((x if side == 0 else w - 1 - x, y))
        poly = pts + ([(0, h), (0, 0)] if side == 0 else [(w, h), (w, 0)])
        d.polygon(poly, fill=0)
    t.putalpha(m)
    # edge shading
    edge = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ed = ImageDraw.Draw(edge)
    ed.rectangle([0, 0, w, 3], fill=(255, 255, 255, 70)); ed.rectangle([0, h - 4, w, h], fill=(0, 0, 0, 90))
    t = Image.alpha_composite(t, Image.composite(edge, Image.new('RGBA', (w, h)), m))
    t = t.rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', t.size, (0, 0, 0, 0))
    sh.putalpha(t.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 0.6))
    out = Image.new('RGBA', (t.width + 12, t.height + 12), (0, 0, 0, 0))
    out.alpha_composite(sh, (8, 10)); out.alpha_composite(t, (0, 0))
    return out


def text_layer(txt, font, size, fill, stroke=14, stroke_fill=(0, 0, 0), angle=0, shadow=True, track=0):
    f = ImageFont.truetype(F + font, size)
    # measure with tracking
    widths = [f.getbbox(ch)[2] - f.getbbox(ch)[0] if ch != ' ' else size * 0.25 for ch in txt]
    asc, desc = f.getmetrics()
    tw = int(sum(widths) + track * (len(txt) - 1)) + stroke * 4
    th = asc + desc + stroke * 4
    L = Image.new('RGBA', (tw + 40, th + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    x = stroke * 2 + 20
    for ch, cw in zip(txt, widths):
        d.text((x - f.getbbox(ch)[0], stroke * 2 + 20), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += cw + track
    L = L.crop(L.getbbox())
    if shadow:
        s = Image.new('RGBA', (L.width + 30, L.height + 30), (0, 0, 0, 0))
        sm = Image.new('RGBA', L.size, (0, 0, 0, 255)); s.paste(sm, (14, 16), L.split()[3])
        s = s.filter(ImageFilter.GaussianBlur(5)); s.alpha_composite(L, (0, 0)); L = s
    return L.rotate(angle, expand=True, resample=Image.BICUBIC)


def stamp(txt, size, color=(220, 30, 40), angle=8):
    f = ImageFont.truetype(F + 'Anton-Regular.ttf', size)
    bb = f.getbbox(txt); w, h = bb[2] - bb[0] + size, bb[3] - bb[1] + size * 0.6
    L = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([4, 4, w - 5, h - 5], radius=10, outline=color + (255,), width=max(5, size // 9), fill=(255, 255, 255, 235))
    d.text((size / 2 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), txt, font=f, fill=color + (255,))
    # grunge: knock out specks
    rng = np.random.default_rng(7)
    a = np.asarray(L.split()[3]).astype(np.float32)
    a *= (rng.random(a.shape) > 0.06)
    L.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    return L.rotate(angle, expand=True, resample=Image.BICUBIC)


def load_cut(n):
    im = Image.open(FR + f'mmb_{n}_x4.png').convert('RGBA')
    im.putalpha(Image.open(FR + f'mmb_{n}_x4_mask.png').convert('L'))
    return im


def build_A(out):
    bg = background(FR + 'mmb_226.png')
    spot(bg, (330, 380), 520, (40, 70, 160))
    cut = load_cut('230')
    # keep Mermaid Man only (drop the cave post on the left): x>=880 in x4 coords
    st, pad = sticker(cut, (900, 0, 2560, 1920), scale=0.52)
    # tape over the mouth: mouth ~ (345,282) in 640px frame -> x4*0.47 = *1.88, relative to bbox
    bbox = load_cut('230').split()[3].crop((900, 0, 2560, 1920)).point(lambda v: 255 if v > 110 else 0).getbbox()
    ox, oy = bbox[0] + 900, bbox[1]
    mx = (372 * 4 - ox) * 0.52 + pad; my = (272 * 4 - oy) * 0.52 + pad
    tp = tape(300, 86, angle=-8)
    st.alpha_composite(tp, (int(mx - tp.width / 2), int(my - tp.height / 2)))
    bg.alpha_composite(st, (-70, 18))
    t = text_layer('SILENCED', 'Anton-Regular.ttf', 178, (255, 255, 255), stroke=12, angle=4, track=4)
    bg.alpha_composite(t, (W - t.width - 26, 210))
    s = stamp('2012', 74, angle=-9)
    bg.alpha_composite(s, (W - s.width - 70, 70))
    bg.convert('RGB').save(out, quality=95)


def build_B(out):
    bg = background(FR + 'mmb_226.png', tint=(30, 10, 50))
    spot(bg, (330, 380), 520, (90, 50, 150))
    cut = load_cut('250')
    st, pad = sticker(cut, (820, 0, 2560, 1920), scale=0.47)
    bg.alpha_composite(st, (-60, 30))
    t1 = text_layer("WHO'S", 'Anton-Regular.ttf', 150, (255, 255, 255), stroke=11, angle=4, track=3)
    t2 = text_layer('ERNIE?', 'Anton-Regular.ttf', 196, (255, 214, 0), stroke=13, angle=4, track=3)
    bg.alpha_composite(t1, (W - t1.width - 120, 70))
    bg.alpha_composite(t2, (W - t2.width - 40, 250))
    bg.convert('RGB').save(out, quality=95)


if __name__ == '__main__':
    build_A(sys.argv[1]); build_B(sys.argv[2])
