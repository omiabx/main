"""Edit engine: VO alignment, timeline, frame compositor, audio mix, chunked encode."""
import json, os, re, subprocess, math, difflib, functools
import numpy as np
import cv2
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import resample_poly
from num2words import num2words

ROOT = '/home/user/media'
FPS = 30
W, H = 1920, 1080
SR = 48000
FONTS = ROOT + '/fonts/'
MARGIN = 1.16          # decode oversize for zoom headroom

SOURCES = {            # display aspect of each source
    'src/s1d1.mp4': 4 / 3, 'src/s1d3.mp4': 4 / 3, 'src/s3d2.mp4': 4 / 3, 'src/s9d1.mp4': 4 / 3,
    'src/mmbegins.mp4': 4 / 3, 'src/bttp.mp4': 4 / 3,
    'arch/mchale_credits.mp4': 4 / 3, 'arch/batman_trailer.mp4': 16 / 9,
}


# ----------------------------------------------------------------------------- text / words
def norm_tokens(text):
    text = text.replace('’', "'").replace('—', ' ').replace('-', ' ')
    out = []
    for w in text.split():
        w = re.sub(r"[^A-Za-z0-9']", '', w).lower()
        if not w:
            continue
        if re.fullmatch(r'\d+(st|nd|rd|th)?', w):
            n = int(re.sub(r'\D', '', w))
            ws = num2words(n, to='year') if 1900 <= n <= 2099 else num2words(n)
            out += [x for x in re.sub(r'[^a-z ]', ' ', ws.replace('-', ' ')).split()]
            continue
        out.append(w.strip("'"))
    return out


def script_blocks(path='/home/user/main/mermaid-man-video/SCRIPT.md'):
    s = open(path).read()
    blocks, cur = {}, None
    for line in s.splitlines():
        m = re.match(r'\*\*VO (\d+)\*\*', line)
        if m:
            cur = '%02d' % int(m.group(1)); blocks[cur] = []; continue
        if line.startswith('> ') and cur:
            blocks[cur].append(line[2:])
        elif line.startswith('`[') or line.startswith('###'):
            cur = None
    return {k: ' '.join(v) for k, v in blocks.items()}


PARTS = [('1', ['01', '02', '03', '04', '05', '06', '07', '08']),
         ('2', ['09', '10', '11', '12']),
         ('3', ['13', '14', '15', '16', '17', '18']),
         ('4', ['19', '20', '21', '22'])]


def transcribe_words(path, cache):
    if os.path.exists(cache):
        return json.load(open(cache))
    from faster_whisper import WhisperModel
    m = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=4)
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(a, beam_size=5, word_timestamps=True)
    words = [(w.start, w.end, w.word.strip()) for s in segs for w in s.words]
    json.dump(words, open(cache, 'w'))
    return words


def align_vo(vo_dir, cache_dir):
    """returns {block: {'part','t0','t1','tok':[...], 'times':[(s,e)...]}}"""
    blocks = script_blocks()
    out = {}
    for part, ids in PARTS:
        cand = [f for f in os.listdir(vo_dir) if re.match(rf'(?i)part_?{part}\.(mp3|wav|m4a)$', f)]
        path = os.path.join(vo_dir, cand[0])
        words = transcribe_words(path, os.path.join(cache_dir, f'part{part}_words.json'))
        wt = []
        for s, e, w in words:
            for t in norm_tokens(w):
                wt.append((t, s, e))
        st, owner = [], []
        for b in ids:
            for t in norm_tokens(blocks[b]):
                st.append(t); owner.append(b)
        sm = difflib.SequenceMatcher(None, st, [x[0] for x in wt], autojunk=False)
        times = [None] * len(st)
        for a, b2, n in sm.get_matching_blocks():
            for k in range(n):
                times[a + k] = (wt[b2 + k][1], wt[b2 + k][2])
        # interpolate gaps
        known = [i for i, t in enumerate(times) if t]
        for i in range(len(times)):
            if times[i] is None:
                prev = max([k for k in known if k < i], default=None)
                nxt = min([k for k in known if k > i], default=None)
                if prev is None:
                    times[i] = (times[nxt][0] - 0.3, times[nxt][0] - 0.05)
                elif nxt is None:
                    times[i] = (times[prev][1] + 0.05, times[prev][1] + 0.3)
                else:
                    f = (i - prev) / (nxt - prev)
                    t = times[prev][1] + f * (times[nxt][0] - times[prev][1])
                    times[i] = (t, t + 0.05)
        dur = sf.info(path).duration
        for b in ids:
            idx = [i for i, o in enumerate(owner) if o == b]
            out[b] = {'part': part, 'path': path, 'tok': [st[i] for i in idx], 'times': [times[i] for i in idx],
                      't0': times[idx[0]][0], 't1': times[idx[-1]][1], 'dur': dur}
        match = sum(1 for t in times if t) / len(times)
        print(f'part {part}: {len(words)} words transcribed, script aligned')
    # cut points: snap to real silence in the waveform (protects against extra / improvised speech between blocks)
    for part, ids in PARTS:
        path = out[ids[0]]['path']
        pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
        x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
        hop = 160
        fr = x[:len(x) // hop * hop].reshape(-1, hop)
        db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-7)
        quiet = db < -50

        def runs(a, b):
            i0, i1 = max(0, int(a * 100)), min(len(quiet), int(b * 100))
            rr, st = [], None
            for i in range(i0, i1):
                if quiet[i] and st is None:
                    st = i
                if (not quiet[i] or i == i1 - 1) and st is not None:
                    if i - st >= 4:
                        rr.append((st / 100, i / 100))
                    st = None
            return rr

        for i, b in enumerate(ids):
            o = out[b]
            prev_end = out[ids[i - 1]]['t1'] if i > 0 else 0.0
            next_start = out[ids[i + 1]]['t0'] if i + 1 < len(ids) else o['dur']
            o['a0'] = max(prev_end + (o['t0'] - prev_end) * 0.5, o['t0'] - 0.25)
            o['a1'] = min(o['t1'] + (next_start - o['t1']) * 0.5, o['t1'] + 0.35)
            r = runs(o['t1'] - 0.25, o['t1'] + 0.7)
            if r:
                s0, s1 = r[0]
                o['a1'] = s0 + min((s1 - s0) * 0.6, 0.25)
            r = runs(o['t0'] - 0.7, o['t0'] + 0.15)
            if r:
                s0, s1 = r[-1]
                o['a0'] = s1 - min((s1 - s0) * 0.5, 0.15)
    return out


# ----------------------------------------------------------------------------- fonts / text layers
@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def text_rgba(txt, fname='Anton-Regular.ttf', size=120, fill=(255, 255, 255), stroke=10,
              stroke_fill=(0, 0, 0), shadow=True, track=0, line_gap=1.08, align='center'):
    f = font(fname, size)
    lines = txt.split('\n')
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * line_gap)
    widths = []
    for ln in lines:
        w = 0
        for ch in ln:
            bb = f.getbbox(ch)
            w += (bb[2] if ch != ' ' else size * 0.28) + track
        widths.append(int(w))
    tw = max(widths) + stroke * 4 + 40
    th = lh * len(lines) + stroke * 4 + 40
    L = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    for i, ln in enumerate(lines):
        x = (tw - widths[i]) / 2 if align == 'center' else stroke * 2 + 20
        y = stroke * 2 + 20 + i * lh
        for ch in ln:
            d.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            x += (f.getbbox(ch)[2] if ch != ' ' else size * 0.28) + track
    bb = L.getbbox()
    L = L.crop(bb) if bb else L
    if shadow:
        sh = Image.new('RGBA', (L.width + 24, L.height + 24), (0, 0, 0, 0))
        sh.paste(Image.new('RGBA', L.size, (0, 0, 0, 200)), (10, 12), L.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        sh.alpha_composite(L, (0, 0))
        L = sh
    return np.asarray(L).astype(np.float32) / 255.0


def load_rgba(path, max_w=None, max_h=None):
    im = Image.open(path).convert('RGBA')
    if max_w or max_h:
        s = min((max_w or 1e9) / im.width, (max_h or 1e9) / im.height)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def sticker_rgba(img_path, mask_path=None, height=700, outline=12):
    im = Image.open(img_path).convert('RGBA')
    if mask_path:
        im.putalpha(Image.open(mask_path).convert('L').point(lambda v: 255 if v > 110 else 0))
    im = im.crop(im.getbbox())
    s = height / im.height
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    pad = outline * 3
    c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    c.paste(im, (pad, pad), im)
    a = c.split()[3]
    ring = a.filter(ImageFilter.MaxFilter(outline * 2 + 1)).filter(ImageFilter.GaussianBlur(1))
    shadow = a.filter(ImageFilter.MaxFilter(outline * 2 + 1)).filter(ImageFilter.GaussianBlur(16))
    out = Image.new('RGBA', c.size, (0, 0, 0, 0))
    out.paste(Image.new('RGBA', c.size, (0, 0, 0, 255)), (8, 12), shadow.point(lambda v: int(v * 0.7)))
    out.paste(Image.new('RGBA', c.size, (255, 255, 255, 255)), (0, 0), ring)
    out.alpha_composite(c)
    return np.asarray(out).astype(np.float32) / 255.0


def blend(frame, layer, x, y, alpha=1.0):
    """frame float32 HxWx3 in 0..1, layer float32 hxwx4; x,y top-left (can be off-screen)"""
    h, w = layer.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    L = layer[y0 - y:y1 - y, x0 - x:x1 - x]
    a = L[..., 3:4] * alpha
    frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - a) + L[..., :3] * a


def scaled(layer, s):
    if abs(s - 1) < 1e-3:
        return layer
    h, w = layer.shape[:2]
    return cv2.resize(layer, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_LINEAR)


def ease_out_back(x, k=1.70158):
    x = min(max(x, 0), 1) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


# ----------------------------------------------------------------------------- base shots
def card_dark(f, t, d, k):
    f[:] = 0.035
    f += grain_tex(int(t * FPS)) * 0.015


class Shot:
    """kind: 'video' | 'image' | 'card'"""

    def __init__(self, kind, **kw):
        self.kind = kind
        self.kw = kw
        self.start = self.end = None

    def __repr__(self):
        return f'Shot({self.kind},{self.start:.2f}-{self.end:.2f},{self.kw.get("src") or self.kw.get("path") or ""})'


def V(src, t, z0=1.0, z1=1.07, y=0.42, x=0.5, grade=None, speed=1.0, freeze=False, rewind=False, snap=True):
    return Shot('video', src=src, t=t, z0=z0, z1=z1, y=y, x=x, grade=grade, speed=speed, freeze=freeze, rewind=rewind, snap=snap)


def I(path, c0=(0.5, 0.5, 1.0), c1=(0.5, 0.5, 1.12), grade=None, bg='blur'):
    """c = (cx, cy, zoom) zoom 1 => image fills screen (cover)"""
    return Shot('image', path=path, c0=c0, c1=c1, grade=grade, bg=bg)


def CARD(fn, **kw):
    return Shot('card', fn=fn, **kw)


class VideoReader:
    def __init__(self, src, t, n_frames, speed=1.0, freeze=False):
        ar = SOURCES.get(src, 4 / 3)
        self.dw = int(W * MARGIN) // 2 * 2
        self.dh = int(self.dw / ar) // 2 * 2
        if self.dh < H * MARGIN:
            self.dh = int(H * MARGIN) // 2 * 2
            self.dw = int(self.dh * ar) // 2 * 2
        self.freeze = freeze
        vf = f'fps={FPS},scale={self.dw}:{self.dh}:flags=lanczos,unsharp=5:5:0.55:5:5:0.0'
        if speed != 1.0:
            vf = f'setpts=PTS/{speed},' + vf
        n = 1 if freeze else n_frames + 2
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{max(0, t):.3f}', '-i', ROOT + '/' + src,
                                   '-vf', vf, '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8)
        self.last = None
        self.sz = self.dw * self.dh * 3

    def read(self):
        if self.freeze and self.last is not None:
            return self.last
        buf = self.p.stdout.read(self.sz)
        if len(buf) == self.sz:
            self.last = np.frombuffer(buf, np.uint8).reshape(self.dh, self.dw, 3)
        elif self.last is None:
            self.last = np.zeros((self.dh, self.dw, 3), np.uint8)
        return self.last

    def close(self):
        try:
            self.p.stdout.close(); self.p.kill()
        except Exception:
            pass


@functools.lru_cache(8)
def image_cache(path):
    im = Image.open(ROOT + '/' + path).convert('RGB')
    return np.asarray(im)


def frame_from_image(path, cx, cy, z, bg='blur'):
    img = image_cache(path)
    ih, iw = img.shape[:2]
    cover = max(W / iw, H / ih)
    contain = min(W / iw, H / ih)
    if bg == 'contain':
        s = contain * z
    else:
        s = cover * z
    # window in image coords
    ww, wh = W / s, H / s
    x0 = cx * iw - ww / 2
    y0 = cy * ih - wh / 2
    M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(14, 14, 18))
    if bg == 'contain':
        small = cv2.resize(img, (W // 8, H // 8))
        blurred = cv2.GaussianBlur(cv2.resize(small, (W, H)), (0, 0), 25) * 0.35
        mask = cv2.warpAffine(np.ones((ih, iw), np.float32), M, (W, H))[..., None]
        out = out * mask + blurred * (1 - mask)
    return out.astype(np.float32) / 255.0


# ----------------------------------------------------------------------------- grading
_grain = None


def grain_tex(i):
    global _grain
    if _grain is None:
        r = np.random.default_rng(3)
        _grain = [cv2.GaussianBlur(r.standard_normal((H // 2, W // 2)).astype(np.float32), (0, 0), 0.8) for _ in range(8)]
    g = _grain[i % 8]
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]


_vig = None


def vignette():
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.66)) ** 2)
        _vig = np.clip(1.25 - d * 0.75, 0.25, 1).astype(np.float32)[..., None]
    return _vig


def apply_grade(f, grade, fi, t_local=0.0):
    if not grade:
        return f
    g = dict(grade) if isinstance(grade, dict) else {'look': grade}
    look = g.get('look')
    if look in ('bw', 'archive'):
        y = (f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114)[..., None]
        f = np.repeat(y, 3, 2)
        if look == 'archive':
            f = f * np.array([1.04, 1.0, 0.9], np.float32)  # warm paper
            f = (f - 0.5) * 1.12 + 0.5
            f = f + grain_tex(fi) * 0.045
            f = f * (0.96 + 0.04 * math.sin(fi * 2.3) * math.sin(fi * 0.7))
            f = f * vignette()
    elif look == 'desat':
        amt = g.get('amt', 0.6)
        y = (f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114)[..., None]
        f = f * (1 - amt) + y * amt
        f = f * (0.85 + 0.15 * vignette())
    elif look == 'dark':
        f = f * 0.45 * vignette()
    elif look == 'fade_desat':      # desaturate progressively
        dur = g.get('dur', 4.0)
        amt = min(1, t_local / dur) * g.get('amt', 0.85)
        y = (f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114)[..., None]
        f = f * (1 - amt) + y * amt
        f = f * (1 - 0.35 * amt + 0.35 * amt * vignette())
    return np.clip(f, 0, 1)


# ----------------------------------------------------------------------------- overlays
class Ov:
    def __init__(self, fn, start=None, end=None, **kw):
        self.fn, self.start, self.end, self.kw = fn, start, end, kw
        self.cache = {}


def ov_text(frame, t, d, o):
    """pop-in text. kw: txt, x, y (center, 0..1), size, color, font, stroke, angle, anim('pop'|'slide'|'type'|'fade')"""
    k = o.kw
    key = 'L'
    if key not in o.cache:
        L = text_rgba(k['txt'], k.get('font', 'Anton-Regular.ttf'), k.get('size', 120), tuple(k.get('color', (255, 255, 255))),
                      k.get('stroke', 10), shadow=k.get('shadow', True), track=k.get('track', 2))
        if k.get('angle'):
            im = Image.fromarray((L * 255).astype(np.uint8)).rotate(k['angle'], expand=True, resample=Image.BICUBIC)
            L = np.asarray(im).astype(np.float32) / 255
        if k.get('box'):
            pad = 26
            bx = np.zeros((L.shape[0] + pad * 2, L.shape[1] + pad * 2, 4), np.float32)
            bx[..., :3] = np.array(k['box'], np.float32) / 255; bx[..., 3] = k.get('box_alpha', 0.85)
            a = L[..., 3:4]
            bx[pad:-pad, pad:-pad, :3] = bx[pad:-pad, pad:-pad, :3] * (1 - a) + L[..., :3] * a
            L = bx
        o.cache[key] = L
    L = o.cache[key]
    anim = k.get('anim', 'pop')
    alpha = 1.0
    s = 1.0
    dx = dy = 0
    if anim == 'pop':
        s = 0.55 + 0.45 * ease_out_back(t / 0.22, 2.2)
        alpha = min(1, t / 0.08)
    elif anim == 'slide':
        dx = (1 - ease_out(t / 0.3)) * k.get('slide_from', -400)
        alpha = min(1, t / 0.12)
    elif anim == 'fade':
        alpha = min(1, t / 0.35)
    elif anim == 'punch':
        s = 1.6 - 0.6 * ease_out(t / 0.12)
        alpha = min(1, t / 0.05)
    out_t = d - t
    if k.get('out', True) and out_t < 0.18:
        alpha *= max(0, out_t / 0.18)
        if anim == 'pop':
            s *= 0.9 + 0.1 * out_t / 0.18
    if k.get('drift', True):
        s *= 1 + 0.03 * (t / max(d, 0.1))
    Ls = scaled(L, s)
    cx, cy = k.get('x', 0.5) * W + dx, k.get('y', 0.5) * H + dy
    blend(frame, Ls, cx - Ls.shape[1] / 2, cy - Ls.shape[0] / 2, alpha)


def ov_label(frame, t, d, o):
    """lower-left episode label: kw txt, sub"""
    k = o.kw
    if 'L' not in o.cache:
        f1, f2 = font('Oswald.ttf', 46), font('Oswald.ttf', 30)
        w = int(max(f1.getlength(k['txt']), f2.getlength(k.get('sub', ''))) + 70)
        h = 128 if k.get('sub') else 84
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, w, h], fill=(12, 14, 20, 225))
        dr.rectangle([0, 0, 10, h], fill=(255, 205, 0, 255))
        dr.text((32, 12), k['txt'], font=f1, fill=(255, 255, 255))
        if k.get('sub'):
            dr.text((33, 72), k['sub'], font=f2, fill=(255, 205, 0))
        o.cache['L'] = np.asarray(im).astype(np.float32) / 255
    L = o.cache['L']
    p = ease_out(t / 0.35)
    q = 1 if d - t > 0.3 else ease_in_out((d - t) / 0.3)
    x = 70 - (1 - p) * (L.shape[1] + 80) - (1 - q) * (L.shape[1] + 80)
    blend(frame, L, x, H - 120 - L.shape[0] + (0 if k.get('top') is None else 0) if not k.get('top') else 80, 1.0)


def ov_sticker(frame, t, d, o):
    """kw: path, mask, height, x, y (center), from_ ('left','right','bottom', 'pop')"""
    k = o.kw
    if 'L' not in o.cache:
        o.cache['L'] = sticker_rgba(ROOT + '/' + k['path'], ROOT + '/' + k['mask'] if k.get('mask') else None,
                                    k.get('height', 700), k.get('outline', 12))
        if k.get('flip'):
            o.cache['L'] = o.cache['L'][:, ::-1].copy()
    L = o.cache['L']
    fr = k.get('from_', 'pop')
    cx, cy = k.get('x', 0.25) * W, k.get('y', 0.55) * H
    s = 1.0
    if fr == 'pop':
        s = 0.5 + 0.5 * ease_out_back(t / 0.25, 1.8)
    elif fr == 'left':
        cx -= (1 - ease_out(t / 0.35)) * (W * 0.7)
    elif fr == 'right':
        cx += (1 - ease_out(t / 0.35)) * (W * 0.7)
    elif fr == 'bottom':
        cy += (1 - ease_out(t / 0.35)) * H
    alpha = 1.0
    if d - t < 0.2:
        alpha = max(0, (d - t) / 0.2)
    s *= 1 + 0.025 * t / max(d, 0.1)
    s *= 1 + 0.012 * math.sin(t * 3.1)
    Ls = scaled(L, s)
    blend(frame, Ls, cx - Ls.shape[1] / 2, cy - Ls.shape[0] / 2, alpha)


def ov_image(frame, t, d, o):
    """floating framed photo: kw path, x, y, height, angle, border"""
    k = o.kw
    if 'L' not in o.cache:
        im = Image.open(ROOT + '/' + k['path']).convert('RGB')
        if k.get('crop'):
            c = k['crop']; im = im.crop((int(c[0] * im.width), int(c[1] * im.height), int(c[2] * im.width), int(c[3] * im.height)))
        if k.get('bw'):
            im = im.convert('L').convert('RGB')
        s = k.get('height', 600) / im.height
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        b = k.get('border', 16)
        fr = Image.new('RGBA', (im.width + 2 * b, im.height + 2 * b + k.get('caption_h', 0)), (245, 242, 232, 255))
        fr.paste(im, (b, b))
        if k.get('caption'):
            dr = ImageDraw.Draw(fr)
            f = font('SpecialElite-Regular.ttf', 30)
            dr.text((b + 4, im.height + b + 10), k['caption'], font=f, fill=(30, 30, 30))
        fr = fr.rotate(k.get('angle', 0), expand=True, resample=Image.BICUBIC)
        sh = Image.new('RGBA', (fr.width + 40, fr.height + 40), (0, 0, 0, 0))
        sh.paste(Image.new('RGBA', fr.size, (0, 0, 0, 170)), (24, 28), fr.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        sh.alpha_composite(fr, (0, 0))
        o.cache['L'] = np.asarray(sh).astype(np.float32) / 255
    L = o.cache['L']
    fr = k.get('from_', 'pop')
    cx, cy = k.get('x', 0.5) * W, k.get('y', 0.5) * H
    s = 1.0
    if fr == 'pop':
        s = 0.6 + 0.4 * ease_out_back(t / 0.28, 1.6)
    elif fr == 'drop':
        cy -= (1 - ease_out(t / 0.4)) * H
    elif fr == 'right':
        cx += (1 - ease_out(t / 0.4)) * W * 0.8
    elif fr == 'left':
        cx -= (1 - ease_out(t / 0.4)) * W * 0.8
    s *= 1 + 0.035 * t / max(d, 0.1)
    alpha = 1 if d - t > 0.2 else max(0, (d - t) / 0.2)
    Ls = scaled(L, s)
    blend(frame, Ls, cx - Ls.shape[1] / 2, cy - Ls.shape[0] / 2, alpha)


def ov_circle(frame, t, d, o):
    """hand-drawn red ellipse drawn on. kw cx, cy, rx, ry (pixels, screen), width"""
    k = o.kw
    p = ease_out(t / 0.45)
    if 'pts' not in o.cache:
        r = np.random.default_rng(int(k['cx'] + k['cy']))
        n = 120
        th = np.linspace(0, 2 * np.pi * 1.12, n) - 0.6
        wob = 1 + np.cumsum(r.normal(0, 0.006, n))
        ex = k['rx'] * wob * np.cos(th)
        ey = k['ry'] * wob * np.sin(th) + np.linspace(0, k['ry'] * 0.12, n)
        ang = math.radians(k.get('angle', 0))
        xs = k['cx'] + ex * math.cos(ang) - ey * math.sin(ang)
        ys = k['cy'] + ex * math.sin(ang) + ey * math.cos(ang)
        o.cache['pts'] = np.stack([xs, ys], 1)
    pts = o.cache['pts'][:max(2, int(len(o.cache['pts']) * p))]
    lay = np.zeros((H, W), np.uint8)
    cv2.polylines(lay, [pts.astype(np.int32)], False, 255, k.get('width', 9), cv2.LINE_AA)
    a = lay.astype(np.float32)[..., None] / 255
    alpha = 1 if d - t > 0.2 else max(0, (d - t) / 0.2)
    col = np.array(k.get('color', (235, 30, 40)), np.float32) / 255
    frame[:] = frame * (1 - a * alpha) + col * a * alpha


def ov_quote(frame, t, d, o):
    """quote card over darkened frame. kw txt, who"""
    k = o.kw
    if 'L' not in o.cache:
        f = font('SpecialElite-Regular.ttf', k.get('size', 74))
        words = k['txt'].split()
        lines, cur = [], ''
        for w in words:
            if f.getlength(cur + ' ' + w) > 1400:
                lines.append(cur); cur = w
            else:
                cur = (cur + ' ' + w).strip()
        lines.append(cur)
        lh = int(k.get('size', 74) * 1.35)
        im = Image.new('RGBA', (1560, lh * len(lines) + 150), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.text((0, -30), '“', font=font('Anton-Regular.ttf', 150), fill=(255, 205, 0))
        for i, ln in enumerate(lines):
            dr.text((80, 20 + i * lh), ln, font=f, fill=(245, 245, 240))
        dr.text((80, 40 + len(lines) * lh), '— ' + k['who'] if False else k['who'], font=font('Oswald.ttf', 38), fill=(255, 205, 0))
        o.cache['L'] = np.asarray(im).astype(np.float32) / 255
        o.cache['n'] = sum(len(l) for l in lines)
    L = o.cache['L']
    dim = min(1, t / 0.3) * (1 if d - t > 0.3 else max(0, (d - t) / 0.3))
    frame *= (1 - 0.72 * dim)
    # typewriter reveal by columns (cheap): reveal width over time
    rev = min(1, t / max(0.6, min(2.2, d * 0.45)))
    w = int(L.shape[1] * rev) if k.get('type', True) else L.shape[1]
    Lr = L.copy()
    Lr[:, w:, 3] = 0
    Lr[-int(70):, :, 3] = L[-int(70):, :, 3] * min(1, max(0, (t - 0.8) / 0.4))
    blend(frame, Lr, (W - L.shape[1]) / 2 + 40, (H - L.shape[0]) / 2, dim)


def ov_redact(frame, t, d, o):
    """'ERNIE & TIM' with black bars that can lift. kw names list, lift_at (s) or None"""
    k = o.kw
    ink = (25, 22, 20) if k.get('paper') else (240, 240, 235)
    if k.get('paper'):
        if 'bg' not in o.cache:
            r = np.random.default_rng(5)
            bg = np.ones((H, W, 3), np.float32) * np.array([0.91, 0.88, 0.80], np.float32)
            bg += cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), 2)[..., None] * 0.025
            bg *= (0.75 + 0.25 * vignette())
            o.cache['bg'] = bg
            o.cache['hdr'] = text_rgba('CLASSIFIED  ·  ORIGIN SPECIAL', 'SpecialElite-Regular.ttf', 54, (170, 30, 30), 0, shadow=False)
        frame[:] = o.cache['bg']
        hd = o.cache['hdr']
        blend(frame, hd, (W - hd.shape[1]) / 2, H * 0.24)
    if 'L' not in o.cache:
        o.cache['L'] = [text_rgba(n, 'SpecialElite-Regular.ttf', 170, ink, 0, shadow=False) for n in k['names']]
    Ls = o.cache['L']
    gap = 140
    tot = sum(L.shape[1] for L in Ls) + gap * (len(Ls) - 1)
    x = (W - tot) / 2
    lift = k.get('lift_at')
    for i, L in enumerate(Ls):
        y = H * k.get('y', 0.5) - L.shape[0] / 2
        a = min(1, (t - i * 0.25) / 0.2)
        if a > 0:
            blend(frame, L, x, y, a)
            bar_on = lift is None or t < lift + i * 0.15
            if bar_on:
                bw = int(L.shape[1] * min(1, (t - i * 0.25) / 0.25) + 30)
                cv2.rectangle(frame, (int(x - 15), int(y + 8)), (int(x - 15 + bw), int(y + L.shape[0] - 4)), (0.02, 0.02, 0.02), -1)
        x += L.shape[1] + gap
    if len(Ls) == 2:
        amp = text_rgba('&', 'SpecialElite-Regular.ttf', 120, ink, 0, shadow=False) if 'amp' not in o.cache else o.cache['amp']
        o.cache['amp'] = amp
        blend(frame, amp, (W - amp.shape[1]) / 2 + (Ls[0].shape[1] - Ls[1].shape[1]) / 2, H * k.get('y', 0.5) - amp.shape[0] / 2, min(1, t / 0.3))


def ov_timeline(frame, t, d, o):
    """1966 ---- 1999 bar with counter. kw a, b, label"""
    k = o.kw
    p = ease_in_out(t / k.get('draw', 1.8))
    y = int(H * 0.55)
    x0, x1 = 360, W - 360
    xe = int(x0 + (x1 - x0) * p)
    frame *= 0.35
    cv2.line(frame, (x0, y), (x1, y), (0.35, 0.35, 0.35), 6, cv2.LINE_AA)
    cv2.line(frame, (x0, y), (xe, y), (1.0, 0.8, 0.0), 10, cv2.LINE_AA)
    cv2.circle(frame, (x0, y), 18, (1, 1, 1), -1, cv2.LINE_AA)
    if p > 0.98:
        cv2.circle(frame, (x1, y), 18, (1, 1, 1), -1, cv2.LINE_AA)
    for key, xx, val in (('a', x0, str(k['a'])), ('b', x1, str(k['b']))):
        if key == 'b' and p < 0.98:
            continue
        if key not in o.cache:
            o.cache[key] = text_rgba(val, 'Anton-Regular.ttf', 110, (255, 255, 255), 8)
        L = o.cache[key]
        blend(frame, L, xx - L.shape[1] / 2, y - L.shape[0] - 40)
    n = int(round(k['b'] - k['a'])) if False else int(round((k['b'] - k['a']) * p))
    lab = f"{n} {k.get('unit', 'YEARS')}"
    if lab not in o.cache:
        o.cache[lab] = text_rgba(lab, 'Anton-Regular.ttf', 92, (255, 205, 0), 8)
    L = o.cache[lab]
    blend(frame, L, (x0 + xe) / 2 - L.shape[1] / 2, y + 40)


def ov_counter(frame, t, d, o):
    k = o.kw
    p = ease_out(t / k.get('dur', 1.2))
    n = int(round(k['n'] * p))
    lab = k.get('fmt', '{}').format(n)
    if lab not in o.cache:
        o.cache[lab] = text_rgba(lab, 'Anton-Regular.ttf', k.get('size', 200), tuple(k.get('color', (255, 205, 0))), 12)
    L = o.cache[lab]
    s = 1 + 0.06 * (1 - ease_out((t - k.get('dur', 1.2)) / 0.2)) if t > k.get('dur', 1.2) else 1
    Ls = scaled(L, s)
    alpha = 1 if d - t > 0.18 else max(0, (d - t) / 0.18)
    blend(frame, Ls, k.get('x', 0.5) * W - Ls.shape[1] / 2, k.get('y', 0.5) * H - Ls.shape[0] / 2, alpha)


def ov_datecard(frame, t, d, o):
    """full black card with typed date. kw txt, sub"""
    k = o.kw
    frame[:] = 0.03
    frame += grain_tex(int(t * FPS)) * 0.02
    if 'chars' not in o.cache:
        o.cache['chars'] = {}
    txt = k['txt']
    n = min(len(txt), int(t / k.get('cps', 0.07)) + 1)
    s = txt[:n]
    if s not in o.cache['chars']:
        o.cache['chars'][s] = text_rgba(s, 'SpecialElite-Regular.ttf', k.get('size', 110), (240, 238, 228), 0, shadow=False)
    L = o.cache['chars'][s]
    full = o.cache['chars'].get(txt)
    if full is None:
        full = o.cache['chars'][txt] = text_rgba(txt, 'SpecialElite-Regular.ttf', k.get('size', 110), (240, 238, 228), 0, shadow=False)
    blend(frame, L, (W - full.shape[1]) / 2, H * 0.47 - full.shape[0] / 2)
    if k.get('sub') and t > len(txt) * k.get('cps', 0.07) + 0.3:
        if 'sub' not in o.cache:
            o.cache['sub'] = text_rgba(k['sub'], 'Oswald.ttf', 44, (255, 205, 0), 0, shadow=False)
        S = o.cache['sub']
        blend(frame, S, (W - S.shape[1]) / 2, H * 0.47 + full.shape[0] / 2 + 30, min(1, (t - len(txt) * k.get('cps', 0.07) - 0.3) / 0.3))


def ov_flash(frame, t, d, o):
    a = max(0, 1 - t / d) * o.kw.get('amt', 0.85)
    frame[:] = frame * (1 - a) + a * np.array(o.kw.get('color', (1, 1, 1)), np.float32)


def ov_fade(frame, t, d, o):
    """fade from/to black. kw mode in/out"""
    p = t / d
    a = 1 - p if o.kw.get('mode', 'in') == 'in' else p
    frame *= (1 - a)


def ov_tvoff(frame, t, d, o):
    p = ease_in_out(t / d)
    sy = max(0.004, 1 - p * 1.0)
    sx = 1 if p < 0.6 else max(0.0, 1 - (p - 0.6) / 0.4)
    src = (frame * (1 + p * 1.5)).clip(0, 1)
    h, w = max(2, int(H * sy)), max(2, int(W * sx))
    small = cv2.resize(src, (w, h))
    frame[:] = 0
    y0, x0 = (H - h) // 2, (W - w) // 2
    frame[y0:y0 + h, x0:x0 + w] = small


def ov_vhs_rewind(frame, t, d, o):
    r = np.random.default_rng(int(t * 100))
    for _ in range(6):
        y = r.integers(0, H - 40)
        hh = r.integers(4, 26)
        frame[y:y + hh] = np.roll(frame[y:y + hh], r.integers(-120, 120), axis=1) * 0.7 + 0.3
    frame[:] = frame * 0.85 + 0.03
    if 'L' not in o.cache:
        o.cache['L'] = text_rgba('◀◀', 'Inter.ttf', 90, (255, 255, 255), 0, shadow=True)
    blend(frame, o.cache['L'], 70, 60)


def ov_static(frame, t, d, o):
    r = np.random.default_rng(int(t * 1000) % 99991)
    n = r.random((H // 4, W // 4)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    a = o.kw.get('amt', 0.6) * (1 if d - t > 0.1 else (d - t) / 0.1)
    frame[:] = frame * (1 - a) + n * a


def ov_glitch(frame, t, d, o):
    r = np.random.default_rng(int(t * 60))
    sh = int(r.integers(10, 40))
    f2 = frame.copy()
    f2[..., 0] = np.roll(frame[..., 0], sh, 1)
    f2[..., 2] = np.roll(frame[..., 2], -sh, 1)
    for _ in range(5):
        y = r.integers(0, H - 60); hh = r.integers(10, 60)
        f2[y:y + hh] = np.roll(f2[y:y + hh], r.integers(-200, 200), 1)
    frame[:] = f2


def ov_names(frame, t, d, o):
    """labels with lines pointing to spots: kw items=[(txt, x, y, tx, ty)] (label pos, target pos) in px"""
    k = o.kw
    for i, (txt, x, y, tx, ty) in enumerate(k['items']):
        tt = t - i * k.get('stagger', 0.35)
        if tt <= 0:
            continue
        key = 'L' + str(i)
        if key not in o.cache:
            o.cache[key] = text_rgba(txt, 'Anton-Regular.ttf', k.get('size', 64), tuple(k.get('color', (255, 255, 255))), 7, track=2)
        L = o.cache[key]
        p = ease_out(tt / 0.3)
        alpha = p if d - t > 0.2 else max(0, (d - t) / 0.2)
        ex, ey = x + (tx - x) * p, y + (ty - y) * p
        cv2.line(frame, (int(x), int(y)), (int(ex), int(ey)), (1, 0.82, 0), 5, cv2.LINE_AA)
        cv2.circle(frame, (int(ex), int(ey)), 9, (1, 0.82, 0), -1, cv2.LINE_AA)
        blend(frame, scaled(L, 0.7 + 0.3 * ease_out_back(tt / 0.25)), x - L.shape[1] / 2, y - L.shape[0] - 6, alpha)


def ov_letterbox(frame, t, d, o):
    h = int(o.kw.get('h', 110) * ease_out(t / 0.4))
    frame[:h] = 0
    frame[H - h:] = 0


def ov_subs(frame, t, d, o):
    """clip subtitles: kw lines=[(t0, t1, text)] in local time"""
    act = [(a, b, txt) for (a, b, txt) in o.kw['lines'] if a <= t < b]
    for (a, b, txt) in act[-1:]:          # only the newest line: no overlapping subtitles
        if True:
            key = txt
            if key not in o.cache:
                o.cache[key] = text_rgba(txt, 'Oswald.ttf', 54, (255, 255, 255), 6, track=0)
            L = o.cache[key]
            blend(frame, L, (W - L.shape[1]) / 2, H - 70 - L.shape[0])


def ov_split(frame, t, d, o):
    """two framed panels side by side with captions; kw left, right: dict(path|frame=(src,t), caption)"""
    k = o.kw
    if 'P' not in o.cache:
        panels = []
        for side in ('left', 'right'):
            p = k[side]
            if 'path' in p:
                im = Image.open(ROOT + '/' + p['path']).convert('RGB')
                if p.get('crop'):
                    c = p['crop']; im = im.crop((int(c[0] * im.width), int(c[1] * im.height), int(c[2] * im.width), int(c[3] * im.height)))
            else:
                src, tt = p['frame']
                raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(tt), '-i', ROOT + '/' + src, '-frames:v', '1', '-vf', 'scale=960:720', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
                import io
                im = Image.open(io.BytesIO(raw)).convert('RGB')
                if p.get('crop'):
                    c = p['crop']; im = im.crop((int(c[0] * im.width), int(c[1] * im.height), int(c[2] * im.width), int(c[3] * im.height)))
            if p.get('bw'):
                im = im.convert('L').convert('RGB')
            s = min(820 / im.width, 640 / im.height)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            fr = Image.new('RGBA', (im.width + 24, im.height + 24), (255, 255, 255, 255))
            fr.paste(im, (12, 12))
            panels.append((np.asarray(fr).astype(np.float32) / 255, p.get('caption', ''), p.get('cap_color', (255, 255, 255))))
        o.cache['P'] = panels
        o.cache['C'] = [text_rgba(c, 'Anton-Regular.ttf', 70, cc, 7) if c else None for _, c, cc in panels]
    frame *= 0.3
    for i, (L, cap, _) in enumerate(o.cache['P']):
        tt = t - i * 0.3
        if tt <= 0:
            continue
        cx = W * (0.27 if i == 0 else 0.73)
        dy = (1 - ease_out(tt / 0.35)) * 200
        alpha = min(1, tt / 0.2) * (1 if d - t > 0.2 else max(0, (d - t) / 0.2))
        blend(frame, L, cx - L.shape[1] / 2, H * 0.44 - L.shape[0] / 2 + dy, alpha)
        C = o.cache['C'][i]
        if C is not None:
            blend(frame, C, cx - C.shape[1] / 2, H * 0.44 + L.shape[0] / 2 + 10 + dy, alpha)
    if k.get('mid'):
        if 'M' not in o.cache:
            o.cache['M'] = text_rgba(k['mid'], 'Anton-Regular.ttf', 110, (255, 205, 0), 9)
        M = o.cache['M']
        if t > 0.6:
            blend(frame, scaled(M, 0.6 + 0.4 * ease_out_back((t - 0.6) / 0.25)), W / 2 - M.shape[1] / 2, H * 0.44 - M.shape[0] / 2)


OVS = {k[3:]: v for k, v in globals().items() if k.startswith('ov_')}


# ----------------------------------------------------------------------------- shake / zoom punches (global)
class GFX:
    def __init__(self, kind, start, dur, **kw):
        self.kind, self.start, self.dur, self.kw = kind, start, dur, kw


def shake_offset(gfx, t):
    dx = dy = 0.0
    for g in gfx:
        if g.kind == 'shake' and g.start <= t < g.start + g.dur:
            p = (t - g.start) / g.dur
            amp = g.kw.get('amp', 22) * (1 - p) ** 1.5
            dx += amp * math.sin(t * 91.0)
            dy += amp * math.cos(t * 73.0)
    return dx, dy


def punch_scale(gfx, t):
    s = 1.0
    for g in gfx:
        if g.kind == 'punch' and g.start <= t < g.start + g.dur:
            p = (t - g.start)
            s *= 1 + (g.kw.get('amt', 0.18)) * ease_out(p / 0.08)
    return s


# ----------------------------------------------------------------------------- frame renderer
class Renderer:
    def __init__(self, timeline):
        self.tl = timeline
        self.readers = {}

    def base_frame(self, sh, t, fi):
        lt = t - sh.start
        d = sh.end - sh.start
        k = sh.kw
        if sh.kind == 'video':
            r = self.readers.get(id(sh))
            if r is None:
                tin = k['t'] + (lt * k['speed'] if not k['freeze'] else 0)
                n = int(math.ceil((sh.end - t) * FPS)) + 2
                r = self.readers[id(sh)] = VideoReader(k['src'], tin, n, k['speed'], k['freeze'])
                r.start_lt = lt
            img = r.read()
            p = lt / max(d, 1e-3)
            z = k['z0'] + (k['z1'] - k['z0']) * ease_in_out(p) if not k.get('linear') else k['z0'] + (k['z1'] - k['z0']) * p
            zz = z * punch_scale(self.tl['gfx'], t)
            ww, hh = W * MARGIN / zz, H * MARGIN / zz
            ww = min(ww, r.dw); hh = min(hh, r.dh)
            cx = k['x'] * r.dw
            cy = k['y'] * r.dh
            cx = min(max(cx, ww / 2), r.dw - ww / 2)
            cy = min(max(cy, hh / 2), r.dh - hh / 2)
            s = W / ww
            M = np.array([[s, 0, -(cx - ww / 2) * s], [0, s, -(cy - hh / 2) * s]], np.float32)
            f = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        elif sh.kind == 'image':
            p = ease_in_out(lt / max(d, 1e-3))
            c = [a + (b - a) * p for a, b in zip(k['c0'], k['c1'])]
            f = frame_from_image(k['path'], c[0], c[1], c[2] * punch_scale(self.tl['gfx'], t), k.get('bg', 'cover'))
        else:
            f = np.zeros((H, W, 3), np.float32)
            k['fn'](f, lt, d, k)
        return apply_grade(f, k.get('grade'), fi, lt)

    def frame(self, fi):
        t = fi / FPS
        f = None
        for sh in self.tl['shots']:
            if sh.start <= t < sh.end:
                f = self.base_frame(sh, t, fi)
                break
        if f is None:
            f = np.zeros((H, W, 3), np.float32)
        for o in self.tl['ovs']:
            if o.start <= t < o.end:
                OVS[o.fn](f, t - o.start, o.end - o.start, o)
        dx, dy = shake_offset(self.tl['gfx'], t)
        if dx or dy:
            M = np.array([[1.04, 0, dx - W * 0.02], [0, 1.04, dy - H * 0.02]], np.float32)
            f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        # close readers that ended
        for sh in self.tl['shots']:
            if sh.end <= t and id(sh) in self.readers:
                self.readers.pop(id(sh)).close()
        return (np.clip(f, 0, 1) * 255).astype(np.uint8)


def render_chunk(args):
    timeline_path, f0, f1, out, scale = args
    import pickle
    tl = pickle.load(open(timeline_path, 'rb'))
    R = Renderer(tl)
    ow, oh = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                            '-i', '-', '-vf', f'scale={ow}:{oh}' if scale != 1 else 'null',
                            '-c:v', 'libx264', '-preset', 'medium' if scale == 1 else 'veryfast', '-crf', '17' if scale == 1 else '26',
                            '-pix_fmt', 'yuv420p', '-g', '60', out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        enc.stdin.write(R.frame(fi).tobytes())
    enc.stdin.close(); enc.wait()
    for r in R.readers.values():
        r.close()
    return out


# ----------------------------------------------------------------------------- audio
def load_audio(path, sr=SR):
    x, s = sf.read(path, always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, 1)
    if s != sr:
        g = math.gcd(s, sr)
        x = resample_poly(x, sr // g, s // g, axis=0)
    return x.astype(np.float32)


def lufs(x):
    import pyloudnorm as pyln
    m = pyln.Meter(SR)
    try:
        return m.integrated_loudness(x)
    except Exception:
        return -30.0


def mix_audio(events, total, out_path):
    buf = np.zeros((int(total * SR) + SR, 2), np.float32)
    for ev in events:
        x = ev['data'] if 'data' in ev else load_audio(ev['path'])
        if 'trim' in ev:
            a, b = ev['trim']
            x = x[int(a * SR):int(b * SR)]
        g = 10 ** (ev.get('gain', 0) / 20)
        x = x * g
        fi, fo = ev.get('fade_in', 0.005), ev.get('fade_out', 0.01)
        n = len(x)
        if n == 0:
            continue
        a = min(n, int(fi * SR)); b = min(n, int(fo * SR))
        if a: x[:a] *= np.linspace(0, 1, a)[:, None]
        if b: x[-b:] *= np.linspace(1, 0, b)[:, None]
        s = int(ev['t'] * SR)
        if s < 0:
            x = x[-s:]; s = 0
        e = min(len(buf), s + len(x))
        buf[s:e] += x[:e - s]
    sf.write(out_path, buf[:int(total * SR)], SR, subtype='FLOAT')
    return out_path
