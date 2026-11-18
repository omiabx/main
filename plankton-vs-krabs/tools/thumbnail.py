"""Thumbnails (1280x720) in the channel's style: one big character with a white sticker outline, 1-3 huge words
(one highlighted), bright background, a red label badge.
Drop in:  thumb/krabs.png     Mr. Krabs, guilty/side-eye (background-removed PNG works best)
          thumb/plankton.png  Plankton, angry/yelling (background-removed PNG works best)
Characters are never drawn here; they are only composited from your frames. Without them, labelled placeholders show the layout.
Run: python3 tools/thumbnail.py -> output/thumbnail_A.png, output/thumbnail_B.png, output/thumbnail_mobile_check.png"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gfx
from gfx import text_img, font, INK, WHITE, YELLOW, RED

TW, TH = 1280, 720


def load(name, size, label):
    p = os.path.join(ROOT, "thumb", name)
    if os.path.exists(p):
        im = Image.open(p).convert("RGBA")
        cut = im.getextrema()[3][0] < 250
        if cut: im.thumbnail(size, Image.LANCZOS)
        else: im = ImageOps.fit(im, size, Image.LANCZOS)
        a = np.asarray(im).astype(np.float32); rgb = a[..., :3]
        rgb = np.clip((rgb - 128) * 1.15 + 132, 0, 255); m = rgb.mean(2, keepdims=True); rgb = np.clip(m + (rgb - m) * 1.3, 0, 255)
        a[..., :3] = rgb; im = Image.fromarray(a.astype(np.uint8))
        if not cut:
            mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], 36, fill=255)
            im.putalpha(mask)
        return im
    w, h = size; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 40, fill=(60, 64, 74, 255))
    t = text_img(label, 46, "cond", (230, 230, 230)); im.paste(t, ((w - t.width) // 2, (h - t.height) // 2), t)
    return im


def sticker(im, px=10):
    a = im.split()[3].filter(ImageFilter.MaxFilter(px * 2 + 1))
    out = Image.new("RGBA", (im.width + 4 * px, im.height + 4 * px), (0, 0, 0, 0))
    wht = Image.new("RGBA", im.size, (255, 255, 255, 255)); wht.putalpha(a)
    out.paste(wht, (2 * px, 2 * px), wht); out.paste(im, (2 * px, 2 * px), im)
    return gfx.shadow(out, 0, 16, 170)


def badge(text, rot=-6):
    t = text_img(text, 40, "cond", (255, 236, 236))
    b = Image.new("RGBA", (t.width + 50, t.height + 22), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle([0, 0, b.width - 1, b.height - 1], 10, fill=(196, 26, 26, 255), outline=(255, 255, 255, 255), width=4)
    b.paste(t, (25, 11), t)
    glow = b.filter(ImageFilter.GaussianBlur(10))
    out = Image.new("RGBA", (b.width + 40, b.height + 40), (0, 0, 0, 0)); out.paste(glow, (20, 20), glow); out.paste(b, (20, 20), b)
    return out.rotate(rot, expand=True, resample=Image.BICUBIC)


def cartoon_text(text, size):
    """chunky cartoon headline: yellow->orange gradient, thick dark outline, drop shadow"""
    f = font(size, "cartoon"); bb = f.getbbox(text)
    w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 60
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).text((30 - bb[0], 30 - bb[1]), text, font=f, fill=255)
    g = np.linspace(0, 1, h)[:, None, None]
    grad = (np.array([255, 226, 60]) * (1 - g) + np.array([246, 120, 20]) * g) * np.ones((h, w, 1))
    fill = Image.fromarray(grad.astype(np.uint8)).convert("RGBA"); fill.putalpha(mask)
    ol = Image.new("RGBA", (w, h), (52, 22, 6, 255)); ol.putalpha(mask.filter(ImageFilter.MaxFilter(19)))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.alpha_composite(ol); out.alpha_composite(fill)
    return gfx.shadow(out, 8, 6, 200)


def condensed_text(lines):
    """stacked condensed caps, white with one highlighted word, black outline"""
    ims = [text_img(t, sz, "cond", col, 9, INK) for t, col, sz in lines]
    w = max(i.width for i in ims); h = sum(i.height for i in ims) - 30 * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in ims: out.paste(i, (0, y), i); y += i.height - 30
    return gfx.shadow(out, 8, 8, 200)


def bg_spotlight():
    y = np.linspace(-1, 1, TH)[:, None, None]; x = np.linspace(-1, 1, TW)[None, :, None]
    a = np.ones((TH, TW, 3), np.float32) * 6
    g = np.exp(-(((x - .42) / .55) ** 2 + ((y - .05) / .75) ** 2))
    a += g * np.array([235, 232, 222], np.float32) * .9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def bg_underwater():
    y = np.linspace(0, 1, TH)[:, None, None]; x = np.linspace(0, 1, TW)[None, :, None]
    a = np.array([60, 190, 240], np.float32) * (1 - y) + np.array([14, 92, 190], np.float32) * y
    rays = np.clip(np.sin(x * 22 + y * 3) * np.sin(x * 9 - 1), 0, None) * (1 - y) * 40
    a = a + rays
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    for _ in range(28):
        cx, cy, r = rng.uniform(0, TW), rng.uniform(0, TH), rng.uniform(6, 22)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(230, 250, 255, 150), width=3)
    return im


def torn_half():
    pw, ph = 250, 320
    p = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    pts = [(0, 0), (pw - 30, 0)] + [(pw - 30 + (22 if i % 2 else -10), y) for i, y in enumerate(range(20, ph, 24))] + [(pw - 30, ph), (0, ph)]
    d.polygon(pts, fill=(246, 240, 224, 255))
    for y in range(80, ph - 30, 32): d.rectangle([22, y, 22 + (120 if y % 64 else 160), y + 10], fill=(90, 80, 70, 255))
    t = text_img("SECRET", 46, "cond", INK); p.paste(t, (18, 14), t)
    return sticker(p.rotate(-10, expand=True, resample=Image.BICUBIC), 6)


def variant_a():
    """condensed headline + spotlight (like the channel's 'removed' style)"""
    c = bg_spotlight()
    kr = sticker(load("krabs.png", (640, 640), "MR. KRABS\nguilty / side-eye"), 10)
    c.alpha_composite(kr, (TW - kr.width + 40, TH - kr.height + 70))
    pl = sticker(load("plankton.png", (230, 230), "PLANKTON\nangry"), 8)
    c.alpha_composite(pl, (330, 440))
    c.alpha_composite(torn_half(), (560, 360))
    head = condensed_text([("HALF", WHITE, 175), ("WAS", WHITE, 175), ("HIS.", YELLOW, 190)])
    c.alpha_composite(head, (24, max(-10, (TH - head.height) // 2 - 10)))
    b = badge("FRIEND OR FOE · 2007", -5); c.alpha_composite(b, (TW - b.width - 30, 18))
    return c


def variant_b():
    """cartoon gradient headline on bright underwater"""
    c = bg_underwater()
    kr = sticker(load("krabs.png", (620, 620), "MR. KRABS\nguilty / side-eye"), 10)
    c.alpha_composite(kr, (-30, TH - kr.height + 60))
    pl = sticker(load("plankton.png", (260, 260), "PLANKTON\nangry"), 8)
    c.alpha_composite(pl, (TW - pl.width + 10, TH - pl.height + 10))
    c.alpha_composite(torn_half(), (640, 380))
    t1 = cartoon_text("STOLEN", 170); t2 = cartoon_text("RECIPE?!", 150)
    c.alpha_composite(t1.rotate(-4, expand=True, resample=Image.BICUBIC), (560, -10))
    c.alpha_composite(t2.rotate(-4, expand=True, resample=Image.BICUBIC), (540, 160))
    return c


def build():
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    A, B = variant_a().convert("RGB"), variant_b().convert("RGB")
    A.save(os.path.join(ROOT, "output", "thumbnail_A.png")); B.save(os.path.join(ROOT, "output", "thumbnail_B.png"))
    A.save(os.path.join(ROOT, "output", "thumbnail.png"))
    chk = Image.new("RGB", (560, 330), WHITE); d = ImageDraw.Draw(chk)
    for i, im in enumerate((A, B)):
        chk.paste(im.resize((246, 138), Image.LANCZOS), (20 + i * 270, 60))
        d.text((20 + i * 270, 210), "AB"[i], fill=INK, font=font(40, "cond"))
    d.text((20, 15), "phone-feed size (246x138)", fill=INK, font=font(30, "cond"))
    chk.save(os.path.join(ROOT, "output", "thumbnail_mobile_check.png"))
    print("wrote thumbnail_A.png, thumbnail_B.png, thumbnail_mobile_check.png")


if __name__ == "__main__":
    build()
