# Torn Honor Frames

A userscript that turns the honor bar on Torn profile pages into an ornate frame around the
profile picture, with the player's name on the frame's nameplate in Torn's own honor lettering.

## Install

Install a userscript manager ([Tampermonkey](https://www.tampermonkey.net/), Violentmonkey,
Greasemonkey, Torn PDA's script manager, Userscripts on Safari), then open
[honor-frames.user.js](https://raw.githubusercontent.com/manuelcecchetto/torn-honor-frames/main/userscript/honor-frames.user.js)
and confirm. Managers that auto-update fetch new versions from the same link.

The script runs only on profile pages with no special permissions (`@grant none`). Every frame's
geometry is built in; it loads only the image of the frame being shown, as a plain `<img>` from
this repository (`raw.githubusercontent.com`), and sends nothing about you or the page anywhere.

## Layout

- `userscript/honor-frames.user.js`: the script.
- `frames/`: 1128 frames, one per honor bar, and `frames.json` with each frame's photo window,
  nameplate box (CSS px in the 232x348 box) and content hash.
- `tools/prompt.txt`, `tools/template-small.png`: the prompt and layout guide used to generate
  each frame from its bar with GPT Image (1024x1536, high, transparent background).
- `tools/process.py research/raw/<id>.png ...`: generated image to frame (finds window and
  nameplate, removes green spill and grey haze). `MANIFEST=` writes the boxes elsewhere for
  parallel runs. `tools/check.py` flags broken frames, `tools/qa_sheet.py` draws contact sheets.
- `tools/build.py`: copies `frames/frames.json` into the script's `FRAMES` line. Run it after any
  frame change and bump `@version`.
- `tools/skip.txt`: bars left out (flags, camo and plain textures), except Taiwan (208), a
  special edition: its frame was generated without characters, then `tools/pooh.py` adds
  E. H. Shepard's 1926 Winnie-the-Pooh drawings (public domain, Wikimedia Commons
  `Winnie-the-Pooh 092.png` and `093.png`); the image API refuses Pooh with that flag. 163 and 1144 were refused by
  the image API's moderation and have no frame.
- `research/` (not committed): source bars, raw generations, Torn's profile CSS/JS.

A changed frame reaches players with the next script version (`tools/build.py`, bump
`@version`); each frame URL carries its content hash, so browsers never mix an old image with new
geometry for long. jsDelivr was dropped: it kept serving `@main`
from hours before, even after a purge.

The frames are derived from Torn's honor bar artwork, which belongs to TORN LTD; the MIT license
covers the code only.
