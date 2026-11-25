"""Add a cartoon odometer counter (spinning, motion-blurred digits) to the AI thumbnail base."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import font

BASE = sys.argv[1]; OUT = sys.argv[2]
S = 2  # supersample

def vblur(img, length):
    """Vertical motion blur (box kernel)."""
    if length <= 1: return img
    a = np.asarray(img).astype(np.float32)
    k = int(length); pad = k // 2
    p = np.pad(a, ((pad, pad), (0, 0), (0, 0)), mode="edge")
    c = np.cumsum(p, axis=0); c = np.concatenate([np.zeros((1,) + c.shape[1:]), c], 0)
    out = (c[k:] - c[:-k]) / k
    return Image.fromarray(np.clip(out[: a.shape[0]], 0, 255).astype(np.uint8), img.mode)

def wheel(w, h, digit, blur):
    """One odometer wheel: a vertical strip of digits, cropped to the window and motion-blurred."""
    strip_h = h * 3
    strip = Image.new("RGBA", (w, strip_h), (246, 240, 226, 255)); d = ImageDraw.Draw(strip)
    f = font("anton", int(h * 0.78))
    for k, dd in enumerate([(digit + 1) % 10, digit, (digit - 1) % 10]):
        d.text((w / 2, h * k + h / 2), str(dd), font=f, fill=(22, 20, 24), anchor="mm")
    strip = vblur(strip, blur)
    win = strip.crop((0, h, w, 2 * h))
    # cylinder shading: darker at top and bottom
    sh = np.linspace(-1, 1, h); sh = (1 - 0.55 * sh ** 2)[:, None, None]
    a = np.asarray(win).astype(np.float32); a[..., :3] *= sh
    win = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], int(10 * S), fill=255)
    win.putalpha(m); return win

def counter(W=640, H=250):
    W, H = W * S, H * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ol = 9 * S
    # body: black outline, red bezel, dark screen
    d.rounded_rectangle([0, 52 * S, W - 1, H - 1], 30 * S, fill=(18, 18, 22))
    d.rounded_rectangle([ol, 52 * S + ol, W - 1 - ol, H - 1 - ol], 24 * S, fill=(214, 38, 38))
    sx0, sy0, sx1, sy1 = 34 * S, 52 * S + 34 * S, W - 34 * S, H - 30 * S
    d.rounded_rectangle([sx0 - 5 * S, sy0 - 5 * S, sx1 + 5 * S, sy1 + 5 * S], 16 * S, fill=(18, 18, 22))
    d.rounded_rectangle([sx0, sy0, sx1, sy1], 12 * S, fill=(34, 36, 46))
    # wheels: 6 digits with a comma, blur increasing to the right
    digits = [4, 6, 8, 5, 3, 9]; blurs = [70, 95, 125, 150, 175, 200]
    n = 6; gap = 10 * S; comma_w = 26 * S
    ww = int((sx1 - sx0 - 2 * gap - (n - 1) * gap - comma_w) / n); wh = sy1 - sy0 - 2 * gap
    x = sx0 + gap
    for i in range(n):
        im.alpha_composite(wheel(ww, wh, digits[i], blurs[i] * S // 2), (int(x), int(sy0 + gap)))
        x += ww + gap
        if i == 2:
            d.text((x + comma_w / 2 - gap / 2, sy1 - 18 * S), ",", font=font("anton", 70 * S), fill=(246, 240, 226), anchor="ms")
            x += comma_w
    # glossy highlight on the screen
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.rounded_rectangle([sx0, sy0, sx1, sy0 + (sy1 - sy0) * 0.38], 12 * S, fill=(255, 255, 255, 38))
    im.alpha_composite(gl)
    # label plate on top
    f = font("anton", 46 * S); lbl = "POPULATION"
    bb = d.textbbox((0, 0), lbl, font=f); lw = bb[2] - bb[0] + 60 * S; lh = 70 * S
    lx0 = (W - lw) / 2
    d.rounded_rectangle([lx0, 6 * S, lx0 + lw, 6 * S + lh], 14 * S, fill=(18, 18, 22))
    d.rounded_rectangle([lx0 + 6 * S, 12 * S, lx0 + lw - 6 * S, lh], 10 * S, fill=(255, 210, 40))
    d.text((W / 2, 6 * S + lh / 2 + 2 * S), lbl, font=f, fill=(18, 18, 22), anchor="mm")
    return im

def speed_lines(canvas, box):
    """Cartoon whoosh arcs on both sides of the counter."""
    d = ImageDraw.Draw(canvas); x0, y0, x1, y1 = box; cy = (y0 + y1) / 2 + 20 * S
    for side in (-1, 1):
        for k, (r, a0, a1) in enumerate([(70, 140, 220), (100, 150, 210), (130, 160, 200)]):
            cx = (x0 - 10 * S) if side < 0 else (x1 + 10 * S)
            rr = r * S
            bbox = [cx - rr, cy - rr, cx + rr, cy + rr]
            if side < 0: d.arc(bbox, a0, a1, fill=(255, 255, 255, 230), width=7 * S)
            else: d.arc(bbox, (a0 + 180) % 360, (a1 + 180) % 360, fill=(255, 255, 255, 230), width=7 * S)

def main():
    base = Image.open(BASE).convert("RGB")
    bw, bh = base.size
    big = base.resize((bw * S, bh * S), Image.LANCZOS).convert("RGBA")
    c = counter()
    cw, ch = c.size
    x = (bw * S - cw) // 2; y = 6 * S
    # soft shadow
    sh = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sm = Image.new("RGBA", c.size, (0, 0, 0, 150)); sm.putalpha(c.getchannel("A").point(lambda v: int(v * 0.55)))
    sh.paste(sm, (x + 10 * S, y + 16 * S), sm); sh = sh.filter(ImageFilter.GaussianBlur(14 * S))
    big.alpha_composite(sh)
    speed_lines(big, (x, y + 52 * S, x + cw, y + ch))
    big.alpha_composite(c, (x, y))
    out = big.resize((bw, bh), Image.LANCZOS).convert("RGB")
    # final 1280x720 (crop the slight extra width, then scale)
    tw = int(bh * 16 / 9); out = out.crop(((bw - tw) // 2, 0, (bw - tw) // 2 + tw, bh)).resize((1280, 720), Image.LANCZOS)
    out.save(OUT, quality=92); print(OUT, os.path.getsize(OUT))

main()
