"""Lint Xtrades Short scripts against the channel's writing rules."""
import re, sys
from num2words import num2words as n2w

CTA = "More breakdowns like this live in the free Xtrades server. Link's in the caption."
BANNED = ["here's the thing", "here is the thing", "kicker", "let's dive", "dive in", "delve", "landscape",
          "game-changer", "game changer", "only time will tell", "at the end of the day", "buckle up",
          "polymarket", "bettor", "betting market", "prediction market", "odds", "the result", "why so sure",
          "what flips", "in conclusion", "the bottom line", "simply put", "make no mistake", "spoiler"]
WPS = (2.55, 2.85)  # spoken words/sec range for this voice at stability 60

def spoken(text):
    t = text.replace("Xtrades", "X trades")
    t = re.sub(r"\$(\d[\d,]*)\.(\d\d)", lambda m: f"{n2w(int(m.group(1).replace(',','')))} dollars and {n2w(int(m.group(2)))} cents" if m.group(2)!='00' else f"{n2w(int(m.group(1).replace(',','')))} dollars", t)
    t = re.sub(r"\$(\d[\d,]*)", lambda m: n2w(int(m.group(1).replace(',', ''))) + " dollars", t)
    t = re.sub(r"(\d[\d,]*)%", lambda m: n2w(int(m.group(1).replace(',', ''))) + " percent", t)
    t = re.sub(r"\b(19|20)\d\d\b", lambda m: n2w(int(m.group(0)), to="year"), t)
    t = re.sub(r"\d[\d,]*", lambda m: n2w(int(m.group(0).replace(',', ''))), t)
    return t

def lint(path):
    text = open(path).read().strip()
    issues = []
    if "—" in text or "–" in text or " - " in text: issues.append("dash found")
    if "?" in text: issues.append("question mark (no self-answered questions)")
    low = text.lower()
    for b in BANNED:
        if re.search(r"\b" + re.escape(b) + r"\b", low): issues.append(f"banned phrase: {b!r}")
    if re.search(r"\b(it'?s|is|was) not\b[^.]*,\s*(it'?s|but)\b", low): issues.append("'not X, it's/but Y' pattern")
    if not text.endswith(CTA): issues.append("CTA not verbatim at end")
    body = text[: -len(CTA)].strip()
    sents = [s.strip() for s in re.split(r"(?<=[.!])\s+", body) if s.strip()]
    for s in sents:
        if len(s.split()) < 5: issues.append(f"possible fragment: {s!r}")
        if re.search(r"\b\w+, \w+(?: \w+)?,? and \w+\b", s) and s.count(",") >= 2: issues.append(f"check list-of-three: {s!r}")
    if not re.search(r"\d|four|one", sents[0]): issues.append("hook has no hard number")
    sp = spoken(text)
    w = len(sp.split())
    lo, hi = w / WPS[1], w / WPS[0]
    flag = "" if lo >= 55 and hi <= 75 else "  <-- OUTSIDE 55-75s"
    print(f"== {path}: {len(text.split())} written / {w} spoken words, est {lo:.0f}-{hi:.0f}s{flag}")
    for i in issues: print("   !", i)
    if not issues: print("   ok: no rule hits")
    return sp

if __name__ == "__main__":
    for p in sys.argv[1:]:
        sp = lint(p)
        if "--spoken" in sys.argv: print(sp)
