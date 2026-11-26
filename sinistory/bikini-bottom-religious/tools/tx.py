# usage: tx.py SRC OUT.json [model] [start] [dur]
import sys, subprocess, json, numpy as np, time
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else 'base.en'
ss = float(sys.argv[4]) if len(sys.argv) > 4 else 0
dur = sys.argv[5] if len(sys.argv) > 5 else None
cmd = ['ffmpeg','-nostdin','-loglevel','error','-ss',str(ss),'-i',src] + (['-t',dur] if dur else []) + ['-ac','1','-ar','16000','-f','s16le','-']
a = np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout, np.int16).astype(np.float32)/32768
t=time.time()
m = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=4)
segs,_ = m.transcribe(a, beam_size=1, vad_filter=False, word_timestamps=True, condition_on_previous_text=False)
res=[]
for s in segs:
    res.append({'start':round(s.start+ss,2),'end':round(s.end+ss,2),'text':s.text.strip(),
                'words':[[round(w.start+ss,2),round(w.end+ss,2),w.word] for w in (s.words or [])]})
json.dump(res, open(out,'w'))
print(f'{src}: {len(a)/16000:.0f}s audio in {time.time()-t:.0f}s', file=sys.stderr)
