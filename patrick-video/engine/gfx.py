"""Original 'case file' graphics primitives (PIL). No show artwork is drawn here."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
FONTS = os.path.join(ROOT, "fonts")
W, H = 1920, 1080

INK = (24, 20, 18)
PAPER = (226, 205, 160)
PAPER_DARK = (196, 170, 120)
RED = (200, 30, 36)
WHITE = (245, 242, 235)
DESK = (22, 20, 19)


def font(name, size):
    files = {
        "anton": "Anton-Regular.ttf",
        "type": "SpecialElite-Regular.ttf",
        "marker": "PermanentMarker-Regular.ttf",
        "oswald": "Oswald.ttf",
    }
    return ImageFont.truetype(os.path.join(FONTS, files[name]), size)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.7):
    x = max(0.0, min(1.0, x))
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def _grain(size, amount, seed):
    rng = np.random.default_rng(seed)
    g = rng.normal(0, amount, (size[1], size[0], 1))
    return g


def desk_background(seed=0):
    """Dark desk with vignette and subtle wood-ish streaks."""
    rng = np.random.default_rng(seed)
    y = np.linspace(-1, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    vign = 1 - 0.55 * (x ** 2 * 0.6 + y ** 2)
    streak = 0.04 * np.sin(y * 90 + np.sin(x * 3) * 2) + 0.03 * np.sin(y * 23)
    base = np.array(DESK, dtype=float)[None, None, :] * (vign[..., None] + streak[..., None])
    base += rng.normal(0, 3, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


def paper_texture(size, seed=1, color=PAPER):
    w, h = size
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3)) * np.array(color, dtype=float)
    blot = Image.fromarray((rng.random((max(2, h // 40), max(2, w // 40))) * 255).astype(np.uint8))
    blot = np.asarray(blot.resize((w, h), Image.BICUBIC), dtype=float)[..., None] / 255
    base *= 0.93 + 0.1 * blot
    base += rng.normal(0, 4, (h, w, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


def drop_shadow(img_rgba, offset=(14, 18), blur=18, opacity=150):
    w, h = img_rgba.size
    pad = blur * 3
    sh = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    alpha = img_rgba.split()[-1].point(lambda a: a * opacity // 255)
    sh.paste((0, 0, 0, 255), (pad, pad), alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (offset[0], offset[1]))
    out.alpha_composite(img_rgba, (pad, pad))
    return out, pad


def folder(label_lines, size=(1300, 820), seed=3):
    """Manila case folder with a tab and typed label."""
    w, h = size
    img = Image.new("RGBA", (w, h + 70), (0, 0, 0, 0))
    tex = paper_texture((w, h + 70), seed)
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 70, w, h + 70), 18, fill=255)
    d.rounded_rectangle((60, 0, 520, 110), 18, fill=255)
    img.paste(tex, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.line((0, 120, w, 120), fill=PAPER_DARK + (255,), width=3)
    # typed label sticker
    lab = Image.new("RGBA", (900, 90 + 62 * (len(label_lines) - 1)), WHITE + (255,))
    ld = ImageDraw.Draw(lab)
    for i, line in enumerate(label_lines):
        ld.text((28, 18 + 62 * i), line, font=font("type", 50), fill=INK)
    lab = lab.rotate(-1.2, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lab, (120, 200))
    return img


def stamp(text, color=RED, size=110, angle=-12, seed=5):
    f = font("anton", size)
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padx, pady = 40, 30
    img = Image.new("RGBA", (tw + padx * 2, th + pady * 2 + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((6, 6, img.width - 6, img.height - 6), 14, outline=color + (255,), width=10)
    d.text((padx - bbox[0], pady - bbox[1] + 8), text, font=f, fill=color + (255,))
    # ink wear: knock out random specks
    rng = np.random.default_rng(seed)
    a = np.asarray(img.split()[-1], dtype=float)
    a *= rng.random(a.shape) > 0.12
    img.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    return img.rotate(angle, expand=True, resample=Image.BICUBIC)


def date_card(date, title, season, progress):
    """Typed date stamp: '10.21.2005 // PATRICK SMARTPANTS // S4'. progress 0..1 types it out."""
    full = f"{date}  //  {title}  //  {season}"
    n = int(round(len(full) * max(0.0, min(1.0, progress))))
    shown = full[:n]
    f = font("type", 64)
    bbox = f.getbbox(full)
    w = bbox[2] - bbox[0] + 80
    img = Image.new("RGBA", (w, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 130), fill=(12, 12, 12, 215))
    d.rectangle((0, 0, 10, 130), fill=RED + (255,))
    d.text((40, 28), shown, font=f, fill=WHITE)
    if progress < 1.0 or (int(progress * 10) % 2 == 0):
        cx = 40 + (f.getlength(shown) if shown else 0) + 6
        d.rectangle((cx, 34, cx + 26, 100), fill=WHITE + (200,))
    return img


def evidence_frame(content, tag, tilt=0.0):
    """Puts a frame (clip still or placeholder) in a white evidence border with a tag."""
    b = 22
    img = Image.new("RGBA", (content.width + b * 2, content.height + b * 2 + 70), WHITE + (255,))
    img.paste(content, (b, b))
    d = ImageDraw.Draw(img)
    d.text((b + 6, content.height + b + 12), tag, font=font("type", 44), fill=INK)
    return img.rotate(tilt, expand=True, resample=Image.BICUBIC)


def placeholder_clip(w=1280, h=720, label="SHOW CLIP"):
    img = Image.new("RGB", (w, h), (52, 56, 62))
    d = ImageDraw.Draw(img)
    for i in range(-h, w, 60):
        d.line((i, 0, i + h, h), fill=(60, 64, 70), width=20)
    f = font("anton", 90)
    tw = f.getlength(label)
    d.text(((w - tw) / 2, h / 2 - 70), label, font=f, fill=(150, 155, 160))
    return img


def marker_circle(size, progress, color=RED, width=12, seed=2):
    """Hand-drawn marker ellipse that draws on over progress 0..1."""
    w, h = size
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    wob = rng.normal(0, 0.025, 8)
    steps = 140
    end = int(steps * 1.12 * ease_out(progress))
    pts = []
    for i in range(end):
        a = -math.pi / 2 + 2 * math.pi * i / steps
        r = 1 + wob[i % 8] * math.sin(i / 9) + 0.03 * i / steps
        pts.append((20 + w / 2 + math.cos(a) * w / 2 * r, 20 + h / 2 + math.sin(a) * h / 2 * r))
    if len(pts) > 1:
        d.line(pts, fill=color + (235,), width=width, joint="curve")
    return img


def brain_monitor(t, level=1.0, label="BRAIN ACTIVITY", flat=False):
    """Corner seismograph. level scales the amplitude; flat draws a flatline."""
    w, h = 420, 150
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w, h), 14, fill=(8, 14, 10, 210), outline=(60, 200, 110, 255), width=3)
    for gx in range(20, w, 40):
        d.line((gx, 34, gx, h - 10), fill=(25, 60, 35, 255))
    d.text((14, 6), label, font=font("oswald", 22), fill=(90, 230, 140))
    pts = []
    for x in range(10, w - 10, 3):
        ph = t * 3.0 - x / 55.0
        if flat:
            y = 0
        else:
            beat = math.exp(-((ph % 1.6) - 0.8) ** 2 * 120) * 34
            y = (beat + 4 * math.sin(ph * 9)) * level
        pts.append((x, h * 0.62 - y))
    d.line(pts, fill=(90, 255, 150, 255), width=3)
    return img


def shake_offset(t, t0, dur=0.12, amp=14):
    if t0 <= t < t0 + dur:
        k = 1 - (t - t0) / dur
        return int(math.sin(t * 190) * amp * k), int(math.cos(t * 160) * amp * k)
    return 0, 0
