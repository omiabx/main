"""Render the video.
  python3 tools/render.py --preview            # no VO needed: estimated timing + burned-in script subtitles
  python3 tools/render.py                       # final: uses vo/NN.mp3, aligns with Whisper, outputs MP4
Options: --chunks 01,02  --out path.mp4  --jobs 4
Inputs:  vo/01.mp3..17.mp3 ; clips/C01.mp4 ... or clips/clips.csv (id,file,start,end)"""
import os, re, sys, json, csv, glob, math, wave, argparse, subprocess, difflib
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gfx
from gfx import W, H, text_img, paste, ease_out, ease_back, KRABS, PLANK, WHITE, INK, YELLOW
import timeline as TL

FPS = 30; SR = 48000
BUILD = os.path.join(ROOT, "build"); VO = os.path.join(ROOT, "vo"); CLIPDIR = os.path.join(ROOT, "clips")
SFXDIR = os.path.join(ROOT, "assets", "sfx")


# ---------------- script + timing ----------------
def load_chunks():
    s = open(os.path.join(ROOT, "01_VOICEOVER_CHUNKS.md")).read()
    out = {}
    for m in re.finditer(r"### (\d+) [^\n]*\n```\n(.*?)```", s, re.S):
        out[m.group(1)] = m.group(2).strip()
    return out


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n):
    if n < 20: return [ONES[n]]
    if n < 100: return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000: return [ONES[n // 100], "hundred"] + (num_words(n % 100) if n % 100 else [])
    if 1900 <= n < 2000 or 2010 <= n < 2100:
        return num_words(n // 100) + (num_words(n % 100) if n % 100 else ["hundred"])
    if n < 10000: return num_words(n // 1000) + ["thousand"] + (num_words(n % 1000) if n % 1000 else [])
    return [str(n)]


def toks(text):
    out = []
    for w in re.findall(r"[A-Za-z0-9']+(?:[-.][A-Za-z0-9']+)*", text):
        for p in re.split(r"-", w):
            p = p.lower().replace("'", "").replace(".", "")
            m = re.fullmatch(r"(\d+)(st|nd|rd|th)?", p)
            if m: out += num_words(int(m.group(1)))
            elif p: out.append(p)
    return out


def estimate_words(text):
    """fake timing for preview: list of (token, start) + total duration"""
    t = 0.25; res = []
    for para in text.split("\n\n"):
        for w in para.split():
            for tk in toks(w):
                res.append((tk, t)); t += 0.30
            if w.endswith("..."): t += 0.55
            elif w.endswith((".", "?", "!")): t += 0.32
            elif w.endswith((",", ":")): t += 0.12
        t += 0.35
    return res, t


_model = None
def whisper_words(path, prompt):
    global _model
    from faster_whisper import WhisperModel
    if _model is None: _model = WhisperModel("small.en", device="cpu", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    audio = np.frombuffer(raw, np.float32).copy()
    segs, info = _model.transcribe(audio, word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in s.words: words.append((w.word, w.start, w.end))
    return words, info.duration


def align(cid, text):
    """returns script tokens with times, VO duration"""
    mp3 = os.path.join(VO, cid + ".mp3")
    stoks = toks(text)
    cache = os.path.join(BUILD, f"align_{cid}.json")
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(mp3):
        words, dur = json.load(open(cache))
    else:
        words, dur = whisper_words(mp3, text)
        json.dump([words, dur], open(cache, "w"))
    wt = []
    for w, s, e in words:
        for tk in toks(w): wt.append((tk, s))
    sm = difflib.SequenceMatcher(a=stoks, b=[x[0] for x in wt], autojunk=False)
    times = [None] * len(stoks)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n): times[a + k] = wt[b + k][1]
    # interpolate gaps
    known = [i for i, v in enumerate(times) if v is not None]
    if not known: times = list(np.linspace(0, dur, len(stoks), endpoint=False))
    else:
        for i in range(len(times)):
            if times[i] is None:
                lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
                if lo is None: times[i] = max(0, times[hi] - (hi - i) * .3)
                elif hi is None: times[i] = min(dur, times[lo] + (i - lo) * .3)
                else: times[i] = times[lo] + (times[hi] - times[lo]) * (i - lo) / (hi - lo)
    matched = sum(1 for _, _, n in sm.get_matching_blocks() for _ in range(n))
    print(f"  [{cid}] aligned {matched}/{len(stoks)} words, VO {dur:.1f}s")
    return list(zip(stoks, times)), dur


def resolve(cid, shots, words, vo_dur, tail):
    tokens = [w for w, _ in words]; pos = 0; out = []
    total = vo_dur + tail
    for sh in shots:
        a = sh["at"]
        if a.startswith("@+"):
            t = vo_dur + float(a[2:])
        else:
            at = toks(a); found = None
            for i in range(pos, len(tokens) - len(at) + 1):
                if tokens[i:i + len(at)] == at: found = i; break
            if found is None: raise SystemExit(f"[{cid}] anchor not found in order: {a!r}")
            pos = found + 1; t = words[found][1]
        out.append([max(0, t - 0.04), sh])
    out[0][0] = 0.0
    # enforce monotonic, min length
    for i in range(1, len(out)):
        out[i][0] = max(out[i][0], out[i - 1][0] + 0.35)
    res = []
    for i, (t, sh) in enumerate(out):
        end = out[i + 1][0] if i + 1 < len(out) else total
        res.append({"start": t, "end": max(end, t + .1), **sh})
    return res, total


# ---------------- clips ----------------
def clip_index():
    idx = {}
    csvp = os.path.join(CLIPDIR, "clips.csv")
    if os.path.exists(csvp):
        for row in csv.reader(open(csvp)):
            if not row or row[0].startswith("#") or row[0].lower() == "id": continue
            cid, f = row[0].strip(), row[1].strip()
            st = parse_ts(row[2]) if len(row) > 2 and row[2].strip() else 0
            en = parse_ts(row[3]) if len(row) > 3 and row[3].strip() else None
            p = f if os.path.isabs(f) else os.path.join(CLIPDIR, f)
            if os.path.exists(p): idx[cid] = (p, st, en)
    for p in glob.glob(os.path.join(CLIPDIR, "C*.*")) + glob.glob(os.path.join(CLIPDIR, "B*.*")):
        cid = os.path.splitext(os.path.basename(p))[0]
        if cid not in idx and not p.endswith(".csv"): idx[cid] = (p, 0, None)
    return idx


def parse_ts(s):
    s = s.strip(); parts = [float(x) for x in s.split(":")]
    v = 0
    for x in parts: v = v * 60 + x
    return v


def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 5.0


def read_frames(path, start, n):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", path, "-frames:v", str(n), "-vf",
           f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    k = len(raw) // (W * H * 3)
    fr = [np.frombuffer(raw, np.uint8, W * H * 3, i * W * H * 3).reshape(H, W, 3) for i in range(k)]
    return fr


# ---------------- effects ----------------
_vig = None
def vignette():
    global _vig
    if _vig is None:
        x = np.linspace(-1, 1, W)[None, :]; y = np.linspace(-1, 1, H)[:, None]
        _vig = (1 - 0.28 * np.clip((x ** 2 + y ** 2) - .25, 0, None))[..., None].astype(np.float32)
    return _vig


def apply_fx(a, fx, fi):
    if not fx: return a
    f = a.astype(np.float32)
    if fx == "sepia":
        g = f @ np.array([[.393, .349, .272], [.769, .686, .534], [.189, .168, .131]], np.float32)
        f = f * .62 + g * .38
    elif fx == "bw":
        g = f.mean(2, keepdims=True); f = np.repeat(g, 3, 2) * 1.05
    elif fx == "dark":
        f = f * 0.62
    elif fx == "vhs":
        return a
    return np.clip(f, 0, 255).astype(np.uint8)


def zoom_crop(im, z, ox=0, oy=0):
    if abs(z - 1) < .002 and not ox and not oy: return im
    z = max(z, W / (W - 2 * min(abs(ox), W * .3)), H / (H - 2 * min(abs(oy), H * .3)))
    w, h = W / z, H / z
    x0 = min(max((W - w) / 2 + ox, 0), W - w); y0 = min(max((H - h) / 2 + oy, 0), H - h)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))


def strip(ti, bg, alpha=180, padx=26, pady=12):
    im = Image.new("RGBA", (ti.width + 2 * padx, ti.height + 2 * pady), bg + (alpha,))
    im.paste(ti, (padx, pady), ti); return im


def overlays(c, sh, lt, dur, chapter, subtitle):
    v = sh["v"]
    if v.get("tag"):
        im = strip(text_img(v["tag"], 34, "type", (238, 234, 224)), (10, 10, 12), 170)
        paste(c, im, 50 + im.width / 2, H - 80, 1, min(1, lt / .25))
    if v.get("label"):
        txt, col = v["label"]; im = strip(text_img(txt, 50, "cond", WHITE), col, 235)
        paste(c, im, 50 + im.width / 2, 80, 1, min(1, lt / .1))
    if v.get("text"):
        ti = text_img(v["text"], 96, "cond", gfx.YELLOW, 7, gfx.INK)
        paste(c, ti, W / 2, H * .83, min(1, 1700 / ti.width) * (0.96 + 0.04 * ease_out(lt / .2)), min(1, lt / .1))
    if v.get("stamp"):
        gfx.scrawl(c, v["stamp"].lower(), W * .68, H * .38, lt - .1, gfx.RED, 92, -6)
    if subtitle:
        ti = text_img(subtitle, 34, "bold", WHITE)
        bx = Image.new("RGBA", (ti.width + 40, ti.height + 20), (0, 0, 0, 170)); bx.paste(ti, (20, 10), ti)
        paste(c, bx, W / 2, H - 40 - bx.height / 2 + 20)


_still_cache = {}
def get_still(cid, cidx, ss=1.0):
    key = (cid, ss)
    if key not in _still_cache:
        im = None
        if cid in cidx:
            p, st, en = cidx[cid]; L = (en - st) if en else probe_dur(p) - st
            fr = read_frames(p, st + min(ss, max(0, L - .3)), 1)
            if fr: im = Image.fromarray(fr[0])
        _still_cache[key] = im
    return _still_cache[key]


def gfx_args(v, cidx):
    a = dict(v.get("args", {}))
    if "stills" in a: a["stills"] = tuple(get_still(x, cidx) if x else None for x in a["stills"])
    if "still" in a:
        if "label" not in a: a["label"] = a["still"]
        a["still"] = get_still(a["still"], cidx, a.pop("still_ss", 1.0))
    return a


def render_chunk(job):
    cid, shots, total, chapter, subs, out = job
    cidx = clip_index()
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    nframes_total = int(round(total * FPS)); fi = 0
    for si, sh in enumerate(shots):
        f0 = int(round(sh["start"] * FPS)); f1 = nframes_total if si == len(shots) - 1 else int(round(sh["end"] * FPS))
        n = max(1, f1 - f0); dur = n / FPS; v = sh["v"]
        frames = None; gargs = gfx_args(v, cidx) if v["type"] == "gfx" else None
        if v["type"] == "clip":
            if v["id"] in cidx:
                p, st, en = cidx[v["id"]]
                L = (en - st) if en else probe_dur(p) - st
                ss = min(v.get("ss", 0), max(0, L - 0.3))
                frames = read_frames(p, st + ss, 1 if v.get("freeze") else min(n, int(max(1, (L - ss) * FPS))))
            if not frames:
                desc = TL.CLIPS.get(v["id"], ("", None, ""))
                frames = [np.array(gfx.placeholder(v["id"], f"{desc[0]}: {desc[2]}", 0))]
        for k in range(n):
            lt = k / FPS
            if v["type"] == "clip":
                base = Image.fromarray(apply_fx(frames[min(k, len(frames) - 1)], v.get("fx"), fi))
                p = k / max(1, n - 1); zm = v.get("zoom")
                z = {"in": 1.0 + .06 * p, "out": 1.08 - .07 * p, "punch": 1.16 + .04 * p}.get(zm, 1.0)
                if v.get("bite"): z = 1.0 + .03 * p
            else:
                base = gfx.GFX[v["name"]](lt, dur, **gargs); z = 1.0
            img = zoom_crop(base, z)
            if v["type"] == "clip":
                a = (np.asarray(img).astype(np.float32) * vignette()).astype(np.uint8); img = Image.fromarray(a)
            sub = None
            if subs:
                tt = sh["start"] + lt
                for (s0, s1, txt) in subs:
                    if s0 <= tt < s1: sub = txt; break
            overlays(img, sh, lt, dur, None, sub)
            enc.stdin.write(img.tobytes()); fi += 1
    enc.stdin.close(); enc.wait()
    return out


# ---------------- audio ----------------
def load_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
    return a


def decode_mono(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def anchor_time(words, anchor):
    tokens = [w for w, _ in words]; at = toks(anchor)
    for i in range(len(tokens) - len(at) + 1):
        if tokens[i:i + len(at)] == at: return words[i][1]
    raise SystemExit(f"anchor not found: {anchor!r}")


def apply_bites(cid, shots, total, words, vo_dur):
    """Insert show-dialogue bites: the VO pauses, the clip plays with its own audio, then VO resumes."""
    cidx = clip_index(); ins = []; pos_tokens = 0
    for anchor, bid, mx in TL.BITES.get(cid, []):
        if bid not in cidx: continue
        p, st, en = cidx[bid]; L = (en - st) if en else probe_dur(p) - st
        d = max(.5, min(L, mx))
        tb = vo_dur + .25 if anchor == "@end" else max(0, anchor_time(words, anchor) - .08)
        ins.append((tb, bid, d, p, st))
    ins.sort()
    def shift(tt):
        return tt + sum(d for (tb, _, d, _, _) in ins if tb <= tt + 1e-6)
    out = []
    for sh in shots:
        sh = dict(sh); sh["start"] = shift(sh["start"]) if sh["start"] > 0 else 0.0; out.append(sh)
    acc = 0.0; bite_audio = []
    for (tb, bid, d, p, st) in ins:
        bs = tb + acc
        out.append({"start": bs, "end": bs + d, "at": "(bite)", "v": {"type": "clip", "id": bid, "bite": True}, "sfx": []})
        bite_audio.append((bs, p, st, d)); acc += d
    out.sort(key=lambda x: x["start"])
    new_total = total + acc
    for i, sh in enumerate(out):
        sh["end"] = out[i + 1]["start"] if i + 1 < len(out) else new_total
    # resume shots that were interrupted by a bite: the shot after a bite continues the pre-bite visual
    bounds = [0.0] + [tb for (tb, *_r) in ins] + [vo_dur + 30]
    segs = []; acc = 0.0
    for i in range(len(bounds) - 1):
        segs.append((bounds[i], bounds[i + 1], bounds[i] + acc))
        if i < len(ins): acc += ins[i][2]
    return out, new_total, segs, bite_audio, shift


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", action="store_true")
    ap.add_argument("--chunks"); ap.add_argument("--out"); ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--reuse", action="store_true")
    a = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    chunks = load_chunks()
    ids = a.chunks.split(",") if a.chunks else sorted(chunks)
    plan = []; t_global = 0.0; audio_events = []; vo_parts = []; chapter = None; chapters = []; bites_global = []
    for cid in ids:
        text = chunks[cid]
        have_vo = os.path.exists(os.path.join(VO, cid + ".mp3")) and not a.preview
        if have_vo: words, vo_dur = align(cid, text)
        else: words, vo_dur = estimate_words(text)
        tail = TL.TAIL.get(cid, .3)
        shots, total = resolve(cid, TL.T[cid], words, vo_dur, tail)
        shots, total, vo_segs, bite_audio, shift = apply_bites(cid, shots, total, words, vo_dur)
        for (ccid, anchor, name) in TL.CHAPTERS:
            if ccid == cid:
                tt = 0.0 if anchor is None else anchor_time(words, anchor)
                chapters.append((t_global + shift(tt), name))
        for sh in shots:
            v = sh["v"]
            if v["type"] == "gfx" and v["name"] in gfx.PAPER_CARDS and not any(
                    (x if isinstance(x, str) else x[0]) in ("paper", "type", "type_burst") or (not isinstance(x, str) and x[1] <= .15 and False) for x in sh["sfx"]):
                sh["sfx"] = [("pin" if v["name"] in ("polaroid", "three_versions") else "paper", 0, .55)] + list(sh["sfx"])
        chapter = TL.CH.get(cid, chapter)
        subs = None
        if a.preview:
            # sentence subtitles from estimated word times
            sents = re.split(r"(?<=[.?!])\s+", text.replace("\n", " ")); subs = []; wi = 0
            for s in sents:
                n = len(toks(s))
                if n == 0: continue
                st = words[wi][1]; en = words[wi + n][1] if wi + n < len(words) else total
                subs.append((st, en, s if len(s) < 95 else s[:92] + "...")); wi += n
        plan.append((cid, shots, total, chapter, subs, os.path.join(BUILD, f"v_{cid}.mp4")))
        for sh in shots:
            for s in sh["sfx"]:
                if isinstance(s, str): s = (s, 0, 1)
                name, off, vol = s[0], s[1], s[2]
                rep, iv = (s[3], s[4]) if len(s) > 4 else (1, 0)
                for r in range(rep):
                    audio_events.append((t_global + sh["start"] + off + r * iv, name, vol))
        vo_parts.append((t_global, os.path.join(VO, cid + ".mp3") if have_vo else None, vo_segs))
        for (bt, bp, bst, bd) in bite_audio: bites_global.append((t_global + bt, bp, bst, bd))
        t_global += total
    json.dump([[p[0], [{k: (v if k != "v" else v) for k, v in s.items()} for s in p[1]], p[2]] for p in plan],
              open(os.path.join(BUILD, "plan.json"), "w"), indent=1, default=str)
    print(f"total runtime {t_global / 60:.2f} min, {sum(len(p[1]) for p in plan)} shots, {len(audio_events)} sfx hits")

    todo = plan
    if a.reuse:
        todo = [p for p in plan if not (os.path.exists(p[5]) and abs(probe_dur(p[5]) - round(p[2] * FPS) / FPS) < .1)]
        print("  reusing", len(plan) - len(todo), "chunks")
    with ProcessPoolExecutor(a.jobs) as ex:
        for out in ex.map(render_chunk, todo): print("  rendered", os.path.basename(out))

    # audio mix
    n = int(t_global * SR) + SR; mixv = np.zeros(n, np.float32); mixs = np.zeros(n, np.float32)
    vo_rms = []
    for t0, p, segs in vo_parts:
        if p:
            a_ = decode_mono(p); vo_rms.append(np.sqrt(np.mean(a_[np.abs(a_) > .01] ** 2)) if np.any(np.abs(a_) > .01) else .1)
            for (v0, v1, at) in segs:
                seg = a_[int(v0 * SR):int(v1 * SR)]; s = int((t0 + at) * SR)
                fade = min(len(seg), int(.01 * SR))
                if fade: seg = seg.copy(); seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
                mixv[s:s + len(seg)] += seg[:n - s]
    target = float(np.median(vo_rms)) if vo_rms else .1
    for (t0, p, st, d) in bites_global:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{st:.3f}", "-i", p, "-t", f"{d:.3f}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True).stdout
        b = np.frombuffer(raw, np.float32).copy()
        if not len(b): continue
        act = b[np.abs(b) > .01]; r = np.sqrt(np.mean(act ** 2)) if len(act) else .1
        b *= min(4.0, target * .9 / max(r, 1e-4))
        f_ = min(len(b), int(.03 * SR)); b[:f_] *= np.linspace(0, 1, f_); b[-f_:] *= np.linspace(1, 0, f_)
        s = int(t0 * SR); mixv[s:s + len(b)] += b[:n - s]
    json.dump(chapters, open(os.path.join(BUILD, "chapters.json"), "w"))
    cache = {}
    for t0, name, vol in audio_events:
        if name not in cache: cache[name] = load_wav(os.path.join(SFXDIR, name + ".wav"))
        a_ = cache[name]; s = max(0, int(t0 * SR)); e = min(n, s + len(a_))
        mixs[s:e] += a_[:e - s] * vol
    # keep SFX under the voice: ~-8 dB relative, light duck while VO active
    vo_env = np.convolve(np.abs(mixv), np.ones(2400) / 2400, "same")
    duck = 1 - 0.45 * np.clip(vo_env / 0.05, 0, 1)
    mix = mixv + mixs * 0.34 * duck
    peak = np.max(np.abs(mix)) or 1
    if peak > .98: mix = mix / peak * .98
    wav = os.path.join(BUILD, "mix.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

    lst = os.path.join(BUILD, "concat.txt")
    open(lst, "w").write("".join(f"file '{p[5]}'\n" for p in plan))
    out = a.out or os.path.join(ROOT, "output", "preview.mp4" if a.preview else "plankton_vs_krabs_FINAL.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # two-pass loudness normalisation to -14 LUFS / -1.5 dBTP
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    mj = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={mj['input_i']}:measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}"
          f":measured_thresh={mj['input_thresh']}:offset={mj['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", ln, "-ac", "2", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    # loudnorm's linear mode can undershoot; measure and apply a final clean gain trim toward -14 LUFS
    r = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    gain = min(-14 - I, -1.5 - pk)
    if abs(gain) > .2:
        tmp = out + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", f"volume={gain:.2f}dB",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, out)
    print(f"wrote {out}  (loudness {I + gain:.1f} LUFS)")


if __name__ == "__main__":
    main()
