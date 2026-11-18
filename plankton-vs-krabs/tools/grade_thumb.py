"""Color-grade a finished thumbnail: punchier contrast, vivid reds, brighter/saturated characters,
darker + slightly cooler background for separation, light sharpening.
Run: python3 tools/grade_thumb.py thumb/user_thumb.jpg  -> output/thumbnail.png (1280x720) + output/thumbnail_full.png"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    s = np.where(mx > 1e-6, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx


def hsv_to_rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6; f = h * 6 - np.floor(h * 6)
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    out = np.zeros(h.shape + (3,), np.float32)
    for k, (R, G, B) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        m = i == k
        out[..., 0][m] = R[m]; out[..., 1][m] = G[m]; out[..., 2][m] = B[m]
    return out


def subject_mask(im):
    """characters (soft mask); falls back to a centre-left ellipse if rembg isn't available"""
    try:
        from rembg import remove, new_session
        cut = remove(im, session=new_session("isnet-anime"), only_mask=True, post_process_mask=True)
        m = np.asarray(cut.convert("L").filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
        return m
    except Exception:
        h, w = im.height, im.width
        y, x = np.mgrid[0:h, 0:w]
        return np.clip(1 - (((x - w * .25) / (w * .3)) ** 2 + ((y - h * .6) / (h * .5)) ** 2), 0, 1).astype(np.float32)


def grade(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    m = subject_mask(im)[..., None]

    # 1) global contrast S-curve
    a = np.clip(a, 0, 1); a = a + 0.18 * (a - a ** 2) * (2 * a - 1) * -1 + 0.0
    a = np.clip(0.5 + (a - 0.5) * 1.10, 0, 1)

    h, s, v = rgb_to_hsv(a)
    # 2) vibrance (boosts muted colours more than already-saturated ones)
    s = np.clip(s + (1 - s) * s * 0.55, 0, 1)
    # 3) vivid reds (Krabs + red title): extra saturation, slight lift
    red = np.clip(1 - np.minimum(np.abs(h - 0.0), np.abs(h - 1.0)) / 0.06, 0, 1) * (s > .35)
    s = np.clip(s + red * 0.10, 0, 1); v = np.clip(v * (1 + red * 0.08), 0, 1)
    a = hsv_to_rgb(h, s, v)
    # protect the title text (bright whites and strong reds) from the background darkening
    white = ((s < .14) & (v > .72)).astype(np.float32)
    redtxt = ((red > .5) & (s > .55) & (v > .45)).astype(np.float32)
    prot = np.asarray(Image.fromarray((np.maximum(white, redtxt) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
                      .filter(ImageFilter.GaussianBlur(2))).astype(np.float32)[..., None] / 255
    m = np.maximum(m, prot)

    # 4) characters pop: brighter + more saturated; background darker + slightly cooler
    lum = a.mean(-1, keepdims=True)
    subj = np.clip(np.clip(lum + (a - lum) * 1.10, 0, 1) * 1.08 + 0.01, 0, 1)
    bg = a * 0.88; bg[..., 2] = bg[..., 2] * 1.04 + 0.01
    a = np.clip(subj * m + bg * (1 - m), 0, 1)

    # 5) gentle vignette
    H, W = a.shape[:2]; y = np.linspace(-1, 1, H)[:, None, None]; x = np.linspace(-1, 1, W)[None, :, None]
    a *= 1 - 0.16 * np.clip(x ** 2 * .8 + y ** 2 - .35, 0, None) * (1 - m)

    out = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=3))


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "thumb", "user_thumb.jpg")
    g = grade(Image.open(src))
    g.save(os.path.join(ROOT, "output", "thumbnail_full.png"))
    g.resize((1280, int(1280 * g.height / g.width)), Image.LANCZOS).resize((1280, 720), Image.LANCZOS).save(os.path.join(ROOT, "output", "thumbnail.png"))
    print("wrote output/thumbnail.png and output/thumbnail_full.png")
