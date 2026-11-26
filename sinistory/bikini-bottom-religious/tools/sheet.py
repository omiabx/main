import subprocess,sys
from PIL import Image, ImageDraw
from io import BytesIO
src,out,step=sys.argv[1],sys.argv[2],float(sys.argv[3])
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src],capture_output=True,text=True).stdout)
ts=[i*step+0.5 for i in range(int(dur/step)+1) if i*step+0.5<dur]
ims=[(t,Image.open(BytesIO(subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i',src,'-frames:v','1','-vf','scale=320:180','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout))) for t in ts]
cols=6; rows=(len(ims)+cols-1)//cols; s=Image.new('RGB',(320*cols,196*rows)); d=ImageDraw.Draw(s)
for i,(t,im) in enumerate(ims): x,y=(i%cols)*320,(i//cols)*196; s.paste(im,(x,y+16)); d.text((x+3,y+2),f'{t:.1f}',fill='yellow')
s.save(out)
