"""Small rendering kit for The Sinistory house style.
Everything is drawn at 1920x1080, 30 fps, and streamed as raw RGB into one ffmpeg encode."""
import subprocess, numpy as np, math, os, json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
ROOT = '/tmp/claude-0/-home-user-main/097e55d9-3f75-5e8f-88d6-04e1d361aa0f/scratchpad/'
SRC = ROOT + 'src/'
FONTS = ROOT + 'edit/fonts/'
def font(name, size): return ImageFont.truetype(FONTS + {'anton': 'Anton-Regular.ttf', 'type': 'SpecialElite-Regular.ttf', 'hand': 'PatrickHandSC-Regular.ttf', 'marker': 'GochiHand-Regular.ttf'}[name], size)

NAVY_C, NAVY_E = (24, 29, 44), (11, 14, 24)
PAPER_C, PAPER_E = (229, 222, 206), (178, 172, 158)
INK, RED, CREAM, POLA = (21, 21, 21), (205, 32, 42), (238, 232, 218), (245, 242, 235)

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back_out(x, s=1.6): x = min(max(x, 0), 1) - 1; return 1 + x * x * ((s + 1) * x + s)

_rng = np.random.default_rng(3)
def _bg(c, e):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2).clip(0, 1) ** 1.6
    img = np.array(c)[None, None, :] * (1 - r[..., None]) + np.array(e)[None, None, :] * r[..., None]
    return img
_BG = {'navy': _bg(NAVY_C, NAVY_E), 'paper': _bg(PAPER_C, PAPER_E)}
_GRAIN = [_rng.normal(0, 1, (H, W, 1)) for _ in range(4)]
def background(kind, n):
    g = 3.0 if kind == 'navy' else 5.0
    return Image.fromarray(np.clip(_BG[kind] + _GRAIN[(n // 2) % 4] * g, 0, 255).astype(np.uint8))

def notebook(n):
    im = Image.fromarray(np.clip(_bg((244, 240, 229), (214, 208, 192)) + _GRAIN[(n // 2) % 4] * 3, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for y in range(150, H, 64): d.line([(0, y), (W, y)], fill=(160, 185, 214), width=2)
    d.line([(300, 0), (300, H)], fill=(214, 92, 92), width=3)
    return im

# ---------- source footage ----------
def _sar_crop(src, yoff):
    w = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.strip())
    if w >= 1200:  # movie BD rip (square pixels): 6% punch-in hides the corner watermark
        return 'crop=iw*0.94:ih*0.94:(iw-iw*0.94)/2:(ih-ih*0.94)*%f' % yoff
    cw = w - 16; ch = cw // 2  # DVD 8:9 SAR: (cw*8/9) / (cw/2) = 16:9
    return f'crop={cw}:{ch}:8:(ih-{ch})*{yoff}'

def clip_frames(name, ss, dur, yoff=0.5):
    src = SRC + name
    vf = f'{_sar_crop(src, yoff)},scale={W}:{H}:flags=lanczos,fps={FPS}'
    raw = subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-ss', f'{ss:.3f}', '-i', src, '-t', f'{dur + 0.2:.3f}', '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    n = len(raw) // (W * H * 3)
    return [Image.frombuffer('RGB', (W, H), raw[i * W * H * 3:(i + 1) * W * H * 3]) for i in range(n)]

def still43(name, t, w=960):
    src = SRC + name
    r = subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', '-vf', f'crop=iw-16:ih:8:0,scale={w}:{w * 3 // 4}:flags=lanczos', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
    return Image.open(BytesIO(r.stdout)).convert('RGB')

def zoom(im, z, cx=.5, cy=.5):
    if abs(z - 1) < 1e-4: return im
    cw, ch = W / z, H / z
    x0 = min(max(cx * W - cw / 2, 0), W - cw); y0 = min(max(cy * H - ch / 2, 0), H - ch)
    return im.transform((W, H), Image.AFFINE, (cw / W, 0, x0, 0, ch / H, y0), resample=Image.BICUBIC)

# ---------- graphic elements ----------
def polaroid(photo, caption, photo_w=1100, rot=-2.0):
    ph = photo.resize((photo_w, photo_w * 3 // 4), Image.LANCZOS)
    b, bot = int(photo_w * .045), int(photo_w * .16)
    card = Image.new('RGBA', (photo_w + 2 * b, ph.height + b + bot), POLA + (255,))
    card.paste(ph, (b, b))
    d = ImageDraw.Draw(card); f = font('hand', int(photo_w * .058))
    tw = d.textlength(caption, font=f); d.text(((card.width - tw) / 2, ph.height + b + bot * .22), caption, font=f, fill=INK)
    pad = 60; out = Image.new('RGBA', (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([pad + 10, pad + 18, pad + card.width + 10, pad + card.height + 18], fill=(0, 0, 0, 150))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(14)))
    out.alpha_composite(card, (pad, pad))
    pr = int(photo_w * .016); cx, cy = out.width // 2, pad + b // 2 + 2   # push-pin
    dd = ImageDraw.Draw(out); dd.ellipse([cx - pr + 3, cy - pr + 5, cx + pr + 3, cy + pr + 5], fill=(0, 0, 0, 90))
    dd.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=RED + (255,)); dd.ellipse([cx - pr * .45, cy - pr * .55, cx - pr * .05, cy - pr * .15], fill=(255, 140, 140, 255))
    return out.rotate(rot, resample=Image.BICUBIC, expand=True)

def paste_center(base, el, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0: el = el.resize((max(1, int(el.width * scale)), max(1, int(el.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        a = el.getchannel('A').point(lambda v: int(v * alpha)); el = el.copy(); el.putalpha(a)
    base.alpha_composite(el, (int(cx - el.width / 2), int(cy - el.height / 2)))

def label_img(text):
    f = font('type', 34); tw = ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(text, font=f)
    im = Image.new('RGBA', (int(tw + 64), 68), (30, 30, 34, 220))
    ImageDraw.Draw(im).text((32, 13), text, font=f, fill=CREAM)
    return im

def paper_tag(text, size=130, q=True):
    f = font('anton', size); d0 = ImageDraw.Draw(Image.new('RGB', (1, 1))); bb = d0.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0] + 120, bb[3] - bb[1] + 110
    card = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0))
    sh = Image.new('RGBA', card.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([48, 52, 48 + w, 52 + h], fill=(0, 0, 0, 140))
    card = Image.alpha_composite(card, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(card); d.rectangle([40, 40, 40 + w, 40 + h], fill=(240, 235, 222, 255))
    d.text((40 + 60 - bb[0], 40 + 55 - bb[1]), text, font=f, fill=INK)
    if q: d.text((40 + w - 40, -10), '?', font=font('marker', int(size * 1.05)), fill=RED)
    return card

def wobbly_line(d, x0, x1, y, prog, width=10, seed=1):
    r = np.random.default_rng(seed); xs = np.linspace(x0, x1, 40); ys = y + np.cumsum(r.normal(0, .8, 40)) + np.sin(np.linspace(0, 3, 40)) * 2
    k = max(2, int(40 * prog)); pts = list(zip(xs[:k], ys[:k]))
    if prog > 0: d.line(pts, fill=RED, width=width, joint='curve')

def hand_circle(d, cx, cy, rx, ry, prog, width=9):
    t = np.linspace(-.6, -.6 + 2 * math.pi * 1.08 * prog, 80)
    pts = [(cx + rx * (1 + .04 * math.sin(3 * a)) * math.cos(a), cy + ry * math.sin(a)) for a in t]
    if prog > 0: d.line(pts, fill=RED, width=width, joint='curve')

# ---------- audio ----------
SR = 48000
def load_audio(path, ss=None, dur=None):
    cmd = ['ffmpeg', '-nostdin', '-loglevel', 'error'] + (['-ss', f'{ss:.3f}'] if ss is not None else []) + ['-i', path] + (['-t', f'{dur:.3f}'] if dur else []) + ['-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()

def fade(x, fi=0.01, fo=0.015):
    n = len(x); a, b = int(fi * SR), int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)[:, None]
    if b: x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x

def lufs(x):
    import pyloudnorm as pyln
    return pyln.Meter(SR).integrated_loudness(x)

def gain_to(x, target):
    l = lufs(x); return x * 10 ** ((target - l) / 20)
