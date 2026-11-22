"""12-second look/sound test of the edit language using only original graphics.
Run: python3 engine/style_test.py  -> out/style_test.mp4
"""
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

import gfx

FPS = 30
DUR = 12.0
ROOT = gfx.ROOT
OUT_DIR = os.path.join(ROOT, "out")
SR = 48000


def load_wav(name):
    with wave.open(os.path.join(ROOT, "sfx", name + ".wav")) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32767


def build_audio(events, path):
    buf = np.zeros(int(SR * DUR))
    room = load_wav("room_tone")
    buf[: len(room)] += room
    buf[len(room): 2 * len(room)] += room[: len(buf) - len(room)]
    for at, name, gain in events:
        s = load_wav(name) * gain
        i = int(at * SR)
        e = min(len(buf), i + len(s))
        buf[i:e] += s[: e - i]
    buf = np.clip(buf, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bg = gfx.desk_background().convert("RGBA")
    fold = gfx.folder(["FILE NO. 0047", "SUBJECT: PATRICK STAR", "RE: THE BRAIN"])
    fold_sh, fpad = gfx.drop_shadow(fold)
    st_file = gfx.stamp("CASE OPEN", size=120, angle=-10)
    clip = gfx.evidence_frame(gfx.placeholder_clip(label="SHOW CLIP (C09)"), "EXHIBIT D  //  S4", tilt=1.5)
    clip_sh, cpad = gfx.drop_shadow(clip.convert("RGBA"))
    st_suspect = gfx.stamp("PRIME SUSPECT", size=100, angle=-8, seed=9)

    events = [
        (0.0, "whoosh", 0.8), (0.32, "folder_slam", 1.0), (1.2, "stamp", 1.0),
        (2.45, "whoosh_short", 0.7), (2.6, "typing", 0.8), (4.25, "typewriter_bell", 0.5),
        (6.5, "record_scratch", 0.9), (6.9, "pin", 0.5), (8.0, "stamp", 1.0), (8.05, "impact", 0.6),
        (9.6, "paper_slide", 0.6), (10.5, "flatline", 0.6), (11.4, "glitch", 0.5),
    ]
    wav = os.path.join(OUT_DIR, "style_test.wav")
    build_audio(events, wav)

    mp4 = os.path.join(OUT_DIR, "style_test.mp4")
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{gfx.W}x{gfx.H}", "-r", str(FPS), "-i", "-", "-i", wav,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "320k", "-shortest", mp4],
        stdin=subprocess.PIPE)

    for fi in range(int(DUR * FPS)):
        t = fi / FPS
        frame = bg.copy()
        sx, sy = gfx.shake_offset(t, 0.33, 0.15, 18)
        sx2, sy2 = gfx.shake_offset(t, 8.0, 0.15, 16)
        sx, sy = sx + sx2, sy + sy2

        if t < 2.5:  # folder slams in, CASE OPEN stamp
            k = gfx.ease_out((t - 0.0) / 0.35)
            scale = 1.25 - 0.25 * k
            f = fold_sh.resize((int(fold_sh.width * scale), int(fold_sh.height * scale)))
            x = (gfx.W - f.width) // 2 + sx
            y = int((gfx.H - f.height) // 2 + (1 - k) * -500) + sy
            frame.alpha_composite(f, (x, y))
            if t >= 1.2:
                ks = gfx.ease_back((t - 1.2) / 0.12)
                s = st_file.resize((max(1, int(st_file.width * (1.6 - 0.6 * ks))), max(1, int(st_file.height * (1.6 - 0.6 * ks)))))
                frame.alpha_composite(s, (1080 - s.width // 2 + sx, 640 - s.height // 2 + sy))
        else:  # evidence clip with slow push-in
            tt = t - 2.5
            k = gfx.ease_out(tt / 0.4)
            zoom = 0.86 + 0.03 * tt / 9.5
            c = clip_sh.resize((int(clip_sh.width * zoom), int(clip_sh.height * zoom)))
            x = (gfx.W - c.width) // 2 + int((1 - k) * 1400) + sx
            y = (gfx.H - c.height) // 2 + 40 + sy
            frame.alpha_composite(c, (x, y))
            if t >= 6.9:
                circ = gfx.marker_circle((420, 300), (t - 6.9) / 0.6)
                frame.alpha_composite(circ, (x + int(c.width * 0.52), y + int(c.height * 0.30)))
            if t >= 8.0:
                ks = gfx.ease_back((t - 8.0) / 0.12)
                s = st_suspect.resize((max(1, int(st_suspect.width * (1.6 - 0.6 * ks))), max(1, int(st_suspect.height * (1.6 - 0.6 * ks)))))
                sxp, syp = 330 - s.width // 2 + sx, 800 - s.height // 2 + sy
                frame.alpha_composite(s, (sxp, syp))
                if t >= 9.6:  # cross out + handwritten "MY READ"
                    d = ImageDraw.Draw(frame)
                    p = gfx.ease_out((t - 9.6) / 0.25)
                    d.line((sxp + 30, syp + s.height // 2, sxp + 30 + (s.width - 60) * p, syp + s.height // 2 - 10),
                           fill=gfx.INK + (255,), width=14)
                    if t >= 9.9:
                        d.text((sxp + 60, syp + s.height - 10), "my read", font=gfx.font("marker", 84), fill=gfx.RED + (255,))
            card = gfx.date_card("10.21.2005", "PATRICK SMARTPANTS", "S4", (t - 2.6) / 1.6)
            frame.alpha_composite(card, (90 + int((1 - k) * -800), 70))

        if t >= 1.5:  # brain monitor in the corner for the rest of the video
            flat = t >= 10.5
            level = 1.0 if t < 9.5 else max(0.0, 1 - (t - 9.5))
            mon = gfx.brain_monitor(t, level, "BRAIN: NOT FOUND" if flat and int(t * 4) % 2 else "BRAIN ACTIVITY", flat)
            frame.alpha_composite(mon, (gfx.W - mon.width - 50, gfx.H - mon.height - 50))

        if 11.4 <= t < 11.75:  # glitch out
            arr = np.asarray(frame.convert("RGB")).copy()
            for _ in range(6):
                r0 = np.random.randint(0, gfx.H - 60)
                arr[r0:r0 + 50] = np.roll(arr[r0:r0 + 50], np.random.randint(-120, 120), axis=1)
            frame = Image.fromarray(arr).convert("RGBA")
        if t >= 11.75:
            frame = Image.new("RGBA", frame.size, (0, 0, 0, 255))

        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", mp4)


if __name__ == "__main__":
    main()
