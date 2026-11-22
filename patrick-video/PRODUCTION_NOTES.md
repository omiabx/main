# Production notes

## 1. Thumbnail (target 5%+ CTR)

Your channel's thumbnails share a look: one character with a thick white sticker outline, a dark background, and 1-2 huge words in red/white. This one keeps that so it reads as yours, and adds a curiosity gap the title doesn't answer.

**Main (A): "BRAIN DAMAGE?"**
- Left 60%: Patrick from `T1.png` (SmartPants, top of his head knocked off), cut out, thick white outline, slight tilt.
- Right: **BRAIN** in white over **DAMAGE?** in red, heavy condensed font, black stroke.
- Background: near-black with a faint corkboard texture and one red string running behind him (the "file" brand).
- Why it works: it's readable at phone size in under a second, it's literally true (the head injury in SmartPants, and real starfish having no brain), and "did Patrick have brain damage??" is a question people want answered.

**Test variant (B): the date**
- Patrick's blank face (`T2.png`) with a red marker circle, and a typed evidence label: **OCT 21, 2005**. Small text above: "the day it happened".
- Run A vs B with YouTube's *Test & Compare*. A should win on browse; B is the one that stands out from every other "Patrick got dumber" thumbnail.

What I avoid: before/after split with arrows (the reference video already uses it), a shocked face plus emoji, and more than 3 words.

I build both thumbnails as soon as `T1.png` and `T2.png` arrive. The text treatment and layout are ready in code.

## 2. Title options

1. **When did Patrick Become Stupid??** (yours, keep it; it's a search term)
2. Patrick Was Never Smart. Here's Proof.
3. The Exact Day Patrick Lost His Brain

## 3. Description (paste-ready; matches your existing format)

```
May 1, 1999: in the very first episode of SpongeBob, Patrick Star is the one giving the pep talk. Twelve years later he's reading a pet-sitting list upside down.

So when did it happen? I went back through Jellyfishing, The Secret Box, I'm with Stupid, Valentine's Day, Patrick SmartPants, Pat No Pay and Pet Sitter Pat, read what Stephen Hillenburg, Bill Fagerbakke and Jay Lender said about the character, and ended up in a 2023 Nature paper about starfish anatomy.

[CHAPTERS GO HERE]

Episodes referenced:
Help Wanted (S1, 1999) · Jellyfishing (S1, 1999) · Valentine's Day (S1, 2000) · Big Pink Loser (S2) · The Secret Box (S3, 2001) · Sandy, SpongeBob, and the Worm (S2, 2001) · I'm with Stupid (S2) · Patrick SmartPants (S4, 2005) · That's No Lady (S4) · Pat No Pay (S5, 2007) · Pet Sitter Pat (S7, 2011) · The Patrick Star Show (2021)

Sources:
Patrick Star (Hillenburg's "probably the dumbest guy in town", Fagerbakke's audition and "AquaDauber", Jay Lender on Valentine's Day): https://en.wikipedia.org/wiki/Patrick_Star
The Oral History of SpongeBob SquarePants, Hogan's Alley #17 (2010): https://web.archive.org/web/20150831044034/http://cartoonician.com/the-oral-history-of-spongebob-squarepants/
Paul Tibbitt (showrunner, seasons 4-9): https://en.wikipedia.org/wiki/Paul_Tibbitt
The Patrick Star Show (premiered July 9, 2021): https://en.wikipedia.org/wiki/The_Patrick_Star_Show
Episode transcripts and air dates: https://spongebob.fandom.com
"Study reveals the location of a starfish's head", Stanford (Nov 2023): https://news.stanford.edu/stories/2023/11/study-reveals-location-starfishs-head
"A starfish body is just one giant head, study finds", Smithsonian: https://www.smithsonianmag.com/smart-news/a-starfish-body-is-just-one-giant-head-study-finds-180983192/

October 21, 2005 as the turning point is my own read, not something anyone who worked on the show has said. Same for the Tibbitt connection: he co-wrote The Secret Box too, so I don't think this is one person's fault.

When do YOU think Patrick hit the point of no return?

SpongeBob SquarePants and all clips belong to Nickelodeon / Paramount. Used here for commentary and criticism under fair use.
```

## 4. How the script avoids reading like AI

Built from Wikipedia's *Signs of AI writing* guide plus the usual YouTube-AI-script habits. What I cut or never wrote:

| AI habit | What the script does instead |
|---|---|
| "It's not just X, it's Y" / "not X, but Y" contrasts | Plain statements. The one real contrast (2001 vs 2005) is made with dates and two actual episodes |
| Lists of three for rhythm ("bold, brave, and brilliant") | Lists have 2 or 4+ items, or one item and a pause ("Patrick is into art. And math. And classical music.") |
| "Let's dive in", "buckle up", "here's the thing", "but here's where it gets interesting" | Transitions come from the story ("This is where my theory started falling apart.") |
| Fancy vocab: delve, tapestry, testament, landscape, intricate, pivotal, underscores | Words you'd actually say to a friend |
| "serves as" / "stands as" instead of "is" | "is" |
| A summary at the end of every section | Sections end on a joke, a hook, or a clip |
| Vague "fans have noticed..." claims | Every claim has a date, an episode, or a named person |
| Fake certainty | "That's my read." plus naming the counter-evidence (Tibbitt co-wrote The Secret Box) |
| Same-length sections, list structure | Uneven beats. Some are 6 seconds, one is 40 |
| Em dashes everywhere | None in the voiceover. Commas and ellipses only, which also gives ElevenLabs natural pauses |
| Word-by-word captions on screen the whole time (the AI-channel look) | No full captions. Text on screen only for dates, quotes, and evidence |

Retention structure: three open loops started in the first 90 seconds (the 2011 list, "I wanted a date", the starfish paper), one mid-video ("hold on to that name", paid off 4 minutes later), callbacks instead of recaps (the phone gag, the string, Valentine's Day returning in the science section), and the main reveal saved for the last 90 seconds.

## 5. Edit language

The "file" look your channel description promises, with no AI imagery:

- **Desk + folder system:** manila folder, paper grain, typed labels, rubber stamps (EXHIBIT A-F, PRIME SUSPECT, MY READ), red string on a corkboard that grows across the video. I build all of it in code.
- **Date cards:** every episode opens with a typed stamp `MM.DD.YYYY // TITLE // S#`. This is the main pacing device and it's your channel's signature.
- **Brain monitor:** a small seismograph in the corner that runs the whole video and reacts to the story (steady, flat, flatline, "BRAIN: NOT FOUND"). It's a running gag nobody else has.
- **Clip treatment:** punch-in zooms on the line, freeze-frame + red marker circle for evidence, 2-4 frame shake on impacts. Every clip gets a frame border so it reads as "evidence footage".
- **Pacing rule:** the image changes at least every 3-5 seconds, and nothing sits still under narration longer than 6 seconds.
- **Real-world material:** Wikimedia Commons photos (cast, real starfish), screenshots of the actual source pages (Stanford, Nature, Hogan's Alley archive). Each gets a source tag in the corner.

## 6. Sound (SFX only, no music)

All SFX are synthesized here from scratch, so there's no licensing problem:
whoosh (transitions), paper slide, folder slam, rubber stamp, typewriter keys + carriage bell (date cards), pin push (corkboard), record scratch (freeze-frames), camera shutter (polaroids), heart-monitor beep + flatline, phone ring + hang-up click, receipt printer, low impact boom (reveals), riser (before the verdict).

Mix: voiceover at -14 LUFS integrated, SFX ducked under VO, clip dialogue raised to match VO loudness. Room tone between beats so silence never sounds dead.

## 7. What happens next

1. You generate `VO_01.mp3` ... `VO_32.mp3` from `VO_CHUNKS.txt` and gather the clips/frames in `CLIPS_NEEDED.md`.
2. I time the edit to the real audio lengths, build every graphic, mix the SFX, and render a 1080p30 MP4 (H.264, AAC 320k, YouTube-ready) plus both thumbnails at 1280x720.
3. I fix the chapter timestamps in the description to match the final cut.
