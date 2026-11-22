"""Card + overlay renderers for the edit. Everything here is original graphics, real photos,
source-document crops, or the user's own clips. No show character artwork is drawn."""
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import gfx
from gfx import W, H, INK, RED, WHITE, PAPER, font, ease_out, ease_back

ROOT = gfx.ROOT
A = lambda *p: os.path.join(ROOT, "assets", *p)
GREEN = (90, 255, 150)
YELLOW = (255, 214, 64)


# ---------------------------------------------------------------- helpers
def place(frame, img, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if img is None or alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        img = img.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 0.99:
        img = img.copy()
        img.putalpha(img.split()[-1].point(lambda a: int(a * alpha)))
    x, y = int(cx - img.width / 2), int(cy - img.height / 2)
    if x >= W or y >= H or x + img.width <= 0 or y + img.height <= 0:
        return
    frame.alpha_composite(img, (max(0, x), max(0, y)),
                          (max(0, -x), max(0, -y)))


def fit(img, maxw, maxh):
    s = min(maxw / img.width, maxh / img.height)
    return img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)


def text_img(text, fnt, fill, stroke=0, stroke_fill=(0, 0, 0), pad=10):
    b = fnt.getbbox(text, stroke_width=stroke)
    img = Image.new("RGBA", (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - b[0], pad - b[1]), text, font=fnt, fill=fill,
                             stroke_width=stroke, stroke_fill=stroke_fill)
    return img


@lru_cache(512)
def ctext(text, fname, size, fill, stroke=0):
    return text_img(text, font(fname, size), fill, stroke=stroke, stroke_fill=(0, 0, 0))


def wrap(text, fnt, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if fnt.getlength(t) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


@lru_cache(None)
def shadowed(key, img_fn):
    img = img_fn()
    sh, pad = gfx.drop_shadow(img)
    return sh


def with_shadow(img, blur=16, off=(12, 16), opacity=150):
    sh, _ = gfx.drop_shadow(img, off, blur, opacity)
    return sh


@lru_cache(None)
def corkboard():
    rng = np.random.default_rng(11)
    base = np.ones((H, W, 3)) * np.array([150, 108, 70], float)
    n = Image.fromarray((rng.random((H // 6, W // 6)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    base *= (0.85 + 0.25 * np.asarray(n, float) / 255)[..., None]
    base += rng.normal(0, 10, (H, W, 1))
    speck = rng.random((H, W)) > 0.996
    base[speck] *= 0.5
    y = np.linspace(-1, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    base *= (1 - 0.35 * (x ** 2 * 0.5 + y ** 2))[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


@lru_cache(None)
def desk():
    return gfx.desk_background().convert("RGBA")


def index_card(lines, w=430, red=True, seed=0):
    f = font("type", 34)
    lh = 44
    h = 60 + lh * len(lines)
    img = Image.new("RGBA", (w, h), (250, 248, 240, 255))
    d = ImageDraw.Draw(img)
    for yy in range(56, h, lh):
        d.line((0, yy + 8, w, yy + 8), fill=(170, 200, 230, 255), width=2)
    if red:
        d.line((0, 44, w, 44), fill=RED + (255,), width=3)
    for i, ln in enumerate(lines):
        d.text((22, 12 + lh * i + (8 if i else 0)), ln, font=f, fill=INK)
    return img


def pin_img():
    img = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 34, 34), fill=(190, 25, 30, 255))
    d.ellipse((12, 10, 22, 20), fill=(255, 140, 140, 255))
    return img


def red_string(d, p0, p1, prog=1.0, sag=40):
    pts = []
    n = 30
    for i in range(int(n * prog) + 1):
        u = i / n
        x = p0[0] + (p1[0] - p0[0]) * u
        y = p0[1] + (p1[1] - p0[1]) * u + math.sin(math.pi * u) * sag
        pts.append((x, y))
    if len(pts) > 1:
        d.line(pts, fill=(185, 20, 25, 255), width=5, joint="curve")


# ---------------------------------------------------------------- video frames
class ClipReader:
    """Sequential frame reader for a video file (restarts on seek)."""
    _open = {}

    def __init__(self, path):
        self.path, self.proc, self.pos, self.last = path, None, None, None

    @classmethod
    def get(cls, path):
        if path not in cls._open:
            cls._open[path] = ClipReader(path)
        return cls._open[path]

    def frame(self, t, size=(W, H), fps=30):
        idx = int(round(t * fps))
        if self.proc is None or self.pos is None or idx < self.pos or idx > self.pos + 90:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(
                ["ffmpeg", "-loglevel", "error", "-ss", f"{idx / fps:.3f}", "-i", self.path,
                 "-vf", f"fps={fps},scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,"
                        f"pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2",
                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.pos = idx - 1
            self.size = size
        nbytes = size[0] * size[1] * 3
        while self.pos < idx:
            buf = self.proc.stdout.read(nbytes)
            if len(buf) < nbytes:
                break
            self.last = Image.frombytes("RGB", size, buf)
            self.pos += 1
        return (self.last or Image.new("RGB", size, (0, 0, 0))).convert("RGBA")


def media_frame(path, label, t, size):
    """Frame from a user clip if it exists, otherwise a labelled placeholder."""
    if path and os.path.exists(path):
        return ClipReader.get(path).frame(t, size)
    return placeholder(label, size)


@lru_cache(64)
def placeholder(label, size):
    """Episode file card (paper) shown where footage would go."""
    import re as _re
    label = _re.sub(r"^[BC]\d\d[a-z]?\s+", "", label)
    w, h = size
    img = gfx.paper_texture((w, h), seed=len(label), color=(232, 220, 190)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, int(h * 0.16)), fill=(40, 36, 32, 255))
    d.text((int(w * 0.04), int(h * 0.035)), "EPISODE FILE", font=font("oswald", int(h * 0.075)), fill=(235, 225, 200))
    f = font("anton", int(h * 0.15))
    lines = wrap(label.upper(), f, w * 0.86)
    y = h * 0.55 - len(lines) * h * 0.09
    for ln in lines:
        d.text(((w - f.getlength(ln)) / 2, y), ln, font=f, fill=INK)
        y += h * 0.18
    for yy in range(int(h * 0.85), h, int(h * 0.05)):
        d.line((int(w * 0.06), yy, int(w * 0.94), yy), fill=(190, 170, 130, 255), width=2)
    return img


# ---------------------------------------------------------------- card base
class Card:
    """Main visual. Lives from t0 until the next card starts. Decorations have absolute times."""
    enter = "slide"
    sfx = None

    def __init__(self, t0, **kw):
        self.t0 = t0
        self.kw = kw
        self.decor = []  # (t, kind, params)
        self.push = kw.get("push", 0.035)
        self.enter = kw.get("enter", self.enter)
        self._cache = {}

    def cached(self, key, fn):
        if key not in self._cache:
            if len(self._cache) > 400:
                self._cache.clear()
            self._cache[key] = fn()
        return self._cache[key]

    # decoration builders --------------------------------------------------
    def stamp(self, t, text, x=1400, y=800, angle=-9, size=96, color=RED):
        self.decor.append((t, "stamp", dict(img=gfx.stamp(text, color, size, angle), x=x, y=y)))
        return self

    def note(self, t, text, x=1400, y=900, size=72, color=RED, angle=-4):
        self.decor.append((t, "note", dict(text=text, x=x, y=y, size=size, color=color, angle=angle)))
        return self

    def circle(self, t, x, y, w, h):
        self.decor.append((t, "circle", dict(x=x, y=y, w=w, h=h)))
        return self

    def strike(self, t, x0, y0, x1, y1, color=RED):
        self.decor.append((t, "strike", dict(p0=(x0, y0), p1=(x1, y1), color=color)))
        return self

    def source(self, text):
        self.decor.append((self.t0, "source", dict(text=text)))
        return self

    def caption(self, t, text, y=930, t1=None):
        self.decor.append((t, "caption", dict(text=text, y=y, t1=t1)))
        return self

    # rendering -----------------------------------------------------------
    def content(self, frame, t, life):
        pass

    def background(self):
        return desk()

    def draw_decor(self, frame, t):
        d = ImageDraw.Draw(frame)
        for t0, kind, p in self.decor:
            if t < t0:
                continue
            k = t - t0
            if kind == "stamp":
                s = 1.7 - 0.7 * ease_back(k / 0.13)
                place(frame, p["img"], p["x"], p["y"], s, alpha=min(1, k / 0.06))
            elif kind == "note":
                f = font("marker", p["size"])
                img = text_img(p["text"], f, p["color"] + (255,))
                n = max(1, int(img.width * ease_out(k / 0.45)))
                img = img.crop((0, 0, n, img.height))
                place(frame, img.rotate(p["angle"], expand=True, resample=Image.BICUBIC),
                      p["x"] - (img.width - n) / 2 * 0, p["y"])
            elif kind == "circle":
                c = gfx.marker_circle((p["w"], p["h"]), k / 0.55)
                place(frame, c, p["x"], p["y"])
            elif kind == "strike":
                u = ease_out(k / 0.3)
                (x0, y0), (x1, y1) = p["p0"], p["p1"]
                d.line((x0, y0, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u), fill=p["color"] + (255,), width=16)
            elif kind == "source":
                f = font("oswald", 26)
                txt = "SOURCE: " + p["text"]
                tw = f.getlength(txt)
                d.rectangle((40, H - 74, 40 + tw + 30, H - 30), fill=(0, 0, 0, 170))
                d.text((55, H - 72), txt, font=f, fill=(230, 230, 225))
            elif kind == "caption":
                if p["t1"] and t > p["t1"]:
                    continue
                f = font("anton", 64)
                img = text_img(p["text"], f, WHITE + (255,), pad=18)
                bg = Image.new("RGBA", img.size, RED + (235,))
                bg.alpha_composite(img)
                place(frame, bg, W / 2, p["y"], 0.8 + 0.2 * ease_back(k / 0.18))


# ---------------------------------------------------------------- card types
class TextSlam(Card):
    """Big kinetic words. lines: list of (text, color). times: per-line appearance times."""
    enter = "cut"

    def content(self, frame, t, life):
        lines = self.kw["lines"]
        times = self.kw.get("times") or [self.t0] * len(lines)
        size = self.kw.get("size", 170)
        total = len(lines) * size * 1.08
        y = H / 2 - total / 2 + size * 0.54
        for (txt, col), tt in zip(lines, times):
            if t >= tt:
                k = t - tt
                img = ctext(txt, "anton", size, tuple(col) + (255,), 6)
                if img.width > W - 160:
                    img = fit(img, W - 160, img.height)
                place(frame, img, W / 2, y, 1.25 - 0.25 * ease_back(k / 0.16))
            y += size * 1.08


class Folder(Card):
    enter = "drop"

    def content(self, frame, t, life):
        img = self._img()
        k = ease_out(life / 0.35)
        place(frame, img, W / 2, H / 2 + 20 + (1 - k) * -520, 1.18 - 0.18 * k)

    @lru_cache(None)
    def _img(self):
        return with_shadow(gfx.folder(self.kw["label"]))


class Doc(Card):
    """A source-document crop lying on the desk, slowly zooming toward a focus point (fx, fy in 0..1)."""

    def content(self, frame, t, life):
        img = self._img()
        fx, fy = self.kw.get("focus", (0.5, 0.5))
        z = 1.0 + self.kw.get("zoom", 0.18) * ease_out(life / max(1.0, self.kw.get("zoom_time", 6.0)))
        cx = W / 2 + (0.5 - fx) * img.width * (z - 1)
        cy = H / 2 + (0.5 - fy) * img.height * (z - 1)
        place(frame, img, cx, cy, z)

    @lru_cache(None)
    def _img(self):
        im = Image.open(A(self.kw["file"])).convert("RGBA")
        im = fit(im, self.kw.get("w", 1500), self.kw.get("h", 860))
        paper = Image.new("RGBA", (im.width + 60, im.height + 60), (255, 255, 255, 255))
        paper.alpha_composite(im, (30, 30))
        paper = paper.rotate(self.kw.get("rot", 1.2), expand=True, resample=Image.BICUBIC)
        return with_shadow(paper)


class Photo(Card):
    """Polaroid-style real photo with handwritten caption and a pin."""

    def content(self, frame, t, life):
        img = self._img()
        k = ease_out(life / 0.4)
        place(frame, img, self.kw.get("x", W / 2) + (1 - k) * 900, H / 2 + 10, 1.0 + 0.04 * life / 6)

    @lru_cache(None)
    def _img(self):
        im = Image.open(A(self.kw["file"])).convert("RGB")
        crop = self.kw.get("crop")
        if crop:
            w0, h0 = im.size
            im = im.crop((int(crop[0] * w0), int(crop[1] * h0), int(crop[2] * w0), int(crop[3] * h0)))
        im = fit(im, self.kw.get("w", 760), self.kw.get("h", 700))
        b = 30
        pol = Image.new("RGBA", (im.width + 2 * b, im.height + b + 130), (248, 246, 240, 255))
        pol.paste(im, (b, b))
        d = ImageDraw.Draw(pol)
        f = font("marker", 46)
        cap = self.kw.get("caption", "")
        d.text(((pol.width - f.getlength(cap)) / 2, im.height + b + 30), cap, font=f, fill=INK)
        cr = self.kw.get("credit")
        if cr:
            f2 = font("oswald", 18)
            d.text((pol.width - f2.getlength(cr) - 16, pol.height - 30), cr, font=f2, fill=(120, 120, 120))
        pol.alpha_composite(pin_img(), (pol.width // 2 - 20, 4))
        pol = pol.rotate(self.kw.get("rot", -3), expand=True, resample=Image.BICUBIC)
        return with_shadow(pol)


class Media(Card):
    """B-roll or show still inside an evidence frame (placeholder until the user's clip exists)."""

    def content(self, frame, t, life):
        size = (1280, 720)
        src = self.kw.get("path")
        real = bool(src) and os.path.exists(os.path.join(ROOT, src))
        flip = 0.0
        if self.kw.get("flip_at") and t >= self.kw["flip_at"]:
            flip = round(ease_out((t - self.kw["flip_at"]) / 0.35), 2)

        def build():
            inner = media_frame(src and os.path.join(ROOT, src), self.kw.get("label", "B-ROLL"),
                                self.kw.get("src_in", 0.0) + life, size).convert("RGB")
            if flip:
                inner = inner.rotate(180 * flip, resample=Image.BILINEAR)
            return gfx.evidence_frame(inner, self.kw.get("tag", "EVIDENCE"), tilt=self.kw.get("tilt", 1.2))
        ev = build() if real else self.cached(("ev", flip), build)
        k = ease_out(life / 0.35)
        place(frame, ev, W / 2 + 60, H / 2 + 50, 0.9 + 0.035 * life / 6)


class Clip(Card):
    """Full-screen show clip with its own audio (audio handled in the mixer)."""
    enter = "cut"

    def content(self, frame, t, life):
        seg = self.kw["seg"]
        if not seg.get("real"):
            return self.transcript(frame, t, life, seg)
        img = media_frame(seg.get("path"), f"SHOW CLIP {seg['id']}", seg.get("src_in", 0) + life, (W, H))
        z = 1.0 + 0.04 * min(1, life / max(1, seg["dur"]))
        if self.kw.get("punch") and t >= self.kw["punch"]:
            z += 0.12 * ease_out((t - self.kw["punch"]) / 0.12)
        place(frame, img, W / 2, H / 2, z)
        d = ImageDraw.Draw(frame)
        f = font("oswald", 24)
        d.rectangle((W - 260, 40, W - 40, 80), fill=(0, 0, 0, 150))
        d.ellipse((W - 248, 52, W - 232, 68), fill=RED)
        d.text((W - 222, 44), f"EXHIBIT // {seg['id']}", font=f, fill=WHITE)

    def background(self):
        return None

    def transcript(self, frame, t, life, seg):
        from timeline import TRANSCRIPT
        head, lines = TRANSCRIPT[seg["id"]]
        frame.paste((14, 13, 12, 255), (0, 0, W, H))
        total = sum(len(x) for _, x in lines)
        n = int(total * min(1.0, life / max(0.6, seg["dur"] * 0.55)))
        key = ("tr", n)

        def build():
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            fh = font("oswald", 34)
            d.text((140, 150), "TRANSCRIPT  //  " + head, font=fh, fill=(200, 190, 170))
            d.line((140, 200, W - 140, 200), fill=RED + (255,), width=4)
            ft, fs = font("type", 66), font("oswald", 40)
            y = 270
            left = n
            for who, txt in lines:
                if left <= 0:
                    break
                shown = txt[:left]
                left -= len(txt)
                if who:
                    d.text((140, y + 14), who, font=fs, fill=RED + (255,))
                for ln in wrap(shown, ft, W - 560):
                    d.text((440, y), ln, font=ft, fill=(240, 235, 222))
                    y += 82
                y += 30
            return img
        frame.alpha_composite(self.cached(key, build))
        d = ImageDraw.Draw(frame)
        f = font("oswald", 24)
        d.rectangle((W - 300, 40, W - 40, 80), fill=(0, 0, 0, 150))
        d.ellipse((W - 288, 52, W - 272, 68), fill=RED)
        d.text((W - 262, 44), f"EXHIBIT // {seg['id']}", font=f, fill=WHITE)


class Quote(Card):
    """Typed quote revealed in sync with the narrator. words: list of (global_time, word)."""

    def build_card(self, t, n):
        text = self.kw["text"]
        who = self.kw.get("who", "")
        f = font("type", self.kw.get("size", 62))
        lines = wrap(text, f, 1450)
        card = Image.new("RGBA", (1620, 140 + 86 * len(lines) + 90), (244, 238, 222, 255))
        d = ImageDraw.Draw(card)
        n_total = len(text.split())
        shown = 0
        y = 70
        for ln in lines:
            ws = ln.split()
            part = " ".join(ws[:max(0, n - shown)])
            shown += len(ws)
            d.text((90, y), part, font=f, fill=INK)
            y += 86
        d.text((60, 30), "“", font=font("anton", 120), fill=RED)
        if n >= n_total:
            d.text((card.width - 90 - font("oswald", 36).getlength(who), y + 20), who,
                   font=font("oswald", 36), fill=(90, 80, 70))
        for strike in self.kw.get("strikes", []):  # (t, word_text, replacement)
            pass
        return card

    def content(self, frame, t, life):
        spoken = self.kw.get("words") or []
        n_total = len(self.kw["text"].split())
        n = n_total if not spoken else min(n_total, int(round(
            sum(1 for g, _ in spoken if g <= t) * n_total / max(1, len(spoken)))) + 1)
        img = self.cached(("q", n), lambda: with_shadow(self.build_card(t, n).rotate(
            -0.8, expand=True, resample=Image.BICUBIC)))
        k = ease_out(life / 0.3)
        place(frame, img, W / 2, H / 2 + (1 - k) * 300, 1 + 0.03 * life / 8)


class Letter(Quote):
    def content(self, frame, t, life):
        spoken = self.kw.get("words") or []
        n_total = len(self.kw["text"].split())
        n = n_total if not spoken else min(n_total, int(round(
            sum(1 for g, _ in spoken if g <= t) * n_total / max(1, len(spoken)))) + 1)
        img = self.cached(("l", n), lambda: with_shadow(self.letter(t).rotate(1.5, expand=True,
                                                                               resample=Image.BICUBIC)))
        place(frame, img, W / 2, H / 2 + 20, 0.95 + 0.03 * life / 8)

    def letter(self, t):
        text = self.kw["text"]
        f = font("type", 56)
        lines = wrap(text, f, 1000)
        paper = gfx.paper_texture((1200, 200 + 80 * len(lines) + 120), seed=21).convert("RGBA")
        d = ImageDraw.Draw(paper)
        spoken = self.kw.get("words") or []
        n_total = len(text.split())
        n = n_total if not spoken else min(n_total, int(round(
            sum(1 for g, _ in spoken if g <= t) * n_total / max(1, len(spoken)))) + 1)
        d.text((90, 70), self.kw.get("head", "Dear Patrick,"), font=f, fill=INK)
        y, shown = 170, 0
        for ln in lines:
            ws = ln.split()
            d.text((90, y), " ".join(ws[:max(0, n - shown)]), font=f, fill=INK)
            shown += len(ws)
            y += 80
        if n >= n_total:
            d.text((700, y + 20), self.kw.get("sign", "Love, Daddy."), font=font("marker", 60), fill=(30, 40, 120))
        return paper


class Board(Card):
    """Corkboard investigation. items: dict name->(x,y,lines,t_appear). strings: (a,b,t). focus: (x,y,zoom)."""
    enter = "cut"

    def background(self):
        return corkboard()

    def content(self, frame, t, life):
        d = ImageDraw.Draw(frame)
        items = self.kw["items"]
        zx, zy, z = self.kw.get("focus", (W / 2, H / 2, 1.0))
        if self.kw.get("pullback"):
            u = ease_out(life / 2.5)
            z = z + (1.0 - z) * u
            zx = zx + (W / 2 - zx) * u
            zy = zy + (H / 2 - zy) * u
        tf = lambda x, y: ((x - zx) * z + W / 2, (y - zy) * z + H / 2)
        for a, b, ts in self.kw.get("strings", []):
            if t >= ts:
                p0 = tf(*items[a][:2])
                p1 = tf(*items[b][:2])
                red_string(d, (p0[0], p0[1] - 40 * z), (p1[0], p1[1] - 40 * z), ease_out((t - ts) / 0.5), 50 * z)
        for name, (x, y, lines, ta) in items.items():
            if t < ta:
                continue
            k = t - ta
            img = self._card(name, tuple(lines))
            px, py = tf(x, y)
            s = z * (1.25 - 0.25 * ease_back(k / 0.18)) if k < 0.3 else z
            place(frame, img, px, py, s, rot=(hash(name) % 7) - 3)
            place(frame, pin_img(), px, py - img.height * z / 2 + 10 * z, z)

    @lru_cache(None)
    def _card(self, name, lines):
        return with_shadow(index_card(list(lines), w=max(380, 24 * max(len(x) for x in lines) + 40)), 8, (6, 8))


class Checklist(Card):
    """Typed list where each row appears at its time. rows: (t, text, mark) mark in {'y','n',None}."""

    def content(self, frame, t, life):
        key = tuple((t >= tt, t >= tt + 0.35) for tt, _, _ in self.kw["rows"])
        img = self.cached(key, lambda: with_shadow(self.sheet(t).rotate(-1, expand=True, resample=Image.BICUBIC)))
        place(frame, img, W / 2, H / 2, 0.92 + 0.03 * life / 8)

    def sheet(self, t):
        paper = gfx.paper_texture((1300, 140 + 120 * len(self.kw["rows"])), seed=8).convert("RGBA")
        d = ImageDraw.Draw(paper)
        d.text((70, 40), self.kw.get("title", ""), font=font("anton", 64), fill=RED)
        f = font("type", 66)
        y = 150
        for tt, txt, mark in self.kw["rows"]:
            if t >= tt:
                d.text((150, y), txt, font=f, fill=INK)
                if mark and t >= tt + 0.35:
                    col = (30, 140, 60) if mark == "y" else RED
                    sym = "✔" if mark == "y" else "✘"
                    d.text((60, y - 10), sym, font=font("marker", 80) if False else gfx.ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72), fill=col)
            y += 120
        return paper


class Split(Card):
    """Two evidence frames side by side with labels."""

    def content(self, frame, t, life):
        for i, (label, tag, ta) in enumerate(self.kw["panels"]):
            if t < ta:
                continue
            k = ease_out((t - ta) / 0.3)
            inner = placeholder(label, (800, 450)).convert("RGB")
            ev = gfx.evidence_frame(inner, tag, tilt=-2 if i == 0 else 2)
            place(frame, ev, 500 + 920 * i, H / 2 + (1 - k) * 700, 0.98)
        if self.kw.get("mid") and t >= self.kw["mid"][1]:
            img = text_img(self.kw["mid"][0], font("anton", 220), RED + (255,), stroke=8, stroke_fill=(0, 0, 0))
            place(frame, img, W / 2, H / 2, 1.3 - 0.3 * ease_back((t - self.kw["mid"][1]) / 0.15))


class Counter(Card):
    """Rolling year counter (a -> b) between t_start and t_end with label."""
    enter = "cut"

    def content(self, frame, t, life):
        a, b = self.kw["range"]
        ts, te = self.kw["t_start"], self.kw["t_end"]
        u = ease_out((t - ts) / max(0.01, te - ts)) if t >= ts else 0
        val = int(round(a + (b - a) * u))
        img = text_img(str(val), font("anton", 330), WHITE + (255,), stroke=8, stroke_fill=(0, 0, 0))
        place(frame, img, W / 2, H / 2 - 40)
        lab = self.kw.get("label", "")
        if lab:
            place(frame, text_img(lab, font("type", 64), (235, 225, 200, 255)), W / 2, H / 2 + 200)


class Receipt(Card):
    def content(self, frame, t, life):
        rows = self.kw["rows"]  # (t, left, right)
        wpx = 760
        hpx = 220 + 70 * len(rows) + 160
        img = Image.new("RGBA", (wpx, hpx), (250, 250, 246, 255))
        d = ImageDraw.Draw(img)
        f = font("type", 44)
        d.text((wpx / 2 - f.getlength(self.kw.get("head", "")) / 2, 40), self.kw.get("head", ""), font=f, fill=INK)
        d.line((40, 120, wpx - 40, 120), fill=INK, width=3)
        y = 150
        shown = 0
        for tt, l, r in rows:
            if t >= tt:
                d.text((50, y), l, font=f, fill=INK)
                d.text((wpx - 50 - f.getlength(r), y), r, font=f, fill=INK)
                shown = y + 70
            y += 70
        # receipt grows as lines print
        crop_h = max(160, shown + 40)
        img = self.cached(("r", crop_h), lambda: with_shadow(img.crop((0, 0, wpx, min(hpx, crop_h))).rotate(
            1.5, expand=True, resample=Image.BICUBIC)))
        place(frame, img, W / 2, 30 + img.height / 2, 1.0)


class Dictionary(Card):
    def content(self, frame, t, life):
        txt = self.kw["definition"]
        n = int(len(txt) * min(1, max(0, (t - self.kw["t_def"]) / 2.2)))
        img = self.cached(("d", n), lambda: with_shadow(self.sheet(n).rotate(-0.8, expand=True,
                                                                           resample=Image.BICUBIC)))
        place(frame, img, W / 2, H / 2, 0.95 + 0.03 * life / 8)

    def sheet(self, n):
        paper = self.cached("paper", lambda: gfx.paper_texture((1500, 640), seed=31, color=(240, 232, 210))
                            .convert("RGBA")).copy()
        d = ImageDraw.Draw(paper)
        d.text((80, 60), self.kw["word"], font=font("anton", 120), fill=INK)
        d.text((90, 210), self.kw.get("pron", ""), font=font("type", 46), fill=(110, 90, 70))
        f = font("type", 50)
        txt = self.kw["definition"]
        y = 300
        for ln in wrap(txt[:n], f, 1330):
            d.text((90, y), ln, font=f, fill=INK)
            y += 66
        return paper


class Copies(Card):
    """The same joke card photocopied until it fills the frame."""
    enter = "cut"

    def content(self, frame, t, life):
        card = self._card()
        n = 1 + int(max(0, t - self.kw["t_copy"]) * self.kw.get("rate", 9))
        rng = np.random.default_rng(4)
        pos = [(W / 2, H / 2, 0)] + [(rng.uniform(150, W - 150), rng.uniform(120, H - 120), rng.uniform(-25, 25))
                                     for _ in range(200)]
        for i in range(min(n, len(pos))):
            x, y, r = pos[i]
            img = self.cached(("c", i), lambda: card.resize((int(card.width * .75), int(card.height * .75)))
                              .rotate(r, expand=True, resample=Image.BILINEAR))
            place(frame, img, x, y)

    @lru_cache(None)
    def _card(self):
        return with_shadow(index_card(self.kw["lines"], w=560), 8, (6, 8))


class Starfish(Card):
    """Original anatomical diagram of a real starfish: nerve ring, radial nerves, then 'head' genes."""
    enter = "cut"

    def content(self, frame, t, life):
        tn, th = self.kw.get("t_nerves", 1e9), self.kw.get("t_head", 1e9)
        qn = round(ease_out((t - tn) / 1.2), 2) if t >= tn else -1
        qh = round(ease_out((t - th) / 1.5), 2) if t >= th else -1
        frame.alpha_composite(self.cached((qn, qh), lambda: self.layer(qn, qh)))
        lab = ImageDraw.Draw(frame)
        f = font("oswald", 44)
        for (tt, txt, col, y) in self.kw.get("labels", []):
            if t >= tt:
                lab.text((1330, y), txt, font=f, fill=col)

    def layer(self, qn, qh):
        cx, cy, R, r = W / 2 - 150, H / 2 + 20, 400, 140
        arms = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rad = R if i % 2 == 0 else r
            arms.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.polygon(arms, fill=(214, 168, 120, 255), outline=(120, 80, 50, 255))
        d.line(arms + [arms[0]], fill=(120, 80, 50, 255), width=6, joint="curve")
        if qn >= 0:
            u = qn
            d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), outline=(255, 245, 120, 255), width=int(8 * u) + 1)
            for i in range(5):
                a = -math.pi / 2 + i * 2 * math.pi / 5
                d.line((cx + math.cos(a) * 70, cy + math.sin(a) * 70,
                        cx + math.cos(a) * (70 + (R - 90) * u), cy + math.sin(a) * (70 + (R - 90) * u)),
                       fill=(255, 245, 120, 255), width=8)
        if qh >= 0:
            u = qh
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse((cx - 130, cy - 130, cx + 130, cy + 130), fill=(80, 200, 255, int(170 * u)))
            for i in range(5):
                a = -math.pi / 2 + i * 2 * math.pi / 5
                gd.line((cx, cy, cx + math.cos(a) * (R - 40) * u, cy + math.sin(a) * (R - 40) * u),
                        fill=(80, 200, 255, int(170 * u)), width=70)
            layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
        return layer


class EndScreen(Card):
    enter = "cut"

    def content(self, frame, t, life):
        frame.paste((10, 10, 10, 255), (0, 0, W, H))
        d = ImageDraw.Draw(frame)
        for i, x in enumerate((180, 1000)):
            d.rounded_rectangle((x, 300, x + 740, 716), 16, outline=(70, 70, 70), width=4)
        f = font("oswald", 36)
        d.text((180, 240), "NEXT FILE", font=f, fill=(150, 150, 150))
        st = gfx.stamp("FILE CLOSED", size=90, angle=-6)
        place(frame, st, W / 2, 150, 1.6 - 0.6 * ease_back(life / 0.15))


class Black(Card):
    enter = "cut"

    def content(self, frame, t, life):
        frame.paste((0, 0, 0, 255), (0, 0, W, H))
        if self.kw.get("text"):
            f = font("type", self.kw.get("size", 110))
            full = self.kw["text"]
            n = int(len(full) * min(1, life / self.kw.get("type_time", 1.2)))
            img = text_img(full[:n] or " ", f, WHITE + (255,))
            place(frame, img, W / 2 - (text_img(full, f, WHITE).width - img.width) / 2, H / 2)


# ---------------------------------------------------------------- overlays
def date_card_overlay(frame, t, start, date, title, season, dur=4.2):
    if not (start <= t < start + dur):
        return
    k = t - start
    card = gfx.date_card(date, title, season, k / 1.4)
    x = 80
    if k > dur - 0.35:
        x -= (k - (dur - 0.35)) / 0.35 * (card.width + 120)
    frame.alpha_composite(card, (int(x), 70))


def chapter_overlay(frame, t, start, num, title, dur=3.6):
    if not (start <= t < start + dur):
        return
    k = t - start
    a = min(1, k / 0.25, (dur - k) / 0.3)
    f1, f2 = font("oswald", 26), font("anton", 52)
    tw = int(f2.getlength(title.upper())) + 60
    img = Image.new("RGBA", (tw, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, tw, 120), fill=(10, 10, 10, 200))
    d.rectangle((tw - 10, 0, tw, 120), fill=RED + (255,))
    d.text((22, 8), f"FILE {num:02d}", font=f1, fill=RED + (255,))
    d.text((22, 40), title.upper(), font=f2, fill=WHITE + (255,))
    slide = (1 - ease_out(k / 0.3)) * (tw + 80)
    place(frame, img, W - 60 - tw / 2 + slide, 130, 1.0, alpha=a)


def monitor_overlay(frame, t, state):
    if state is None:
        return
    level, label, flat = state
    mon = gfx.brain_monitor(t, level, label, flat)
    mon = mon.resize((int(mon.width * 0.8), int(mon.height * 0.8)), Image.BILINEAR)
    frame.alpha_composite(mon, (W - mon.width - 36, H - mon.height - 36))
