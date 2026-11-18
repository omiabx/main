#!/usr/bin/env python3
"""
fetch_clips.py: find and download the short episode clips the edit needs (C01–C45 + dialogue bites B01–B11).

HOW IT WORKS (per clip)
  1. Searches YouTube for the moment (prefers official SpongeBob / Nickelodeon uploads).
  2. Reads the video's English captions and looks for that moment's keywords to locate it.
  3. Downloads ONLY that short section (a few seconds) as clips/<ID>.mp4.
  If it can't locate the moment, it downloads the short candidate video(s) to clips/_candidates/
  and lists them in clips/review.csv so you can trim by hand (or just send me start/end times).

SETUP (once)
  pip install -U yt-dlp
  + ffmpeg on your PATH  (Windows: `winget install ffmpeg`, Mac: `brew install ffmpeg`)

RUN
  python fetch_clips.py                     # everything
  python fetch_clips.py --only C13,C16,B03  # just some
  python fetch_clips.py --dry-run           # show what it would pick, download nothing
  python fetch_clips.py --redo C13          # replace one you didn't like
  python fetch_clips.py --cookies-browser chrome   # if YouTube asks you to "confirm you're not a bot"

AFTER
  Check clips/_preview/*.jpg (one frame per clip) and clips/review.csv, fix any misses, then send me the clips/ folder.
  clips/sources.csv records the URL + timestamps of every clip (handy for your description credits).

These are short excerpts for commentary/criticism, which is how your channel already uses them. Clips are only ever
a few seconds long; the script never downloads a full episode on purpose (candidates are capped at 8 minutes).
"""
import argparse, csv, glob, os, re, shutil, subprocess, sys

try:
    import yt_dlp
    from yt_dlp.utils import download_range_func
except ImportError:
    sys.exit("yt-dlp is missing. Run:  pip install -U yt-dlp")

# id: (search query, caption keywords that mark the moment, seconds to keep)
CLIPS = {
    "C01": ("SpongeBob Plankton first episode I went to college", ["college"], 8),
    "C02": ("SpongeBob Krusty Krab outside", ["krusty krab"], 6),
    "C03": ("SpongeBob Chum Bucket Plankton restaurant", ["chum bucket"], 6),
    "C04": ("SpongeBob Plankton Karen computer wife", ["karen"], 6),
    "C05": ("SpongeBob Plankton's Pet Spot amoeba", ["spot"], 6),
    "C06": ("SpongeBob Plankton's Regular customer chum", ["regular", "chum"], 8),
    "C07": ("SpongeBob Friend or Foe young Mr Krabs Plankton kids", ["best friend", "friends"], 8),
    "C08": ("SpongeBob Friend or Foe SpongeBob asks Mr Krabs about Plankton", ["why", "hate", "plankton"], 8),
    "C09": ("SpongeBob Friend or Foe Mr Krabs version of the story", ["evil", "children", "burger"], 8),
    "C10": ("SpongeBob Friend or Foe Krabs thrown in garbage", ["garbage", "trash", "dump"], 6),
    "C11": ("SpongeBob Friend or Foe Plankton's version", ["evil", "krabs", "version"], 8),
    "C12": ("SpongeBob Friend or Foe Karen tells what really happened", ["karen", "really", "truth"], 8),
    "C13": ("SpongeBob Friend or Foe penny balloon carnival", ["penny", "balloon"], 8),
    "C14": ("SpongeBob Friend or Foe Stinky's Burgers", ["stinky", "business"], 8),
    "C15": ("SpongeBob Friend or Foe burger stand dump", ["burger", "customer"], 8),
    "C16": ("SpongeBob Friend or Foe old man Jenkins burger", ["jenkins"], 8),
    "C17": ("SpongeBob Friend or Foe recipe ripped in half fight", ["recipe", "fault"], 8),
    "C18": ("SpongeBob Friend or Foe Krabby Patty invented", ["krabby patty", "delicious"], 8),
    "C19": ("SpongeBob Friend or Foe Plankton chum burger revenge", ["chum", "revenge", "formula"], 8),
    "C20": ("SpongeBob Plankton controls SpongeBob brain", ["brain", "control"], 8),
    "C21": ("SpongeBob Imitation Krabs robot Mr Krabs", ["robot"], 8),
    "C22": ("SpongeBob F.U.N. Plankton SpongeBob friends", ["friend", "fun"], 8),
    "C23": ("SpongeBob Plankton fails to steal formula compilation", ["formula"], 12),
    "C24": ("SpongeBob Movie Plankton steals King Neptune's crown", ["crown", "neptune"], 8),
    "C25": ("SpongeBob Movie Planktopolis bucket helmets", ["planktopolis", "bucket"], 8),
    "C26": ("SpongeBob Movie Goofy Goober Rock buckets", ["goofy goober", "rock"], 8),
    "C27": ("SpongeBob Single Cell Anniversary Karen formula", ["anniversary", "formula"], 8),
    "C28": ("SpongeBob Plankton's Regular Karen pays", ["paid", "pay"], 8),
    "C29": ("SpongeBob Plankton's Regular Krusty Krab chum menu", ["chum", "menu"], 8),
    "C30": ("SpongeBob Enemy In-Law Plankton dating Mama Krabs", ["mother", "mom", "mama"], 8),
    "C31": ("SpongeBob One Coarse Meal Krabs dresses as Pearl whale", ["whale", "pearl"], 10),
    "C32": ("SpongeBob One Coarse Meal SpongeBob too far", ["too far", "enough"], 8),
    "C33": ("SpongeBob Born Again Krabs 62 cents Flying Dutchman", ["62", "sixty two", "cents"], 8),
    "C34": ("SpongeBob Born Again Krabs Squidward 62 cents", ["cents", "soul"], 8),
    "C35": ("SpongeBob Plankton Retires", ["retire", "retirement"], 8),
    "C36": ("SpongeBob Plankton Retires ceiling fan spying", ["fan", "spy"], 8),
    "C37": ("SpongeBob Plankton Retires robot", ["robot"], 8),
    "C38": ("Plankton The Movie Netflix trailer Karen", ["karen"], 8),
    "C39": ("SpongeBob Friend or Foe ending formula chase", ["formula", "friends"], 10),
    "C40": ("Mr Krabs money", ["money"], 6),
    "C41": ("Krabby Patty secret formula", ["secret formula", "formula"], 6),
    "C43": ("Plankton evil laugh", ["laugh", "laughter"], 5),
    "C44": ("SpongeBob Pearl Mr Krabs daughter", ["pearl", "daddy"], 5),
    "C45": ("SpongeBob Friend or Foe kids bully Krabs Plankton", ["loser", "nerd", "bully"], 6),
    # dialogue bites: one short, clear line each (their audio IS used, so prefer moments with little background music)
    "B01": ("SpongeBob Plankton first episode Krabs formula threat", ["formula", "business"], 3.5),
    "B02": ("SpongeBob Friend or Foe SpongeBob asks Mr Krabs about Plankton", ["why", "plankton"], 4),
    "B03": ("SpongeBob Friend or Foe old man Jenkins", ["jenkins"], 3.5),
    "B04": ("SpongeBob Friend or Foe Krabs Plankton argue recipe", ["fault", "recipe"], 4),
    "B05": ("SpongeBob Plankton's Regular Karen paying", ["paid", "pay"], 4),
    "B06": ("SpongeBob Enemy In-Law Mr Krabs mother Plankton", ["mother"], 3.5),
    "B07": ("SpongeBob One Coarse Meal SpongeBob too far", ["too far"], 4),
    "B08": ("SpongeBob Born Again Krabs Squidward 62 cents", ["more", "cents"], 3.5),
    "B09": ("SpongeBob Plankton Retires robot Mr Krabs", ["robot"], 4),
    "B10": ("SpongeBob Friend or Foe ending formula", ["formula"], 4),
    "B11": ("SpongeBob Plankton I went to college", ["college"], 3),
}

OFFICIAL = re.compile(r"spongebob|nickelodeon|nick\b|paramount|netflix", re.I)
# meme edits / reuploads that would put the wrong (or edited) footage in the video
JUNK = re.compile(r"\bhood\b|meme|\bytp\b|poop|parody|remix|reverse|earrape|ear rape|\bbut\b|\bif\b|1 ?hour|10 ?hours|loop|"
                  r"in real life|\birl\b|\bai\b|edit\b|edited|animatic|fan ?made|roblox|minecraft|reaction|react", re.I)
BOT_HITS = [0]


class _Quiet:
    def debug(self, m): pass
    def info(self, m): pass
    def warning(self, m): pass
    def error(self, m):
        if "not a bot" in m or "Sign in to confirm" in m: BOT_HITS[0] += 1
MAX_CANDIDATE_SECONDS = 8 * 60


def ydl_base(args, quiet=True):
    o = {"quiet": quiet, "no_warnings": True, "noprogress": True, "logger": _Quiet()}
    if args.cookies_browser: o["cookiesfrombrowser"] = (args.cookies_browser,)
    return o


def search(args, query, n):
    with yt_dlp.YoutubeDL({**ydl_base(args), "extract_flat": True}) as y:
        res = y.extract_info(f"ytsearch{n}:{query}", download=False) or {}
    out = []
    for e in res.get("entries") or []:
        if not e or not e.get("id"): continue
        if JUNK.search(e.get("title") or ""): continue
        out.append({"id": e["id"], "url": f"https://www.youtube.com/watch?v={e['id']}", "title": e.get("title") or "",
                    "channel": e.get("channel") or e.get("uploader") or "", "duration": e.get("duration") or 0})
    return out


def rank(cands, query, kws):
    words = set(re.findall(r"[a-z0-9']+", query.lower())) | {w for k in kws for w in k.split()}
    def score(c):
        s = 0
        if OFFICIAL.search(c["channel"]): s += 5
        s += len(words & set(re.findall(r"[a-z0-9']+", c["title"].lower())))
        if c["duration"] and c["duration"] > MAX_CANDIDATE_SECONDS: s -= 4
        if re.search(r"full episode|full movie|compilation", c["title"], re.I) and "compilation" not in query.lower(): s -= 2
        return s
    return sorted(cands, key=score, reverse=True)


def vtt_cues(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    cues = []
    for m in re.finditer(r"(\d+):(\d\d):(\d\d)\.(\d+) --> [^\n]*\n(.*?)(?:\n\n|\Z)", txt, re.S):
        h, mi, s, ms, body = m.groups()
        t = int(h) * 3600 + int(mi) * 60 + int(s) + float("0." + ms)
        body = re.sub(r"<[^>]+>", "", body).replace("\n", " ").strip().lower()
        if body and (not cues or body != cues[-1][1]): cues.append((t, body))
    return cues


def locate(args, url, kws, tmp):
    """returns caption time (s) of the best keyword hit, or None"""
    for f in glob.glob(os.path.join(tmp, "*")): os.remove(f)
    o = {**ydl_base(args), "skip_download": True, "writesubtitles": True, "writeautomaticsub": True,
         "subtitleslangs": ["en", "en-US", "en-GB", "en.*"], "subtitlesformat": "vtt", "outtmpl": os.path.join(tmp, "sub.%(ext)s")}
    try:
        with yt_dlp.YoutubeDL(o) as y: y.download([url])
    except Exception:
        return None
    vtts = glob.glob(os.path.join(tmp, "*.vtt"))
    if not vtts: return None
    cues = vtt_cues(vtts[0]); best = (0, None)
    for i, (t, _) in enumerate(cues):
        window = " ".join(b for _, b in cues[max(0, i - 1): i + 3])
        hits = sum(window.count(k.lower()) for k in kws)
        if hits > best[0]: best = (hits, t)
    return best[1]


def download_section(args, url, start, end, out_noext):
    o = {**ydl_base(args), "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/b",
         "merge_output_format": "mp4", "outtmpl": out_noext + ".%(ext)s",
         "download_ranges": download_range_func(None, [(max(0, start), end)]), "force_keyframes_at_cuts": True}
    with yt_dlp.YoutubeDL(o) as y: y.download([url])


def download_whole(args, url, out_noext):
    o = {**ydl_base(args), "format": "bv*[height<=1080]+ba/b[height<=1080]/b", "merge_output_format": "mp4", "outtmpl": out_noext + ".%(ext)s"}
    with yt_dlp.YoutubeDL(o) as y: y.download([url])


def preview(clip, jpg):
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", clip, "-frames:v", "1", "-vf", "scale=640:-2", jpg])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="clips", help="output folder (default: ./clips)")
    ap.add_argument("--only", help="comma-separated IDs, e.g. C13,B03")
    ap.add_argument("--redo", help="comma-separated IDs to re-download even if present")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--candidates", type=int, default=6, help="search results to consider per clip")
    ap.add_argument("--cookies-browser", help="chrome / firefox / edge / brave, if YouTube blocks you")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"): sys.exit("ffmpeg not found on PATH (needed to cut sections). Install it first.")

    out = args.out; tmp = os.path.join(out, "_tmp"); cand_dir = os.path.join(out, "_candidates"); prev = os.path.join(out, "_preview")
    for d in (out, tmp, cand_dir, prev): os.makedirs(d, exist_ok=True)
    ids = [i.strip().upper() for i in args.only.split(",")] if args.only else list(CLIPS)
    redo = {i.strip().upper() for i in args.redo.split(",")} if args.redo else set()
    ids += [r for r in redo if r not in ids]

    src_path = os.path.join(out, "sources.csv"); rev_path = os.path.join(out, "review.csv")
    sources = {r["id"]: r for r in csv.DictReader(open(src_path, encoding="utf-8"))} if os.path.exists(src_path) else {}
    review = []
    ok = 0
    for cid in ids:
        if cid not in CLIPS: print(f"{cid}: unknown id, skipped"); continue
        query, kws, secs = CLIPS[cid]
        have = [p for p in glob.glob(os.path.join(out, cid + ".*")) if not p.endswith(".part")]
        if have and cid not in redo: print(f"{cid}: already have {os.path.basename(have[0])}"); ok += 1; continue
        for p in have: os.remove(p)
        print(f"{cid}: searching '{query}' ...", flush=True)
        try:
            cands = rank(search(args, query, args.candidates), query, kws)
        except Exception as e:
            print(f"   search failed: {e}"); review.append({"id": cid, "reason": "search failed", "candidates": ""}); continue
        picked = None
        for c in cands[:3]:
            if c["duration"] and c["duration"] > 3 * 3600: continue
            t = locate(args, c["url"], kws, tmp)
            if t is not None: picked = (c, t); break
        if picked:
            c, t = picked
            lead = 0.3 if cid.startswith("B") else 1.0
            start, end = max(0, t - lead), max(0, t - lead) + secs
            print(f"   -> {c['title'][:70]!r} [{c['channel']}] @ {start:.1f}-{end:.1f}s")
            if not args.dry_run:
                try:
                    download_section(args, c["url"], start, end, os.path.join(out, cid))
                    got = [p for p in glob.glob(os.path.join(out, cid + ".*")) if not p.endswith(".part")]
                    if got: preview(got[0], os.path.join(prev, cid + ".jpg")); ok += 1
                    sources[cid] = {"id": cid, "url": c["url"], "title": c["title"], "channel": c["channel"],
                                    "start": f"{start:.2f}", "end": f"{end:.2f}", "method": "captions"}
                except Exception as e:
                    print(f"   download failed: {e}"); review.append({"id": cid, "reason": f"download failed: {e}", "candidates": c["url"]})
        else:
            short = [c for c in cands if c["duration"] and c["duration"] <= MAX_CANDIDATE_SECONDS][:2]
            print(f"   couldn't locate the moment from captions; {len(short)} short candidate(s) for manual trim")
            if not args.dry_run:
                for k, c in enumerate(short):
                    try: download_whole(args, c["url"], os.path.join(cand_dir, f"{cid}__{k + 1}"))
                    except Exception as e: print(f"   candidate download failed: {e}")
            review.append({"id": cid, "reason": "moment not found in captions (trim from _candidates/ or send me times)",
                           "candidates": " | ".join(f"{c['url']} ({c['title'][:50]})" for c in short)})

    with open(src_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "url", "title", "channel", "start", "end", "method"]); w.writeheader()
        for k in sorted(sources): w.writerow(sources[k])
    with open(rev_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "reason", "candidates"]); w.writeheader()
        for r in review: w.writerow(r)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nDone. {ok}/{len(ids)} clips ready in {out}/   |   {len(review)} need review -> {rev_path}")
    print(f"Glance through {prev}/ to check each auto-picked clip shows the right moment.")
    if BOT_HITS[0]:
        print(f"\nYouTube asked to 'confirm you're not a bot' {BOT_HITS[0]} time(s). Re-run with your browser's login, e.g.:")
        print("  python fetch_clips.py --cookies-browser chrome      (it skips clips you already have)")


if __name__ == "__main__":
    main()
