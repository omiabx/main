from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
F="fonts/"; W,H=1280,720
def font(n,s): return ImageFont.truetype(F+n,s)

# plain background: dark navy with a soft red glow behind the text
y=np.linspace(0,1,H)[:,None]; x=np.linspace(0,1,W)[None,:]
bg=np.zeros((H,W,3)); bg[...,0]=14+8*y; bg[...,1]=16+6*y; bg[...,2]=34+14*(1-y)
glow=np.exp(-(((x-.8)/.3)**2+((y-.5)/.5)**2)); bg[...,0]+=110*glow; bg[...,1]+=8*glow; bg[...,2]+=10*glow
canvas=Image.fromarray(bg.clip(0,255).astype(np.uint8)).convert("RGBA")

# Sandy with agent shades + earpiece
s=Image.open("work/frames/sandy_smirk.png").convert("RGBA"); d=ImageDraw.Draw(s)
pts=[(345+70*t+18*np.sin(t*40),690+560*t) for t in np.linspace(0,1,60)]
d.line(pts,fill=(235,235,235,255),width=10,joint="curve")
d.ellipse((318,650,380,712),fill=(30,30,30,255),outline=(230,230,230,255),width=6)
d.line([(480,745),(372,690)],fill=(18,18,18,255),width=22)
for b in ((470,672,760,880),(712,668,915,868)):
    d.rounded_rectangle(b,radius=70,fill=(14,14,18,255),outline=(5,5,5,255),width=10)
d.rounded_rectangle((728,735,762,760),radius=10,fill=(10,10,10,255))
for (x0,y0) in ((520,700),(745,698)):
    d.polygon([(x0,y0+60),(x0+60,y0),(x0+95,y0),(x0+35,y0+60)],fill=(255,255,255,120))
    d.polygon([(x0+70,y0+70),(x0+110,y0+30),(x0+125,y0+30),(x0+85,y0+70)],fill=(255,255,255,90))
s=s.crop((40,180,1300,1440)).resize((760,760),Image.LANCZOS)
s=ImageEnhance.Color(s).enhance(1.3); s=ImageEnhance.Contrast(s).enhance(1.1)
m=np.full((760,760),255,np.float32); fade=np.clip((np.arange(760)-560)/200,0,1); m*=(1-fade)[None,:]
s.putalpha(Image.fromarray(m.astype(np.uint8)))
canvas.alpha_composite(s,(-30,-20))

# stacked headline
def word(txt,size,fill):
    t=Image.new("RGBA",(900,400),(0,0,0,0)); td=ImageDraw.Draw(t); f=font("Anton.ttf",size)
    bb=td.textbbox((0,0),txt,font=f,stroke_width=14); td.text((30-bb[0],30-bb[1]),txt,font=f,fill=fill,stroke_width=14,stroke_fill=(0,0,0))
    return t.crop(t.getbbox())
def place(t,cx,top,rot):
    t=t.rotate(rot,expand=True,resample=Image.BICUBIC)
    sh=Image.new("RGBA",t.size,(0,0,0,0)); sh.putalpha(t.split()[3].point(lambda a:a*0.7)); sh=sh.filter(ImageFilter.GaussianBlur(12))
    x=int(cx-t.size[0]/2); canvas.alpha_composite(sh,(x+10,top+10)); canvas.alpha_composite(t,(x,top))
place(word("SPY",300,(255,214,30)),985,70,-4)
place(word("AGENT",205,(255,255,255)),985,395,-4)

out=np.array(canvas.convert("RGB")).astype(np.float32)
yy,xx=np.mgrid[0:H,0:W]; v=1-0.28*(((xx-W/2)/(W/1.4))**2+((yy-H/2)/(H/1.3))**2)
im=Image.fromarray((out*v[...,None]).clip(0,255).astype(np.uint8))
im.save("/home/user/main/sandy_video/thumbnail_spy.png"); im.resize((320,180),Image.LANCZOS).save("work/thumb_spy_small.png")
