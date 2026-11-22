"""Thumbnails (1280x720) from the user's frame grabs in frames/.
A: frames/T1.png + "BRAIN / DAMAGE?"      B: frames/T2.png + red circle + "OCT 21, 2005"
If a frame is missing, a grey placeholder shows the layout.
Optional: frames/T1_cut.png / T2_cut.png (transparent cut-outs) are used instead when present.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import gfx  # noqa: E402

ROOT = gfx.ROOT
TW, TH = 1280, 720
RED = (226, 30, 38)


def bg():
    rng = np.random.default_rng(5)
    y = np.linspace(-1, 1, TH)[:, None]
    x = np.linspace(-1, 1, TW)[None, :]
    v = np.clip(1 - 0.6 * (x ** 2 * 0.5 + y ** 2), 0, 1)
    base = np.dstack([v * 34, v * 26, v * 24]) + rng.normal(0, 3, (TH, TW, 1))
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.line([(0, 600), (400, 520), (820, 640), (1280, 470)], fill=(150, 20, 24, 255), width=7, joint="curve")
    return img


def sticker(img, border=14):
    """White sticker outline around a cut-out (alpha) image."""
    a = img.split()[-1]
    grown = a.filter(ImageFilter.MaxFilter(border * 2 + 1))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste((255, 255, 255, 255), (0, 0), grown)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 200), (0, 0), grown.filter(ImageFilter.GaussianBlur(12)))
    res = Image.new("RGBA", img.size, (0, 0, 0, 0))
    res.alpha_composite(sh, (8, 10))
    res.alpha_composite(out)
    res.alpha_composite(img)
    return res


def subject(name, box):
    """Cut-out if available; else the frame grab in a white-bordered tilted card; else placeholder."""
    w, h = box
    cut = os.path.join(ROOT, "frames", name + "_cut.png")
    raw = os.path.join(ROOT, "frames", name + ".png")
    if os.path.exists(cut):
        im = Image.open(cut).convert("RGBA")
        im.thumbnail((w, h), Image.LANCZOS)
        pad = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
        pad.alpha_composite(im, (20, 20))
        return sticker(pad)
    if os.path.exists(raw):
        im = Image.open(raw).convert("RGB")
    else:
        im = gfx.placeholder_clip(w, h, f"{name}.png").convert("RGB")
    im = im.resize((w - 28, h - 28), Image.LANCZOS) if im.size != (w - 28, h - 28) else im
    card = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    card.paste(im, (14, 14))
    return card.rotate(-3, expand=True, resample=Image.BICUBIC)


def word(text, size, fill, stroke=10):
    f = gfx.font("anton", size)
    b = f.getbbox(text, stroke_width=stroke)
    img = Image.new("RGBA", (b[2] - b[0] + 30, b[3] - b[1] + 30), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((15 - b[0], 15 - b[1]), text, font=f, fill=fill, stroke_width=stroke,
                             stroke_fill=(0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 220), (0, 0), img.split()[-1].filter(ImageFilter.GaussianBlur(6)))
    out = Image.new("RGBA", (img.width + 12, img.height + 12), (0, 0, 0, 0))
    out.alpha_composite(sh, (10, 12))
    out.alpha_composite(img)
    return out


def thumb_a():
    t = bg()
    s = subject("T1", (760, 640))
    t.alpha_composite(s, (-10, TH - s.height + 10))
    w1 = word("BRAIN", 210, (255, 255, 255))
    w2 = word("DAMAGE?", 200, RED)
    t.alpha_composite(w1.rotate(4, expand=True, resample=Image.BICUBIC), (TW - w1.width - 30, 40))
    t.alpha_composite(w2.rotate(4, expand=True, resample=Image.BICUBIC), (TW - w2.width - 20, 300))
    return t.convert("RGB")


def thumb_b():
    t = bg()
    s = subject("T2", (820, 660))
    t.alpha_composite(s, (40, TH - s.height + 20))
    circ = gfx.marker_circle((420, 330), 1.0, color=RED, width=16)
    t.alpha_composite(circ, (180, 130))
    small = word("THE DAY IT HAPPENED:", 64, (255, 255, 255), 6)
    t.alpha_composite(small, (TW - small.width - 30, 70))
    f = gfx.font("anton", 112)
    b = f.getbbox("OCT 21, 2005")
    label = Image.new("RGBA", (b[2] - b[0] + 60, b[3] - b[1] + 50), (250, 248, 240, 255))
    ImageDraw.Draw(label).text((30 - b[0], 25 - b[1]), "OCT 21, 2005", font=f, fill=(20, 20, 20))
    label = label.rotate(-5, expand=True, resample=Image.BICUBIC)
    t.alpha_composite(label, (TW - label.width - 40, 190))
    return t.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(ROOT, "out")
    os.makedirs(out, exist_ok=True)
    thumb_a().save(os.path.join(out, "thumbnail_A.png"))
    thumb_b().save(os.path.join(out, "thumbnail_B.png"))
    print("wrote out/thumbnail_A.png, out/thumbnail_B.png")
