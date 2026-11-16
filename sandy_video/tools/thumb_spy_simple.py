from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
F="fonts/"; W,H=1280,720
def font(n,s): return ImageFont.truetype(F+n,s)

# plain background
sea=Image.open("work/frames/sea_plate.png").convert("RGB")
sea=sea.crop((0,362,1916,1440)).resize((W,H),Image.LANCZOS)   # 16:9 slice keeping the rock arch at the bottom
sea=ImageEnhance.Color(sea).enhance(1.25)
canvas=sea.convert("RGBA")  # the whole background is the sea

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
# cut-out: helmet bubble + suit collar (no soft fade, so the background stays one flat colour)
mask=Image.new("L",s.size,0); md=ImageDraw.Draw(mask)
md.ellipse((650-598,745-598,650+598,745+598),fill=255)
md.polygon([(345,1190),(1085,1190),(1110,1440),(320,1440)],fill=255)
s=ImageEnhance.Color(s).enhance(1.3); s=ImageEnhance.Contrast(s).enhance(1.1); s.putalpha(mask)
box=(30,130,1290,1440); s=s.crop(box); sc=720/(box[3]-box[1]); s=s.resize((int(s.size[0]*sc),720),Image.LANCZOS)
al=s.split()[3]; ring=al.filter(ImageFilter.MaxFilter(15))
stroke=Image.new("RGBA",s.size,(255,255,255,0)); stroke.putalpha(ring)
shadow=Image.new("RGBA",s.size,(0,0,0,0)); shadow.putalpha(ring.point(lambda v:v*0.55).filter(ImageFilter.GaussianBlur(12)))
X,Y=40,8
canvas.alpha_composite(shadow,(X+10,Y+12)); canvas.alpha_composite(stroke,(X,Y)); canvas.alpha_composite(s,(X,Y))

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

im=canvas.convert("RGB")  # no vignette
im.save("/home/user/main/sandy_video/thumbnail_spy.png"); im.resize((320,180),Image.LANCZOS).save("work/thumb_spy_small.png")
