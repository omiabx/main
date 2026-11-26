import json,re,glob,difflib,sys
chunks=re.findall(r"## Chunk (\d+): ([^\n(]*?)\s+\(.*?```\n(.*?)```",open('/home/user/main/sinistory/bikini-bottom-religious/04_voiceover_chunks.md').read(),re.S)
norm=lambda s:re.sub(r"[^a-z0-9' ]",' ',s.lower().replace('-',' ')).split()
NUM={'2000':'two thousand','2010':'twenty ten','62':'sixty two','10000':'ten thousand','10,000':'ten thousand','47':'forty seven','22':'twenty two','1100':'eleven hundred','3':'three'}
def nn(ws):
    out=[]
    for w in ws: out+= NUM.get(w,w).split()
    return out
for f in sorted(glob.glob('vo/*.json')):
    words=nn(norm(' '.join(s['text'] for s in json.load(open(f)))))
    best=max(chunks,key=lambda c:difflib.SequenceMatcher(None,nn(norm(c[2])),words).ratio())
    ref=nn(norm(best[2])); sm=difflib.SequenceMatcher(None,ref,words)
    print(f"\n=== {f[3:11]}  ->  Chunk {best[0]} ({best[1].strip()})  similarity {sm.ratio():.3f}  ref {len(ref)}w / heard {len(words)}w")
    for op,a1,a2,b1,b2 in sm.get_opcodes():
        if op!='equal': print(f"   {op:8s} script: {' '.join(ref[a1:a2])!r:45.45} | heard: {' '.join(words[b1:b2])!r}")
