#!/usr/bin/env -S uv run --with numpy --with pillow python3
"""Flags frames that cannot work: an opaque photo window, an opaque (non-transparent) background,
or a window of implausible size. Prints one line per flagged frame."""
import json
import numpy as np
from PIL import Image

m = json.load(open('frames/frames.json'))
for i, f in m.items():
    a = np.array(Image.open(f'frames/{i}.webp').convert('RGBA')).astype(float) / 255
    S = a.shape[1] / 232
    x0, y0, x1, y1 = (round(v * S) for v in f['win'])
    w, h = x1 - x0, y1 - y0
    inner = a[y0 + h // 5:y1 - h // 5, x0 + w // 5:x1 - w // 5, 3].mean()
    c = 10 * round(S)
    corners = np.mean([a[:c, :c, 3].mean(), a[:c, -c:, 3].mean(), a[-c:, :c, 3].mean(), a[-c:, -c:, 3].mean()])
    why = []
    if inner > 0.05: why.append(f'window {inner:.2f} opaque')
    if corners > 0.9: why.append(f'corners {corners:.2f} opaque')
    if (x1 - x0) / S < 150 or (y1 - y0) / S < 200: why.append(f'window {f["win"]}')
    if why: print(i, '; '.join(why))
