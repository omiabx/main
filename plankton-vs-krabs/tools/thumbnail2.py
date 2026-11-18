"""Thumbnails in the reference style: one big character cutout (from your own episode frames), clean background
(blurred episode frame or black with glow), 2 lines of huge text. No boxes, no borders.
Inputs: thumb/krabs_cut.png, thumb/plankton_cut.png (background-removed frames), thumb/bg.png (any episode frame).
Run: python3 tools/thumbnail2.py -> output/thumbnail_A.png, output/thumbnail_B.png"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "assets", "fonts")
TW, TH = 1280, 720


def largest_only(im):
    """keep only the biggest connected shape (drops stray bits the cutout picked up)"""
    from scipy import ndimage
    a = np.asarray(im.split()[3]) > 40
    lab, n = ndimage.label(a)
    if n <= 1: return im
    sizes = ndimage.sum(a, lab, range(1, n + 1)); keep = lab == (1 + int(np.argmax(sizes)))
    keep = ndimage.binary_dilation(keep, iterations=2)
    al = np.where(keep, np.asarray(im.split()[3]), 0).astype(np.uint8)
    im = im.copy(); im.putalpha(Image.fromarray(al)); return im


def trim(im):
    im = largest_only(im)
    a = np.asarray(im.split()[3]); a = (a > 40).astype(np.uint8) * 255
    clean = Image.fromarray(a).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    im = im.copy(); im.putalpha(Image.fromarray(np.minimum(np.asarray(im.split()[3]), np.asarray(clean))))
    return im.crop(im.getbbox())


def fit_h(im, h):
    r = h / im.height; return im.resize((int(im.width * r), int(h)), Image.LANCZOS)


def text_block(lines, font_path, fill, stroke, stroke_fill, variation=None, line_gap=-0.05):
    ims = []
    for txt, size in lines:
        f = ImageFont.truetype(font_path, size)
        if variation:
            try: f.set_variation_by_axes(variation)
            except Exception: pass
        bb = f.getbbox(txt, stroke_width=stroke)
        im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        ims.append(im)
    w = max(i.width for i in ims); h = sum(i.height for i in ims) + int(line_gap * sum(i.height for i in ims))
    out = Image.new("RGBA", (w, max(h, 1)), (0, 0, 0, 0)); y = 0
    for i in ims:
        out.alpha_composite(i, ((w - i.width) // 2, y)); y += int(i.height * (1 + line_gap))
    return out


def drop_shadow(im, blur=18, op=170, off=(10, 12)):
    a = im.split()[3].point(lambda v: v * op // 255)
    sh = Image.new("RGBA", (im.width + 4 * blur, im.height + 4 * blur), (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.paste(blk, (2 * blur + off[0], 2 * blur + off[1]), blk)
    sh = sh.filter(ImageFilter.GaussianBlur(blur)); sh.alpha_composite(im, (2 * blur, 2 * blur))
    return sh, 2 * blur


def glow(im, radius=26, strength=2.2, color=(255, 255, 255)):
    a = im.split()[3].filter(ImageFilter.MaxFilter(9))
    pad = radius * 3
    g = Image.new("L", (im.width + 2 * pad, im.height + 2 * pad), 0); g.paste(a, (pad, pad))
    g = g.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
    out = Image.new("RGBA", g.size, color + (0,)); out.putalpha(g)
    out.alpha_composite(im, (pad, pad))
    return out, pad


def variant_a():
    bg = Image.open(os.path.join(ROOT, "thumb", "bg.png")).convert("RGB")
    bg = ImageOps.fit(bg, (TW, TH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(9))
    a = np.asarray(bg).astype(np.float32) * 0.62
    x = np.linspace(-1, 1, TW)[None, :, None]; y = np.linspace(-1, 1, TH)[:, None, None]
    a *= 1 - 0.35 * np.clip(x ** 2 + y ** 2 - .2, 0, None)
    c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    kr = fit_h(trim(Image.open(os.path.join(ROOT, "thumb", "krabs_cut.png")).convert("RGBA")), 700)
    ks, pad = drop_shadow(kr)
    c.alpha_composite(ks, (20 - pad, TH - kr.height + 40 - pad))
    t = text_block([("BEST", 190), ("FRIENDS?", 160)], os.path.join(F, "LilitaOne-Regular.ttf"),
                   (232, 36, 28), 14, (12, 8, 8), line_gap=-0.12)
    ts, tp = drop_shadow(t, 10, 200, (6, 8))
    c.alpha_composite(ts, (TW - t.width - 30 - tp, (TH - t.height) // 2 - 10 - tp))
    return c.convert("RGB")


def variant_b():
    c = Image.new("RGBA", (TW, TH), (0, 0, 0, 255))
    pl = fit_h(trim(Image.open(os.path.join(ROOT, "thumb", "plankton_cut.png")).convert("RGBA")), 690)
    g, pad = glow(pl)
    c.alpha_composite(g, (60 - pad, TH - pl.height + 40 - pad))
    t = text_block([("THE RECIPE", 96), ("WAS HALF HIS", 118)], os.path.join(F, "Fredoka-VF.ttf"),
                   (255, 255, 255), 0, (0, 0, 0), variation=[700, 100], line_gap=0.0)
    c.alpha_composite(t, (max(470, TW - t.width - 40), (TH - t.height) // 2))
    return c.convert("RGB")


def final():
    """one thumbnail: Plankton cutout with white edge glow, blurred dark episode background, red outlined text"""
    bg = Image.open(os.path.join(ROOT, "thumb", "bg.png")).convert("RGB")
    bg = ImageOps.fit(bg, (TW, TH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(10))
    a = np.asarray(bg).astype(np.float32) * 0.55
    x = np.linspace(-1, 1, TW)[None, :, None]; y = np.linspace(-1, 1, TH)[:, None, None]
    a *= 1 - 0.4 * np.clip(x ** 2 + y ** 2 - .2, 0, None)
    c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    pl = fit_h(trim(Image.open(os.path.join(ROOT, "thumb", "plankton_cut.png")).convert("RGBA")), 700)
    g, pad = glow(pl, radius=16, strength=1.6)
    c.alpha_composite(g, (70 - pad, TH - pl.height + 40 - pad))
    t = text_block([("HALF WAS", 170), ("HIS?", 230)], os.path.join(F, "LilitaOne-Regular.ttf"),
                   (232, 36, 28), 14, (12, 8, 8), line_gap=-0.1)
    ts, tp = drop_shadow(t, 10, 200, (6, 8))
    c.alpha_composite(ts, (TW - t.width - 50 - tp, (TH - t.height) // 2 - tp))
    return c.convert("RGB")


def final_duo():
    """Krabs + Plankton cutouts facing each other, blurred dark episode background, red outlined text on top"""
    bg = Image.open(os.path.join(ROOT, "thumb", "bg.png")).convert("RGB")
    bg = ImageOps.fit(bg, (TW, TH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(10))
    a = np.asarray(bg).astype(np.float32) * 0.55
    x = np.linspace(-1, 1, TW)[None, :, None]; y = np.linspace(-1, 1, TH)[:, None, None]
    a *= 1 - 0.4 * np.clip(x ** 2 + y ** 2 - .2, 0, None)
    c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    kr = fit_h(trim(Image.open(os.path.join(ROOT, "thumb", "krabs_cut.png")).convert("RGBA")), 560)
    pl = ImageOps.mirror(fit_h(trim(Image.open(os.path.join(ROOT, "thumb", "plankton_cut.png")).convert("RGBA")), 520))
    gk, pk = glow(kr, radius=14, strength=1.5); gp, pp = glow(pl, radius=14, strength=1.5)
    c.alpha_composite(gk, (20 - pk, TH - kr.height + 30 - pk))
    c.alpha_composite(gp, (TW - pl.width - 70 - pp, TH - pl.height + 30 - pp))
    t = text_block([("RIVALRY", 190)], os.path.join(F, "LilitaOne-Regular.ttf"),
                   (232, 36, 28), 14, (12, 8, 8))
    ts, tp = drop_shadow(t, 10, 200, (6, 8))
    c.alpha_composite(ts, ((TW - t.width) // 2 - tp, 18 - tp))
    return c.convert("RGB")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    T = final_duo(); T.save(os.path.join(ROOT, "output", "thumbnail.png"))
    chk = Image.new("RGB", (290, 180), (255, 255, 255)); chk.paste(T.resize((246, 138), Image.LANCZOS), (22, 21))
    chk.save(os.path.join(ROOT, "output", "thumbnail_mobile_check.png"))
    print("wrote output/thumbnail.png")
    raise SystemExit


if False:
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    T = final(); T.save(os.path.join(ROOT, "output", "thumbnail.png"))
    chk = Image.new("RGB", (290, 180), (255, 255, 255)); chk.paste(T.resize((246, 138), Image.LANCZOS), (22, 21))
    chk.save(os.path.join(ROOT, "output", "thumbnail_mobile_check.png"))
    print("wrote output/thumbnail.png")
    raise SystemExit


if False:
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    A, B = variant_a(), variant_b()
    A.save(os.path.join(ROOT, "output", "thumbnail_A.png")); B.save(os.path.join(ROOT, "output", "thumbnail_B.png"))
    A.save(os.path.join(ROOT, "output", "thumbnail.png"))
    chk = Image.new("RGB", (560, 200), (255, 255, 255))
    for i, im in enumerate((A, B)): chk.paste(im.resize((246, 138), Image.LANCZOS), (20 + i * 270, 40))
    chk.save(os.path.join(ROOT, "output", "thumbnail_mobile_check.png"))
    print("wrote thumbnail_A.png, thumbnail_B.png")
