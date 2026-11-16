import sys, os, json, subprocess, numpy as np, wave, multiprocessing as mp
sys.path.insert(0, os.path.dirname(__file__))
from edit import *

OUT = os.path.join(ROOT, "work/blocks"); os.makedirs(OUT, exist_ok=True)

def plan():
    blocks = []; t = 0.0
    for i, (k, key) in enumerate(ORDER):
        items, dur = build(k, key)
        n = int(round(dur * FPS)); dur = n / FPS
        blocks.append(dict(i=i, kind=k, key=key, start=t, dur=dur, n=n, sfx=[(t + a, nm, g) for it in items for (a, nm, g) in it.sfx()]))
        t += dur
    return blocks, t

def render_block(b):
    items, _ = build(b["kind"], b["key"])
    base = [x for x in items if x.base]; ov = [x for x in items if not x.base and not x.post]; post = [x for x in items if x.post]
    path = f"{OUT}/{b['i']:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), path], stdin=subprocess.PIPE)
    for f in range(b["n"]):
        t = f / FPS; c = np.zeros((H, W, 3), np.uint8)
        for x in base:
            if x.active(t): x.draw(c, t)
        for x in ov:
            if x.active(t): x.draw(c, t)
        for x in post:
            if x.active(t): c = x.apply(c, t)
        c = vignette(grain(c, f), .22)
        p.stdin.write(np.ascontiguousarray(c).tobytes())
    p.stdin.close(); p.wait()
    for x in base:
        if getattr(x, "r", None): x.r.close()
    return path

def load_wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", "48000", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def clip_audio(src, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", os.path.join(ROOT, SRC[src]["path"]), "-t", f"{b - a:.3f}", "-vn", "-f", "f32le", "-ac", "2", "-ar", "48000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); n = min(len(x), 960)
    x[:n] *= np.linspace(0, 1, n)[:, None]; x[-n:] *= np.linspace(1, 0, n)[:, None]; return x

def rms_speech(x):
    m = np.abs(x).mean(1); fr = m[:len(m) // 480 * 480].reshape(-1, 480).mean(1); fr = np.sort(fr)[len(fr) // 2:]; return fr.mean() + 1e-9

def mix(blocks, total):
    SR = 48000; out = np.zeros((int((total + 1) * SR), 2), np.float32)
    vo_rms = []
    for b in blocks:
        if b["kind"] == "vo":
            v = load_wav(os.path.join(ROOT, f"vo/{b['key']:02d}.wav")); s = int(b["start"] * SR)
            out[s:s + len(v)] += v[:len(out) - s]; vo_rms.append(rms_speech(v))
    target = np.median(vo_rms) * 1.0
    for b in blocks:
        if b["kind"] == "clip":
            src, a, e, _, _ = CLIPS[b["key"]]; x = clip_audio(src, a, e); x *= min(4.0, target / rms_speech(x))
            s = int(b["start"] * SR); out[s:s + len(x)] += x[:len(out) - s]
        else:  # quiet underwater ambience under narration
            bed = load_wav(os.path.join(ROOT, "sfx/underwater_bed.wav")) * 0.05; s = int(b["start"] * SR); L = int(b["dur"] * SR)
            reps = np.tile(bed, (L // len(bed) + 1, 1))[:L]; f = min(4800, L // 2)
            reps[:f] *= np.linspace(0, 1, f)[:, None]; reps[-f:] *= np.linspace(1, 0, f)[:, None]; out[s:s + L] += reps
    cache = {}
    for b in blocks:
        for (t, nm, g) in b["sfx"]:
            if nm not in cache: cache[nm] = load_wav(os.path.join(ROOT, f"sfx/{nm}.wav"))
            x = cache[nm] * (10 ** (g / 20)) * 0.55; s = max(0, int(t * SR)); out[s:s + len(x)] += x[:len(out) - s]
    out = out[:int(total * SR)]
    peak = np.abs(out).max(); out /= max(1.0, peak / 0.97)
    path = os.path.join(ROOT, "work/mix.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    return path

if __name__ == "__main__":
    blocks, total = plan()
    json.dump([{k: v for k, v in b.items() if k != "sfx"} for b in blocks], open(os.path.join(ROOT, "work/plan.json"), "w"), indent=1)
    print(f"{len(blocks)} blocks, total {total:.2f}s")
    sel = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 and sys.argv[1] != "all" else [b["i"] for b in blocks]
    todo = [b for b in blocks if b["i"] in sel]
    todo.sort(key=lambda b: -b["n"])
    with mp.Pool(4) as pool:
        for pth in pool.imap_unordered(render_block, todo): print("rendered", os.path.basename(pth), flush=True)
    if len(sel) == len(blocks):
        a = mix(blocks, total)
        with open(os.path.join(ROOT, "work/concat.txt"), "w") as f:
            for b in blocks: f.write(f"file '{OUT}/{b['i']:02d}.mp4'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(ROOT, "work/concat.txt"), "-i", a,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                        "-movflags", "+faststart", "-shortest", os.path.join(ROOT, "work/final.mp4")], check=True)
        print("FINAL done")
