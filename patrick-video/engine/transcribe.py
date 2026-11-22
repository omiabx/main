"""Transcribe the uploaded parts with word timestamps -> work/<id>.json"""
import json, sys, os, subprocess
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=4)
for p in sys.argv[1:]:
    pcm = subprocess.run(['ffmpeg','-loglevel','error','-i',p,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(audio, word_timestamps=True, beam_size=5, vad_filter=False)
    words = [dict(w=w.word, s=w.start, e=w.end) for s in segs for w in s.words]
    out = os.path.join('work', os.path.basename(p)[:8] + '.json')
    json.dump(words, open(out, 'w'))
    print(out, len(words), ' '.join(x['w'] for x in words[:14]))
