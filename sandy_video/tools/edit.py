"""Timeline / edit decision list for 'Why Sandy Cheeks lives in Bikini Bottom'."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

VO = json.load(open(os.path.join(ROOT, "work/vo_map.json")))
CW = json.load(open(os.path.join(ROOT, "work/clip_words.json")))

# ============================================================== item types
class Item:
    base = False; post = False
    def __init__(self, t0, t1): self.t0, self.t1 = t0, t1
    def active(self, t): return self.t0 <= t < self.t1
    def sfx(self): return []

class Bg(Item):
    base = True
    def draw(self, c, t): c[:] = bg_frame(t)

class Black(Item):
    base = True
    def draw(self, c, t): c[:] = 0

class Vid(Item):
    """Full-frame footage. s=source time at t0. speed 0 = freeze."""
    base = True
    def __init__(self, src, s, t0, t1, z0=1.0, z1=1.06, cx=.5, cy=.5, speed=1.0, crop_cy=.45, punch=(), fx=None, ease=ease_in_out, dark=0.0, rot=0.0):
        super().__init__(t0, t1); self.a = (src, s, speed, crop_cy); self.z0, self.z1, self.cx, self.cy = z0, z1, cx, cy
        self.punch, self.fx, self.ease, self.dark, self.rot = punch, fx, ease, dark, rot; self.r = None
    def draw(self, c, t):
        src, s, speed, ccy = self.a
        if self.r is None: self.r = Reader(src, s, max(0.2, (self.t1 - self.t0) * speed + 0.2), ccy)
        f = self.r.get(int((t - self.t0) * speed * FPS))
        p = (t - self.t0) / max(1e-6, self.t1 - self.t0); z = lerp(self.z0, self.z1, self.ease(p))
        for pt, amt, dur in self.punch:
            if t >= pt: z *= 1 + amt * ease_out((t - pt) / dur)
        out = warp_full(f, z, self.cx, self.cy, rot=self.rot)
        if self.fx == "surveil": out = surveil(out, t)
        elif self.fx == "desat":
            g = cv2.cvtColor(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR); out = cv2.addWeighted(out, .35, g, .65, 0)
        elif self.fx == "rewind":
            out = cv2.addWeighted(out, .8, np.full_like(out, (60, 20, 20)), .2, 0)
            for y in range(int((t * 900) % 140), H, 140): out[y:y + 6] = 230
        if self.dark: out = (out * (1 - self.dark)).astype(np.uint8)
        c[:] = out

class Img(Item):
    """Overlay RGBA. anim in: pop | slam | slide_up | slide_left | slide_right | drop | fade | none"""
    def __init__(self, img, t0, t1, x, y, scale=1.0, rot=0.0, anim="pop", out="fade", din=0.22, dout=0.18, drift=0.0, shadow=False, alpha=1.0, sfx_in=None, gain=-6):
        super().__init__(t0, t1); self.img = with_shadow(img) if shadow else img
        self.x, self.y, self.s, self.rot, self.anim, self.out, self.din, self.dout, self.drift, self.alpha = x, y, scale, rot, anim, out, din, dout, drift, alpha
        self.sfx_in, self.gain = sfx_in, gain
    def sfx(self): return [(self.t0, self.sfx_in, self.gain)] if self.sfx_in else []
    def draw(self, c, t):
        x, y, s, a, r = self.x, self.y, self.s, self.alpha, self.rot
        p = (t - self.t0) / self.din
        if self.anim == "pop": s *= ease_back(p) if p < 1 else 1
        elif self.anim == "slam": s *= lerp(2.3, 1.0, ease_out(p)); a *= clamp(p * 3)
        elif self.anim == "slide_up": y += (1 - ease_out(p)) * 900; r += (1 - ease_out(p)) * 8
        elif self.anim == "slide_left": x += (1 - ease_out(p)) * 1400
        elif self.anim == "slide_right": x -= (1 - ease_out(p)) * 1400
        elif self.anim == "drop": y -= (1 - ease_out(p)) * 700
        elif self.anim == "fade": a *= clamp(p)
        s *= 1 + self.drift * (t - self.t0)
        q = (self.t1 - t) / self.dout
        if self.out == "fade" and q < 1: a *= clamp(q)
        elif self.out == "slide_down" and q < 1: y += (1 - clamp(q)) ** 2 * 1100
        elif self.out == "shrink" and q < 1: s *= clamp(q)
        blit(c, self.img, x, y, s, r, a)

def Text(text, t0, t1, x, y, size=150, fname="Anton.ttf", fill=(255, 255, 255), stroke=8, sf=(0, 0, 0), shadow=14, **kw):
    return Img(text_img(text, fname, size, fill, stroke, sf, shadow), t0, t1, x, y, **kw)

class Typed(Item):
    """Typewriter reveal, left-aligned at (x,y) top-left."""
    def __init__(self, text, t0, t1, x, y, size=90, fname="SpecialElite.ttf", fill=(245, 238, 215), cps=22, stroke=0, sf=(0, 0, 0), sound=True, gain=-14, out="fade"):
        super().__init__(t0, t1); self.text, self.x, self.y, self.cps, self.sound, self.gain, self.out = text, x, y, cps, sound, gain, out
        self.kw = (fname, size, fill, stroke, sf)
        if x is None: self.x = (W - text_img(text, fname, size, fill, stroke, sf, 0, 10).shape[1]) / 2
    def sfx(self):
        if not self.sound: return []
        n = len(self.text.replace(" ", "")); return [(self.t0 + i / self.cps, "type", self.gain) for i in range(0, len(self.text), 1) if self.text[i] != " "][:40]
    def draw(self, c, t):
        n = int((t - self.t0) * self.cps) + 1; s = self.text[:max(0, n)]
        if not s.strip(): return
        im = text_img(s, *self.kw[:2], self.kw[2], self.kw[3], self.kw[4], 0, 10)
        a = clamp((self.t1 - t) / 0.18) if self.out == "fade" else 1
        blit(c, im, self.x + im.shape[1] / 2, self.y + im.shape[0] / 2, 1, 0, a)

class Ellipse(Item):
    def __init__(self, t0, t1, cx, cy, rx, ry, dur=0.35, color=(40, 40, 225), th=12, rot=-8, sound=True):
        super().__init__(t0, t1); self.a = (cx, cy, rx, ry, color, th, rot); self.dur, self.sound = dur, sound
    def sfx(self): return [(self.t0, "swipe", -10)] if self.sound else []
    def draw(self, c, t):
        cx, cy, rx, ry, col, th, rot = self.a; marker_ellipse(c, cx, cy, rx, ry, (t - self.t0) / self.dur, col, th, rot)

class Arrow(Item):
    def __init__(self, t0, t1, p0, p1, dur=0.25, color=(40, 40, 225), th=12, sound=True):
        super().__init__(t0, t1); self.a = (p0, p1, color, th); self.dur, self.sound = dur, sound
    def sfx(self): return [(self.t0, "swipe", -12)] if self.sound else []
    def draw(self, c, t): p0, p1, col, th = self.a; marker_arrow(c, p0, p1, (t - self.t0) / self.dur, col, th)

class Line(Item):
    def __init__(self, t0, t1, p0, p1, dur=0.25, color=(40, 40, 225), th=12, sound=True):
        super().__init__(t0, t1); self.a = (p0, p1, color, th); self.dur, self.sound = dur, sound
    def sfx(self): return [(self.t0, "swipe", -12)] if self.sound else []
    def draw(self, c, t): p0, p1, col, th = self.a; marker_line(c, p0, p1, (t - self.t0) / self.dur, col, th)

class Rect(Item):
    def __init__(self, t0, t1, x0, y0, x1, y1, color=(0, 0, 0), a=0.6):
        super().__init__(t0, t1); self.r = (x0, y0, x1, y1, color, a)
    def draw(self, c, t):
        x0, y0, x1, y1, col, a = self.r; roi = c[y0:y1, x0:x1]; c[y0:y1, x0:x1] = (roi * (1 - a) + np.array(col) * a).astype(np.uint8)

class Draw(Item):
    """Generic: fn(canvas, local_t)."""
    def __init__(self, t0, t1, fn, snd=()):
        super().__init__(t0, t1); self.fn, self.snd = fn, snd
    def sfx(self): return list(self.snd)
    def draw(self, c, t): self.fn(c, t - self.t0)

# ---- post items
class Shake(Item):
    post = True
    def __init__(self, t0, t1, amp=14, decay=True): super().__init__(t0, t1); self.amp, self.decay = amp, decay
    def apply(self, c, t):
        a = self.amp * ((1 - (t - self.t0) / (self.t1 - self.t0)) if self.decay else 1); return shake(c, t, a)

class Glitch(Item):
    post = True
    def __init__(self, t0, t1, strength=1.0, sound=True): super().__init__(t0, t1); self.s, self.sound = strength, sound
    def sfx(self): return [(self.t0, "glitch", -8)] if self.sound else []
    def apply(self, c, t): return glitch(c, t, self.s)

class Flash(Item):
    post = True
    def __init__(self, t0, dur=0.12, color=255): super().__init__(t0, t0 + dur); self.col = color
    def apply(self, c, t):
        a = 1 - (t - self.t0) / (self.t1 - self.t0); return cv2.addWeighted(c, 1 - a * .85, np.full_like(c, self.col), a * .85, 0)

class Whip(Item):
    """motion blur + slide around a cut at time tc"""
    post = True
    def __init__(self, tc, half=0.12, sound="whoosh1", gain=-6): super().__init__(tc - half, tc + half); self.tc, self.half, self.snd, self.g = tc, half, sound, gain
    def sfx(self): return [(self.tc - 0.2, self.snd, self.g)] if self.snd else []
    def apply(self, c, t):
        k = 1 - abs(t - self.tc) / self.half; out = whip_blur(c, 120 * k)
        dx = (1 if t < self.tc else -1) * -260 * k
        return cv2.warpAffine(out, np.float32([[1, 0, dx], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)

class Fade(Item):
    post = True
    def __init__(self, t0, t1, direction="in"): super().__init__(t0, t1); self.d = direction
    def apply(self, c, t):
        p = (t - self.t0) / (self.t1 - self.t0); a = p if self.d == "in" else 1 - p
        return (c * clamp(a)).astype(np.uint8)

class Snd(Item):
    """pure sound cue"""
    def __init__(self, t, name, gain=-6): super().__init__(t, t); self.n, self.g = name, gain
    def active(self, t): return False
    def sfx(self): return [(self.t0, self.n, self.g)]

# ============================================================== reusable pieces
def tag(text, t0, t1):
    im = text_img(text, "CourierPrime.ttf", 40, (255, 222, 90), 0, (0, 0, 0), 0, 18)
    h, w = im.shape[:2]; bg = np.zeros((h + 8, w + 30, 4), np.uint8); bg[..., 3] = 175
    bg[4:4 + h, 15:15 + w] = np.where(im[..., 3:4] > 0, im, bg[4:4 + h, 15:15 + w])
    a = bg.astype(np.float32); ia = im[..., 3:4].astype(np.float32) / 255
    region = a[4:4 + h, 15:15 + w]; region[..., :3] = im[..., :3] * ia + region[..., :3] * (1 - ia); region[..., 3:4] = np.maximum(region[..., 3:4], im[..., 3:4])
    a[4:4 + h, 15:15 + w] = region
    bg = a.astype(np.uint8)
    return Img(bg, t0, t1, 70 + bg.shape[1] / 2, 70 + bg.shape[0] / 2, anim="slide_right", din=0.3)

def captions(clip_key, src_in, src_out, offset=0.0):
    """Lower-third subtitle for a show clip, phrase by phrase."""
    words = [w for w in CW[clip_key] if src_in - 0.05 <= w[1] < src_out]
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if w[0][-1] in ".!?," and len(cur) >= 3 or len(cur) >= 7: phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    items = []
    for i, p in enumerate(phrases):
        a = p[0][1] - src_in + offset; b = (phrases[i + 1][0][1] - src_in + offset) if i + 1 < len(phrases) else (src_out - src_in + offset)
        txt = " ".join(x[0] for x in p)
        txt = txt.replace("praise", "breathe").replace("Chief", "Cheeks").replace("My boss says", "My bosses!").replace(" -year", "-year").replace("Tree Dome", "Treedome").replace("Cuz", "'Cause")
        im = text_img(txt, "CourierPrime.ttf", 56, (255, 255, 255), 5, (0, 0, 0), 8, 14)
        items.append(Img(im, max(0, a - 0.05), b, W / 2, H - 120, anim="none", out="none"))
    return items

def contract(t0, t1, x=W / 2, y=H / 2 + 20, scale=0.95, rot=-3, anim="slide_up", sfx="whoosh2"):
    return Img(doc_img(), t0, t1, x, y, scale, rot, anim=anim, din=0.35, shadow=True, sfx_in=sfx, gain=-7)

def stamp(text, t0, t1, x, y, rot=-14, size=170, color=(222, 28, 36), snd="stamp", gain=-2):
    return [Img(stamp_img(text, color, size), t0, t1, x, y, 1.0, rot, anim="slam", din=0.12, sfx_in=snd, gain=gain), Shake(t0 + 0.1, t0 + 0.45, 18)]

def still(src, t):
    r = Reader(src, t, 0.2); f = r.get(0).copy(); r.close(); return f

def slam_word(text, t0, t1, x=W / 2, y=H / 2, size=260, fill=(255, 220, 40), snd="impact_small", gain=-4, rot=-3):
    return [Text(text, t0, t1, x, y, size, fill=fill, stroke=12, rot=rot, anim="slam", din=0.14, sfx_in=snd, gain=gain), Shake(t0 + .1, t0 + .4, 12)]

def ty(text, t0, t1, x, y, size=90, **kw): return Typed(text, t0, t1, x, y, size, **kw)

# ============================================================== blocks
def block_vo(n):
    w = VO[str(n)]; T = w["dur"]
    it = []; tail = 0.12
    if n == 1:
        it += [Bg(0, 2.55), Typed("MAY 5, 2006", 0.05, 2.55, None, 420, 170, cps=16)]
        it += [Bg(2.55, 6.15), contract(2.6, 6.15, W / 2 + 260, H / 2 + 40, 0.9, -4)]
        pol = polaroid(still("ch", 669.6), 520)
        it += [Img(pol, 2.75, 6.15, 520, 470, 1, 6, anim="slide_right", din=.3, shadow=True, sfx_in="whoosh3", gain=-10)]
        it += [Ellipse(3.9, 6.15, 1125, 602, 255, 58, rot=-4)]
        it += [Vid("ch", 669.6, 6.15, 7.75, 1.25, 1.32, cx=.7, cy=.45, speed=0, dark=.55)] + slam_word("20 YEARS", 6.2, 7.75, size=300)
        it += [Vid("tea", 64.2, 7.75, 9.5, 1.18, 1.0)]
        it += [Vid("ch", 654.5, 9.5, 10.8, 1.0, 1.0, cx=.5, cy=.45, punch=[(9.8, .35, .2)]), Snd(9.78, "pop", -4), Snd(9.6, "bubbles_small", -12)]
        it += [Vid("pr", 185.6, 10.8, T + tail, 1.0, 1.08, cx=.55, cy=.4, speed=0), Ellipse(12.9, T + tail, 1110, 470, 350, 400, dur=.4)]
        it += [Text("FISHBOWL", 13.0, T + tail, 420, 220, 110, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=8, anim="pop")]
        it += [Whip(6.15, sound="whoosh1"), Whip(10.8, sound="whoosh3")]
    elif n == 2:
        tail = 0.5
        it += [Vid("ch", 668.5, 0, 1.95, 1.05, 1.18, cx=.75, cy=.35, speed=.45), Text('"I accept!"', 0.35, 1.95, W / 2, H - 130, 90, "CourierPrime.ttf", (255, 255, 255), 6, rot=0, anim="fade")]
        it += [Bg(1.95, 5.85), Snd(1.95, "whoosh2", -9)]
        it += [ty("MAY 2006", 2.75, 5.85, 330, 330, 120, cps=18), ty("+ 20 YEARS", 2.1, 5.85, 920, 330, 120, cps=18)]
        it += [Line(3.85, 5.85, (330, 520), (1590, 520), dur=.25, color=(240, 240, 240), th=8)]
        it += [Text("MAY 2026", 4.45, 5.85, W / 2, 720, 230, fill=(255, 220, 40), stroke=10, rot=-2, anim="pop", sfx_in="pop", gain=-3)]
        it += [Bg(5.85, T + tail), contract(5.85, 9.15, W / 2, H / 2 + 30, .95, -3, anim="none", sfx=None), Snd(5.75, "swipe", -10)]
        it += stamp("EXPIRED", 6.85, 9.15, W / 2 + 10, H / 2 + 120, size=190)
        it += [Img(note_img("6 MONTHS\nAGO", 360, 260, size=56), 7.55, 9.15, 1550, 280, 1, 7, anim="pop", sfx_in="pop", gain=-9)]
        it += [Vid("ch", 687.4, 9.15, T + tail, 1.0, 1.12, cx=.48, cy=.55, speed=.3), Snd(9.2, "bubbles_small", -12)]
        it += [Whip(9.15, sound="whoosh4")]
    elif n == 3:
        it += [Vid("tea", 880.0, 0, 3.0, 1.0, 1.1, cx=.5, cy=.4), Text("TEXAS", 1.9, 3.0, 1450, 300, 120, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=-6), Arrow(1.95, 3.0, (1380, 380), (1110, 520))]
        it += [Vid("tea", 72.0, 3.0, 5.0, 1.0, 1.12, cx=.62, cy=.5), Text("BIKINI BOTTOM", 3.05, 5.0, W / 2, 160, 120, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=2)]
        it += [Bg(5.0, T + tail), Snd(4.95, "whoosh2", -10)]
        cards = [("#1", "1999"), ("#2", "2006"), ("#3", "2024")]
        ts = [5.45, 7.05, 7.9]
        for i, (a, b) in enumerate(cards):
            im = card_img((b,), 470, f"ANSWER {a}", seed=i)
            x = 430 + i * 530; tt = ts[i]
            if i < 2:
                it += [Img(im, tt, T + tail, x, 520, 1, [-5, 3, -2][i], anim="drop", din=.25, shadow=True, sfx_in="whoosh3", gain=-11, out="slide_down", dout=.45)]
            else:
                it += [Img(im, tt, 10.85, x, 520, 1, -2, anim="drop", din=.25, shadow=True, sfx_in="whoosh3", gain=-11)]
                it += [Img(im, 10.85, T + tail, W / 2, 500, 1.55, -2, anim="pop", din=.3, shadow=True, sfx_in="whoosh1", gain=-10)]
        it += [Glitch(9.6, 10.0, .8)]
        it += stamp("SHADY", 13.0, T + tail, W / 2 + 120, 720, rot=-10, size=150)
    elif n == 4:
        it += [Vid("tea", 1094.0, 0, 6.1, 1.0, 1.08)]
        it += [Img(card_img(("TEA AT THE TREEDOME", "SEASON 1  .  1999"), 900, "EPISODE", seed=4), 1.35, 6.1, 560, 760, 0.9, -3, anim="slide_right", din=.3, shadow=True, sfx_in="whoosh2", gain=-10)]
        it += [Vid("tea", 815.5, 6.1, 8.9, 1.0, 1.15, cx=.5, cy=.45, speed=1)]
        it += [Vid("tea", 838.0, 8.9, 11.75, 1.0, 1.05, punch=[(10.92, .25, .15)]), Snd(10.92, "impact_small", -6), Shake(10.95, 11.3, 14)]
        it += [Vid("tea", 902.5, 11.75, 13.95, 1.0, 1.08)]
        it += [Vid("tea", 910.6, 13.95, T + tail, 1.0, 1.04)]
        it += [Whip(6.1, sound="whoosh1", gain=-9)]
    elif n == 5:
        it += [Vid("tea", 1006.0, 0, 2.6, 1.0, 1.08), Vid("tea", 1253.6, 2.6, 3.85, 1.0, 1.2, punch=[(2.62, .2, .15)]), Snd(2.6, "impact_small", -7)]
        it += [Vid("tea", 1060.5, 3.85, 5.9, 1.0, 1.1)]
        it += [Vid("tea", 921.4, 5.9, 8.8, 1.08, 1.08, speed=0, fx="rewind"), Snd(5.85, "scratch", -6)]
        it += [Text('"I NEED IT TO BREATHE."', 6.1, 8.8, W / 2, H - 150, 80, "CourierPrime.ttf", (255, 255, 255), 6, anim="pop")]
        it += [Vid("tea", 1157.0, 8.8, T + tail, 1.0, 1.28, cx=.5, cy=.4, speed=.6)]
    elif n == 6:
        tail = 0.3
        it += [Vid("tea", 1165.2, 0, 2.75, 1.0, 1.15, speed=0, cx=.55, cy=.4, dark=.25)]
        it += [Text("FIRST VISITOR.", 0.0, 2.75, W / 2, 330, 170, fill=(255, 255, 255), stroke=10, anim="pop", sfx_in="pop", gain=-8)]
        it += slam_word("EVER.", 1.5, 2.75, W / 2, 620, 230, fill=(255, 70, 60))
        it += [Vid("ch", 102.0, 2.75, 6.0, 1.0, 1.0)] if False else [Vid("hib", 12.0, 2.75, 6.0, 1.0, 1.15, cx=.5, cy=.5, speed=.7), Snd(3.0, "bubbles_small", -14)]
        it += [Vid("tea", 1165.2, 6.0, T + tail, 1.2, 1.3, speed=0, cx=.55, cy=.4, dark=.15)]
        it += [Text("EVER.", 8.2, T + tail, 1500, 300, 150, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=-8, anim="pop", sfx_in="pop", gain=-8), Ellipse(8.25, T + tail, 1500, 305, 210, 110, dur=.3)]
    elif n == 7:
        it += [Vid("pr", 195.0, 0, 1.3, 1.0, 1.08), Vid("sq", 54.5, 1.3, 2.5, 1.0, 1.08), Vid("hib", 28.0, 2.5, 3.6, 1.0, 1.08)]
        it += [Whip(1.3, .08, "whoosh3", -12), Whip(2.5, .08, "whoosh3", -12)]
        it += [Vid("hib", 28.9, 3.6, 5.05, 1.08, 1.08, speed=0, fx="desat"), Text("DOESN'T FIT.", 3.65, 5.05, W / 2, 540, 200, fill=(255, 255, 255), stroke=10, anim="slam", din=.12, sfx_in="impact_small", gain=-6)]
        it += [Vid("hib", 24.0, 5.05, T + tail, 1.0, 1.1)]
    elif n == 8:
        it += [Vid("sq", 58.5, 0, 2.35, 1.0, 1.08), Vid("sq", 141.0, 2.35, 4.4, 1.0, 1.15), Vid("sq", 154.2, 4.4, T + tail, 1.0, 1.2, cx=.4, cy=.5)]
    elif n == 9:
        it += [Vid("pr", 180.0, 0, 2.6, 1.0, 1.08)]
        it += [Img(card_img(("PRESSURE",), 560, "EPISODE", seed=9), 0.85, 2.6, 520, 780, .95, -3, anim="slide_right", din=.3, shadow=True, sfx_in="whoosh2", gain=-10)]
        it += [Vid("pr", 190.5, 2.6, 3.7, 1.0, 1.06), Vid("pr", 221.0, 3.7, 4.8, 1.0, 1.06), Vid("pr", 240.5, 4.8, 5.9, 1.0, 1.06)]
        it += [Vid("pr", 300.5, 5.9, T + tail, 1.0, 1.12)]
    elif n == 10:
        it += [Vid("pr", 333.5, 0, 2.0, 1.0, 1.06), Vid("pr", 339.5, 2.0, 4.25, 1.0, 1.08), Vid("pr", 362.5, 4.25, 5.7, 1.0, 1.2, speed=1.4)]
        it += [Black(5.7, 6.6), Snd(5.68, "tv_off", -10), Text("anyway.", 5.75, 6.6, W / 2, H / 2, 70, "SpecialElite.ttf", (200, 200, 200), 0, shadow=0, anim="none")]
        it += [Vid("hib", 13.5, 6.6, 12.65, 1.0, 1.18, speed=.6, dark=.1), Snd(6.7, "bubbles_small", -16)]
        it += [Snd(10.7, "riser", -12), Bg(12.65, T + tail)] + slam_word("SEASON 4", 12.68, T + tail, size=280)
        it += [Glitch(12.6, 12.85, 1.0)]
    elif n == 11:
        tail = 0.2
        it += [Vid("ch", 128.6, 0, T + tail, 1.0, 1.0, speed=0, cx=.5, cy=.4, punch=[(0.7, .3, .12)])] + slam_word("BOSSES.", 0.74, T + tail, W / 2, 860, 220, fill=(255, 70, 60))
    elif n == 12:
        it += [Vid("ch", 363.6, 0, 4.5, 1.0, 1.1, speed=.25, punch=[(1.58, .18, .2)])]
        it += [Vid("ch", 368.0, 4.5, 5.4, 1.0, 1.06), Vid("ch", 373.3, 5.4, T + tail, 1.0, 1.08)]
        for i, (tt, x) in enumerate([(3.52, 520), (3.66, 960), (3.82, 1400)]):
            it += [Text("BOSS", tt, 4.5, x, 170, 100, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=[-8, 3, 7][i], anim="pop", sfx_in="pop", gain=-10)]
    elif n == 13:
        it += [Bg(0, 1.95), ty("TREEDOME ENTERPRISES LTD.", 0.0, 1.95, 250, 470, 96, fname="CourierPrime.ttf", cps=30, gain=-18)]
        it += [Vid("ch", 654.3, 1.95, 8.4, 1.0, 1.15, cx=.45, cy=.5, speed=.2)]
        it += [Text("TREEDOME", 2.1, 4.2, W / 2 - 100, 170, 110, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=-4), Arrow(2.15, 4.2, (W / 2 - 100, 260), (870, 470))]
        it += [Text("TREEDOME ENTERPRISES", 2.6, 4.2, W / 2 + 120, 320, 70, "CourierPrime.ttf", (255, 220, 40), 6, rot=-4, anim="pop", sfx_in="pop", gain=-10)]
        sign = card_img(("STAFF HOUSING", "PROPERTY OF", "TREEDOME ENT. LTD."), 760, None, seed=13, color=(250, 236, 120))
        it += [Img(sign, 7.0, 8.4, 1340, 700, .85, 6, anim="slam", din=.14, shadow=True, sfx_in="stamp", gain=-4), Shake(7.1, 7.45, 14)]
        it += [Vid("ch", 129.2, 8.4, T + tail, 1.0, 1.06)]
    elif n == 14:
        tail = 5.75
        it += [Bg(0, 7.05), contract(0, 7.05, W / 2, H / 2 + 20, .98, -2, anim="slide_up")]
        def hl(y): return lambda c, lt: highlight(c, 630, y, 1300, y + 66, lt / .3)
        # contract rows on canvas: doc centred at (960, 560) scale .98 -> top-left ~ (588, 99)
        it += [Draw(0.75, 7.05, hl(198), [(0.75, "swipe", -12)]), Draw(2.95, 7.05, hl(382), [(2.95, "swipe", -12)]), Draw(4.25, 7.05, hl(466), [(4.25, "swipe", -12)])]
        it += [Line(5.6, 7.05, (870, 512), (1290, 500), dur=.2)]
        it += [Vid("ch", 274.0, 7.05, 10.1, 1.0, 1.1), Vid("ch", 284.5, 10.1, 12.75, 1.0, 1.08)]
        it += [Vid("ch", 309.6, 12.75, T + tail, 1.0, 1.12), Snd(12.8, "bubbles_small", -16)]
        it += [Text("~ the things I'll miss the most of all ~", 12.95, 15.8, W / 2, H - 150, 64, "SpecialElite.ttf", (255, 255, 255), 5, anim="fade", din=.25)]
        it += [Text("~ are the friends I've come to know ~", 15.85, T + tail, W / 2, H - 150, 64, "SpecialElite.ttf", (255, 255, 255), 5, anim="fade", din=.25)]
        it += [Whip(7.05, sound="whoosh2", gain=-10)]
    elif n == 15:
        it += [Vid("ch", 657.2, 0, 2.3, 1.0, 1.08)]
        it += [Vid("ch", 499.5, 2.3, 3.62, 1.0, 1.1), Vid("ch", 576.0, 3.62, 5.8, 1.0, 1.12, punch=[(3.64, .15, .12)]), Snd(3.64, "impact_big", -6), Shake(3.66, 4.1, 16)]
        it += [Vid("ch", 586.0, 5.8, 8.3, 1.0, 1.08)] + stamp("CLOSED", 6.9, 8.3, W / 2, 360, rot=8, size=160)
        it += [Vid("ch", 636.0, 8.3, 10.2, 1.0, 1.08), Vid("ch", 639.0, 10.2, 12.0, 1.0, 1.1), Vid("ch", 648.0, 12.0, 13.75, 1.0, 1.12), Shake(12.0, 13.7, 7, decay=False)]
        it += [Vid("ch", 657.4, 13.75, T + tail, 1.0, 1.05)]
    elif n == 16:
        tail = 0.8
        it += [Bg(0, T + tail), contract(0, T + tail, W / 2 + 330, H / 2 + 30, .9, -3, anim="slide_left")]
        it += [Text("20 YEARS", 0.0, 1.6, 520, H / 2, 200, fill=(255, 220, 40), stroke=10, rot=-4, anim="pop", sfx_in="pop", gain=-6)]
        it += [Img(card_img(("CHIMPS AHOY", "FIRST AIRED", "MAY 5, 2006"), 620, "EPISODE", seed=16), 1.65, 3.9, 520, H / 2 + 20, .95, -4, anim="drop", din=.25, shadow=True, sfx_in="whoosh3", gain=-10)]
        it += [Text("MAY 2026", 3.95, T + tail, 520, H / 2, 210, fill=(255, 255, 255), stroke=10, rot=-4, anim="slam", din=.14, sfx_in="impact_small", gain=-6)]
        it += stamp("EXPIRED", 6.3, T + tail, W / 2 + 340, H / 2 + 120, rot=-14, size=210, snd="impact_big", gain=-3) + [Snd(6.3, "stamp", -2)]
    elif n == 17:
        it += [Bg(0, T + tail), Glitch(0, 0.25, .9)]
        it += [Img(card_img(("2024",), 470, "ANSWER #3", seed=2), 0.55, 2.45, W / 2, H / 2, 1.5, -2, anim="pop", shadow=True, sfx_in="whoosh1", gain=-10)]
        it += [ty("SAVING BIKINI BOTTOM", 2.5, 6.4, 330, 360, 120, fname="Anton.ttf", cps=26, gain=-16), ty("THE SANDY CHEEKS MOVIE  (NETFLIX, 2024)", 3.9, 6.4, 340, 560, 56, fname="CourierPrime.ttf", cps=40, gain=-20)]
        chimp = polaroid(still("ch", 373.4), 520)
        it += [Img(chimp, 6.45, 8.05, W / 2, H / 2, 1, 4, anim="pop", shadow=True)]
        it += [Line(6.55, 8.05, (W / 2 - 250, H / 2 - 230), (W / 2 + 250, H / 2 + 260), .14, th=26), Line(6.7, 8.05, (W / 2 + 250, H / 2 - 230), (W / 2 - 250, H / 2 + 260), .14, th=26), Snd(6.55, "buzz", -10)]
        it += [Img(card_img(("GALVESTON, TEXAS",), 700, "LAB LOCATION", seed=7), 8.1, 10.75, W / 2, H / 2, 1.05, 3, anim="drop", din=.25, shadow=True, sfx_in="whoosh3", gain=-10)]
        for i, (ch, tt) in enumerate(zip("BOOTS", [10.82, 11.18, 11.5, 11.7, 12.02])):
            it += [Text(ch, tt, T + tail, 480 + i * 240, 450, 300, fill=(255, 220, 40), stroke=12, anim="slam", din=.1, sfx_in="stamp", gain=-8, rot=[-4, 3, -2, 4, -3][i])]
        it += [ty("BUREAU OF OFFICIAL TEXAS SCIENCE", 12.84, T + tail, 330, 700, 70, fname="CourierPrime.ttf", cps=24, gain=-18)]
    elif n == 18:
        tail = 0.9
        def scoop(c, lt):
            f = scoop.f
            p = ease_in_out((lt - 0.4) / 1.4)
            sc = lerp(1.0, 0.42, p); y = lerp(H / 2, H / 2 - 40, p); r = lerp(0, -5, p)
            c[:] = bg_frame(lt)
            img = polaroid(f, 1800) if p > 0.02 else None
            if img is None: c[:] = f
            else: blit(c, with_shadow(img) if p > .5 else img, W / 2, y, sc * 1.0, r)
        scoop.f = still("tea", 73.5)
        it += [Draw(0, 4.9, scoop, [(0.75, "whoosh4", -6), (0.9, "bubbles_burst", -8)])]
        it += [Text("ENTIRE TOWN", 3.3, 4.9, W / 2 + 330, 860, 90, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=10, rot=-6, anim="pop", sfx_in="pop", gain=-8)]
        it += [Bg(4.9, 10.1), Img(card_img(("SUE NAHMEE",), 620, "NEW BOSS", seed=18), 4.95, 10.1, 560, 470, 1.05, -3, anim="slide_right", din=.3, shadow=True, sfx_in="whoosh2", gain=-10)]
        sb = polaroid(still("ch", 690.6), 520)
        it += [Img(sb, 8.6, 10.1, 1350, 520, 1, 5, anim="pop", shadow=True, sfx_in="pop", gain=-8), Img(note_img("$19.99", 300, 150, (255, 255, 255), 64), 8.85, 10.1, 1520, 330, 1, -12, anim="pop", sfx_in="pop", gain=-10)]
        it += [Vid("tea", 1098.0, 10.1, 13.6, 1.0, 1.12, fx="surveil"), Snd(10.1, "static", -14), Snd(12.3, "shutter", -8)]
        it += [Vid("ch", 600.6, 13.6, 20.95, 1.0, 1.18, cx=.5, cy=.55, fx="surveil", speed=.55)]
        def box(c, lt):
            col = (60, 60, 240); x0, y0, x1, y1 = 640, 470, 1660, 1040
            if lt % .4 < .3: cv2.rectangle(c, (x0, y0), (x1, y1), col, 5); cv2.putText(c, "TARGET: FRIENDS", (x0, y0 - 18), cv2.FONT_HERSHEY_SIMPLEX, 1.3, col, 3, cv2.LINE_AA)
        it += [Draw(19.9, 20.95, box, [(19.9, "buzz", -16)])]
        it += [Black(20.95, T + tail), Snd(20.9, "tv_off", -8)]
    elif n == 19:
        it += [Bg(0, 3.6), Img(card_img(("NOT IN ANY EPISODE",), 820, "ANSWER #4", seed=19), 0.05, 3.6, W / 2, H / 2, 1.2, -3, anim="drop", din=.25, shadow=True, sfx_in="whoosh3", gain=-10)]
        it += [Vid("tea", 64.0, 3.6, T + tail, 1.0, 1.25, speed=.35, dark=.55)]
        it += [ty("STEPHEN HILLENBURG", 4.15, T + tail, 170, 170, 120, fname="Anton.ttf", cps=24, gain=-16)]
        it += [ty("created SpongeBob SquarePants", 5.4, 7.3, 180, 330, 56, fname="CourierPrime.ttf", cps=40, sound=False)]
        c1 = card_img(("MARINE BIOLOGY DEGREE",), 900, "HUMBOLDT STATE", seed=21)
        c2 = card_img(("TAUGHT MARINE BIOLOGY",), 900, "ORANGE COUNTY MARINE INSTITUTE", seed=22)
        c3 = card_img(('COMIC: "THE INTERTIDAL ZONE"',), 900, "FOR HIS STUDENTS", seed=23)
        it += [Img(c1, 7.4, T + tail, 640, 540, .82, -3, anim="slide_right", din=.3, shadow=True, sfx_in="whoosh2", gain=-11)]
        it += [Img(c2, 11.85, T + tail, 1290, 660, .82, 2, anim="slide_left", din=.3, shadow=True, sfx_in="whoosh2", gain=-11)]
        it += [Img(c3, 15.3, T + tail, 760, 860, .82, -1, anim="slide_up", din=.3, shadow=True, sfx_in="whoosh2", gain=-11)]
    elif n == 20:
        it += [Vid("tea", 66.0, 0, 3.6, 1.0, 1.15, speed=.6), Vid("tea", 20.0, 3.6, 5.6, 1.0, 1.1), Vid("ch", 57.5, 5.6, 7.7, 1.0, 1.1)]
        it += [Bg(7.7, 14.5), Img(polaroid(still("tea", 880.5), 600), 7.75, 14.5, 720, 520, 1, -5, anim="drop", din=.25, shadow=True, sfx_in="whoosh3", gain=-10)]
        it += [Text("?", 8.5, 14.5, 1180, 300, 220, "PermanentMarker.ttf", (255, 220, 40), 0, shadow=10, rot=10, anim="pop", sfx_in="pop", gain=-10)]
        it += [Img(note_img("my read.\nnot a fact.", 440, 300, size=58), 12.8, 14.5, 1400, 640, 1, 6, anim="pop", sfx_in="pop", gain=-9)]
        it += [Vid("ch", 605.8, 14.5, 18.1, 1.0, 1.1, speed=.5)]
        it += [Vid("ch", 600.6, 18.1, T + tail, 1.0, 1.0)]
        def pan(c, lt): pass
        it[-1] = Vid("ch", 600.6, 18.1, T + tail, 1.15, 1.3, cx=.55, cy=.55)
    elif n == 21:
        tail = 1.0
        it += [Vid("ch", 654.5, 0, 3.5, 1.0, 1.1, cx=.48, cy=.55)]
        it += [Bg(3.5, 11.2), contract(3.5, 11.2, W / 2 + 300, H / 2 + 30, .9, -3, anim="slide_left")]
        for i, (tx, tt) in enumerate([("3 chimps", 5.56), ("grant money", 6.44), ("20-yr contract", 7.68)]):
            it += [Text("v  " + tx, tt, 11.2, 470, 380 + i * 150, 76, "PermanentMarker.ttf", (255, 255, 255), 0, shadow=8, rot=-3, anim="pop", sfx_in="pop", gain=-9)]
        it += stamp("EXPIRED", 9.8, 11.2, W / 2 + 310, H / 2 + 120, rot=-14, size=190)
        it += [Vid("ch", 687.4, 11.2, 12.55, 1.05, 1.1, cx=.48, cy=.55, speed=.5), Snd(11.3, "bubbles_small", -14)]
        it += [Vid("ch", 690.2, 12.55, T + tail, 1.0, 1.12, cx=.45, cy=.4, speed=.5)]
    elif n == 22:
        tail = 4.2
        it += [Vid("ch", 626.8, 0, 2.75, 1.0, 1.0, speed=0, cx=.45, cy=.35, punch=[(1.82, .4, .12)]), Snd(1.82, "pop", -4)]
        it += [Bg(2.75, T + tail), Fade(2.75, 3.1, "in")]
        it += [Typed("Clips: Tea at the Treedome (1999), Prehibernation Week,", 3.0, T + tail, 260, 430, 40, fname="CourierPrime.ttf", cps=200, sound=False, out="none")]
        it += [Typed("Squirrel Jokes, Pressure, Chimps Ahoy (2006).", 3.0, T + tail, 260, 500, 40, fname="CourierPrime.ttf", cps=200, sound=False, out="none"), Typed("SpongeBob SquarePants (c) Nickelodeon. Used for commentary.", 3.0, T + tail, 260, 570, 40, fname="CourierPrime.ttf", cps=200, sound=False, out="none"), Fade(T + tail - 0.8, T + tail, "out")]
    return it, T + tail

CLIPS = {
    "tea_helmet": ("tea", 914.45, 923.9, "S1 . TEA AT THE TREEDOME (1999)", .45),
    "tea_visit": ("tea", 1163.1, 1166.0, "S1 . TEA AT THE TREEDOME (1999)", .4),
    "hib": ("hib", 54.55, 63.25, "PREHIBERNATION WEEK", .45),
    "sq_billy": ("sq", 278.3, 281.55, "SQUIRREL JOKES", .45),
    "sq_diff": ("sq", 316.8, 319.85, "SQUIRREL JOKES", .45),
    "pressure": ("pr", 309.7, 316.95, "PRESSURE", .45),
    "ch_coming": ("ch", 122.2, 128.45, "S4 . CHIMPS AHOY (2006)", .4),
    "ch_board": ("ch", 379.6, 383.6, "S4 . CHIMPS AHOY (2006)", .4),
    "ch_funding": ("ch", 133.0, 139.8, "S4 . CHIMPS AHOY (2006)", .4),
    "ch_contract": ("ch", 660.55, 670.6, "S4 . CHIMPS AHOY (2006)", .4),
}

def block_clip(k):
    src, a, b, label, ccy = CLIPS[k]; d = b - a
    it = [Vid(src, a, 0, d, 1.0, 1.05, crop_cy=ccy)] + captions(k, a, b) + [tag(label, 0, d)]
    if k == "ch_contract":
        it += [Snd(668.7 - a, "ding", -14)]
    return it, d

ORDER = [("vo", 1), ("vo", 2), ("vo", 3), ("vo", 4), ("clip", "tea_helmet"), ("vo", 5), ("clip", "tea_visit"), ("vo", 6), ("vo", 7), ("clip", "hib"),
         ("vo", 8), ("clip", "sq_billy"), ("clip", "sq_diff"), ("vo", 9), ("clip", "pressure"), ("vo", 10), ("clip", "ch_coming"), ("vo", 11), ("vo", 12),
         ("clip", "ch_board"), ("vo", 13), ("clip", "ch_funding"), ("vo", 14), ("vo", 15), ("clip", "ch_contract"), ("vo", 16), ("vo", 17), ("vo", 18),
         ("vo", 19), ("vo", 20), ("vo", 21), ("vo", 22)]

def build(kind, key): return block_vo(key) if kind == "vo" else block_clip(key)
