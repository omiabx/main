"""Full edit: 'How Many People Actually Live in Bikini Bottom?'"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from graphics import *
from data import *
from coldopen import build_coldopen, mix_events, polaroid_shot, pillar

PD = os.path.join(SCR, "archive_pd")
NAT = os.path.join(PD, "natives.mp4"); BAK = os.path.join(PD, "baker_hq.mp4")
TAGS = {"WEHTS": "WHAT EVER HAPPENED TO SPONGEBOB? · 2008", "PH": "PATTY HYPE · 2001", "NN": "NAUTICAL NOVICE · 2008",
        "BG": "BAND GEEKS · 2001", "NAVY": "U.S. NAVY FOOTAGE · 1946", "BAKER": "OPERATION CROSSROADS · BAKER TEST · 1946"}

class TL:
    def __init__(self): self.shots, self.ovs, self.aud = [], [], []
    def cuts(self, seq, end):
        """seq: list of (T, factory(t0,t1)) -> shots; last one ends at `end`."""
        seq = sorted(seq, key=lambda x: x[0])
        for i, (t0, fac) in enumerate(seq):
            t1 = seq[i + 1][0] if i + 1 < len(seq) else end
            if t1 - t0 > 0.02: self.shots.append(fac(t0, t1))
    def ov(self, t0, t1, fn): self.ovs.append({"t0": t0, "t1": t1, "draw": fn})
    def sfx(self, name, at, g=0.4): self.aud.append(("sfx", name, at, g))
    def tag(self, T, key, dur=2.6):
        txt = TAGS[key]
        self.ov(T, T + dur, lambda img, tl, tg: ep_tag(img, txt, alpha=clamp(tl / 0.2) * clamp((dur - tl) / 0.3)))
    def pill(self, T, text, dur=3.2):
        def d(img, tl, tg):
            p = clamp(tl / 0.35) if tl < dur - 0.35 else clamp((dur - tl) / 0.35)
            chapter_pill(img, text, p)
        self.ov(T, T + dur, d); self.sfx("swish", T, 0.25)
    def place_vo(self, chunk, T, parts, gap_after=0.35):
        """parts: list of ('vo', a, b) or ('ins', path, s, e, gain[, pause]). Returns (vt, ins_times, end)."""
        V = VO[chunk]; segs = []; ins = []; t = T
        for p in parts:
            if p[0] == "vo":
                a, b = p[1], p[2]; self.aud.append(("vo", V, t, a, b - a, 1.0)); segs.append((a, b, t)); t += b - a
            else:
                path, s, e, g = p[1:5]; pause = p[5] if len(p) > 5 else 0.15
                t += pause; self.aud.append(("clip", path, t, s, e - s, g)); ins.append((t, path, s, e)); t += (e - s) + pause
        def vt(v):
            for a, b, t0 in segs:
                if a - 1e-6 <= v <= b + 1e-6: return t0 + (v - a)
            # nearest
            best = min(segs, key=lambda sg: min(abs(v - sg[0]), abs(v - sg[1])))
            return best[2] + (v - best[0])
        return vt, ins, t + gap_after

def W_(c, word, nth=0):  # word start time in chunk c
    return word_t(c, word, nth)

# ---------- shot factory shorthands ----------
def C(path, src, zoom=(1.0, 1.08), cx=(0.5, 0.5), cy=(0.5, 0.5), ymax=480, speed=1.0, gray=(0, 0)):
    return lambda t0, t1: clip_shot(t0, t1, path, src, speed=speed, zoom=zoom, cx=cx, cy=cy, ymax=ymax, gray=gray)
def St(path, src, zoom=(1.0, 1.08), cx=(0.5, 0.5), cy=(0.5, 0.5), ymax=480, gray=(0, 0), ease=ease_in_out):
    return lambda t0, t1: still_shot(t0, t1, path, src, zoom=zoom, cx=cx, cy=cy, ymax=ymax, gray=gray, ease=ease)
def Fn(fn): return lambda t0, t1: fn_shot(t0, t1, fn)
def Pol(img, cap, rot=-2.5, notes=None, zt=0.3): return lambda t0, t1: polaroid_shot(t0, t1, img, cap, rot=rot, notes=notes, zoom_through=zt)
def Navy(draw):
    def fn(tl, tg):
        im = navy_bg().convert("RGBA"); draw(im, tl); return im.convert("RGB")
    return Fn(fn)

SIGN_CLOSE = dict(cx=(0.766, 0.766), cy=(0.83, 0.83), ymax=400)

# ---------- reusable graphics ----------
def crowd_img(): return grab(S2, CROWD_T)
def head_crop(i, size=80):
    x, y = HEADS[i]; im = crowd_img()
    x0 = int(min(max(0, x - size / 2), 640 - size)); y0 = int(min(max(0, y - size / 2 + 6), 480 - size))
    return im.crop((x0, y0, x0 + size, y0 + size))

def checklist_draw(items, times, checks, cols=2, w=700, h=120, y0=230):
    cards = [paper_card(t, w, h, 52) for t in items]; cards_c = [paper_card(t, w, h, 52, check=True) for t in items]
    def d(im, tl):
        for i, it in enumerate(items):
            if tl < times[i]: continue
            r, c = divmod(i, cols); x = W / 2 + (c - (cols - 1) / 2) * (w + 60); y = y0 + r * (h + 34)
            card = cards_c[i] if tl >= checks[i] else cards[i]
            paste_scaled(im, card, x, lerp(y + 40, y, ease_out((tl - times[i]) / 0.2)), alpha=clamp((tl - times[i]) / 0.12), rot=(-1.2 if (i % 2) else 1.0))
    return d

def ticket(num="No. 46,853"):
    w, h = 760, 330
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=(236, 200, 120))
    for y in range(20, h, 34): d.ellipse([-14, y, 14, y + 18], fill=(0, 0, 0, 0)); d.ellipse([w - 14, y, w + 14, y + 18], fill=(0, 0, 0, 0))
    d.rounded_rectangle([22, 22, w - 23, h - 23], 18, outline=(150, 60, 40), width=4)
    d.text((w / 2, 95), "PRETTY PATTIES", font=font("type", 52), fill=(120, 40, 30), anchor="mm")
    d.text((w / 2, 200), num, font=font("anton", 110), fill=(40, 25, 20), anchor="mm")
    d.text((w / 2, 280), "PLEASE WAIT YOUR TURN", font=font("type", 30), fill=(120, 40, 30), anchor="mm")
    return drop_shadow(im)

def gas_station():
    w, h = 1000, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, h - 40, w, h], fill=(70, 70, 80))
    d.rectangle([60, 150, 940, 190], fill=(196, 52, 44)); d.rectangle([120, 190, 150, h - 40], fill=CARD); d.rectangle([850, 190, 880, h - 40], fill=CARD)
    d.rectangle([520, 250, 900, h - 40], fill=CARD); d.rectangle([600, 330, 700, h - 40], fill=(60, 70, 90)); d.rectangle([740, 320, 860, 420], fill=(150, 190, 220))
    for x in (250, 380):
        d.rectangle([x, 330, x + 70, h - 40], fill=(196, 52, 44)); d.rectangle([x + 12, 350, x + 58, 400], fill=CARD)
    d.text((w / 2, 110), "DALE'S GAS", font=font("anton", 96), fill=CARD, anchor="mm")
    return im

def map_draw(progress_fn):
    """Schematic (not to scale) map: Bikini -> Rongerik -> Kwajalein -> Kili."""
    pts = {"BIKINI": (420, 360), "RONGERIK": (800, 300), "KWAJALEIN": (980, 640), "KILI": (1470, 840)}
    order = ["BIKINI", "RONGERIK", "KWAJALEIN", "KILI"]
    def d(im, tl):
        dr = ImageDraw.Draw(im)
        prog = progress_fn(tl)
        for i, k in enumerate(order):
            if prog < i: break
            x, y = pts[k]
            dr.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(40, 36, 30)); dr.ellipse([x - 9, y - 9, x + 9, y + 9], fill=CARD)
            dr.text((x + 30, y - 6), k, font=font("anton", 54), fill=(40, 36, 30), anchor="lm")
            if i + 1 < len(order) and prog > i:
                x2, y2 = pts[order[i + 1]]; marker_arrow(im, (x + 20, y + 10), (x2 - 20, y2 - 10), progress=clamp(prog - i))
        dr.text((W - 60, H - 50), "NOT TO SCALE", font=font("type", 30), fill=(90, 84, 74), anchor="rm")
    return d

def bar_draw(tl):
    pass

# =====================================================================
def build_all():
    tl = TL()
    shots, ovs, aud, T = build_coldopen(0.0)
    tl.shots += shots; tl.ovs += ovs; tl.aud += aud

    # ================= CHUNK 2 (+2B inserted before "The problem is") =================
    c = "2"; split = 39.95
    vt2, _, _ = tl.place_vo(c, T, [("vo", 0.0, split)], gap_after=0)
    t2b = vt2(split) + 0.25
    vb, _, _ = tl.place_vo("2b", t2b, [("vo", 0.0, WORDS["2b"]["dur"])], gap_after=0)
    tr = vb(WORDS["2b"]["dur"]) + 0.3
    vr, _, end2 = tl.place_vo(c, tr, [("vo", 40.05, WORDS[c]["dur"])])
    tl.pill(vt2(0.0), "EXHIBIT A · THE SIGN")
    names = ["SpongeBob", "Patrick", "Squidward", "Mr. Krabs", "Sandy", "Plankton", "Karen", "Mrs. Puff", "Pearl", "Gary",
             "Larry", "Mermaid Man", "Barnacle Boy", "Flying Dutchman", "\"MY LEG!\" guy"]
    ntimes = [W_(c, "SpongeBob,"), W_(c, "Patrick,"), W_(c, "Squidward,"), W_(c, "Mr."), W_(c, "Sandy,"), W_(c, "Plankton,"),
              W_(c, "Karen,"), W_(c, "Mrs."), W_(c, "Pearl."), W_(c, "Gary,"), W_(c, "Larry,"), W_(c, "Mermaid"), W_(c, "Barnacle"),
              W_(c, "Flying"), W_(c, "my")]
    cards = [paper_card(n, 420, 104, 33) for n in names]; cardsc = [paper_card(n, 420, 104, 33, check=True) for n in names]
    g0 = vt2(12.5)
    def namegrid(im, t):
        tg = g0 + t; cols = 4
        for i, n in enumerate(names):
            ti = vt2(ntimes[i]) if i < 10 else vt2(ntimes[i])
            if tg < ti - 0.05: continue
            r, cc = divmod(i, cols); x = 300 + cc * 440; y = 250 + r * 150
            paste_scaled(im, cardsc[i] if tg > ti + 0.25 else cards[i], x, y, rot=(-1.5 if (i % 3) else 1.2), alpha=clamp((tg - ti + 0.05) / 0.1))
        cnt = sum(1 for i in range(len(names)) if tg >= vt2(ntimes[i]))
        paste_scaled(im, label_box(f"{cnt} / 538", 80), 1640, 960, rot=-2)
    tl.cuts([
        (vt2(0.0), St(S5, 2978.6, zoom=(1.1, 1.25), cx=(0.55, 0.6), cy=(0.4, 0.38), ymax=CAP)),
        (vt2(3.4), Navy(lambda im, t: (paste_scaled(im, label_box("538 PEOPLE", 120), W / 2, 420, scale=pop_in(t, 0.2)),
                                       paste_scaled(im, marker_text("= not a town", 90), W / 2, 640, alpha=clamp((t - (vt2(5.84) - vt2(3.4))) / 0.15)),
                                       paste_scaled(im, marker_text("a village.", 110), W / 2, 820, alpha=clamp((t - (vt2(7.4) - vt2(3.4))) / 0.15), rot=-3)))),
        (vt2(8.4), C(S5, 2744.0, zoom=(1.1, 1.2), ymax=CAP)),
        (vt2(10.25), C(S5, 2745.5, zoom=(2.0, 2.1), cx=(0.68, 0.68), cy=(0.62, 0.62), ymax=CAP)),
        (vt2(12.4), Navy(namegrid)),
        (vt2(37.2), Navy(lambda im, t: (paste_scaled(im, label_box("523 TO GO", 140), W / 2, 460, scale=pop_in(t, 0.2)),
                                        paste_scaled(im, marker_text("very doable", 96), W / 2, 700, rot=-4, alpha=clamp((t - (vt2(38.82) - vt2(37.2))) / 0.15))))),
        # 2B
        (vb(0.0), C(S5, 2974.6, zoom=(1.0, 1.15), ymax=CAP)),
        (vb(2.6), C(S5, 2958.6, zoom=(1.1, 1.2), ymax=CAP)),
        (vb(5.3), C(S5, 3076.0, zoom=(1.05, 1.15), ymax=CAP)),
        (vb(7.5), St(S5, 3090.0, zoom=(1.25, 1.55), cx=(0.42, 0.45), cy=(0.4, 0.62), ymax=CAP)),
        (vb(13.5), St(S5, 2982.2, zoom=(1.7, 1.8), gray=(1, 1), **SIGN_CLOSE)),
        # back to chunk 2: "The problem is, this town keeps doing things..."
        (vr(40.1), St(S2, 6629.0, zoom=(1.4, 1.55))),
        (vr(41.2), C(D05, 4370.5, zoom=(1.1, 1.2), ymax=CAP)),
        (vr(42.4), St(S2, 6792.0, zoom=(1.0, 1.1))),
        (vr(43.6), C(N6, 3774.0, zoom=(1.0, 1.1), ymax=CAP)),
    ], end2)
    tl.tag(vt2(8.4), "WEHTS"); tl.tag(vb(5.3), "WEHTS")
    for k in [vt2(3.4), vt2(8.4), vt2(12.4), vt2(37.2), vb(0.0), vr(40.1)]: tl.sfx("whoosh_short", k - 0.05, 0.22)
    for i in range(len(names)): tl.sfx("typekey", vt2(ntimes[i]), 0.35)
    tl.sfx("stamp", vt2(3.45), 0.4); tl.sfx("pop", vt2(37.25), 0.3); tl.sfx("shutter", vb(13.5), 0.4)
    tl.aud.append(("clip", S5, vb(5.3), 3076.0, 2.0, 0.0))
    T = end2

    # ================= CHUNK 3: THE LINE =================
    c = "3"
    vt3, ins, end3 = tl.place_vo(c, T, [("vo", 0.0, 16.9), ("ins", S2, 6624.8, 6627.6, 1.0, 0.1), ("ins", S2, 6631.9, 6636.9, 1.0, 0.1),
                                        ("vo", 17.3, WORDS[c]["dur"])])
    tl.pill(vt3(0.0), "EXHIBIT B · THE LINE")
    i1, i2 = ins[0][0], ins[1][0]
    tk = ticket()
    tl.cuts([
        (vt3(0.0), Pol(grab(S2, 6450.0), "PATTY HYPE (2001)", rot=2.0)),
        (vt3(2.55), C(S2, 6337.0, zoom=(1.05, 1.15))),
        (vt3(4.6), St(S2, 6363.0, zoom=(1.1, 1.3))),
        (vt3(6.75), C(S2, 6362.0, zoom=(1.0, 1.1))),
        (vt3(8.25), C(S2, 6392.6, zoom=(1.2, 1.3))),
        (vt3(10.15), C(S2, 6446.5, zoom=(1.0, 1.08))),
        (vt3(11.9), C(S2, 6450.0, zoom=(1.3, 1.4), cx=(0.35, 0.35))),
        (vt3(13.1), C(S2, 6609.6, zoom=(1.0, 1.1))),
        (vt3(15.45), St(S2, 6629.0, zoom=(1.6, 1.15), ease=lambda x: x)),
        (i1, C(S2, 6624.8, zoom=(1.1, 1.15))),
        (i2, C(S2, 6631.9, zoom=(1.0, 1.06))),
        (vt3(17.3), Navy(lambda im, t: paste_scaled(im, text_layer("46,853", font("anton", 300), stroke=0, shadow=10), W / 2, H / 2, scale=pop_in(t, 0.2)))),
        (vt3(20.4), C(S2, 6450.2, zoom=(1.4, 1.5), cx=(0.3, 0.3), cy=(0.45, 0.45))),
        (vt3(24.05), Navy(lambda im, t: paste_scaled(im, tk, W / 2, lerp(H + 300, H / 2, ease_out(t / 0.3)), rot=-3))),
        (vt3(26.35), Navy(lambda im, t: (
            paste_scaled(im, label_box("538 PEOPLE", 96), 520, 480, scale=pop_in(t, 0.2)),
            paste_scaled(im, marker_text("x 87 trips", 100), W / 2 + 40, 480, alpha=clamp((t - (vt3(31.32) - vt3(26.35))) / 0.15), rot=-3),
            paste_scaled(im, label_box("46,853", 96), 1460, 480, scale=pop_in(t - (vt3(31.32) - vt3(26.35)) - 0.3, 0.2))))),
        (vt3(33.25), St(S2, 6363.0, zoom=(1.6, 1.8), cx=(0.68, 0.7), cy=(0.35, 0.35))),
        (vt3(35.3), C(S2, 6658.5, zoom=(1.1, 1.2))),
        (vt3(37.1), St(S5, 2978.6, zoom=(1.05, 1.4), cx=(0.55, 0.62), cy=(0.4, 0.35), ymax=CAP, gray=(0, 0.6))),
    ], end3)
    tl.tag(vt3(2.55), "PH")
    for k in [vt3(2.55), vt3(17.3), vt3(24.05), vt3(26.35), vt3(37.1)]: tl.sfx("whoosh_short", k - 0.05, 0.22)
    tl.sfx("hit", vt3(17.3), 0.4); tl.sfx("stamp", vt3(24.35), 0.4); tl.sfx("pop", vt3(31.32), 0.3); tl.sfx("pop", vt3(31.32) + 0.3, 0.3)
    tl.aud.append(("clip", S2, vt3(15.45), 6620.0, 1.2, 0.25))
    T = end3

    # ================= CHUNK 4: THE WITNESS =================
    c = "4"
    vt4, ins, end4 = tl.place_vo(c, T, [("vo", 0.0, 19.4), ("ins", N6, 3796.7, 3802.5, 1.0, 0.1), ("vo", 19.6, WORDS[c]["dur"])])
    tl.pill(vt4(0.0), "EXHIBIT C · THE WITNESS")
    iM = ins[0][0]
    form_m = [("POPULATION:", "MILLIONS?", None), ("SOURCE:", "MRS. PUFF", None), ("CONDITION:", "INFLATED", None)]
    def millions_form(im, t):
        f = drop_shadow(census_form(form_m, stamp="UNVERIFIED", stamp_p=clamp((t - 1.0) / 0.5), typed_p=clamp(t / 0.9)))
        paste_scaled(im, f, W / 2, lerp(H + 500, H / 2, ease_out(t / 0.3)), scale=1.1, rot=-1.5)
    three = [("538", "VILLAGE"), ("46,853", "CITY"), ("MILLIONS", "COUNTRY")]
    tts = [W_(c, "village,"), W_(c, "city,"), W_(c, "country.")]
    boxes = [label_box(a, 110, 520) for a, _ in three]; notes3 = [marker_text(b.lower(), 76) for _, b in three]
    def threeboxes(im, t):
        t0 = vt4(30.0)
        for i in range(3):
            ti = vt4(tts[i]) - t0 - 0.35
            if t < ti: continue
            x = 360 + i * 600; paste_scaled(im, boxes[i], x, 470, scale=pop_in(t - ti, 0.2), rot=[-2, 1.5, -1][i])
            if t > ti + 0.25: paste_scaled(im, notes3[i], x, 680, rot=-4)
    tl.cuts([
        (vt4(0.0), Pol(grab(N6, 3470.0), "NAUTICAL NOVICE (2008)", rot=-2.0)),
        (vt4(3.0), C(N6, 3600.0, zoom=(1.1, 1.2), ymax=CAP)),
        (vt4(5.15), C(N6, 3781.5, zoom=(1.3, 1.45), ymax=CAP)),
        (vt4(8.85), C(N6, 3700.0, zoom=(1.0, 1.1), ymax=CAP)),
        (vt4(11.85), C(N6, 3745.0, zoom=(1.0, 1.1), ymax=CAP)),
        (vt4(14.0), C(N6, 3773.6, zoom=(1.1, 1.2), ymax=CAP)),
        (vt4(16.3), C(N6, 3793.2, zoom=(1.0, 1.1), ymax=CAP)),
        (iM, C(N6, 3796.7, zoom=(1.05, 1.12), ymax=CAP)),
        (iM + 4.2, C(N6, 3800.9, zoom=(1.2, 1.25), ymax=CAP)),
        (vt4(19.65), St(N6, 3798.5, zoom=(1.6, 1.7), cx=(0.68, 0.68), cy=(0.4, 0.4), ymax=CAP, gray=(1, 1))),
        (vt4(20.8), C(N6, 3781.0, zoom=(1.6, 1.7), cx=(0.3, 0.3), cy=(0.45, 0.45), ymax=CAP)),
        (vt4(22.3), C(N6, 3797.5, zoom=(1.4, 1.5), cx=(0.7, 0.7), cy=(0.4, 0.4), ymax=CAP)),
        (vt4(23.5), Navy(millions_form)),
        (vt4(26.35), C(N6, 3905.5, zoom=(1.1, 1.2), ymax=CAP)),
        (vt4(30.0), Navy(threeboxes)),
        (vt4(36.15), St(S2, CROWD_T, zoom=(1.0, 1.2), gray=(0, 0))),
    ], end4)
    tl.tag(vt4(3.0), "NN")
    for k in [vt4(3.0), vt4(8.85), vt4(23.5), vt4(30.0), vt4(36.15)]: tl.sfx("whoosh_short", k - 0.05, 0.22)
    tl.sfx("shutter", vt4(19.65), 0.45); tl.sfx("stamp", vt4(24.5), 0.5); tl.sfx("shutter", vt4(36.15), 0.4)
    ov_m = text_layer("MILLIONS", font("anton", 220), stroke=0, shadow=12)
    tl.ov(vt4(19.7), vt4(20.8), lambda img, t, tg: paste_scaled(img, ov_m, W / 2, 820, scale=pop_in(t, 0.2)))
    for k, tt in enumerate(tts): tl.sfx("pop", vt4(tt) - 0.35, 0.3)
    T = end4

    # ================= CHUNK 5: THE STADIUM =================
    c = "5"
    vt5, ins, end5 = tl.place_vo(c, T, [("vo", 0.0, 29.3), ("ins", D05, 4373.4, 4378.1, 1.0, 0.15), ("vo", 29.9, WORDS[c]["dur"])])
    tl.pill(vt5(0.0), "EXHIBIT D · THE STADIUM")
    iB = ins[0][0]
    n = len(HEADS); crowdP = pillar(crowd_img())
    def counting_fast(t0v):
        def fn(tl_, tg):
            im = crowdP.copy().convert("RGBA"); dur = 1.75; cnt = 0
            for i, (x, y) in enumerate(HEADS):
                ti = dur * (i / n) ** 0.8
                if tl_ >= ti: cnt += 1; dot(im, 240 + x * 2.25, y * 2.25, 11, pop_in(tl_ - ti, 0.12))
            ep_tag(im, f"FISH COUNTED: {cnt}")
            if cnt == n: paste_scaled(im, text_layer("77", font("anton", 300), stroke=0, shadow=12), W / 2, H / 2, scale=pop_in(tl_ - dur - 0.15, 0.2))
            return im.convert("RGB")
        return fn
    def bars(im, t):
        x0 = 200; full = 1520
        paste_scaled(im, label_box("THE LINE: 46,853", 64), x0 + 330, 330)
        ImageDraw.Draw(im).rectangle([x0, 420, x0 + int(full * ease_out(t / 0.6)), 500], fill=CARD)
        paste_scaled(im, label_box("THE CROWD SHOT: 77", 64), x0 + 380, 650)
        ImageDraw.Draw(im).rectangle([x0, 740, x0 + max(3, int(full * 77 / 46853)), 820], fill=(200, 40, 40))
        if t > 0.9: paste_scaled(im, marker_text("~ 1/600th", 110), 1180, 780, rot=-4, alpha=clamp((t - 0.9) / 0.15))
    tl.cuts([
        (vt5(0.0), Pol(grab(D05, 4311.0), "BAND GEEKS (2001)", rot=2.5)),
        (vt5(1.5), C(D05, 3861.0, zoom=(1.1, 1.2), ymax=CAP)),
        (vt5(4.85), C(D05, 4310.0, zoom=(1.0, 1.1), ymax=CAP)),
        (vt5(7.55), C(D05, 4368.5, zoom=(1.0, 1.1), ymax=CAP)),
        (vt5(10.1), St(D05, 4371.3, zoom=(1.0, 1.15), ymax=CAP, ease=lambda x: x)),
        (vt5(17.1), St(D05, 4373.0, zoom=(1.6, 1.7), cx=(0.45, 0.45), cy=(0.35, 0.35), ymax=CAP)),
        (vt5(18.9), C(D05, 4370.5, zoom=(1.0, 1.1), ymax=CAP)),
        (vt5(22.0), C(D05, 4372.0, zoom=(1.2, 1.3), ymax=CAP)),
        (vt5(26.7), C(D05, 4373.0, zoom=(1.0, 1.05), ymax=CAP)),
        (iB, C(D05, 4373.4, zoom=(1.0, 1.05), ymax=CAP)),
        (iB + 2.6, C(D05, 4376.0, zoom=(1.35, 1.4), cx=(0.55, 0.55), cy=(0.45, 0.45), ymax=CAP)),
        (vt5(29.9), St(D05, 4377.0, zoom=(1.4, 1.5), cx=(0.55, 0.55), cy=(0.45, 0.45), ymax=CAP, gray=(1, 1))),
        (vt5(33.5), St(D05, 4371.3, zoom=(1.0, 1.1), ymax=CAP, gray=(1, 1))),
        (vt5(35.75), Pol(crowd_img(), "PATTY HYPE (2001)", rot=-2.0)),
        (vt5(40.2), Fn(lambda t_, tg: pillar(crowd_img()))),
        (vt5(42.3), Fn(counting_fast(0))),
        (vt5(45.45), Navy(bars)),
    ], end5)
    tl.tag(vt5(1.5), "BG")
    note = marker_text("remember this one", 80)
    tl.ov(vt5(30.0), vt5(33.5), lambda img, t, tg: paste_scaled(img, note, 1300, 200, rot=-5, scale=pop_in(t, 0.2)))
    tl.ov(vt5(33.6), vt5(35.75), lambda img, t, tg: paste_scaled(img, label_box("HUMANS: 0", 100), W / 2, H / 2, scale=pop_in(t, 0.2), rot=-2))
    tl.sfx("shutter", vt5(10.1), 0.45); tl.sfx("scratch", vt5(17.1) - 0.05, 0.45)
    tl.aud.append(("clip", D05, vt5(18.9), 4370.5, (vt5(26.7) - vt5(18.9)), 0.35))
    for k in [vt5(1.5), vt5(30.0), vt5(35.75), vt5(45.45)]: tl.sfx("whoosh_short", k - 0.05, 0.22)
    for i in range(0, n, 3): tl.sfx("tick", vt5(42.3) + 1.75 * (i / n) ** 0.8, 0.18)
    tl.sfx("ding", vt5(44.15), 0.35); tl.sfx("pop", vt5(30.0), 0.3); tl.sfx("stamp", vt5(33.6), 0.35)
    T = end5

    # ================= CHUNK 6: SAME GUY =================
    c = "6"
    vt6, ins, end6 = tl.place_vo(c, T, [("vo", 0.0, 13.42), ("vo", 15.55, WORDS[c]["dur"]), ("ins", S2, 6604.8, 6608.1, 1.0, 0.25)])
    tl.pill(vt6(0.0), "EXHIBIT E · SAME GUY")
    iL = ins[0][0]
    A, B = REPEATS["smallblue"]; L, R = REPEATS["yellow"]
    def zoom_on(pt, z):
        x, y = pt
        return St(S2, CROWD_T, zoom=(z, z * 1.08), cx=(x / 640, x / 640), cy=(y / 480, y / 480))
    pa = polaroid(grab(S2, CROWD_T).crop((0, 118, 84, 188)).resize((480, 400)), "THIS ONE", 620)
    pb = polaroid(grab(S2, CROWD_T).crop((552, 0, 636, 70)).resize((480, 400)), "ALSO THIS ONE", 620)
    fishcards = [polaroid(head_crop(i, 90).resize((360, 360)), f"FISH #{k + 1}", 420) for k, i in enumerate([4, 11, 33, 47, 60])]
    def modelsheet(im, t):
        for k, fc in enumerate(fishcards):
            ti = 0.15 + k * 0.35
            if t >= ti: paste_scaled(im, fc, 260 + k * 350, 540 + (40 if k % 2 else -40), rot=[-4, 3, -2, 4, -3][k], scale=pop_in(t - ti, 0.2))
    faces = [head_crop(i, 76).resize((150, 150)) for i in range(0, 77, 2)][:40]
    def forty(im, t):
        for k, f in enumerate(faces):
            ti = 0.05 + k * 0.03
            if t < ti: continue
            r, cc = divmod(k, 10); x = 330 + cc * 140; y = 260 + r * 160
            card = Image.new("RGBA", (158, 158), CARD + (255,)); card.paste(f, (4, 4))
            paste_scaled(im, card, x, y, scale=pop_in(t - ti, 0.15), rot=((k * 37) % 9) - 4)
        paste_scaled(im, label_box("40 RESIDENTS?", 80), W / 2, 980, rot=-1.5)
    tl.cuts([
        (vt6(0.0), Fn(lambda t_, tg: pillar(crowd_img()))),
        (vt6(1.8), St(S2, CROWD_T, zoom=(1.0, 1.5), ease=lambda x: x)),
        (vt6(3.8), zoom_on(A, 3.2)),
        (vt6(7.85), zoom_on(B, 3.2)),
        (vt6(10.3), zoom_on(L, 2.8)),
        (vt6(11.9), zoom_on(R, 2.8)),
        (vt6(12.95), Navy(lambda im, t: (paste_scaled(im, pa, 560, 540, rot=-3, scale=pop_in(t, 0.2)), paste_scaled(im, pb, 1360, 540, rot=3, scale=pop_in(t - 0.25, 0.2))))),
        (vt6(15.6), Navy(modelsheet)),
        (vt6(25.9), Navy(lambda im, t: paste_scaled(im, marker_text("theory #2:", 120), W / 2, 420, rot=-3, scale=pop_in(t, 0.2)) or
                         paste_scaled(im, label_box("BIKINI BOTTOM IS TINY", 100), W / 2, 640, scale=pop_in(t - (vt6(27.99) - vt6(25.9)), 0.2)))),
        (vt6(30.9), Navy(forty)),
        (vt6(34.85), St(S2, 6629.0, zoom=(1.4, 1.55))),
        (vt6(35.85), C(S2, 6280.0, zoom=(1.0, 1.08))),
        (vt6(37.35), C(D05, 4371.0, zoom=(1.1, 1.2), ymax=CAP)),
        (vt6(38.75), St(D05, 4373.0, zoom=(1.7, 1.8), cx=(0.4, 0.4), cy=(0.35, 0.35), ymax=CAP)),
        (vt6(40.4), C(S5, 4775.0, zoom=(1.0, 1.1), ymax=CAP)),
        (vt6(41.7), St(S2, 6629.0, zoom=(1.5, 1.7))),
        (vt6(44.2), C(S2, 6767.0, zoom=(1.0, 1.1), speed=0.8)),
        (vt6(47.3), C(S2, 6606.0, zoom=(1.0, 1.05))),
        (iL, C(S2, 6604.8, zoom=(1.0, 1.05))),
        (iL + 1.5, C(S2, 6606.3, zoom=(1.45, 1.5), cx=(0.35, 0.35), cy=(0.5, 0.5))),
    ], end6)
    for k in [vt6(3.8), vt6(7.85), vt6(10.3), vt6(11.9)]: tl.sfx("whoosh_short", k - 0.05, 0.3)
    for k in [vt6(12.95), vt6(15.6), vt6(25.9), vt6(30.9), vt6(34.85)]: tl.sfx("swish", k - 0.04, 0.25)
    for k in range(5): tl.sfx("pop", vt6(15.6) + 0.15 + k * 0.35, 0.25)
    for k in range(0, 40, 3): tl.sfx("pop_hi", vt6(30.9) + 0.05 + k * 0.03, 0.12)
    T = end6

    # ================= CHUNK 7: THE STUFF =================
    c = "7"
    vt7, _, end7 = tl.place_vo(c, T, [("vo", 0.0, WORDS[c]["dur"])])
    tl.pill(vt7(0.0), "EXHIBIT F · THE STUFF")
    items = ["Hospital", "Police force", "Stadium", "Mall", "Glove-themed theme park", "Boating school", "Two restaurants at war"]
    it_t = [W_(c, "hospital."), W_(c, "police"), W_(c, "stadium."), W_(c, "mall."), W_(c, "entire"), W_(c, "boating"), W_(c, "two")]
    base = vt7(3.6)
    ck = checklist_draw(items, [vt7(x) - base - 0.1 for x in it_t], [vt7(x) - base + 0.35 for x in it_t], cols=2, w=740, h=112, y0=190)
    gs = gas_station(); dale = marker_text("est. population: Dale", 70)
    tl.cuts([
        (vt7(0.0), Navy(forty)),
        (vt7(3.6), Navy(ck)),
        (vt7(8.45), C(D05, 4368.5, zoom=(1.0, 1.1), ymax=CAP)),
        (vt7(9.45), Navy(lambda im, t: ck(im, t + vt7(9.45) - base))),
        (vt7(13.5), C(N6, 3455.0, zoom=(1.0, 1.08), ymax=CAP)),
        (vt7(14.95), C(S2, 6280.0, zoom=(1.0, 1.08))),
        (vt7(16.5), C(S5, 4082.0, zoom=(1.0, 1.1), ymax=CAP)),
        (vt7(18.3), Navy(lambda im, t: ck(im, t + vt7(18.3) - base))),
        (vt7(20.6), Navy(lambda im, t: (paste_scaled(im, gs, W / 2, 560, scale=pop_in(t, 0.25)),
                                        paste_scaled(im, dale, 1500, 200, rot=-5, alpha=clamp((t - (vt7(24.4) - vt7(20.6))) / 0.15))))),
        (vt7(26.8), C(D05, 4368.5, zoom=(1.0, 1.1), ymax=CAP)),
        (vt7(28.45), C(D05, 4371.0, zoom=(1.1, 1.2), ymax=CAP)),
        (vt7(31.45), C(S5, 4082.0, zoom=(1.2, 1.3), ymax=CAP)),
        (vt7(35.75), St(S5, 4083.5, zoom=(1.5, 1.6), cy=(0.4, 0.4), ymax=CAP, gray=(1, 1))),
    ], end7)
    tl.tag(vt7(13.5), "NN", 1.4)
    tl.ov(vt7(35.8), end7, lambda img, t, tg: paste_scaled(img, label_box("25+ YEARS", 110), 1450, 860, scale=pop_in(t, 0.2), rot=-3))
    for x in it_t: tl.sfx("tick", vt7(x) + 0.35, 0.35)
    tl.sfx("cricket", vt7(24.3), 0.3); tl.sfx("stamp", vt7(35.85), 0.35)
    for k in [vt7(3.6), vt7(20.6)]: tl.sfx("swish", k - 0.04, 0.25)
    T = end7

    # ================= CHUNK 8: THE VERDICT =================
    c = "8"
    vt8, _, end8 = tl.place_vo(c, T, [("vo", 0.0, WORDS[c]["dur"])])
    tl.pill(vt8(0.0), "THE VERDICT", 3.0)
    form_v = [("POPULATION:", "~50,000", "538"), ("SOURCE:", "THE PATTY LINE", None), ("METHOD:", "ACTUAL COUNTING", None)]
    def verdict_form(im, t):
        f = drop_shadow(census_form(form_v, stamp="CORRECTED", stamp_p=clamp((t - 1.4) / 0.5), typed_p=clamp(t / 1.2)))
        paste_scaled(im, f, W / 2, lerp(H + 500, H / 2, ease_out(t / 0.3)), scale=1.12, rot=1.5)
    allck = checklist_draw(items, [0] * 7, [0.1 + k * 0.12 for k in range(7)], cols=2, w=740, h=112, y0=190)
    tl.cuts([
        (vt8(0.0), Navy(lambda im, t: None)),
        (vt8(2.05), St(S5, 2978.6, zoom=(1.1, 1.2), cx=(0.55, 0.6), cy=(0.4, 0.38), ymax=CAP, gray=(0.9, 0.9))),
        (vt8(5.1), St(S5, 2982.2, zoom=(1.3, 1.45), cx=(0.62, 0.7), cy=(0.83, 0.83), ymax=400, gray=(0.9, 0.9))),
        (vt8(10.7), C(S5, 2985.9, zoom=(1.35, 1.4), cx=(0.62, 0.62), ymax=CAP)),
        (vt8(12.6), St(S2, 6629.0, zoom=(1.3, 1.6), ease=lambda x: x)),
        (vt8(19.05), Navy(lambda im, t: paste_scaled(im, tk, W / 2, lerp(H + 300, H / 2, ease_out(t / 0.3)), rot=2))),
        (vt8(21.2), St(S2, 6363.0, zoom=(1.1, 1.25))),
        (vt8(24.4), C(S2, 6730.0, zoom=(1.0, 1.1))),
        (vt8(28.15), St(S2, CROWD_T, zoom=(1.2, 1.0))),
        (vt8(30.75), Navy(lambda im, t: (paste_scaled(im, text_layer("~50,000", font("anton", 300), stroke=0, shadow=12), W / 2, 470, scale=pop_in(t, 0.22)),
                                         paste_scaled(im, paper_card("our estimate", 520, 120, 52), W / 2, 760, rot=-2, alpha=clamp((t - 0.4) / 0.15))))),
        (vt8(34.2), Navy(allck)),
        (vt8(42.05), Navy(verdict_form)),
        (vt8(46.35), C(N6, 3781.5, zoom=(1.3, 1.4), ymax=CAP)),
        (vt8(50.7), C(N6, 3700.5, zoom=(1.1, 1.2), ymax=CAP)),
        (vt8(53.0), St(N6, 3798.5, zoom=(1.6, 1.65), cx=(0.68, 0.68), cy=(0.4, 0.4), ymax=CAP)),
    ], end8 + 0.4)
    tl.sfx("hit", vt8(30.75), 0.5); tl.sfx("stamp", vt8(43.5), 0.55)
    for k in range(7): tl.sfx("tick", vt8(34.2) + 0.1 + k * 0.12, 0.3)
    for k in [vt8(2.05), vt8(12.6), vt8(19.05), vt8(30.75), vt8(34.2), vt8(42.05)]: tl.sfx("whoosh_short", k - 0.05, 0.22)
    tl.sfx("typekey", vt8(42.3), 0.3); tl.sfx("typekey", vt8(42.5), 0.3); tl.sfx("typekey", vt8(42.7), 0.3)
    T = end8 + 0.4

    # ================= CHUNK 9: THE OTHER BIKINI =================
    c = "9"
    vt9, ins, end9 = tl.place_vo(c, T, [("vo", 0.0, 44.75), ("ins", D05, 4376.0, 4378.1, 1.0, 0.15), ("vo", 47.75, WORDS[c]["dur"])], gap_after=0.0)
    iS = ins[0][0]
    tl.pill(vt9(0.4), "ONE MORE BIKINI", 3.0)
    form_b = [("POPULATION:", "5", "167"), ("REASON:", "ATOMIC TESTING", None), ("SINCE:", "1946", None)]
    def bikini_form(im, t):
        f = drop_shadow(census_form(form_b, typed_p=clamp(t / 1.5), title="BIKINI ATOLL", sub="MARSHALL ISLANDS"))
        paste_scaled(im, f, W / 2, H / 2, scale=lerp(1.05, 1.15, t / 6), rot=-1)
    timeline_cards = [paper_card(s, 640, 120, 46) for s in ["1946 · moved off", "1968 · told it's safe", "1978 · evacuated again"]]
    def tlcards(im, t):
        for k, cd in enumerate(timeline_cards):
            ti = [0.0, 1.0, 2.4][k]
            if t >= ti: paste_scaled(im, cd, W / 2, 330 + k * 200, rot=[-1.5, 1, -1][k], alpha=clamp((t - ti) / 0.15))
    mp = map_draw(lambda t: clamp(t / 0.5) + clamp((t - 0.7) / 0.5) + clamp((t - 1.4) / 0.5))
    def boardmap(t_, tg):
        im = board_bg().convert("RGBA"); mp(im, t_); return im.convert("RGB")
    def big(txt):
        L = text_layer(txt, font("anton", 340), stroke=0, shadow=12)
        return Navy(lambda im, t: paste_scaled(im, L, W / 2, H / 2, alpha=clamp(t / 0.4)))
    endcard_title = text_layer("THE BIKINI BOTTOM CENSUS", font("anton", 60), stroke=0, shadow=6)
    tl.cuts([
        (vt9(0.0), Navy(lambda im, t: None)),
        (vt9(3.6), St(S2, 6775.5, zoom=(1.0, 1.15))),
        (vt9(6.8), C(NAT, 20.0, zoom=(1.0, 1.1))),
        (vt9(8.4), C(NAT, 290.0, zoom=(1.0, 1.08))),
        (vt9(11.7), C(NAT, 280.0, zoom=(1.0, 1.08))),
        (vt9(13.7), C(NAT, 300.0, zoom=(1.05, 1.12))),
        (vt9(16.0), big("167")),
        (vt9(17.95), C(NAT, 258.0, zoom=(1.0, 1.08))),
        (vt9(19.75), C(NAT, 56.0, zoom=(1.0, 1.08))),
        (vt9(22.9), C(BAK, 2.0, zoom=(1.0, 1.15), speed=0.85)),
        (vt9(24.6), C(NAT, 392.0, zoom=(1.0, 1.08))),
        (vt9(27.0), C(NAT, 312.0, zoom=(1.0, 1.08))),
        (vt9(29.7), C(NAT, 376.0, zoom=(1.0, 1.08))),
        (vt9(31.45), C(NAT, 484.0, zoom=(1.0, 1.08))),
        (vt9(33.3), Fn(boardmap)),
        (vt9(36.0), Navy(tlcards)),
        (vt9(40.1), C(BAK, 62.0, zoom=(1.0, 1.1))),
        (vt9(43.2), Pol(grab(D05, 4311.0), "BAND GEEKS (2001)", rot=2.0, zt=0.25)),
        (iS, C(D05, 4376.0, zoom=(1.3, 1.35), cx=(0.55, 0.55), cy=(0.45, 0.45), ymax=CAP)),
        (vt9(47.8), St(D05, 4377.6, zoom=(1.5, 1.7), cx=(0.55, 0.55), cy=(0.45, 0.45), ymax=CAP, gray=(0, 1))),
        (vt9(50.1), C(BAK, 4.0, zoom=(1.0, 1.1), speed=0.7)),
        (vt9(51.95), C(NAT, 16.0, zoom=(1.0, 1.1))),
        (vt9(55.0), big("5")),
        (vt9(57.6), C(S5, 2985.9, zoom=(1.35, 1.4), cx=(0.62, 0.62), ymax=CAP, gray=(1, 1))),
        (vt9(62.2), Navy(bikini_form)),
        (vt9(68.4), Navy(lambda im, t: paste_scaled(im, endcard_title, W / 2, 120, alpha=clamp(t / 0.5)))),
    ], vt9(WORDS[c]["dur"]) + 12.0)
    tl.tag(vt9(6.8), "NAVY", 3.0); tl.tag(vt9(22.9), "BAKER", 1.6); tl.tag(vt9(50.1), "BAKER", 1.8)
    tl.sfx("hit", vt9(0.0), 0.35); tl.sfx("boom", vt9(22.9), 0.55); tl.sfx("boom", vt9(50.1), 0.45)
    tl.sfx("whoosh_down", vt9(3.55), 0.25); tl.sfx("swish", vt9(33.3), 0.25); tl.sfx("swish", vt9(36.0), 0.25); tl.sfx("swish", vt9(62.2), 0.25)
    for k in range(3): tl.sfx("typekey", vt9(62.3) + k * 0.25, 0.3)
    total = vt9(WORDS[c]["dur"]) + 12.0
    return tl, total

if __name__ == "__main__":
    tl, total = build_all()
    print("total duration", round(total, 2), "s; shots", len(tl.shots))
    if len(sys.argv) > 2:  # partial render: start end
        a, b = float(sys.argv[2]), float(sys.argv[3])
    else:
        a, b = 0.0, total
    mx = Mixer(total + 1); mix_events(mx, tl.aud)
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCR, "renders", "full.mp4")
    if a > 0 or b < total:
        # shift timeline for a partial preview
        shots = [dict(s, t0=s["t0"] - a, t1=s["t1"] - a) for s in tl.shots if s["t1"] > a and s["t0"] < b]
        for s in shots:
            if s["t0"] < 0:
                f0 = s["frame"]; off = -s["t0"]; s["frame"] = (lambda f0, off: lambda tl_, tg: f0(tl_ + off, tg + off))(f0, off); s["t0"] = 0
        ovs = [dict(o, t0=o["t0"] - a, t1=o["t1"] - a) for o in tl.ovs if o["t1"] > a and o["t0"] < b]
        m2 = Mixer(b - a + 1); m2.buf[:] = mx.buf[int(a * SR):int(a * SR) + len(m2.buf)] if len(mx.buf) > int(a * SR) + len(m2.buf) else np.pad(mx.buf[int(a * SR):], ((0, len(m2.buf) - len(mx.buf[int(a * SR):])), (0, 0)))
        render(shots, ovs, m2, out, b - a)
    else:
        render(tl.shots, tl.ovs, mx, out, total)
