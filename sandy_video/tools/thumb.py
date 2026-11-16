from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import numpy as np, random
F="fonts/"; W,H=1280,720
def font(n,s): return ImageFont.truetype(F+n,s)
random.seed(3)
canvas=Image.new("RGB",(W,H),(10,22,48))
# background gradient (deep water)
g=np.zeros((H,W,3)); y=np.linspace(0,1,H)[:,None]
g[...,0]=10+20*y; g[...,1]=40+30*(1-y); g[...,2]=90+40*(1-y)
canvas=Image.fromarray(g.astype(np.uint8))
# Sandy panel
s=Image.open("work/frames/sandy_panic_128.5.png").convert("RGB")
s=s.crop((360,70,1200,910)).resize((780,780),Image.LANCZOS)
s=ImageEnhance.Color(s).enhance(1.35); s=ImageEnhance.Contrast(s).enhance(1.12)
mask=Image.new("L",s.size,255); md=np.array(mask,dtype=float)
fade=np.clip((np.arange(780)-560)/220,0,1)  # fade right edge
md=md*(1-fade[None,:]); mask=Image.fromarray(md.astype(np.uint8))
canvas.paste(s,(-40,-40),mask)
# contract paper
P=Image.new("RGBA",(500,620),(0,0,0,0)); pd=ImageDraw.Draw(P)
pd.rectangle((0,0,499,619),fill=(246,240,222,255))
noise=(np.random.default_rng(1).normal(0,7,(620,500))).clip(-20,20)
arr=np.array(P).astype(float); arr[...,:3]+=noise[...,None]; P=Image.fromarray(arr.clip(0,255).astype(np.uint8))
pd=ImageDraw.Draw(P)
pd.text((30,28),"TREEDOME ENTERPRISES LTD.",font=font("CourierPrime.ttf",27),fill=(40,40,40))
pd.line((30,66,470,66),fill=(60,60,60),width=3)
pd.text((30,80),"EMPLOYMENT CONTRACT",font=font("SpecialElite.ttf",34),fill=(20,20,20))
lines=[("EMPLOYEE:","S. CHEEKS"),("TERM:","20 YEARS"),("DATED:","MAY 2006")]
for i,(a,b) in enumerate(lines):
    yy=150+i*62
    pd.text((30,yy),a,font=font("SpecialElite.ttf",28),fill=(70,70,70))
    pd.text((200,yy-6),b,font=font("PermanentMarker.ttf",36),fill=(25,40,120))
for i in range(4): pd.line((30,360+i*30,300+random.randint(0,170),360+i*30),fill=(150,150,140),width=4)
pd.text((40,505),"The Board",font=font("PermanentMarker.ttf",34),fill=(25,40,120))
pd.line((30,555,330,555),fill=(60,60,60),width=2)
# chimp photo clipped on paper
c=Image.open("work/frames/chimp_373.5.png").convert("RGB").crop((420,230,1100,910)).resize((200,200),Image.LANCZOS)
c=ImageEnhance.Color(c).enhance(1.25)
ph=Image.new("RGBA",(218,218),(255,255,255,255)); ph.paste(c,(10,10)); ph=ph.rotate(9,expand=True,resample=Image.BICUBIC)
P=P.rotate(5,expand=True,resample=Image.BICUBIC)
sh=Image.new("RGBA",P.size,(0,0,0,0)); sh.putalpha(P.split()[3].point(lambda v: v*0.6)); sh=sh.filter(ImageFilter.GaussianBlur(14))
canvas=canvas.convert("RGBA")
canvas.alpha_composite(Image.new("RGBA",P.size,(0,0,0,170)) if False else sh,(735,62)); canvas.alpha_composite(P,(720,45))
canvas.alpha_composite(sh2,(1015,22)) if False else None
# chimp photo on top corner
phs=Image.new('RGBA',ph.size,(0,0,0,0)); phs.putalpha(ph.split()[3].point(lambda v:v*0.55)); phs=phs.filter(ImageFilter.GaussianBlur(10))
canvas.alpha_composite(phs,(1062,18)); canvas.alpha_composite(ph,(1050,2))
# EXPIRED stamp
st=Image.new("RGBA",(760,230),(0,0,0,0)); sd=ImageDraw.Draw(st)
red=(222,28,36,255)
sd.rounded_rectangle((8,8,752,222),radius=22,outline=red,width=16)
fnt=font("Anton.ttf",170); bb=sd.textbbox((0,0),"EXPIRED",font=fnt)
sd.text(((760-(bb[2]-bb[0]))/2-bb[0],(230-(bb[3]-bb[1]))/2-bb[1]),"EXPIRED",font=fnt,fill=red)
# grunge: punch random holes
a=np.array(st); rng=np.random.default_rng(5); holes=rng.random(a.shape[:2])<0.06
a[...,3]=np.where(holes,0,a[...,3]); st=Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6))
st=st.rotate(14,expand=True,resample=Image.BICUBIC)
# white outline glow behind stamp for contrast
glow=Image.new("RGBA",st.size,(255,255,255,0)); glow.putalpha(st.split()[3].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3)))
canvas.alpha_composite(glow,(575,345)); canvas.alpha_composite(st,(575,345))
# vignette
v=np.ones((H,W)); yy,xx=np.mgrid[0:H,0:W]; v=1-0.35*(((xx-W/2)/(W/1.4))**2+((yy-H/2)/(H/1.3))**2)
out=(np.array(canvas.convert("RGB")).astype(float)*v[...,None]).clip(0,255).astype(np.uint8)
im=Image.fromarray(out); im.save("/home/user/main/sandy_video/thumbnail.png"); im.resize((320,180),Image.LANCZOS).save("work/thumb_small.png")
