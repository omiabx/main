"""Find the exact line inside each uploaded (untrimmed) clip and write clips/trims.json.
Run after dropping C01.mp4 ... C13.mp4 into clips/.  python3 engine/locate_clips.py
"""
import difflib
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from timeline import TRANSCRIPT, norm, probe  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
CLIPS = os.path.join(ROOT, "clips")
NO_DIALOGUE = {"C05": 7.0, "C08": 9.0, "C09": 6.0}  # action moments: keep first N seconds after the start


def main():
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
    path = os.path.join(CLIPS, "trims.json")
    trims = json.load(open(path)) if os.path.exists(path) else {}
    for cid, (_, lines) in sorted(TRANSCRIPT.items()):
        f = os.path.join(CLIPS, cid + ".mp4")
        if not os.path.exists(f):
            continue
        dur = probe(f)
        if cid in NO_DIALOGUE:
            trims[cid] = [0.3, min(dur - 0.1, 0.3 + NO_DIALOGUE[cid])]
            print(cid, "action clip ->", trims[cid])
            continue
        pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                             capture_output=True).stdout
        audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
        segs, _ = model.transcribe(audio, word_timestamps=True)
        words = [w for s in segs for w in s.words]
        heard = [norm(w.word) for w in words]
        want = [norm(x) for _, t in lines if not t.startswith("[") for x in t.split() if norm(x)]
        sm = difflib.SequenceMatcher(None, want, heard, autojunk=False)
        hits = [b + k for a, b, size in sm.get_matching_blocks() for k in range(size)]
        if len(hits) < max(2, len(want) // 3):
            print(cid, "line not found, keeping whole clip (check it)")
            trims[cid] = [0.0, dur]
            continue
        a = max(0.0, words[min(hits)].start - 0.45)
        b = min(dur, words[max(hits)].end + 0.6)
        trims[cid] = [round(a, 2), round(b, 2)]
        print(cid, f"matched {len(hits)}/{len(want)} words ->", trims[cid])
    json.dump(trims, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
