#!/usr/bin/env -S uv run --with numpy --with pillow --with scipy python3
"""Turns generated honor frames (1024x1536) into the frames the userscript shows.

  tools/process.py research/raw/246.png [...]

For each image: finds the portrait window (the transparent or #00FF00 hole around the
centre) and the nameplate (the plain field above it), clears green spill, scales the
canvas to the 232x348 box, and writes frames/<id>.webp plus both boxes (CSS px) and a
content hash into frames/frames.json. The frame may overlap the window's rim: the photo sits
behind it.
"""
import hashlib, json, os, sys
from PIL import Image
import numpy as np
from scipy import ndimage

# Layout in CSS pixels (userscript/honor-frames.user.js uses the same box).
W, H = 232, 348                 # the frame as laid out in the guide
WIN = (16, 55, 216, 330)        # portrait window in the guide: x0, y0, x1, y1
PLATE = (32, 16, 200, 44)       # nameplate, as asked for in the layout guide
OUT_SCALE = 2                    # frames are stored at 2x
OUT_DIR = 'frames'


def keyed(a):
    """Pixels that are hole: transparent, or the #00FF00 key of an opaque generation."""
    r, g, b, al = (a[..., i].astype(int) for i in range(4))
    green = (g > 160) & (g - r > 90) & (g - b > 90)
    return (al < 128) | green


def flood(mask, seed):
    labels, _ = ndimage.label(mask)
    return labels == labels[seed]


def bbox(m):
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def find_window(a):
    hole = keyed(a)
    h, w = hole.shape
    # Seed at the centre of the guide's window, or the nearest hole pixel to it.
    sy, sx = int(h * (WIN[1] + WIN[3]) / 2 / H), int(w * (WIN[0] + WIN[2]) / 2 / W)
    if not hole[sy, sx]:
        ys, xs = np.nonzero(hole)
        k = np.argmin((ys - sy) ** 2 + (xs - sx) ** 2); sy, sx = int(ys[k]), int(xs[k])
    region = flood(hole, (sy, sx))
    # A window open to the canvas edge leaked into the background: shrink to rows/cols mostly inside.
    x0, y0, x1, y1 = bbox(region)
    cols = region.mean(0); rows = region.mean(1)
    inner_c = np.nonzero(cols > 0.5 * cols.max())[0]; inner_r = np.nonzero(rows > 0.5 * rows.max())[0]
    return (int(inner_c.min()), int(inner_r.min()), int(inner_c.max()) + 1, int(inner_r.max()) + 1), region


def _lum(a):
    return (a[..., :3].astype(float) @ [0.299, 0.587, 0.114]) * (a[..., 3] / 255)


def _rims(e, lo, hi):
    """The pair of edge peaks (i < j, lo <= j - i < hi) that are both strong with a calmer span between."""
    e = np.convolve(e, np.ones(3) / 3, 'same')
    n = len(e)
    cs = np.concatenate([[0], np.cumsum(e)])
    i = np.arange(2, max(3, n - lo))[:, None]
    j = i + np.arange(lo, hi)[None, :]
    ok = j < n - 2
    jj = np.where(ok, j, i + lo)
    inner = (cs[jj - 8] - cs[i + 8]) / (jj - i - 16)
    sc = np.where(ok, np.minimum(e[i], e[jj]) - 0.25 * inner, -np.inf)
    if not np.isfinite(sc).any():
        return None
    a, b = np.unravel_index(np.argmax(sc), sc.shape)
    return float(sc[a, b]), int(i[a, 0]) + 1, int(jj[a, b]) + 1


def find_plate(a, win):
    """The nameplate: a rectangular cartouche above the window, found by its rim, the strongest
    horizontal edges spanning the frame's middle and then the strongest vertical edges between them."""
    h, w = a.shape[:2]
    lum = _lum(a)
    band = lum[:win[1] + 10, int(w * .3):int(w * .7)]
    r = _rims(np.abs(band[2:] - band[:-2]).mean(1), 60, 220)
    if not r:
        return None
    y0, y1 = r[1], r[2]
    rows = lum[y0 + 6:y1 - 6]
    ex = np.abs(rows[:, 2:] - rows[:, :-2]).mean(0)
    # Left rim in the left third, right rim in the right third.
    L = int(np.argmax(np.convolve(ex[:w // 3], np.ones(3) / 3, 'same'))) + 1
    R = int(np.argmax(np.convolve(ex[2 * w // 3:], np.ones(3) / 3, 'same'))) + 2 * w // 3 + 1
    return L, y0, R, y1


def unmagenta(a):
    """The guide's magenta plate marker, if the model kept it: repaint it as a dark field."""
    r, g, b = (a[..., i].astype(int) for i in range(3))
    m = (r > 180) & (b > 180) & (g < 110)
    if m.sum() < 500:
        return a
    ys = np.nonzero(m)[0]; y0, y1 = ys.min(), ys.max() + 1
    t = (np.arange(a.shape[0])[:, None] - y0) / max(1, y1 - y0)
    shade = (22 + 14 * (1 - np.clip(t, 0, 1))).repeat(a.shape[1], 1)
    for i, k in enumerate((1.0, 0.92, 0.8)):
        a[..., i] = np.where(m, (shade * k).astype(np.uint8), a[..., i])
    a[..., 3] = np.where(m, 255, a[..., 3])
    return a


def dehaze(a):
    """Grey haze or shadow the model sometimes leaves around the frame (a lighter box on Torn's dark
    page): semi-transparent, unsaturated pixels connected to the canvas edge become transparent.
    Coloured glows (neon) are saturated and stay."""
    rgb = a[..., :3].astype(int)
    sat = rgb.max(-1) - rgb.min(-1)
    haze = (a[..., 3] < 230) & (sat < 40)
    labels, _ = ndimage.label(haze)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    out = a.copy()
    out[np.isin(labels, edge[edge > 0]), 3] = 0
    return out


def despill(a, region):
    """Clear the hole and the green glow the model sometimes leaves on its edge."""
    out = a.copy()
    near = ndimage.maximum_filter(region, size=25)
    r, g, b = (out[..., i].astype(int) for i in range(3))
    spill = near & (g > r + 30) & (g > b + 30)
    out[region, 3] = 0
    # Greenish edge pixels: pull green down to the larger of red/blue and fade them.
    cap = np.maximum(r, b)
    out[..., 1] = np.where(spill, np.minimum(g, cap), out[..., 1]).astype(np.uint8)
    out[..., 3] = np.where(spill, (out[..., 3] * 0.5).astype(np.uint8), out[..., 3])
    return out


def process(path):
    hid = os.path.splitext(os.path.basename(path))[0].split('-')[0]
    im = Image.open(path).convert('RGBA')
    a = unmagenta(np.array(im))
    win, region = find_window(a)
    plate = find_plate(a, win)
    a = dehaze(despill(a, region))
    # The whole canvas becomes the frame box; the photo goes where this frame's window is.
    S = OUT_SCALE
    k = W / a.shape[1]
    out = Image.fromarray(a).resize((W * S, H * S), Image.LANCZOS)
    css = lambda b: [round(v * k) for v in b]
    p = css(plate) if plate else list(PLATE)
    os.makedirs(OUT_DIR, exist_ok=True)
    out.save(f'{OUT_DIR}/{hid}.webp', 'WEBP', quality=88, method=6)
    v = hashlib.sha1(open(f'{OUT_DIR}/{hid}.webp', 'rb').read()).hexdigest()[:8]
    return hid, {'win': css(win), 'plate': p, 'v': v, 'detected': bool(plate)}


if __name__ == '__main__':
    mf = os.environ.get('MANIFEST', f'{OUT_DIR}/frames.json')
    manifest = json.load(open(mf)) if os.path.exists(mf) else {}
    for p in sys.argv[1:]:
        hid, info = process(p)
        manifest[hid] = {'win': info['win'], 'plate': info['plate'], 'v': info['v']}
        print(hid, info)
    json.dump(dict(sorted(manifest.items(), key=lambda kv: int(kv[0]))), open(mf, 'w'), separators=(',', ':'))
