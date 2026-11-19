import subprocess, re, json, sys
jobs = {'src/s1d1.mp4': (6186, 6849), 'src/s3d2.mp4': (4740, 5453), 'src/mmbegins.mp4': (0, 663),
        'src/bttp.mp4': (0, 1036), 'src/s9d1.mp4': (1368, 2022), 'arch/mchale_credits.mp4': (0, 40), 'arch/batman_trailer.mp4': (0, 31)}
out = {}
for src, (a, b) in jobs.items():
    r = subprocess.run(['ffmpeg', '-hide_banner', '-ss', str(a), '-t', str(b - a), '-i', src, '-vf', "scale=320:-1,select='gt(scene,0.28)',showinfo", '-f', 'null', '-'],
                       capture_output=True, text=True)
    cuts = [round(a + float(m), 2) for m in re.findall(r'pts_time:([\d.]+)', r.stderr)]
    out[src] = [a] + cuts + [b]
    print(src, len(cuts), 'cuts')
json.dump(out, open('tr/scenes.json', 'w'))
