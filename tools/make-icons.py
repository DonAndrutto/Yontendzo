#!/usr/bin/env python3
"""Derive the Yontendzo icon set from the master artwork (IMG_8733.jpeg).

The master is a rounded "app tile" floating on a white page with a drop
shadow. Platforms apply their own mask (iOS squircle, Android adaptive
circle/squircle, browser tab square), so baking in corners and white
margins makes the installed icon look like a small sticker inside a badge.
Everything here therefore starts by cropping to the tile and painting the
rounded corners back out to a full-bleed square.

Three families come out of that master:

  * full-bleed  — the whole composition (tree, wheel, both wordmarks) for
                  the home screen / apple-touch / PWA "any" icons, where
                  the icon is drawn at 120-192px and the wordmark reads.
  * maskable    — emblem only, centred inside Android's 80% safe circle on
                  an extrapolated gradient, since a circular mask would
                  otherwise slice through the YONTENDZO wordmark.
  * favicon     — tight crop on the tree-and-wheel emblem, because at 16px
                  the wordmarks collapse into noise and only the emblem
                  silhouette survives.

Run from the repository root:  python3 tools/make-icons.py
"""

import os

import numpy as np
from PIL import Image, ImageFilter

SRC = "IMG_8733.jpeg"
OUT_DIR = "icons"

# A pixel this much brighter than the modelled background counts as artwork
# (gold strokes and their glow) when the emblem is lifted off its backdrop.
GLOW_RANGE = 55.0


def find_tile(arr):
    """Return the (left, top, side) square covering the artwork tile only.

    The threshold sits below the drop shadow's brightness so the shadow is
    read as page, not tile. Edges are taken as the median over the middle
    half of the rows/columns, which ignores the rounded corners.
    """
    dark = arr.mean(axis=2) < 150
    h, w = dark.shape

    def edges(lines):
        firsts, lasts = [], []
        for line in lines:
            idx = np.where(line)[0]
            if len(idx):
                firsts.append(idx[0])
                lasts.append(idx[-1])
        return int(np.median(firsts)), int(np.median(lasts))

    x0, x1 = edges(dark[h // 4:3 * h // 4])
    y0, y1 = edges(dark[:, w // 4:3 * w // 4].T)
    side = min(x1 - x0 + 1, y1 - y0 + 1)
    return x0 + (x1 - x0 + 1 - side) // 2, y0 + (y1 - y0 + 1 - side) // 2, side


def dilate(mask, steps):
    """Grow a boolean mask by `steps` pixels in the four cardinal directions."""
    for _ in range(steps):
        grown = mask.copy()
        grown[1:, :] |= mask[:-1, :]
        grown[:-1, :] |= mask[1:, :]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        mask = grown
    return mask


def outside_mask(arr):
    """Mask of the light pixels outside the tile's rounded corners."""
    h, w, _ = arr.shape
    light = arr.mean(axis=2) > 150
    mask = np.zeros((h, w), dtype=bool)
    for sy, sx in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if not light[sy, sx]:
            continue
        stack = [(sy, sx)]
        mask[sy, sx] = True
        while stack:
            y, x = stack.pop()
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and light[ny, nx] and not mask[ny, nx]:
                    mask[ny, nx] = True
                    stack.append((ny, nx))
    # Grow by a few pixels to swallow the anti-aliased rim of the corner.
    return dilate(mask, 3)


def background_model(arr, mask):
    """Per-row background colour for the left and right edges of the tile.

    The tile's gradient runs top-to-bottom but also shifts slightly across
    the width, so each side is sampled separately and the fill interpolates
    between them. Rows whose sample band falls inside a corner have too few
    valid pixels; those are extrapolated from the nearest solid rows.
    """
    h, w, _ = arr.shape
    band = max(8, w // 20)
    sides = []
    for lo, hi in ((10, 10 + band), (w - 10 - band, w - 10)):
        colours = np.zeros((h, 3))
        valid = np.zeros(h, dtype=bool)
        for y in range(h):
            keep = ~mask[y, lo:hi]
            if keep.sum() >= band // 3:
                colours[y] = np.median(arr[y, lo:hi][keep], axis=0)
                valid[y] = True
        idx = np.where(valid)[0]
        # Straight-line extrapolation off each end of the solid range keeps
        # the gradient continuous where it meets real pixels.
        for target, ref in ((np.arange(0, idx[0]), idx[:120]),
                            (np.arange(idx[-1] + 1, h), idx[-120:])):
            if not len(target):
                continue
            for ch in range(3):
                slope, intercept = np.polyfit(ref, colours[ref, ch], 1)
                colours[target, ch] = slope * target + intercept
        sides.append(np.clip(colours, 0, 255))
    return sides


def build_master(path):
    """Full-bleed square version of the artwork: no margin, no rounded corners."""
    arr = np.asarray(Image.open(path).convert("RGB")).astype(float)
    left, top, side = find_tile(arr)
    tile = arr[top:top + side, left:left + side].copy()

    mask = outside_mask(tile)
    left_bg, right_bg = background_model(tile, mask)
    t = (np.arange(side) / (side - 1))[None, :, None]
    fill = left_bg[:, None, :] * (1 - t) + right_bg[:, None, :] * t
    tile[mask] = fill[mask]

    # The tile is drawn as a lit card, so a pale bevel highlight traces its
    # rounded border. Left in, it survives as an arc floating inside whatever
    # mask the platform applies. Fade it back into the gradient wherever a
    # ring hugging the old border is brighter than the background and not
    # gold (which keeps the wordmark, close to the bottom edge, untouched).
    border = mask.copy()
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    ring = dilate(border, max(4, int(round(side * 0.022)))) & ~mask
    lift = tile.mean(axis=2) - fill.mean(axis=2)
    gold = (tile[:, :, 0] - tile[:, :, 2]) > 45
    strength = np.clip((lift - 8) / 12, 0, 1) * (ring & ~gold)
    tile += (fill - tile) * strength[:, :, None]
    return tile, fill


def emblem_box(tile):
    """Bounding box of the tree-and-wheel emblem, excluding both wordmarks."""
    r, g, b = tile[:, :, 0], tile[:, :, 1], tile[:, :, 2]
    gold = (r > 120) & (g > 90) & (r > b + 40)
    rows = np.where(gold.sum(axis=1) > 0)[0]
    # The emblem is the first gold block; a clear gap separates it from the
    # Tibetan line and the Latin wordmark below.
    end = rows[0]
    for y in rows[1:]:
        if y - end > 5:
            break
        end = y
    cols = np.where(gold[rows[0]:end + 1].sum(axis=0) > 0)[0]
    return cols[0], rows[0], cols[-1], end


def resize(arr, size):
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    return img.resize((size, size), Image.LANCZOS)


def crisp(img):
    """Restore the contrast a 1387px master loses on the way down.

    The smaller the target, the more the fine gold filigree greys out, so
    the sharpening scales with how far the image has been reduced. Without
    it a 16px favicon is an indistinct blob.
    """
    size = img.size[0]
    radius, percent = (1.0, 120) if size <= 48 else \
                      (1.0, 90) if size <= 96 else \
                      (0.8, 60) if size <= 256 else (0.8, 35)
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent,
                                              threshold=0))


def save(img, name):
    """Write a sharpened palette PNG.

    The artwork is a dark gradient behind flat gold, so 256 dithered colours
    are visually indistinguishable from truecolour at any size these icons
    are drawn at — and about a fifth of the bytes.
    """
    path = os.path.join(OUT_DIR, name)
    quantized = crisp(img).quantize(colors=256, method=Image.FASTOCTREE,
                                    dither=Image.FLOYDSTEINBERG)
    quantized.save(path, optimize=True)
    print(f"  {path:38s} {img.size[0]:>4}px  {os.path.getsize(path) / 1024:6.1f} KB")


def make_maskable(tile, fill, size):
    """Emblem centred on the extrapolated gradient, inside the safe circle.

    Android masks maskable icons down to a circle 80% of the icon's width.
    The emblem is lifted off its own backdrop with a soft alpha so its glow
    survives the move, then composited onto a wordmark-free gradient.
    """
    x0, y0, x1, y1 = emblem_box(tile)
    pad = int(0.02 * tile.shape[0])
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(tile.shape[1] - 1, x1 + pad), min(tile.shape[0] - 1, y1 + pad)

    crop = tile[y0:y1 + 1, x0:x1 + 1]
    base = fill[y0:y1 + 1, x0:x1 + 1]
    lift = crop.mean(axis=2) - base.mean(axis=2)
    alpha = np.clip(lift / GLOW_RANGE, 0, 1)
    emblem = Image.fromarray(
        np.dstack([np.clip(crop, 0, 255), alpha * 255]).astype(np.uint8), "RGBA")

    canvas = resize(fill, size).convert("RGBA")
    # 62% of the width keeps every stroke well inside the 80% safe circle.
    eh = int(round(size * 0.62))
    ew = max(1, int(round(eh * emblem.width / emblem.height)))
    emblem = emblem.resize((ew, eh), Image.LANCZOS)
    canvas.alpha_composite(emblem, ((size - ew) // 2, (size - eh) // 2))
    return canvas.convert("RGB")


def make_favicon_source(tile):
    """Square crop on the emblem — the only part that still reads at 16px."""
    x0, y0, x1, y1 = emblem_box(tile)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = max(x1 - x0, y1 - y0) * 1.10
    half = side / 2
    # Keep the crop inside the tile without letting it drift off the emblem.
    cx = min(max(cx, half), tile.shape[1] - half)
    cy = min(max(cy, half), tile.shape[0] - half)
    left, top = int(round(cx - half)), int(round(cy - half))
    side = int(round(side))
    return tile[top:top + side, left:left + side]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tile, fill = build_master(SRC)
    print(f"master tile: {tile.shape[1]}x{tile.shape[0]}")

    print("full-bleed (home screen, PWA, apple-touch):")
    for name, size in (("apple-touch-icon.png", 180),
                       ("icon-192.png", 192),
                       ("icon-512.png", 512)):
        save(resize(tile, size), name)

    print("maskable (Android adaptive):")
    for size in (192, 512):
        save(make_maskable(tile, fill, size), f"icon-maskable-{size}.png")

    print("favicon (browser tab):")
    fav = make_favicon_source(tile)
    for size in (16, 32, 48, 96):
        save(resize(fav, size), f"favicon-{size}.png")
    # Hand the .ico each frame ready-made. Left to itself it would derive the
    # small frames from the 48px one, which loses the per-size sharpening.
    ico = os.path.join(OUT_DIR, "favicon.ico")
    frames = {size: crisp(resize(fav, size)) for size in (16, 32, 48)}
    frames[48].save(ico, sizes=[(s, s) for s in sorted(frames)],
                    append_images=[frames[16], frames[32]])
    print(f"  {ico:38s}       {os.path.getsize(ico) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
