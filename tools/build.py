#!/usr/bin/env python3
"""Writes frames/frames.json into the userscript's FRAMES line. Run after tools/process.py,
then bump @version so installed scripts update."""
import json, re

p = 'userscript/honor-frames.user.js'
s = open(p).read()
frames = json.dumps(json.load(open('frames/frames.json')), separators=(',', ':'))
s, n = re.subn(r'^  const FRAMES = .*;$', lambda m: f'  const FRAMES = {frames};', s, flags=re.M)
assert n == 1, n
open(p, 'w').write(s)
print(f'{p}: {len(json.loads(frames))} frames, {len(s) // 1024} KB')
