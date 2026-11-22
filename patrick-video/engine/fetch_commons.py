import json,urllib.request,urllib.parse,time,re,os
files={"hillenburg.jpg":"File:Stephen Hillenburg by Carlos Cazurro (cropped).jpg",
"starfish1.jpg":"File:Asterias rubens.jpg",
"starfish2.jpg":"File:Ochre sea star (Pisaster ochraceus) Tofino.jpg",
"starfish3.jpg":"File:Starfishes.jpg"}
UA={'User-Agent':'SinistoryResearch/1.0 (video research)'}
for fn,title in files.items():
    for attempt in range(12):
        if os.path.exists(fn): break
        try:
            q=urllib.parse.urlencode(dict(action='query',titles=title,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1280,format='json'))
            p=list(json.load(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+q,headers=UA)))['query']['pages'].values())[0]['imageinfo'][0]
            md=p['extmetadata']; lic=md.get('LicenseShortName',{}).get('value'); art=re.sub('<.*?>','',md.get('Artist',{}).get('value','')).strip()
            time.sleep(10)
            data=urllib.request.urlopen(urllib.request.Request(p['thumburl'],headers=UA)).read()
            open(fn,'wb').write(data)
            open('CREDITS.txt','a').write(f"{fn}: \"{title[5:]}\" by {art}, {lic}, via Wikimedia Commons ({p['descriptionurl']})\n")
            print('ok',fn,flush=True)
        except Exception as e:
            print(fn,'retry',attempt,e,flush=True); time.sleep(30+30*attempt)
    time.sleep(20)
print('done')
