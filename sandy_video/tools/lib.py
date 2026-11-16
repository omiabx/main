import subprocess, numpy as np, cv2, math, random, functools, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")

# ---------------------------------------------------------------- sources
SRC = {
    "tea":  dict(path="src/ep/s1_e01-03.mkv", dw=958, dh=720, subs=False),
    "ch":   dict(path="src/ep/chimps.mp4",     dw=640, dh=480, subs=False),
    "hib":  dict(path="src/ep/leaves_q.mp4",   dw=638, dh=480, subs=True),
    "sq":   dict(path="src/ep/squirreljokes.mp4", dw=638, dh=480, subs=True),
    "pr":   dict(path="src/ep/ch14_q.mp4",     dw=638, dh=480, subs=True),
}

def crop_box(src, cy=0.45):
    s = SRC[src]; dw, dh = s["dw"], s["dh"]
    if s["subs"]:            # keep the top ~70% so burned-in captions are cut off
        ch = int(dh * 0.70); cw = int(ch * 16 / 9); x = (dw - cw) // 2; y = 0
    else:
        cw = dw; ch = int(dw * 9 / 16); x = 0; y = int((dh - ch) * cy)
    return cw - cw % 2, ch - ch % 2, x, y

class Reader:
    """Sequential frame reader for a source range, output 1920x1080 BGR."""
    def __init__(self, src, start, dur, cy=0.45, size=(W, H)):
        s = SRC[src]; cw, ch, x, y = crop_box(src, cy)
        vf = f"scale={s['dw']}:{s['dh']},setsar=1,crop={cw}:{ch}:{x}:{y},scale={size[0]}:{size[1]}:flags=lanczos,fps={FPS}"
        self.size = size
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", os.path.join(ROOT, s["path"]),
                                   "-t", f"{dur + 0.5:.3f}", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.idx = -1; self.last = np.zeros((size[1], size[0], 3), np.uint8)
    def get(self, i):
        n = self.size[0] * self.size[1] * 3
        while self.idx < i:
            b = self.p.stdout.read(n)
            if len(b) < n: break
            self.last = np.frombuffer(b, np.uint8).reshape(self.size[1], self.size[0], 3); self.idx += 1
        return self.last
    def close(self):
        try: self.p.kill()
        except Exception: pass

# ---------------------------------------------------------------- easing
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_back(x, s=1.9): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t

# ---------------------------------------------------------------- 2D helpers
def warp_full(img, zoom=1.0, cx=0.5, cy=0.5, dx=0, dy=0, rot=0.0):
    if abs(zoom - 1) < 1e-4 and dx == 0 and dy == 0 and rot == 0: return img.copy()
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((cx * w, cy * h), rot, zoom)
    M[0, 2] += (w / 2 - cx * w) * 0 + dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def blit(canvas, rgba, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    """Composite an RGBA (numpy, RGBA order) image centred at (cx,cy)."""
    if alpha <= 0.003 or scale <= 0.003: return
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
    M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], float) @ M.T
    x0, y0 = np.floor(corners.min(0)).astype(int); x1, y1 = np.ceil(corners.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0: return
    M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
    patch = cv2.warpAffine(rgba, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    a = patch[..., 3:4].astype(np.float32) / 255 * alpha
    roi = canvas[y0:y1, x0:x1].astype(np.float32)
    col = patch[..., 2::-1].astype(np.float32)  # RGB->BGR
    canvas[y0:y1, x0:x1] = (roi * (1 - a) + col * a).astype(np.uint8)

def to_rgba(bgr, border=0):
    rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
    return rgba

# ---------------------------------------------------------------- graphics (PIL -> RGBA numpy)
@functools.lru_cache(None)
def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), size)

@functools.lru_cache(None)
def text_img(text, fname="Anton.ttf", size=120, fill=(255, 255, 255), stroke=0, stroke_fill=(0, 0, 0), shadow=0, pad=20, spacing=6):
    f = font(fname, size)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = tmp.multiline_textbbox((0, 0), text, font=f, stroke_width=stroke, spacing=spacing, align="center")
    w, h = bb[2] - bb[0] + pad * 2 + shadow, bb[3] - bb[1] + pad * 2 + shadow
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
        ds.multiline_text((pad - bb[0] + shadow, pad - bb[1] + shadow), text, font=f, fill=(0, 0, 0, 200), stroke_width=stroke, stroke_fill=(0, 0, 0, 200), spacing=spacing, align="center")
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(shadow / 2))); d = ImageDraw.Draw(im)
    d.multiline_text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, spacing=spacing, align="center")
    return np.array(im)

def paper(w, h, color=(246, 240, 222), seed=0):
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 4), np.float32); a[..., :3] = color; a[..., 3] = 255
    a[..., :3] += rng.normal(0, 6, (h, w, 1)); return a.clip(0, 255).astype(np.uint8)

@functools.lru_cache(None)
def doc_img(kind="contract"):
    """Contract / letter documents. Returns RGBA numpy."""
    w, h = 760, 940
    im = Image.fromarray(paper(w, h, seed=2)); d = ImageDraw.Draw(im)
    tf = font("CourierPrime.ttf", 34); se = font("SpecialElite.ttf", 46); se2 = font("SpecialElite.ttf", 34); mk = font("PermanentMarker.ttf", 44)
    d.text((44, 40), "TREEDOME ENTERPRISES LTD.", font=tf, fill=(40, 40, 40))
    d.line((44, 88, 716, 88), fill=(60, 60, 60), width=3)
    d.text((44, 108), "EMPLOYMENT CONTRACT", font=se, fill=(20, 20, 20))
    rows = [("EMPLOYEE:", "S. CHEEKS"), ("POSITION:", "RESEARCHER"), ("FUNDING:", "GRANT"), ("TERM:", "20 YEARS"), ("DATED:", "MAY 2006")]
    for i, (a, b) in enumerate(rows):
        y = 210 + i * 86
        d.text((44, y), a, font=se2, fill=(70, 70, 70)); d.text((300, y - 8), b, font=mk, fill=(25, 40, 120))
    for i in range(4): d.line((44, 668 + i * 34, 420 + (i * 97) % 270, 668 + i * 34), fill=(160, 158, 148), width=5)
    d.text((60, 830), "The Board", font=font("PermanentMarker.ttf", 40), fill=(25, 40, 120))
    d.line((44, 885, 400, 885), fill=(60, 60, 60), width=2)
    d.text((440, 855), "signed", font=font("SpecialElite.ttf", 26), fill=(110, 110, 110))
    return np.array(im)
CONTRACT_ROWS_Y = {"EMPLOYEE": 210, "POSITION": 296, "FUNDING": 382, "TERM": 468, "DATED": 554}

@functools.lru_cache(None)
def stamp_img(text="EXPIRED", color=(222, 28, 36), size=170, seed=5):
    f = font("Anton.ttf", size)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10))); bb = tmp.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; w, h = tw + 120, th + 90
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, w - 8, h - 8), radius=22, outline=color + (255,), width=max(8, size // 11))
    d.text(((w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]), text, font=f, fill=color + (255,))
    a = np.array(im); rng = np.random.default_rng(seed)
    holes = rng.random(a.shape[:2]) < 0.07; a[..., 3] = np.where(holes, 0, a[..., 3])
    return np.array(Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.7)))

@functools.lru_cache(None)
def card_img(lines, w=820, title=None, seed=1, color=(250, 246, 232)):
    """Index card with typewriter lines (tuple of strings)."""
    lh = 64; h = 120 + lh * len(lines) + (70 if title else 0)
    im = Image.fromarray(paper(w, h, color, seed)); d = ImageDraw.Draw(im)
    d.line((0, 70 if title else 40, w, 70 if title else 40), fill=(220, 90, 90), width=3)
    for i in range(len(lines) + 2): d.line((0, (70 if title else 40) + lh * (i + 1), w, (70 if title else 40) + lh * (i + 1)), fill=(170, 200, 225), width=2)
    y = 20
    if title: d.text((36, 14), title, font=font("CourierPrime.ttf", 38), fill=(190, 40, 40)); y = 80
    for i, ln in enumerate(lines):
        d.text((36, y + 18 + i * lh), ln, font=font("SpecialElite.ttf", 44), fill=(25, 25, 25))
    return np.array(im)

@functools.lru_cache(None)
def note_img(text, w=420, h=300, color=(255, 230, 90), size=54, rot_seed=0):
    im = Image.new("RGBA", (w, h), color + (255,)); d = ImageDraw.Draw(im)
    f = font("PermanentMarker.ttf", size)
    bb = d.multiline_textbbox((0, 0), text, font=f, align="center", spacing=4)
    d.multiline_text(((w - (bb[2] - bb[0])) / 2 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=(30, 30, 30), align="center", spacing=4)
    return np.array(im)

def polaroid(bgr, w=560):
    h0, w0 = bgr.shape[:2]; ih = int(w * h0 / w0)
    img = cv2.resize(bgr, (w, ih), interpolation=cv2.INTER_AREA)
    b = 22; out = np.full((ih + b + 70, w + 2 * b, 4), 255, np.uint8)
    out[..., :3] = (248, 246, 240)
    out[b:b + ih, b:b + w, :3] = img[..., ::-1]
    return out

def with_shadow(rgba, blur=18, off=12, strength=0.55):
    h, w = rgba.shape[:2]; p = blur * 2 + off
    out = np.zeros((h + 2 * p, w + 2 * p, 4), np.uint8)
    a = np.zeros((h + 2 * p, w + 2 * p), np.float32); a[p + off:p + off + h, p + off:p + off + w] = rgba[..., 3] / 255 * strength
    a = cv2.GaussianBlur(a, (0, 0), blur)
    out[..., 3] = (a * 255).astype(np.uint8)
    src = rgba.astype(np.float32); sa = src[..., 3:4] / 255
    reg = out[p:p + h, p:p + w].astype(np.float32); ra = reg[..., 3:4] / 255
    oa = sa + ra * (1 - sa)
    col = (src[..., :3] * sa + reg[..., :3] * ra * (1 - sa)) / np.maximum(oa, 1e-6)
    out[p:p + h, p:p + w, :3] = col.astype(np.uint8); out[p:p + h, p:p + w, 3] = (oa[..., 0] * 255).astype(np.uint8)
    return out

# ---------------------------------------------------------------- backgrounds
@functools.lru_cache(None)
def blueprint():
    g = np.zeros((H, W, 3), np.float32)
    y = np.linspace(0, 1, H)[:, None]
    g[..., 0] = 58 - 18 * y; g[..., 1] = 30 - 8 * y; g[..., 2] = 14 + 0 * y  # BGR navy
    g = g.repeat(1, 1) if False else g
    for x in range(0, W, 48): g[:, x:x + 1] += (14, 9, 4)
    for yy in range(0, H, 48): g[yy:yy + 1, :] += (14, 9, 4)
    for x in range(0, W, 240): g[:, x:x + 2] += (22, 14, 6)
    for yy in range(0, H, 240): g[yy:yy + 2, :] += (22, 14, 6)
    rng = np.random.default_rng(3); g += rng.normal(0, 3, (H, W, 1))
    return g.clip(0, 255).astype(np.uint8)

_parts = np.random.default_rng(11).random((60, 4))
def bg_frame(t):
    c = blueprint().copy()
    for px, py, r, sp in _parts:
        y = (py * H - t * (20 + 40 * sp)) % H; x = px * W + 8 * math.sin(t * (0.6 + sp) + px * 9)
        cv2.circle(c, (int(x), int(y)), int(2 + 4 * r), (110, 80, 50), 1, cv2.LINE_AA)
    return c

# ---------------------------------------------------------------- post FX
_vig = None
def vignette(img, s=0.33):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W]; _vig = (1 - s * (((xx - W / 2) / (W / 1.35)) ** 2 + ((yy - H / 2) / (H / 1.2)) ** 2)).astype(np.float32)[..., None]
    return (img.astype(np.float32) * _vig).clip(0, 255).astype(np.uint8)

_grain = [np.random.default_rng(i).normal(0, 7, (H // 2, W // 2, 1)).astype(np.float32) for i in range(6)]
def grain(img, i):
    g = cv2.resize(_grain[i % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return (img.astype(np.float32) + g).clip(0, 255).astype(np.uint8)

def shake(img, t, amp, seed=0):
    dx = amp * math.sin(t * 91 + seed) * math.cos(t * 37); dy = amp * math.cos(t * 73 + seed * 2)
    M = np.float32([[1, 0, dx], [0, 1, dy]]); return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)

def glitch(img, t, strength=1.0, seed=0):
    rng = np.random.default_rng(int(t * 1000) + seed); out = img.copy()
    k = int(18 * strength); out[..., 2] = np.roll(img[..., 2], k, 1); out[..., 0] = np.roll(img[..., 0], -k, 1)
    for _ in range(int(9 * strength)):
        y = rng.integers(0, H - 60); hh = rng.integers(8, 70); s = rng.integers(-120, 120)
        out[y:y + hh] = np.roll(out[y:y + hh], s, 1)
    return out

def whip_blur(img, amount, horiz=True):
    k = max(1, int(amount))
    ker = np.zeros((1, k) if horiz else (k, 1), np.float32); ker[:] = 1 / k
    return cv2.filter2D(img, -1, ker)

def surveil(img, t):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); g = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR).astype(np.float32)
    g *= (0.75, 1.0, 0.8); g[::4] *= 0.78
    out = g.clip(0, 255).astype(np.uint8)
    cv2.rectangle(out, (60, 60), (W - 60, H - 60), (230, 230, 230), 2)
    if int(t * 2) % 2 == 0: cv2.circle(out, (110, 112), 16, (40, 40, 230), -1, cv2.LINE_AA)
    cv2.putText(out, "REC", (140, 126), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (235, 235, 235), 3, cv2.LINE_AA)
    s = 3600 * 2 + 17 * 60 + 4 + t
    tc = f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d}:{int((s % 1) * 30):02d}"
    cv2.putText(out, tc, (W - 420, H - 90), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (235, 235, 235), 3, cv2.LINE_AA)
    cv2.putText(out, "CAM 03  TREEDOME", (110, H - 90), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (235, 235, 235), 2, cv2.LINE_AA)
    return out

# ---------------------------------------------------------------- marker drawing
def marker_ellipse(img, cx, cy, rx, ry, prog, color=(40, 40, 225), th=11, rot=-8):
    if prog <= 0: return
    end = int(380 * clamp(prog))
    cv2.ellipse(img, (int(cx), int(cy)), (int(rx), int(ry)), rot, -100, -100 + end, color, th, cv2.LINE_AA)

def marker_line(img, p0, p1, prog, color=(40, 40, 225), th=11):
    if prog <= 0: return
    p = clamp(prog); x = p0[0] + (p1[0] - p0[0]) * p; y = p0[1] + (p1[1] - p0[1]) * p
    cv2.line(img, (int(p0[0]), int(p0[1])), (int(x), int(y)), color, th, cv2.LINE_AA)

def marker_arrow(img, p0, p1, prog, color=(40, 40, 225), th=10):
    if prog <= 0: return
    p = clamp(prog); x = p0[0] + (p1[0] - p0[0]) * p; y = p0[1] + (p1[1] - p0[1]) * p
    cv2.arrowedLine(img, (int(p0[0]), int(p0[1])), (int(x), int(y)), color, th, cv2.LINE_AA, tipLength=0.22 if p > 0.6 else 0)

def highlight(img, x0, y0, x1, y1, prog, color=(60, 235, 255), a=0.45):
    if prog <= 0: return
    x = int(x0 + (x1 - x0) * clamp(prog)); roi = img[y0:y1, x0:x]
    if roi.size: img[y0:y1, x0:x] = (roi * (1 - a) + np.array(color) * a).astype(np.uint8)
