"""Original motion graphics (no show characters are drawn here; characters come only from
user-supplied episode clips). Every generator: fn(t, d, **kw) -> PIL.Image RGB 1920x1080."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
INK = (17, 17, 17); PAPER = (242, 232, 213); WHITE = (255, 255, 255)
KRABS = (226, 54, 44); PLANK = (47, 191, 74); KAREN = (58, 160, 255); YELLOW = (255, 212, 0)
OCEAN = (8, 34, 52); GREY = (120, 120, 120)

FONTS = {
    "black": "/usr/share/fonts/truetype/inter/InterDisplay-Black.ttf",
    "bold": "/usr/share/fonts/truetype/inter/Inter-ExtraBold.ttf",
    "type": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
}


def _find_fonts():
    import glob, os
    for k, pat in {"black": "*InterDisplay*Black*", "bold": "*Inter*ExtraBold*",
                   "type": "*DejaVuSansMono-Bold*", "serif": "*DejaVuSerif-Bold*"}.items():
        if not os.path.exists(FONTS[k]):
            hits = sorted(glob.glob("/usr/share/fonts/**/" + pat, recursive=True))
            if hits: FONTS[k] = hits[0]
_find_fonts()


@lru_cache(256)
def font(size, kind="black"):
    return ImageFont.truetype(FONTS[kind], int(size))


def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_in_out(x): x = min(max(x, 0), 1); return 3 * x * x - 2 * x ** 3
def ease_back(x):
    x = min(max(x, 0), 1); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


@lru_cache(64)
def text_img(text, size, kind="black", fill=WHITE, stroke=0, stroke_fill=INK, spacing=0):
    f = font(size, kind)
    lines = text.split("\n")
    boxes = [f.getbbox(l or " ", stroke_width=stroke) for l in lines]
    lh = int(size * 1.08) + spacing
    w = max(b[2] - b[0] for b in boxes) + 4 * stroke + 8
    h = lh * (len(lines) - 1) + (boxes[-1][3]) + 2 * stroke + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = boxes[i][2] - boxes[i][0]
        dr.text(((w - lw) // 2 - boxes[i][0], i * lh + stroke), l, font=f, fill=fill,
                stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.01 or alpha <= 0.01: return
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def shadow(im, off=10, blur=12, op=150):
    s = Image.new("RGBA", (im.width + 4 * blur, im.height + 4 * blur), (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * op // 255)
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a)
    s.paste(blk, (2 * blur + off, 2 * blur + off), blk)
    s = s.filter(ImageFilter.GaussianBlur(blur))
    s.paste(im, (2 * blur, 2 * blur), im)
    return s


# ---------- backgrounds ----------
@lru_cache(4)
def _grain(seed=0, amt=14):
    r = np.random.default_rng(seed).normal(0, amt, (H, W, 1)).astype(np.float32)
    return r


@lru_cache(2)
def _ocean_base():
    y = np.linspace(0, 1, H)[:, None, None]; x = np.linspace(-1, 1, W)[None, :, None]
    top = np.array([14, 58, 84], np.float32); bot = np.array([4, 16, 28], np.float32)
    img = top * (1 - y) + bot * y
    v = 1 - 0.35 * (x ** 2 + ((y - .4) * 1.4) ** 2)
    return np.clip(img * v, 0, 255).astype(np.float32)


def bg_ocean(t=0, tint=None):
    a = _ocean_base().copy()
    # drifting light rays
    xs = np.arange(W)[None, :]
    rays = 0
    for k, (sp, fq, ph) in enumerate([(0.05, 0.004, 0), (0.03, 0.0067, 2), (0.07, 0.0021, 4)]):
        rays = rays + np.sin(xs * fq + t * sp * 6 + ph)
    rays = (np.clip(rays, 0, None) * 6)[..., None] * np.linspace(1, 0, H)[:, None, None]
    a = a + rays + _grain(1, 7)[:H]
    if tint is not None: a = a * 0.75 + np.array(tint, np.float32) * 0.25 * (a / 255 + .3)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


@lru_cache(2)
def _paper():
    a = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32)
    rng = np.random.default_rng(3)
    blot = rng.normal(0, 1, (H // 40 + 1, W // 40 + 1)).astype(np.float32)
    blot = np.array(Image.fromarray(((blot - blot.min()) / (np.ptp(blot)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)
    a = a - (blot[..., None] / 255) * 18 + _grain(2, 9)
    x = np.linspace(-1, 1, W)[None, :, None]; y = np.linspace(-1, 1, H)[:, None, None]
    a = a * (1 - 0.22 * (x ** 2 + y ** 2))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def bg_paper(): return _paper().copy()


def bg_solid(c): return Image.new("RGB", (W, H), c)


def stamp_img(text, color=KRABS, size=110):
    f = font(size, "black"); b = f.getbbox(text)
    w, h = b[2] - b[0] + 80, b[3] - b[1] + 60
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 7, h - 7], outline=color + (235,), width=12)
    d.text((40 - b[0], 30 - b[1]), text, font=f, fill=color + (235,))
    # distress
    a = np.array(im); m = np.random.default_rng(len(text)).random(a.shape[:2]) < 0.12
    a[..., 3][m] = (a[..., 3][m] * 0.3).astype(np.uint8)
    return Image.fromarray(a)


def draw_stamp(canvas, text, cx, cy, local_t, color=KRABS, size=110, rot=-8):
    if local_t < 0: return
    s = 1 + 1.6 * (1 - ease_out(local_t / 0.12))
    paste(canvas, stamp_img(text, color, size), cx, cy, s, min(1, local_t / 0.06 + .2), rot)


# ---------- cards ----------
def title_card(t, d, num="CHAPTER 1", title="TITLE", accent=YELLOW):
    c = bg_ocean(t)
    dr = ImageDraw.Draw(c)
    # accent bar wipe
    bw = int(ease_out(t / 0.35) * 260)
    dr.rectangle([W // 2 - bw, 330, W // 2 + bw, 342], fill=accent)
    paste(c, text_img(num, 54, "bold", accent), W / 2, 285, 1, ease_out(t / .3))
    words = title.split(" ")
    # wrap into <= 2 lines
    lines, cur = [], ""
    for w_ in words:
        if len(cur + " " + w_) > 16 and cur: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    lines.append(cur)
    y = 470
    k = 0
    for ln in lines:
        x_words = ln.split(" "); full = text_img(ln, 150, "black", WHITE)
        # reveal word by word with slam
        xs = W / 2 - full.width / 2
        f = font(150, "black")
        for w_ in x_words:
            wi = text_img(w_, 150, "black", WHITE, 0)
            lt = t - 0.12 - k * 0.09
            if lt > 0:
                s = 1 + 0.5 * (1 - ease_out(lt / .14))
                paste(c, wi, xs + wi.width / 2, y, s, min(1, lt / .08))
            xs += f.getlength(w_ + " "); k += 1
        y += 165
    slow = 1 + 0.03 * t / max(d, .1)
    return zoom_img(c, slow)


def zoom_img(im, z, cx=0.5, cy=0.5):
    if abs(z - 1) < 0.002: return im
    w, h = W / z, H / z; x0 = (W - w) * cx; y0 = (H - h) * cy
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))


def big_text(t, d, text="TEXT", color=WHITE, bg="ink", size=170, sub=None, stamp=None):
    c = bg_solid(INK) if bg == "ink" else (bg_paper() if bg == "paper" else
                                         bg_solid(YELLOW) if bg == "yellow" else bg_ocean(t))
    fill = color if bg != "paper" else INK
    if bg == "yellow": fill = INK
    s = ease_back(t / 0.22)
    ti = text_img(text, size, "black", fill); fit = min(1, 1700 / ti.width)
    paste(c, ti, W / 2, H / 2 - (40 if sub else 0), fit * (0.6 + 0.4 * s + 0.02 * t), min(1, t / .06))
    if sub:
        paste(c, text_img(sub, 54, "bold", (fill if bg != "ink" else (200, 200, 200))), W / 2, H / 2 + size * .62, 1, ease_out((t - .25) / .3))
    if stamp: draw_stamp(c, stamp[0], W / 2 + 330, H / 2 + 170, t - stamp[1], KRABS, 90)
    return c


def typewriter(t, d, lines=("JULY 31, 1999",), size=120, sub=None, cps=14, bg="paper"):
    c = bg_paper() if bg == "paper" else bg_solid(INK)
    fill = INK if bg == "paper" else WHITE
    total = sum(len(l) for l in lines); shown = int(t * cps)
    y = H / 2 - (len(lines) - 1) * size * 0.6 - (40 if sub else 0)
    for l in lines:
        s = l[:max(0, shown)]; shown -= len(l)
        if s:
            im = text_img(s, size, "type", fill)
            full = text_img(l, size, "type", fill)
            c.paste(im, (int(W / 2 - full.width / 2), int(y - full.height / 2)), im)
        y += size * 1.2
    if sub and t > total / cps + .2:
        paste(c, text_img(sub, 48, "bold", (KRABS)), W / 2, y + 10, 1, ease_out((t - total / cps - .2) / .3))
    # cursor blink
    return c


def counter(t, d, a=1999, b=2026, label="YEARS", suffix="", roll=1.6, color=YELLOW):
    c = bg_ocean(t)
    x = ease_in_out(t / roll); v = int(round(a + (b - a) * x))
    paste(c, text_img(f"{v}{suffix}", 330, "black", color), W / 2, H / 2 - 50, 1 + .015 * t)
    paste(c, text_img(label, 64, "bold", WHITE), W / 2, H / 2 + 170, 1, ease_out((t - .3) / .3))
    return c


def vs_card(t, d, left="LEMONADE STAND", right="COSTCO PARKING LOT", lc=YELLOW, rc=KAREN, sub=None):
    c = bg_ocean(t); dr = ImageDraw.Draw(c)
    sl = ease_back(t / .25); sr = ease_back((t - .35) / .25)
    paste(c, shadow(text_img(left.replace(" ", "\n", 1) if len(left) > 12 else left, 110, "black", lc)), W * .24, H / 2, sl)
    paste(c, shadow(text_img(right.replace(" ", "\n", 1) if len(right) > 12 else right, 110, "black", rc)), W * .76, H / 2, sr)
    if t > .25: paste(c, text_img("vs", 90, "serif", WHITE), W / 2, H / 2, ease_back((t - .25) / .2))
    if sub: paste(c, text_img(sub, 52, "bold", (210, 210, 210)), W / 2, H - 170, 1, ease_out((t - .8) / .3))
    return c


def map_street(t, d, left="KRUSTY KRAB", right="CHUM BUCKET", note="≈ ONE STREET"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    # street
    dr.rectangle([W // 2 - 150, 0, W // 2 + 150, H], fill=(70, 70, 75))
    for y in range(-60, H, 120):
        yy = y + int(t * 90) % 120
        dr.rectangle([W // 2 - 8, yy, W // 2 + 8, yy + 60], fill=(240, 220, 90))
    for i, (lab, col, cx) in enumerate([(left, KRABS, W * .23), (right, PLANK, W * .77)]):
        s = ease_back((t - i * .25) / .3)
        if s <= 0: continue
        bw, bh = int(560 * s), int(380 * s)
        blk = Image.new("RGBA", (bw + 1, bh + 1), (0, 0, 0, 0)); bd = ImageDraw.Draw(blk)
        bd.rectangle([0, 0, bw, bh], fill=col + (255,), outline=INK + (255,), width=max(1, int(10 * s)))
        c.paste(blk, (int(cx - bw / 2), int(H / 2 - bh / 2)), blk)
        paste(c, text_img(lab, 60, "black", WHITE, 4), cx, H / 2, s)
    # arrow
    p = ease_out((t - .7) / .5)
    if p > 0:
        x0, x1 = W * .23 + 290, W * .77 - 290; xm = x0 + (x1 - x0) * p
        dr.line([x0, H * .2, xm, H * .2], fill=INK, width=10)
        if p > .95:
            for xx, sgn in ((x0, 1), (x1, -1)):
                dr.polygon([(xx, H * .2), (xx + 34 * sgn, H * .2 - 22), (xx + 34 * sgn, H * .2 + 22)], fill=INK)
            paste(c, text_img(note, 58, "black", INK), W / 2, H * .2 - 62, ease_back((t - 1.2) / .25))
    return c


def magnify(t, d):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    cx, cy = W * .5, H * .52
    dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=PLANK)
    paste(c, text_img("HILLENBURG'S ORIGINAL PLAN", 64, "black", INK), W / 2, 150, 1, ease_out(t / .3))
    p = ease_out((t - .4) / .8)
    mx = cx + (1 - p) * 700; my = cy + (1 - p) * 300; r = 220
    if p > 0:
        # lens: magnified dot
        lens = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); ld = ImageDraw.Draw(lens)
        ld.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=(250, 244, 230, 255))
        dx, dy = cx - mx, cy - my
        ld.ellipse([r + dx * 6 - 26, r + dy * 6 - 26, r + dx * 6 + 26, r + dy * 6 + 26], fill=PLANK + (255,))
        mask = Image.new("L", lens.size, 0); ImageDraw.Draw(mask).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
        c.paste(lens, (int(mx - r), int(my - r)), mask)
        dr.ellipse([mx - r, my - r, mx + r, my + r], outline=INK, width=22)
        ang = math.radians(45)
        dr.line([mx + r * math.cos(ang), my + r * math.sin(ang), mx + (r + 260) * math.cos(ang), my + (r + 260) * math.sin(ang)], fill=INK, width=48)
    if t > 1.4:
        paste(c, text_img("(that's him)", 54, "bold", KRABS), cx - 330, cy + 260, 1, ease_out((t - 1.4) / .3), 6)
        dr.line([cx - 250, cy + 220, cx - 20, cy + 20], fill=KRABS, width=6)
    return c


def strike(t, d, top="PLANNED: 1–2 EPISODES", bottom="ACTUAL: 27 YEARS"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    a = text_img(top, 110, "type", INK); paste(c, a, W / 2, H * .38, 1, ease_out(t / .2))
    p = ease_out((t - .5) / .35)
    if p > 0:
        x0 = W / 2 - a.width / 2 - 20; dr.line([x0, H * .38 + 6, x0 + (a.width + 40) * p, H * .38 - 6], fill=KRABS, width=16)
    if t > .9: paste(c, text_img(bottom, 120, "black", KRABS), W / 2, H * .62, ease_back((t - .9) / .25), 1, -3)
    return c


def chat(t, d, msgs=(("NICKELODEON", "Can we get a famous guest star?"), ("HILLENBURG", "No. It's Doug.")), note="(paraphrased)", step=1.1):
    c = bg_ocean(t)
    y = 300
    for i, (who, msg) in enumerate(msgs):
        lt = t - i * step
        if lt < 0: break
        left = i % 2 == 0
        f = font(64, "bold"); tw = int(f.getlength(msg)) + 90
        bub = Image.new("RGBA", (tw, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
        bd.rounded_rectangle([0, 0, tw - 1, 149], 50, fill=(WHITE if left else KAREN) + (255,))
        bd.text((45, 38), msg, font=f, fill=INK if left else WHITE)
        cx = 140 + tw / 2 if left else W - 140 - tw / 2
        s = ease_back(lt / .25)
        paste(c, text_img(who, 40, "bold", (180, 200, 215)), cx - tw / 2 + 110 if left else cx + tw / 2 - 110, y - 20, 1, min(1, lt / .1))
        paste(c, shadow(bub, 6, 10, 100), cx, y + 95, s)
        y += 260
    if note: paste(c, text_img(note, 36, "bold", (150, 170, 185)), W - 200, H - 60)
    return c


def nameplate(t, d, name="MR. LAWRENCE", role="voice of Plankton since 1999", color=PLANK):
    c = bg_ocean(t); dr = ImageDraw.Draw(c)
    p = ease_out(t / .35)
    bw = int(1300 * p)
    dr.rectangle([W / 2 - 650, H / 2 - 150, W / 2 - 650 + bw, H / 2 + 150], fill=INK)
    dr.rectangle([W / 2 - 650, H / 2 - 150, W / 2 - 650 + min(bw, 26), H / 2 + 150], fill=color)
    if t > .2:
        paste(c, text_img(name, 120, "black", WHITE), W / 2 + 10, H / 2 - 40, 1, ease_out((t - .2) / .2))
        paste(c, text_img(role, 52, "bold", color), W / 2 + 10, H / 2 + 75, 1, ease_out((t - .35) / .25))
    return c


def checklist(t, d, items=("STEAL THE FORMULA", "MAKE KRABBY PATTIES", "BANKRUPT MR. KRABS", "RULE THE WORLD (?)"),
              title="THE PLAN", reveal=None, stamp_at=None, stamp="FAILED"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    paste(c, text_img(title, 96, "black", INK), W / 2, 150)
    reveal = reveal or [0.3 + i * 0.7 for i in range(len(items))]
    for i, it in enumerate(items):
        lt = t - reveal[i]
        if lt < 0: continue
        y = 330 + i * 150
        dr.rectangle([420, y - 40, 500, y + 40], outline=INK, width=8)
        paste(c, text_img(f"{i + 1}. {it}", 74, "type", INK), 520 + text_img(f"{i + 1}. {it}", 74, "type", INK).width / 2, y, 1, min(1, lt / .1))
    if stamp_at is not None: draw_stamp(c, stamp, W / 2 + 120, H / 2 + 60, t - stamp_at, KRABS, 200, -12)
    return c


def scoreboard(t, d, p="0", k="∞", note=None, flip=None):
    c = bg_solid((10, 10, 12)); dr = ImageDraw.Draw(c)
    dr.rounded_rectangle([160, 200, W - 160, H - 200], 40, fill=(24, 24, 28), outline=(60, 60, 66), width=8)
    for i, (lab, val, col, cx) in enumerate([("PLANKTON", p, PLANK, W * .3), ("KRABS", k, KRABS, W * .7)]):
        paste(c, text_img(lab, 70, "black", col), cx, 310)
        v = val
        if flip and flip[0] == i and t < flip[2]: v = flip[1]
        im = text_img(v, 330, "type", (255, 190, 40))
        g = im.filter(ImageFilter.GaussianBlur(14))
        paste(c, g, cx, H / 2 + 60, 1, .8); paste(c, im, cx, H / 2 + 60)
    dr.line([W / 2, 260, W / 2, H - 260], fill=(60, 60, 66), width=6)
    if note: paste(c, text_img(note, 46, "bold", (200, 200, 200)), W / 2, H - 120, 1, ease_out((t - .4) / .3))
    return c


def three_versions(t, d, active=None, unreliable=(), titles=("KRABS", "PLANKTON", "KAREN"), stamp_t=0.25):
    c = bg_ocean(t); dr = ImageDraw.Draw(c)
    cols = [KRABS, PLANK, KAREN]
    for i in range(3):
        cx = W * (0.2 + 0.3 * i); s = ease_back((t - i * .12) / .25)
        if s <= 0: continue
        on = active is None or active == i
        pw, ph = int(460 * s), int(640 * s)
        pan = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(pan)
        pd.rounded_rectangle([0, 0, pw - 1, ph - 1], 30, fill=(cols[i] if on else (55, 60, 66)) + (255,), outline=INK + (255,), width=10)
        z = 1.06 if active == i else 1
        paste(c, shadow(pan, 10, 14, 120), cx, H / 2 + 20, z)
        paste(c, text_img(f"VERSION {i + 1}", 52, "bold", WHITE if on else (150, 150, 150)), cx, H / 2 - 170 * z, s * z)
        paste(c, text_img(titles[i], 80 if len(titles[i]) < 7 else 66, "black", WHITE if on else (150, 150, 150)), cx, H / 2 + 20, s * z)
        if i in unreliable:
            draw_stamp(c, "UNRELIABLE", cx, H / 2 + 200, t - stamp_t - .1 * i if i == max(unreliable) else 5, INK, 54, -14)
    return c


def equation(t, d, parts=(("PLANKTON", PLANK), ("+", WHITE), ("KRABS", KRABS), ("=", WHITE), ("PLABS", YELLOW)), times=None):
    c = bg_ocean(t)
    times = times or [0, .45, .8, 1.25, 1.5]
    xs = [W * .16, W * .33, W * .46, W * .6, W * .8]
    for (txt, col), x, tt in zip(parts, xs, times):
        lt = t - tt
        if lt < 0: continue
        sz = 104 if txt not in "+=" else 110
        if txt == "PLABS": sz = 150
        paste(c, shadow(text_img(txt, sz, "black", col)), x, H / 2, ease_back(lt / .22))
    return c


def rip_paper(t, d, rip_at=0.6, label=None, title="SECRET RECIPE", halves=("", "")):
    c = bg_ocean(t)
    pw, ph = 760, 900
    paper = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(paper)
    pd.rectangle([0, 0, pw - 1, ph - 1], fill=PAPER + (255,))
    for y in range(230, ph - 60, 70): pd.line([60, y, pw - 60, y], fill=(190, 175, 150, 255), width=3)
    tw = text_img(title, 70, "black", INK); paper.paste(tw, ((pw - tw.width) // 2, 80), tw)
    rng = random.Random(4)
    for y in range(250, ph - 80, 70):
        x = 70;
        while x < pw - 120:
            w_ = rng.randint(40, 140); pd.rectangle([x, y - 30, x + w_, y - 12], fill=(90, 80, 70, 255)); x += w_ + 25
    # jagged split
    pts = [(pw / 2 + rng.randint(-30, 30), y) for y in range(0, ph + 1, 45)]
    left = Image.new("L", (pw, ph), 0); ImageDraw.Draw(left).polygon([(0, 0)] + pts + [(0, ph)], fill=255)
    right = Image.new("L", (pw, ph), 0); ImageDraw.Draw(right).polygon([(pw, 0)] + pts + [(pw, ph)], fill=255)
    L = paper.copy(); L.putalpha(Image.composite(paper.split()[3], Image.new("L", (pw, ph), 0), left))
    R = paper.copy(); R.putalpha(Image.composite(paper.split()[3], Image.new("L", (pw, ph), 0), right))
    sep = ease_out((t - rip_at) / .5) * 260 if t > rip_at else (math.sin(t * 60) * 3 if t > rip_at - .3 else 0)
    rot = ease_out((t - rip_at) / .5) * 7 if t > rip_at else 0
    for im, sgn in ((L, -1), (R, 1)):
        paste(c, shadow(im, 8, 12, 110), W / 2 + sgn * sep, H / 2 + 20, 1, 1, -sgn * rot)
    if t > rip_at + .4:
        for (txt, col), sgn in zip(halves, (-1, 1)):
            if txt: paste(c, shadow(text_img(txt, 60, "black", col, 4)), W / 2 + sgn * (sep + 200), H - 120, ease_back((t - rip_at - .4) / .25))
    if label: paste(c, text_img(label, 70, "black", WHITE, 5), W / 2, 90, 1, ease_out(t / .2))
    return c


def evidence(t, d, n=4, title="CASE FILE: THE KRABBY PATTY",
             fields=(("INVENTED BY", "TWO KIDS"), ("METHOD", "ACCIDENT"), ("OCCASION", "A BREAKUP"), ("CREDITED TO", "ONE CRAB")),
             stamp_last=True):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    paste(c, text_img(title, 76, "black", INK), W / 2, 150)
    dr.line([300, 210, W - 300, 210], fill=INK, width=6)
    for i, (k, v) in enumerate(fields[:n]):
        y = 330 + i * 160
        newest = i == n - 1
        ks = text_img(k + ":", 64, "type", (90, 80, 70))
        c.paste(ks, (330, int(y - ks.height / 2)), ks)
        shown = v if not newest else v[:int(t * 18)]
        if shown:
            vs = text_img(shown, 84, "black", KRABS if (newest and stamp_last and n == len(fields)) else INK)
            c.paste(vs, (900, int(y - vs.height / 2)), vs)
    if stamp_last and n == len(fields):
        draw_stamp(c, "CLOSED?", W - 420, H - 170, t - .7, KRABS, 90, -10)
    return c


def error_card(t, d, title="CONTINUITY ERROR", body="\"Enemy In-Law\" (2005) calls it\nan old Krabs FAMILY recipe.", stamp="IGNORED", stamp_at=1.0):
    c = bg_solid((20, 20, 24)); dr = ImageDraw.Draw(c)
    dr.rectangle([260, 260, W - 260, H - 260], fill=(36, 36, 42), outline=(255, 80, 80), width=8)
    dr.rectangle([260, 260, W - 260, 360], fill=(255, 80, 80))
    paste(c, text_img("⚠ " + title, 64, "black", WHITE), W / 2, 310)
    paste(c, text_img(body, 60, "bold", WHITE), W / 2, H / 2 + 60, 1, ease_out((t - .15) / .2))
    draw_stamp(c, stamp, W / 2 + 380, H - 280, t - stamp_at, YELLOW, 110, -10)
    return c


def exchange(t, d, rows=(("1¢", "one balloon", "for Plankton"), ("62¢", "one soul", "SpongeBob's")), title="MR. KRABS: EXCHANGE RATES"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    paste(c, text_img(title, 80, "black", INK), W / 2, 160)
    for i, (a, b, cmt) in enumerate(rows):
        lt = t - .3 - i * .8
        if lt < 0: continue
        y = 420 + i * 250
        paste(c, text_img(a, 170, "black", KRABS), 520, y, ease_back(lt / .2))
        paste(c, text_img("=", 120, "black", INK), 820, y, 1, min(1, lt / .1))
        paste(c, text_img(b, 100, "black", INK), 1240, y - 20, 1, min(1, lt / .15))
        paste(c, text_img(cmt, 50, "bold", GREY), 1240, y + 60, 1, min(1, (lt - .2) / .2))
    return c


def phone(t, d, handle="chum.bucket.official", viewer="krusty_krab_backup_2", sub="Story viewed by"):
    c = bg_ocean(t); dr = ImageDraw.Draw(c)
    s = ease_back(t / .3); pw, ph = int(560 * s), int(980 * s)
    if s <= 0: return c
    ph_ = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph_)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], int(70 * s), fill=(15, 15, 18, 255))
    pd.rounded_rectangle([int(24 * s), int(24 * s), pw - int(24 * s), ph - int(24 * s)], int(50 * s), fill=(250, 250, 250, 255))
    paste(c, shadow(ph_, 10, 16, 140), W / 2, H / 2)
    if t > .3:
        x0 = W / 2 - 230; y0 = H / 2 - 400
        dr.ellipse([x0, y0, x0 + 120, y0 + 120], fill=PLANK, outline=(230, 60, 120), width=8)
        dr.text((x0 + 135, y0 + 40), handle, font=font(30, "bold"), fill=INK)
        dr.rectangle([x0, y0 + 160, x0 + 460, y0 + 520], fill=(200, 230, 205))
        paste(c, text_img("BACK ON MY\nGRIND 💪" if False else "BACK ON MY\nGRIND", 54, "black", INK), x0 + 230, y0 + 340)
    if t > 1.0:
        x0 = W / 2 - 230; y0 = H / 2 + 170
        dr.text((x0, y0), sub, font=font(34, "bold"), fill=GREY)
        lt = t - 1.0
        for i, v in enumerate([viewer, "krabs_robot_unit", "not_mr_krabs_99"]):
            if lt > i * .5:
                dr.ellipse([x0, y0 + 60 + i * 80, x0 + 56, y0 + 116 + i * 80], fill=KRABS)
                dr.text((x0 + 76, y0 + 70 + i * 80), v, font=font(32, "bold"), fill=INK)
    return c


def watch_loop(t, d):
    c = bg_ocean(t); dr = ImageDraw.Draw(c)
    nodes = [("PLANKTON", PLANK, W * .2, H * .32), ("ROBOT\nPLANKTON", PLANK, W * .2, H * .72),
             ("KRABS", KRABS, W * .8, H * .32), ("ROBOT\nKRABS", KRABS, W * .8, H * .72)]
    for i, (lab, col, x, y) in enumerate(nodes):
        lt = t - i * .3
        if lt < 0: continue
        im = text_img(lab, 64, "black", WHITE)
        bx = Image.new("RGBA", (im.width + 80, im.height + 60), col + (255,))
        bx.paste(im, (40, 30), im)
        paste(c, shadow(bx, 8, 10, 120), x, y, ease_back(lt / .25))
    if t > 1.3:
        p = ease_out((t - 1.3) / .6)
        for y in (H * .32, H * .72):
            xa, xb = W * .2 + 260, W * .8 - 260
            dr.line([xa, y, xa + (xb - xa) * p, y], fill=YELLOW, width=10)
        if p > .9:
            paste(c, text_img("👀 WATCHING 👀" if False else "WATCHING EACH OTHER", 60, "black", YELLOW), W / 2, H * .52, ease_back((t - 1.9) / .25))
    return c


def pie(t, d, title="THINGS PLANKTON DOES", sub="(according to Mr. Krabs)", label="ABOUT KRABS: 100%"):
    c = bg_paper(); dr = ImageDraw.Draw(c)
    paste(c, text_img(title, 80, "black", INK), W / 2, 130); paste(c, text_img(sub, 48, "bold", GREY), W / 2, 210)
    p = ease_out((t - .2) / 1.0)
    cx, cy, r = W / 2 - 250, H / 2 + 90, 300
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 210, 190), outline=INK, width=8)
    if p > 0: dr.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * p, fill=KRABS, outline=INK, width=8)
    if t > 1.3:
        dr.rectangle([cx + r + 120, cy - 30, cx + r + 170, cy + 20], fill=KRABS, outline=INK, width=4)
        li = text_img(label, 64, "black", INK); paste(c, li, cx + r + 200 + li.width / 2, cy - 5, ease_back((t - 1.3) / .25))
    return c


def heartbreak(t, d, text="A BREAKUP."):
    c = bg_solid(INK); dr = ImageDraw.Draw(c)
    def heart(sz):
        im = Image.new("RGBA", (sz * 2, sz * 2), (0, 0, 0, 0)); hd = ImageDraw.Draw(im)
        pts = []
        for a in np.linspace(0, 2 * np.pi, 120):
            x = 16 * np.sin(a) ** 3; y = 13 * np.cos(a) - 5 * np.cos(2 * a) - 2 * np.cos(3 * a) - np.cos(4 * a)
            pts.append((sz + x * sz / 17, sz - y * sz / 17))
        hd.polygon(pts, fill=KRABS + (255,)); return im
    h = heart(260)
    split = ease_out((t - .6) / .4) * 70 if t > .6 else 0
    m = Image.new("L", h.size, 0); md = ImageDraw.Draw(m)
    zig = [(260 + (25 if i % 2 else -25), y) for i, y in enumerate(range(0, 521, 52))]
    md.polygon([(0, 0)] + zig + [(0, 520)], fill=255)
    L = h.copy(); L.putalpha(Image.composite(h.split()[3], Image.new("L", h.size, 0), m))
    R = h.copy(); R.putalpha(Image.composite(Image.new("L", h.size, 0), h.split()[3], m))
    s = ease_back(t / .25)
    paste(c, L, W / 2 - split, H / 2 - 90, s, 1, split * .15); paste(c, R, W / 2 + split, H / 2 - 90, s, 1, -split * .15)
    if t > .7: paste(c, text_img(text, 130, "black", WHITE), W / 2, H - 170, ease_back((t - .7) / .2))
    return c


def verdict(t, d, lit=None, title="WHO'S THE BAD GUY?"):
    c = bg_solid((12, 10, 10)); dr = ImageDraw.Draw(c)
    paste(c, text_img(title, 90, "black", WHITE), W / 2, 170, 1, ease_out(t / .3))
    for i, (lab, col, cx) in enumerate([("KRABS", KRABS, W * .3), ("PLANKTON", PLANK, W * .7)]):
        on = lit is None or lit == i
        flick = 1 if lit is not None else (0.55 + 0.45 * abs(math.sin(t * 7 + i * 2)))
        b = (1 if on else .22) * flick
        # spotlight cone
        cone = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(cone)
        cd.polygon([(cx - 60, 0), (cx + 60, 0), (cx + 330, H - 200), (cx - 330, H - 200)], fill=(255, 250, 220, int(55 * b)))
        c.paste(cone, (0, 0), cone.filter(ImageFilter.GaussianBlur(20)))
        plate = Image.new("RGBA", (560, 170), (0, 0, 0, 0)); pd = ImageDraw.Draw(plate)
        pd.rounded_rectangle([0, 0, 559, 169], 20, fill=tuple(int(v * (0.35 + 0.65 * b)) for v in col) + (255,), outline=(200, 170, 90, 255), width=8)
        im = text_img(lab, 96, "black", WHITE); plate.paste(im, ((560 - im.width) // 2, (170 - im.height) // 2), im)
        paste(c, shadow(plate), cx, H - 280, 1.08 if (lit == i) else 1)
        if lit is None: paste(c, text_img("?", 200, "black", (230, 230, 230)), cx, H / 2 - 60, 1, b)
    return c


def balloon(t, d, text="1¢", rise=True):
    c = bg_solid((10, 14, 20)); dr = ImageDraw.Draw(c)
    y = H * .45 - (t * 40 if rise else 0); x = W / 2 + math.sin(t * 1.3) * 18
    # string
    pts = [(x + math.sin(t * 2 + k * .4) * 10 * (k / 12), y + 150 + k * 40) for k in range(14)]
    dr.line(pts, fill=(200, 200, 200), width=4)
    b = Image.new("RGBA", (300, 380), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
    bd.ellipse([10, 10, 290, 340], fill=KRABS + (255,)); bd.polygon([(150, 330), (130, 370), (170, 370)], fill=KRABS + (255,))
    bd.ellipse([70, 60, 120, 140], fill=(255, 140, 130, 200))
    paste(c, b, x, y, 1, min(1, t / .4))
    if text: paste(c, text_img(text, 110, "black", WHITE), W / 2, H - 140, 1, ease_out((t - .4) / .4))
    return c


def coins(t, d, text="every penny after that", n=70):
    c = bg_solid((10, 14, 20)); dr = ImageDraw.Draw(c)
    rng = random.Random(9)
    landed = 0
    for i in range(n):
        t0 = i * 0.045; x = W / 2 + rng.gauss(0, 170)
        ty = H - 160 - (i // 7) * 14 - rng.random() * 30
        lt = t - t0
        if lt < 0: break
        y = min(ty, -60 + 2400 * lt * lt)
        if y >= ty: landed += 1
        rx = 60; ry = 18 if y >= ty else 40
        dr.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(214, 168, 60), outline=(120, 84, 20), width=5)
    paste(c, text_img(text, 70, "bold", (230, 230, 230)), W / 2, 170, 1, ease_out(t / .4))
    paste(c, text_img(f"${landed * 0.01:.2f}", 60, "type", (214, 168, 60)), W - 260, 170)
    return c


def watchlist(t, d, eps=("PLANKTON!", "F.U.N.", "FRIEND OR FOE", "ENEMY IN-LAW", "ONE COARSE MEAL", "PLANKTON RETIRES",
                          "PLANKTON'S REGULAR", "SINGLE CELL ANNIVERSARY", "IMITATION KRABS", "BORN AGAIN KRABS",
                          "THE ALGAE'S ALWAYS GREENER", "PLANKTON'S PET")):
    c = bg_solid((14, 14, 18)); dr = ImageDraw.Draw(c)
    cols, tw, th = 3, 540, 190
    off = t * 40
    for i, e in enumerate(eps):
        r, k = divmod(i, cols)
        x = 120 + k * (tw + 60); y = 120 + r * (th + 50) - off
        lt = t - i * .1
        if lt < 0: continue
        dr.rounded_rectangle([x, y, x + tw, y + th], 18, fill=(34, 34, 42))
        im = text_img(e, 44 if len(e) < 18 else 34, "black", WHITE); c.paste(im, (int(x + 30), int(y + th / 2 - im.height / 2)), im)
        if lt > .25:
            dr.ellipse([x + tw - 80, y + 20, x + tw - 20, y + 80], fill=PLANK)
            dr.line([(x + tw - 66, y + 52), (x + tw - 54, y + 64), (x + tw - 32, y + 36)], fill=WHITE, width=7)
        dr.rectangle([x, y + th - 12, x + tw * min(1, lt / .6), y + th], fill=KRABS)
    paste(c, text_img("WATCHED", 64, "black", YELLOW), W / 2, H - 70)
    return c


def end_black(t, d, text=""):
    c = bg_solid((0, 0, 0))
    if text: paste(c, text_img(text, 60, "type", (220, 220, 220)), W / 2, H / 2, 1, ease_out(t / .4))
    return c


def placeholder(clip_id, desc, t):
    c = bg_solid((28, 30, 36)); dr = ImageDraw.Draw(c)
    for x in range(0, W, 120): dr.line([x, 0, x, H], fill=(36, 38, 46), width=2)
    for y in range(0, H, 120): dr.line([0, y, W, y], fill=(36, 38, 46), width=2)
    paste(c, text_img(f"CLIP {clip_id}", 120, "black", (255, 200, 60)), W / 2, H / 2 - 120)
    lines, cur = [], ""
    for w_ in desc.split(" "):
        if len(cur) + len(w_) > 46: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    lines.append(cur)
    paste(c, text_img("\n".join(lines[:4]), 48, "bold", (220, 220, 220)), W / 2, H / 2 + 80)
    return c


GFX = {k: v for k, v in globals().items() if callable(v) and k in (
    "title_card big_text typewriter counter vs_card map_street magnify strike chat nameplate checklist scoreboard "
    "three_versions equation rip_paper evidence error_card exchange phone watch_loop pie heartbreak verdict balloon "
    "coins watchlist end_black").split()}
