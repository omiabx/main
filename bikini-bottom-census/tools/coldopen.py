"""Cold open (style test): chunk 1 voiceover + clips + graphics + SFX."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from graphics import *
from data import *

def pillar(src):
    """4:3 frame centered on 16:9 with blurred, darkened sides."""
    bg = src.resize((W, int(W * 3 / 4)), Image.BICUBIC).crop((0, (int(W * 3 / 4) - H) // 2, W, (int(W * 3 / 4) - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(25)).point(lambda v: int(v * 0.45))
    fg = src.resize((1440, 1080), Image.BICUBIC).filter(ImageFilter.UnsharpMask(2.2, 70, 2))
    bg.paste(fg, (240, 0)); return bg

def build_coldopen(T0=0.0):
    """Returns (shots, overlays, audio_events, end_time). T0 = start offset on the master timeline."""
    shots, ovs, aud = [], [], []
    V = VO["1"]
    # --- VO segmentation (chunk 1) ---
    A_end = 15.75                    # "...crosses out the eight."
    INS = 4.3                        # inserted show moment ("Minus one.")
    B_src = (16.90, 20.78)           # "537. He updated the census on his way out of town,"  (drops "with a marker")
    C_src = (21.90, WORDS["1"]["dur"])
    tB = T0 + A_end + INS
    tC = tB + (B_src[1] - B_src[0]) + 0.15
    off = tC - C_src[0]              # map chunk-1 time v -> master time for segment C
    end = T0 + (C_src[1] - C_src[0]) + (tC - T0) + 0.4
    aud += [("vo", V, T0, 0.0, A_end, 1.0), ("vo", V, tB, B_src[0], B_src[1] - B_src[0], 1.0),
            ("vo", V, tC, C_src[0], C_src[1] - C_src[0], 1.0)]
    vA = lambda v: T0 + v
    vC = lambda v: v + off

    # ambience bed under the opening
    aud.append(("sfx", "wind", T0, 0.18))
    # 0. sign wide, push in
    shots.append(clip_shot(vA(0), vA(3.3), S5, 2978.2, speed=0.55, zoom=(1.05, 1.35), cx=(0.55, 0.62), cy=(0.4, 0.35), ymax=CAP))
    # 1. "Population? 538." close-up of sign
    shots.append(still_shot(vA(3.3), vA(6.2), S5, 2982.2, zoom=(1.3, 1.6), cx=(0.62, 0.766), cy=(0.83, 0.83), ymax=400))
    aud.append(("sfx", "whoosh_short", vA(3.2), 0.35))
    t538 = vA(4.88)
    aud.append(("sfx", "stamp", t538, 0.55))
    def circ(img, tl, tg):
        d = ImageDraw.Draw(img); p = clamp(tl / 0.45)
        marker_circle(d, (600, 560, 1320, 960), progress=p, width=16, seed=4)
    ovs.append({"t0": t538, "t1": vA(6.2), "draw": circ})
    aud.append(("sfx", "scribble", t538 + 0.02, 0.25))
    # 2. "decides the town doesn't need him" -> crying SpongeBob
    shots.append(clip_shot(vA(6.2), vA(10.5), S5, 2921.5, zoom=(1.1, 1.3), cy=(0.45, 0.4), ymax=CAP))
    aud.append(("sfx", "whoosh_down", vA(6.1), 0.3))
    # 3. packs a bag
    shots.append(clip_shot(vA(10.5), vA(11.6), S5, 2955.6, zoom=(1.15, 1.2), ymax=CAP))
    # 4. walks out
    shots.append(clip_shot(vA(11.6), vA(12.6), S5, 2960.4, zoom=(1.1, 1.15), ymax=CAP))
    # 5. stops at this sign
    shots.append(clip_shot(vA(12.6), vA(14.2), S5, 2979.6, zoom=(1.05, 1.2), cy=(0.4, 0.4), ymax=CAP))
    # 6. "crosses out the eight" -> 538 close (hand approaching)
    shots.append(still_shot(vA(14.2), vA(A_end), S5, 2983.6, zoom=(1.0, 1.12), ymax=CAP))
    # 7. INSERT the actual moment with show audio
    tI = vA(A_end)
    shots.append(clip_shot(tI, tI + INS, S5, 2983.9, zoom=(1.0, 1.08), ymax=CAP))
    aud.append(("clip", S5, tI, 2983.9, INS, 1.0))
    aud.append(("sfx", "scribble", tI + 1.6, 0.35))
    # 8. freeze on 537 + shutter + "-1"
    shots.append(still_shot(tB, tB + 1.45, S5, 2988.0, zoom=(1.05, 1.35), cx=(0.5, 0.55), ymax=CAP, ease=ease_out))
    aud.append(("sfx", "shutter", tB, 0.6))
    def minus1(img, tl, tg):
        paste_scaled(img, label("-1", 220, RED, stroke=14), 1560, 300, scale=pop_in(tl, 0.22), rot=-10)
    ovs.append({"t0": tB + 0.1, "t1": tB + 1.45, "draw": minus1}); aud.append(("sfx", "pop", tB + 0.1, 0.5))
    # 9. census form (typed), runs into segment C ("Which would be totally fine")
    tF = tB + 1.45; tF_end = vC(23.82)
    bg_form = grab(S5, 2978.5)
    lines = [("POPULATION:", "537", "538"), ("UPDATED BY:", "S. SQUAREPANTS", None),
             ("METHOD:", "CHALK, ON HIS WAY OUT", None)]
    def form_frame(tl, tg):
        b = frame_fill(bg_form, 1.2, 0.6, 0.4, CAP).filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.5))
        typed = clamp(tl / 2.2); st = clamp((tl - 2.5) / 0.5)
        f = census_form(lines, stamp="OFFICIAL", stamp_p=st, typed_p=typed)
        im = b.convert("RGBA"); sc = lerp(0.9, 0.95, tl / max(0.1, tF_end - tF))
        y = lerp(H + 450, H / 2, ease_out(tl / 0.35))
        paste_scaled(im, f, W / 2, y, scale=sc * 1.22, rot=1.5)
        return im.convert("RGB")
    shots.append(fn_shot(tF, tF_end, form_frame))
    aud.append(("sfx", "whoosh", tF - 0.05, 0.4))
    for k in range(18):
        aud.append(("sfx", "typekey", tF + 0.3 + k * 0.11 + (0.03 if k % 3 == 0 else 0), 0.35))
    aud.append(("sfx", "stamp", tF + 2.5, 0.7))
    # 10. "except" -> record scratch, then "seven years earlier" card
    tEx = vC(23.82)
    aud.append(("sfx", "scratch", tEx - 0.05, 0.5))
    bgc, tc = time_card("SEVEN YEARS\nEARLIER...", grab(S2, 6450.0))
    def card(tl, tg):
        im = bgc.copy(); paste_scaled(im, tc, W / 2, H / 2, scale=lerp(0.95, 1.05, tl / 1.7) * pop_in(tl, 0.3)); return im.convert("RGB")
    shots.append(fn_shot(tEx, vC(25.42), card))
    aud.append(("sfx", "whoosh", tEx + 0.05, 0.45))
    # 11. 46,853 counter over the Patty Hype crowd
    t46 = vC(25.42); t46_end = vC(30.82)
    shots.append(clip_shot(t46, t46_end, S2, 6766.6, speed=0.82, zoom=(1.0, 1.25), cy=(0.5, 0.45)))
    aud.append(("clip", S2, t46, 6766.6, (t46_end - t46) * 0.82, 0.25))
    def counter(img, tl, tg):
        p = ease_out(clamp(tl / 2.4)); n = int(round(46853 * p))
        s = f"{n:,}"
        sc = 1.0 + (0.12 * max(0, 1 - (tl - 2.4) / 0.25) if tl > 2.4 else 0)
        paste_scaled(img, big_number(s, 210, YEL if tl > 2.4 else WHITE), W / 2, 800, scale=sc)
        paste_scaled(img, label("PEOPLE IN ONE LINE", 64), W / 2, 960, alpha=clamp(tl / 0.3))
    ovs.append({"t0": t46 + 0.05, "t1": t46_end, "draw": counter})
    aud.append(("sfx", "counter", t46 + 0.05, 0.45)); aud.append(("sfx", "counter", t46 + 0.85, 0.3))
    aud.append(("sfx", "ding", t46 + 2.45, 0.45))
    # 12. 87 Bikini Bottoms grid
    t87 = vC(30.82); t87_end = vC(34.55)
    icon = sign_icon(1.0)
    cols, rows = 13, 7; gx, gy = 142, 128; ox = W / 2 - (cols - 1) * gx / 2; oy = 120
    gbg = frame_fill(grab(S5, 2975.0), 1.0, sharpen=False, ymax=CAP).filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.5))
    rng = np.random.default_rng(5); jit = [(rng.uniform(-14, 14), rng.uniform(-10, 10), rng.uniform(-8, 8)) for _ in range(87)]
    order = list(range(87))
    def grid(tl, tg):
        im = gbg.copy().convert("RGBA")
        for i in order:
            ti = 0.02 + i * 0.016
            if tl < ti: continue
            r, c = divmod(i, cols)
            paste_scaled(im, icon, ox + c * gx + jit[i][0], oy + r * gy + jit[i][1], scale=0.92 * pop_in(tl - ti, 0.18), rot=jit[i][2])
        cnt = min(87, int(clamp((tl - 0.02) / (86 * 0.016)) * 87) + (1 if tl > 0.02 else 0))
        paste_scaled(im, label(f"{cnt} BIKINI BOTTOMS", 96, YEL), W / 2, 1010, scale=1.0)
        return im.convert("RGB")
    shots.append(fn_shot(t87, t87_end, grid))
    aud.append(("sfx", "whoosh_short", t87 - 0.05, 0.35))
    for k in range(0, 87, 4):
        aud.append(("sfx", "pop_hi" if k % 8 else "pop", t87 + 0.02 + k * 0.016, 0.16))
    # 13. "pink hamburger" -> patties pile
    shots.append(clip_shot(t87_end, vC(35.9), S2, 6658.5, zoom=(1.05, 1.25), cy=(0.4, 0.35)))
    # 14. "So, somebody's lying." split screen
    tL = vC(35.9); tL_end = vC(38.05)
    left = grab(S5, 2982.2); right = grab(S2, CROWD_T)
    def split(tl, tg):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        b = frame_fill(right, 1.0).crop((W // 4, 0, W // 4 + W // 2 - 6, H))
        a = frame_fill(left, 1.6, 0.766, 0.83, 400).crop((W // 4, 0, W // 4 + W // 2 - 6, H))
        im.paste(a, (0, 0)); im.paste(b, (W // 2 + 6, 0)); im = im.convert("RGBA")
        paste_scaled(im, label("538", 150, WHITE), W / 4, 300, scale=pop_in(tl, 0.2))
        paste_scaled(im, label("46,853", 150, WHITE), 3 * W / 4, 300, scale=pop_in(tl - 0.15, 0.2))
        tq = tl - (vC(37.18) - tL)
        if tq > 0:
            paste_scaled(im, label("?", 420, RED, stroke=18), W / 2, H / 2 - 40, scale=pop_in(tq, 0.2))
        return im.convert("RGB")
    shots.append(fn_shot(tL, tL_end, split))
    aud.append(("sfx", "swish", tL - 0.03, 0.35)); aud.append(("sfx", "hit", vC(37.18), 0.5))
    # 15. counting fish one by one (preview of chapter 5)
    tD = vC(38.05); tD_end = vC(45.6)
    crowd = pillar(grab(S2, CROWD_T))
    n = len(HEADS)
    times = [0.25 + 5.6 * (i / n) ** 0.62 for i in range(n)]   # starts slow, speeds up
    def counting(tl, tg):
        k = ease_in_out(clamp(tl / (tD_end - tD)))
        im = crowd.copy().convert("RGBA")
        cnt = 0
        for i, (x, y) in enumerate(HEADS):
            if tl >= times[i]:
                cnt += 1; dot(im, 240 + x * 2.25, y * 2.25, 12, pop_in(tl - times[i], 0.15))
        paste_scaled(im, label(f"FISH COUNTED: {cnt}", 70, YEL), W / 2, 1020)
        return im.convert("RGB")
    shots.append(fn_shot(tD, tD_end, counting))
    aud.append(("sfx", "shutter", tD, 0.5))
    for i in range(n):
        if i < 20 or i % 2 == 0:
            aud.append(("sfx", "tick", tD + times[i], 0.22))
    # 16. "I got an answer. It's not the one on the sign." -> 538 + red X
    tS = vC(45.6); tS_end = vC(49.0)
    shots.append(still_shot(tS, tS_end, S5, 2982.2, zoom=(1.6, 1.7), cx=(0.766, 0.766), cy=(0.83, 0.83), ymax=400))
    tX = vC(47.42)
    ovs.append({"t0": tX, "t1": tS_end, "draw": lambda img, tl, tg: red_x(img, 960, 770, 300, clamp(tl / 0.35), width=34)})
    aud.append(("sfx", "scribble", tX, 0.35)); aud.append(("sfx", "whoosh_short", tS - 0.05, 0.3))
    # 17. "darker..." -> island at sunset, drains to grey, slow push
    tK = vC(49.0); tK_end = vC(C_src[1]) + 0.25
    shots.append(still_shot(tK, tK_end, S2, 6775.5, zoom=(1.0, 1.5), cx=(0.5, 0.47), cy=(0.6, 0.62), gray=(0.0, 1.0), ease=lambda x: x))
    aud.append(("sfx", "ocean_rumble", tK, 0.55)); aud.append(("sfx", "heartbeat", tK + 2.6, 0.5))
    # 18. hard cut to black + boom + title
    tT = tK_end
    title = text_layer("HOW MANY PEOPLE\nACTUALLY LIVE IN\nBIKINI BOTTOM?", font("anton", 150), stroke=0, shadow=0, spacing=18)
    def titlecard(tl, tg):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        if tl > 0.35:
            paste_scaled(im, title, W / 2, H / 2, scale=lerp(1.0, 1.04, clamp((tl - 0.35) / 3)), alpha=clamp((tl - 0.35) / 0.25))
        return im.convert("RGB")
    shots.append(fn_shot(tT, tT + 3.2, titlecard))
    aud.append(("sfx", "boom", tT, 0.85))
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
