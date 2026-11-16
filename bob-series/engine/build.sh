#!/usr/bin/env bash
# Build an episode MP4 from a folder of voice files (01.mp3 ... 15.mp3 or .wav).
# usage: engine/build.sh <voice_dir> <work_dir> <out.mp4> [workers]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VO="$1"; WORK="$2"; OUT="$3"; NW="${4:-4}"
mkdir -p "$WORK/seg"
python3 "$HERE/align.py" "$VO" "$HERE/../ep05/script.json" "$WORK/align.json"
node "$HERE/render.js" info "$WORK/align.json" "$WORK/info.json"
DUR=$(python3 -c "import json;print(json.load(open('$WORK/info.json'))['duration'])")
python3 "$HERE/sfx.py" "$WORK/sfx" >/dev/null
python3 "$HERE/mix.py" "$WORK/info.json" "$WORK/mix.wav"
STEP=$(python3 -c "import math;print(math.ceil($DUR/$NW))")
rm -f "$WORK"/seg/*.mp4; : > "$WORK/seg/list.txt"
for i in $(seq 0 $((NW-1))); do
  A=$((i*STEP)); B=$(((i+1)*STEP)); [ $i -eq $((NW-1)) ] && B=99999
  node "$HERE/render.js" video "$WORK/align.json" $A $B "$WORK/seg/$i.mp4" 30 > "$WORK/seg/$i.log" 2>&1 &
  echo "file '$WORK/seg/$i.mp4'" >> "$WORK/seg/list.txt"
done
wait
ffmpeg -y -v error -f concat -safe 0 -i "$WORK/seg/list.txt" -c copy "$WORK/video.mp4"
ffmpeg -y -v error -i "$WORK/video.mp4" -i "$WORK/mix.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -profile:v high -r 30 -movflags +faststart \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -shortest "$OUT"
echo "done: $OUT"
