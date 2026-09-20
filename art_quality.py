from __future__ import annotations

import math
from pathlib import Path


class ArtQualityError(RuntimeError):
    pass


def _percentile(values: list[int], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return float(ordered[index])


def _entropy(values: list[int]) -> float:
    if not values:
        return 0.0
    counts = [0] * 256
    for value in values:
        counts[value] += 1
    total = float(len(values))
    result = 0.0
    for count in counts:
        if not count:
            continue
        probability = count / total
        result -= probability * math.log2(probability)
    return result


def _grid(expected_frames: int) -> tuple[int, int]:
    columns = max(1, math.ceil(math.sqrt(expected_frames)))
    while columns < expected_frames and expected_frames % columns:
        columns += 1
    return columns, max(1, expected_frames // columns)



def _subject_perceptual_hash(image, *, size: int = 16) -> str:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    subject = image.crop(bbox) if bbox else image
    gray = subject.convert("L").resize((size, size))
    values = list(gray.getdata())
    average = sum(values) / max(1, len(values))
    bits = "".join("1" if value >= average else "0" for value in values)
    return "".join(
        f"{int(bits[index:index + 4], 2):x}"
        for index in range(0, len(bits), 4)
    )


def _average_visible_rgb(pixels) -> list[int]:
    visible = [(r, g, b) for r, g, b, a in pixels if a >= 32]
    if not visible:
        return [0, 0, 0]
    count = len(visible)
    return [
        int(round(sum(value[index] for value in visible) / count))
        for index in range(3)
    ]


def evaluate_raster_art(path: Path, manifest: dict) -> dict:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ArtQualityError("Pillow is required for technical art quality checks") from exc

    try:
        with Image.open(path) as image:
            image.load()
            rgba = image.convert("RGBA")
    except (OSError, ValueError) as exc:
        raise ArtQualityError(f"unable to inspect raster art: {type(exc).__name__}") from exc

    width, height = rgba.size
    pixels = list(rgba.getdata())
    alpha = [value[3] for value in pixels]
    perceptual_hash = _subject_perceptual_hash(rgba)
    average_rgb = _average_visible_rgb(pixels)
    visible = [value for value in pixels if value[3] >= 32]
    occupancy = len(visible) / max(1, len(pixels))

    border = []
    if width > 0 and height > 0:
        for x in range(width):
            border.append(rgba.getpixel((x, 0))[3])
            if height > 1:
                border.append(rgba.getpixel((x, height - 1))[3])
        for y in range(1, max(1, height - 1)):
            border.append(rgba.getpixel((0, y))[3])
            if width > 1:
                border.append(rgba.getpixel((width - 1, y))[3])
    border_alpha_ratio = sum(value >= 32 for value in border) / max(1, len(border))

    alpha_image = rgba.getchannel("A")
    bbox = alpha_image.getbbox()
    if bbox:
        left, top, right, bottom = bbox
        transparent_margin = min(left, top, width - right, height - bottom)
    else:
        transparent_margin = 0

    luminance = [
        int(round(0.2126 * r + 0.7152 * g + 0.0722 * b))
        for r, g, b, a in visible
    ]
    contrast_span = _percentile(luminance, 0.95) - _percentile(luminance, 0.05)
    entropy = _entropy(luminance)

    border_score = max(0.0, 1.0 - border_alpha_ratio / 0.12)
    if 0.08 <= occupancy <= 0.78:
        occupancy_score = 1.0
    elif occupancy < 0.08:
        occupancy_score = max(0.0, occupancy / 0.08)
    else:
        occupancy_score = max(0.0, 1.0 - (occupancy - 0.78) / 0.22)
    contrast_score = max(0.0, min(1.0, contrast_span / 110.0))
    entropy_score = max(0.0, min(1.0, entropy / 6.0))

    constraints = manifest.get("constraints") if isinstance(manifest, dict) else {}
    constraints = constraints if isinstance(constraints, dict) else {}
    expected_frames = constraints.get("expectedFrames")
    frame_consistency = 1.0
    frame_occupancies = []
    if isinstance(expected_frames, int) and expected_frames > 1:
        columns, rows = _grid(expected_frames)
        if width % columns == 0 and height % rows == 0:
            frame_width = width // columns
            frame_height = height // rows
            for index in range(expected_frames):
                col = index % columns
                row = index // columns
                frame = rgba.crop((
                    col * frame_width,
                    row * frame_height,
                    (col + 1) * frame_width,
                    (row + 1) * frame_height,
                ))
                frame_alpha = list(frame.getchannel("A").getdata())
                frame_occupancies.append(
                    sum(value >= 32 for value in frame_alpha) / max(1, len(frame_alpha))
                )
            mean = sum(frame_occupancies) / len(frame_occupancies)
            if mean > 0:
                variance = sum((value - mean) ** 2 for value in frame_occupancies) / len(frame_occupancies)
                frame_consistency = max(0.0, 1.0 - math.sqrt(variance) / mean)

    score = (
        0.30 * border_score
        + 0.20 * occupancy_score
        + 0.20 * contrast_score
        + 0.15 * entropy_score
        + 0.15 * frame_consistency
    )
    score = max(0.0, min(1.0, score))

    errors = []
    warnings = []
    if constraints.get("requiresAlpha") is True and min(alpha or [255]) >= 255:
        errors.append("transparent background required but raster is fully opaque")
    max_border = constraints.get("maxBorderAlphaRatio", 0.08)
    try:
        max_border = float(max_border)
    except (TypeError, ValueError):
        max_border = 0.08
    if border_alpha_ratio > max_border:
        warnings.append(
            f"visible art touches image border too often ({border_alpha_ratio:.3f} > {max_border:.3f})"
        )
    min_score = constraints.get("technicalQualityMin")
    if min_score is not None:
        try:
            required = float(min_score)
        except (TypeError, ValueError) as exc:
            raise ArtQualityError("technicalQualityMin must be numeric") from exc
        if not 0.0 <= required <= 1.0:
            raise ArtQualityError("technicalQualityMin must be between 0 and 1")
        if score < required:
            errors.append(
                f"technical art quality score {score:.3f} is below required {required:.3f}"
            )

    return {
        "score": round(score, 6),
        "passed": not errors,
        "metrics": {
            "occupancy": round(occupancy, 6),
            "borderAlphaRatio": round(border_alpha_ratio, 6),
            "transparentMargin": int(transparent_margin),
            "contrastSpan": round(contrast_span, 3),
            "luminanceEntropy": round(entropy, 6),
            "frameConsistency": round(frame_consistency, 6),
            "frameOccupancies": [round(value, 6) for value in frame_occupancies],
            "perceptualHash": perceptual_hash,
            "averageRgb": average_rgb,
        },
        "errors": errors,
        "warnings": warnings,
    }
