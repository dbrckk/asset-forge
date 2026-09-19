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



def validate_runtime_atlas(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["runtime atlas must be an object"]

    allowed_top = {
        "format",
        "version",
        "image",
        "imageSize",
        "frameCount",
        "capabilities",
        "frames",
    }
    unknown_top = sorted(set(data) - allowed_top)
    for field in unknown_top:
        errors.append(f"unknown top-level field: {field}")

    if data.get("format") != "asset-forge-runtime-atlas":
        errors.append("format must be asset-forge-runtime-atlas")
    if data.get("version") != 1:
        errors.append("version must be 1")

    image = data.get("image")
    if not isinstance(image, str) or not image.strip():
        errors.append("image must be a non-empty string")

    image_size = data.get("imageSize")
    if not isinstance(image_size, dict):
        errors.append("imageSize must be an object")
        atlas_width = atlas_height = None
    else:
        try:
            atlas_width = _positive_int(image_size.get("width"), "imageSize.width")
            atlas_height = _positive_int(image_size.get("height"), "imageSize.height")
        except ValueError as exc:
            errors.append(str(exc))
            atlas_width = atlas_height = None

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, dict):
        errors.append("capabilities must be an object")
    else:
        if capabilities.get("trimOffsets") is not True:
            errors.append("capabilities.trimOffsets must be true")
        if capabilities.get("clockwise90Rotation") is not True:
            errors.append("capabilities.clockwise90Rotation must be true")
        for field in sorted(set(capabilities) - {"trimOffsets", "clockwise90Rotation"}):
            errors.append(f"unknown capabilities field: {field}")

    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append("frames must be a non-empty array")
        frames = []

    frame_count = data.get("frameCount")
    if not isinstance(frame_count, int) or frame_count <= 0:
        errors.append("frameCount must be a positive integer")
    elif frame_count != len(frames):
        errors.append(
            f"frameCount {frame_count} does not match frames length {len(frames)}"
        )

    seen_indices: set[int] = set()
    allowed_frame = {
        "index",
        "name",
        "atlasRegion",
        "uv",
        "sourceRegion",
        "sourceSize",
        "trimOffset",
        "rotation",
    }

    for position, frame in enumerate(frames):
        if not isinstance(frame, dict):
            errors.append(f"frame {position}: object required")
            continue

        for field in sorted(set(frame) - allowed_frame):
            errors.append(f"frame {position}: unknown field {field}")

        index = frame.get("index")
        if not isinstance(index, int) or index < 0:
            errors.append(f"frame {position}.index must be a non-negative integer")
            index_label = position
        else:
            index_label = index
            if index in seen_indices:
                errors.append(f"duplicate frame index {index}")
            seen_indices.add(index)

        name = frame.get("name")
        if name is not None and not isinstance(name, str):
            errors.append(f"frame {index_label}.name must be string or null")

        atlas_region = frame.get("atlasRegion")
        if not isinstance(atlas_region, dict):
            errors.append(f"frame {index_label}.atlasRegion must be an object")
            region = None
        else:
            try:
                x = _non_negative_int(atlas_region.get("x"), f"frame {index_label}.atlasRegion.x")
                y = _non_negative_int(atlas_region.get("y"), f"frame {index_label}.atlasRegion.y")
                width = _positive_int(atlas_region.get("width"), f"frame {index_label}.atlasRegion.width")
                height = _positive_int(atlas_region.get("height"), f"frame {index_label}.atlasRegion.height")
                region = (x, y, width, height)
                if atlas_width is not None and x + width > atlas_width:
                    errors.append(f"frame {index_label}: atlasRegion exceeds image width")
                if atlas_height is not None and y + height > atlas_height:
                    errors.append(f"frame {index_label}: atlasRegion exceeds image height")
            except ValueError as exc:
                errors.append(str(exc))
                region = None

        def read_size(field_name: str):
            obj = frame.get(field_name)
            if not isinstance(obj, dict):
                errors.append(f"frame {index_label}.{field_name} must be an object")
                return None
            try:
                return (
                    _positive_int(obj.get("width"), f"frame {index_label}.{field_name}.width"),
                    _positive_int(obj.get("height"), f"frame {index_label}.{field_name}.height"),
                )
            except ValueError as exc:
                errors.append(str(exc))
                return None

        source_region = read_size("sourceRegion")
        source_size = read_size("sourceSize")

        trim_offset = frame.get("trimOffset")
        if not isinstance(trim_offset, dict):
            errors.append(f"frame {index_label}.trimOffset must be an object")
            offset = None
        else:
            try:
                offset = (
                    _non_negative_int(trim_offset.get("x"), f"frame {index_label}.trimOffset.x"),
                    _non_negative_int(trim_offset.get("y"), f"frame {index_label}.trimOffset.y"),
                )
            except ValueError as exc:
                errors.append(str(exc))
                offset = None

        rotation = frame.get("rotation")
        if not isinstance(rotation, dict):
            errors.append(f"frame {index_label}.rotation must be an object")
            rotated = None
            degrees = None
        else:
            rotated = rotation.get("rotated")
            degrees = rotation.get("degreesClockwise")
            if not isinstance(rotated, bool):
                errors.append(f"frame {index_label}.rotation.rotated must be boolean")
            if degrees not in {0, 90}:
                errors.append(f"frame {index_label}.rotation.degreesClockwise must be 0 or 90")
            if isinstance(rotated, bool) and degrees in {0, 90}:
                if rotated != (degrees == 90):
                    errors.append(
                        f"frame {index_label}: rotation flag and degreesClockwise disagree"
                    )

        uv = frame.get("uv")
        if not isinstance(uv, dict):
            errors.append(f"frame {index_label}.uv must be an object")
        else:
            values = []
            for key in ("u0", "v0", "u1", "v1"):
                value = uv.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    errors.append(f"frame {index_label}.uv.{key} must be a number")
                    values.append(None)
                elif not 0 <= float(value) <= 1:
                    errors.append(f"frame {index_label}.uv.{key} must be between 0 and 1")
                    values.append(None)
                else:
                    values.append(float(value))
            if all(value is not None for value in values) and region and atlas_width and atlas_height:
                x, y, width, height = region
                expected = (
                    x / atlas_width,
                    y / atlas_height,
                    (x + width) / atlas_width,
                    (y + height) / atlas_height,
                )
                for key, actual, wanted in zip(("u0", "v0", "u1", "v1"), values, expected):
                    if abs(actual - wanted) > 1e-9:
                        errors.append(f"frame {index_label}.uv.{key} does not match atlasRegion")

        if region and source_region and isinstance(rotated, bool) and degrees in {0, 90}:
            _, _, width, height = region
            source_region_width, source_region_height = source_region
            expected = (
                (source_region_height, source_region_width)
                if rotated
                else (source_region_width, source_region_height)
            )
            if (width, height) != expected:
                errors.append(
                    f"frame {index_label}: atlasRegion dimensions do not match rotation/sourceRegion"
                )

        if source_region and source_size and offset:
            source_region_width, source_region_height = source_region
            source_width, source_height = source_size
            offset_x, offset_y = offset
            if offset_x + source_region_width > source_width:
                errors.append(f"frame {index_label}: sourceRegion exceeds sourceSize.width")
            if offset_y + source_region_height > source_height:
                errors.append(f"frame {index_label}: sourceRegion exceeds sourceSize.height")

    return errors
