# Torn Honor Frames

A userscript that turns the honor bar on Torn profile pages into an ornate frame around the
profile picture, with the player's name on the frame's nameplate in Torn's own honor lettering.

## Install

Install [Tampermonkey](https://www.tampermonkey.net/), then open
[honor-frames.user.js](https://raw.githubusercontent.com/manuelcecchetto/torn-honor-frames/main/userscript/honor-frames.user.js)
and confirm. Tampermonkey updates it from the same link.

The script runs only on profile pages. It downloads `frames/frames.json` and the frame for the
honor being shown straight from this repository (`raw.githubusercontent.com`); it sends nothing
about you or the page anywhere.

## Layout

- `userscript/honor-frames.user.js`: the script.
- `frames/`: 1128 frames, one per honor bar, and `frames.json` with each frame's photo window,
  nameplate box (CSS px in the 232x348 box) and content hash.
- `tools/prompt.txt`, `tools/template-small.png`: the prompt and layout guide used to generate
  each frame from its bar with GPT Image (1024x1536, high, transparent background).
- `tools/process.py research/raw/<id>.png ...`: generated image to frame (finds window and
  nameplate, removes green spill and grey haze). `MANIFEST=` writes the boxes elsewhere for
  parallel runs. `tools/check.py` flags broken frames, `tools/qa_sheet.py` draws contact sheets.
- `tools/skip.txt`: bars left out (flags, camo and plain textures). 163 and 1144 were refused by
  the image API's moderation and have no frame.
- `research/` (not committed): source bars, raw generations, Torn's profile CSS/JS.

A pushed frame reaches players within 5 minutes (GitHub's raw cache); each frame URL carries its
content hash, so browsers never show an old one. jsDelivr was dropped: it kept serving `@main`
from hours before, even after a purge.

The frames are derived from Torn's honor bar artwork, which belongs to TORN LTD; the MIT license
covers the code only.
