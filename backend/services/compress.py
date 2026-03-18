"""
Image compression utility — resize + JPEG encode for fast CDN delivery.
"""
from __future__ import annotations
import io

_MAX_DIMENSION = 1200  # px on longest side
_JPEG_QUALITY = 82


def compress_image(image_bytes: bytes) -> bytes:
    """
    Resize to max 1200px on the longest side and encode as JPEG.
    Returns compressed bytes, or the original bytes if Pillow fails.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        w, h = img.size
        longest = max(w, h)
        if longest > _MAX_DIMENSION:
            scale = _MAX_DIMENSION / longest
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
        return buf.getvalue()
    except Exception as exc:
        print(f"[compress] failed: {exc}")
        return image_bytes
