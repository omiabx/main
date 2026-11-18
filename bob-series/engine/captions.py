"""Word-timed SRT captions from script + alignment + timeline info.
usage: captions.py <script.json> <align.json> <info.json> <out.srt>
Audio demos (vclip events) get their own caption line."""
import json, re, math, sys
Sp, Ap, Ip, O = sys.argv[1:5]
S = json.load(open(Sp)); al = json.load(open(Ap)); info = json.load(open(Ip))
vt = {v['id']: v['t'] for v in info['voice']}
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower().replace('-', ''))
caps = []
for c in S['chunks']:
    ws = al[c['id']]['words']; k = 0; toks = []
    for tok in c['text'].split():
        parts = [p for p in tok.split('-') if norm(p)]
        if not parts: continue
        toks.append((tok, vt[c['id']] + ws[k]['s'], vt[c['id']] + ws[k + len(parts) - 1]['e'])); k += len(parts)
    sent, cur = [], []
    for t in toks:
        cur.append(t)
        if re.search(r'[.?!]["”]?$', t[0]): sent.append(cur); cur = []
    if cur: sent.append(cur)
    for se in sent:
        L = len(' '.join(x[0] for x in se)); n = max(1, math.ceil(L / 42)); target = L / n; part = []
        for i, t in enumerate(se):
            part.append(t)
            if len(' '.join(x[0] for x in part)) >= target * 0.92 and i < len(se) - 1 and n > 1 and len(' '.join(x[0] for x in se[i + 1:])) >= 10:
                caps.append(part); part = []; n -= 1; target = len(' '.join(x[0] for x in se[i + 1:])) / max(1, n)
        if part: caps.append(part)
first_line = re.split(r'(?<=[.?!])\s', S['chunks'][0]['text'].replace('\n', ' '))[0]
for e in [x for x in info['sfx'] if x['n'] == 'vclip']:
    lab = f"(the same line, measured {e['rate']:,} times a second)" if e.get('rate') else '(the same line, at full quality)'
    caps.append([(f'"{first_line}" {lab}', e['t'], e['t'] + (e['b'] - e['a']))])
caps.sort(key=lambda c: c[0][1])
def ts(t): ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
out = []
for i, cp in enumerate(caps):
    a = cp[0][1]; b = cp[-1][2] + 0.3
    if i + 1 < len(caps): b = min(b, caps[i + 1][0][1] - 0.02)
    out.append(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{' '.join(x[0] for x in cp)}\n")
open(O, 'w').write('\n'.join(out)); print(len(caps), 'captions ->', O)
