"""
Tests for compress_image — resize-to-1200px + JPEG encode used on every upload.
We generate real images in-memory with Pillow so these test actual behavior,
not mocks.
"""
import io

from PIL import Image

from backend.services.compress import compress_image


def _image_bytes(width: int, height: int, fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", (width, height), (120, 60, 30))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _size_of(image_bytes: bytes) -> tuple[int, int]:
    return Image.open(io.BytesIO(image_bytes)).size


def test_large_image_is_downscaled_to_1200_longest_side():
    out = compress_image(_image_bytes(3000, 2000))
    w, h = _size_of(out)
    assert max(w, h) == 1200        # longest side clamped
    assert (w, h) == (1200, 800)    # aspect ratio preserved (3000:2000)


def test_output_is_always_jpeg():
    out = compress_image(_image_bytes(500, 500, fmt="PNG"))
    assert Image.open(io.BytesIO(out)).format == "JPEG"


def test_small_image_is_not_upscaled():
    out = compress_image(_image_bytes(400, 300))
    assert _size_of(out) == (400, 300)   # already under 1200 -> untouched dimensions


def test_invalid_bytes_return_the_original_unchanged():
    """If the bytes aren't a valid image, we must fail safe and return them as-is."""
    garbage = b"this is definitely not an image"
    assert compress_image(garbage) == garbage
