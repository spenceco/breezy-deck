#!/usr/bin/env python3
"""Make vaporwave.png: a retro sunset all around you. A striped sun straight
ahead, purple mountains with neon edges, and a glowing magenta grid floor
running out to the horizon under a pink-to-violet sky.
Needs Pillow and numpy (see pano.py).
  make-vaporwave.py [out.png]"""
import sys

import numpy as np
from PIL import Image

import pano

rng = np.random.default_rng(1985)
W, H, P = pano.W, pano.H, pano.PX_PER_DEG
horizon = H // 2
SUN_LAT, SUN_R = np.radians(9), 13.0         # sun centre and radius (degrees)

lon, lat = pano.grid()
up = np.clip(lat / (np.pi / 2), 0, 1)
img = pano.lerp_colors(up, [(0, (255, 90, 170)), (0.07, (170, 40, 160)), (0.25, (70, 15, 110)),
                            (0.6, (22, 5, 50)), (1, (8, 2, 22))])

# Stars in the upper sky.
n = 1200
sz = rng.uniform(0.35, 1, n)
sy = ((np.pi / 2 - np.arcsin(sz)) / np.pi * H).astype(int)
sx = rng.integers(0, W, n)
img[sy, sx] += (rng.random(n) ** 2 * 170 + 60)[:, None]

# Sun straight ahead: yellow at the top to hot pink, with the classic stripes.
cosd = np.sin(lat) * np.sin(SUN_LAT) + np.cos(lat) * np.cos(SUN_LAT) * np.cos(lon)
d = np.degrees(np.arccos(np.clip(cosd, -1, 1)))
rel = (np.degrees(lat) - np.degrees(SUN_LAT)) / SUN_R      # +1 top .. -1 bottom of the sun
sun = pano.lerp_colors(np.clip((1 - rel) / 2, 0, 1), [(0, (255, 235, 90)), (0.5, (255, 130, 90)), (1, (255, 40, 150))])
stripe_w = np.clip(-rel, 0, 1) * 0.55                       # stripes widen towards the bottom
stripes = ((rel * 7) % 1) > stripe_w
inside = np.clip((SUN_R - d) * 3, 0, 1) * stripes * (lat > 0)
img = img * (1 - inside[..., None]) + sun * inside[..., None]
img += np.array([255, 70, 150]) * (np.exp(-np.maximum(d - SUN_R, 0) / 7) * (d > SUN_R) * 0.35)[..., None]
del cosd, d, rel, sun, stripes, inside

# Mountains with neon outlines, kept clear of the sun.
for height, color, edge in [((1, 9), (60, 10, 90), (0, 220, 255)), ((0.5, 5), (35, 5, 60), (255, 60, 200))]:
    noise = pano.periodic_noise(W, rng, octaves=7, falloff=0.65)
    h = height[0] + (height[1] - height[0]) * (1 - np.abs(noise)) ** 2
    away = np.abs(((np.arange(W) + 0.5) / W - 0.5) * 360)   # degrees from straight ahead
    h *= np.clip((away - SUN_R - 6) / 15, 0, 1)
    top = (horizon - h * P).astype(int)
    rows = np.arange(horizon)[:, None]
    body = rows >= top[None, :]
    img[:horizon][body] = np.array(color, dtype=np.float32)
    rim = (rows >= top[None, :] - 2) & (rows <= top[None, :] + 1) & (h[None, :] > 0.2)
    img[:horizon][rim] = edge

# Grid floor one unit below your eyes: world position of every floor pixel.
below = -lat[horizon:]                                     # angle below the horizon
dist = 1 / np.tan(np.maximum(below, 1e-4))
gx, gz = dist * np.sin(lon[horizon:]), dist * np.cos(lon[horizon:])
pixel = dist / np.sin(np.maximum(below, 1e-4)) * (np.pi / H)   # floor length one pixel covers
lines = np.zeros_like(dist)
for g in (gx, gz):
    off = np.abs(g % 1 - 0.5)          # distance to the nearest line; you stand mid-square
    lines = np.maximum(lines, np.clip(1 - (off - 0.02) / np.maximum(pixel, 1e-6), 0, 1))
lines *= np.clip(1.2 - pixel * 3, 0, 1)                    # fade lines too fine to draw
fog = np.exp(-dist / 18)
floor = np.array([25, 0, 40]) * (1 - fog[..., None]) * 0.6 + np.array([10, 0, 20])
floor += np.array([255, 50, 200]) * (lines * fog)[..., None]
floor += np.array([255, 70, 170]) * np.exp(-below * 25)[..., None] * 0.5   # horizon haze
img[horizon:] = floor
del lon, lat, gx, gz, dist, pixel, lines, fog, floor

pano.save(pano.bloom(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), radius=6, strength=0.6),
          sys.argv[1] if len(sys.argv) > 1 else "vaporwave.png")
