import json, subprocess, sys, time
Q = {"C03": "spongebob firmly grasp it", "C06": "spongebob push it somewhere else", "C07": "spongebob sack of diapers",
     "C08": "spongebob valentines day patrick", "C09": "patrick smartpants", "C11": "spongebob thats no lady",
     "C12": "spongebob pet sitter pat", "C02": "pet sitter pat spongebob"}
res = {}
for cid, q in Q.items():
    ids = subprocess.run(["yt-dlp", "--flat-playlist", "--print", "%(url)s", f"bilisearch6:{q}"],
                         capture_output=True, text=True, timeout=90).stdout.split()
    print("==", cid, q, flush=True)
    res[cid] = []
    for u in ids:
        time.sleep(1.5)
        p = subprocess.run(["yt-dlp", "-j", "--no-playlist", u], capture_output=True, text=True, timeout=90)
        if p.returncode:
            print("   fail", u, p.stderr.strip().splitlines()[-1][:120] if p.stderr.strip() else ""); continue
        j = json.loads(p.stdout)
        res[cid].append(dict(url=u, title=j.get("title"), dur=j.get("duration"), h=j.get("height")))
        print(f"   {j.get('duration')}s h={j.get('height')} {u}  {j.get('title','')[:70]}", flush=True)
    time.sleep(2)
json.dump(res, open("work/bili_candidates.json", "w"), indent=1, ensure_ascii=False)
