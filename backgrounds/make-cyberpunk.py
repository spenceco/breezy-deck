#!/usr/bin/env python3
"""Make cyberpunk.png: a neon city at night all around you. Layers of
buildings with lit windows and neon strips under a magenta-glow sky, mirrored
in a wet street below the horizon.
Needs Pillow and numpy (see pano.py).
  make-cyberpunk.py [out.png]"""
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import pano

random.seed(2077)
W, H, P = pano.W, pano.H, pano.PX_PER_DEG
horizon = H // 2
NEON = [(255, 40, 190), (0, 230, 255), (180, 60, 255), (255, 200, 60), (60, 255, 170)]
WINDOWS = [(0, 210, 255), (255, 60, 190), (255, 190, 100), (200, 220, 255)]

# Sky: dark at the top, a magenta and violet glow from the city at the horizon.
lon, lat = pano.grid()
up = np.clip(lat / (np.pi / 2), 0, 1)
sky = pano.lerp_colors(up, [(0, (150, 30, 120)), (0.06, (80, 20, 90)), (0.25, (25, 8, 45)), (1, (4, 2, 12))])
del lon, lat
img = Image.fromarray(sky.astype(np.uint8))
draw = ImageDraw.Draw(img)


def building_row(height_deg, width_deg, color, window_chance, neon_chance):
    x = random.uniform(0, 5) * P
    while x < W:
        w = random.uniform(*width_deg) * P
        h = random.uniform(*height_deg) * P
        x0, x1, y0 = x, x + w, horizon - h
        # Draw at x and x - W so buildings cross the image's left/right edge seamlessly.
        for shift in (0, -W):
            draw.rectangle([x0 + shift, y0, x1 + shift, horizon], fill=color)
        if window_chance:
            win, gap = max(2, w / 14), max(3, w / 9)
            yy = y0 + gap
            while yy < horizon - gap:
                xx = x0 + gap / 2
                while xx < x1 - win:
                    if random.random() < window_chance:
                        c = random.choice(WINDOWS)
                        f = random.uniform(0.35, 1)
                        for shift in (0, -W):
                            draw.rectangle([xx + shift, yy, xx + win + shift, yy + win * 1.3],
                                           fill=tuple(int(v * f) for v in c))
                    xx += gap
                yy += gap * 1.4
        if random.random() < neon_chance:
            c = random.choice(NEON)
            for shift in (0, -W):
                draw.line([x0 + shift, y0, x1 + shift, y0], fill=c, width=3)  # roof edge
                if random.random() < 0.5:                                    # vertical sign
                    sx = x0 + shift + random.uniform(0.2, 0.8) * w
                    draw.rectangle([sx, y0 + h * 0.15, sx + max(4, w * 0.08), y0 + h * 0.55], fill=c)
        x += w + random.uniform(0, 0.6) * P


building_row((1, 6), (1, 3), (60, 25, 85), 0.10, 0.05)    # far, hazy
building_row((3, 14), (2, 5), (30, 14, 48), 0.22, 0.15)   # middle
building_row((8, 30), (3, 8), (12, 7, 22), 0.30, 0.35)    # near, tall
img = pano.bloom(img, radius=7, strength=1.0)

# Wet street: the city mirrored below the horizon, smeared downwards and darker.
a = np.asarray(img, dtype=np.float32)
refl = a[horizon - 1::-1][:H - horizon].copy()
refl_img = Image.fromarray(refl.astype(np.uint8)).filter(ImageFilter.BoxBlur(2))
refl_img = refl_img.resize((W, (H - horizon) // 8)).resize((W, H - horizon), Image.BILINEAR)
refl = np.asarray(refl_img, dtype=np.float32)
depth = np.linspace(0, 1, H - horizon, dtype=np.float32)[:, None, None]
street = refl * 0.45 * np.exp(-depth * 5) + np.array([10, 5, 16]) * (1 - depth)
a[horizon:] = street
pano.save(a, sys.argv[1] if len(sys.argv) > 1 else "cyberpunk.png")
