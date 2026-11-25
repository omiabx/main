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

def census_form(lines, stamp=None, stamp_p=1.0, typed_p=1.0, title="BIKINI BOTTOM", sub="OFFICIAL CENSUS RECORD"):
    """A typed government form. lines: list of (label, value, strike_value_or_None)."""
    fw, fh = 1100, 820
    im = paper_texture(fw, fh).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle([20, 20, fw - 20, fh - 20], outline=INK, width=4)
    d.text((fw / 2, 85), title, font=font("type", 64), fill=INK, anchor="mm")
    d.text((fw / 2, 150), sub, font=font("type", 40), fill=INK, anchor="mm")
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

# ---------------- channel house style (matched to TheSinistory reference) ----------------
NAVY = (20, 24, 38); CARD = (243, 238, 224); BOARD = (214, 207, 191); PILL = (196, 52, 44)
_navy_cache = {}
def navy_bg(color=NAVY, seed=11):
    if color in _navy_cache: return _navy_cache[color].copy()
    rng = np.random.default_rng(seed)
    a = np.ones((H, W, 3), np.float32) * np.array(color, np.float32)
    a += rng.normal(0, 3.0, (H, W, 1))
    y, x = np.ogrid[:H, :W]; r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a *= np.clip(1.08 - 0.35 * r ** 2, 0.5, 1.1)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); _navy_cache[color] = im
    return im.copy()

def board_bg(): return navy_bg(BOARD, 12)

def drop_shadow(layer, off=(10, 14), blur=14, alpha=150):
    w, h = layer.size; pad = blur * 3
    sh = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    a = layer.getchannel("A").point(lambda v: int(v * alpha / 255))
    blk = Image.new("RGBA", layer.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.paste(blk, (pad + off[0], pad + off[1]), blk); sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(layer, (pad, pad)); return sh

def polaroid(src_img, caption, w=860, pin=True):
    """Pinned instant-photo card: src_img (PIL RGB, any size) cropped 16:10 into it."""
    pw = w; ph_img = int(w * 0.92 * 10 / 16); border = int(w * 0.04)
    ph = ph_img + border + int(w * 0.14)
    card = Image.new("RGBA", (pw, ph), CARD + (255,))
    iw = pw - 2 * border
    s = src_img.copy(); sw, sh_ = s.size; tw = sw; th = int(sw * ph_img / iw)
    if th > sh_: th = sh_; tw = int(th * iw / ph_img)
    s = s.crop(((sw - tw) // 2, (sh_ - th) // 2, (sw - tw) // 2 + tw, (sh_ - th) // 2 + th)).resize((iw, ph_img), Image.BICUBIC)
    card.paste(s, (border, border))
    d = ImageDraw.Draw(card)
    d.text((pw / 2, border + ph_img + (ph - border - ph_img) / 2), caption, font=font("marker", int(w * 0.04)), fill=(30, 28, 26), anchor="mm")
    if pin:
        d.ellipse([pw / 2 - 14, 6, pw / 2 + 14, 34], fill=(200, 30, 30)); d.ellipse([pw / 2 - 6, 12, pw / 2 + 2, 20], fill=(255, 150, 150))
    return drop_shadow(card)

def ep_tag(img, text, alpha=1.0):
    """Bottom-left typewriter episode tag in a dark box."""
    f = font("type", 34); d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), text, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    box = Image.new("RGBA", (tw + 56, th + 40), (22, 22, 26, int(215 * alpha)))
    ImageDraw.Draw(box).text((28, 20 - bb[1]), text, font=f, fill=(240, 236, 226, int(255 * alpha)))
    img.alpha_composite(box, (48, H - 48 - box.size[1]))

def chapter_pill(img, text, p=1.0):
    """Top-left red section pill (slides in)."""
    f = font("anton", 62); d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), text, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    box = Image.new("RGBA", (tw + 64, th + 44), PILL + (255,))
    ImageDraw.Draw(box).text((32, 22 - bb[1]), text, font=f, fill=(255, 255, 255))
    x = int(lerp(-box.size[0], 48, ease_out(p)))
    img.alpha_composite(box, (x, 48)) if x >= 0 else img.paste(box, (x, 48), box)

def paper_card(text, w=520, h=150, size=54, check=False, fnt="type", line=True):
    card = Image.new("RGBA", (w, h), CARD + (255,)); d = ImageDraw.Draw(card)
    if line: d.line([0, int(h * 0.22), w, int(h * 0.22)], fill=(200, 80, 80), width=2)
    d.text((36, h * 0.6), text, font=font(fnt, size), fill=(30, 28, 26), anchor="lm")
    if check:
        d.line([w - 110, h * 0.55, w - 85, h * 0.78, w - 40, h * 0.25], fill=(200, 30, 30), width=9, joint="curve")
    return drop_shadow(card, (6, 9), 10, 120)

def label_box(text, size=96, w=None):
    """Bold Anton label on a cream card (like KRUSTY KRAB / CHUM BUCKET boxes)."""
    f = font("anton", size); d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = d0.textbbox((0, 0), text, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    bw = w or tw + 90; bh = th + 80
    card = Image.new("RGBA", (bw, bh), CARD + (255,)); d = ImageDraw.Draw(card)
    d.rectangle([0, 0, bw - 1, bh - 1], outline=(40, 36, 30), width=3)
    d.text((bw / 2, bh / 2), text, font=f, fill=(25, 22, 20), anchor="mm")
    return drop_shadow(card, (6, 9), 10, 120)

def marker_text(text, size=70, color=(200, 30, 30)):
    return text_layer(text, font("marker", size), fill=color, stroke=0, shadow=0)

def marker_arrow(img, p0, p1, progress=1.0, color=(200, 30, 30), width=8):
    d = ImageDraw.Draw(img); x = lerp(p0[0], p1[0], progress); y = lerp(p0[1], p1[1], progress)
    d.line([p0, (x, y)], fill=color, width=width)
    if progress >= 0.98:
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for s in (-1, 1):
            a = ang + math.pi + s * 0.5
            d.line([(x, y), (x + 34 * math.cos(a), y + 34 * math.sin(a))], fill=color, width=width)
