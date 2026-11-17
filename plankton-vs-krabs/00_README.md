# Plankton vs. Mr. Krabs: "He Was in the Room"

Long-form video (about 11–12 min). No music: voiceover, SFX and edits only.

## The angle (why this one stands out)
Most videos on this topic are either a scheme compilation or "Mr. Krabs is the real villain." This one has a single argument, and the structure is lifted from the show itself:

1. **Cold open.** 27 years of the same guy getting thrown out of the same door.
2. **The reframe.** This rivalry is a breakup.
3. **Rashomon.** *Friend or Foe* (2007) tells the origin three times (Krabs's version, Plankton's version, Karen's). We play it as three unreliable narrators, then reveal that the Krabby Patty was invented by **both of them, by accident, during the fight that ended the friendship.** Title drop: *"he was in the room."*
4. **The losing streak.** A running scoreboard; the one win (Plan Z, 2004) gets revoked.
5. **The case against Krabs.** Chum on the menu to steal Plankton's one (paid) customer, *One Coarse Meal*, 62 cents.
6. **Neither wants it to end.** In *Plankton Retires* (written by Mr. Lawrence) **both** of them send robot decoys to keep spying on each other.
7. **Verdict + callback.** The first penny Krabs ever found went on a balloon for Plankton. *Every penny after that, he kept.* Button: "he did go to college."

Open loops that carry retention: *"except one time"* (paid off in ch.3), *"remember the balloon"* (paid off in the last 20 s), *"I'll tell you which one at the end"* (the verdict).

## Titles (pair with the thumbnail)
| Title | Why |
|---|---|
| **Plankton Helped Invent the Krabby Patty** ← recommended | Sounds false, is true (per *Friend or Foe*). Strong curiosity gap. |
| Mr. Krabs Could End This Rivalry Whenever He Wants | Opinion title, invites comments. |
| SpongeBob's Longest Rivalry Is Actually a Breakup | Softer, but "breakup" is an unexpected word for this topic. |

## Thumbnail
`output/thumbnail.png`: big guilty Mr. Krabs on the left, a torn **SECRET** recipe half in the middle, tiny angry Plankton inside a magnifying glass on the right (a nod to Hillenburg's original "too small to see" design), and **"HALF WAS HIS."** in yellow. Three words, readable at phone size (`output/thumbnail_mobile_check.png`). Red/green split = Krabs/Plankton color coding used throughout the video.
It's a layout until you add the two frames (`thumb/krabs.png`, `thumb/plankton.png`); then run `python3 tools/thumbnail.py`.

## The AI-script patterns this script avoids
Researched from writing-detection guides and creator write-ups (sources in chat). None of these appear in the script:
- "It's not X, it's Y" / "This isn't just X" contrast framing (the #1 tell). One slipped into a draft and I cut it.
- Em dashes everywhere. There are zero, which also keeps ElevenLabs from inserting odd pauses.
- Reflexive rule-of-three lists and stacked adjectives ("bold, brilliant, and iconic").
- Signposting: "let's dive in", "buckle up", "in this video we'll explore", "without further ado".
- Fake-suspense pivots: "but here's the thing", "here's the kicker", "plot twist", "little did he know", "and that's when everything changed".
- Self-answered question chains and "The reason? Money." colon reveals.
- Stock vocabulary: delve, tapestry, testament, journey, landscape, iconic, masterclass, crucial, resonate.
- Even, symmetrical paragraphs that all end on a zinger.
- "At the end of the day / ultimately / so next time you watch…" moral wrap-ups.
- Both-sides neutrality. The script takes a side and names a villain.
- Vague claims ("many fans believe"). Every factual claim names an episode.

What it does instead: specific scene details (the penny, Old Man Jenkins, "Plabs"), a narrator with opinions who admits a contradiction and ignores it on purpose, uneven sentence lengths, spoken asides ("which, fair"), callbacks, and jokes timed for a cut.

## Workflow
1. Generate the VO from `01_VOICEOVER_CHUNKS.md` → `vo/01.mp3 … vo/17.mp3`.
2. Supply clips per `03_CLIP_LIST.md` → `clips/`.
3. Supply two thumbnail frames → `thumb/`.
4. Render: `python3 tools/render.py` → `output/plankton_vs_krabs_FINAL.mp4` (1080p30, H.264, AAC, -14 LUFS).

| Path | What |
|---|---|
| `01_VOICEOVER_CHUNKS.md` | Script as copy-paste ElevenLabs chunks + settings |
| `02_EDIT_PLAN.md` | Every shot, anchor word, effect and SFX cue (218 shots) |
| `03_CLIP_LIST.md` | 45 show moments needed, with episode names |
| `tools/timeline.py` | The edit itself (change a shot here, re-render) |
| `tools/render.py` | Whisper word-alignment → frame renderer → SFX mix → MP4 |
| `tools/gfx.py` | Original motion graphics (no show characters are drawn) |
| `tools/sfx.py` | Synthesizes all 30 SFX from scratch (no licensing issues) |
| `tools/thumbnail.py` | Thumbnail compositor |
