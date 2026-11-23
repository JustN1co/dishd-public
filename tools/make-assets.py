"""Derive web-ready logo, favicon and OG assets from media/light-logo.jpg."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SRC = Path("media/light-logo.jpg")
OUT = Path("media")

img = Image.open(SRC).convert("RGB")
arr = np.asarray(img).astype(np.float32)

# Background = most common (corner) colour.
cream = arr[0:40, 0:40].reshape(-1, 3).mean(axis=0)
print("cream:", cream.round().tolist())

dist = np.sqrt(((arr - cream) ** 2).sum(axis=2))
mask = dist > 24

ys, xs = np.nonzero(mask)
top, bottom, left, right = ys.min(), ys.max(), xs.min(), xs.max()
print("bbox:", left, top, right, bottom)

# Glyph colours actually used (orange body + red dot).
core = arr[dist > 200]
# two-cluster split: the red dot is much darker in the green channel
orange = core[core[:, 1] > 130].mean(axis=0)
red = core[core[:, 1] <= 130].mean(axis=0)
print("orange:", orange.round().tolist(), "red:", red.round().tolist())

# Un-mix every pixel between cream and the nearest glyph colour.
h, w, _ = arr.shape
best_a = np.zeros((h, w), dtype=np.float32)
best_c = np.zeros((h, w, 3), dtype=np.float32)
for colour in (orange, red):
    direction = colour - cream
    denom = float((direction ** 2).sum())
    a = ((arr - cream) * direction).sum(axis=2) / denom
    a = np.clip(a, 0.0, 1.0)
    fitted = cream + a[..., None] * direction
    err = np.sqrt(((arr - fitted) ** 2).sum(axis=2))
    better = err < 40
    take = (a > best_a) & better
    best_a[take] = a[take]
    best_c[take] = colour

alpha = (np.clip(best_a * 1.15, 0, 1) * 255).astype(np.uint8)
rgb = np.where(best_a[..., None] > 0.002, best_c, arr).astype(np.uint8)
rgba = np.dstack([rgb, alpha])
logo_full = Image.fromarray(rgba, "RGBA").crop((left, top, right + 1, bottom + 1))

# Square canvas with breathing room, transparent.
pad_ratio = 0.06
cw, ch = logo_full.size
side = int(max(cw, ch) * (1 + pad_ratio * 2))
square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
square.paste(logo_full, ((side - cw) // 2, (side - ch) // 2), logo_full)
square.resize((640, 640), Image.LANCZOS).save(OUT / "logo.png", optimize=True)
square.resize((160, 160), Image.LANCZOS).save(OUT / "logo-160.png", optimize=True)


def icon(size: int, radius_ratio: float = 0.22) -> Image.Image:
    """Opaque app-icon style tile: cream background, rounded corners."""
    scale = 4
    s = size * scale
    tile = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    draw.rounded_rectangle(
        (0, 0, s - 1, s - 1),
        radius=int(s * radius_ratio),
        fill=tuple(int(v) for v in cream) + (255,),
    )
    inner = int(s * 0.80)
    mark = square.resize((inner, inner), Image.LANCZOS)
    tile.paste(mark, ((s - inner) // 2, (s - inner) // 2), mark)
    return tile.resize((size, size), Image.LANCZOS)


icon(32).save(OUT / "favicon-32.png", optimize=True)
icon(192).save(OUT / "favicon-192.png", optimize=True)
icon(180, 0.0).save(OUT / "apple-touch-icon.png", optimize=True)
sizes = [(16, 16), (32, 32), (48, 48)]
icon(256).save(OUT / "favicon.ico", format="ICO", sizes=sizes)

# Social sharing cover (1200x630).
og = Image.new("RGB", (1200, 630), tuple(int(v) for v in cream))
mark = square.resize((360, 360), Image.LANCZOS)
og.paste(mark, ((1200 - 360) // 2, (630 - 360) // 2 - 12), mark)
og.save(OUT / "og-cover.png", optimize=True)

for f in sorted(OUT.iterdir()):
    print(f.name, f"{f.stat().st_size / 1024:.1f} kB")
