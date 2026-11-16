"""Builds the episode soundtrack: voice chunks + SFX events + ambience beds (no music).
usage: mix.py <info.json> <out.wav>
"""
import json, sys, subprocess, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from sfx import make, SR, lp

info = json.load(open(sys.argv[1])); out = sys.argv[2]
N = int(SR * (info['duration'] + 0.5))
voice = np.zeros(N); fxb = np.zeros(N); beds = np.zeros(N)

def load(f):
    return np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']), np.float32).astype(np.float64)
def place(buf, x, t, g=1.0):
    i = int(round(t * SR));
    if i >= len(buf): return
    e = min(len(buf), i + len(x)); buf[i:e] += x[:e - i] * g

# voice: level-match chunks (speech RMS)
for v in info['voice']:
    x = load(v['file'])
    a = np.abs(x); thr = np.percentile(a, 60); rms = np.sqrt(np.mean(x[a > thr] ** 2)) if np.any(a > thr) else 0.1
    place(voice, x * (0.12 / max(rms, 1e-4)), v['t'])
cache = {}
SFX_GAIN = 0.32
for e in info['sfx']:
    n = e['n']
    if n.startswith('bed_'):
        place(beds, make(n, e['dur'] + 0.4), max(0, e['t'] - 0.2), e['g']); continue
    if 'dur' in e: x = make(n, e['dur'])
    else:
        if n not in cache: cache[n] = make(n)
        x = cache[n]
    place(fxb, x, e['t'], e['g'] * SFX_GAIN)
# duck beds + fx under voice
venv = lp(np.abs(voice), 8)
venv = venv / (venv.max() + 1e-9)
duck_b = 1 - 0.5 * np.clip(venv * 6, 0, 1)
duck_f = 1 - 0.25 * np.clip(venv * 6, 0, 1)
mixd = voice + fxb * duck_f + beds * duck_b
mixd = mixd / max(1.0, np.max(np.abs(mixd)) / 0.95)
st = np.stack([mixd, mixd], 1)
import wave
w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print('mixed', out, round(len(mixd) / SR, 2), 's')
