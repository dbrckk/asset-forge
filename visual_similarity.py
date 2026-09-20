from __future__ import annotations

from pathlib import Path


class VisualSimilarityError(RuntimeError):
    pass


def _load_rgba(path: Path, *, size: int = 32):
    try:
        from PIL import Image
    except ImportError as exc:
        raise VisualSimilarityError("Pillow is required for visual similarity checks") from exc
    try:
        with Image.open(path) as image:
            image.load()
            return image.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    except (OSError, ValueError) as exc:
        raise VisualSimilarityError(f"cannot inspect visual similarity image: {path}") from exc



def _crop_to_alpha_subject(image, *, padding_ratio: float = 0.08):
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return image
    left, top, right, bottom = bbox
    width = max(1, right - left)
    height = max(1, bottom - top)
    pad_x = max(1, int(round(width * padding_ratio)))
    pad_y = max(1, int(round(height * padding_ratio)))
    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(image.width, right + pad_x)
    bottom = min(image.height, bottom + pad_y)
    return image.crop((left, top, right, bottom))


def _subject_normalized(image, *, size: int = 32):
    subject = _crop_to_alpha_subject(image)
    return subject.resize((size, size))


def _edge_signature(image, width: int = 16, height: int = 16) -> list[int]:
    try:
        from PIL import ImageFilter
    except ImportError:
        return _average_hash(image, width, height)
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES).resize((width, height))
    pixels = list(edges.getdata())
    average = sum(pixels) / max(1, len(pixels))
    return [1 if value >= average else 0 for value in pixels]


def _histogram_signature(image, bins: int = 8) -> list[float]:
    rgba = list(image.getdata())
    values = [0.0] * (bins * 3)
    weight_total = 0.0
    for r, g, b, a in rgba:
        weight = a / 255.0
        if weight <= 0:
            continue
        values[min(bins - 1, r * bins // 256)] += weight
        values[bins + min(bins - 1, g * bins // 256)] += weight
        values[2 * bins + min(bins - 1, b * bins // 256)] += weight
        weight_total += weight
    if weight_total <= 0:
        return values
    scale = 1.0 / (weight_total * 3.0)
    return [value * scale for value in values]


def _histogram_similarity(a: list[float], b: list[float]) -> float:
    distance = sum(abs(x - y) for x, y in zip(a, b))
    return max(0.0, min(1.0, 1.0 - distance / 2.0))


def _average_hash(image, width: int = 16, height: int = 16) -> list[int]:
    gray = image.convert("L").resize((width, height))
    pixels = list(gray.getdata())
    average = sum(pixels) / max(1, len(pixels))
    return [1 if value >= average else 0 for value in pixels]


def _hash_similarity(a: list[int], b: list[int]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    distance = sum(1 for x, y in zip(a, b) if x != y)
    return 1.0 - distance / len(a)


def _alpha_occupancy(image) -> float:
    alpha = image.getchannel("A")
    pixels = list(alpha.getdata())
    return sum(1 for value in pixels if value >= 32) / max(1, len(pixels))


def _occupancy_similarity(a: float, b: float) -> float:
    return max(0.0, 1.0 - abs(a - b))



def _sprite_sheet_frames(image, *, max_frames: int = 4):
    width, height = image.size
    if width <= 0 or height <= 0:
        return [image]
    frames = []
    if width >= height * 2:
        columns = min(max_frames, max(2, round(width / height)))
        frame_width = width / columns
        for index in range(columns):
            left = int(round(index * frame_width))
            right = int(round((index + 1) * frame_width))
            if right > left:
                frames.append(image.crop((left, 0, right, height)))
    elif height >= width * 2:
        rows = min(max_frames, max(2, round(height / width)))
        frame_height = height / rows
        for index in range(rows):
            top = int(round(index * frame_height))
            bottom = int(round((index + 1) * frame_height))
            if bottom > top:
                frames.append(image.crop((0, top, width, bottom)))
    return frames or [image]


def _single_image_similarity(parent_image, child_image) -> dict:
    parent_subject = _subject_normalized(parent_image, size=32)
    child_subject = _subject_normalized(child_image, size=32)
    palette = _histogram_similarity(
        _histogram_signature(parent_subject),
        _histogram_signature(child_subject),
    )
    subject_structure = _hash_similarity(
        _average_hash(parent_subject),
        _average_hash(child_subject),
    )
    edge_structure = _hash_similarity(
        _edge_signature(parent_subject),
        _edge_signature(child_subject),
    )
    occupancy = _occupancy_similarity(
        _alpha_occupancy(parent_image),
        _alpha_occupancy(child_image),
    )
    score = (
        0.45 * palette
        + 0.20 * subject_structure
        + 0.25 * edge_structure
        + 0.10 * occupancy
    )
    return {
        "score": max(0.0, min(1.0, score)),
        "palette": palette,
        "subjectStructure": subject_structure,
        "edgeStructure": edge_structure,
        "occupancy": occupancy,
    }


def compare_visuals(parent: Path, child: Path) -> dict:
    parent_image = _load_rgba(Path(parent), size=64)
    child_image = _load_rgba(Path(child), size=64)

    parent_frames = _sprite_sheet_frames(parent_image)
    child_frames = _sprite_sheet_frames(child_image)
    frame_scores = []
    for child_frame in child_frames:
        candidates = [
            _single_image_similarity(parent_frame, child_frame)
            for parent_frame in parent_frames
        ]
        frame_scores.append(max(candidates, key=lambda item: item["score"]))

    best = sum(item["score"] for item in frame_scores) / max(1, len(frame_scores))
    components = {
        key: sum(item[key] for item in frame_scores) / max(1, len(frame_scores))
        for key in ("palette", "subjectStructure", "edgeStructure", "occupancy")
    }
    return {
        "score": round(max(0.0, min(1.0, best)), 6),
        "components": {key: round(value, 6) for key, value in components.items()},
        "frameScores": [round(item["score"], 6) for item in frame_scores],
        "parentFrameCount": len(parent_frames),
        "childFrameCount": len(child_frames),
        "parent": str(parent),
        "child": str(child),
    }


def compare_against_references(child: Path, references: list[Path]) -> dict:
    if not references:
        return {
            "score": None,
            "bestReference": None,
            "comparisons": [],
        }
    comparisons = [compare_visuals(reference, child) for reference in references]
    best = max(comparisons, key=lambda value: float(value["score"]))
    return {
        "score": best["score"],
        "bestReference": best["parent"],
        "comparisons": comparisons,
    }
