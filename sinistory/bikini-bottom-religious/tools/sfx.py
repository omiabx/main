# Procedurally synthesized SFX (no samples, no licensing). 48 kHz mono 16-bit.
import numpy as np, scipy.signal as ss, soundfile as sf, os, sys
SR=48000; OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True); rng=np.random.default_rng(7)
def bp(x,lo,hi,o=2): return ss.sosfilt(ss.butter(o,[lo,hi],'band',fs=SR,output='sos'),x)
def lp(x,f,o=2): return ss.sosfilt(ss.butter(o,f,'low',fs=SR,output='sos'),x)
def hp(x,f,o=2): return ss.sosfilt(ss.butter(o,f,'high',fs=SR,output='sos'),x)
def env(n,a,d): t=np.arange(n)/SR; return np.minimum(t/a,1)*np.exp(-np.maximum(t-a,0)/d)
def norm(x,peak_db): return x/np.max(np.abs(x))*10**(peak_db/20)
def save(name,x): sf.write(f'{OUT}/{name}.wav',x.astype(np.float32),SR,subtype='PCM_16')
# whoosh: noise through a swept band-pass, swell then fade
n=int(.55*SR); t=np.arange(n)/SR; noise=rng.standard_normal(n); out=np.zeros(n)
for i in range(0,n,480):
    f=300+2600*np.sin(np.pi*min(i/n,1))**1.5
    seg=noise[max(0,i-2048):i+480]; y=bp(seg,f*0.6,f*1.6)[-480:] if len(seg)>=480 else np.zeros(480)
    out[i:i+480]=y[:len(out[i:i+480])]
e=np.sin(np.pi*np.clip(t/0.55,0,1))**2.2; save('whoosh',norm(out*e,-10))
# pop: fast downward sine chirp + tiny click
n=int(.09*SR); t=np.arange(n)/SR; f=900*np.exp(-t*28)+180; ph=2*np.pi*np.cumsum(f)/SR
x=np.sin(ph)*env(n,.002,.025)+0.3*hp(rng.standard_normal(n),2000)*env(n,.0005,.004); save('pop',norm(x,-8))
# typewriter key: sharp metallic click + low knock
n=int(.06*SR); t=np.arange(n)/SR
x=bp(rng.standard_normal(n),2500,7000,3)*env(n,.0003,.006)+0.6*np.sin(2*np.pi*190*t)*env(n,.001,.012)+0.25*np.sin(2*np.pi*3100*t)*env(n,.0005,.01)
save('type',norm(x,-6))
# shutter: two mechanical clicks with filtered noise
n=int(.16*SR); x=np.zeros(n)
for off,g in [(0,1.0),(int(.055*SR),.8)]:
    m=int(.03*SR); c=bp(rng.standard_normal(m),1200,6000,2)*env(m,.0003,.005)*g; x[off:off+m]+=c
x+=0.15*bp(rng.standard_normal(n),800,3000)*env(n,.002,.05); save('shutter',norm(x,-8))
# stamp: low thump + paper slap
n=int(.35*SR); t=np.arange(n)/SR
x=np.sin(2*np.pi*(95*np.exp(-t*6)+45)*t)*env(n,.002,.09)+0.5*bp(rng.standard_normal(n),400,3500)*env(n,.0005,.02)
save('stamp',norm(lp(x,6000),-3))
# ding: small bell (inharmonic partials)
n=int(1.4*SR); t=np.arange(n)/SR; x=sum(a*np.sin(2*np.pi*1320*r*t)*np.exp(-t*d) for a,r,d in [(1,1,3),(.5,2.76,5),(.3,5.4,8),(.2,8.93,11)])
save('ding',norm(x*env(n,.001,10),-10))
# hit: deep boom
n=int(.6*SR); t=np.arange(n)/SR; x=np.sin(2*np.pi*(70*np.exp(-t*4)+35)*t)*env(n,.003,.18)+0.2*lp(rng.standard_normal(n),900)*env(n,.001,.05)
save('hit',norm(x,-3))
# record scratch: noisy pitch sweep
n=int(.45*SR); t=np.arange(n)/SR; f=600+1800*np.sin(2*np.pi*3.2*t)**2; ph=2*np.pi*np.cumsum(f)/SR
x=(0.6*np.sign(np.sin(ph))+0.5*rng.standard_normal(n))*np.sin(np.pi*t/0.45); save('scratch',norm(bp(x,300,5000),-10))
print(sorted(os.listdir(OUT)))
