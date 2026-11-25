"""Minimal timeline renderer: clips + stills + overlays + audio mix -> MP4.

Shots cover the timeline back to back. Overlays float on top. Audio events are mixed in numpy.
"""
import subprocess, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

W, H, FPS, SR = 1920, 1080, 30, 48000
SCR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(SCR, "assets", "fonts")
SFXDIR = os.path.join(SCR, "assets", "sfx")

def font(name, size):
    m = {"anton": "anton-latin-400-normal", "marker": "permanent-marker-latin-400-normal",
         "lucky": "luckiest-guy-latin-400-normal", "type": "special-elite-latin-400-normal",
         "oswald": "oswald-latin-700-normal", "bebas": "bebas-neue-latin-400-normal"}[name]
    return ImageFont.truetype(os.path.join(FONTS, m + ".ttf"), size)

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back_out(x, s=1.9):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, x): return a + (b - a) * x

# ---------------- video sources ----------------
class ClipReader:
    """Sequential frame reader for a source range, display-corrected to 640x480 (4:3)."""
    def __init__(self, path, start, dur, speed=1.0, pre=None):
        self.w, self.h = 640, 480
        vf = (pre + "," if pre else "") + f"setpts=PTS/{speed},scale={self.w}:{self.h}:flags=lanczos,setsar=1,fps={FPS}"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", path,
                                   "-t", f"{dur * speed + 0.5:.3f}", "-vf", vf, "-an",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None
    def next(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3:
            self.last = Image.frombuffer("RGB", (self.w, self.h), b, "raw", "RGB", 0, 1)
        return self.last
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass

_still_cache = {}
PRE = {"natives.mp4": "crop=1440:1080:240:0", "baker_hq.mp4": "crop=960:720:160:0"}
def grab(path, t, pre=None):
    """Single display-corrected 640x480 frame."""
    pre = pre or PRE.get(os.path.basename(path))
    k = (path, round(t, 3))
    if k not in _still_cache:
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                            "-vf", (pre + "," if pre else "") + "scale=640:480:flags=lanczos,setsar=1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True).stdout
        _still_cache[k] = Image.frombuffer("RGB", (640, 480), b, "raw", "RGB", 0, 1).copy()
    return _still_cache[k]

def frame_fill(src, zoom=1.0, cx=0.5, cy=0.5, ymax=480, sharpen=True):
    """Crop a 16:9 window from a 640x480 source and scale to 1920x1080.
    zoom>1 punches in. cx/cy are normalized centers. ymax limits the bottom (hides burned captions)."""
    sw, sh = src.size
    bw = sw / zoom; bh = bw * 9 / 16
    usable = min(ymax, sh)
    if bh > usable:
        bh = usable; bw = bh * 16 / 9
    x0 = clamp(cx * sw - bw / 2, 0, sw - bw); y0 = clamp(cy * usable - bh / 2, 0, usable - bh)
    im = src.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))
    if sharpen:
        im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    return im

# ---------------- drawing helpers ----------------
def text_layer(txt, fnt, fill=(255, 255, 255), stroke=10, stroke_fill=(0, 0, 0), shadow=8, spacing=0):
    """Render outlined text to an RGBA image (tight bbox + padding)."""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = d.multiline_textbbox((0, 0), txt, font=fnt, stroke_width=stroke, align="center", spacing=spacing)
    pad = stroke + shadow + 6
    w, h = int(math.ceil(bb[2] - bb[0] + pad * 2)), int(math.ceil(bb[3] - bb[1] + pad * 2))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if shadow:
        dr.multiline_text((pad - bb[0] + shadow, pad - bb[1] + shadow), txt, font=fnt, fill=(0, 0, 0, 170),
                          stroke_width=stroke, stroke_fill=(0, 0, 0, 170), align="center", spacing=spacing)
    dr.multiline_text((pad - bb[0], pad - bb[1]), txt, font=fnt, fill=fill, stroke_width=stroke,
                      stroke_fill=stroke_fill, align="center", spacing=spacing)
    return im

def paste_scaled(base, layer, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01: return
    lw, lh = layer.size
    L = layer
    if abs(scale - 1) > 1e-3:
        L = L.resize((max(1, int(lw * scale)), max(1, int(lh * scale))), Image.BICUBIC)
    if rot:
        L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = L.getchannel("A").point(lambda v: int(v * alpha)); L = L.copy(); L.putalpha(a)
    base.alpha_composite(L, (int(cx - L.size[0] / 2), int(cy - L.size[1] / 2))) if base.mode == "RGBA" else \
        base.paste(L, (int(cx - L.size[0] / 2), int(cy - L.size[1] / 2)), L)

def pop_in(t, dur=0.25):
    """Scale curve for a punchy pop-in."""
    return back_out(t / dur) if t < dur else 1.0

def vignette(strength=0.55):
    y, x = np.ogrid[:H, :W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    v = np.clip(1 - strength * np.clip(r - 0.45, 0, None) ** 1.6, 0, 1)
    return v[..., None].astype(np.float32)
VIG = None
def apply_vignette(im, strength=0.55):
    global VIG
    if VIG is None: VIG = vignette(strength)
    a = np.asarray(im).astype(np.float32) * VIG
    return Image.fromarray(a.astype(np.uint8))

def desaturate(im, amount):
    if amount <= 0: return im
    g = ImageOps.grayscale(im).convert("RGB")
    return Image.blend(im, g, clamp(amount))

def marker_circle(draw, box, color=(230, 30, 30), width=10, progress=1.0, wobble=0.04, seed=1):
    """Hand-drawn-ish ellipse drawn progressively."""
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    rnd = np.random.default_rng(seed); ph = rnd.uniform(0, 6.28)
    n = int(90 * progress) + 2
    pts = []
    for i in range(n):
        a = ph + i / 90 * 2 * math.pi * 1.08
        k = 1 + wobble * math.sin(3 * a + ph)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    draw.line(pts, fill=color, width=width, joint="curve")

# ---------------- audio ----------------
def load_audio(path, start=0.0, dur=None, speed=1.0):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", path]
    if dur is not None: cmd += ["-t", f"{dur * speed:.3f}"]
    af = f"atempo={speed}" if abs(speed - 1) > 1e-3 else "anull"
    cmd += ["-af", af, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    b = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()

class Mixer:
    def __init__(self, dur):
        self.buf = np.zeros((int(dur * SR) + SR, 2), np.float32)
    def add(self, arr, at, gain=1.0, fade_in=0.0, fade_out=0.0):
        if arr is None or len(arr) == 0: return
        a = arr * gain
        if fade_in > 0:
            n = min(len(a), int(fade_in * SR)); a[:n] *= np.linspace(0, 1, n)[:, None]
        if fade_out > 0:
            n = min(len(a), int(fade_out * SR)); a[-n:] *= np.linspace(1, 0, n)[:, None]
        s = int(at * SR)
        if s < 0: a = a[-s:]; s = 0
        e = min(len(self.buf), s + len(a)); self.buf[s:e] += a[: e - s]
    def sfx(self, name, at, gain=0.6):
        self.add(load_audio(os.path.join(SFXDIR, name + ".wav")), at, gain)
    def write(self, path):
        x = self.buf
        peak = np.max(np.abs(x)) or 1
        # soft limiter
        x = np.tanh(x * 1.1) / np.tanh(1.1) if peak > 0.98 else x
        x = np.clip(x, -1, 1)
        from scipy.io import wavfile
        wavfile.write(path, SR, (x * 32767).astype(np.int16))

# ---------------- render ----------------
def render(shots, overlays, mixer, out_path, dur, post=None):
    """shots: list of dict(t0, t1, frame=fn(t_local, t_global)->PIL RGB 1920x1080, open/close optional)
    overlays: list of dict(t0, t1, draw=fn(img_rgba, t_local, t_global))"""
    wav = out_path + ".wav"; mixer.write(wav)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
                            out_path], stdin=subprocess.PIPE)
    nf = int(round(dur * FPS))
    shots = sorted(shots, key=lambda s: s["t0"])
    si = 0; active = None
    for f in range(nf):
        tg = f / FPS
        while si < len(shots) and shots[si]["t0"] <= tg + 1e-6:
            if active and "close" in active: active["close"]()
            active = shots[si]; si += 1
            if "open" in active: active["open"]()
        if active and tg < active["t1"]:
            img = active["frame"](tg - active["t0"], tg)
        else:
            img = Image.new("RGB", (W, H), (0, 0, 0))
        img = img.convert("RGBA")
        for o in overlays:
            if o["t0"] <= tg < o["t1"]:
                o["draw"](img, tg - o["t0"], tg)
        img = img.convert("RGB")
        if post: img = post(img, tg)
        if img.size != (W, H):
            print("WARN frame size", img.size, "at", round(tg, 2), flush=True); img = img.resize((W, H))
        enc.stdin.write(img.tobytes())
        if f % 300 == 0: print(f"frame {f}/{nf}", flush=True)
    if active and "close" in active: active["close"]()
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print("rendered", out_path)

# ---------------- shot factories ----------------
def clip_shot(t0, t1, path, src_t, speed=1.0, zoom=(1.0, 1.0), cx=(0.5, 0.5), cy=(0.5, 0.5), ymax=480,
              gray=(0.0, 0.0), ease=ease_in_out, shake=0.0):
    dur = t1 - t0; st = {}
    def op(): st["r"] = ClipReader(path, src_t, dur, speed, PRE.get(os.path.basename(path)))
    def cl(): st["r"].close()
    def fr(tl, tg):
        src = st["r"].next(); k = ease(tl / dur) if dur > 0 else 1
        z = lerp(*zoom, k); x = lerp(*cx, k); y = lerp(*cy, k)
        if shake:
            x += shake * math.sin(tg * 53) * 0.01; y += shake * math.cos(tg * 47) * 0.01
        im = frame_fill(src, z, x, y, ymax)
        return desaturate(im, lerp(*gray, k))
    return {"t0": t0, "t1": t1, "frame": fr, "open": op, "close": cl}

def still_shot(t0, t1, path, src_t, zoom=(1.0, 1.0), cx=(0.5, 0.5), cy=(0.5, 0.5), ymax=480, gray=(0, 0),
               ease=ease_in_out, img=None):
    dur = t1 - t0
    def fr(tl, tg):
        src = img if img is not None else grab(path, src_t)
        k = ease(tl / dur) if dur > 0 else 1
        im = frame_fill(src, lerp(*zoom, k), lerp(*cx, k), lerp(*cy, k), ymax)
        return desaturate(im, lerp(*gray, k))
    return {"t0": t0, "t1": t1, "frame": fr}

def color_shot(t0, t1, color=(0, 0, 0)):
    base = Image.new("RGB", (W, H), color)
    return {"t0": t0, "t1": t1, "frame": lambda tl, tg: base.copy()}

def fn_shot(t0, t1, fn):
    return {"t0": t0, "t1": t1, "frame": fn}
