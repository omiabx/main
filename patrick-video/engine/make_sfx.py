"""Synthesize the video's SFX library from scratch (no samples, no licensing).

Run: python3 engine/make_sfx.py  -> writes 48 kHz mono WAVs into sfx/
"""
import os
import wave

import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(__file__), "..", "sfx")
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, r=0.2, shape=4.0):
    """Attack / exponential release envelope over n samples."""
    x = np.arange(n) / SR
    e = np.minimum(1.0, x / max(a, 1e-4))
    return e * np.exp(-shape * np.maximum(0, x - a) / max(r, 1e-4))


def lp(x, cut):
    """One-pole low-pass. cut may be a scalar or per-sample array (Hz)."""
    cut = np.broadcast_to(np.asarray(cut, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y


def hp(x, cut):
    return x - lp(x, cut)


def bp(x, lo, hi):
    return lp(hp(x, lo), hi)


def noise(d):
    return rng.standard_normal(int(SR * d))


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def save(name, x, peak=0.89):
    x = norm(np.asarray(x, dtype=float), peak)
    fade = min(len(x), int(0.004 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def pad(x, d):
    out = np.zeros(int(SR * d))
    out[: len(x)] += x[: len(out)]
    return out


def mix_at(base, x, at):
    i = int(at * SR)
    end = min(len(base), i + len(x))
    base[i:end] += x[: end - i]
    return base


def whoosh(d=0.55, rev=False):
    n = noise(d)
    x = t(d) / d
    bell = np.sin(np.pi * x) ** 2
    cut = 300 + 5200 * np.sin(np.pi * x) ** 1.5
    y = lp(hp(n, 120), cut) * bell
    return y[::-1] if rev else y


def impact(d=1.4):
    tt = t(d)
    f = 38 + 70 * np.exp(-tt * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.002, 0.45, 5)
    click = lp(noise(d), 2500) * env(len(tt), 0.001, 0.03, 6)
    tail = lp(noise(d), 400) * env(len(tt), 0.01, 0.6, 5) * 0.4
    return body + 0.5 * click + tail


def thud(d=0.35, f0=85):
    tt = t(d)
    f = f0 + 60 * np.exp(-tt * 40)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, 0.09, 5)
    s += lp(noise(d), 1800) * env(len(tt), 0.001, 0.025, 6) * 0.8
    return s


def paper(d=0.45):
    n = noise(d)
    grain = (rng.random(len(n)) > 0.985) * rng.standard_normal(len(n)) * 3
    x = t(d) / d
    shape = np.sin(np.pi * x) ** 0.8
    return bp(n * 0.5 + grain, 900, 6500) * shape


def type_key(d=0.07):
    tt = t(d)
    k = bp(noise(d), 1500, 7000) * env(len(tt), 0.0005, 0.012, 6)
    body = np.sin(2 * np.pi * 180 * tt) * env(len(tt), 0.0005, 0.02, 6) * 0.6
    return k + body


def bell(d=1.2, f=2093):
    tt = t(d)
    s = sum(np.sin(2 * np.pi * f * m * tt) * a for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.2)])
    return s * env(len(tt), 0.001, 0.5, 5)


def shutter(d=0.25):
    a = bp(noise(0.03), 2000, 9000) * env(int(0.03 * SR), 0.0005, 0.01, 6)
    b = bp(noise(0.05), 1200, 7000) * env(int(0.05 * SR), 0.0005, 0.02, 6) * 0.8
    out = np.zeros(int(SR * d))
    mix_at(out, a, 0)
    mix_at(out, b, 0.085)
    return out


def scratch(d=0.6):
    tt = t(d)
    rate = np.interp(tt, [0, 0.12, 0.3, 0.45, d], [1.0, -1.6, 1.4, -0.8, 0])
    ph = np.cumsum(rate) / SR
    tone = np.sin(2 * np.pi * 220 * ph * 6) * 0.5
    grit = bp(noise(d), 600, 4000) * np.abs(rate)
    return (tone + grit) * env(len(tt), 0.003, 0.4, 3)


def beep(d=0.18, f=1000):
    tt = t(d)
    e = np.minimum(1, tt / 0.004) * np.minimum(1, (d - tt) / 0.01)
    return np.sin(2 * np.pi * f * tt) * e


def phone_ring(d=2.2):
    out = np.zeros(int(SR * d))
    for start in (0, 0.45):
        tt = t(0.4)
        trem = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 20 * tt))
        tone = (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * trem
        mix_at(out, tone * np.minimum(1, tt / 0.01), start)
    return out


def hangup(d=0.3):
    return thud(d, 260) * 0.7 + pad(type_key(0.06), d)


def printer(d=1.6):
    out = np.zeros(int(SR * d))
    lines = int(d / 0.09)
    for i in range(lines):
        tt = t(0.07)
        buzz = np.sign(np.sin(2 * np.pi * (620 + 40 * (i % 3)) * tt)) * 0.25
        buzz = lp(buzz + bp(noise(0.07), 1500, 6000) * 0.3, 5000) * env(len(tt), 0.002, 0.05, 3)
        mix_at(out, buzz, i * 0.09)
    return out


def pin(d=0.25):
    return thud(d, 420) * 0.6 + pad(bp(noise(0.02), 3000, 9000) * env(int(0.02 * SR), 0.0005, 0.006, 6), d)


def riser(d=3.0):
    tt = t(d)
    x = tt / d
    cut = 200 + 7000 * x ** 2
    n = lp(hp(noise(d), 150), cut) * x ** 1.5
    f = 110 * 2 ** (3 * x)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * x ** 2 * 0.3
    return n + tone


def pop(d=0.12):
    tt = t(d)
    f = 900 * np.exp(-tt * 30) + 250
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.0005, 0.04, 6)


def glitch(d=0.35):
    out = np.zeros(int(SR * d))
    pos = 0
    while pos < len(out):
        seg = int(SR * rng.uniform(0.008, 0.03))
        kind = rng.integers(3)
        tt = np.arange(seg) / SR
        if kind == 0:
            s = np.sign(np.sin(2 * np.pi * rng.uniform(200, 2000) * tt))
        elif kind == 1:
            s = rng.standard_normal(seg)
        else:
            s = np.zeros(seg)
        out[pos:pos + seg] = s[: len(out) - pos] * 0.6
        pos += seg
    return lp(out, 6000)


def room_tone(d=10.0):
    return lp(noise(d), 300) * 0.02 + lp(noise(d), 2500) * 0.004


def main():
    save("whoosh", whoosh())
    save("whoosh_short", whoosh(0.3))
    save("whoosh_rev", whoosh(0.6, rev=True))
    save("impact", impact())
    save("thud", thud())
    folder = pad(paper(0.3), 0.8)
    mix_at(folder, thud(0.5, 70), 0.22)
    save("folder_slam", folder)
    stamp = pad(thud(0.3, 120), 0.5)
    mix_at(stamp, bp(noise(0.05), 800, 4000) * env(int(0.05 * SR), 0.001, 0.02, 6) * 0.5, 0.0)
    save("stamp", stamp)
    save("paper_slide", paper(0.5))
    save("type_key", type_key(), peak=0.6)
    typing = np.zeros(int(SR * 1.6))
    at = 0.0
    while at < 1.45:
        mix_at(typing, type_key() * rng.uniform(0.6, 1.0), at)
        at += rng.uniform(0.055, 0.11)
    save("typing", typing, peak=0.7)
    save("typewriter_bell", bell())
    save("shutter", shutter())
    save("record_scratch", scratch())
    save("monitor_beep", pad(beep(), 0.3), peak=0.5)
    save("flatline", pad(beep(2.5), 2.8), peak=0.5)
    save("phone_ring", phone_ring(), peak=0.6)
    save("hangup", hangup())
    save("receipt_printer", printer(), peak=0.6)
    save("pin", pin())
    save("riser", riser())
    save("pop", pop())
    save("glitch", glitch(), peak=0.6)
    save("room_tone", room_tone(), peak=0.08)
    print("wrote", len(os.listdir(OUT)), "files to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
