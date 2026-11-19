"""Driver: align VO -> build edit -> render video chunks in parallel -> mix audio -> mux MP4."""
import sys, os, pickle, subprocess, time, argparse
sys.path.insert(0, '/home/user/media/tools')
from multiprocessing import Pool
from engine import *
import edl

ap = argparse.ArgumentParser()
ap.add_argument('vo_dir'); ap.add_argument('out')
ap.add_argument('--scale', type=float, default=1.0)
ap.add_argument('--range', type=str, default=None, help='a:b seconds (preview)')
ap.add_argument('--jobs', type=int, default=4)
args = ap.parse_args()

work = os.path.join(os.path.dirname(os.path.abspath(args.out)), 'work_' + os.path.basename(args.out).rsplit('.', 1)[0])
os.makedirs(work, exist_ok=True)
t0 = time.time()
A = align_vo(args.vo_dir, args.vo_dir)
tl = edl.build(A)
pk = os.path.join(work, 'timeline.pkl'); pickle.dump(tl, open(pk, 'wb'))
total = tl['total']
import json as _js; _js.dump(tl['marks'], open(os.path.join(work, 'marks.json'), 'w'))
print(f'timeline {total:.1f}s, {len(tl["shots"])} shots, {len(tl["ovs"])} overlays, {len(tl["audio"])} audio events')

a, b = (0, total) if not args.range else map(float, args.range.split(':'))
f0, f1 = int(a * FPS), int(min(b, total) * FPS)
n = args.jobs
bounds = [f0 + (f1 - f0) * i // n for i in range(n + 1)]
chunks = [(pk, bounds[i], bounds[i + 1], os.path.join(work, f'chunk{i}.mp4'), args.scale) for i in range(n)]
with Pool(n) as p:
    p.map(render_chunk, chunks)
lst = os.path.join(work, 'list.txt')
open(lst, 'w').write(''.join(f"file '{c[3]}'\n" for c in chunks))
vid = os.path.join(work, 'video.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid], check=True)
print(f'video done {time.time() - t0:.0f}s')

# ---- audio
events = []
part_gain = {}
for ev in tl['audio']:
    ev = dict(ev)
    if ev.get('vo'):
        if ev['path'] not in part_gain:
            part_gain[ev['path']] = -16.0 - lufs(load_audio(ev['path']))
        ev['gain'] += part_gain[ev['path']]
    elif ev.get('clip'):
        x = load_audio(ev['path'])
        L = lufs(x) if len(x) > SR * 0.5 else -22
        ev['gain'] += (-17.5 - L) if L > -60 else 0
        ev['data'] = x
    events.append(ev)
raw = os.path.join(work, 'mix_raw.wav')
mix_audio(events, total, raw)
seg = ['-ss', str(a), '-t', str(min(b, total) - a)]
mixed = os.path.join(work, 'mix.wav')
# two-pass loudnorm to -14 LUFS / -1.5 dBTP
import json as _j, re as _re
r = subprocess.run(['ffmpeg', '-hide_banner', '-y'] + seg + ['-i', raw, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
m = _j.loads(_re.search(r'\{[^{}]*\}', r.stderr[r.stderr.rfind('{') - 5:], _re.S).group(0))
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + seg + ['-i', raw, '-af', af, '-ar', '48000', mixed], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', mixed, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', args.out], check=True)
print(f'done {args.out} in {time.time() - t0:.0f}s')
