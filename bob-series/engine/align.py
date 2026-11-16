# usage: align.py <audio_dir> <script.json> <out.json>
# Voice files can be either:
#   - one file per take, as listed in script.json "takes" (part1.mp3 ... partN.mp3), or
#   - one file per section (01.mp3 ... 15.mp3).
# Takes are transcribed, matched word-by-word to the script, then cut into per-section clips
# so the edit timeline (which is built per section) works the same either way.
# Output: per section -> {file, dur, words:[{w,s,e}]} with times relative to that section's clip.
import json, sys, os, re, subprocess, difflib, wave
import numpy as np
from faster_whisper import WhisperModel

SR = 16000
def load(f, sr=SR): return np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-']), np.float32)
NUM = {'60': 'sixty', '12': 'twelve', '36': 'thirtysix', '255': 'twohundredandfiftyfive', '768': 'sevenhundredandsixtyeight', '5': 'five', '8': 'eight', '16': 'sixteen', '40': 'forty', '100': 'hundred', '200': 'two'}
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower().replace('-', ''))
words_of = lambda text: [w for w in (norm(x) for x in text.replace('-', ' ').split()) if w]

A, Sp, O = sys.argv[1:4]; S = json.load(open(Sp))
TXT = {c['id']: c['text'] for c in S['chunks']}
m = WhisperModel('small.en', device='cpu', compute_type='int8')
find = lambda base: next((os.path.join(A, base + e) for e in ('.mp3', '.wav', '.m4a') if os.path.exists(os.path.join(A, base + e))), None)

def align_words(au, sw):
    dur = len(au) / SR
    segs, _ = m.transcribe(au, word_timestamps=True, language='en', condition_on_previous_text=False)
    hw = [(norm(x.word), x.start, x.end) for s in segs for x in s.words]; hw = [h for h in hw if h[0]]
    sm = difflib.SequenceMatcher(None, sw, [NUM.get(h[0], h[0]) for h in hw], autojunk=False)
    t = [None] * len(sw)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n): t[a + k] = (hw[b + k][1], hw[b + k][2])
    known = [i for i, x in enumerate(t) if x]
    for i in range(len(sw)):
        if t[i]: continue
        p = max([k for k in known if k < i], default=None); q = min([k for k in known if k > i], default=None)
        ps = t[p][1] if p is not None else 0.0; qs = t[q][0] if q is not None else dur
        lo = p if p is not None else -1; hi = q if q is not None else len(sw)
        s = ps + (qs - ps) * (i - lo) / (hi - lo); t[i] = (s, s + (qs - ps) / (hi - lo))
    return t, len(known)

def write_wav(path, x, sr):
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

out = {}
clipdir = os.path.join(os.path.dirname(os.path.abspath(O)), 'voice_sections'); os.makedirs(clipdir, exist_ok=True)
takes = S.get('takes', [])
use_takes = takes and all(find(t['id']) for t in takes)
if use_takes:
    for tk in takes:
        f = find(tk['id']); au = load(f); hi = load(f, 48000)
        secs = tk['sections']; per = [words_of(TXT[s]) for s in secs]; sw = sum(per, [])
        t, nk = align_words(au, sw)
        print(tk['id'], f'{len(au)/SR:.1f}s', 'matched', nk, '/', len(sw))
        idx = 0; bounds = []
        for s, ws in zip(secs, per): bounds.append((s, idx, idx + len(ws) - 1)); idx += len(ws)
        for k, (s, i0, i1) in enumerate(bounds):
            first, last = t[i0][0], t[i1][1]
            prev_end = t[bounds[k - 1][2]][1] if k else 0.0
            next_start = t[bounds[k + 1][1]][0] if k < len(bounds) - 1 else len(au) / SR
            a = max((prev_end + first) / 2, first - 0.2) if k else max(0.0, first - 0.2)
            b = min((last + next_start) / 2, last + 0.35) if k < len(bounds) - 1 else min(len(au) / SR, last + 0.5)
            clip = hi[int(a * 48000):int(b * 48000)].copy()
            fl = min(len(clip) // 4, int(0.012 * 48000)); r = np.linspace(0, 1, fl)
            if fl: clip[:fl] *= r; clip[-fl:] *= r[::-1]
            cp = os.path.join(clipdir, s + '.wav'); write_wav(cp, clip, 48000)
            out[s] = {'file': cp, 'dur': round(len(clip) / 48000, 3), 'take': tk['id'],
                      'words': [{'w': w, 's': round(x[0] - a, 3), 'e': round(x[1] - a, 3)} for w, x in zip(per[[b_[0] for b_ in bounds].index(s)], t[i0:i1 + 1])]}
else:
    for c in S['chunks']:
        f = find(c['id']);
        if not f: sys.exit(f'missing voice file for section {c["id"]} (or takes {[t["id"] for t in takes]})')
        au = load(f); sw = words_of(c['text']); t, nk = align_words(au, sw)
        out[c['id']] = {'file': os.path.abspath(f), 'dur': round(len(au) / SR, 3), 'words': [{'w': w, 's': round(a, 3), 'e': round(b, 3)} for w, (a, b) in zip(sw, t)]}
        print(c['id'], round(len(au) / SR, 2), 'matched', nk, '/', len(sw))
json.dump(out, open(O, 'w'), indent=0)
