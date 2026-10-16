#!/usr/bin/env python3
"""Make matrix.png: green "digital rain" all around you, mirrored katakana
and digits falling in columns, fading out towards straight up and down.
Needs Pillow and numpy (see pano.py) and the Noto Sans CJK font.
  make-matrix.py [out.png]"""
import random
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

import pano

FONT = "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"
CELL = 22                 # glyph cell height in pixels (about 1.3 degrees)
COL_W = 18                # column spacing in pixels
MAX_LAT = 58              # rain only within this many degrees of the horizon
random.seed(1999)

chars = [chr(c) for c in range(0xFF66, 0xFF9E)] + list("0123456789Z:.=*+-<>¦")
font = ImageFont.truetype(FONT, CELL - 2)
glyphs = []
for ch in chars:
    g = Image.new("L", (COL_W, CELL))
    ImageDraw.Draw(g).text((COL_W / 2, CELL / 2), ch, fill=255, font=font, anchor="mm")
    glyphs.append(ImageOps.mirror(g))  # the film's glyphs are mirrored

img = Image.new("RGB", (pano.W, pano.H))
top, bottom = int(pano.deg_y(MAX_LAT)), int(pano.deg_y(-MAX_LAT))
rows = (bottom - top) // CELL


def fade(y):  # dim towards the top and bottom of the rain band
    d = abs(y - pano.H / 2) / (pano.H / 2 - top)
    return max(0.0, 1 - d ** 3)


for col in range(pano.W // COL_W):
    x = col * COL_W
    for _ in range(random.randint(1, 3)):          # drops in this column
        head = random.randint(0, rows + 20)
        length = random.randint(6, 34)
        for i in range(length):
            row = head - i
            if not 0 <= row < rows:
                continue
            y = top + row * CELL
            t = i / length                          # 0 at the head, 1 at the tail end
            f = fade(y + CELL / 2)
            if i == 0:
                color = (200, 255, 210)             # bright, almost white head
            else:
                v = (1 - t) ** 1.4
                color = (int(20 * v), int(70 + 185 * v), int(30 + 40 * v))
            color = tuple(int(c * f) for c in color)
            img.paste(color, (x, y), random.choice(glyphs))

pano.save(pano.bloom(img, radius=5, strength=0.9), sys.argv[1] if len(sys.argv) > 1 else "matrix.png")
