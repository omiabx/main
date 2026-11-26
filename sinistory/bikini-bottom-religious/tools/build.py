"""Builds Parts 1-5 of 'Is Bikini Bottom Secretly Religious?' from a declarative shot list.
usage: build.py PART   (PART in 1..5) -> out/partN_video.mp4, out/partN_mix.wav, out/partN_timeline.json"""
import sys, json, re, numpy as np, soundfile as sf, subprocess
sys.path.insert(0, '/tmp/claude-0/-home-user-main/097e55d9-3f75-5e8f-88d6-04e1d361aa0f/scratchpad/tools')
from sinistory import *
from PIL import Image, ImageDraw, ImageFilter

E = ROOT + 'edit/'; OUT = E + 'out/'; GAP = 0.12

# ---------------------------------------------------------------- graphics
def chapter_card(n, title):
    f = font('anton', 150)
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    size = 150
    while d0.textlength(title, font=font('anton', size)) > 1700: size -= 6
    f = font('anton', size); tw = d0.textlength(title, font=f); part = f'PART {n}'
    def fn(t, k, dur):
        im = background('paper', k); d = ImageDraw.Draw(im)
        ft = font('type', 62); shown = part[:max(0, min(len(part), int(t / .06)))]
        pw = d.textlength(part, font=ft); d.text(((W - pw) / 2, 300), shown, font=ft, fill=(70, 70, 70))
        d.text(((W - tw) / 2, 480), title, font=f, fill=INK)
        wobbly_line(d, (W - tw) / 2 - 8, (W + tw) / 2 + 8, 480 + size * 1.22, ease((t - .45) / .45), 11, seed=n)
        return zoom(im, 1 + .02 * ease(t / dur))
    sfx = [(0.0, 'whoosh', -7)] + [(i * .06, 'type', -14) for i in range(len(part)) if part[i] != ' ']
    return fn, sfx

def tags_scene(tags, marks=(), push=.03):
    """tags: (text, t0, x, y, rot, size, q); marks: ('arrow'|'check', t0, x0, y0, x1, y1)"""
    imgs = [(paper_tag(tx, sz, q).rotate(r, resample=Image.BICUBIC, expand=True), t0, x, y) for tx, t0, x, y, r, sz, q in tags]
    def fn(t, k, dur):
        bg = background('navy', k).convert('RGBA')
        for im, t0, x, y in imgs:
            if t >= t0: p = ease_out((t - t0) / .13); paste_center(bg, im, x, y, 1.4 - .4 * p, min(1, p * 1.5))
        d = ImageDraw.Draw(bg)
        for kind, t0, x0, y0, x1, y1 in marks:
            p = ease((t - t0) / .3)
            if p <= 0: continue
            if kind == 'arrow':
                xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p; d.line([(x0, y0), (xe, ye)], fill=RED, width=12)
                if p >= 1: d.polygon([(x1, y1), (x1 - 40, y1 - 26), (x1 - 40, y1 + 26)], fill=RED)
            else:
                pts = [(x0, y0), (x0 + 40, y0 + 45), (x0 + 120, y0 - 70)]
                seg = pts[:2] if p < .4 else pts
                if p < .4: seg = [pts[0], (pts[0][0] + 40 * p / .4, pts[0][1] + 45 * p / .4)]
                else: q = (p - .4) / .6; seg = [pts[0], pts[1], (pts[1][0] + 80 * q, pts[1][1] - 115 * q)]
                d.line(seg, fill=RED, width=20, joint='curve')
        return zoom(bg.convert('RGB'), 1 + push * ease(t / dur))
    sfx = [(t0, 'stamp', -6) for _, t0, *_ in tags] + [(m[1], 'pop' if m[0] == 'arrow' else 'ding', -8 if m[0] == 'arrow' else -12) for m in marks]
    return fn, sfx

def counter_scene(value, lines, t0=.2, run=1.0, fmt='{:,}'):
    def fn(t, k, dur):
        bg = background('navy', k); d = ImageDraw.Draw(bg); fl = font('type', 46)
        for i, l in enumerate(lines):
            lw = d.textlength(l, font=fl); d.text(((W - lw) / 2, 250 + i * 62), l, font=fl, fill=CREAM)
        if t >= t0:
            v = fmt.format(int(round(value * ease((t - t0) / run)))); f = font('anton', 300); vw = d.textlength(v, font=f)
            d.text(((W - vw) / 2, 430), v, font=f, fill=CREAM)
        return zoom(bg, 1 + .03 * ease(t / dur))
    sfx = [(t0 + i * .08, 'type', -15) for i in range(int(run / .08))]
    return fn, sfx

def search_scene(queries):
    """queries: (word, t0, [(result_line, t_rel_after_typing)])"""
    def fn(t, k, dur):
        bg = background('navy', k).convert('RGBA'); d = ImageDraw.Draw(bg)
        d.text((260, 170), 'SEARCH THE TRANSCRIPTS', font=font('type', 42), fill=CREAM)
        d.rounded_rectangle([250, 240, 1670, 350], 14, fill=(240, 235, 222, 255))
        cur, res = '', []
        for w, t0, results in queries:
            if t >= t0:
                cur = w[:max(0, min(len(w), int((t - t0) / .07) + 1))]; te = t0 + len(w) * .07
                res = [(r, te + tr) for r, tr in results]
        d.text((290, 262), cur + ('|' if int(t * 4) % 2 == 0 else ''), font=font('type', 60), fill=INK)
        for i, (r, tr) in enumerate(res):
            if t >= tr:
                a = int(255 * ease((t - tr) / .15)); y = 420 + i * 118
                d.rounded_rectangle([250, y, 1670, y + 96], 10, fill=(240, 235, 222, a))
                big = r.startswith('0 ')
                d.text((290, y + 20), r, font=font('anton' if big else 'type', 56 if big else 44), fill=(RED if big else INK) + (a,))
        return bg.convert('RGB')
    sfx = []
    for w, t0, results in queries:
        sfx += [(t0 + i * .07, 'type', -12) for i in range(len(w))]
        te = t0 + len(w) * .07; sfx += [(te + tr, 'pop', -9) for _, tr in results]
    return fn, sfx

def definition_scene(word, sub):
    def fn(t, k, dur):
        im = background('paper', k); d = ImageDraw.Draw(im); f = font('anton', 190)
        ww = d.textlength(word, font=f); d.text(((W - ww) / 2, 290), word, font=f, fill=INK)
        wobbly_line(d, (W - ww) / 2, (W + ww) / 2, 540, ease((t - .3) / .4), 12, seed=9)
        fs = font('type', 52); shown = sub[:max(0, min(len(sub), int((t - .7) / .04)))]
        sw = d.textlength(sub, font=fs); d.text(((W - sw) / 2, 600), shown, font=fs, fill=(70, 70, 70))
        return zoom(im, 1 + .025 * ease(t / dur))
    sfx = [(0, 'whoosh', -9)] + [(.7 + i * .04, 'type', -15) for i in range(0, len(sub), 2)]
    return fn, sfx

# ---------------------------------------------------------------- shot specs
def C(src, ss, **o): return ('c', src, ss, o)       # muted footage
def St(src, t, **o): return ('s', src, t, o)        # still with push
def G(g): return ('g', g)                           # graphic (fn, sfx)

def shot_fn(spec, dur):
    if spec[0] == 'g':
        fn, _ = spec[1]; return lambda t, k: fn(t, k, dur)
    kind, src, ss, o = spec
    z0, z1, yoff, cx, cy = o.get('z0', 1.0), o.get('z1', 1.05), o.get('yoff', .5), o.get('cx', .5), o.get('cy', .5)
    cache = {}
    circ = o.get('circle')
    def f(t, k):
        if 'fr' not in cache: cache['fr'] = clip_frames(src + '.mp4', ss, dur if kind == 'c' else .05, yoff)
        fr = cache['fr']
        im = fr[min(int(t * FPS), len(fr) - 1)] if kind == 'c' else fr[0]
        im = zoom(im, z0 + (z1 - z0) * ease(t / dur), cx, cy)
        if circ:
            im = im.copy(); hand_circle(ImageDraw.Draw(im), *circ, ease((t - .4) / .45), width=10)
        return im
    f.cache = cache
    return f

# ---------------------------------------------------------------- parts
P = {}
P[1] = [('card', 1, 'THE GOD UPSTAIRS'),
 ('vo', 'C2', 0.0, 8.90, [(4.5, C('S1_D3', 3466.0, label="NEPTUNE'S SPATULA · 2000")), (None, C('S1_D3', 3706.0, z0=1.0, z1=1.08))]),
 ('vo', 'C2', 8.90, 19.10, [(2.6, C('S1_D3', 3404.2)), (2.5, C('S1_D3', 3411.0)), (2.4, C('S1_D3', 3430.0)), (None, C('S1_D3', 3443.0))]),
 ('vo', 'C2', 19.10, 26.10, [(2.6, C('S1_D3', 3450.2)), (2.2, C('S1_D3', 3466.8)), (None, C('S1_D3', 3477.0, z1=1.1))]),
 ('clip', 'S1_D3', 3482.85, 3494.70, {}),
 ('vo', 'C2', 26.10, 40.20, [(2.8, C('S1_D3', 3945.0)), (3.0, C('S1_D3', 3699.2)), (2.8, C('S1_D3', 3708.0)), (None, C('S1_D3', 3714.6, z1=1.0, z0=1.0))]),
 ('clip', 'S1_D3', 3722.30, 3736.20, {}),
 ('vo', 'C2', 40.20, 52.90, [(3.0, St('S1_D3', 3727.3, z1=1.1)), (2.6, C('S1_D3', 3945.6)), (2.6, C('S1_D3', 3994.3)), (None, C('S1_D3', 4002.4, z1=1.1))]),
 ('clip', 'S1_D3', 4012.90, 4019.40, {}),
 ('vo', 'C2', 52.90, 67.15, [(3.6, C('MOVIE_03', 34.0, label='THE SPONGEBOB SQUAREPANTS MOVIE · 2004')), (3.6, C('MOVIE_03', 38.5)), (3.5, C('MOVIE_03', 42.4)), (None, C('MOVIE_03', 46.0))]),
 ('clip', 'MOVIE_03', 49.50, 56.05, {}),
 ('vo', 'C2', 67.15, 71.00, [(None, C('MOVIE_04', 24.6))]),
 ('clip', 'MOVIE_04', 28.40, 32.95, {}),
 ('vo', 'C2', 71.00, 87.40, [(3.2, C('S06E47', 425.0, label='THE CLASH OF TRITON · 2010')), (3.4, C('S06E47', 434.5)), (3.5, C('S06E47', 438.8)), (3.2, C('S06E47', 442.8)), (None, C('S06E47', 446.0))]),
 ('clip', 'S06E47', 450.90, 460.40, {}),
 ('vo', 'C2', 87.40, 101.20, [(2.8, C('S06E47', 499.5)), (2.6, C('S06E47', 510.0)), (3.4, C('S06E47', 525.8)), (2.4, C('S06E47', 530.4)), (None, St('S1_D3', 3713.1, z0=1.0, z1=1.12, cy=.35))]),
]
P[2] = [('card', 2, 'THE FAITHFUL'),
 ('vo', 'C3', 0.0, 5.25, [(None, G(tags_scene([('THANK GOD', .25, 470, 520, -3, 120, False), ('THANK NEPTUNE', 2.3, 1400, 560, 2.5, 120, False)], [('arrow', 1.3, 800, 535, 1050, 548)])))]),
 ('vo', 'C3', 5.25, 12.20, [(None, G(counter_scene(47, ['"THANK NEPTUNE"', 'ACROSS THE TRANSCRIPTS'], t0=3.6, run=1.4)))]),
 ('clip', 'S01E38', 231.80, 235.45, {'label': 'MERMAID MAN AND BARNACLE BOY II · 2000'}),
 ('clip', 'S3_D1', 6217.70, 6224.15, {'label': 'DOING TIME · 2002'}),
 ('vo', 'C3', 12.20, 25.30, [(2.6, C('S3_D1', 6225.0)), (2.4, C('S01E38', 236.0)), (3.0, C('S15E07', 1095.5, label='STUDENT DRIVER SURVIVOR · 2024')), (None, C('S15E07', 1100.0))]),
 ('clip', 'S15E07', 1104.90, 1109.45, {}),
 ('vo', 'C3', 25.30, 36.45, [(3.6, C('S2_D1', 6319.3, label='PATTY HYPE · 2001', yoff=.25)), (3.0, St('S2_D1', 6324.4, z0=1.0, z1=1.1)), (None, C('S2_D1', 6326.4))]),
 ('clip', 'S2_D1', 6328.20, 6331.95, {}),
 ('vo', 'C3', 36.45, 44.90, [(None, G(tags_scene([('IN THE NAME OF NEPTUNE', .35, 960, 380, -2, 100, False), ('IN THE NAME OF MONEY', 2.3, 960, 700, 1.5, 100, False)], [('check', 6.1, 1530, 700, 0, 0)])))]),
]
P[3] = [('card', 3, 'THE AFTERLIFE'),
 ('vo', 'C4', 0.0, 9.40, [(3.8, C('S3_D2', 9642.0)), (None, C('S3_D2', 9565.0, label='BORN AGAIN KRABS · 2002'))]),
 ('vo', 'C4', 9.40, 16.15, [(None, G(definition_scene('"BORN AGAIN"', 'A PHRASE FROM EVANGELICAL CHRISTIANITY')))]),
 ('vo', 'C4', 16.15, 36.70, [(2.8, C('S3_D2', 9567.0)), (2.4, C('S3_D2', 9600.5)), (2.6, C('S3_D2', 9617.0)), (2.6, C('S3_D2', 9628.0)), (2.4, C('S3_D2', 9634.5)), (2.6, C('S3_D2', 9641.5)), (None, St('S3_D2', 10019.0, z0=1.0, z1=1.12, cx=.65, cy=.6))]),
 ('clip', 'S3_D2', 9646.20, 9650.90, {}),
 ('vo', 'C4', 36.70, 44.80, [(4.6, C('S3_D2', 9651.4)), (None, C('S3_D2', 9672.5))]),
 ('clip', 'S3_D2', 9679.10, 9689.20, {}),
 ('vo', 'C4', 44.80, 49.20, [(None, C('S3_D2', 9689.0))]),
 ('clip', 'S3_D2', 9694.20, 9699.45, {}),
 ('vo', 'C4', 49.20, 74.20, [(4.9, G(tags_scene([('THE SIN: BEING CHEAP', .3, 960, 540, -2, 120, False)]))), (3.2, C('S3_D2', 9708.8)), (3.4, C('S3_D2', 9713.0)), (3.4, C('S3_D2', 9717.0)), (3.0, C('S3_D2', 9722.6)), (2.9, C('S3_D2', 9730.5)), (None, C('S3_D2', 9742.2))]),
 ('vo', 'C4', 74.20, 104.50, [(2.4, C('S3_D2', 9864.5)), (2.4, C('S3_D2', 9879.5)), (2.8, C('S3_D2', 9901.7)), (2.6, C('S3_D2', 9906.5)), (2.6, C('S3_D2', 9913.5)), (3.4, C('S3_D2', 9967.2)), (2.6, C('S3_D2', 9975.0)), (2.6, C('S3_D2', 9981.0)), (2.8, C('S3_D2', 10014.0)), (2.6, C('S3_D2', 10024.0)), (None, C('S3_D2', 10033.5))]),
 ('clip', 'S3_D2', 10042.70, 10050.85, {}),
 ('vo', 'C4', 104.50, 113.70, [(2.2, St('S3_D2', 10048.2, z0=1.0, z1=1.15)), (3.6, C('S3_D2', 10055.2)), (None, C('S3_D2', 10099.0))]),
 ('vo', 'C4', 113.70, 127.55, [(3.6, C('S3_D1', 2899.5, label='JUST ONE BITE · 2001')), (3.4, C('S3_D1', 2903.2)), (3.4, C('S3_D1', 2906.5)), (None, C('S3_D1', 2909.6))]),
 ('clip', 'S3_D1', 2912.30, 2917.45, {}),
 ('vo', 'C4', 127.55, 138.20, [(4.6, St('S3_D1', 2916.0, z0=1.0, z1=1.1)), (3.0, St('S3_D1', 2917.7, z0=1.05, z1=1.15, cy=.35)), (None, C('S3_D1', 2918.4))]),
]
P[4] = [('card', 4, 'HOLIDAYS WITHOUT A CHURCH'),
 ('vo', 'C5', 0.0, 12.40, [(2.8, C('S2_D1', 9843.0, label='CHRISTMAS WHO? · 2000')), (2.2, St('S2_D1', 9844.0, z0=1.15, z1=1.25, cy=.35)), (3.6, C('S2_D1', 9757.0)), (None, C('S2_D1', 9764.0))]),
 ('clip', 'S2_D1', 9771.70, 9775.45, {}),
 ('vo', 'C5', 12.40, 21.80, [(3.0, C('S2_D1', 9839.0)), (3.0, C('S2_D1', 9846.5)), (None, C('S2_D1', 9852.5))]),
 ('clip', 'S2_D1', 9863.30, 9869.55, {}),
 ('vo', 'C5', 21.80, 48.20, [(3.4, C('S2_D1', 9899.0)), (3.4, C('S2_D1', 9903.0)), (3.8, C('S2_D1', 9906.6)), (3.6, G(definition_scene('MISSIONARY', 'SOMEONE SENT FAR AWAY TO SPREAD A FAITH'))), (3.0, C('S2_D1', 9876.0)), (2.8, C('S2_D1', 9884.0)), (3.0, C('S2_D1', 9910.8)), (None, C('S2_D1', 9931.5))]),
 ('clip', 'S2_D1', 9936.70, 9942.85, {}),
 ('vo', 'C5', 48.20, 51.10, [(None, G(search_scene([('manger', .25, [('0 RESULTS IN CHRISTMAS WHO?', .4)])])))]),
 ('vo', 'C5', 51.10, 77.40, [(3.6, C('S06E08', 59.0, label='GONE · 2008')), (3.0, C('S06E08', 94.0)), (3.2, C('S06E08', 199.0)), (3.0, C('S06E08', 245.0)), (3.4, C('S06E08', 252.5)), (3.4, C('S06E08', 427.0)), (3.4, C('S06E08', 565.5)), (None, C('S06E08', 574.0))]),
 ('clip', 'S06E08', 612.40, 623.10, {}),
 ('vo', 'C5', 77.40, 87.50, [(3.2, St('S06E08', 617.2, z0=1.0, z1=1.1)), (3.6, C('S06E08', 620.0)), (None, St('S06E08', 624.2, z0=1.0, z1=1.06))]),
 ('clip', 'S06E08', 624.80, 628.80, {}),
]
P[5] = [('card', 5, 'THE ONLY CHURCH IN BIKINI BOTTOM'),
 ('vo', 'C6', 0.0, 20.0, [(None, G(search_scene([('church', 2.3, [('MID-LIFE CRUSTACEAN · BELL SOUND EFFECT', .4), ('SQUIDWARD THE UNFRIENDLY GHOST · BELL SOUND EFFECT', 1.0), ('PAT-A-THON · "TAKE IT AWAY, CHURCH CURTAINS!"', 7.4)]), ('amen', 15.7, [('0 EPISODES', .45)])])))]),
 ('vo', 'C6', 20.0, 45.00, [(3.2, C('S3_D1', 1489.0, label='CLUB SPONGEBOB · 2002')), (3.0, C('S3_D1', 1497.0)), (3.4, C('S3_D1', 1504.0)), (2.8, C('S3_D1', 1537.5)), (2.8, C('S3_D1', 1546.0)), (2.4, C('S3_D1', 1572.0)), (3.2, C('S3_D1', 1614.0)), (None, C('S3_D1', 1634.5))]),
 ('clip', 'S3_D1', 1641.00, 1644.80, {}),
 ('vo', 'C6', 45.00, 61.55, [(2.4, C('S3_D1', 1650.5)), (2.4, C('S3_D1', 1657.6)), (2.6, C('S3_D1', 1663.0)), (2.4, C('S3_D1', 1676.0)), (2.4, C('S3_D1', 1712.0)), (2.4, C('S3_D1', 1744.0)), (None, C('S3_D1', 1758.0))]),
 ('clip', 'S3_D1', 1793.55, 1802.60, {}),
 ('vo', 'C6', 61.55, 70.85, [(2.8, C('S3_D1', 1814.0)), (3.0, C('S3_D1', 1817.0)), (None, C('S3_D1', 1820.0))]),
 ('clip', 'S3_D1', 1804.40, 1809.10, {}),
 ('clip', 'S3_D1', 1823.00, 1825.90, {}),
 ('vo', 'C6', 70.85, 76.10, [(2.6, C('S3_D1', 1880.0)), (None, C('S3_D1', 1892.5))]),
 ('clip', 'S3_D1', 1907.30, 1919.05, {}),
 ('clip', 'S3_D1', 1919.30, 1921.40, {}),
 ('vo', 'C6', 76.10, 92.00, [(2.8, C('S3_D1', 1928.0)), (2.4, C('S3_D1', 1937.0)), (2.4, C('S3_D1', 1944.0)), (2.6, C('S3_D1', 1949.0)), (2.6, C('S3_D1', 1956.0)), (None, C('S3_D1', 1962.5))]),
 ('vo', 'C6', 92.00, 97.45, [(2.6, C('S3_D1', 2009.0)), (None, C('S3_D1', 2016.0))]),
 ('clip', 'S3_D1', 2034.40, 2037.00, {}),
 ('vo', 'C6', 97.45, 113.40, [(2.6, C('S3_D1', 2037.0)), (3.0, C('S3_D1', 2040.6)), (3.2, C('S3_D1', 2043.6)), (3.0, C('S3_D1', 2050.4)), (None, C('S3_D1', 2052.8))]),
 ('clip', 'S3_D1', 2055.90, 2060.70, {'end_black': 1.2}),
]

# ---------------------------------------------------------------- build
_SIL = {}
def snap(ch, x):
    if x <= 0.01: return x
    if ch not in _SIL:
        o = subprocess.run(['ffmpeg', '-nostdin', '-i', E + f'vo/{ch}.mp3', '-af', 'silencedetect=n=-38dB:d=0.08', '-f', 'null', '-'], capture_output=True, text=True).stderr
        st = [float(v) for v in re.findall(r'silence_start: ([0-9.]+)', o)]; en = [float(v) for v in re.findall(r'silence_end: ([0-9.]+)', o)]
        _SIL[ch] = [(a + b) / 2 for a, b in zip(st, en)]
    c = min(_SIL[ch], key=lambda m: abs(m - x), default=x)
    return c if abs(c - x) < 0.7 else x

def build(n):
    items = P[n]; scenes, labels, events, t = [], [], [], 0.0
    vo_cache = {}
    for it in items:
        if it[0] == 'card':
            fn, sfx = chapter_card(it[1], it[2]); d = 2.6
            scenes.append((t, t + d, (lambda fn, d: lambda tt, k: fn(tt, k, d))(fn, d)))
            events += [(t + a, 'sfx', s, db) for a, s, db in sfx]; t += d + GAP
        elif it[0] == 'vo':
            _, ch, a, b, shots = it
            a, b = snap(ch, a), snap(ch, b)
            if ch not in vo_cache: vo_cache[ch] = gain_to(load_audio(E + f'vo/{ch}.mp3'), -16.0)
            vo = vo_cache[ch]; b = min(b, len(vo) / SR); d = b - a
            events.append((t, 'audio', fade(vo[int(a * SR):int(b * SR)].copy()), 0))
            rem, tt = d, t
            for i, (sd, spec) in enumerate(shots):
                sd = rem if (sd is None or i == len(shots) - 1) else min(sd, rem)
                scenes.append((tt, tt + sd, shot_fn(spec, sd)))
                if spec[0] != 'g' and spec[3].get('label'): labels.append((tt + .08, tt + min(3.6, d), spec[3]['label']))
                if spec[0] == 'g': events += [(tt + a2, 'sfx', s, db) for a2, s, db in spec[1][1]]
                tt += sd; rem -= sd
            t += d + GAP
        elif it[0] == 'clip':
            _, src, a, b, o = it; d = b - a
            def mk(src=src, a=a, d=d, yoff=o.get('yoff', .5)):
                cache = {}
                def f(tt, k):
                    if 'fr' not in cache: cache['fr'] = clip_frames(src + '.mp4', a, d, yoff)
                    fr = cache['fr']; return zoom(fr[min(int(tt * FPS), len(fr) - 1)], 1 + .03 * ease(tt / d))
                f.cache = cache; return f
            scenes.append((t, t + d, mk()))
            au = fade(gain_to(load_audio(SRC + src + '.mp4', a, d), -16.5), .02, .08)
            events.append((t, 'audio', au, 0))
            if o.get('label'): labels.append((t + .05, t + min(3.4, d), o['label']))
            t += d
            if o.get('end_black'):
                bl = o['end_black']; scenes.append((t, t + bl, lambda tt, k: Image.new('RGB', (W, H), (0, 0, 0)))); t += bl
            else: t += GAP
    total = t
    # video
    vpath = OUT + f'part{n}_video.mp4'
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', vpath], stdin=subprocess.PIPE)
    LBL = {txt: label_img(txt) for _, _, txt in labels}
    nf = int(round(total * FPS)); si = 0
    for k in range(nf):
        tt = k / FPS
        while si < len(scenes) - 1 and tt >= scenes[si][1]:
            if si >= 1: getattr(scenes[si - 1][2], 'cache', {}).clear()
            si += 1
        s0, s1, fn = scenes[si]
        if tt < s0:  # inside a GAP: hold previous scene's last frame
            s0, s1, fn = scenes[max(0, si - 1)]; im = fn(s1 - s0 - 1e-3, k)
        else: im = fn(tt - s0, k)
        for a, b, txt in labels:
            if a <= tt < b:
                al = min(1, (tt - a) / .2, (b - tt) / .2); im = im.convert('RGBA'); lab = LBL[txt]; paste_center(im, lab, 52 + lab.width / 2, 1000, 1.0, al); im = im.convert('RGB')
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    # audio
    mix = np.zeros((int((total + 1) * SR), 2), np.float32)
    SFX = {}
    for at, kind, x, db in events:
        if kind == 'sfx':
            if x not in SFX: SFX[x] = load_audio(E + f'sfx/{x}.wav')
            x = SFX[x]
        i = int(at * SR); x = x * 10 ** (db / 20); mix[i:i + len(x)] += x[:len(mix) - i]
    mix = mix[:int(total * SR)]
    sf.write(OUT + f'part{n}_mix.wav', mix, SR, subtype='FLOAT')
    json.dump({'total': total}, open(OUT + f'part{n}_timeline.json', 'w'))
    print(f'part {n}: {total:.2f}s', flush=True)

if __name__ == '__main__':
    for n in map(int, sys.argv[1:]): build(n)
