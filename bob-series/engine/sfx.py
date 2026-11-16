"""Procedural SFX for the series (no music). All sounds synthesized; deterministic.
usage: sfx.py <outdir>   -> writes one-shot wavs; loops/beds are generated on demand by mix.py via make(name, dur)
"""
import numpy as np, sys, os, wave
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)
T = lambda d: np.arange(int(SR * d)) / SR

def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def env(n, a=0.002, d=0.1):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d); return e
def noise(d): return rng.standard_normal(int(SR * d))
def sweep(f0, f1, d, kind='sin', curve=1.0):
    t = T(d); f = f0 + (f1 - f0) * (t / d) ** curve; ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if kind == 'sin' else np.sign(np.sin(ph)) * 0.6
def sq(f, d, duty=0.5):
    t = T(d); return np.where((t * f) % 1 < duty, 0.5, -0.5)
def norm(x, p=0.9): m = np.max(np.abs(x)) or 1; return x / m * p
def pad(x, d): return np.concatenate([x, np.zeros(max(0, int(SR * d) - len(x)))])
def at(base, x, t, g=1.0):
    i = int(t * SR); end = min(len(base), i + len(x)); base[i:end] += x[:end - i] * g; return base

# ---------------- one-shots ----------------
def pop():
    x = sweep(380, 980, 0.09) * env(int(SR * 0.09), 0.002, 0.035)
    c = hp(noise(0.012), 2000) * env(int(SR * 0.012), 0.0005, 0.003) * 0.3
    return norm(pad(x, 0.12) + pad(c, 0.12), 0.8)
def tick(): return norm(lp(sq(2200, 0.03, 0.3), 6000) * env(int(SR * 0.03), 0.001, 0.008), 0.6)
def lamp():
    a = lp(sq(660, 0.05), 5000) * env(int(SR * 0.05), 0.001, 0.02)
    b = lp(sq(990, 0.07), 5000) * env(int(SR * 0.07), 0.001, 0.03)
    th = np.sin(2 * np.pi * 90 * T(0.08)) * env(int(SR * 0.08), 0.001, 0.03)
    out = np.zeros(int(SR * 0.16)); at(out, a, 0); at(out, b, 0.045); at(out, th, 0, 0.6); return norm(out, 0.7)
def tile():
    t = T(0.12); x = (np.sin(2 * np.pi * 420 * t) + 0.5 * np.sin(2 * np.pi * 1180 * t)) * env(len(t), 0.0008, 0.025)
    n = bp(noise(0.12), 800, 4000) * env(len(t), 0.0005, 0.006) * 0.6
    return norm(x + n, 0.6)
def block():
    t = T(0.35); x = np.sin(2 * np.pi * (110 - 40 * t / 0.35) * t) * env(len(t), 0.002, 0.09)
    n = lp(noise(0.35), 900) * env(len(t), 0.001, 0.03) * 0.8
    return norm(x + n, 0.85)
def whoosh(d=0.55, f0=250, f1=2600, f2=500):
    n = noise(d); out = np.zeros_like(n); seg = 512
    for i in range(0, len(n), seg):
        p = i / len(n); fc = f0 + (f1 - f0) * (p / 0.6) if p < 0.6 else f1 + (f2 - f1) * ((p - 0.6) / 0.4)
        out[i:i + seg] = n[i:i + seg]
    x = bp(n, 200, 3500) * 0.5 + lp(n, 900) * 0.5
    e = np.sin(np.pi * np.clip(T(d) / d, 0, 1)) ** 2
    return norm(x * e, 0.55)
def zoom(): return norm(whoosh(0.7) * 0.7 + 0.25 * sweep(180, 1100, 0.7, curve=2) * np.sin(np.pi * T(0.7) / 0.7) ** 2, 0.6)
def zoomout(): return norm(whoosh(0.7) * 0.7 + 0.25 * sweep(1100, 180, 0.7, curve=0.5) * np.sin(np.pi * T(0.7) / 0.7) ** 2, 0.6)
def glitch():
    out = np.zeros(int(SR * 0.45)); t = 0
    while t < 0.42:
        d = rng.uniform(0.015, 0.05); f = rng.choice([180, 330, 520, 870, 1400, 2100])
        x = np.round(sq(f, d, rng.uniform(0.2, 0.6)) * 4) / 4 * env(int(SR * d), 0.0005, d)
        at(out, x, t, rng.uniform(0.4, 1)); t += d * rng.uniform(0.6, 1.2)
    return norm(lp(out, 7000), 0.6)
def sparkle():
    out = np.zeros(int(SR * 0.7))
    for k in range(7):
        f = rng.uniform(2200, 4800); d = 0.35; x = np.sin(2 * np.pi * f * T(d)) * env(int(SR * d), 0.001, 0.07)
        at(out, x, k * 0.06, rng.uniform(0.4, 1))
    return norm(out, 0.45)
def step():
    x = lp(noise(0.09), rng.uniform(900, 1400)) * env(int(SR * 0.09), 0.004, 0.025)
    return norm(x, 0.5)
def flagpop():
    out = np.zeros(int(SR * 0.5)); at(out, pop(), 0, 0.7)
    fl = bp(noise(0.35), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * T(0.35))) * env(int(SR * 0.35), 0.01, 0.12)
    at(out, fl, 0.03, 0.4); return norm(out, 0.7)
def flag():
    out = np.zeros(int(SR * 0.9))
    th = np.sin(2 * np.pi * 70 * T(0.25)) * env(int(SR * 0.25), 0.001, 0.06) + lp(noise(0.25), 500) * env(int(SR * 0.25), 0.001, 0.02)
    at(out, th, 0, 1.0)
    fl = bp(noise(0.7), 300, 3000) * (0.55 + 0.45 * np.sin(2 * np.pi * 16 * T(0.7))) * env(int(SR * 0.7), 0.02, 0.25)
    at(out, fl, 0.08, 0.45); return norm(out, 0.85)
def shatter():
    out = np.zeros(int(SR * 0.8))
    for k in range(40):
        x = tile() * rng.uniform(0.2, 0.7); at(out, x[: int(SR * 0.08)], rng.uniform(0, 0.6) ** 1.3)
    return norm(out + whoosh(0.8) * 0.4, 0.7)
def settle():
    out = np.zeros(int(SR * 0.7))
    for k in range(25):
        x = tile() * rng.uniform(0.2, 0.6); at(out, x[: int(SR * 0.08)], 0.6 - rng.uniform(0, 0.6) ** 1.5)
    return norm(out, 0.6)
def chime():
    t = T(1.1); x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dcy) for f, a, dcy in [(1318, 1, 0.35), (1976, 0.5, 0.25), (2637, 0.25, 0.18)])
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dcy) for f, a, dcy in [(1760, 1, 0.4), (2637, 0.45, 0.25)])
    out = np.zeros(int(SR * 1.3)); at(out, x * env(len(t), 0.002, 9), 0); at(out, y * env(len(t), 0.002, 9), 0.11, 0.8)
    return norm(out, 0.5)
def buzz():
    t = T(0.38); x = (sq(110, 0.38) + sq(117, 0.38)) * env(len(t), 0.005, 0.25); return norm(lp(x, 2500), 0.6)
def split():
    out = np.zeros(int(SR * 0.7)); at(out, whoosh(0.5), 0, 0.6)
    z = hp(noise(0.3), 3000) * env(int(SR * 0.3), 0.001, 0.06); at(out, z, 0.05, 0.5)
    at(out, sweep(300, 1500, 0.25) * env(int(SR * 0.25), 0.002, 0.08), 0.02, 0.5); return norm(out, 0.7)
def lighton():
    z = bp(noise(0.08), 1500, 6000) * env(int(SR * 0.08), 0.001, 0.02)
    p = np.sin(2 * np.pi * 1046 * T(0.3)) * env(int(SR * 0.3), 0.002, 0.08)
    h = np.sin(2 * np.pi * 120 * T(0.3)) * env(int(SR * 0.3), 0.01, 0.12) * 0.4
    out = np.zeros(int(SR * 0.35)); at(out, z, 0, 0.6); at(out, p, 0.01, 0.6); at(out, h, 0); return norm(out, 0.6)
def lightoff():
    p = sweep(700, 200, 0.18) * env(int(SR * 0.18), 0.002, 0.07); return norm(lp(p, 3000), 0.5)
def pick():
    out = np.zeros(int(SR * 0.3)); at(out, sweep(1200, 500, 0.12) * env(int(SR * 0.12), 0.001, 0.05), 0)
    at(out, tile()[: int(SR * 0.08)], 0.1, 0.6); return norm(out, 0.6)
def boop():
    t = T(0.45); f = 620 - 300 * (t / 0.45) + 25 * np.sin(2 * np.pi * 14 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.005, 0.2); return norm(x, 0.6)
def scan():
    x = bp(noise(0.3), 2000, 8000) * np.sin(np.pi * T(0.3) / 0.3) ** 2; return norm(x, 0.3)
def rumble():
    x = lp(noise(2.2), 140, 4) * np.sin(np.pi * T(2.2) / 2.2) ** 1.5
    return norm(x, 0.8)

ONESHOT = dict(pop=pop, tick=tick, lamp=lamp, tile=tile, block=block, whoosh=whoosh, zoom=zoom, zoomout=zoomout, glitch=glitch,
               sparkle=sparkle, step=step, flagpop=flagpop, flag=flag, shatter=shatter, settle=settle, chime=chime, buzz=buzz,
               split=split, lighton=lighton, lightoff=lightoff, pick=pick, boop=boop, scan=scan, rumble=rumble)

# ---------------- duration-based ----------------
def count(d):
    out = np.zeros(int(SR * (d + 0.1))); t = 0.0
    while t < d:
        at(out, tick(), t, 0.7); t += 0.12 * (1 - 0.85 * t / d) + 0.015
    return out
def flicker(d):
    out = np.zeros(int(SR * (d + 0.2))); t = 0.0
    while t < d: at(out, lamp(), t, rng.uniform(0.25, 0.5)); t += rng.uniform(0.07, 0.11)
    return out
def paintloop(d):
    out = np.zeros(int(SR * (d + 0.2))); t = 0.0
    while t < d: at(out, tile(), t, rng.uniform(0.2, 0.45)); t += rng.uniform(0.03, 0.07)
    return out
def bed(kind, d):
    n = int(SR * d)
    if kind == 'canyon' or kind == 'map':
        w = lp(rng.standard_normal(n), 500 if kind == 'canyon' else 380, 2)
        m = 0.55 + 0.45 * np.sin(2 * np.pi * np.arange(n) / SR * 0.13 + rng.uniform(0, 6)) * np.sin(2 * np.pi * np.arange(n) / SR * 0.047 + 1)
        x = w * m
        g = 0.09 if kind == 'canyon' else 0.06
    else:
        t = np.arange(n) / SR
        x = 0.4 * np.sin(2 * np.pi * 55 * t) + 0.2 * np.sin(2 * np.pi * 110.4 * t) + lp(rng.standard_normal(n), 300) * 0.6
        g = 0.035
    x = x / (np.std(x) + 1e-9) * g
    f = min(n // 2, int(SR * 0.35)); ramp = np.linspace(0, 1, f); x[:f] *= ramp; x[-f:] *= ramp[::-1]
    return x
DUR = dict(count=count, flicker=flicker, paintloop=paintloop,
           bed_canyon=lambda d: bed('canyon', d), bed_map=lambda d: bed('map', d), bed_stage=lambda d: bed('stage', d))

def make(name, dur=None):
    if name in ONESHOT: return ONESHOT[name]()
    return DUR[name](dur)

def write(path, x):
    x = np.clip(x, -1, 1); w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype(np.int16).tobytes()); w.close()

if __name__ == '__main__':
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    for k in ONESHOT: write(os.path.join(od, k + '.wav'), make(k))
    print('wrote', len(ONESHOT))
