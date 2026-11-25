"""Cold open (style test v2, matched to the channel's house style): chunk 1 VO + clips + graphics + SFX."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from graphics import *
from data import *

def pillar(src):
    """4:3 frame centered on 16:9 over navy."""
    bg = navy_bg()
    fg = src.resize((1440, 1080), Image.BICUBIC).filter(ImageFilter.UnsharpMask(2.2, 70, 2))
    bg.paste(fg, (240, 0)); return bg

def with_tag(shot, text, dur=2.6):
    """Wrap a shot so the episode tag shows for its first `dur` seconds."""
    f0 = shot["frame"]
    def fr(tl, tg):
        im = f0(tl, tg)
        if tl < dur:
            im = im.convert("RGBA"); ep_tag(im, text, alpha=clamp(tl / 0.2) * clamp((dur - tl) / 0.3)); im = im.convert("RGB")
        return im
    s = dict(shot); s["frame"] = fr; return s

def polaroid_shot(t0, t1, src_img, caption, rot=-3.0, notes=None, zoom_through=0.0):
    """Navy card with a pinned polaroid; optional zoom-through into the photo at the end."""
    pol = polaroid(src_img, caption, 900); dur = t1 - t0
    def fr(tl, tg):
        im = navy_bg().convert("RGBA")
        sc = lerp(0.96, 1.02, tl / dur)
        if zoom_through and tl > dur - zoom_through:
            k = (tl - (dur - zoom_through)) / zoom_through; sc *= lerp(1.0, 2.6, k ** 2)
        y = lerp(H / 2 + 60, H / 2, ease_out(tl / 0.35))
        paste_scaled(im, pol, W / 2, y, scale=sc, rot=rot)
        if notes: notes(im, tl)
        return im.convert("RGB")
    return fn_shot(t0, t1, fr)

def build_coldopen(T0=0.0):
    shots, ovs, aud = [], [], []
    V = VO["1"]
    A_end = 15.75; INS = 4.3
    B_src = (16.90, 20.78); C_src = (21.90, WORDS["1"]["dur"])
    tB = T0 + A_end + INS
    tC = tB + (B_src[1] - B_src[0]) + 0.15
    off = tC - C_src[0]
    aud += [("vo", V, T0, 0.0, A_end, 1.0), ("vo", V, tB, B_src[0], B_src[1] - B_src[0], 1.0),
            ("vo", V, tC, C_src[0], C_src[1] - C_src[0], 1.0)]
    vA = lambda v: T0 + v
    vC = lambda v: v + off
    WEHTS = "WHAT EVER HAPPENED TO SPONGEBOB? · 2008"; PH = "PATTY HYPE · 2001"

    aud.append(("sfx", "wind", T0, 0.15))
    # --- "This sign is on the road out of Bikini Bottom." polaroid -> zoom through into footage
    shots.append(polaroid_shot(vA(0), vA(1.7), grab(S5, 2978.6), "WHAT EVER HAPPENED TO SPONGEBOB? (2008)", rot=-2.5, zoom_through=0.3))
    aud.append(("sfx", "whoosh_short", vA(1.45), 0.3))
    shots.append(with_tag(clip_shot(vA(1.7), vA(3.3), S5, 2978.2, speed=0.6, zoom=(1.15, 1.35), cx=(0.55, 0.62), cy=(0.4, 0.35), ymax=CAP), WEHTS, 3.0))
    # --- "Population? 538."
    shots.append(still_shot(vA(3.3), vA(4.85), S5, 2982.2, zoom=(1.3, 1.4), cx=(0.62, 0.7), cy=(0.83, 0.83), ymax=400))
    t538 = vA(4.85)
    shots.append(still_shot(t538, vA(6.2), S5, 2982.2, zoom=(1.75, 1.85), cx=(0.766, 0.766), cy=(0.83, 0.83), ymax=400))
    aud.append(("sfx", "hit", t538, 0.45)); aud.append(("sfx", "scribble", t538 + 0.05, 0.25))
    ovs.append({"t0": t538 + 0.05, "t1": vA(6.2), "draw": lambda img, tl, tg: marker_circle(ImageDraw.Draw(img), (560, 560, 1360, 990), progress=clamp(tl / 0.4), width=14, seed=4)})
    # --- "decides the town doesn't need him anymore" (3 quick cuts)
    shots.append(clip_shot(vA(6.2), vA(7.6), S5, 2917.4, zoom=(1.1, 1.15), ymax=CAP))
    shots.append(clip_shot(vA(7.6), vA(8.7), S5, 2921.5, zoom=(1.1, 1.15), ymax=CAP))
    shots.append(clip_shot(vA(8.7), vA(10.5), S5, 2925.0, zoom=(1.45, 1.55), cy=(0.4, 0.4), ymax=CAP))
    aud.append(("sfx", "whoosh_down", vA(6.15), 0.25))
    # --- packs a bag / walks out / stops at sign
    shots.append(clip_shot(vA(10.5), vA(11.6), S5, 2955.6, zoom=(1.15, 1.2), ymax=CAP))
    shots.append(clip_shot(vA(11.6), vA(12.6), S5, 2960.4, zoom=(1.1, 1.15), ymax=CAP))
    shots.append(clip_shot(vA(12.6), vA(14.2), S5, 2979.6, zoom=(1.05, 1.2), cy=(0.4, 0.4), ymax=CAP))
    shots.append(still_shot(vA(14.2), vA(A_end), S5, 2983.6, zoom=(1.0, 1.12), ymax=CAP))
    # --- INSERT: the real moment with show audio, two angles
    tI = vA(A_end)
    shots.append(clip_shot(tI, tI + 2.0, S5, 2983.9, zoom=(1.0, 1.05), ymax=CAP))
    shots.append(clip_shot(tI + 2.0, tI + INS, S5, 2985.9, zoom=(1.35, 1.4), cx=(0.62, 0.62), ymax=CAP))
    aud.append(("clip", S5, tI, 2983.9, INS, 1.0))
    aud.append(("sfx", "scribble", tI + 1.6, 0.3))
    # --- 537 freeze, B&W, handwritten -1
    shots.append(still_shot(tB, tB + 1.45, S5, 2988.0, zoom=(1.05, 1.35), cx=(0.5, 0.55), ymax=CAP, gray=(1.0, 1.0), ease=ease_out))
    aud.append(("sfx", "shutter", tB, 0.55))
    m1 = marker_text("-1", 260)
    ovs.append({"t0": tB + 0.15, "t1": tB + 1.45, "draw": lambda img, tl, tg: paste_scaled(img, m1, 1500, 330, scale=pop_in(tl, 0.2), rot=-8)})
    aud.append(("sfx", "scribble", tB + 0.15, 0.25))
    # --- census form on navy
    tF = tB + 1.45; tF_end = vC(23.82)
    lines = [("POPULATION:", "537", "538"), ("UPDATED BY:", "S. SQUAREPANTS", None), ("METHOD:", "CHALK, ON HIS WAY OUT", None)]
    def form_frame(tl, tg):
        im = navy_bg().convert("RGBA")
        f = census_form(lines, stamp="OFFICIAL", stamp_p=clamp((tl - 2.5) / 0.5), typed_p=clamp(tl / 2.2))
        f = drop_shadow(f)
        paste_scaled(im, f, W / 2, lerp(H + 500, H / 2, ease_out(tl / 0.35)), scale=lerp(1.08, 1.13, tl / 4), rot=1.5)
        return im.convert("RGB")
    shots.append(fn_shot(tF, tF_end, form_frame))
    aud.append(("sfx", "whoosh", tF - 0.05, 0.35))
    for k in range(18):
        aud.append(("sfx", "typekey", tF + 0.3 + k * 0.11 + (0.03 if k % 3 == 0 else 0), 0.3))
    aud.append(("sfx", "stamp", tF + 2.5, 0.6))
    # --- "except, seven years earlier" -> Patty Hype polaroid + marker note
    tEx = vC(23.82)
    aud.append(("sfx", "scratch", tEx - 0.05, 0.4))
    note = marker_text("7 years earlier", 64)
    def notes(im, tl):
        if tl > 0.35:
            p = clamp((tl - 0.35) / 0.3)
            marker_arrow(im, (1560, 300), (1390, 400), progress=p)
            if p >= 1: paste_scaled(im, note, 1620, 240, rot=-6)
    shots.append(polaroid_shot(tEx, vC(25.42), grab(S2, 6450.0), "PATTY HYPE (2001)", rot=2.5, notes=notes, zoom_through=0.25))
    aud.append(("sfx", "whoosh", tEx + 0.02, 0.35))
    # --- 46,853: three quick angles on the crowd, counter rolls across them
    t46 = vC(25.42); t46_end = vC(30.82); seg = (t46_end - t46) / 3
    shots.append(with_tag(clip_shot(t46, t46 + seg, S2, 6766.6, speed=0.8, zoom=(1.0, 1.1)), PH, 2.4))
    shots.append(clip_shot(t46 + seg, t46 + 2 * seg, S2, 6767.8, speed=0.8, zoom=(1.7, 1.8), cx=(0.42, 0.42), cy=(0.55, 0.55)))
    shots.append(clip_shot(t46 + 2 * seg, t46_end, S2, 6769.0, speed=0.8, zoom=(1.3, 1.45), cx=(0.7, 0.72), cy=(0.35, 0.3)))
    aud.append(("clip", S2, t46, 6766.6, (t46_end - t46) * 0.8, 0.22))
    numL = {}
    def counter(img, tl, tg):
        p = ease_out(clamp(tl / 2.4)); s = f"{int(round(46853 * p)):,}"
        if s not in numL: numL[s] = text_layer(s, font("anton", 230), stroke=0, shadow=10)
        paste_scaled(img, numL[s], W / 2, 520, scale=1.0 + (0.08 * max(0, 1 - (tl - 2.4) / 0.25) if tl > 2.4 else 0))
        if tl > 2.4:
            paste_scaled(img, paper_card("people in one line", 640, 120, 50), W / 2, 720, scale=pop_in(tl - 2.4, 0.2), rot=-1.5)
    ovs.append({"t0": t46 + 0.05, "t1": t46_end, "draw": counter})
    aud.append(("sfx", "counter", t46 + 0.05, 0.4)); aud.append(("sfx", "counter", t46 + 0.85, 0.28))
    aud.append(("sfx", "ding", t46 + 2.45, 0.35))
    for k in (1, 2): aud.append(("sfx", "whoosh_short", t46 + k * seg - 0.08, 0.18))
    # --- 87 Bikini Bottoms on navy
    t87 = vC(30.82); t87_end = vC(34.55)
    icon = sign_icon(1.0); cols = 13; gx, gy = 142, 122; ox = W / 2 - (cols - 1) * gx / 2; oy = 140
    rng = np.random.default_rng(5); jit = [(rng.uniform(-12, 12), rng.uniform(-8, 8), rng.uniform(-7, 7)) for _ in range(87)]
    def grid(tl, tg):
        im = navy_bg().convert("RGBA")
        for i in range(87):
            ti = 0.02 + i * 0.016
            if tl < ti: continue
            r, c = divmod(i, cols)
            paste_scaled(im, icon, ox + c * gx + jit[i][0], oy + r * gy + jit[i][1], scale=0.9 * pop_in(tl - ti, 0.18), rot=jit[i][2])
        cnt = min(87, 1 + int(clamp((tl - 0.02) / (86 * 0.016)) * 86)) if tl > 0.02 else 0
        paste_scaled(im, paper_card(f"{cnt} Bikini Bottoms", 620, 120, 50), W / 2, 1000, rot=-1)
        return im.convert("RGB")
    shots.append(fn_shot(t87, t87_end, grid))
    aud.append(("sfx", "whoosh_short", t87 - 0.05, 0.3))
    for k in range(0, 87, 4):
        aud.append(("sfx", "pop_hi" if k % 8 else "pop", t87 + 0.02 + k * 0.016, 0.14))
    # --- pink hamburger
    shots.append(clip_shot(t87_end, vC(35.9), S2, 6658.5, zoom=(1.15, 1.35), cy=(0.4, 0.35)))
    # --- "So, somebody's lying." two polaroids on navy
    tL = vC(35.9); tL_end = vC(38.05)
    pa = polaroid(frame_fill(grab(S5, 2982.2), 1.6, 0.766, 0.83, 400), "THE SIGN: 538", 720)
    pb = polaroid(frame_fill(grab(S2, CROWD_T), 1.0), "THE LINE: 46,853", 720)
    q = marker_text("?", 300)
    def two(tl, tg):
        im = navy_bg().convert("RGBA")
        paste_scaled(im, pa, 500, lerp(620, 540, ease_out(tl / 0.3)), rot=-4)
        paste_scaled(im, pb, 1420, lerp(620, 540, ease_out((tl - 0.12) / 0.3)), rot=3.5, alpha=clamp((tl - 0.12) / 0.1))
        tq = tl - (vC(37.18) - tL)
        if tq > 0: paste_scaled(im, q, W / 2, 520, scale=pop_in(tq, 0.2))
        return im.convert("RGB")
    shots.append(fn_shot(tL, tL_end, two))
    aud.append(("sfx", "swish", tL - 0.03, 0.3)); aud.append(("sfx", "swish", tL + 0.1, 0.2)); aud.append(("sfx", "hit", vC(37.18), 0.4))
    # --- counting fish one by one
    tD = vC(38.05); tD_end = vC(45.6)
    crowd = pillar(grab(S2, CROWD_T)); n = len(HEADS)
    times = [0.25 + 5.6 * (i / n) ** 0.62 for i in range(n)]
    cards = {}
    def counting(tl, tg):
        im = crowd.copy().convert("RGBA"); cnt = 0
        for i, (x, y) in enumerate(HEADS):
            if tl >= times[i]:
                cnt += 1; dot(im, 240 + x * 2.25, y * 2.25, 11, pop_in(tl - times[i], 0.15))
        ep_tag(im, f"FISH COUNTED: {cnt}")
        return im.convert("RGB")
    shots.append(fn_shot(tD, tD_end, counting))
    aud.append(("sfx", "shutter", tD, 0.45))
    for i in range(n):
        if i < 20 or i % 2 == 0: aud.append(("sfx", "tick", tD + times[i], 0.2))
    # --- "I got an answer. It's not the one on the sign."
    tS = vC(45.6); tS_end = vC(49.0)
    shots.append(still_shot(tS, vC(47.3), S5, 2982.2, zoom=(1.3, 1.4), cx=(0.66, 0.7), cy=(0.83, 0.83), ymax=400))
    shots.append(still_shot(vC(47.3), tS_end, S5, 2982.2, zoom=(1.7, 1.75), cx=(0.766, 0.766), cy=(0.83, 0.83), ymax=400))
    tX = vC(47.42)
    ovs.append({"t0": tX, "t1": tS_end, "draw": lambda img, tl, tg: red_x(img, 960, 770, 300, clamp(tl / 0.35), width=30)})
    aud.append(("sfx", "scribble", tX, 0.3)); aud.append(("sfx", "whoosh_short", tS - 0.05, 0.25))
    # --- "darker..." island drains to B&W
    tK = vC(49.0); tK_end = vC(C_src[1]) + 0.25
    shots.append(still_shot(tK, tK_end, S2, 6775.5, zoom=(1.0, 1.5), cx=(0.5, 0.47), cy=(0.6, 0.62), gray=(0.0, 1.0), ease=lambda x: x))
    aud.append(("sfx", "ocean_rumble", tK, 0.5)); aud.append(("sfx", "heartbeat", tK + 2.6, 0.45))
    # --- title card
    tT = tK_end
    title = text_layer("HOW MANY PEOPLE\nACTUALLY LIVE IN\nBIKINI BOTTOM?", font("anton", 140), stroke=0, shadow=8, spacing=16)
    def titlecard(tl, tg):
        im = navy_bg().convert("RGBA")
        if tl > 0.35:
            paste_scaled(im, title, W / 2, H / 2 + 30, scale=lerp(1.0, 1.04, clamp((tl - 0.35) / 3)), alpha=clamp((tl - 0.35) / 0.25))
            chapter_pill(im, "THE BIKINI BOTTOM CENSUS", clamp((tl - 0.6) / 0.35))
        return im.convert("RGB")
    shots.append(fn_shot(tT, tT + 3.2, titlecard))
    aud.append(("sfx", "boom", tT, 0.8))
    return shots, ovs, aud, tT + 3.2

def mix_events(mx, aud):
    for ev in aud:
        kind = ev[0]
        if kind == "vo":
            _, path, at, start, dur, g = ev; mx.add(load_audio(path, start, dur), at, g, 0.005, 0.02)
        elif kind == "clip":
            _, path, at, start, dur, g = ev; mx.add(load_audio(path, start, dur), at, g, 0.03, 0.08)
        elif kind == "sfx":
            _, name, at, g = ev; mx.sfx(name, at, g)

if __name__ == "__main__":
    shots, ovs, aud, end = build_coldopen(0.0)
    mx = Mixer(end + 1); mix_events(mx, aud)
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCR, "renders", "coldopen_test.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    render(shots, ovs, mx, out, end)
