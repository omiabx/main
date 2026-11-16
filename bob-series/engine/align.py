# usage: align.py <audio_dir> <script.json> <out.json>   (audio files named <id>.mp3 or <id>.wav)
# Output: for each chunk, every SCRIPT word with start/end seconds (whisper words matched to script words).
import json,sys,os,re,subprocess,difflib
import numpy as np
from faster_whisper import WhisperModel
def load(f): return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',f,'-ac','1','-ar','16000','-f','f32le','-']),np.float32)
NUM={'60':'sixty','12':'twelve','36':'thirtysix','255':'twohundredandfiftyfive','768':'sevenhundredandsixtyeight','5':'five','8':'eight','16':'sixteen','40':'forty','100':'hundred','200':'two'}
norm=lambda w: re.sub(r"[^a-z0-9']","",w.lower().replace('-',''))
A,Sp,O=sys.argv[1:4]; S=json.load(open(Sp))
m=WhisperModel('small.en',device='cpu',compute_type='int8')
out={}
for c in S['chunks']:
    f=next(os.path.join(A,c['id']+e) for e in ('.mp3','.wav') if os.path.exists(os.path.join(A,c['id']+e)))
    au=load(f); dur=len(au)/16000
    segs,_=m.transcribe(au,word_timestamps=True,language='en',condition_on_previous_text=False)
    hw=[(norm(x.word),x.start,x.end) for s in segs for x in s.words]; hw=[h for h in hw if h[0]]
    sw=[norm(w) for w in c['text'].replace('-',' ').split()]; sw=[w for w in sw if w]
    sm=difflib.SequenceMatcher(None,sw,[NUM.get(h[0],h[0]) for h in hw],autojunk=False)
    t=[None]*len(sw)
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): t[a+k]=(hw[b+k][1],hw[b+k][2])
    # interpolate gaps
    known=[i for i,x in enumerate(t) if x]
    for i in range(len(sw)):
        if t[i]: continue
        p=max([k for k in known if k<i],default=None); q=min([k for k in known if k>i],default=None)
        ps=t[p][1] if p is not None else 0.0; qs=t[q][0] if q is not None else dur
        lo=p if p is not None else -1; hi=q if q is not None else len(sw)
        fr=(i-lo)/(hi-lo); s=ps+(qs-ps)*fr; t[i]=(s,s+(qs-ps)/(hi-lo))
    out[c['id']]={'file':os.path.abspath(f),'dur':round(dur,3),'words':[{'w':w,'s':round(a,3),'e':round(b,3)} for w,(a,b) in zip(sw,t)]}
    print(c['id'],round(dur,2),'matched',len(known),'/',len(sw))
json.dump(out,open(O,'w'),indent=0)
