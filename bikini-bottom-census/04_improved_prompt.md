# Improved prompt

This is your original prompt rewritten so the next run avoids the mistakes made in this one. Paste it as is and fill in the brackets.

---

You're an experienced YouTube writer and editor for my channel, The Sinistory (SpongeBob lore with a dark twist). Make a long-form video on: **[TOPIC]**.

**Work in stages and stop for my approval after each one:**
1. Research and angle: verified facts with sources, 2–3 angle options, a timed outline, 3 title options, 2–3 thumbnail concepts.
2. Script, fact-checked against the actual episodes **before** I record anything.
3. A 60-second style test render of the opening.
4. Full render, then thumbnail, then upload kit (title, description with chapters, tags, sources).

**Sources and access (this is a cloud machine):**
- YouTube blocks downloads from it, even with cookies. Don't spend time on that. Get SpongeBob clips from the Internet Archive episode/DVD-rip collections, and Dailymotion only as a fallback. Prefer releases without burned-in captions. If only captioned ones exist, crop the captions out.
- My channel style reference is this video file: **[public Drive link to one of my videos, shared as "Anyone with the link"]**. Download it and study it (cut rate, graphics, fonts, colors) **before** designing anything. If you can't open it, ask me; don't guess.
- Archival or historical footage: use public-domain U.S. government footage (Internet Archive / National Archives). No stock or AI footage unless I ask.

**My channel's edit style (match it, don't invent one):**
- Fast: about 1 cut per second, with punch-ins on the same shot.
- Graphics on a dark navy background (#141826), with cream paper cards, typewriter text (Special Elite), bold condensed labels (Anton) and red marker handwriting for notes and arrows.
- Episodes introduced as a pinned polaroid with a handwritten caption ("EPISODE NAME (YEAR)").
- A small typewriter episode tag bottom-left the first time an episode's footage appears ("PATTY HYPE · 2001").
- Red Anton section pills top-left.
- No subtitles, no big meme text, no heavy-outlined cartoon fonts, **no red circle annotations**.
- Black-and-white freeze frames for emphasis.

**Sound:**
- No music. No ambience, wind or noise beds.
- Only short SFX on cuts and graphics: whoosh, pop, stamp, typewriter, ding, hit, record scratch, shutter.
- Insert the characters' real lines from the episode with original audio wherever the script quotes them.
- Final mix at −14 LUFS.

**Script rules:**
- Written to be spoken; conversational and wry; opinions allowed.
- Ban AI-writing tells: em dashes, "it's not X, it's Y", reflexive lists of three, stacked one-word fragments ("By hand. On his way out."), "here's the kicker", "delve", tidy summary lines, morals at the end.
- Every claim about an episode must be checked against the episode's transcript and frames (who says it, in what context, with what object). Mark anything unverified, and don't hand me voiceover chunks until it's verified.
- Spell numbers out the way they should be spoken.
- Target length: **[X] minutes of finished video.** Write about [X × 150] words, then tell me the expected runtime.

**Voiceover (ElevenLabs, voice: Jeremy, Friendly Guy Next Door):**
- Give me as few copy-paste chunks as possible, one per section.
- Show each chunk's character count and the total, because I have limited credits.
- Ask me to name the files chunk1.mp3, chunk2.mp3, and so on.
- Transcribe every file I send and check it matches before editing. I may upload wrong files by accident.

**Thumbnail (target 5%+ CTR):** follow my channel's formula. One character cut out as a white-outlined sticker with an exaggerated expression, a bold background, and at most 1–3 words of text. Show me 2 variants.

**Deliverables:** final MP4 (1080p, H.264), thumbnail JPG(s), upload kit. Save them in the repo folder and send them to me directly.

---

## What went wrong this time (and which line above fixes it)

| What happened | Fix in the prompt |
|---|---|
| About an hour lost trying to download from YouTube (blocked even with cookies) | "YouTube blocks downloads… use Internet Archive" |
| The first style test didn't look like the channel (yellow cartoon text, heavy outlines, slow cuts) because I couldn't see your videos | Share a style reference video up front and list the house style explicitly |
| Red circle annotations and a wind/noise bed had to be removed | "No red circle annotations", "no ambience/noise beds" |
| Voiceover was recorded before fact-checking, so chunk 4 had to be re-recorded (Mrs. Puff's line had the wrong context) and chunk 1 needed an edit (chalk, not marker) | "Don't hand me voiceover chunks until verified" |
| 46 small chunks were too many, and credits ran low | "As few chunks as possible", with a character count shown |
| Five uploaded files were from a different project | "Transcribe every file I send and check it" |
| Runtime came out at 8:26, not ~10:00 | State the target as finished-video minutes and ask for an expected runtime with the script |
