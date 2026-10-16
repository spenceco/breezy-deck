"""Shared helpers for the background generators (make-*.py).

The backgrounds are 360-degree equirectangular panoramas: x runs once around
you (longitude), y from straight up (top) to straight down (bottom), with the
horizon across the middle. The middle of the image is straight ahead.
Needs Pillow and numpy (e.g. in a venv: pip install pillow numpy).
"""
import numpy as np
from PIL import Image, ImageFilter

W, H = 6144, 3072
PX_PER_DEG = W / 360


def grid():
    """Longitude and latitude (radians) of every pixel centre, as 2-D arrays.
    Longitude 0 is the middle of the image (straight ahead)."""
    lon = (np.arange(W, dtype=np.float32) + 0.5) / W * 2 * np.pi - np.pi
    lat = np.pi / 2 - (np.arange(H, dtype=np.float32) + 0.5) / H * np.pi
    return np.meshgrid(lon, lat)


def deg_x(lon_deg):
    """Image x of a longitude in degrees (0 = straight ahead)."""
    return (lon_deg / 360 + 0.5) * W % W


def deg_y(lat_deg):
    """Image y of a latitude in degrees (0 = horizon, 90 = straight up)."""
    return (90 - lat_deg) / 180 * H


def lerp_colors(t, stops):
    """Colour ramp: t in [0, 1] (array), stops = [(t, (r, g, b)), ...]."""
    ts = [s[0] for s in stops]
    return np.stack([np.interp(t, ts, [s[1][c] for s in stops]) for c in range(3)], axis=-1)


def periodic_noise(n, rng, octaves=7, base=2, falloff=0.55):
    """1-D fractal noise over n samples that wraps around seamlessly: a sum of
    sines with whole-number frequencies. Roughly in [-1, 1]."""
    x = np.arange(n) / n * 2 * np.pi
    out = np.zeros(n)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        for k in range(base ** o, base ** (o + 1)):
            out += amp / (base ** o) * np.sin(k * x + rng.uniform(0, 2 * np.pi))
        total += amp
        amp *= falloff
    return out / (np.abs(out).max() or 1)


def bloom(img, radius=6, strength=0.8):
    """Add a soft glow around bright parts (neon, glyphs)."""
    glow = img.filter(ImageFilter.GaussianBlur(radius))
    a = np.asarray(img, dtype=np.float32) + strength * np.asarray(glow, dtype=np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def save(arr_or_img, path):
    img = arr_or_img if isinstance(arr_or_img, Image.Image) else \
        Image.fromarray(np.clip(arr_or_img, 0, 255).astype(np.uint8))
    img.convert("RGB").save(path, optimize=True)
    print(f"wrote {path} ({img.width}x{img.height})")
