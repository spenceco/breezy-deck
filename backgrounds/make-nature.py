#!/usr/bin/env python3
"""Make nature.png: a mountain lake at dusk all around you. Layered ridges
fading into the haze, a pine treeline, a sunset glow on one side and the moon
and first stars on the other, all mirrored in the still lake.
Needs Pillow and numpy (see pano.py).
  make-nature.py [out.png]"""
import sys

import numpy as np

import pano

rng = np.random.default_rng(42)
W, H, P = pano.W, pano.H, pano.PX_PER_DEG
horizon = H // 2
SUNSET_LON = np.radians(-120)   # the glow sits behind-left; the moon opposite
MOON_LON, MOON_LAT = np.radians(35), np.radians(28)

lon, lat = pano.grid()
up = np.clip(lat / (np.pi / 2), 0, 1)
# Angular distance from the sunset direction along the horizon (0..1).
toward_sun = (1 + np.cos(lon - SUNSET_LON)) / 2
sky = pano.lerp_colors(up, [(0, (70, 80, 130)), (0.15, (35, 50, 100)), (0.5, (12, 20, 55)), (1, (4, 7, 22))])
glow = pano.lerp_colors(up, [(0, (255, 140, 70)), (0.08, (200, 90, 90)), (0.3, (60, 40, 90)), (1, (0, 0, 0))])
sky += glow * (toward_sun ** 3)[..., None] * 0.9

# Stars, fewer near the glow and the horizon.
n = 2500
sz = rng.uniform(0.15, 1, n)
s_lat, s_lon = np.arcsin(sz), rng.uniform(-np.pi, np.pi, n)
sx = ((s_lon / (2 * np.pi) + 0.5) * W).astype(int) % W
sy = ((np.pi / 2 - s_lat) / np.pi * H).astype(int)
b = rng.random(n) ** 3 * 200 + 50
b *= 1 - ((1 + np.cos(s_lon - SUNSET_LON)) / 2) ** 2
for dx, dy, f in [(0, 0, 1), (1, 0, 0.35), (0, 1, 0.35), (1, 1, 0.2)]:
    np.add.at(sky, ((sy + dy) % H, (sx + dx) % W), (b * f)[:, None] * np.array([0.9, 0.95, 1.0]))

# Moon with a soft halo.
cosd = np.sin(lat) * np.sin(MOON_LAT) + np.cos(lat) * np.cos(MOON_LAT) * np.cos(lon - MOON_LON)
d = np.degrees(np.arccos(np.clip(cosd, -1, 1)))
sky += np.array([235, 235, 215]) * np.clip((1.6 - d) / 0.15, 0, 1)[..., None]
sky += np.array([90, 100, 130]) * np.exp(-d / 6)[..., None] * 0.5
del cosd, d, glow, lon, lat, up

img = sky
cols = np.arange(W)


def ridge(height_deg, rough, color, haze, octaves=8, trees=False):
    """Fill everything below a wrapping ridgeline (heights in degrees)."""
    periodic = pano.periodic_noise(W, rng, octaves=octaves, falloff=rough)
    h = height_deg[0] + (height_deg[1] - height_deg[0]) * (1 - np.abs(periodic)) ** 1.5
    if trees:  # small pointed pines along the top
        spikes = np.abs(((cols / (0.35 * P)) % 1) - 0.5) * 2
        h = h + (1 - spikes) * rng.uniform(0.3, 0.9, W).round(1) * 0.9
    top = (horizon - h * P).astype(int)
    rows = np.arange(horizon)[:, None]
    mask = rows >= top[None, :]
    # Far ridges blend towards the sky colour just above the horizon (haze).
    c = np.array(color, dtype=np.float32) * (1 - haze) + img[horizon - 1] * haze
    img[:horizon][mask] = c[np.nonzero(mask)[1]]


ridge((3, 17), 0.72, (55, 60, 100), 0.55)
ridge((2, 12), 0.7, (35, 40, 70), 0.35)
ridge((1, 7), 0.65, (18, 22, 40), 0.15)
ridge((0.6, 2.5), 0.45, (8, 12, 18), 0.0, trees=True)

# Still lake: the scene mirrored, slightly darker and bluer, with faint ripples.
refl = img[horizon - 1::-1][:H - horizon].copy()
rows = np.arange(H - horizon)
shift = (np.sin(rows * 0.9) * np.minimum(rows / 300, 1) * 3).astype(int)
for r in range(0, H - horizon):
    if shift[r]:
        refl[r] = np.roll(refl[r], shift[r], axis=0)
depth = (rows / (H - horizon))[:, None, None]
img[horizon:] = refl * np.array([0.55, 0.6, 0.7]) * np.exp(-depth * 2.5) + np.array([3, 5, 10])
pano.save(img, sys.argv[1] if len(sys.argv) > 1 else "nature.png")
