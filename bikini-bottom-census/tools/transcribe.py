"""Transcribe a video file to a timestamped text file.
Usage: python3 transcribe.py <video> <out.txt> [model]
"""
import subprocess, sys, os, tempfile
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "small.en"

import numpy as np
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], check=True, capture_output=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)

m = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(audio, beam_size=1, vad_filter=True, condition_on_previous_text=False)

def ts(t):
    h, r = divmod(int(t), 3600); mm, s = divmod(r, 60)
    return f"{h:01d}:{mm:02d}:{s:02d}"

with open(out, "w") as f:
    for s in segs:
        f.write(f"[{ts(s.start)}-{ts(s.end)}] {s.text.strip()}\n")
        f.flush()
print("done", out)
