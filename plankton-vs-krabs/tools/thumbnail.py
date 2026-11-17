"""Thumbnail compositor (1280x720).
Drop in:  thumb/krabs.png     a Mr. Krabs frame from the show (guilty/side-eye expression), ideally a cutout PNG
          thumb/plankton.png  a small Plankton frame (angry, pointing / yelling), ideally a cutout PNG
Without them, labelled placeholders show the layout. Characters are never drawn here, only composited from your frames.
Run: python3 tools/thumbnail.py  ->  output/thumbnail.png (+ output/thumbnail_mobile_check.png)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gfx
from gfx import text_img, KRABS, PLANK, YELLOW, INK, WHITE, PAPER

TW, TH = 1280, 720


def bg():
    y = np.linspace(0, 1, TH)[:, None, None]; x = np.linspace(0, 1, TW)[None, :, None]
    left = np.array([120, 14, 10], np.float32); right = np.array([6, 40, 20], np.float32)
    a = left * (1 - x) + right * x
    a = a * (1 - 0.45 * ((x - .5) ** 2 * 2 + (y - .45) ** 2 * 2.2))
    # hot rim glow behind Krabs
    g = np.exp(-(((x - .27) / .25) ** 2 + ((y - .55) / .45) ** 2))
    a += g * np.array([255, 70, 40], np.float32) * .35
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def load(name, box, label, col):
    p = os.path.join(ROOT, "thumb", name)
    w, h = box
    if os.path.exists(p):
        im = Image.open(p).convert("RGBA")
        if im.getextrema()[3][0] == 255:  # opaque frame: soft fade edges
            im = ImageOps.fit(im, (w, h), Image.LANCZOS)
            m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([18, 18, w - 18, h - 18], 40, fill=255)
            im.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
        else:
            im.thumbnail((w, h), Image.LANCZOS)
        # punchy grade
        rgb = im.convert("RGB"); a = np.asarray(rgb).astype(np.float32)
        a = np.clip((a - 128) * 1.18 + 128 + 6, 0, 255); s = a.mean(2, keepdims=True); a = np.clip(s + (a - s) * 1.25, 0, 255)
        out = Image.fromarray(a.astype(np.uint8)).convert("RGBA"); out.putalpha(im.split()[3]); return out
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 30, fill=(30, 30, 34, 235), outline=col + (255,), width=6)
    t = text_img(label, 40, "black", WHITE); im.paste(t, ((w - t.width) // 2, (h - t.height) // 2), t)
    return im


def outline(im, px=8, col=WHITE):
    a = im.split()[3].filter(ImageFilter.MaxFilter(px * 2 + 1))
    o = Image.new("RGBA", im.size, col + (255,)); o.putalpha(a)
    o.paste(im, (0, 0), im); return o


def torn_half():
    pw, ph = 230, 300
    p = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    pts = [(0, 0), (pw - 30, 0)] + [(pw - 30 + (22 if i % 2 else -10), y) for i, y in enumerate(range(20, ph, 24))] + [(pw - 30, ph), (0, ph)]
    d.polygon(pts, fill=PAPER + (255,))
    for y in range(70, ph - 30, 30): d.rectangle([22, y, 22 + (120 if y % 60 else 160), y + 10], fill=(90, 80, 70, 255))
    t = text_img("SECRET", 34, "black", INK); p.paste(t, (20, 18), t)
    return p.rotate(-12, expand=True, resample=Image.BICUBIC)


def build():
    c = bg().convert("RGBA")
    # Krabs big, left
    kr = load("krabs.png", (700, 700), "MR. KRABS\n(guilty side-eye)\nthumb/krabs.png", KRABS)
    c.alpha_composite(gfx.shadow(outline(kr, 6), 0, 18, 200), (-40, 30))
    # torn recipe half held between them
    th = outline(torn_half(), 5, INK)
    c.alpha_composite(gfx.shadow(th, 8, 10, 160), (560, 300))
    # Plankton small, right, in a magnifier ring (ties to the "sesame seed" joke)
    pl = load("plankton.png", (300, 300), "PLANKTON\n(angry)", PLANK)
    ring = Image.new("RGBA", (380, 380), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    rd.ellipse([10, 10, 370, 370], fill=(255, 255, 255, 40))
    m = Image.new("L", (380, 380), 0); ImageDraw.Draw(m).ellipse([22, 22, 358, 358], fill=255)
    inner = Image.new("RGBA", (380, 380), (0, 0, 0, 0)); inner.alpha_composite(pl, ((380 - pl.width) // 2, (380 - pl.height) // 2))
    inner.putalpha(Image.fromarray(np.minimum(np.asarray(inner.split()[3]), np.asarray(m))))
    ring.alpha_composite(inner)
    rd.ellipse([10, 10, 370, 370], outline=INK + (255,), width=22); rd.ellipse([16, 16, 364, 364], outline=WHITE + (255,), width=6)
    handle = Image.new("RGBA", (380, 380), (0, 0, 0, 0))
    c.alpha_composite(gfx.shadow(ring, 8, 14, 170), (850, 300))
    hd = ImageDraw.Draw(c); hd.line([1100, 640, 1230, 740], fill=INK, width=40)
    # headline
    head = gfx.shadow(text_img("HALF WAS\nHIS.", 128, "black", YELLOW, 11, INK), 10, 12, 200).rotate(3, expand=True, resample=Image.BICUBIC)
    c.alpha_composite(head, (TW - head.width + 10, -20))
    # red arrow from text to the torn paper
    ad = ImageDraw.Draw(c)
    ad.line([(860, 330), (790, 400)], fill=KRABS, width=22)
    ad.polygon([(760, 432), (825, 410), (780, 365)], fill=KRABS)
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    out = os.path.join(ROOT, "output", "thumbnail.png")
    c.convert("RGB").save(out)
    # mobile legibility check: how it looks at the size of a phone feed
    sm = c.convert("RGB").resize((246, 138), Image.LANCZOS)
    chk = Image.new("RGB", (560, 220), (255, 255, 255)); chk.paste(sm, (20, 40))
    d = ImageDraw.Draw(chk); d.text((280, 60), "phone-feed size\n(246x138)", fill=INK, font=gfx.font(26, "bold"))
    chk.save(os.path.join(ROOT, "output", "thumbnail_mobile_check.png"))
    print("wrote", out)


if __name__ == "__main__":
    build()
