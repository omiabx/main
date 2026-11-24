# Script style rules: what this script will NOT do

Each rule below is a pattern that makes a script read as machine-written. The script gets checked against every line of this list before you see it.

## Punctuation and shape
1. **No em dashes (—).** This is the single most recognised AI tell. Use full stops, commas, or "..." for spoken pauses.
2. **No automatic lists of three.** "Fast, cheap, and reliable." If there are two things, say two. If there are five, say five.
3. **No "It's not X, it's Y" / "This isn't just X. It's Y."** framing.
4. **No colon reveals** ("The answer? Simple: ..."), no rhetorical-question-then-answer every paragraph.
5. **Paragraph lengths vary.** Some lines are three words. Some ramble. AI keeps every paragraph the same size.

## Words and phrases that are banned
delve, tapestry, testament, realm, landscape, intricate, pivotal, underscore, vibrant, navigate, journey, unpack, dive deep / deep dive, "buckle up", "let's dive in", "in today's video", "without further ado", "but here's the thing", "here's the kicker", "and that's where things get interesting", "the answer might surprise you", "little did they know", "at the end of the day", "it's worth noting", "interestingly", "fascinating", "a stark reminder", "serves as a reminder", "in a world where", "one thing is clear", "quietly", "whispers of", "ever-evolving", "game-changer", "rabbit hole", "mind-blowing", "spoiler alert".

## Structure
6. **No summary line closing each section** ("So, as we can see, the sign can't be trusted."). The next section just starts.
7. **No moral at the end.** No "maybe the real population was the friends we made". The ending hits and stops.
8. **No hedging stacks** ("it could perhaps be argued that..."). Commit to claims. Where the show is unclear, say so once, plainly.
9. **No fake balance.** We pick a number at the end and defend it.
10. **No over-explaining jokes.** If a clip is funny, the clip does the work; narration shuts up.

## Written TO BE SPOKEN
11. Contractions always (it's, they're, that's, won't).
12. Sentences that run on a little, the way people talk. Occasional "like", "okay", "anyway" where a person would say them, not sprinkled for flavour.
13. Numbers written the way the voice should say them ("forty-six thousand, eight hundred and fifty-three"), so ElevenLabs doesn't read "46,853" weirdly.
14. Clip cues are in [BRACKETS] and are never in the voiceover chunks.
15. Pauses are done with line breaks between chunks, not with SSML tags or "(pause)".
16. The narrator has opinions, gets things wrong on purpose and corrects themselves, talks to the show and its characters, and sometimes to the editor.

## Facts
17. Every claim about an episode gets checked against the episode itself (transcribed audio + frames) before it goes in. If I couldn't verify it, it's cut or flagged.
