"""Counter look variations on the same thumbnail base."""
import sys, os, math, importlib.util
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import font

S = 2
BASE = sys.argv[1]; OUTDIR = sys.argv[2]

def load_odometer():
    sys.argv_backup = sys.argv
    spec = importlib.util.spec_from_file_location("tc", os.path.join(os.path.dirname(__file__), "thumb_counter.py"))
    src = open(spec.origin).read().replace("\nmain()\n", "\n")
    ns = {"__file__": spec.origin, "__name__": "tc"}
    sys.argv = ["x", BASE, "/dev/null"]; exec(compile(src, spec.origin, "exec"), ns); sys.argv = sys.argv_backup
    return ns

TC = load_odometer()
vblur = TC["vblur"]

def hblur(img, length):
    return vblur(img.transpose(Image.Transpose.ROTATE_90), length).transpose(Image.Transpose.ROTATE_270)

def outline_body(W, H, top, fill, bezel=None, r=30):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); ol = 9 * S
    d.rounded_rectangle([0, top, W - 1, H - 1], r * S, fill=(18, 18, 22))
    d.rounded_rectangle([ol, top + ol, W - 1 - ol, H - 1 - ol], (r - 6) * S, fill=bezel or fill)
    return im, d

def label_plate(im, text, bg=(255, 210, 40), fg=(18, 18, 22), y=6, fnt="anton", size=46):
    d = ImageDraw.Draw(im); W = im.size[0]
    f = font(fnt, size * S); bb = d.textbbox((0, 0), text, font=f); lw = bb[2] - bb[0] + 60 * S; lh = 70 * S; lx0 = (W - lw) / 2
    d.rounded_rectangle([lx0, y * S, lx0 + lw, y * S + lh], 14 * S, fill=(18, 18, 22))
    d.rounded_rectangle([lx0 + 6 * S, (y + 6) * S, lx0 + lw - 6 * S, (y - 6) * S + lh], 10 * S, fill=bg)
    d.text((W / 2, y * S + lh / 2 + 2 * S), text, font=f, fill=fg, anchor="mm")

# ---------- B: stadium LED scoreboard ----------
SEG = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
def seven_seg(d, x, y, w, h, digit, color, t):
    pts = {"a": (x + t, y, x + w - t, y + t), "g": (x + t, y + h / 2 - t / 2, x + w - t, y + h / 2 + t / 2), "d": (x + t, y + h - t, x + w - t, y + h),
           "f": (x, y + t, x + t, y + h / 2 - t / 2), "b": (x + w - t, y + t, x + w, y + h / 2 - t / 2),
           "e": (x, y + h / 2 + t / 2, x + t, y + h - t), "c": (x + w - t, y + h / 2 + t / 2, x + w, y + h - t)}
    for sname in SEG[digit]:
        d.rounded_rectangle(pts[sname], int(t / 2), fill=color)

def led(W=660, H=250):
    W, H = W * S, H * S; top = 52 * S
    im, d = outline_body(W, H, top, (70, 74, 86), bezel=(110, 116, 130))
    sx0, sy0, sx1, sy1 = 30 * S, top + 30 * S, W - 30 * S, H - 28 * S
    d.rounded_rectangle([sx0, sy0, sx1, sy1], 12 * S, fill=(10, 10, 12))
    # dot grid texture
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(grid)
    for yy in range(int(sy0) + 6 * S, int(sy1), 9 * S):
        for xx in range(int(sx0) + 6 * S, int(sx1), 9 * S):
            gd.ellipse([xx, yy, xx + 3 * S, yy + 3 * S], fill=(40, 20, 20, 255))
    im.alpha_composite(grid)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gdr = ImageDraw.Draw(glow)
    n = 6; pad = 22 * S; comma = 24 * S; dw = (sx1 - sx0 - 2 * pad - comma - (n - 1) * 16 * S) / n; dh = sy1 - sy0 - 40 * S
    rng = np.random.default_rng(3); x = sx0 + pad
    for i in range(n):
        # ghost several digits on top of each other = flickering too fast to read
        seven_seg(d, x, sy0 + 20 * S, dw, dh, 8, (48, 18, 16), 13 * S)          # unlit segments
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        a, b = rng.choice(10, 2, replace=False)
        off = [0.10, 0.18, 0.26, 0.34, 0.42, 0.5][i] * dh                   # faster on the right
        seven_seg(ld, x, sy0 + 20 * S - off, dw, dh, int(a), (255, 150, 60, 255), 13 * S)
        seven_seg(ld, x, sy0 + 20 * S + dh - off + 14 * S, dw, dh, int(b), (255, 150, 60, 255), 13 * S)
        layer = vblur(layer, int((14 + 9 * i) * S))
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([x - 4 * S, sy0 + 12 * S, x + dw + 4 * S, sy1 - 12 * S], fill=255)
        layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.getchannel("A")), np.asarray(m))))
        glow.alpha_composite(layer)
        x += dw + 16 * S
        if i == 2:
            gdr.ellipse([x - 4 * S, sy1 - 34 * S, x + 10 * S, sy1 - 20 * S], fill=(255, 60, 30, 255)); x += comma
    bloom = glow.filter(ImageFilter.GaussianBlur(10 * S))
    bright = Image.fromarray(np.clip(np.asarray(glow).astype(np.int32) * np.array([1, 1, 1, 4]), 0, 255).astype(np.uint8), 'RGBA')
    big_bloom = bright.filter(ImageFilter.GaussianBlur(18 * S))
    base = np.asarray(im).astype(np.float32)
    for L, g in ((big_bloom, 1.4), (bloom, 1.2), (bright, 1.0)):
        a = np.asarray(L).astype(np.float32); al = a[..., 3:4] / 255 * g
        base[..., :3] = base[..., :3] + a[..., :3] * al          # additive glow
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), 'RGBA')
    label_plate(im, "POPULATION", bg=(255, 70, 40), fg=(255, 255, 255))
    return im

# ---------- C: split-flap board ----------
def flap(w, h, digit, blur, bg=(36, 38, 44), fg=(245, 245, 240), flapc=(70, 72, 80, 150)):
    strip = Image.new("RGBA", (w, h * 3), bg + (255,)); d = ImageDraw.Draw(strip)
    f = font("oswald", int(h * 0.8))
    for k, dd in enumerate([(digit + 3) % 10, digit, (digit + 7) % 10]):
        d.text((w / 2, h * k + h / 2), str(dd), font=f, fill=fg, anchor="mm")
    strip = vblur(strip, blur); win = strip.crop((0, h, w, 2 * h)); d = ImageDraw.Draw(win)
    d.line([0, h / 2, w, h / 2], fill=(10, 10, 12), width=4 * S)                       # split line
    d.rectangle([0, h / 2 - 2 * S, 5 * S, h / 2 + 2 * S], fill=(120, 120, 120)); d.rectangle([w - 5 * S, h / 2 - 2 * S, w, h / 2 + 2 * S], fill=(120, 120, 120))
    # a flap caught mid-flip: lighter skewed panel over the top half
    fl = Image.new("RGBA", (w, h), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl)
    fd.polygon([(6 * S, h * 0.12), (w - 6 * S, h * 0.12), (w - 2 * S, h / 2 - 2 * S), (2 * S, h / 2 - 2 * S)], fill=flapc)
    win.alpha_composite(fl)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 8 * S, fill=255); win.putalpha(m)
    return win

def splitflap(W=660, H=250):
    W, H = W * S, H * S; top = 52 * S
    im, d = outline_body(W, H, top, (28, 30, 36), bezel=(52, 56, 66))
    sx0, sy0, sx1, sy1 = 28 * S, top + 28 * S, W - 28 * S, H - 26 * S
    n = 6; gap = 10 * S; comma = 22 * S; fw = int((sx1 - sx0 - (n + 1) * gap - comma) / n); fh = int(sy1 - sy0)
    digits = [4, 6, 8, 5, 3, 9]; blurs = [60, 90, 120, 150, 175, 200]; x = sx0 + gap
    for i in range(n):
        im.alpha_composite(flap(fw, fh, digits[i], blurs[i] * S // 2), (int(x), int(sy0)))
        x += fw + gap
        if i == 2:
            d.text((x + comma / 2 - gap / 2, sy1 - 14 * S), ",", font=font("oswald", 70 * S), fill=(245, 245, 240), anchor="ms"); x += comma
    label_plate(im, "POPULATION", bg=(245, 245, 240), fg=(18, 18, 22))
    return im

# ---------- D: wooden town sign ----------
def wood_sign(W=720, H=290):
    W, H = W * S, H * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); ol = 9 * S
    planks = [(0, 0, W, int(H * 0.36)), (int(W * 0.02), int(H * 0.34), int(W * 0.98), int(H * 1.0))]
    rng = np.random.default_rng(8)
    for i, (x0, y0, x1, y1) in enumerate(planks):
        d.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], 16 * S, fill=(18, 18, 22))
        d.rounded_rectangle([x0 + ol, y0 + ol, x1 - 1 - ol, y1 - 1 - ol], 12 * S, fill=(205, 162, 104))
        for k in range(7):  # wood grain
            yy = rng.uniform(y0 + 20 * S, y1 - 20 * S); xa = rng.uniform(x0 + 30 * S, x1 - 260 * S)
            d.line([xa, yy, xa + rng.uniform(120, 260) * S, yy + rng.uniform(-4, 4) * S], fill=(168, 124, 72), width=4 * S)
        for xx in (x0 + 28 * S, x1 - 28 * S):  # nails
            d.ellipse([xx - 8 * S, (y0 + y1) / 2 - 8 * S, xx + 8 * S, (y0 + y1) / 2 + 8 * S], fill=(90, 80, 70))
    d.text((W / 2, H * 0.18), "BIKINI BOTTOM", font=font("lucky", 58 * S), fill=(200, 30, 30), anchor="mm")
    d.text((W * 0.06, H * 0.68), "POPULATION:", font=font("lucky", 46 * S), fill=(40, 28, 20), anchor="lm")
    # digits being rewritten nonstop: several numbers smeared together sideways
    num = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nd = ImageDraw.Draw(num)
    for k, txt in enumerate(["46,853", "538,000", "50,000"]):
        nd.text((W * 0.735 + (k - 1) * 10 * S, H * 0.68 + (k - 1) * 4 * S), txt, font=font("anton", 100 * S), fill=(30, 22, 18, [255, 150, 110][k]), anchor="mm")
    num = hblur(num, 26 * S)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([int(W * 0.02) + ol, int(H * 0.34) + ol, int(W * 0.98) - ol, H - ol], 12 * S, fill=255)
    num.putalpha(Image.fromarray(np.minimum(np.asarray(num.getchannel("A")), np.asarray(m))))
    im.alpha_composite(num)
    # chalk scribble marks
    return im

def compose(counter_img, out_path, top_y=6, lines=True):
    base = Image.open(BASE).convert("RGB"); bw, bh = base.size
    big = base.resize((bw * S, bh * S), Image.LANCZOS).convert("RGBA")
    c = counter_img; cw, ch = c.size; x = (bw * S - cw) // 2; y = top_y * S
    sh = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sm = Image.new("RGBA", c.size, (0, 0, 0, 150)); sm.putalpha(c.getchannel("A").point(lambda v: int(v * 0.55)))
    sh.paste(sm, (x + 10 * S, y + 16 * S), sm); sh = sh.filter(ImageFilter.GaussianBlur(14 * S)); big.alpha_composite(sh)
    if lines: TC["speed_lines"](big, (x, y + 52 * S, x + cw, y + ch))
    big.alpha_composite(c, (x, y))
    out = big.resize((bw, bh), Image.LANCZOS).convert("RGB")
    tw = int(bh * 16 / 9); out = out.crop(((bw - tw) // 2, 0, (bw - tw) // 2 + tw, bh)).resize((1280, 720), Image.LANCZOS)
    out.save(out_path, quality=92); return out

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    outs = [("A_odometer", TC["counter"](), True), ("B_led_scoreboard", led(), True), ("C_split_flap", splitflap(), True), ("D_wooden_sign", wood_sign(), True)]
    ims = []
    for name, c, ln in outs:
        p = os.path.join(OUTDIR, f"thumbnail_{name}.jpg"); ims.append(compose(c, p, lines=ln)); print(p, os.path.getsize(p))
    g = Image.new("RGB", (1280 * 2, 720 * 2))
    for i, im in enumerate(ims): g.paste(im, ((i % 2) * 1280, (i // 2) * 720))
    g.resize((1280, 720), Image.LANCZOS).save(os.path.join(OUTDIR, "compare.jpg"), quality=88)

# ---------- E: frameless floating flip tiles ----------
def float_tile(w, h, digit, blur, tilt):
    """A single split-flap card with cartoon outline, caught mid-flip (vertical smear + angled top flap)."""
    pad = 10 * S
    card = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w + 2 * pad - 1, h + 2 * pad - 1], 18 * S, fill=(18, 18, 22))          # thick outline
    inner = flap(w, h, digit, blur, bg=(246, 240, 226), fg=(22, 20, 24), flapc=(255, 255, 255, 90))
    card.alpha_composite(inner, (pad, pad))
    # top flap swinging down: lighter trapezoid above the card edge
    fl = Image.new("RGBA", card.size, (0, 0, 0, 0)); fd = ImageDraw.Draw(fl)
    cw = w + 2 * pad
    fd.polygon([(pad + 10 * S, pad + h * 0.05), (cw - pad - 10 * S, pad + h * 0.05), (cw - pad, pad + h / 2 - 3 * S), (pad, pad + h / 2 - 3 * S)], fill=(255, 255, 255, 70))
    card.alpha_composite(fl)
    return card.rotate(tilt, resample=Image.BICUBIC, expand=True)

def floating_flaps(label=False, W=860, H=260):
    W, H = W * S, H * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    digits = [4, 6, 8, 5, 3, 9]; blurs = [45, 70, 95, 120, 145, 170]; tilts = [-6, 3, -2, 5, -4, 6]
    top = (78 if label else 14) * S
    tw, th = 92 * S, 150 * S; gap = 6 * S; comma = 30 * S
    tiles = [float_tile(tw, th, digits[i], blurs[i] * S // 2, tilts[i]) for i in range(6)]
    total = sum(t.size[0] for t in tiles) + 5 * gap + comma; x = (W - total) / 2
    d = ImageDraw.Draw(im)
    for i, t in enumerate(tiles):
        yoff = [0, 8, -6, 8, -8, 4][i] * S
        im.alpha_composite(t, (int(x), int(top + yoff - (t.size[1] - th) / 2)))
        x += t.size[0] + gap
        if i == 2:
            d.text((x + comma / 2 - gap, top + th + 4 * S), ",", font=font("anton", 100 * S), fill=(255, 255, 255), anchor="ms",
                   stroke_width=7 * S, stroke_fill=(18, 18, 22))
            x += comma
    if label:
        d.text((W / 2, 40 * S), "POPULATION", font=font("anton", 66 * S), fill=(255, 255, 255), anchor="mm",
               stroke_width=9 * S, stroke_fill=(18, 18, 22))
    return im

def compose_free(c, out_path):
    """Like compose(), but no frame-specific shadow offset assumptions; small whoosh lines on the tiles."""
    return compose(c, out_path, top_y=4, lines=False)
