from __future__ import annotations


def _positive_int(value, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}: integer required") from exc
    if result <= 0:
        raise ValueError(f"{field}: must be > 0")
    return result


def _non_negative_int(value, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}: integer required") from exc
    if result < 0:
        raise ValueError(f"{field}: must be >= 0")
    return result


def build_runtime_atlas(atlas_metadata: dict) -> dict:
    if not isinstance(atlas_metadata, dict):
        raise ValueError("atlas metadata must be an object")

    frames = atlas_metadata.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("atlas metadata must contain at least one frame")

    image = atlas_metadata.get("image")
    if not isinstance(image, str) or not image.strip():
        raise ValueError("atlas metadata image must be a non-empty string")

    atlas_width = _positive_int(atlas_metadata.get("imageWidth"), "imageWidth")
    atlas_height = _positive_int(atlas_metadata.get("imageHeight"), "imageHeight")

    runtime_frames = []
    seen_indices: set[int] = set()

    for fallback_index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"frame {fallback_index}: object required")

        index = _non_negative_int(frame.get("index", fallback_index), f"frame {fallback_index}.index")
        if index in seen_indices:
            raise ValueError(f"duplicate frame index {index}")
        seen_indices.add(index)

        x = _non_negative_int(frame.get("x"), f"frame {index}.x")
        y = _non_negative_int(frame.get("y"), f"frame {index}.y")
        width = _positive_int(frame.get("width"), f"frame {index}.width")
        height = _positive_int(frame.get("height"), f"frame {index}.height")

        if x + width > atlas_width or y + height > atlas_height:
            raise ValueError(f"frame {index}: atlas region exceeds image bounds")

        rotated = bool(frame.get("rotated", False))
        rotation_degrees = int(frame.get("rotationDegrees", 90 if rotated else 0))
        if rotated and rotation_degrees != 90:
            raise ValueError(f"frame {index}: rotated frames must use 90 degrees")
        if not rotated and rotation_degrees != 0:
            raise ValueError(f"frame {index}: non-rotated frames must use 0 degrees")

        source_region_width = _positive_int(
            frame.get("sourceRegionWidth", height if rotated else width),
            f"frame {index}.sourceRegionWidth",
        )
        source_region_height = _positive_int(
            frame.get("sourceRegionHeight", width if rotated else height),
            f"frame {index}.sourceRegionHeight",
        )

        expected_width = source_region_height if rotated else source_region_width
        expected_height = source_region_width if rotated else source_region_height
        if (width, height) != (expected_width, expected_height):
            raise ValueError(
                f"frame {index}: atlas region dimensions do not match rotation metadata"
            )

        source_width = _positive_int(
            frame.get("sourceWidth", source_region_width),
            f"frame {index}.sourceWidth",
        )
        source_height = _positive_int(
            frame.get("sourceHeight", source_region_height),
            f"frame {index}.sourceHeight",
        )
        offset_x = _non_negative_int(frame.get("offsetX", 0), f"frame {index}.offsetX")
        offset_y = _non_negative_int(frame.get("offsetY", 0), f"frame {index}.offsetY")

        if offset_x + source_region_width > source_width:
            raise ValueError(f"frame {index}: source region exceeds sourceWidth")
        if offset_y + source_region_height > source_height:
            raise ValueError(f"frame {index}: source region exceeds sourceHeight")

        runtime_frames.append(
            {
                "index": index,
                "name": frame.get("name"),
                "atlasRegion": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                },
                "uv": {
                    "u0": x / atlas_width,
                    "v0": y / atlas_height,
                    "u1": (x + width) / atlas_width,
                    "v1": (y + height) / atlas_height,
                },
                "sourceRegion": {
                    "width": source_region_width,
                    "height": source_region_height,
                },
                "sourceSize": {
                    "width": source_width,
                    "height": source_height,
                },
                "trimOffset": {
                    "x": offset_x,
                    "y": offset_y,
                },
                "rotation": {
                    "rotated": rotated,
                    "degreesClockwise": rotation_degrees,
                },
            }
        )

    runtime_frames.sort(key=lambda item: item["index"])
    return {
        "format": "asset-forge-runtime-atlas",
        "version": 1,
        "image": image,
        "imageSize": {
            "width": atlas_width,
            "height": atlas_height,
        },
        "frameCount": len(runtime_frames),
        "capabilities": {
            "trimOffsets": True,
            "clockwise90Rotation": True,
        },
        "frames": runtime_frames,
    }
