"""Builds the master timeline: VO segments from PART_n.mp3 with show-clip slots between them,
and maps every transcribed word to a global time so graphics can be anchored to phrases."""
import json
import os
import re
import subprocess

ROOT = os.path.join(os.path.dirname(__file__), "..")
W = lambda *p: os.path.join(ROOT, *p)

# clip slot goes AFTER this beat
CLIP_AFTER = {"VO_01": "C01", "VO_02": "C02", "VO_07": "C03", "VO_09": "C04", "VO_10": "C05",
              "VO_12": "C06", "VO_14": "C07", "VO_16": "C08", "VO_20": "C09", "VO_21": "C10",
              "VO_24": "C11", "VO_25": "C12", "VO_27": "C13"}
# placeholder lengths until the real clips arrive (seconds)
CLIP_EST = {"C01": 6.0, "C02": 5.0, "C03": 9.0, "C04": 8.0, "C05": 7.0, "C06": 7.0, "C07": 4.0,
            "C08": 10.0, "C09": 6.0, "C10": 9.0, "C11": 4.5, "C12": 4.5, "C13": 12.0}
FUZZY = []
# Used when a clip file is missing: the moment plays as a typed transcript card instead.
TRANSCRIPT = {
    "C01": ("HELP WANTED  //  S1  //  1999", [("PATRICK", "Where do ya think you're goin'?"),
                                              ("PATRICK", "You're goin' to the Krusty Krab and get, that, job!")]),
    "C02": ("PET SITTER PAT  //  S8  //  2011", [("PATRICK", "You need to work on your handwriting, SpongeBob."),
                                                 ("", "[crumples up the list]")]),
    "C03": ("JELLYFISHING  //  S1  //  1999", [("PATRICK", "Firmly grasp it."), ("PATRICK", "Firmly grasp it."),
                                               ("PATRICK", "FIRMLY GRASP IT!"), ("", "[Squidward screams]")]),
    "C04": ("THE SECRET BOX  //  S2  //  2001", [("PATRICK", "The inner machinations of my mind are an enigma.")]),
    "C05": ("THE SECRET BOX  //  S2  //  2001", [("", "[Patrick pulls the string. A hidden compartment opens.]"),
                                                 ("", "[Inside: SpongeBob at the Christmas party.]")]),
    "C06": ("SANDY, SPONGEBOB, AND THE WORM  //  S2  //  2001",
            [("PATRICK", "We should take Bikini Bottom and push it somewhere else!"),
             ("SQUIDWARD", "That idea may just be crazy enough... to get us all killed!")]),
    "C07": ("I'M WITH STUPID  //  S2  //  2001",
            [("PATRICK", "SpongeBob, my parents think I'm dumber than a sack of diapers.")]),
    "C08": ("VALENTINE'S DAY  //  S1  //  2000", [("", "[Patrick rampages across the carnival.]"),
                                                  ("", "[He corners a crowd on the dock.]")]),
    "C09": ("PATRICK SMARTPANTS  //  S4  //  2005", [("", "[Patrick runs off a cliff, still reading the sign:]"),
                                                     ("SIGN", "DANGER: CLIFF")]),
    "C10": ("PATRICK SMARTPANTS  //  S4  //  2005", [("PATRICK", "...exactly five meters due north."),
                                                     ("SPONGEBOB", "Brain coral! No wonder you got so smart, buddy.")]),
    "C11": ("THAT'S NO LADY  //  S4  //  2006", [("PATRICK", "Ford knee."), ("MR. KRABS", "That's a seven, Patricia.")]),
    "C12": ("PET SITTER PAT  //  S8  //  2011",
            [("PATRICK", "Snail Tales? I thought it was called \"Meow, meow, meow.\"")]),
    "C13": ("BIG PINK LOSER  //  S2  //  2001", [("CALLER", "Is this the Krusty Krab?"), ("PATRICK", "No, this is Patrick."),
                                                 ("CALLER", "Is this the Krusty Krab?"), ("PATRICK", "No! This is Patrick!")]),
}


def transcript_dur(cid):
    n = sum(len(t) for _, t in TRANSCRIPT[cid][1])
    return round(min(7.5, max(3.6, 1.4 + n * 0.045)), 2)


LEAD_IN = 0.35
PART_GAP = 0.45
END_SCREEN = 14.0

NUM = {"1st": "first", "2": "two", "7": "seven", "4": "four", "9": "nine", "50": "fifty",
       "14th": "fourteenth", "21st": "twentyfirst", "9th": "ninth", "11": "eleven", "20": "twenty",
       "24": "twentyfour", "1": "first", "21": "twentyfirst"}


def norm(w):
    w = w.lower().replace("'", "").replace("’", "")
    w = re.sub(r"[^a-z0-9]", "", w)
    return NUM.get(w, w)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def clip_info(cid):
    """Real clip if present (with optional trims from clips/trims.json), else placeholder."""
    path = W("clips", cid + ".mp4")
    trims = {}
    if os.path.exists(W("clips", "trims.json")):
        trims = json.load(open(W("clips", "trims.json")))
    if os.path.exists(path):
        dur = probe(path)
        a, b = trims.get(cid, [0.5, max(0.6, dur - 0.5)])
        return dict(id=cid, path=path, src_in=a, dur=b - a, real=True)
    return dict(id=cid, path=None, src_in=0.0, dur=transcript_dur(cid), real=False)


class Timeline:
    def __init__(self):
        beats = json.load(open(W("work", "beats.json")))
        self.beats = {b["id"]: b for b in beats}
        self.words = {}
        for p in range(1, 7):
            ws = json.load(open(W("work", f"PART_{p}.json")))
            self.words[p] = ws
        self._patch_words()
        self.part_dur = {p: probe(W("vo", f"PART_{p}.mp3")) for p in range(1, 7)}
        self.segments = []  # dicts: kind vo|clip|end, g0, g1, ...
        g = LEAD_IN
        for p in range(1, 7):
            pb = [b for b in beats if b["part"] == p]
            a0 = 0.0
            for i, b in enumerate(pb):
                if b["id"] in CLIP_AFTER or i == len(pb) - 1:
                    if i == len(pb) - 1:
                        a1 = self.part_dur[p]
                    else:
                        nxt = pb[i + 1]
                        a1 = min(b["end"] + 0.22, (b["end"] + nxt["start"]) / 2 + 0.1, nxt["start"] - 0.03)
                    seg = dict(kind="vo", part=p, a0=a0, a1=a1, g0=g, g1=g + (a1 - a0),
                               beats=[x["id"] for x in pb if a0 - 0.05 <= x["start"] < a1])
                    self.segments.append(seg)
                    g = seg["g1"]
                    if b["id"] in CLIP_AFTER:
                        c = clip_info(CLIP_AFTER[b["id"]])
                        c.update(kind="clip", g0=g + 0.08, g1=g + 0.08 + c["dur"])
                        self.segments.append(c)
                        g = c["g1"] + 0.12
                    a0 = a1
            g += PART_GAP
        self.vo_end = g
        self.segments.append(dict(kind="end", g0=g, g1=g + END_SCREEN))
        self.duration = g + END_SCREEN

    def _patch_words(self):
        # whisper dropped "they just send Patrick in" in part 5; times measured from a re-transcription
        ws = self.words[5]
        if not any(norm(w["w"]) == "send" for w in ws if 48 < w["s"] < 52):
            ws[:] = [w for w in ws if not (48.9 < w["s"] < 51.7)]
            for t0, t1, word in [(48.94, 49.4, "they"), (49.5, 49.7, "just"), (49.74, 50.1, "send"),
                                 (50.16, 50.5, "Patrick"), (50.58, 50.9, "in."), (51.78, 52.1, "Now,")]:
                ws.append(dict(w=word, s=t0, e=t1))
            ws.sort(key=lambda w: w["s"])

    def g_of(self, part, a):
        for s in self.segments:
            if s["kind"] == "vo" and s["part"] == part and s["a0"] - 1e-6 <= a <= s["a1"] + 1e-6:
                return s["g0"] + (a - s["a0"])
        raise ValueError(f"time {a} in part {part} not inside a VO segment")

    def beat_g(self, bid):
        b = self.beats[bid]
        return self.g_of(b["part"], b["start"]), self.g_of(b["part"], b["end"])

    def at(self, bid, phrase, end=False, nth=0):
        """Global time when `phrase` is spoken inside beat `bid`."""
        b = self.beats[bid]
        ws = [w for w in self.words[b["part"]] if b["start"] - 0.3 <= w["s"] <= b["end"] + 0.3]
        toks = [norm(x) for x in phrase.replace("-", " ").split() if norm(x)]
        wn = [norm(w["w"]) for w in ws]
        hits = []
        for i in range(len(wn)):
            if wn[i] == toks[0] and wn[i:i + len(toks)] == toks:
                hits.append(i)
        if not hits:  # fuzzy: first token only (logged so it can be checked)
            FUZZY.append((bid, phrase))
            for i in range(len(wn)):
                if wn[i] == toks[0]:
                    hits.append(i)
        if len(hits) <= nth:
            raise KeyError(f"phrase not found in {bid}: {phrase!r}  (heard: {' '.join(wn)})")
        i = hits[nth]
        w = ws[min(i + len(toks) - 1, len(ws) - 1)] if end else ws[i]
        return self.g_of(b["part"], w["e"] if end else w["s"])

    def clip(self, cid):
        return next(s for s in self.segments if s["kind"] == "clip" and s["id"] == cid)

    def words_between(self, g0, g1):
        out = []
        for p, ws in self.words.items():
            for w in ws:
                try:
                    g = self.g_of(p, w["s"])
                except ValueError:
                    continue
                if g0 <= g <= g1:
                    out.append((g, w["w"]))
        return sorted(out)


if __name__ == "__main__":
    tl = Timeline()
    for s in tl.segments:
        print(s["kind"], round(s["g0"], 2), round(s["g1"], 2), s.get("id", ""), s.get("beats", ""))
    print("total", round(tl.duration, 1))
