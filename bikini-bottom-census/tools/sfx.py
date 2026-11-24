"""Synthesize a small SFX library (48 kHz, stereo WAV). No music anywhere."""
import numpy as np, os, sys
from scipy import signal
from scipy.io import wavfile

SR = 48000
OUT = sys.argv[1] if len(sys.argv) > 1 else "sfx"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

def t(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, r=None, curve=4.0):
    e = np.ones(n)
    na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    if r is None:
        e *= np.exp(-curve * np.linspace(0, 1, n))
    return e
def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)
def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low"); return signal.lfilter(b, a, x)
def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high"); return signal.lfilter(b, a, x)
def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1; return x / m * peak
def save(name, x, width=0.0):
    x = norm(x)
    if x.ndim == 1:
        d = int(width * SR / 1000)
        R = np.concatenate([np.zeros(d), x])[: len(x)] if d else x
        x = np.stack([x, R], 1)
    wavfile.write(os.path.join(OUT, name + ".wav"), SR, (x * 32767).astype(np.int16))

def sweep_noise(d, f0, f1, q=0.35):
    n = int(SR * d); x = rng.standard_normal(n); y = np.zeros(n); blk = 512
    for i in range(0, n, blk):
        fr = i / n; fc = f0 * (f1 / f0) ** fr
        lo, hi = fc * (1 - q), min(fc * (1 + q), SR / 2 - 100)
        b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
        y[i:i + blk] = signal.lfilter(b, a, x[max(0, i - 2048):i + blk])[-len(x[i:i + blk]):]
    return y

# whooshes
w = sweep_noise(0.45, 300, 4000) * np.sin(np.linspace(0, np.pi, int(SR * 0.45))) ** 2
save("whoosh", w, 8)
save("whoosh_down", sweep_noise(0.5, 3500, 250) * np.sin(np.linspace(0, np.pi, int(SR * 0.5))) ** 1.5, 8)
save("whoosh_short", sweep_noise(0.22, 800, 5000) * np.sin(np.linspace(0, np.pi, int(SR * 0.22))) ** 2, 5)

# pop (cartoon bubble pop)
tt = t(0.09); f = 900 * np.exp(-tt * 18) + 300
save("pop", np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, curve=9))
tt = t(0.07); f = 1400 * np.exp(-tt * 25) + 500
save("pop_hi", np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, curve=10))

# click / tick
x = hp(rng.standard_normal(int(SR * 0.012)), 2000) * env(int(SR * 0.012), 0.0005, curve=12)
save("click", x)
x = np.sin(2 * np.pi * 2600 * t(0.025)) * env(int(SR * 0.025), 0.0005, curve=14)
save("tick", x)

# stamp: thud + paper slap
tt = t(0.35)
thud = np.sin(2 * np.pi * (90 * np.exp(-tt * 8) + 45) * tt) * np.exp(-tt * 14)
slap = bp(rng.standard_normal(len(tt)), 400, 3000) * np.exp(-tt * 60)
save("stamp", thud * 1.0 + slap * 0.8)

# boom (low impact, long tail)
tt = t(2.2)
boom = np.sin(2 * np.pi * (55 * np.exp(-tt * 1.5) + 28) * tt) * np.exp(-tt * 2.2)
rumble = lp(rng.standard_normal(len(tt)), 140) * np.exp(-tt * 1.6) * 3
save("boom", boom + rumble, 12)

# heavy hit (shorter)
tt = t(0.8)
save("hit", np.sin(2 * np.pi * (70 * np.exp(-tt * 6) + 38) * tt) * np.exp(-tt * 6) + lp(rng.standard_normal(len(tt)), 300) * np.exp(-tt * 12) * 1.5, 6)

# ding (bell partials)
tt = t(1.6)
bell = sum(a * np.sin(2 * np.pi * 1320 * r * tt) * np.exp(-tt * d) for a, r, d in
           [(1, 1, 2.2), (0.5, 2.76, 3.5), (0.3, 5.4, 5), (0.2, 8.93, 7)])
save("ding", bell, 4)

# riser (rising filtered noise + tone)
tt = t(1.6)
r = sweep_noise(1.6, 200, 6000, 0.25) * np.linspace(0, 1, len(tt)) ** 2
save("riser", r + 0.25 * np.sin(2 * np.pi * np.cumsum(200 + 900 * np.linspace(0, 1, len(tt)) ** 2) / SR) * np.linspace(0, 1, len(tt)) ** 3, 10)

# typewriter key + carriage bell
tt = t(0.06)
key = bp(rng.standard_normal(len(tt)), 1500, 6000) * np.exp(-tt * 90) + np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 70) * 0.6
save("typekey", key)

# cash register: drawer clunk + bell
tt = t(1.0)
clunk = lp(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 25)
save("register", clunk * 0.9 + np.concatenate([np.zeros(int(SR * 0.08)), bell[: len(tt) - int(SR * 0.08)]]) * 0.6)

# cricket chirps
tt = t(1.6); cr = np.zeros(len(tt))
for k in range(2):
    s = int(SR * (0.15 + 0.7 * k))
    for j in range(4):
        st = s + int(SR * 0.045 * j); nn = int(SR * 0.03)
        cr[st:st + nn] += np.sin(2 * np.pi * 4300 * np.arange(nn) / SR) * np.hanning(nn)
save("cricket", cr)

# wind / underwater ambience bed (8 s, loopable-ish)
tt = t(8.0)
wnd = lp(rng.standard_normal(len(tt)), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * tt))
save("wind", wnd, 20)
amb = lp(rng.standard_normal(len(tt)), 220) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * tt))
save("ocean_rumble", amb, 25)

# tinnitus ring
tt = t(2.5)
save("ring", np.sin(2 * np.pi * 7200 * tt) * np.minimum(1, tt * 4) * np.exp(-tt * 0.6))

# marker / chalk scribble
tt = t(0.9)
sc = bp(rng.standard_normal(len(tt)), 2500, 9000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * tt)))
save("scribble", sc * np.minimum(1, tt * 20) * np.minimum(1, (0.9 - tt) * 20))

# camera shutter (freeze frame)
tt = t(0.12)
sh = hp(rng.standard_normal(len(tt)), 1500) * (np.exp(-tt * 80) + 0.7 * np.exp(-np.maximum(0, tt - 0.05) * 90) * (tt > 0.05))
save("shutter", sh)

# record scratch
tt = t(0.5)
f = 600 + 500 * np.sin(2 * np.pi * 3 * tt)
scr = bp(rng.standard_normal(len(tt)), 300, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR))
save("scratch", scr * np.exp(-tt * 3))

# glitch (short digital stutter)
gl = np.concatenate([np.sign(np.sin(2 * np.pi * fr * t(0.03))) * 0.5 for fr in [220, 880, 440, 1760, 330, 110]])
save("glitch", gl * np.linspace(1, 0.4, len(gl)))

# heartbeat (two thumps)
tt = t(0.9); hb = np.zeros(len(tt))
for off, amp in [(0, 1), (0.22, 0.7)]:
    s = int(SR * off); nn = int(SR * 0.18); x = np.arange(nn) / SR
    hb[s:s + nn] += amp * np.sin(2 * np.pi * 52 * x) * np.exp(-x * 25)
save("heartbeat", hb)

# counter roll (fast mechanical ticks, 1.6 s, accelerating)
tt = t(1.6); cnt = np.zeros(len(tt)); pos = 0.0; gap = 0.09
while pos < 1.55:
    s = int(pos * SR); nn = int(SR * 0.01)
    cnt[s:s + nn] += hp(rng.standard_normal(nn), 3000) * np.exp(-np.arange(nn) / SR * 400)
    pos += gap; gap = max(0.022, gap * 0.9)
save("counter", cnt)

# swish (fast UI swipe)
save("swish", sweep_noise(0.15, 2000, 8000, 0.3) * np.hanning(int(SR * 0.15)), 4)

print("ok", sorted(os.listdir(OUT)))
