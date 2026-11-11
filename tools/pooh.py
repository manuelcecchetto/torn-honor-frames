#!/usr/bin/env -S uv run --with numpy --with pillow --with scipy python3
"""Special edition for honor 208 (Taiwan): pastes E. H. Shepard's 1926 Winnie-the-Pooh drawings
(public domain, Wikimedia Commons "Winnie-the-Pooh 092.png" and "093.png") onto frames/208.webp.

  tools/pooh.py research/pooh-src     (run after tools/process.py research/raw/208.png)

Each drawing is cut out (paper connected to the edge becomes transparent), the paper inside the
outline is filled honey yellow, the ink turns dark brown, and a thin thin gold rim and soft shadow keep
it readable on the enamel. Updates the frame's hash in frames/frames.json.
"""
import hashlib, json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HONEY = np.array([236, 182, 84]); INK = np.array([46, 28, 12]); RIM = np.array([214, 168, 74])


def cutout(path, height, mirror=False):
    g = np.array(Image.open(path).convert('L')).astype(float)
    ink = g < 140
    paper = ~ndimage.binary_dilation(ink, iterations=1)
    lab, _ = ndimage.label(paper)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    outside = np.isin(lab, edge[edge > 0])
    body = ~outside
    body = ndimage.binary_fill_holes(body)
    ys, xs = np.nonzero(body); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    body, gg = body[y0:y1, x0:x1], g[y0:y1, x0:x1]
    t = np.clip((gg - 60) / 140, 0, 1)[..., None]   # 0 ink .. 1 paper
    rgb = INK * (1 - t) + HONEY * t
    a = np.where(body, 255, 0).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), 'RGBA')
    if mirror: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    w = round(im.width * height / im.height)
    im = im.resize((w, height), Image.LANCZOS)
    # thin gold rim and a soft shadow behind
    alpha = im.getchannel('A')
    rim = Image.new('RGBA', im.size, tuple(RIM) + (255,)); rim.putalpha(alpha.filter(ImageFilter.MaxFilter(3)))
    pad = 12
    out = Image.new('RGBA', (w + 2 * pad, height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 150)); sh.putalpha(alpha.filter(ImageFilter.MaxFilter(5)).point(lambda v: v * 0.6))
    shl = Image.new('RGBA', out.size, (0, 0, 0, 0)); shl.alpha_composite(sh, (pad + 3, pad + 4))
    out.alpha_composite(shl.filter(ImageFilter.GaussianBlur(4)))
    out.alpha_composite(rim, (pad, pad)); out.alpha_composite(im, (pad, pad))
    return out, pad


def main(src):
    frame = Image.open('frames/208.webp').convert('RGBA')
    S = frame.width / 232
    # (file, height in CSS px, mirror, centre-x, bottom-y in CSS px)
    for f, h, mirror, cx, by in (('Winnie-the-Pooh_093_png', 92, False, 44, 338),
                                  ('Winnie-the-Pooh_092_png', 70, True, 206, 104)):
        im, pad = cutout(os.path.join(src, f), round(h * S), mirror)
        frame.alpha_composite(im, (round(cx * S - im.width / 2), round(by * S - im.height + pad)))
    frame.save('frames/208.webp', 'WEBP', quality=88, method=6)
    m = json.load(open('frames/frames.json'))
    m['208']['v'] = hashlib.sha1(open('frames/208.webp', 'rb').read()).hexdigest()[:8]
    json.dump(m, open('frames/frames.json', 'w'), separators=(',', ':'))
    print('208', m['208'])


if __name__ == '__main__':
    main(sys.argv[1])
