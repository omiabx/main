from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
F="fonts/"; W,H=1280,720
def font(n,s): return ImageFont.truetype(F+n,s)
rng=np.random.default_rng(4)

# ---------- background: dark dossier navy with grid + red glow
y=np.linspace(0,1,H)[:,None]; x=np.linspace(0,1,W)[None,:]
bg=np.zeros((H,W,3)); bg[...,0]=12+10*y; bg[...,1]=16+8*y; bg[...,2]=30+18*(1-y)
glow=np.exp(-(((x-.78)/.28)**2+((y-.2)/.35)**2)); bg[...,0]+=120*glow; bg[...,1]+=10*glow; bg[...,2]+=12*glow
for gx in range(0,W,40): bg[:,gx]+= (8,10,16)
for gy in range(0,H,40): bg[gy,:]+= (8,10,16)
canvas=Image.fromarray(bg.clip(0,255).astype(np.uint8)).convert("RGBA")

# ---------- Sandy as agent (sunglasses + earpiece drawn on the HD frame)
s=Image.open("work/frames/sandy_smirk.png").convert("RGBA")
d=ImageDraw.Draw(s)
# earpiece coil from ear down to collar
pts=[]
for i in range(60):
    t=i/59; px=345+ 70*t + 18*np.sin(t*40); py=690+ 560*t
    pts.append((px,py))
d.line(pts,fill=(235,235,235,255),width=9,joint="curve")
d.ellipse((318,650,380,712),fill=(30,30,30,255),outline=(230,230,230,255),width=6)
# glasses arm to ear
d.line([(480,745),(372,690)],fill=(18,18,18,255),width=22)
# lenses
lensL=(470,672,760,880); lensR=(712,668,915,868)
for b in (lensL,lensR):
    d.rounded_rectangle(b,radius=70,fill=(14,14,18,255),outline=(5,5,5,255),width=10)
d.rounded_rectangle((728,735,762,760),radius=10,fill=(10,10,10,255))  # bridge
# glints
for (x0,y0) in ((520,700),(745,698)):
    d.polygon([(x0,y0+60),(x0+60,y0),(x0+95,y0),(x0+35,y0+60)],fill=(255,255,255,120))
    d.polygon([(x0+70,y0+70),(x0+110,y0+30),(x0+125,y0+30),(x0+85,y0+70)],fill=(255,255,255,90))
s=s.crop((20,170,1280,1440)).resize((709,715),Image.LANCZOS)
s=ImageEnhance.Color(s).enhance(1.3); s=ImageEnhance.Contrast(s).enhance(1.1)
m=np.full((715,709),255,np.float32); fade=np.clip((np.arange(709)-520)/189,0,1); m*= (1-fade)[None,:]
s.putalpha(Image.fromarray(m.astype(np.uint8)))
canvas.alpha_composite(s,(-20,5))

# ---------- surveillance photo of the "mission"
mph=Image.open("work/frames/sandy_mission.png").convert("RGB").crop((0,560,1120,1400)).resize((520,390),Image.LANCZOS)
g=np.array(mph.convert("L")).astype(np.float32)
g=(g-g.min())/(g.max()-g.min()+1e-6)*230
nv=np.stack([g*0.35,g*1.0,g*0.45],-1)
nv+=rng.normal(0,9,(390,520,1)); nv[::3]*=0.82
yy,xx=np.mgrid[0:390,0:520]; v=1-0.55*(((xx-260)/300)**2+((yy-195)/230)**2); nv*=v[...,None]
ph=Image.fromarray(nv.clip(0,255).astype(np.uint8)); pd=ImageDraw.Draw(ph)
# viewfinder brackets around Sandy (in crop coords she is ~ x60-180, y135-325 at this scale)
cx,cy,bw,bh=118,232,95,118; L=28; col=(255,60,60)
for sx in (-1,1):
    for sy in (-1,1):
        X=cx+sx*bw; Y=cy+sy*bh
        pd.line([(X,Y),(X-sx*L,Y)],fill=col,width=5); pd.line([(X,Y),(X,Y-sy*L)],fill=col,width=5)
pd.text((cx-60,cy-bh-38),"AGENT",font=font("CourierPrime.ttf",28),fill=col)
pd.ellipse((22,18,42,38),fill=(230,40,40)); pd.text((50,12),"REC",font=font("CourierPrime.ttf",28),fill=(230,240,230))
pd.text((300,350),"03:17:04",font=font("CourierPrime.ttf",28),fill=(230,240,230))
pol=Image.new("RGBA",(560,500),(246,244,236,255)); pol.paste(ph,(20,20))
pd2=ImageDraw.Draw(pol); pd2.text((36,420),"Operation: Bikini Bottom",font=font("PermanentMarker.ttf",40),fill=(30,30,40))
pol=pol.resize((476,425),Image.LANCZOS).rotate(5,expand=True,resample=Image.BICUBIC)
sh=Image.new("RGBA",pol.size,(0,0,0,0)); sh.putalpha(pol.split()[3].point(lambda a:a*0.6)); sh=sh.filter(ImageFilter.GaussianBlur(14))
canvas.alpha_composite(sh,(752,248)); canvas.alpha_composite(pol,(740,232))
# paperclip
d=ImageDraw.Draw(canvas)
d.rounded_rectangle((1090,212,1126,305),radius=18,outline=(200,205,215),width=7); d.rounded_rectangle((1099,228,1118,288),radius=10,outline=(200,205,215),width=6)

# ---------- TOP SECRET stamp on the photo corner
st=Image.new("RGBA",(470,130),(0,0,0,0)); sd=ImageDraw.Draw(st); red=(225,30,38,255)
sd.rounded_rectangle((6,6,464,124),radius=14,outline=red,width=10)
f=font("Anton.ttf",86); bb=sd.textbbox((0,0),"TOP SECRET",font=f); sd.text(((470-(bb[2]-bb[0]))/2-bb[0],(130-(bb[3]-bb[1]))/2-bb[1]),"TOP SECRET",font=f,fill=red)
a=np.array(st); a[...,3]=np.where(rng.random(a.shape[:2])<0.07,0,a[...,3]); st=Image.fromarray(a).resize((360,100),Image.LANCZOS).rotate(-12,expand=True,resample=Image.BICUBIC)
canvas.alpha_composite(st,(905,470))

# ---------- SPY AGENT headline
t=Image.new("RGBA",(760,220),(0,0,0,0)); td=ImageDraw.Draw(t); f=font("Anton.ttf",168)
bb=td.textbbox((0,0),"SPY AGENT",font=f,stroke_width=12)
td.text((20-bb[0],20-bb[1]),"SPY AGENT",font=f,fill=(255,214,30),stroke_width=12,stroke_fill=(0,0,0))
t=t.crop(t.getbbox()); t=t.rotate(-3,expand=True,resample=Image.BICUBIC)
tsh=Image.new("RGBA",t.size,(0,0,0,0)); tsh.putalpha(t.split()[3].point(lambda a:a*0.7)); tsh=tsh.filter(ImageFilter.GaussianBlur(10))
tx=W-t.size[0]-26; canvas.alpha_composite(tsh,(tx+8,26)); canvas.alpha_composite(t,(tx,16))

out=np.array(canvas.convert("RGB")).astype(np.float32)
yy,xx=np.mgrid[0:H,0:W]; v=1-0.3*(((xx-W/2)/(W/1.4))**2+((yy-H/2)/(H/1.3))**2)
im=Image.fromarray((out*v[...,None]).clip(0,255).astype(np.uint8))
im.save("/home/user/main/sandy_video/thumbnail_spy.png"); im.resize((320,180),Image.LANCZOS).save("work/thumb_spy_small.png")
