"""Estimate word timings for a script before the VO exists (storyboard use only).
Output: JSON list of {w, start, end} for each written token."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lint import spoken

CPS = 14.5          # spoken characters per second
PAUSE = {",": 0.16, ".": 0.38}

def estimate(text):
    toks = text.split()
    t, out = 0.25, []
    for tok in toks:
        sp = spoken(tok)
        d = max(0.16, len(sp) / CPS)
        out.append({"w": tok, "start": round(t, 3), "end": round(t + d, 3)})
        t += d + 0.03
        if tok[-1] in PAUSE: t += PAUSE[tok[-1]]
    return out

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    words = estimate(open(src).read())
    json.dump(words, open(dst, "w"), indent=0)
    print(f"{src}: {len(words)} tokens, ends {words[-1]['end']:.1f}s")
