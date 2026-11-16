# Bob's trip: series production kit

Everything here is code, so every episode stays visually consistent: same Bob, same friend, same map, same stage.

```
engine/      voxel renderer (three.js in headless Chromium), scenes, map, SFX synth, mixer
  map.js       THE persistent overworld map (see map/MAP.md)
  models.js    Bob, his friend, lamp board, paint wall, props
  scenes.js    canyon, purple concept stage, map, thumbnails
  ep05.js      Episode 5 shot list, overlays and sound cues (anchored to voice words)
  sfx.py       all sound effects, synthesized (no music, no licensed audio)
  build.sh     one command: voice files in -> finished MP4 out
ep05/        script, ElevenLabs chunk sheet, upload kit, thumbnails
map/         map reference images + rules
```

## Build an episode

```bash
cd engine && npm install          # three.js + pixel font (Chromium/Playwright must be available)
pip install faster-whisper scipy numpy
./build.sh ../ep05/voice ../ep05/build ../ep05/episode05.mp4
```

`ep05/voice/` holds `01.mp3 … 15.mp3` from ElevenLabs. The build:
1. transcribes each file with Whisper and matches the words to `script.json` (word-level timing);
2. lays out the edit; every visual and sound cue is pinned to a spoken word, so it follows the real pacing;
3. renders 1080p30 frames in parallel, mixes voice + SFX + ambience, normalises to −14 LUFS, and writes the MP4.
