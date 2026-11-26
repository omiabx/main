import json,re,sys
from rapidfuzz import fuzz
norm=lambda s:re.sub(r"[^a-z0-9' ]",' ',s.lower()).split()
def span(f,q,near=None,win=40):
    ws=[w for s in json.load(open(f)) for w in s['words']]
    if near: ws=[w for w in ws if abs(w[0]-near)<win]
    toks=[(w[0],w[1],t) for w in ws for t in norm(w[2])]
    qn=norm(q); n=len(qn); best=(0,None)
    for i in range(len(toks)):
        for L in range(max(1,n-3),n+4):
            seg=toks[i:i+L]
            if len(seg)<1: continue
            sc=fuzz.ratio(' '.join(qn),' '.join(t for _,_,t in seg))
            if sc>best[0]: best=(sc,(seg[0][0],seg[-1][1],' '.join(t for _,_,t in seg)))
    return best
if __name__=='__main__':
    for line in sys.stdin:
        if not line.strip(): continue
        vid,f,near,q=line.rstrip('\n').split('|')
        sc,(a,b,t)=span('verify/tx/'+f+'.json',q,float(near) if near else None)
        print(f'{vid}\t{f}\t{a:.2f}\t{b:.2f}\t{sc:.0f}\t{t}')
