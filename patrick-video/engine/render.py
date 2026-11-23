"""Render the full video: frames (parallel) + audio mix -> out/patrick_video.mp4

python3 engine/render.py            full render
python3 engine/render.py --from 120 --to 150   render a preview range
python3 engine/render.py --frames 10,95,400    write still PNGs for checking
"""
import argparse
import math
import multiprocessing as mp
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import cards as C  # noqa: E402
import edl  # noqa: E402
from gfx import W, H  # noqa: E402
from timeline import Timeline  # noqa: E402

FPS = 30
SR = 48000
ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
SHAKERS = {"impact": 18, "thud": 10, "stamp": 9, "folder_slam": 14}


class Show:
    def __init__(self):
        self.tl = Timeline()
        self.cards, self.dates, self.chapters, self.sfx, self.monitor = edl.build(self.tl)
        self.starts = [c.t0 for c in self.cards]
        self.shakes = [(t, SHAKERS[n] * min(1.0, g + 0.3)) for t, n, g in self.sfx if n in SHAKERS]
        rng = np.random.default_rng(3)
        self.grain = [Image.fromarray(np.dstack([np.full((H, W), 128, np.uint8)] * 3 + [
            (rng.random((H, W)) * 14).astype(np.uint8)]), "RGBA") for _ in range(3)]

    def card_at(self, t):
        i = max(0, np.searchsorted(self.starts, t, side="right") - 1)
        return i, self.cards[i]

    def monitor_state(self, t):
        st = None
        for tt, level, label, flat in self.monitor:
            if t >= tt:
                st = None if label is None else (level, label, flat)
        return st

    def render_card(self, card, t):
        bg = card.background()
        frame = bg.copy() if bg is not None else Image.new("RGBA", (W, H), (0, 0, 0, 255))
        life = t - card.t0
        card.content(frame, t, life)
        card.draw_decor(frame, t)
        return frame

    def frame(self, t):
        i, card = self.card_at(t)
        life = t - card.t0
        frame = self.render_card(card, t)
        if card.enter == "slide" and life < 0.28 and i > 0 and not isinstance(self.cards[i - 1], C.Clip):
            k = C.ease_out(life / 0.28)
            prev = self.render_card(self.cards[i - 1], t)
            both = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            both.alpha_composite(prev, (int(-k * W) if k < 1 else 0, 0)) if k < 1 else None
            both.paste(frame, (int((1 - k) * W), 0))
            frame = both
        clipish = isinstance(card, (C.Clip, C.Black, C.EndScreen))
        for t0, d, title, season in self.dates:
            C.date_card_overlay(frame, t, t0, d, title, season)
        for t0, n, title in self.chapters:
            C.chapter_overlay(frame, t, t0, n, title)
        if not clipish:
            C.monitor_overlay(frame, t, self.monitor_state(t))
        # camera shake
        dx = dy = 0
        for t0, amp in self.shakes:
            if t0 <= t < t0 + 0.16:
                kk = 1 - (t - t0) / 0.16
                dx += int(math.sin(t * 210) * amp * kk)
                dy += int(math.cos(t * 170) * amp * kk)
        if dx or dy:
            moved = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            moved.paste(frame, (dx, dy))
            frame = moved
        if not isinstance(card, C.Clip):
            frame.alpha_composite(self.grain[int(t * FPS) % 3])
        return frame.convert("RGB")


# ------------------------------------------------------------------ video
def render_range(args):
    idx, f0, f1, path = args
    show = Show()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-g", "60", path], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        ff.stdin.write(show.frame(fi / FPS).tobytes())
        if (fi - f0) % 900 == 0:
            print(f"  worker {idx}: {fi - f0}/{f1 - f0}", flush=True)
    ff.stdin.close()
    ff.wait()
    return path


# ------------------------------------------------------------------ audio
def decode(path, start=0.0, dur=None, af=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", path]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    if af:
        cmd += ["-af", af]
    cmd += ["-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)


def load_sfx(name):
    with wave.open(os.path.join(ROOT, "sfx", name + ".wav")) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32767


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def mix_audio(show, t0, t1, path):
    tl = show.tl
    n = int((t1 - t0) * SR)
    vo = np.zeros(n)
    clips = np.zeros(n)
    fx = np.zeros(n)

    def put(buf, x, at):
        i = int(round((at - t0) * SR))
        a, b = max(0, i), min(n, i + len(x))
        if b > a:
            buf[a:b] += x[a - i:b - i]

    parts = {p: decode(os.path.join(ROOT, "vo", f"PART_{p}.mp3"), af="afftdn=nr=12:nf=-50")
             for p in range(1, 7)}
    for s in tl.segments:
        if s["kind"] == "vo":
            x = parts[s["part"]][int(s["a0"] * SR):int(s["a1"] * SR)].copy()
            f = min(len(x), int(0.01 * SR))
            x[:f] *= np.linspace(0, 1, f)
            x[-f:] *= np.linspace(1, 0, f)
            put(vo, x, s["g0"])
        elif s["kind"] == "clip" and s.get("real"):
            x = decode(s["path"], s["src_in"], s["dur"])
            if len(x):
                x *= 10 ** ((-20 - rms_db(x)) / 20)  # match narration loudness roughly
                f = min(len(x), int(0.03 * SR))
                x[:f] *= np.linspace(0, 1, f)
                x[-f:] *= np.linspace(1, 0, f)
                put(clips, x, s["g0"])
    vo *= 10 ** ((-20 - rms_db(vo[np.abs(vo) > 1e-4] if np.any(np.abs(vo) > 1e-4) else vo)) / 20)

    cache = {}
    for at, name, gain in show.sfx:
        if name not in cache:
            cache[name] = load_sfx(name)
        put(fx, cache[name] * gain * 0.55, at)
    # duck sfx under the voice
    win = int(0.05 * SR)
    env = np.sqrt(np.convolve(vo ** 2, np.ones(win) / win, mode="same"))
    duck = 1 - 0.45 * np.clip(env / 0.05, 0, 1)
    fx *= duck
    mix = vo + clips + fx  # no room tone: the user wants silence between lines
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--frames", default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    show = Show()
    if a.frames:
        for s in a.frames.split(","):
            t = float(s)
            p = os.path.join(WORK, f"still_{t:07.2f}.png")
            show.frame(t).save(p)
            print(p)
        return
    t1 = a.t1 if a.t1 is not None else show.tl.duration
    f0, f1 = int(a.t0 * FPS), int(t1 * FPS)
    print(f"rendering {a.t0:.1f}-{t1:.1f}s ({f1 - f0} frames), {len(show.cards)} cards", flush=True)
    wav = os.path.join(WORK, "mix.wav")
    mix_audio(show, f0 / FPS, f1 / FPS, wav)
    step = math.ceil((f1 - f0) / a.workers)
    jobs = [(i, f0 + i * step, min(f1, f0 + (i + 1) * step), os.path.join(WORK, f"part{i}.mp4"))
            for i in range(a.workers) if f0 + i * step < f1]
    with mp.Pool(len(jobs)) as pool:
        paths = pool.map(render_range, jobs)
    lst = os.path.join(WORK, "concat.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in paths))
    out = a.out or os.path.join(OUT, "patrick_video.mp4" if a.t1 is None and a.t0 == 0 else "preview.mp4")
    # two-pass loudness normalisation to YouTube's -14 LUFS
    import json as _json
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = _json.loads(p[p.rindex("{"):p.rindex("}") + 1])
    ln = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", ln, "-ar", "48000", "-ac", "2",
                    "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "-shortest", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
