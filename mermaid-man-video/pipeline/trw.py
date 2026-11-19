import sys, subprocess, json, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=4)
jobs = json.load(open(sys.argv[1])); out = {}
for name, (src, a, b) in jobs.items():
    pcm = subprocess.run(['ffmpeg','-v','error','-ss',str(a),'-t',str(b-a),'-i',src,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32)/32768
    segs, _ = m.transcribe(audio, beam_size=5, word_timestamps=True, vad_filter=False)
    words = [(round(a+w.start,2), round(a+w.end,2), w.word.strip()) for s in segs for w in s.words]
    out[name] = words
    print(name, ' '.join(f'[{w[0]:.2f}]{w[2]}' for w in words), flush=True)
json.dump(out, open(sys.argv[2],'w'), indent=0)
