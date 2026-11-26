# usage: evidence.py ID SRC START END [nframes]  -> ev/ID.png (labelled frame strip) + ev/ID.txt (small.en transcript of window)
import sys, subprocess, numpy as np, os, json
from PIL import Image, ImageDraw, ImageFont
from faster_whisper import WhisperModel
vid, src, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
n = int(sys.argv[5]) if len(sys.argv) > 5 else 8
OUT='/tmp/claude-0/-home-user-main/097e55d9-3f75-5e8f-88d6-04e1d361aa0f/scratchpad/verify/ev/'
ts=[a-1.0+(b-a+2.0)*i/(n-1) for i in range(n)]
frames=[]
for t in ts:
    r=subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-ss',f'{max(t,0):.3f}','-i',src,'-frames:v','1','-vf','scale=480:-2','-f','image2pipe','-vcodec','png','-'],capture_output=True)
    from io import BytesIO
    try: frames.append((t,Image.open(BytesIO(r.stdout)).convert('RGB')))
    except Exception: pass
W,H=frames[0][1].size; cols=4; rows=(len(frames)+cols-1)//cols
sheet=Image.new('RGB',(cols*W,rows*(H+26)),'black'); d=ImageDraw.Draw(sheet)
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
except Exception: f=ImageFont.load_default()
for i,(t,im) in enumerate(frames):
    x,y=(i%cols)*W,(i//cols)*(H+26); sheet.paste(im,(x,y+26)); d.text((x+6,y+3),f'{vid}  t={t:.2f}s',fill='yellow',font=f)
sheet.save(OUT+vid+'.png')
pad=6
raw=subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-ss',str(max(a-pad,0)),'-i',src,'-t',str(b-a+2*pad),'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
au=np.frombuffer(raw,np.int16).astype(np.float32)/32768
m=WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=4)
segs,_=m.transcribe(au,beam_size=5,condition_on_previous_text=False)
lines=[f'[{s.start+max(a-pad,0):8.2f}-{s.end+max(a-pad,0):8.2f}] {s.text.strip()}' for s in segs]
open(OUT+vid+'.txt','w').write('\n'.join(lines)+'\n'); print('\n'.join(lines))
