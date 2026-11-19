import json, subprocess, os, soundfile as sf, numpy as np
C = json.load(open('tools/clips.json')); PAD = 1.0
jobs = []
for cid, c in C.items():
    for i, (a, b) in enumerate(c['segs']):
        name = f'{cid}_{i}'
        s = max(0, a - PAD)
        subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{s:.3f}','-t',f'{b-a+2*PAD:.3f}','-i',c['src'],'-vn','-ac','2','-ar','44100',f'sep_in/{name}.wav'],check=True)
        jobs.append((name, a - s, b - a))
subprocess.run(['python3','-m','demucs','-n','htdemucs','--two-stems=vocals','-j','2','-o','sep_out']+[f'sep_in/{n}.wav' for n,_,_ in jobs],check=True)
for name, off, dur in jobs:
    v, sr = sf.read(f'sep_out/htdemucs/{name}/vocals.wav')
    full, _ = sf.read(f'sep_in/{name}.wav')
    a, b = int(off*sr), int((off+dur)*sr)
    sf.write(f'clipaudio/{name}_vox.wav', v[a:b], sr)
    sf.write(f'clipaudio/{name}_orig.wav', full[a:b], sr)
    nv = sf.read(f'sep_out/htdemucs/{name}/no_vocals.wav')[0][a:b]
    rms = lambda x: float(np.sqrt((x**2).mean())+1e-9)
    print(f'{name}: vocals rms {rms(v[a:b]):.4f}  accompaniment rms {rms(nv):.4f}')
