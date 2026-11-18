#!/usr/bin/env python3
"""
pack_clips.py: shrink your downloaded clips into one small zip to upload.

Keeps 1080p, re-encodes each clip efficiently (H.264, CRF 27), keeps audio (needed for the B dialogue bites),
and skips _candidates/ and _preview/ (not needed). 30 clips usually come to ~40-60 MB instead of ~360 MB.

RUN (point it at your clips folder):
  python pack_clips.py "C:\\Users\\realo\\AppData\\Local\\Programs\\Microsoft VS Code\\clips"
Output: clips_packed.zip next to this script. Upload that file.
"""
import os, re, shutil, subprocess, sys, zipfile

if len(sys.argv) < 2:
    sys.exit(__doc__)
src = sys.argv[1]
if not os.path.isdir(src):
    sys.exit(f"Folder not found: {src}")
if not shutil.which("ffmpeg"):
    sys.exit("ffmpeg not found on PATH.")

here = os.path.dirname(os.path.abspath(__file__))
work = os.path.join(here, "_packed_tmp")
os.makedirs(work, exist_ok=True)
files = sorted(f for f in os.listdir(src) if re.match(r"^[CB]\d\d\.(mp4|mkv|webm|mov)$", f, re.I))
if not files:
    sys.exit("No C##/B## clips found in that folder.")

before = after = 0
for i, f in enumerate(files, 1):
    inp = os.path.join(src, f); out = os.path.join(work, os.path.splitext(f)[0] + ".mp4")
    before += os.path.getsize(inp)
    print(f"[{i}/{len(files)}] {f}", flush=True)
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp,
                        "-vf", "scale='min(1920,iw)':-2", "-c:v", "libx264", "-preset", "slow", "-crf", "27",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
    if r.returncode != 0 or not os.path.exists(out):
        print(f"   couldn't re-encode, packing original instead"); shutil.copy(inp, os.path.join(work, f)); out = os.path.join(work, f)
    after += os.path.getsize(out)

for extra in ("sources.csv", "review.csv"):
    if os.path.exists(os.path.join(src, extra)): shutil.copy(os.path.join(src, extra), os.path.join(work, extra))

zpath = os.path.join(here, "clips_packed.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
    for f in sorted(os.listdir(work)): z.write(os.path.join(work, f), f)
shutil.rmtree(work, ignore_errors=True)
print(f"\nDone: {len(files)} clips, {before / 1e6:.0f} MB -> {os.path.getsize(zpath) / 1e6:.0f} MB")
print(f"Upload this file: {zpath}")
