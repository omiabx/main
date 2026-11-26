import sys, subprocess, json, numpy as np, soundfile as sf
sys.path.insert(0, '/tmp/claude-0/-home-user-main/097e55d9-3f75-5e8f-88d6-04e1d361aa0f/scratchpad/tools')
from sinistory import *
from PIL import Image, ImageDraw

E = ROOT + 'edit/'
OUT = E + 'out/'; os.makedirs(OUT, exist_ok=True)
C1 = E + 'vo/C1.mp3'
C1OFF = 8.40            # output time = C1 time + 8.40 for the continuous VO tail (C1 19.70 -> 58.04)

# ------------------------------------------------------------------ scenes
scenes = []   # (start, end, fn(t_rel, n) -> PIL RGB)
def add(s, e, fn): scenes.append((s, e, fn))

def clip_scene(name, ss, dur, z0=1.0, z1=1.0, yoff=0.5, cx=.5, cy=.5, extra=None):
    fr = clip_frames(name, ss, dur, yoff)
    def f(t, n):
        im = fr[min(int(t * FPS), len(fr) - 1)]
        im = zoom(im, z0 + (z1 - z0) * ease(t / dur), cx, cy)
        if extra: im = extra(im, t)
        return im
    return f

def still_scene(name, t0, dur, z0, z1, yoff=0.5, cx=.5, cy=.5):
    fr = clip_frames(name, t0, 0.05, yoff)[0]
    return lambda t, n: zoom(fr, z0 + (z1 - z0) * ease(t / dur), cx, cy)

# S1 0.00-2.70 polaroid open, then dive into the photo
pol1 = polaroid(still43('S2_D1.mp4', 6312.5), 'PATTY HYPE (2001)', photo_w=1060, rot=-2)
def s1(t, n):
    bg = background('navy', n).convert('RGBA')
    if t < 2.2: sc = 1.0 + .05 * ease(t / 2.2)
    else: sc = 1.05 + (2.05 - 1.05) * ease((t - 2.2) / .5) ** 1.6
    paste_center(bg, pol1, W / 2, H / 2 + 20 + 90 * ease((t - 2.2) / .5), sc)
    return bg.convert('RGB')
add(0.00, 2.70, s1)
add(2.70, 4.30, clip_scene('S2_D1.mp4', 6312.4, 1.60, 1.0, 1.03))
add(4.30, 6.30, clip_scene('S2_D1.mp4', 6299.2, 2.00, 1.0, 1.04))
add(6.30, 9.30, clip_scene('S2_D1.mp4', 6309.9, 3.00, 1.0, 1.06, yoff=.2, cy=.4))
add(9.30, 12.50, clip_scene('S2_D1.mp4', 6314.6, 3.20, 1.0, 1.04, cx=.35))
add(12.50, 15.75, clip_scene('S2_D1.mp4', 6319.25, 3.25, 1.0, 1.05, yoff=.25))          # CLIP V01 (audio)
add(15.75, 18.20, still_scene('S2_D1.mp4', 6323.0, 2.45, 1.0, 1.10, cx=.55, cy=.45))
add(18.20, 20.60, still_scene('S2_D1.mp4', 6326.2, 2.40, 1.12, 1.0))
add(20.60, 23.15, still_scene('S2_D1.mp4', 6327.0, 2.55, 1.25, 1.35, cx=.5, cy=.4))
add(23.15, 28.10, clip_scene('S2_D1.mp4', 6323.30, 4.95, 1.0, 1.04))                      # CLIP V02 (audio)

def circle_extra(im, t):
    im = im.copy(); d = ImageDraw.Draw(im); hand_circle(d, 905, 728, 150, 205, ease((t - .55) / .45), width=10); return im
add(28.10, 31.30, clip_scene('S2_D1.mp4', 6307.0, 3.20, 1.0, 1.03, extra=circle_extra))

def tally(t, n):
    im = notebook(n); d = ImageDraw.Draw(im)
    f = font('anton', 84); s = '"MR. KRABS, I HAVE AN IDEA."'; tw = d.textlength(s, font=f); d.text(((W - tw) / 2, 230), s, font=f, fill=INK)
    f2 = font('type', 40); s2 = 'SAID BEFORE THE PRAYER'; tw = d.textlength(s2, font=f2); d.text(((W - tw) / 2, 372), s2, font=f2, fill=(90, 90, 90))
    for i, t0 in enumerate([.35, .85, 1.35]):
        p = ease_out((t - t0) / .12)
        if p > 0:
            x = 760 + i * 200; d.line([(x - 6, 560), (x - 6 + 12 * p, 560 + 300 * p)], fill=RED, width=22)
    return im
add(31.30, 33.85, tally)
add(33.85, 36.76, still_scene('S2_D1.mp4', 6329.0, 2.91, 1.0, 1.12, cx=.6, cy=.35))

# S11 transcripts 36.76-47.90
def page_img():
    p = Image.new('RGBA', (470, 620), (238, 233, 220, 255)); d = ImageDraw.Draw(p); r = np.random.default_rng(5)
    for y in range(70, 590, 34): d.line([(50, y), (50 + int(r.uniform(220, 370)), y)], fill=(120, 120, 120, 255), width=7)
    d.text((50, 22), 'TRANSCRIPT', font=font('type', 26), fill=(60, 60, 60, 255))
    sh = Image.new('RGBA', (p.width + 60, p.height + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([36, 40, 36 + p.width, 40 + p.height], fill=(0, 0, 0, 130))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(p, (30, 30)); return sh
PAGE = page_img(); ROTS = [-11, -6, -2, 3, 7, 12]
PAGES = [PAGE.rotate(r, resample=Image.BICUBIC, expand=True) for r in ROTS]
WORDS = [('heaven', 9.12), ('pray', 9.85), ('soul', 10.45)]
def transcripts(t, n):
    bg = background('navy', n).convert('RGBA')
    for i, pg in enumerate(PAGES):
        p = ease_out((t - i * .08) / .45)
        paste_center(bg, pg, 560 + (i - 2.5) * 34, 560 + (1 - p) * 700 - i * 6)
    d = ImageDraw.Draw(bg)
    f = font('type', 44); d.text((1060, 300), 'SPONGEBOB WIKI', font=f, fill=CREAM); d.text((1060, 356), 'TRANSCRIPTS', font=f, fill=CREAM)
    c = int(1172 * ease((t - 4.84) / 1.4))
    if t > 4.84: d.text((1050, 410), f'{c:,}', font=font('anton', 230), fill=CREAM)
    if t > 8.95:
        a = ease((t - 8.95) / .15); d.rounded_rectangle([1060, 760, 1790, 860], 14, fill=(240, 235, 222, int(255 * a)))
        d.text((1090, 787), 'SEARCH:', font=font('type', 40), fill=(120, 120, 120))
        cur = ''
        for w, t0 in WORDS:
            if t >= t0: cur = w[:max(0, min(len(w), int((t - t0) / .055) + 1))]
        d.text((1290, 780), cur + ('|' if int(t * 4) % 2 == 0 else ''), font=font('type', 50), fill=INK)
    return bg.convert('RGB')
add(36.76, 47.90, transcripts)

# S12 polaroid board 47.90-59.09
PB = [(polaroid(still43('S1_D3.mp4', 3713.1), "NEPTUNE'S SPATULA (2000)", 500, -4), 590, 290, .10),
      (polaroid(still43('S3_D2.mp4', 9648.4, w=1000), 'BORN AGAIN KRABS (2002)', 500, 3), 1340, 285, 4.05),
      (polaroid(still43('S3_D2.mp4', 9716.7, w=1000), "DAVY JONES' LOCKER", 500, 2.5), 610, 795, 6.35),
      (polaroid(still43('S2_D1.mp4', 9844.0), 'CHRISTMAS WHO? (2000)', 500, -3), 1350, 790, 8.35)]
def board(t, n):
    bg = background('navy', n).convert('RGBA')
    for el, x, y, t0 in PB:
        if t >= t0:
            p = (t - t0) / .22; paste_center(bg, el, x, y, 1.25 - .25 * back_out(p), min(1, p * 2))
    return zoom(bg.convert('RGB'), 1.0 + .035 * ease(t / 11.19))
add(47.90, 59.09, board)

TAG = paper_tag('CHURCH', 150)
def church(t, n):
    bg = background('navy', n).convert('RGBA'); p = ease_out((t - .1) / .13)
    if t > .1: paste_center(bg, TAG.rotate(-2.5, resample=Image.BICUBIC, expand=True), W / 2, H / 2, 1.5 - .5 * p, min(1, p * 1.5))
    return bg.convert('RGB')
add(59.09, 62.06, church)
add(62.06, 66.44, clip_scene('S3_D1.mp4', 1657.0, 4.38, 1.0, 1.10, cx=.4))

def title(t, n):
    im = background('paper', n); d = ImageDraw.Draw(im); f = font('anton', 160)
    for s, y in [('IS BIKINI BOTTOM', 300), ('SECRETLY RELIGIOUS?', 500)]:
        tw = d.textlength(s, font=f); d.text(((W - tw) / 2, y), s, font=f, fill=INK)
    tw = d.textlength('SECRETLY RELIGIOUS?', font=f); wobbly_line(d, (W - tw) / 2 - 10, (W + tw) / 2 + 10, 742, ease((t - .3) / .4), 12)
    return zoom(im, 1.0 + .02 * ease(t / 3.6))
add(66.44, 70.20, title)
TOTAL = 70.20

LABELS = [(2.78, 6.25, label_img('PATTY HYPE · 2001'))]

# ------------------------------------------------------------------ video
def render_video(path):
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for n in range(int(TOTAL * FPS)):
        t = n / FPS
        s, e, fn = next(x for x in scenes if x[0] <= t < x[1]) if any(x[0] <= t < x[1] for x in scenes) else scenes[-1]
        im = fn(t - s, n)
        for a, b, lab in LABELS:
            if a <= t < b:
                al = min(1, (t - a) / .2, (b - t) / .2); im = im.convert('RGBA'); paste_center(im, lab, 52 + lab.width / 2, 1000, 1.0, al); im = im.convert('RGB')
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()

# ------------------------------------------------------------------ audio
def render_audio(path):
    mix = np.zeros((int((TOTAL + 1) * SR), 2), np.float32)
    def put(x, at, db=0.0):
        i = int(at * SR); x = x * 10 ** (db / 20); mix[i:i + len(x)] += x[:len(mix) - i]
    vo = gain_to(load_audio(C1), -16.0)
    seg = lambda a, b: fade(vo[int(a * SR):int(b * SR)].copy())
    put(seg(0.0, 12.40), 0.00); put(seg(12.40, 19.70), 15.75); put(seg(19.70, len(vo) / SR), 28.10)
    put(fade(gain_to(load_audio(SRC + 'S2_D1.mp4', 6319.25, 3.25), -16.5), .02, .06), 12.50)
    put(fade(gain_to(load_audio(SRC + 'S2_D1.mp4', 6323.30, 4.95), -16.5), .02, .10), 23.15)
    sfx = {k: load_audio(E + f'sfx/{k}.wav') for k in ['whoosh', 'pop', 'type', 'shutter', 'stamp']}
    put(sfx['whoosh'], 2.12, -6); put(sfx['whoosh'], 36.62, -7); put(sfx['whoosh'], 66.30, -6); put(sfx['whoosh'], 47.80, -10)
    for t0 in [.35, .85, 1.35]: put(sfx['pop'], 31.30 + t0, -6)
    put(sfx['pop'], 28.10 + .55, -10)
    for k in range(14): put(sfx['type'], 36.76 + 4.84 + k * .1, -14)
    for w, t0 in WORDS:
        for k in range(len(w)): put(sfx['type'], 36.76 + t0 + k * .055, -12)
    for _, _, _, t0 in PB: put(sfx['shutter'], 47.90 + t0, -6)
    put(sfx['stamp'], 59.09 + .1, -4)
    sf.write(path, mix, SR, subtype='FLOAT')

if __name__ == '__main__':
    render_audio(OUT + 'opening_mix.wav'); print('audio ok', flush=True)
    render_video(OUT + 'opening_video.mp4'); print('video ok', flush=True)
