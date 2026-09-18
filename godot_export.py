from __future__ import annotations

import json
from pathlib import Path


def _godot_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _validate_frames(atlas_metadata: dict) -> list[dict]:
    frames = atlas_metadata.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("atlas metadata must contain at least one frame")

    atlas_width = atlas_metadata.get("imageWidth")
    atlas_height = atlas_metadata.get("imageHeight")
    if atlas_width is not None:
        atlas_width = int(atlas_width)
    if atlas_height is not None:
        atlas_height = int(atlas_height)

    normalized = []
    for index, frame in enumerate(frames):
        try:
            x = int(frame["x"])
            y = int(frame["y"])
            width = int(frame["width"])
            height = int(frame["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid frame {index}: expected integer x/y/width/height"
            ) from exc

        if x < 0 or y < 0:
            raise ValueError(f"invalid frame {index}: x/y must be >= 0")
        if width <= 0 or height <= 0:
            raise ValueError(f"invalid frame {index}: width/height must be > 0")
        if atlas_width is not None and x + width > atlas_width:
            raise ValueError(f"invalid frame {index}: region exceeds atlas width")
        if atlas_height is not None and y + height > atlas_height:
            raise ValueError(f"invalid frame {index}: region exceeds atlas height")

        source_width = int(frame.get("sourceWidth", width))
        source_height = int(frame.get("sourceHeight", height))
        offset_x = int(frame.get("offsetX", 0))
        offset_y = int(frame.get("offsetY", 0))
        if source_width < width or source_height < height:
            raise ValueError(
                f"invalid frame {index}: source dimensions cannot be smaller than trimmed region"
            )
        if offset_x < 0 or offset_y < 0:
            raise ValueError(f"invalid frame {index}: trim offsets must be >= 0")
        if offset_x + width > source_width or offset_y + height > source_height:
            raise ValueError(
                f"invalid frame {index}: trimmed region does not fit source dimensions"
            )

        normalized.append(
            {
                "index": index,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "sourceWidth": source_width,
                "sourceHeight": source_height,
                "offsetX": offset_x,
                "offsetY": offset_y,
                "name": frame.get("name"),
            }
        )
    return normalized


def _normalize_animations(
    frame_count: int,
    animation_name: str,
    fps: float,
    loop: bool,
    animations: list[dict] | None,
) -> list[dict]:
    if animations is None:
        if fps <= 0:
            raise ValueError("fps must be > 0")
        return [
            {
                "name": animation_name,
                "fps": float(fps),
                "loop": bool(loop),
                "frames": [
                    {"index": index, "duration": 1.0}
                    for index in range(frame_count)
                ],
            }
        ]

    if not isinstance(animations, list) or not animations:
        raise ValueError("animations must be a non-empty list")

    seen_names: set[str] = set()
    normalized = []

    for position, animation in enumerate(animations):
        if not isinstance(animation, dict):
            raise ValueError(f"animation {position}: object required")

        name = animation.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"animation {position}: non-empty name required")
        if name in seen_names:
            raise ValueError(f"duplicate animation name: {name}")
        seen_names.add(name)

        speed = animation.get("fps", fps)
        if not isinstance(speed, (int, float)) or speed <= 0:
            raise ValueError(f"animation {name}: fps must be > 0")

        raw_frames = animation.get("frames")
        if not isinstance(raw_frames, list) or not raw_frames:
            raise ValueError(f"animation {name}: frames must be a non-empty list")

        animation_frames = []
        for frame_position, raw in enumerate(raw_frames):
            if isinstance(raw, int):
                frame_index = raw
                duration = 1.0
            elif isinstance(raw, dict):
                try:
                    frame_index = int(raw["index"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(
                        f"animation {name} frame {frame_position}: valid index required"
                    ) from exc
                duration = raw.get("duration", 1.0)
                if not isinstance(duration, (int, float)) or duration <= 0:
                    raise ValueError(
                        f"animation {name} frame {frame_position}: duration must be > 0"
                    )
                duration = float(duration)
            else:
                raise ValueError(
                    f"animation {name} frame {frame_position}: integer index or object required"
                )

            if frame_index < 0 or frame_index >= frame_count:
                raise ValueError(
                    f"animation {name} frame {frame_position}: index {frame_index} out of range"
                )

            animation_frames.append(
                {"index": frame_index, "duration": float(duration)}
            )

        normalized.append(
            {
                "name": name,
                "fps": float(speed),
                "loop": bool(animation.get("loop", loop)),
                "frames": animation_frames,
            }
        )

    return normalized


def render_spriteframes(
    atlas_path: str,
    atlas_metadata: dict,
    animation_name: str = "default",
    fps: float = 12.0,
    loop: bool = True,
    animations: list[dict] | None = None,
) -> str:
    """Render a Godot 4 SpriteFrames .tres backed by AtlasTexture regions."""
    frames = _validate_frames(atlas_metadata)
    animation_defs = _normalize_animations(
        len(frames),
        animation_name,
        fps,
        loop,
        animations,
    )

    lines = [
        f'[gd_resource type="SpriteFrames" load_steps={len(frames) + 2} format=3]',
        "",
        f'[ext_resource type="Texture2D" path={_godot_string(atlas_path)} id="1_atlas"]',
        "",
    ]

    resource_ids: list[str] = []
    for frame in frames:
        index = frame["index"]
        resource_id = f"AtlasTexture_{index}"
        resource_ids.append(resource_id)
        resource_lines = [
            f'[sub_resource type="AtlasTexture" id="{resource_id}"]',
            'atlas = ExtResource("1_atlas")',
            (
                f'region = Rect2({frame["x"]}, {frame["y"]}, '
                f'{frame["width"]}, {frame["height"]})'
            ),
        ]
        extra_width = frame["sourceWidth"] - frame["width"]
        extra_height = frame["sourceHeight"] - frame["height"]
        if extra_width or extra_height or frame["offsetX"] or frame["offsetY"]:
            resource_lines.append(
                f'margin = Rect2({frame["offsetX"]}, {frame["offsetY"]}, '
                f'{extra_width}, {extra_height})'
            )
        resource_lines.append("")
        lines.extend(resource_lines)

    rendered_animations = []
    for animation in animation_defs:
        frame_lines = []
        for frame in animation["frames"]:
            resource_id = resource_ids[frame["index"]]
            frame_lines.append(
                '{"duration": %s, "texture": SubResource("%s")}'
                % (float(frame["duration"]), resource_id)
            )

        rendered_animations.append(
            "{\n"
            f'"frames": [{", ".join(frame_lines)}],\n'
            f'"loop": {str(animation["loop"]).lower()},\n'
            f'"name": &{_godot_string(animation["name"])},\n'
            f'"speed": {float(animation["fps"])}\n'
            "}"
        )

    lines.extend(
        [
            "[resource]",
            "animations = [" + ",\n".join(rendered_animations) + "]",
            "",
        ]
    )
    return "\n".join(lines)


def write_spriteframes(
    output: Path,
    atlas_path: str,
    atlas_metadata: dict,
    animation_name: str = "default",
    fps: float = 12.0,
    loop: bool = True,
    animations: list[dict] | None = None,
) -> None:
    rendered = render_spriteframes(
        atlas_path=atlas_path,
        atlas_metadata=atlas_metadata,
        animation_name=animation_name,
        fps=fps,
        loop=loop,
        animations=animations,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
