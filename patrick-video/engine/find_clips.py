"""Search Dailymotion for each clip moment and list candidates with their best resolution."""
import json, subprocess, sys, urllib.parse, urllib.request
Q = {
 "C01": ["spongebob help wanted", "spongebob help wanted patrick"],
 "C02": ["pet sitter pat", "spongebob pet sitter pat"],
 "C03": ["spongebob firmly grasp it", "spongebob jellyfishing"],
 "C04": ["spongebob secret box", "inner machinations of my mind are an enigma"],
 "C05": ["spongebob secret box"],
 "C06": ["push it somewhere else spongebob", "spongebob sandy and the worm"],
 "C07": ["dumber than a sack of diapers", "spongebob im with stupid"],
 "C08": ["spongebob valentine's day patrick", "patrick valentine rampage"],
 "C09": ["patrick smartpants", "patrick danger cliff"],
 "C10": ["patrick smartpants", "spongebob brain coral"],
 "C11": ["spongebob that's no lady", "that's a seven patricia"],
 "C12": ["pet sitter pat", "spongebob snail tales"],
 "C13": ["no this is patrick", "is this the krusty krab"],
}
out = {}
for cid, qs in Q.items():
    seen = {}
    for q in qs:
        u = "https://api.dailymotion.com/videos?" + urllib.parse.urlencode(dict(
            search=q, fields="id,title,duration,owner.username,height", limit=8))
        for v in json.load(urllib.request.urlopen(u)).get("list", []):
            if v["duration"] <= 1500 and v["id"] not in seen:
                seen[v["id"]] = v
    out[cid] = list(seen.values())
    print("==", cid)
    for v in out[cid]:
        print(f"   {v['duration']:5}s  h={v.get('height')}  {v['id']}  {v['title'][:80]}")
json.dump(out, open("work/dm_candidates.json", "w"), indent=1)
