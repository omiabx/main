#!/bin/bash
# usage: master.sh video.mp4 mix.wav out.mp4  -> two-pass linear loudnorm to -14 LUFS / -1 dBTP, AAC 320k, H.264 copy
set -e
V=$1; A=$2; O=$3
J=$(ffmpeg -nostdin -hide_banner -i "$A" -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -nostdin -y -loglevel error -i "$V" -i "$A" -map 0:v -map 1:a -c:v copy -af "loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$O"
ffmpeg -nostdin -hide_banner -i "$O" -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" 
