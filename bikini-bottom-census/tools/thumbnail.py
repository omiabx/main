"""Thumbnail: huge crowd + blurred population counter + shocked SpongeBob sticker (1280x720)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage as ndi
from engine import font, grab, frame_fill
from data import S2, CROWD_T, SCR

TW, TH = 1280, 720
OUT = os.path.join(SCR, "thumb")

def sticker(cut, outline=14):
    a = np.asarray(cut.getchannel("A")) > 40
    big = ndi.binary_dilation(a, iterations=outline)
    w, h = cut.size
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    white = Image.new("RGBA", (w, h), (255, 255, 255, 255)); white.putalpha(Image.fromarray((big * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1)))
    st.alpha_composite(white); st.alpha_composite(cut)
    return st

def shadowed(layer, off=(10, 14), blur=16, alpha=170):
    w, h = layer.size; pad = blur * 3
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 255)); sh.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha / 255)))
    out.paste(sh, (pad + off[0], pad + off[1]), sh); out = out.filter(ImageFilter.GaussianBlur(blur)); out.alpha_composite(layer, (pad, pad))
    return out

def counter_box(digits="46,853", blur=17, w=760):
    h = 300
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(box)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 28, fill=(18, 20, 30, 245), outline=(220, 40, 40), width=10)
    d.text((w / 2, 62), "POPULATION", font=font("anton", 70), fill=(255, 255, 255), anchor="mm")
    # odometer tiles
    tiles = Image.new("RGBA", (w, h), (0, 0, 0, 0)); td = ImageDraw.Draw(tiles)
    chars = list(digits); n = len(chars); tw = (w - 80) / n
    for i, ch in enumerate(chars):
        x0 = 40 + i * tw
        if ch == ",":
            td.text((x0 + tw / 2, 205), ",", font=font("anton", 120), fill=(240, 236, 226), anchor="mm"); continue
        td.rounded_rectangle([x0 + 6, 115, x0 + tw - 6, 280], 12, fill=(243, 238, 224))
        td.text((x0 + tw / 2, 197), ch, font=font("anton", 140), fill=(20, 20, 24), anchor="mm")
    tiles = tiles.filter(ImageFilter.GaussianBlur(blur))
    box.alpha_composite(tiles)
    return box

def build(variant="A"):
    crowd = frame_fill(grab(S2, CROWD_T), 1.0, 0.5, 0.45, sharpen=True).resize((TW, TH), Image.LANCZOS)
    crowd = ImageEnhance.Color(crowd).enhance(1.25)
    crowd = ImageEnhance.Contrast(crowd).enhance(1.08)
    # darken edges + left-to-right darkening so text area pops
    a = np.asarray(crowd).astype(np.float32)
    y, x = np.ogrid[:TH, :TW]; r = np.sqrt(((x - TW * 0.45) / (TW * 0.6)) ** 2 + ((y - TH * 0.5) / (TH * 0.7)) ** 2)
    a *= np.clip(1.12 - 0.55 * r ** 2, 0.35, 1.0)[..., None]
    base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    sb = sticker(Image.open(os.path.join(OUT, "sb_cut.png")))
    if variant == "A":
        cb = shadowed(counter_box())
        cb = cb.resize((int(cb.width * 0.95), int(cb.height * 0.95)), Image.LANCZOS).rotate(-2, resample=Image.BICUBIC, expand=True)
        base.alpha_composite(cb, (30, 20))
        s = sb.resize((int(sb.width * 0.6), int(sb.height * 0.6)), Image.LANCZOS)
        s = shadowed(s)
        base.alpha_composite(s, (TW - s.width + 40, TH - s.height + 70))
    else:  # B: counter centered high, SpongeBob bottom-left, red arrow
        cb = shadowed(counter_box())
        cb = cb.resize((int(cb.width * 0.95), int(cb.height * 0.95)), Image.LANCZOS).rotate(2, resample=Image.BICUBIC, expand=True)
        base.alpha_composite(cb, (TW - cb.width - 10, 25))
        s = shadowed(sb.resize((int(sb.width * 0.6), int(sb.height * 0.6)), Image.LANCZOS))
        base.alpha_composite(s, (-60, TH - s.height + 70))
        d = ImageDraw.Draw(base)
        d.line([(445, 455), (560, 345)], fill=(230, 30, 30), width=20)
        d.polygon([(592, 312), (512, 336), (566, 392)], fill=(230, 30, 30))
    return base.convert("RGB")

if __name__ == "__main__":
    for v in ("A", "B"):
        im = build(v); p = os.path.join(OUT, f"thumbnail_{v}.jpg"); im.save(p, quality=93); print(p, os.path.getsize(p))
