import sys, json, pickle, bisect
sys.path.insert(0, '/home/user/media/tools')
from engine import *
sc = json.load(open('/home/user/media/tr/scenes.json'))
tl = pickle.load(open(sys.argv[1], 'rb'))
clip_srcs = set()
for sh in tl['shots']:
    k = sh.kw
    if sh.kind != 'video' or k['freeze']:
        continue
    cuts = sc.get(k['src'])
    if not cuts:
        continue
    t = k['t']; d = sh.end - sh.start
    i = bisect.bisect_right(cuts, t) - 1
    s0, s1 = cuts[i], cuts[i + 1] if i + 1 < len(cuts) else 1e9
    flag = ''
    if t - s0 < 0.25 and i > 0: flag += ' NEAR-CUT-START'
    if s1 - t < d - 0.05: flag += f' CROSSES CUT after {s1 - t:.2f}s of {d:.2f}s'
    if flag:
        print(f'{sh.start:7.2f} {k["src"]:24s} t={t:8.2f} scene[{s0:.2f},{s1:.2f}] dur={d:.2f}{flag}')
