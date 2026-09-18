from __future__ import annotations

from pathlib import Path


def detect_pillow_webp() -> dict:
    try:
        from PIL import __version__ as pillow_version
        from PIL import features
    except ImportError:
        return {
            "available": False,
            "backend": "pillow",
            "pillowVersion": None,
            "webpVersion": None,
            "reason": "Pillow is not installed",
        }

    try:
        supported = bool(features.check_module("webp"))
    except (ValueError, AttributeError):
        supported = False

    webp_version = None
    if supported:
        try:
            webp_version = features.version_module("webp")
        except (ValueError, AttributeError):
            webp_version = None

    return {
        "available": supported,
        "backend": "pillow",
        "pillowVersion": pillow_version,
        "webpVersion": webp_version,
        "reason": None if supported else "Pillow is installed without WebP support",
    }


def decode_webp_rgba(path: Path, *, expected_width: int, expected_height: int) -> tuple[int, int, bytes]:
    status = detect_pillow_webp()
    if not status["available"]:
        raise ValueError(
            "WebP pixel decoding requires optional Pillow with libwebp support"
        )

    from PIL import Image

    try:
        with Image.open(path, formats=["WEBP"]) as image:
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("animated WebP is not supported as a raster atlas input")
            image.load()
            if image.size != (expected_width, expected_height):
                raise ValueError(
                    "decoded WebP dimensions do not match validated container dimensions"
                )
            rgba = image.convert("RGBA")
            pixels = rgba.tobytes()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"WebP decode failed: {exc}") from exc

    expected_bytes = expected_width * expected_height * 4
    if len(pixels) != expected_bytes:
        raise ValueError("decoded WebP RGBA buffer size mismatch")
    return expected_width, expected_height, pixels
