"""Synthesised SFX library (no music). Writes 48 kHz stereo WAVs to /home/user/media/sfx."""
import os
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
OUT = '/home/user/media/sfx'
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)


def add(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


def place(out, c, s):
    s = max(0, s)
    if s >= len(out):
        return out
    k = min(len(c), len(out) - s)
    out[s:s + k] += c[:k]
    return out


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.01, r=0.3, curve=3.0):
    """attack/exp-release envelope, lengths in seconds"""
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na) ** 2
    rel = np.linspace(0, 1, n - na)
    e[na:] = (1 - rel) ** curve
    return e


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def sweep_filter(x, f0, f1, q=2.0, steps=60):
    """time-varying bandpass (block based)"""
    out = np.zeros_like(x)
    n = len(x)
    edges = np.linspace(0, n, steps + 1).astype(int)
    fs = np.geomspace(f0, f1, steps)
    zi = None
    for i in range(steps):
        fc = fs[i]
        lo, hi = fc / (1 + 1 / q), min(fc * (1 + 1 / q), SR / 2 - 100)
        sos = signal.butter(2, [lo, hi], btype='band', fs=SR, output='sos')
        if zi is None or zi.shape[0] != sos.shape[0]:
            zi = np.zeros((sos.shape[0], 2))
        seg, zi = signal.sosfilt(sos, x[edges[i]:edges[i + 1]], zi=zi)
        out[edges[i]:edges[i + 1]] = seg
    return out


def reverb(x, decay=0.35, mix=0.18, seed=0):
    x = x.copy(); f = min(len(x) // 3, int(SR * 0.012)); x[-f:] *= np.linspace(1, 0, f)
    r = np.random.default_rng(seed)
    n = int(SR * decay * 3)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / (SR * decay / 3))
    ir = lp(ir, 6000)
    ir /= np.abs(ir).sum() ** 0.5 * 30
    wet = signal.fftconvolve(x, ir)
    dry = np.concatenate([x, np.zeros(len(wet) - len(x))])
    return dry * (1 - mix) + wet * mix * 4


def stereo(x, width=0.0, seed=1):
    if width <= 0:
        return np.stack([x, x], 1)
    d = int(SR * 0.006 * width)
    l = x
    r_ = np.concatenate([np.zeros(d), x[:-d]]) if d else x
    return np.stack([l, r_], 1)


def save(name, x, peak=0.89):
    if x.ndim == 1:
        x = stereo(x)
    x = x / (np.abs(x).max() + 1e-9) * peak
    # tiny fade to kill clicks
    f = min(256, len(x) // 4)
    x[:f] *= np.linspace(0, 1, f)[:, None]
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    sf.write(f'{OUT}/{name}.wav', x.astype(np.float32), SR)


def whoosh(d=0.55, f0=300, f1=4500, seed=0, peak_at=0.6):
    r = np.random.default_rng(seed)
    n = int(SR * d)
    x = r.standard_normal(n)
    x = sweep_filter(x, f0, f1, q=1.6)
    p = int(n * peak_at)
    e = np.concatenate([np.linspace(0, 1, p) ** 2.2, np.linspace(1, 0, n - p) ** 1.6])
    x = x * e
    return reverb(x, 0.25, 0.15, seed)


def impact(d=1.6, f0=95, f1=38, seed=0):
    n = int(SR * d)
    tt = t(d)
    ph = 2 * np.pi * np.cumsum(np.geomspace(f0, f1, n)) / SR
    body = np.sin(ph) * np.exp(-tt * 3.2)
    sub = np.sin(2 * np.pi * 42 * tt) * np.exp(-tt * 2.2) * 0.6
    r = np.random.default_rng(seed)
    click = lp(r.standard_normal(n), 3500) * np.exp(-tt * 38) * 0.9
    crunch = bp(r.standard_normal(n), 150, 1200) * np.exp(-tt * 9) * 0.5
    x = np.tanh((body + sub + click + crunch) * 1.6)
    return reverb(x, 0.6, 0.22, seed)


def thud(d=0.45, seed=3):
    tt = t(d)
    ph = 2 * np.pi * np.cumsum(np.geomspace(140, 55, len(tt))) / SR
    r = np.random.default_rng(seed)
    x = np.sin(ph) * np.exp(-tt * 14) + lp(r.standard_normal(len(tt)), 2000) * np.exp(-tt * 60) * 0.7
    return reverb(np.tanh(x * 1.4), 0.2, 0.1)


def pop(f0=420, f1=1500, d=0.07):
    tt = t(d)
    ph = 2 * np.pi * np.cumsum(np.geomspace(f0, f1, len(tt))) / SR
    x = np.sin(ph) * env(len(tt), 0.002, d, 2.0)
    return reverb(x, 0.12, 0.12)


def bubbles(d=1.1, k=16, seed=5):
    r = np.random.default_rng(seed)
    out = np.zeros(int(SR * (d + 0.3)))
    for i in range(k):
        s = int(r.uniform(0, d) * SR * (i / k) ** 0.7 + r.uniform(0, 0.08) * SR)
        f0 = r.uniform(250, 700)
        b = pop(f0, f0 * r.uniform(2.2, 3.5), r.uniform(0.03, 0.08)) * r.uniform(0.35, 1)
        place(out, b, s)
    return out


def riser(d=1.8, seed=7):
    r = np.random.default_rng(seed)
    n = int(SR * d)
    x = sweep_filter(r.standard_normal(n), 200, 7000, q=3)
    tt = t(d)
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(110, 880, n)) / SR) * 0.25
    e = (tt / d) ** 2.5
    return (x + tone) * e


def reverse_swell(d=0.9, seed=8):
    r = np.random.default_rng(seed)
    n = int(SR * d)
    x = hp(r.standard_normal(n), 2500) * np.exp(-t(d) * 4.5)
    x = reverb(x, 0.5, 0.4)[:n]
    return x[::-1]


def click(d=0.03, f=3000, seed=0):
    r = np.random.default_rng(seed)
    tt = t(d)
    return bp(r.standard_normal(len(tt)), f * 0.6, min(f * 1.6, 20000)) * np.exp(-tt * 300)


def typewriter(n=8, gap=0.085, seed=9):
    r = np.random.default_rng(seed)
    out = np.zeros(int(SR * (n * gap + 0.4)))
    for i in range(n):
        s = int((i * gap + r.uniform(-0.012, 0.012)) * SR)
        c = add(click(0.04, r.uniform(1800, 3200), i), thud(0.06) * 0.25)
        place(out, c * r.uniform(0.6, 1), s)
    return reverb(out, 0.18, 0.12)


def type_one(seed=0):
    return reverb(add(click(0.04, 2600, seed), thud(0.06) * 0.25), 0.15, 0.1)


def shutter():
    a = add(click(0.025, 4200, 1), click(0.02, 1500, 2) * 0.6)
    gap = np.zeros(int(SR * 0.07))
    b = add(click(0.03, 3600, 3) * 0.8, click(0.03, 1100, 4) * 0.5)
    return reverb(np.concatenate([a, gap, b]), 0.15, 0.1)


def static(d=1.0, seed=10):
    r = np.random.default_rng(seed)
    n = int(SR * d)
    x = bp(r.standard_normal(n), 900, 9000) * (0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 60 * t(d))))
    crackle = (r.random(n) > 0.9993) * r.standard_normal(n) * 6
    return (x + lp(crackle, 5000)) * env(n, 0.02, d, 0.8)


def tv_off():
    tt = t(0.35)
    ph = 2 * np.pi * np.cumsum(np.geomspace(2400, 80, len(tt))) / SR
    x = np.sin(ph) * np.exp(-tt * 6) * 0.6
    x[:960] += static(0.02)[:960] * 0.8 if len(x) > 960 else 0
    return reverb(x, 0.2, 0.15)


def record_scratch(seed=12):
    r = np.random.default_rng(seed)
    d = 0.42
    n = int(SR * d)
    tt = t(d)
    rate = 1 + 0.9 * np.sin(2 * np.pi * 3.2 * tt) * np.exp(-tt * 1.5)
    noise = r.standard_normal(n)
    out = np.zeros(n)
    fcs = 600 + 2400 * np.abs(rate - 0.1)
    edges = np.linspace(0, n, 40).astype(int)
    for i in range(39):
        fc = fcs[edges[i]]
        out[edges[i]:edges[i + 1]] = bp(noise[edges[i]:edges[i + 1]], fc * 0.5, min(fc * 1.8, 20000))
    return out * env(n, 0.005, d, 1.5)


def projector(d=4.0, seed=13):
    r = np.random.default_rng(seed)
    n = int(SR * d)
    tt = t(d)
    out = lp(r.standard_normal(n), 400) * 0.25 + np.sin(2 * np.pi * 60 * tt) * 0.05
    for k in np.arange(0, d, 1 / 24):
        s = int((k + r.uniform(-0.002, 0.002)) * SR)
        c = click(0.012, r.uniform(1500, 2600), int(k * 100)) * r.uniform(0.4, 0.8)
        place(out, c, s)
    return out


def tick():
    return reverb(add(click(0.02, 3500, 4), click(0.015, 1200, 5) * 0.6), 0.25, 0.25)


def ding(f=1760):
    tt = t(1.6)
    x = sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * (2.5 + m)) for m, a in [(1, 1), (2.76, 0.35), (5.4, 0.15)])
    x[:300] *= np.linspace(0, 1, 300)
    return reverb(x, 0.4, 0.2)


def glitch(d=0.35, seed=14):
    r = np.random.default_rng(seed)
    n = int(SR * d)
    out = np.zeros(n)
    pos = 0
    while pos < n:
        L = int(r.uniform(0.01, 0.05) * SR)
        kind = r.integers(3)
        tt = np.arange(L) / SR
        if kind == 0:
            seg = np.sign(np.sin(2 * np.pi * r.uniform(80, 900) * tt))
        elif kind == 1:
            seg = r.standard_normal(L)
        else:
            seg = np.zeros(L)
        out[pos:pos + L] = seg[:n - pos] * r.uniform(0.3, 1)
        pos += L
    return np.round(lp(out, 7000) * 6) / 6


def buzz():
    tt = t(0.5)
    x = signal.sawtooth(2 * np.pi * 110 * tt) + signal.sawtooth(2 * np.pi * 116 * tt)
    return lp(x, 2200) * env(len(tt), 0.01, 0.5, 0.6)


def paper(seed=15):
    r = np.random.default_rng(seed)
    d = 0.5
    n = int(SR * d)
    x = bp(r.standard_normal(n), 1500, 8000) * (r.random(n) ** 3)
    x = lp(x, 9000) * env(n, 0.03, d, 1.2)
    return x


def stamp():
    return add(thud(0.5), click(0.03, 1800) * 0.6)


def heartbeat_soft():
    one = thud(0.3, 21) * 0.9
    two = thud(0.3, 22) * 0.6
    out = np.zeros(int(SR * 1.6))
    place(out, one, 0)
    place(out, two, int(SR * 0.28))
    return lp(out, 300)


def swish_short(seed=16):
    return whoosh(0.22, 800, 7000, seed, 0.5)


def tape_rip(seed=17):
    r = np.random.default_rng(seed)
    d = 0.45
    n = int(SR * d)
    am = (r.random(n) > 0.6).astype(float)
    am = lp(am, 600)
    x = bp(r.standard_normal(n), 900, 7000) * am * env(n, 0.01, d, 1.0)
    return reverb(x, 0.15, 0.1)


lib = {
    'whoosh1': whoosh(0.55, 300, 4500, 1),
    'whoosh2': whoosh(0.45, 500, 6000, 2, 0.5),
    'whoosh3': whoosh(0.75, 200, 3000, 3, 0.7),
    'whoosh_rev': whoosh(0.6, 4000, 300, 4, 0.75),
    'swish': swish_short(),
    'impact': impact(),
    'impact_big': impact(2.4, 80, 30, 2),
    'thud': thud(),
    'pop': pop(),
    'pop_hi': pop(700, 2400, 0.05),
    'bubbles': bubbles(),
    'riser': riser(),
    'riser_short': riser(0.9, 3),
    'reverse_swell': reverse_swell(),
    'typewriter': typewriter(),
    'type1': type_one(1),
    'type2': type_one(2),
    'shutter': shutter(),
    'static': static(),
    'static_short': static(0.35, 2),
    'tv_off': tv_off(),
    'scratch': record_scratch(),
    'projector': projector(),
    'tick': tick(),
    'ding': ding(),
    'glitch': glitch(),
    'buzz': buzz(),
    'paper': paper(),
    'stamp': stamp(),
    'heartbeat': heartbeat_soft(),
    'tape_rip': tape_rip(),
}
for k, v in lib.items():
    save(k, v)
print('wrote', len(lib), 'sfx to', OUT)
