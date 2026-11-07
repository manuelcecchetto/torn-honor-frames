#!/usr/bin/env -S uv run --with pillow python3
"""QA contact sheets: every frame with a stand-in photo, its window (cyan) and nameplate (yellow).

  tools/qa_sheet.py photo.png out-prefix [ids...]   (default: every frame in frames.json)
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

m = json.load(open('frames/frames.json'))
photo = Image.open(sys.argv[1]).convert('RGBA')
prefix = sys.argv[2]
ids = sys.argv[3:] or list(m)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 14)
W, H, cols, rows = 232, 348, 10, 6
for s in range(0, len(ids), cols * rows):
    chunk = ids[s:s + cols * rows]
    sheet = Image.new('RGBA', (cols * (W + 6), rows * (H + 6)), (51, 51, 51, 255))
    d = ImageDraw.Draw(sheet)
    for k, i in enumerate(chunk):
        x, y = (k % cols) * (W + 6), (k // cols) * (H + 6)
        f = m[i]
        x0, y0, x1, y1 = f['win']; x0 -= 4; y0 -= 4; x1 += 4; y1 += 4
        r = max((x1 - x0) / photo.width, (y1 - y0) / photo.height)
        ph = photo.resize((round(photo.width * r), round(photo.height * r)))
        ph = ph.crop(((ph.width - (x1 - x0)) // 2, (ph.height - (y1 - y0)) // 2, (ph.width - (x1 - x0)) // 2 + x1 - x0, (ph.height - (y1 - y0)) // 2 + y1 - y0))
        sheet.alpha_composite(ph, (x + x0, y + y0))
        sheet.alpha_composite(Image.open(f'frames/{i}.webp').resize((W, H)), (x, y))
        p = f['plate']; cy = (p[1] + p[3]) / 2
        d.rectangle([x + p[0], y + p[1], x + p[2], y + p[3]], outline=(255, 255, 0, 255))
        d.text((x + (p[0] + p[2]) / 2, y + cy), 'MANUEL', font=font, fill=(255, 255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0, 255))
        d.text((x + 4, y + H - 18), i, font=font, fill=(0, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
    out = f'{prefix}{s // (cols * rows):02d}.jpg'
    sheet.convert('RGB').resize((sheet.width * 3 // 5, sheet.height * 3 // 5), Image.LANCZOS).save(out, quality=82); print(out, chunk[0], chunk[-1])
