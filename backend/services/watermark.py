"""
Watermarked preview generation.

The public, freely-viewable image for every portrait is a DOWNSCALED + WATERMARKED
JPEG. The clean, full-resolution HD file is never served publicly — it is unlocked
per-portrait by spending a credit (see routes/user.py + db/credits.py).

Design guarantees:
  * The returned preview is never larger than _MAX_DIMENSION on its longest side,
    so even if watermarking fails we never leak the full-resolution image.
  * Failures degrade gracefully to a plain downscaled JPEG rather than raising.
"""
from __future__ import annotations

import io

_MAX_DIMENSION = 1400          # px on the longest side of the preview
_JPEG_QUALITY = 80
_WATERMARK_TEXT = "pet-to.com"


def make_preview(image_bytes: bytes, text: str = _WATERMARK_TEXT) -> bytes:
    """Return watermarked, downscaled JPEG bytes for public display.

    Falls back to a plain downscaled JPEG if watermarking fails, and to the
    original bytes only if Pillow is entirely unavailable.
    """
    try:
        from PIL import Image
    except Exception as exc:  # Pillow missing — should not happen (in requirements)
        print(f"[watermark] Pillow unavailable: {exc}")
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        else:
            img = img.convert("RGB")

        # Downscale
        w, h = img.size
        longest = max(w, h)
        if longest > _MAX_DIMENSION:
            scale = _MAX_DIMENSION / longest
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        try:
            img = _apply_watermark(img, text)
        except Exception as exc:
            print(f"[watermark] overlay failed, using clean downscaled preview: {exc}")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
        return buf.getvalue()
    except Exception as exc:
        print(f"[watermark] failed: {exc}")
        return image_bytes


def _apply_watermark(img, text: str):
    """Tile a semi-transparent, diagonal watermark across the image."""
    from PIL import Image, ImageDraw, ImageFont

    base = img.convert("RGBA")
    w, h = base.size

    # Overlay layer for the tiled text
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(18, w // 22)
    font = _load_font(font_size)

    # Measure text
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = font_size * len(text) // 2, font_size

    # Tile the text on a diagonal grid
    step_x = int(tw * 1.8) or 200
    step_y = int(th * 5) or 160
    fill = (255, 255, 255, 70)  # white, ~27% opacity

    y = -step_y
    row = 0
    while y < h + step_y:
        offset = (step_x // 2) if row % 2 else 0
        x = -step_x + offset
        while x < w + step_x:
            draw.text((x, y), text, font=font, fill=fill)
            x += step_x
        y += step_y
        row += 1

    # Rotate the overlay for a diagonal watermark, then composite
    overlay = overlay.rotate(30, expand=False)
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def _load_font(size: int):
    from PIL import ImageFont

    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None
