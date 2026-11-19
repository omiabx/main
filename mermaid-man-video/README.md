# Mermaid Man's Forgotten Past Was Real..

Long-form video for The Sinistory. Character: **Mermaid Man & Barnacle Boy**.

| File | What it is |
|---|---|
| `SCRIPT.md` | Full spoken script with clip placements, character-selection notes and sources |
| `VO_CHUNKS.md` | 4 copy-paste blocks for ElevenLabs → `PART_1.mp3` … `PART_4.mp3` |
| `thumbnail_A_SILENCED.jpg` | Lead thumbnail (1280×720) |
| `thumbnail_B_WHOS_ERNIE.jpg` | A/B variant |
| `YOUTUBE.md` | Title, description with chapter times, tags, settings (written after the final render) |
| `pipeline/` | The edit: alignment, edit decision list, renderer, SFX synth, thumbnail builder |

## How the edit is built

- **Voice → timing.** The ElevenLabs parts are transcribed with Whisper and aligned to the script word by word. Every cut, text pop, sticker and SFX in `pipeline/edl.py` is anchored to a spoken phrase, so the edit follows the narrator's real pacing.
- **Clips.** Real episode footage (DVD rips). Clip audio is run through Demucs and only the dialogue stem is kept, so **no music** from the episodes ends up in the video.
- **SFX.** All synthesised (`pipeline/sfx.py`): whooshes, impacts, typewriter, projector, static, record scratch, etc. No music anywhere.
- **Archive.** McHale's Navy titles, a 1963 TV-listing ad, a 1964 Universal pressbook photo (Joe Flynn, Ernest Borgnine, Tim Conway), the 1966 Batman trailer.
- **Mix.** Narration at −16 LUFS, clips at about −17.5, SFX about 10 dB under. Master loudness-normalised to −14 LUFS / −1.5 dBTP (YouTube's target).

## Rebuild

```
python3 pipeline/render.py <folder with PART_1..4 audio> out/final.mp4
python3 pipeline/meta.py out/work_final/marks.json YOUTUBE.md
```
