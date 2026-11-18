"""Original motion graphics in the channel's "case file" documentary style:
cream paper, condensed caps (Anton), marker handwriting (Permanent Marker), typewriter records (Special Elite),
navy keyword cards, pinned screenshots. No show characters are drawn here: character imagery only ever comes
from user-supplied episode frames passed in as `stills`.
Every generator: fn(t, d, **kw) -> PIL.Image RGB 1920x1080."""
import math, random, os, glob
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
INK = (24, 22, 20); CREAM = (236, 229, 212); PAPER = CREAM; WHITE = (255, 255, 255)
NAVY = (18, 24, 40); YELLOW = (246, 200, 66); RED = (200, 36, 36); BLUE_LINE = (150, 175, 210)
KRABS = (204, 52, 40); PLANK = (52, 150, 76); KAREN = (60, 120, 200); GREY = (120, 116, 108)

HERE = os.path.dirname(os.path.abspath(__file__)); FONTDIR = os.path.join(HERE, "..", "assets", "fonts")


def _sys(pat):
    hits = sorted(glob.glob("/usr/share/fonts/**/" + pat, recursive=True)); return hits[0] if hits else None


FONTS = {
    "cond": os.path.join(FONTDIR, "Anton-Regular.ttf"),
    "marker": os.path.join(FONTDIR, "PermanentMarker-Regular.ttf"),
    "type": os.path.join(FONTDIR, "SpecialElite-Regular.ttf"),
    "cartoon": os.path.join(FONTDIR, "LuckiestGuy-Regular.ttf"),
    "serif": _sys("*Caladea-Regular*") or _sys("*DejaVuSerif.ttf"),
    "bold": _sys("*Inter-Bold.ttf") or _sys("*Inter*Bold*") or _sys("*DejaVuSans-Bold*"),
    "black": _sys("*InterDisplay-Black*") or _sys("*DejaVuSans-Bold*"),
}


@lru_cache(256)
def font(size, kind="cond"):
    return ImageFont.truetype(FONTS[kind], int(size))


def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_in_out(x): x = min(max(x, 0), 1); return 3 * x * x - 2 * x ** 3
def ease_back(x):
    x = min(max(x, 0), 1); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


@lru_cache(128)
def text_img(text, size, kind="cond", fill=WHITE, stroke=0, stroke_fill=INK, spacing=0):
    f = font(size, kind)
    lines = text.split("\n")
    boxes = [f.getbbox(l or " ", stroke_width=stroke) for l in lines]
    lh = int(size * 1.12) + spacing
    w = max(b[2] - b[0] for b in boxes) + 4 * stroke + 12
    h = lh * (len(lines) - 1) + boxes[-1][3] + 2 * stroke + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = boxes[i][2] - boxes[i][0]
        dr.text(((w - lw) // 2 - boxes[i][0], i * lh + stroke + 4), l, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.01 or alpha <= 0.01: return
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def shadow(im, off=8, blur=12, op=130):
    s = Image.new("RGBA", (im.width + 4 * blur, im.height + 4 * blur), (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * op // 255)
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a)
    s.paste(blk, (2 * blur + off, 2 * blur + off), blk)
    s = s.filter(ImageFilter.GaussianBlur(blur)); s.paste(im, (2 * blur, 2 * blur), im)
    return s


def write_on(canvas, text, x, y, t, size=80, kind="marker", fill=INK, cps=16, anchor="l", rot=0):
    """handwriting reveal: text appears left to right. x,y = left-center (anchor l) or center (anchor c)"""
    if not text or not text.strip(): return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    full = text_img(text, size, kind, fill)
    p = min(1, max(0, t * cps / max(1, len(text))))
    if p <= 0: return full
    crop = full.crop((0, 0, max(1, int(full.width * p)), full.height))
    x0 = x if anchor == "l" else x - full.width / 2
    if rot: crop = crop.rotate(rot, resample=Image.BICUBIC, expand=True)
    canvas.paste(crop, (int(x0), int(y - full.height / 2)), crop)
    return full


def marker_circle(dr, cx, cy, rx, ry, p, color=RED, width=9, seed=1):
    """hand-drawn ellipse, p = 0..1 progress (a bit more than one loop)"""
    if p <= 0: return
    r = random.Random(seed); n = 70; pts = []
    a0 = r.uniform(0, 6.28); turns = 1.12
    for i in range(int(n * min(1, p)) + 1):
        a = a0 + turns * 2 * math.pi * i / n
        wob = 1 + 0.04 * math.sin(i * 0.5 + seed) + 0.03 * (i / n)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    if len(pts) > 1: dr.line(pts, fill=color, width=width, joint="curve")


def marker_line(dr, x0, y0, x1, y1, p, color=RED, width=9):
    if p <= 0: return
    dr.line([x0, y0, x0 + (x1 - x0) * min(1, p), y0 + (y1 - y0) * min(1, p)], fill=color, width=width)


def marker_arrow(dr, x0, y0, x1, y1, p, color=RED, width=9):
    marker_line(dr, x0, y0, x1, y1, p, color, width)
    if p >= 1:
        a = math.atan2(y1 - y0, x1 - x0)
        for s in (2.6, -2.6):
            dr.line([x1, y1, x1 + 34 * math.cos(a + s), y1 + 34 * math.sin(a + s)], fill=color, width=width)


# ---------- backgrounds ----------
@lru_cache(4)
def _grain(seed=0, amt=8):
    return np.random.default_rng(seed).normal(0, amt, (H, W, 1)).astype(np.float32)


@lru_cache(2)
def _navy():
    x = np.linspace(-1, 1, W)[None, :, None]; y = np.linspace(-1, 1, H)[:, None, None]
    a = np.ones((H, W, 3), np.float32) * np.array(NAVY, np.float32)
    a = a * (1.12 - 0.32 * (x ** 2 * .6 + y ** 2 * .8)) + _grain(1, 4)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def bg_navy(t=0): return _navy().copy()
bg_ocean = bg_navy


@lru_cache(2)
def _paper():
    a = np.ones((H, W, 3), np.float32) * np.array(CREAM, np.float32)
    rng = np.random.default_rng(3)
    blot = rng.normal(0, 1, (H // 60 + 1, W // 60 + 1)).astype(np.float32)
    blot = np.array(Image.fromarray(((blot - blot.min()) / np.ptp(blot) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)
    a = a - (blot[..., None] / 255) * 10 + _grain(2, 5)
    x = np.linspace(-1, 1, W)[None, :, None]; y = np.linspace(-1, 1, H)[:, None, None]
    a = a * (1 - 0.12 * (x ** 2 + y ** 2))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def bg_paper(): return _paper().copy()


@lru_cache(2)
def _notebook():
    im = _paper().copy(); d = ImageDraw.Draw(im)
    for y in range(150, H, 78): d.line([0, y, W, y], fill=BLUE_LINE, width=3)
    d.line([230, 0, 230, H], fill=(220, 120, 120), width=4)
    return im


def bg_notebook(): return _notebook().copy()
def bg_solid(c): return Image.new("RGB", (W, H), c)


def zoom_img(im, z):
    if abs(z - 1) < 0.002: return im
    w, h = W / z, H / z; x0 = (W - w) / 2; y0 = (H - h) / 2
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))


def card(w, h, color=CREAM, outline=None):
    im = Image.new("RGBA", (w, h), color + (255,))
    if outline: ImageDraw.Draw(im).rectangle([0, 0, w - 1, h - 1], outline=outline + (255,), width=3)
    return im


def still_img(still, w, h, label="CLIP"):
    if still is not None:
        s = still.convert("RGB"); r = max(w / s.width, h / s.height)
        s = s.resize((int(s.width * r) + 1, int(s.height * r) + 1), Image.BILINEAR)
        return s.crop(((s.width - w) // 2, (s.height - h) // 2, (s.width - w) // 2 + w, (s.height - h) // 2 + h)).convert("RGBA")
    im = Image.new("RGBA", (w, h), (70, 74, 84, 255)); d = ImageDraw.Draw(im)
    for k in range(-h, w, 40): d.line([k, 0, k + h, h], fill=(80, 84, 94, 255), width=10)
    t = text_img(label, 44, "cond", (210, 210, 210)); im.paste(t, ((w - t.width) // 2, (h - t.height) // 2), t)
    return im


def photo(still, w, h, caption=None, label="CLIP", border=22, bottom=90):
    pw, ph = w + 2 * border, h + border + (bottom if caption is not None else border)
    p = Image.new("RGBA", (pw, ph), (247, 244, 236, 255))
    p.paste(still_img(still, w, h, label), (border, border))
    if caption:
        c = text_img(caption, 44, "marker", INK)
        sc = min(1, (pw - 30) / c.width)
        if sc < 1: c = c.resize((int(c.width * sc), int(c.height * sc)))
        p.paste(c, ((pw - c.width) // 2, h + border + (bottom - c.height) // 2), c)
    return p


def pin(dr, x, y):
    dr.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(190, 40, 40), outline=(110, 20, 20), width=3)
    dr.ellipse([x - 6, y - 9, x + 2, y - 1], fill=(240, 150, 150))


# ---------- cards ----------
def title_card(t, d, num="PART 1", title="TITLE", accent=None):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    write_on(c, num.upper(), W / 2, 330, t * 2, 54, "type", (110, 100, 90), cps=30, anchor="c")
    ti = text_img(title, 150 if len(title) < 22 else 120, "cond", INK)
    if ti.width > 1680: ti = ti.resize((1680, int(ti.height * 1680 / ti.width)))
    paste(c, ti, W / 2, H / 2 + 20, 1 + .02 * t / max(d, .1), ease_out((t - .1) / .25))
    p = ease_out((t - .4) / .45)
    marker_line(dr, W / 2 - ti.width / 2, H / 2 + ti.height / 2 + 20, W / 2 + ti.width / 2, H / 2 + ti.height / 2 + 8, p, RED, 10)
    return c


def big_text(t, d, text="TEXT", color=None, bg="navy", size=190, sub=None, stamp=None):
    if bg == "quote":
        c = bg_solid((8, 8, 9)); ti = text_img(text, 110, "serif", (240, 238, 232))
        paste(c, ti, W / 2, H / 2, min(1, 1700 / ti.width), ease_out(t / .5))
        if sub: paste(c, text_img(sub, 40, "type", (150, 150, 150)), W / 2, H / 2 + 120, 1, ease_out((t - .4) / .4))
        return c
    c = bg_paper() if bg in ("paper", "yellow") else bg_navy(t)
    fill = INK if bg in ("paper", "yellow") else (color if color not in (None, WHITE) else YELLOW)
    ti = text_img(text, size, "cond", fill); fit = min(1, 1700 / ti.width)
    paste(c, ti, W / 2, H / 2 - (50 if sub else 0), fit * (0.94 + 0.06 * ease_out(t / .3) + 0.012 * t), min(1, t / .12))
    if sub: paste(c, text_img(sub, 44, "type", (225, 222, 214) if bg == "navy" else (90, 84, 76)), W / 2, H / 2 + size * .55, 1, ease_out((t - .3) / .3))
    if stamp: scrawl(c, stamp[0], W / 2 + 360, H / 2 + 200, t - stamp[1])
    return c


def scrawl(c, text, cx, cy, lt, color=RED, size=84, rot=-6, circle=True):
    """red marker note with a hand-drawn circle (replaces rubber stamps)"""
    if lt < 0: return
    dr = ImageDraw.Draw(c)
    full = text_img(text, size, "marker", color)
    write_on(c, text, cx, cy, lt, size, "marker", color, cps=22, anchor="c", rot=rot)
    if circle: marker_circle(dr, cx, cy + 4, full.width / 2 + 50, full.height / 2 + 30, (lt - len(text) / 22) / .35, color, 8, len(text))


def typewriter(t, d, lines=("JULY 31, 1999",), size=120, sub=None, cps=14, bg="paper"):
    c = bg_paper() if bg == "paper" else bg_solid((10, 10, 12))
    fill = INK if bg == "paper" else (235, 232, 224)
    total = sum(len(l) for l in lines); shown = int(t * cps)
    y = H / 2 - (len(lines) - 1) * size * 0.6 - (40 if sub else 0)
    for l in lines:
        s = l[:max(0, shown)]; shown -= len(l)
        full = text_img(l, size, "type", fill)
        if s:
            im = text_img(s, size, "type", fill)
            c.paste(im, (int(W / 2 - full.width / 2), int(y - full.height / 2)), im)
        y += size * 1.2
    if sub and t > total / cps + .2:
        write_on(c, sub, W / 2, y + 20, t - total / cps - .2, 54, "marker", RED, anchor="c")
    return c


def notebook(t, d, lines=(("1999 → 2026", INK, 120),), start=.1, gap=.7, circle_last=False, title=None):
    """handwritten marker math on notebook paper; lines = (text, color, size)"""
    c = bg_notebook(); dr = ImageDraw.Draw(c)
    if title: write_on(c, title, 300, 110, t * 1.5, 56, "marker", (90, 84, 76))
    y = 300 if title else 330; last = None
    for i, (txt, col, sz) in enumerate(lines):
        lt = t - start - i * gap
        if lt > 0:
            full = write_on(c, txt, 320, y, lt, sz, "marker", col, cps=18)
            last = (320, y, full.width, full.height, lt - len(txt) / 18)
        y += max(130, sz * 1.25)
    if circle_last and last:
        x, y0, w_, h_, lt = last
        marker_circle(dr, x + w_ / 2, y0, w_ / 2 + 40, h_ / 2 + 18, lt / .4, RED, 9, 7)
    return c


def counter(t, d, a=1999, b=2026, label="YEARS", suffix="", roll=1.6, color=None):
    lab = label.lower()
    lines = ((f"{a} to {b}", INK, 120), (f"= {b - a} {lab}", RED, 96)) if a > 100 else ((f"{b} {lab}", RED, 100),)
    return notebook(t, d, lines, circle_last=a > 100)


def strike(t, d, top="PLANNED: 1–2 EPISODES", bottom="ACTUAL: 27 YEARS"):
    c = notebook(t, d, ((top.lower(), INK, 100),), start=0)
    dr = ImageDraw.Draw(c); full = text_img(top.lower(), 100, "marker", INK)
    marker_line(dr, 300, 340, 340 + full.width, 320, (t - .9) / .3, RED, 12)
    if t > 1.2: write_on(c, bottom.lower(), 320, 520, t - 1.2, 110, "marker", RED)
    return c


def vs_card(t, d, left="LEMONADE STAND", right="COSTCO PARKING LOT", lc=None, rc=None, sub=None):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    for i, (txt, cx) in enumerate(((left, W * .26), (right, W * .74))):
        lt = t - i * .45
        if lt <= 0: continue
        cd = card(620, 380, (247, 244, 236)); ImageDraw.Draw(cd).rectangle([0, 0, 619, 379], outline=INK + (255,), width=4)
        ti = text_img(txt.replace(" ", "\n", 1), 90, "cond", INK); cd.paste(ti, ((620 - ti.width) // 2, (380 - ti.height) // 2), ti)
        paste(c, shadow(cd, 6, 10, 90), cx, H / 2, 1, min(1, lt / .15), (-2 if i == 0 else 2))
    if t > .3: write_on(c, "vs.", W / 2, H / 2, t - .3, 90, "marker", RED, anchor="c")
    if sub: write_on(c, sub, W / 2, H - 150, t - .9, 56, "marker", INK, anchor="c")
    return c


def map_street(t, d, left="KRUSTY KRAB", right="CHUM BUCKET", note="about one street"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    dr.rectangle([W // 2 - 140, 0, W // 2 + 140, H], fill=(205, 198, 182))
    for y in range(0, H, 110): dr.rectangle([W // 2 - 6, y, W // 2 + 6, y + 55], fill=(250, 246, 236))
    for i, (lab, col, cx) in enumerate([(left, KRABS, W * .23), (right, PLANK, W * .77)]):
        lt = t - i * .3
        if lt <= 0: continue
        bx = card(560, 360, (247, 244, 236)); bd = ImageDraw.Draw(bx)
        bd.rectangle([0, 0, 559, 359], outline=INK + (255,), width=5); bd.rectangle([0, 0, 559, 26], fill=col + (255,))
        ti = text_img(lab, 92, "cond", INK); bx.paste(ti, ((560 - ti.width) // 2, (360 - ti.height) // 2 + 10), ti)
        paste(c, shadow(bx, 6, 10, 90), cx, H / 2, 1, min(1, lt / .15))
    p = (t - .8) / .5; y = H * .22
    marker_arrow(dr, W * .23 + 300, y, W * .77 - 300, y, p, RED)
    if p >= 1 and note: write_on(c, note, W / 2, y - 70, t - 1.3, 60, "marker", RED, anchor="c")
    return c


def magnify(t, d):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    cx, cy = W * .5, H * .54
    dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=INK)
    p = ease_out((t - .4) / .8); mx = cx + (1 - p) * 700; my = cy + (1 - p) * 300; r = 220
    if p > 0:
        lens = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); ld = ImageDraw.Draw(lens)
        ld.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=(246, 242, 232, 255))
        dx, dy = cx - mx, cy - my
        ld.ellipse([r + dx * 6 - 26, r + dy * 6 - 26, r + dx * 6 + 26, r + dy * 6 + 26], fill=INK + (255,))
        m = Image.new("L", lens.size, 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
        c.paste(lens, (int(mx - r), int(my - r)), m)
        dr.ellipse([mx - r, my - r, mx + r, my + r], outline=INK, width=20)
        a = math.radians(45)
        dr.line([mx + r * math.cos(a), my + r * math.sin(a), mx + (r + 250) * math.cos(a), my + (r + 250) * math.sin(a)], fill=INK, width=44)
    return c


def chat(t, d, msgs=(("NICKELODEON", "Can we get a famous guest star?"), ("HILLENBURG", "No. It's Doug.")), note="(paraphrased)", step=1.1):
    c = bg_navy(t); y = 300
    for i, (who, msg) in enumerate(msgs):
        lt = t - i * step
        if lt < 0: break
        left = i % 2 == 0
        f = font(64, "bold"); tw = int(f.getlength(msg)) + 90
        bub = Image.new("RGBA", (tw, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
        bd.rounded_rectangle([0, 0, tw - 1, 149], 50, fill=((240, 236, 226) if left else YELLOW) + (255,))
        bd.text((45, 38), msg, font=f, fill=INK)
        cx = 140 + tw / 2 if left else W - 140 - tw / 2
        paste(c, text_img(who, 40, "type", (170, 180, 200)), cx - tw / 2 + 120 if left else cx + tw / 2 - 120, y - 22, 1, min(1, lt / .1))
        paste(c, bub, cx, y + 95, 0.9 + 0.1 * ease_out(lt / .2), min(1, lt / .1))
        y += 260
    if note: paste(c, text_img(note, 36, "type", (140, 150, 170)), W - 220, H - 60)
    return c


def nameplate(t, d, name="MR. LAWRENCE", role="voice of Plankton since 1999", color=None):
    c = bg_navy(t)
    paste(c, text_img(name, 150, "cond", YELLOW), W / 2, H / 2 - 50, min(1, 1700 / text_img(name, 150, "cond").width), ease_out(t / .25))
    paste(c, text_img(role, 50, "type", (225, 222, 214)), W / 2, H / 2 + 90, 1, ease_out((t - .3) / .3))
    return c


def checklist(t, d, items=("STEAL THE FORMULA", "MAKE KRABBY PATTIES", "BANKRUPT MR. KRABS", "RULE THE WORLD (?)"),
              title="THE PLAN", reveal=None, stamp_at=None, stamp="FAILED"):
    c = bg_notebook(); dr = ImageDraw.Draw(c)
    write_on(c, title.lower(), 320, 140, 9, 84, "marker", INK)
    reveal = reveal or [0.3 + i * 0.7 for i in range(len(items))]
    for i, it in enumerate(items):
        lt = t - reveal[i]
        if lt < 0: continue
        y = 330 + i * 150
        dr.rectangle([330, y - 34, 398, y + 34], outline=INK, width=6)
        write_on(c, it.lower(), 430, y, lt + (9 if lt > .1 else 0), 76, "marker", INK)
    if stamp_at is not None: scrawl(c, stamp, W * .74, H * .6, t - stamp_at, RED, 120, -10)
    return c


def scoreboard(t, d, p="0", k="∞", note=None, flip=None):
    c = bg_notebook(); dr = ImageDraw.Draw(c)
    dr.line([W / 2, 270, W / 2, H - 140], fill=INK, width=6); dr.line([360, 380, W - 360, 380], fill=INK, width=6)
    for lab, val, cx in (("PLANKTON", p, W * .32), ("KRABS", k, W * .68)):
        paste(c, text_img(lab, 96, "cond", INK), cx, 320)
        paste(c, text_img(val, 260, "marker", RED), cx, 610, 0.9 + 0.1 * ease_back(t / .25), min(1, t / .1))
    if note: write_on(c, note, W / 2, H - 90, t - .4, 52, "marker", RED, anchor="c")
    return c


def three_versions(t, d, active=None, unreliable=(), titles=("Krabs's version", "Plankton's version", "Karen's version"),
                   stills=(None, None, None), stamp_t=0.25):
    c = bg_navy(t); dr = ImageDraw.Draw(c)
    ids = ("VERSION 1", "VERSION 2", "VERSION 3")
    for i in range(3):
        lt = t - i * .15
        if lt <= 0: continue
        cx = W * (0.2 + 0.3 * i); on = active is None or active == i
        ph = photo(stills[i] if i < len(stills) else None, 460, 300, titles[i], ids[i])
        if not on:
            a = np.asarray(ph).astype(np.float32); a[..., :3] = a[..., :3] * .45 + 40; ph = Image.fromarray(a.astype(np.uint8))
        rot = (-3, 2, -2)[i]
        paste(c, shadow(ph, 10, 14, 150), cx, H / 2 + 20, (1.08 if active == i else 1) * (0.92 + 0.08 * ease_out(lt / .2)), min(1, lt / .12), rot)
        pin(dr, cx, H / 2 - 200)
        if i in unreliable:
            lt2 = t - stamp_t if i == max(unreliable) else 5
            if lt2 > 0:
                marker_line(dr, cx - 230, H / 2 - 160, cx + 230, H / 2 + 200, lt2 / .2, RED, 12)
                marker_line(dr, cx + 230, H / 2 - 160, cx - 230, H / 2 + 200, (lt2 - .15) / .2, RED, 12)
    return c


def equation(t, d, parts=None, times=None):
    times = times or (0, .45, .8, 1.25, 1.5)
    c = bg_notebook(); dr = ImageDraw.Draw(c)
    lt = t - times[0]
    if lt > 0: write_on(c, "plankton + krabs", 320, 430, lt, 130, "marker", INK, cps=12)
    lt = t - times[3]
    if lt > 0:
        full = write_on(c, "= PLABS", 320, 650, lt, 170, "marker", RED, cps=10)
        marker_circle(dr, 320 + full.width / 2 + 40, 650, full.width / 2 - 20, full.height / 2 + 10, (lt - .6) / .4, RED, 9, 3)
    return c


def rip_paper(t, d, rip_at=0.6, label=None, title="SECRET RECIPE", halves=("", "")):
    c = bg_navy(t)
    pw, ph = 760, 900
    paper = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(paper)
    pd.rectangle([0, 0, pw - 1, ph - 1], fill=(244, 238, 222, 255))
    for y in range(230, ph - 60, 70): pd.line([60, y, pw - 60, y], fill=(190, 175, 150, 255), width=3)
    tw = text_img(title, 76, "cond", INK); paper.paste(tw, ((pw - tw.width) // 2, 80), tw)
    rng = random.Random(4)
    for y in range(250, ph - 80, 70):
        x = 70
        while x < pw - 120:
            w_ = rng.randint(40, 140); pd.rectangle([x, y - 30, x + w_, y - 12], fill=(90, 80, 70, 255)); x += w_ + 25
    pts = [(pw / 2 + rng.randint(-30, 30), y) for y in range(0, ph + 1, 45)]
    left = Image.new("L", (pw, ph), 0); ImageDraw.Draw(left).polygon([(0, 0)] + pts + [(0, ph)], fill=255)
    right = Image.new("L", (pw, ph), 0); ImageDraw.Draw(right).polygon([(pw, 0)] + pts + [(pw, ph)], fill=255)
    L = paper.copy(); L.putalpha(left); R = paper.copy(); R.putalpha(right)
    sep = ease_out((t - rip_at) / .5) * 260 if t > rip_at else (math.sin(t * 60) * 3 if t > rip_at - .3 else 0)
    rot = ease_out((t - rip_at) / .5) * 7 if t > rip_at else 0
    for im, sgn in ((L, -1), (R, 1)): paste(c, shadow(im, 8, 12, 110), W / 2 + sgn * sep, H / 2 + 20, 1, 1, -sgn * rot)
    if t > rip_at + .4:
        for (txt, col), sgn in zip(halves, (-1, 1)):
            if txt: write_on(c, txt.lower(), W / 2 + sgn * (sep + 200), H - 90, t - rip_at - .4, 60, "marker", YELLOW, anchor="c")
    return c


def record_card(c, title, rows, t, newest=None, circle_row=None, header=None, header_col=INK):
    """typed index card on navy, like an archive record"""
    cw, ch = 1400, 780; cx0, cy0 = (W - cw) // 2, (H - ch) // 2 + 20
    cd = card(cw, ch, (245, 240, 226)); d = ImageDraw.Draw(cd)
    for y in range(190, ch - 40, 92): d.line([60, y + 50, cw - 60, y + 50], fill=(200, 210, 225, 255), width=2)
    d.line([0, 150, cw, 150], fill=(210, 120, 120, 255), width=3)
    if header: d.rectangle([0, 0, cw, 110], fill=header_col + (255,))
    ti = text_img(title, 64, "type", WHITE if header else INK); cd.paste(ti, (60, 30 if header else 50), ti)
    c.paste(shadow(cd, 10, 14, 150), (cx0 - 28, cy0 - 28), shadow(cd, 10, 14, 150))
    dr = ImageDraw.Draw(c)
    for i, (k, v) in enumerate(rows):
        y = cy0 + 230 + i * 120
        ks = text_img(k, 52, "type", (110, 100, 90)); c.paste(ks, (cx0 + 70, int(y - ks.height / 2)), ks)
        vt = v if i != newest else v[:max(0, int(t * 20))]
        if vt:
            vs = text_img(vt, 64, "type", INK); c.paste(vs, (cx0 + 600, int(y - vs.height / 2)), vs)
        if circle_row == i:
            full = text_img(v, 64, "type", INK)
            marker_circle(dr, cx0 + 600 + full.width / 2, y, full.width / 2 + 40, 52, (t - .6) / .4, RED, 8, 5)
    return c


def evidence(t, d, n=4, title="SUBJECT: THE KRABBY PATTY",
             fields=(("INVENTED BY:", "two kids"), ("METHOD:", "an accident"), ("OCCASION:", "a breakup"), ("CREDITED TO:", "one crab")),
             stamp_last=True):
    c = bg_navy(t)
    return record_card(c, title, fields[:n], t, newest=n - 1, circle_row=(n - 1 if stamp_last and n == len(fields) else None))


def error_card(t, d, title="CONTINUITY ERROR", body=None, stamp="ignored", stamp_at=1.0):
    c = bg_navy(t)
    rows = (("EPISODE:", "Enemy In-Law (2005)"), ("SAYS:", "old Krabs FAMILY recipe"), ("CONFLICTS WITH:", "Friend or Foe (2007)"))
    record_card(c, title, rows, 9, header=True, header_col=RED)
    if t > stamp_at: scrawl(c, stamp, W * .7, H * .78, t - stamp_at, RED, 110, -8)
    return c


def exchange(t, d, rows=(("1¢", "one balloon", "for Plankton"), ("62¢", "one soul", "SpongeBob's")), title="Mr. Krabs: exchange rates"):
    lines = tuple((f"{a} = {b} ({cmt})", INK if i == 0 else RED, 96) for i, (a, b, cmt) in enumerate(rows))
    return notebook(t, d, lines, start=.2, gap=.9, title=title)


def phone(t, d, handle="chum.bucket.official", viewer="krusty_krab_backup_2", sub="Story viewed by"):
    c = bg_navy(t); dr = ImageDraw.Draw(c)
    s = ease_back(t / .3)
    if s <= 0: return c
    s = max(s, .2); pw, ph = int(560 * s), int(980 * s)
    ph_ = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph_)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], int(70 * s), fill=(15, 15, 18, 255))
    pd.rounded_rectangle([int(24 * s), int(24 * s), pw - int(24 * s), ph - int(24 * s)], int(50 * s), fill=(250, 250, 250, 255))
    paste(c, shadow(ph_, 10, 16, 140), W / 2, H / 2)
    if t > .3:
        x0 = W / 2 - 230; y0 = H / 2 - 400
        dr.ellipse([x0, y0, x0 + 120, y0 + 120], fill=PLANK, outline=(230, 60, 120), width=8)
        dr.text((x0 + 135, y0 + 40), handle, font=font(30, "bold"), fill=INK)
        dr.rectangle([x0, y0 + 160, x0 + 460, y0 + 520], fill=(214, 228, 214))
        paste(c, text_img("BACK ON MY\nGRIND", 64, "cond", INK), x0 + 230, y0 + 340)
    if t > 1.0:
        x0 = W / 2 - 230; y0 = H / 2 + 170
        dr.text((x0, y0), sub, font=font(34, "bold"), fill=GREY)
        for i, v in enumerate([viewer, "krabs_robot_unit", "not_mr_krabs_99"]):
            if t - 1.0 > i * .5:
                dr.ellipse([x0, y0 + 60 + i * 80, x0 + 56, y0 + 116 + i * 80], fill=KRABS)
                dr.text((x0 + 76, y0 + 70 + i * 80), v, font=font(32, "bold"), fill=INK)
    return c


def watch_loop(t, d):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    nodes = [("PLANKTON", W * .22, H * .3), ("ROBOT PLANKTON", W * .22, H * .72), ("KRABS", W * .78, H * .3), ("ROBOT KRABS", W * .78, H * .72)]
    for i, (lab, x, y) in enumerate(nodes):
        lt = t - i * .3
        if lt < 0: continue
        bx = card(520, 170, (247, 244, 236)); ImageDraw.Draw(bx).rectangle([0, 0, 519, 169], outline=INK + (255,), width=5)
        ti = text_img(lab, 74, "cond", INK); bx.paste(ti, ((520 - ti.width) // 2, (170 - ti.height) // 2), ti)
        paste(c, shadow(bx, 6, 8, 80), x, y, 1, min(1, lt / .12))
    for k, y in enumerate((H * .3, H * .72)):
        marker_arrow(dr, W * .22 + 290, y, W * .78 - 290, y, (t - 1.3 - k * .3) / .4, RED)
    for x in (W * .22, W * .78): marker_arrow(dr, x, H * .3 + 100, x, H * .72 - 100, (t - 1.0) / .3, INK, 7)
    return c


def pie(t, d, title="THINGS PLANKTON DOES", sub="(according to Mr. Krabs)", label="about Krabs: 100%"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    paste(c, text_img(title, 90, "cond", INK), W / 2, 130); paste(c, text_img(sub, 44, "type", GREY), W / 2, 220)
    p = ease_out((t - .2) / 1.0); cx, cy, r = W / 2 - 300, H / 2 + 90, 300
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(222, 214, 196), outline=INK, width=6)
    if p > 0: dr.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * p, fill=KRABS, outline=INK, width=6)
    if t > 1.3:
        write_on(c, label, cx + r + 120, cy, t - 1.3, 80, "marker", RED)
        marker_arrow(dr, cx + r + 100, cy, cx + r - 60, cy, (t - 1.8) / .2, RED, 7)
    return c


def heartbreak(t, d, text="a breakup."):
    c = bg_navy(t)
    def heart(sz):
        im = Image.new("RGBA", (sz * 2, sz * 2), (0, 0, 0, 0)); hd = ImageDraw.Draw(im); pts = []
        for a in np.linspace(0, 2 * np.pi, 120):
            x = 16 * np.sin(a) ** 3; y = 13 * np.cos(a) - 5 * np.cos(2 * a) - 2 * np.cos(3 * a) - np.cos(4 * a)
            pts.append((sz + x * sz / 17, sz - y * sz / 17))
        hd.polygon(pts, fill=KRABS + (255,)); return im
    h = heart(240); split = ease_out((t - .6) / .4) * 60 if t > .6 else 0
    m = Image.new("L", h.size, 0); md = ImageDraw.Draw(m)
    zig = [(240 + (24 if i % 2 else -24), y) for i, y in enumerate(range(0, 481, 48))]
    md.polygon([(0, 0)] + zig + [(0, 480)], fill=255)
    L = h.copy(); L.putalpha(Image.composite(h.split()[3], Image.new("L", h.size, 0), m))
    R = h.copy(); R.putalpha(Image.composite(Image.new("L", h.size, 0), h.split()[3], m))
    paste(c, L, W / 2 - split, H / 2 - 100, 1, min(1, t / .15), split * .15); paste(c, R, W / 2 + split, H / 2 - 100, 1, min(1, t / .15), -split * .15)
    if text and t > .7: paste(c, text_img(text.upper(), 130, "cond", YELLOW), W / 2, H - 170, 1, ease_out((t - .7) / .2))
    return c


def verdict(t, d, lit=None, title="WHO'S THE BAD GUY?"):
    c = bg_navy(t); dr = ImageDraw.Draw(c)
    if title: paste(c, text_img(title, 110, "cond", YELLOW), W / 2, 190, 1, ease_out(t / .3))
    for i, (lab, cx) in enumerate([("KRABS", W * .3), ("PLANKTON", W * .7)]):
        on = lit is None or lit == i
        bx = card(600, 260, (245, 240, 226) if on else (90, 92, 100))
        ti = text_img(lab, 120, "cond", INK if on else (60, 60, 66)); bx.paste(ti, ((600 - ti.width) // 2, (260 - ti.height) // 2), ti)
        paste(c, shadow(bx, 8, 12, 140), cx, H / 2 + 120, 1.06 if lit == i else 1, 1, (-2 if i == 0 else 2))
        if lit is None: write_on(c, "?", cx + 250, H / 2 - 30, t - .3 - i * .2, 140, "marker", RED, anchor="c")
        if lit == i: marker_circle(dr, cx, H / 2 + 120, 360, 180, (t - .2) / .4, RED, 12, 11)
    return c


def balloon(t, d, text="", rise=True):
    c = bg_navy(t); dr = ImageDraw.Draw(c)
    y = H * .45 - (t * 40 if rise else 0); x = W / 2 + math.sin(t * 1.3) * 18
    pts = [(x + math.sin(t * 2 + k * .4) * 10 * (k / 12), y + 150 + k * 40) for k in range(14)]
    dr.line(pts, fill=(200, 200, 200), width=4)
    b = Image.new("RGBA", (300, 380), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
    bd.ellipse([10, 10, 290, 340], fill=KRABS + (255,)); bd.polygon([(150, 330), (130, 370), (170, 370)], fill=KRABS + (255,))
    bd.ellipse([70, 60, 120, 140], fill=(240, 140, 130, 200))
    paste(c, b, x, y, 1, min(1, t / .4))
    if text: write_on(c, text, W / 2, H - 140, t - .4, 90, "marker", YELLOW, anchor="c")
    return c


def coins(t, d, text="every penny after that", n=70):
    c = bg_navy(t); dr = ImageDraw.Draw(c); rng = random.Random(9); landed = 0
    for i in range(n):
        t0 = i * 0.045; x = W / 2 + rng.gauss(0, 170); ty = H - 160 - (i // 7) * 14 - rng.random() * 30
        lt = t - t0
        if lt < 0: break
        y = min(ty, -60 + 2400 * lt * lt)
        if y >= ty: landed += 1
        ry = 18 if y >= ty else 40
        dr.ellipse([x - 60, y - ry, x + 60, y + ry], fill=(206, 160, 70), outline=(120, 84, 20), width=5)
    write_on(c, text, W / 2, 170, t, 70, "marker", (235, 230, 220), anchor="c")
    if text: paste(c, text_img(f"${landed * 0.01:.2f}", 64, "type", (226, 190, 100)), W - 260, 170)
    return c


def watchlist(t, d, eps=("Plankton!", "F.U.N.", "Friend or Foe", "Enemy In-Law", "One Coarse Meal", "Plankton Retires",
                          "Plankton's Regular", "Single Cell Anniversary", "Imitation Krabs", "Born Again Krabs",
                          "The Algae's Always Greener", "Plankton's Pet")):
    c = bg_navy(t); dr = ImageDraw.Draw(c)
    for i, e in enumerate(eps):
        r, k = divmod(i, 3); lt = t - i * .1
        if lt < 0: continue
        x = 150 + k * 560; y = 190 + r * 210 - t * 12
        cd = card(500, 160, (245, 240, 226)); cdd = ImageDraw.Draw(cd)
        cdd.line([0, 40, 500, 40], fill=(210, 120, 120, 255), width=2)
        ti = text_img(e, 40 if len(e) < 20 else 32, "type", INK); cd.paste(ti, (24, 70), ti)
        paste(c, cd, x + 250, y + 80, 1, min(1, lt / .1), (i % 3 - 1) * 1.2)
        if lt > .3: dr.line([(x + 420, y + 70), (x + 445, y + 100), (x + 490, y + 30)], fill=RED, width=10, joint="curve")
    return c


def polaroid(t, d, still=None, caption="", label="CLIP", rot=-3):
    c = bg_navy(t); dr = ImageDraw.Draw(c)
    ph = photo(still, 1180, 664, caption, label, 30, 120)
    paste(c, shadow(ph, 14, 18, 160), W / 2, H / 2 + 10, 0.95 + 0.04 * ease_out(t / .4) + 0.012 * t, min(1, t / .1), rot)
    pin(dr, W / 2, H / 2 - 395)
    return c


def end_black(t, d, text=""):
    c = bg_solid((0, 0, 0))
    if text: paste(c, text_img(text, 60, "type", (220, 220, 220)), W / 2, H / 2, 1, ease_out(t / .4))
    return c


def placeholder(clip_id, desc, t):
    c = bg_solid((34, 36, 42)); dr = ImageDraw.Draw(c)
    for k in range(-H, W, 90): dr.line([k, 0, k + H, H], fill=(40, 42, 50), width=26)
    paste(c, text_img(f"CLIP {clip_id}", 130, "cond", YELLOW), W / 2, H / 2 - 120)
    lines, cur = [], ""
    for w_ in desc.split(" "):
        if len(cur) + len(w_) > 46: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    lines.append(cur)
    paste(c, text_img("\n".join(lines[:4]), 46, "type", (220, 220, 220)), W / 2, H / 2 + 80)
    return c


PAPER_CARDS = {"title_card", "typewriter", "notebook", "counter", "strike", "vs_card", "map_street", "magnify", "checklist",
               "scoreboard", "equation", "evidence", "error_card", "exchange", "watch_loop", "pie", "polaroid", "three_versions"}

GFX = {k: v for k, v in globals().items() if callable(v) and k in (
    "title_card big_text typewriter notebook counter vs_card map_street magnify strike chat nameplate checklist scoreboard "
    "three_versions equation rip_paper evidence error_card exchange phone watch_loop pie heartbreak verdict balloon "
    "coins watchlist polaroid end_black").split()}
