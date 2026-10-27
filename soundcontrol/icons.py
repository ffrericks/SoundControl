"""Builds the tray icon images from the app artwork in assets/icon.png."""

from __future__ import annotations

from functools import lru_cache

from paths import resource_path
from PIL import Image, ImageDraw

_TRAY_SIZE = 64


@lru_cache(maxsize=1)
def _source() -> Image.Image:
    return Image.open(resource_path("assets/icon.png")).convert("RGBA")


@lru_cache(maxsize=2)
def speaker_icon(muted: bool) -> Image.Image:
    img = _source().resize((_TRAY_SIZE, _TRAY_SIZE), Image.LANCZOS)
    if muted:
        img = _with_muted_badge(img)
    return img


def _with_muted_badge(img: Image.Image) -> Image.Image:
    img = img.copy()
    draw = ImageDraw.Draw(img)
    size = img.width
    badge = int(size * 0.52)
    x0, y0 = 0, size - badge
    x1, y1 = badge, size
    draw.ellipse(
        [x0, y0, x1, y1], fill=(216, 32, 32, 255), outline=(255, 255, 255, 255), width=2
    )
    pad = badge * 0.28
    draw.line(
        [x0 + pad, y0 + pad, x1 - pad, y1 - pad], fill=(255, 255, 255, 255), width=4
    )
    draw.line(
        [x0 + pad, y1 - pad, x1 - pad, y0 + pad], fill=(255, 255, 255, 255), width=4
    )
    return img
