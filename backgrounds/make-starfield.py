#!/usr/bin/env python3
"""Make starfield.png: a dark 360-degree (equirectangular) star panorama for
the background behind Breezy's screens. Stars are spread evenly over the
sphere and widened towards the poles, so they look round from every angle.
Python's standard library only.
  make-starfield.py [out.png]"""
import math, random, struct, sys, zlib

W, H = 4096, 2048
STARS = 9000
random.seed(7)  # the same sky every time
img = bytearray(W * H * 3)

def add(x, y, rgb, a):
    if not 0 <= y < H:
        return
    i = (y * W + x % W) * 3
    for c in range(3):
        img[i + c] = min(255, img[i + c] + int(rgb[c] * a))

TINTS = [(255, 255, 255), (200, 215, 255), (255, 235, 200), (255, 210, 180)]
for _ in range(STARS):
    z = random.uniform(-1, 1)            # uniform over the sphere
    lat, lon = math.asin(z), random.uniform(0, 2 * math.pi)
    x, y = lon / (2 * math.pi) * W, (math.pi / 2 - lat) / math.pi * H
    b = random.random() ** 6             # mostly faint, a few bright
    rgb = random.choice(TINTS)
    r = 0.6 + 1.6 * b                    # radius in pixels at the equator
    rx = r / max(math.cos(lat), 0.05)    # wider near the poles
    for dy in range(-int(r) - 1, int(r) + 2):
        for dx in range(-int(rx) - 1, int(rx) + 2):
            d = math.hypot(dx / rx, dy / r)
            if d < 1.5:
                add(int(x) + dx, int(y) + dy, rgb, (0.35 + 0.65 * b) * math.exp(-3 * d * d))

def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
raw = b"".join(b"\0" + bytes(img[y * W * 3:(y + 1) * W * 3]) for y in range(H))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) \
    + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
open(sys.argv[1] if len(sys.argv) > 1 else "starfield.png", "wb").write(png)
