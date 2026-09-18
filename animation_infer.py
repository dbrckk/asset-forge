from __future__ import annotations

import re


FRAME_SUFFIX = re.compile(r"^(?P<name>.+?)(?:[_\-. ]?)(?P<number>\d+)$")


def infer_animations(
    atlas_metadata: dict,
    *,
    default_fps: float = 12.0,
    default_loop: bool = True,
) -> dict:
    if default_fps <= 0:
        raise ValueError("default_fps must be > 0")

    frames = atlas_metadata.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("atlas metadata must contain at least one frame")

    groups: dict[str, list[tuple[int, int]]] = {}

    for fallback_index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"frame {fallback_index}: object required")

        index = frame.get("index", fallback_index)
        if not isinstance(index, int) or index < 0:
            raise ValueError(f"frame {fallback_index}: non-negative integer index required")

        raw_name = frame.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            animation_name = "default"
            order = index
        else:
            stem = raw_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            if "." in stem:
                stem = stem.rsplit(".", 1)[0]

            match = FRAME_SUFFIX.match(stem)
            if match:
                animation_name = match.group("name").rstrip("_-. ").strip() or "default"
                order = int(match.group("number"))
            else:
                animation_name = stem.strip() or "default"
                order = index

        groups.setdefault(animation_name, []).append((order, index))

    animations = []
    for name in sorted(groups):
        ordered = sorted(groups[name], key=lambda item: (item[0], item[1]))
        animations.append(
            {
                "name": name,
                "fps": float(default_fps),
                "loop": bool(default_loop),
                "frames": [index for _, index in ordered],
            }
        )

    return {"animations": animations}
