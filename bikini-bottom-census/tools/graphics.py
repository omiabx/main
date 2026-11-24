"""Reusable motion-graphics pieces for the Bikini Bottom census video."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import (W, H, font, text_layer, paste_scaled, pop_in, ease_out, ease_in_out, back_out, clamp, lerp,
                    marker_circle)

RED = (226, 35, 35); YEL = (255, 214, 0); WHITE = (255, 255, 255); BLACK = (0, 0, 0)
PAPER = (238, 228, 200); INK = (40, 36, 30)

def paper_texture(w, h, seed=3):
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(PAPER, np.float32)
    n = rng.normal(0, 7, (h // 4 + 1, w // 4 + 1, 1)).repeat(4, 0).repeat(4, 1)[:h, :w]
    fib = rng.normal(0, 3, (h, w, 1))
    img = np.clip(base + n + fib, 0, 255).astype(np.uint8)
    im = Image.fromarray(img).filter(ImageFilter.GaussianBlur(0.6))
    return im

def sign_icon(scale=1.0, number="538"):
    """Small wooden 'Welcome to Bikini Bottom' sign, drawn (not traced from the show)."""
    w, h = int(150 * scale), int(130 * scale)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    post = (110, 78, 45)
    d.rectangle([w * 0.28, h * 0.55, w * 0.34, h], fill=post); d.rectangle([w * 0.66, h * 0.55, w * 0.72, h], fill=post)
    d.rounded_rectangle([2, 2, w - 3, h * 0.66], radius=int(8 * scale), fill=(196, 160, 112), outline=(70, 48, 25), width=max(2, int(4 * scale)))
    f1 = font("lucky", int(26 * scale)); f2 = font("anton", int(22 * scale))
    d.text((w / 2, h * 0.2), "BIKINI BOTTOM", font=font("lucky", int(19 * scale)), fill=(200, 30, 30), anchor="mm")
    d.text((w / 2, h * 0.47), f"POP. {number}", font=f2, fill=(40, 30, 20), anchor="mm")
    return im

def big_number(txt, size=200, fill=WHITE, stroke=14):
    return text_layer(txt, font("anton", size), fill=fill, stroke=stroke, shadow=10)

def label(txt, size=70, fill=WHITE, fnt="anton", stroke=8):
    return text_layer(txt, font(fnt, size), fill=fill, stroke=stroke, shadow=6)

def census_form(lines, stamp=None, stamp_p=1.0, typed_p=1.0):
    """A typed government form. lines: list of (label, value, strike_value_or_None)."""
    fw, fh = 1100, 820
    im = paper_texture(fw, fh).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle([20, 20, fw - 20, fh - 20], outline=INK, width=4)
    d.text((fw / 2, 85), "BIKINI BOTTOM", font=font("type", 64), fill=INK, anchor="mm")
    d.text((fw / 2, 150), "OFFICIAL CENSUS RECORD", font=font("type", 40), fill=INK, anchor="mm")
    d.line([60, 195, fw - 60, 195], fill=INK, width=3)
    total = sum(len(a) + len(b) for a, b, _ in lines); shown = int(total * typed_p); used = 0
    y = 260
    for lab, val, strike in lines:
        s = lab[: max(0, shown - used)]; used += len(lab)
        d.text((70, y), s, font=font("type", 46), fill=INK)
        v = val[: max(0, shown - used)]; used += len(val)
        vx = 430
        if strike and v:
            d.text((vx, y), strike, font=font("type", 52), fill=INK)
            bb = d.textbbox((vx, y), strike, font=font("type", 52))
            d.line([bb[0] - 6, (bb[1] + bb[3]) / 2, bb[2] + 6, (bb[1] + bb[3]) / 2], fill=RED, width=7)
            vx = bb[2] + 30
        d.text((vx, y), v, font=font("marker", 60) if strike else font("type", 44), fill=(30, 60, 160) if strike else INK)
        y += 120
    if stamp and stamp_p > 0:
        st = Image.new("RGBA", (620, 170), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 614, 164], radius=18, outline=RED + (220,), width=10)
        sd.text((310, 85), stamp, font=font("anton", 92), fill=RED + (220,), anchor="mm")
        sc = lerp(2.2, 1.0, ease_out(stamp_p / 0.6)) if stamp_p < 0.6 else 1.0
        paste_scaled(im, st, fw * 0.62, fh * 0.80, scale=sc, rot=-12, alpha=clamp(stamp_p * 3))
    return im

def time_card(txt, bg):
    """Full-frame card with big bouncy yellow text over a blurred, darkened background frame."""
    from engine import frame_fill
    b = frame_fill(bg, 1.0, sharpen=False).filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55)).convert("RGBA")
    t = text_layer(txt, font("lucky", 150), fill=YEL, stroke=14, shadow=12, spacing=10)
    return b, t

def red_x(img, cx, cy, size, p, width=26):
    d = ImageDraw.Draw(img)
    a = clamp(p * 2); b = clamp(p * 2 - 1)
    if a > 0: d.line([cx - size, cy - size, lerp(cx - size, cx + size, a), lerp(cy - size, cy + size, a)], fill=RED, width=width)
    if b > 0: d.line([cx + size, cy - size, lerp(cx + size, cx - size, b), lerp(cy - size, cy + size, b)], fill=RED, width=width)

def dot(img, x, y, r=13, scale=1.0):
    d = ImageDraw.Draw(img); r = r * scale
    d.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=WHITE)
    d.ellipse([x - r, y - r, x + r, y + r], fill=RED)
