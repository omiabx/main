import numpy as np, wave, os
SR=48000; rng=np.random.default_rng(7); OUT="sfx"
def save(name,x,peak=0.9):
    x=np.asarray(x,np.float64)
    if x.ndim==1: x=np.stack([x,x],1)
    x=x/ (np.abs(x).max()+1e-9)*peak
    with wave.open(f"{OUT}/{name}.wav","wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
t=lambda d: np.arange(int(SR*d))/SR
def env(n,a,r,shape=2.0):
    e=np.ones(n); ai=int(a*SR); ri=int(r*SR)
    if ai: e[:ai]=np.linspace(0,1,ai)**shape
    if ri: e[-ri:]*=np.linspace(1,0,ri)**shape
    return e
def bp(x,lo,hi):  # FFT band-pass, static
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X[(f<lo)|(f>hi)]=0; return np.fft.irfft(X,len(x))
def sweep_filter(x,f0,f1,q=0.35,blk=1024):
    out=np.zeros_like(x); n=len(x)
    for i in range(0,n,blk):
        seg=x[i:i+blk]; fr=i/n; fc=f0*(f1/f0)**fr
        out[i:i+blk]=bp(np.pad(seg,(0,blk-len(seg))),fc*(1-q),fc*(1+q))[:len(seg)]
    return out
def lp(x,fc):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X*=1/(1+(f/fc)**4); return np.fft.irfft(X,len(x))
def pan_sweep(x,l2r=True):
    p=np.linspace(0,1,len(x)) if l2r else np.linspace(1,0,len(x))
    return np.stack([x*np.cos(p*np.pi/2),x*np.sin(p*np.pi/2)],1)
# whooshes
for i,(d,f0,f1) in enumerate([(0.45,300,3500),(0.6,200,2500),(0.35,500,5000),(0.8,150,1800)]):
    n=rng.standard_normal(int(SR*d)); w=sweep_filter(n,f0,f1)
    e=np.sin(np.linspace(0,np.pi,len(w)))**1.5; save(f"whoosh{i+1}",pan_sweep(w*e,i%2==0))
# reverse whoosh into hit
n=rng.standard_normal(int(SR*0.7)); w=sweep_filter(n,200,4000)*np.linspace(0,1,int(SR*.7))**3; save("suck_in",w)
# impacts
def impact(d=1.4,f=48,noise=0.6):
    tt=t(d); body=np.sin(2*np.pi*(f*tt+ (f*1.5)*(1-np.exp(-tt*25))/25))*np.exp(-tt*3.5)
    cr=lp(rng.standard_normal(len(tt)),2500)*np.exp(-tt*28)*noise
    return np.tanh((body+cr)*2.2)
save("impact_big",impact()); save("impact_small",impact(0.6,70,0.9)); save("sub_drop",np.sin(2*np.pi*(90*t(1.6)-25*t(1.6)**2))*np.exp(-t(1.6)*1.8))
# stamp / thud
tt=t(0.35); save("stamp",np.tanh(3*(lp(rng.standard_normal(len(tt)),900)*np.exp(-tt*30)+np.sin(2*np.pi*95*tt)*np.exp(-tt*18))))
# pop / click
tt=t(0.08); save("pop",np.sin(2*np.pi*(600*tt+4000*tt**2))*np.exp(-tt*70))
tt=t(0.03); save("click",bp(rng.standard_normal(len(tt)),2000,9000)*np.exp(-tt*300))
# bubbles
def bubble(f,d=0.12):
    tt=t(d); return np.sin(2*np.pi*f*(tt+ 2.5*tt**2*f/ (f) * 8))*np.exp(-tt*35)*np.minimum(1,tt*400)
def bubbles(dur,count,fl=400,fh=1600):
    x=np.zeros(int(SR*dur))
    for _ in range(count):
        b=bubble(rng.uniform(fl,fh),rng.uniform(.05,.14)); s=rng.integers(0,len(x)-len(b)); x[s:s+len(b)]+=b*rng.uniform(.3,1)
    return x
save("bubbles_burst",bubbles(1.2,45)); save("bubbles_small",bubbles(0.5,9)); save("bubble_single",bubble(700,0.15))
# underwater rumble bed (ambience, not music)
tt=t(12); amb=lp(rng.standard_normal(len(tt)),220)+0.15*bubbles(12,40,300,900); save("underwater_bed",amb*env(len(tt),1,1),0.5)
# glitch / static
x=np.zeros(int(SR*0.45)); i=0
while i<len(x):
    L=rng.integers(400,3000); seg=rng.standard_normal(L) if rng.random()<.5 else np.sign(np.sin(2*np.pi*rng.uniform(80,1200)*np.arange(L)/SR))
    x[i:i+L]=seg[:len(x)-i]*rng.uniform(.3,1); i+=L
save("glitch",x)
tt=t(0.9); save("static",bp(rng.standard_normal(len(tt)),800,8000)*env(len(tt),.01,.2))
# record scratch
tt=t(0.5); fm=np.sin(2*np.pi*(9*tt))*0.5+0.5; save("scratch",sweep_filter(rng.standard_normal(len(tt)),600,2600,0.5)*(0.4+fm)*env(len(tt),.01,.15))
# camera shutter
x=np.zeros(int(SR*.25)); c=bp(rng.standard_normal(1500),1500,9000)*np.exp(-np.arange(1500)/150); x[:1500]+=c; x[5200:6700]+=c*0.8; save("shutter",x)
# typewriter key
tt=t(0.06); save("type",bp(rng.standard_normal(len(tt)),1200,7000)*np.exp(-tt*120)+0.4*np.sin(2*np.pi*180*tt)*np.exp(-tt*80))
# ding (single bell hit)
tt=t(1.5); save("ding",sum(a*np.sin(2*np.pi*f*tt)*np.exp(-tt*k) for f,a,k in [(1320,1,3),(2640,.4,5),(3960,.2,7)]),0.6)
# error buzz
tt=t(0.4); save("buzz",np.sign(np.sin(2*np.pi*110*tt))*0.6*env(len(tt),.005,.05))
# tick (clock)
tt=t(0.02); save("tick",bp(rng.standard_normal(len(tt)),3000,10000)*np.exp(-tt*400))
# heartbeat
x=np.zeros(int(SR*1.0)); hb=lambda: np.sin(2*np.pi*55*t(.15))*np.exp(-t(.15)*25)
x[:7200]+=hb(); x[int(SR*.28):int(SR*.28)+7200]+=hb()*0.7; save("heartbeat",x)
# riser (noise, rising filter) - not musical
n=rng.standard_normal(int(SR*2.0)); r=sweep_filter(n,300,6000,0.25)*np.linspace(0,1,len(n))**2; save("riser",r)
# swipe (short paper slide)
n=rng.standard_normal(int(SR*.25)); save("swipe",sweep_filter(n,2500,900,0.5)*np.sin(np.linspace(0,np.pi,len(n))))
# crack (glass)
x=np.zeros(int(SR*.6))
for _ in range(60):
    s=rng.integers(0,int(SR*.25)); L=rng.integers(80,600); x[s:s+L]+=bp(rng.standard_normal(L),2500,12000)*rng.uniform(.2,1)
x+= 0.5*lp(rng.standard_normal(len(x)),1500)*np.exp(-t(.6)*20); save("glass_crack",x)
# tv off
tt=t(0.35); save("tv_off",np.sin(2*np.pi*(8000-7000*tt/0.35)*tt)*0.3+bp(rng.standard_normal(len(tt)),300,4000)*np.exp(-tt*12))
print(sorted(os.listdir(OUT)))
