# longing-media

Reels for the Longing Instagram account (@athenwrites), a narrated motion-comic of the novel *Longing* by Wahib.
Instagram fetches each finished video and cover from this public repo by its raw link.

- `AUTOMATION.md`: the rules and steps the scheduled runs follow.
- `state.json`: posted parts and the next one.
- `parts/part_NN/`: one reel each (script, its new images).
- `pipeline/`: narration (Kokoro, free), word check (Whisper), renderer, cover maker.
- `reels/`: finished videos and covers.

Build one reel: `bash pipeline/setup.sh` once, then `python3 pipeline/make_reel.py parts/part_03`.
