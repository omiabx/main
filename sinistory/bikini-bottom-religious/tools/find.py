# usage: find.py "quote" tx1.json [tx2.json ...]  -> best matches with times
import sys, json, re
from rapidfuzz import fuzz
q = sys.argv[1]
norm = lambda s: re.sub(r"[^a-z0-9' ]", ' ', s.lower()).split()
qw = norm(q); n = len(qw)
best=[]
for f in sys.argv[2:]:
    words=[]
    for s in json.load(open(f)):
        for w in s['words']: words.append((w[0], w[1], w[2]))
    toks=[(a,b,norm(t)) for a,b,t in words]
    flat=[(a,b,x) for a,b,ts in toks for x in ts]
    for i in range(len(flat)):
        for L in (max(1,n-2), n, n+2):
            seg=flat[i:i+L]
            if not seg: continue
            sc=fuzz.ratio(' '.join(qw), ' '.join(x for _,_,x in seg))
            best.append((sc, f.split('/')[-1], seg[0][0], seg[-1][1], ' '.join(x for _,_,x in seg)))
best.sort(reverse=True)
seen=[]
for b in best:
    if any(b[1]==s[1] and abs(b[2]-s[2])<5 for s in seen): continue
    seen.append(b)
    if len(seen)>=3: break
for sc,f,a,e,t in seen: print(f'{sc:5.1f} {f} {a:8.2f}-{e:8.2f} | {t}')
