"""Write the YouTube upload sheet (title, description with real chapter times, tags)."""
import json, sys
marks = json.load(open(sys.argv[1]))
out = sys.argv[2]

CH = [(None, '"No, not really"'), ('VO02', 'Shady Shoals'), ('VO05', '"Who are you?"'), ('VO07', 'The washing machine'),
      ('VO09', 'Overcooked popcorn'), ('VO10', 'Ernie and Tim'), ('VO11', 'PT-73'), ('VO12', '33 years later'),
      ('VO13', 'Sixty-eight'), ('VO16', 'EVIL'), ('VO17', 'Batman and Robin'), ('VO19', 'July 8, 2012'), ('VO21', 'Yesterday')]


def ts(t):
    t = int(t)
    return f'{t // 60}:{t % 60:02d}'


lines = []
for k, name in CH:
    t = 0 if k is None else marks[k]
    lines.append(f'{ts(t)} {name}')

desc = f"""Mermaid Man can't remember how he became Mermaid Man. The show told us anyway. The answer goes back to a 1962 sitcom about a PT boat.

In 2011, SpongeBob finally gave its two retired superheroes real first names: Ernie and Tim. Those happen to be the first names of Ernest Borgnine and Tim Conway, the skipper and the ensign of McHale's Navy, reunited 33 years later as two old men in a retirement home. I went back through the Mermaid Man episodes to see how much of their forgotten past was actually real.

{chr(10).join(lines)}

Episodes referenced:
Mermaid Man and Barnacle Boy (S1, 1999) · Mermaid Man and Barnacle Boy V (S3, 2002) · Back to the Past (S7, 2010) · Mermaid Man Begins (S8, 2011) · Patrick-Man! (S9, 2012)

Sources:
Mermaid Man and Barnacle Boy (casting via Hillenburg and Drymon, the "Evil!" voice crack, Vincent Waller on not recasting): https://en.wikipedia.org/wiki/Mermaid_Man_and_Barnacle_Boy
McHale's Navy (ABC, Oct 11 1962 to Apr 12 1966, 138 episodes): https://en.wikipedia.org/wiki/McHale%27s_Navy
Tim Conway (born Dec 15 1933, died May 14 2019): https://en.wikipedia.org/wiki/Tim_Conway
"I Was Marty," Ernest Borgnine interview, HuffPost (2011): https://www.huffpost.com/entry/i-was-marty-an-interview_us_883667
Back to the Past (Adam West and Burt Ward as the young heroes): https://en.wikipedia.org/wiki/SpongeBob_SquarePants_season_7

Archive: McHale's Navy opening titles; 1963 TV listing ad; Universal "McHale's Navy" pressbook (1964), Wisconsin Center for Film and Theater Research via the Media History Digital Library; Batman (1966) theatrical trailer. All via the Internet Archive.

Barnacle Boy saying he's 68 in an episode that aired when Tim Conway was 68 is my own observation. I can't prove the writers meant it.

Where did you first see these two? And did you know who was doing the voices?

SpongeBob SquarePants and all clips belong to Nickelodeon / Paramount. McHale's Navy belongs to Universal. Batman (1966) belongs to 20th Century Fox. Used here for commentary and criticism under fair use.
"""

tags = ['spongebob', 'mermaid man', 'barnacle boy', 'mermaid man and barnacle boy', 'spongebob mermaid man', 'mermaid man begins',
        'ernest borgnine', 'tim conway', "mchale's navy", 'spongebob lore', 'spongebob theory', 'spongebob explained',
        'spongebob video essay', 'spongebob dark facts', 'back to the past spongebob', 'adam west spongebob', 'burt ward',
        'mermaid man evil', 'shady shoals', 'spongebob forgotten', 'spongebob squarepants']

doc = f"""# YouTube upload sheet

## Title
**Mermaid Man's Forgotten Past Was Real..**

Backup titles for A/B (if CTR is under 5% after 48h):
- SpongeBob Hid Two Real Men Inside Mermaid Man
- Why Mermaid Man Stopped Talking

## Thumbnails (Test & Compare)
- `thumbnail_A_SILENCED.jpg` (lead)
- `thumbnail_B_WHOS_ERNIE.jpg`

## Description
```
{desc}```

## Tags
```
{', '.join(tags)}
```

## Settings
- Category: Film & Animation
- Made for kids: **No** (commentary on a kids' show, aimed at older fans)
- Altered/synthetic content disclosure: narration is AI voice (ElevenLabs). Episode footage, archive footage and photos are real.
"""
open(out, 'w').write(doc)
print(doc[:600])
