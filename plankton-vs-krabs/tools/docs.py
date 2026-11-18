"""Regenerate 02_EDIT_PLAN.md and 03_CLIP_LIST.md from tools/timeline.py.  Run: python3 tools/docs.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import timeline as TL

def main():
    vo = open(os.path.join(ROOT, "01_VOICEOVER_CHUNKS.md")).read().split("\n")
    L = ["# EDIT PLAN (auto-generated from tools/timeline.py)", "",
         "Style follows the channel: mostly full-screen episode footage, hard cuts, and restrained documentary graphics "
         "(cream case-file cards, marker math on notebook paper, typed record cards with red circles, pinned screenshots, "
         "yellow-on-navy keyword cards, black quote cards). No shakes/flashes/glitches. **No music.**", "",
         "Each shot starts on the **bold anchor words** and runs until the next shot. `C##` = episode clip, `B##` = dialogue bite "
         "(narration pauses, the show line plays with its own audio), `GFX` = original graphic.", ""]
    used = {}
    for cid in sorted(TL.T):
        head = [l for l in vo if l.startswith(f"### {cid} ")][0][4:]
        L += [f"## {head}", "", "| # | Anchor | Visual | SFX |", "|---|---|---|---|"]
        for i, sh in enumerate(TL.T[cid], 1):
            v = sh["v"]
            if v["type"] == "clip":
                used.setdefault(v["id"], set()).add(cid)
                bits = [f"**{v['id']}**"] + [f"{k}: {v[k]}" for k in ("ss", "zoom", "fx", "text", "stamp", "tag") if v.get(k) not in (None, "")]
                if v.get("freeze"): bits.append("FREEZE")
                if v.get("label"): bits.append("label: " + v["label"][0])
                vis = ", ".join(str(b) for b in bits)
            else:
                a = v["args"]
                for k in ("still",):
                    if a.get(k): used.setdefault(a[k], set()).add(cid)
                for x in a.get("stills", ()):
                    if x: used.setdefault(x, set()).add(cid)
                key = {k: a[k] for k in a if isinstance(a[k], (str, int, float)) and k in ("title", "text", "num", "caption", "p", "k", "note", "n", "lit", "active", "bg", "still")}
                vis = f"GFX `{v['name']}` " + (str(key) if key else "")
            sfx = ", ".join((s if isinstance(s, str) else f"{s[0]}@{s[1]:+}s") for s in sh["sfx"]) or "—"
            at = sh["at"] if not sh["at"].startswith("@+") else f"{sh['at'][2:]}s after VO ends"
            L.append(f"| {i} | **{at}** | {vis.replace('|', '/')} | {sfx} |")
        for anchor, bid, mx in TL.BITES.get(cid, []):
            where = "after the last line" if anchor == "@end" else f"before **{anchor}**"
            L.append(f"| bite | {where} | **{bid}** dialogue bite (≤{mx}s, show audio on) | — |")
        L.append("")
    open(os.path.join(ROOT, "02_EDIT_PLAN.md"), "w").write("\n".join(L) + "\n")

    C = ["# CLIP LIST: what I need from the show", "",
         "Footage comes from your own copy of the episodes. Each `C` clip needs **5–10 s**, starting just before the moment. "
         "The renderer zooms and freezes it and **mutes its audio**.", "",
         "**Dialogue bites (`B` clips)** are the channel's narrate → show line → narrate rhythm. Trim each one tightly around a "
         "single short line (1–4 s). Their audio **is** played, so pick moments where the line is clear and there's little or no "
         "background score (the video has no music). Any bite you skip is simply left out, and the narration runs straight through.", "",
         "**Two ways to hand them over:** trimmed files named by ID (`clips/C01.mp4`, `clips/B03.mkv`, …), or whole episodes "
         "plus `clips/clips.csv`:", "```", "id,file,start,end", "C13,friend_or_foe.mp4,03:12,03:20", "B03,friend_or_foe.mp4,05:44.5,05:47", "```",
         "Missing `C` clips render as labelled placeholder cards.", "",
         "*Fair use:* short clips under commentary, as the channel already does (its descriptions carry a fair-use line, and so does `05_DESCRIPTION.md`).", "",
         "## Episode clips", "", "| ID | Episode | Year | Moment | Used in chunks |", "|---|---|---|---|---|"]
    for k, (ep, yr, d) in TL.CLIPS.items():
        C.append(f"| **{k}** | {ep} | {yr or ''} | {d} | {', '.join(sorted(used.get(k, [])))} |")
    C += ["", "## Dialogue bites (optional, but they're a big part of the channel's feel)", "",
          "| ID | Episode | Year | Line / moment | Plays in chunk |", "|---|---|---|---|---|"]
    where = {bid: cid for cid, bl in TL.BITES.items() for _, bid, _ in bl}
    for k, (ep, yr, d) in TL.BITE_CLIPS.items():
        C.append(f"| **{k}** | {ep} | {yr or ''} | {d} | {where.get(k, '')} |")
    C += ["", "## Thumbnail frames", "- `thumb/krabs.png`: Mr. Krabs looking guilty / side-eye (a background-removed PNG gets the white sticker outline).",
          "- `thumb/plankton.png`: Plankton angry / yelling.", ""]
    open(os.path.join(ROOT, "03_CLIP_LIST.md"), "w").write("\n".join(C) + "\n")
    print("docs written")

if __name__ == "__main__":
    main()
