"""Map each script beat (VO_01..VO_32) to start/end times inside PART_n.mp3."""
import json, re, difflib
BEATS = json.load(open('work/beats_text.json'))  # [{id, part, text}]
num = {'1st':'first','2':'two','7':'seven','4':'four','9':'nine','50':'fifty','14th':'fourteenth','21st':'twentyfirst','9th':'ninth'}
def norm(w):
    w = w.lower().replace("'", "").replace("’", "")
    w = re.sub(r'[^a-z0-9]', '', w)
    return num.get(w, w)
out = []
for part in range(1, 7):
    words = json.load(open(f'work/PART_{part}.json'))
    tw = [norm(x['w']) for x in words]
    beats = [b for b in BEATS if b['part'] == part]
    sw, owner = [], []
    for b in beats:
        for w in b['text'].split():
            n = norm(w)
            if n: sw.append(n); owner.append(b['id'])
    sm = difflib.SequenceMatcher(None, sw, tw, autojunk=False)
    s2t = {}
    for a, b2, size in sm.get_matching_blocks():
        for k in range(size): s2t[a + k] = b2 + k
    matched = len(s2t) / len(sw)
    for b in beats:
        idx = [i for i, o in enumerate(owner) if o == b['id']]
        hits = [s2t[i] for i in idx if i in s2t]
        cov = len(hits) / len(idx)
        start, end = words[min(hits)]['s'], words[max(hits)]['e']
        out.append(dict(id=b['id'], part=part, start=round(start, 3), end=round(end, 3), coverage=round(cov, 2)))
    print(f'PART_{part}: {matched:.0%} of script words matched')
json.dump(out, open('work/beats.json', 'w'), indent=1)
for b in out: print(b)
