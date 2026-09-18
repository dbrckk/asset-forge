from __future__ import annotations

import json
from pathlib import Path


def _godot_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_spriteframes(
    atlas_path: str,
    atlas_metadata: dict,
    animation_name: str = "default",
    fps: float = 12.0,
    loop: bool = True,
) -> str:
    """Render a Godot 4 SpriteFrames .tres using AtlasTexture subresources."""
    if fps <= 0:
        raise ValueError("fps must be > 0")

    frames = atlas_metadata.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("atlas metadata must contain at least one frame")

    lines = [
        f'[gd_resource type="SpriteFrames" load_steps={len(frames) + 2} format=3]',
        "",
        f'[ext_resource type="Texture2D" path={_godot_string(atlas_path)} id="1_atlas"]',
        "",
    ]

    resource_ids: list[str] = []
    for index, frame in enumerate(frames):
        try:
            x = int(frame["x"])
            y = int(frame["y"])
            width = int(frame["width"])
            height = int(frame["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid frame {index}: expected integer x/y/width/height") from exc

        if width <= 0 or height <= 0:
            raise ValueError(f"invalid frame {index}: width/height must be > 0")

        resource_id = f"AtlasTexture_{index}"
        resource_ids.append(resource_id)
        lines.extend(
            [
                f'[sub_resource type="AtlasTexture" id="{resource_id}"]',
                'atlas = ExtResource("1_atlas")',
                f"region = Rect2({x}, {y}, {width}, {height})",
                "",
            ]
        )

    frame_lines = []
    for resource_id in resource_ids:
        frame_lines.append(
            '{"duration": 1.0, "texture": SubResource("%s")}' % resource_id
        )

    animation = (
        '[{\n'
        f'"frames": [{", ".join(frame_lines)}],\n'
        f'"loop": {str(loop).lower()},\n'
        f'"name": &{_godot_string(animation_name)},\n'
        f'"speed": {float(fps)}\n'
        '}]'
    )

    lines.extend(["[resource]", f"animations = {animation}", ""])
    return "\n".join(lines)


def write_spriteframes(
    output: Path,
    atlas_path: str,
    atlas_metadata: dict,
    animation_name: str = "default",
    fps: float = 12.0,
    loop: bool = True,
) -> None:
    rendered = render_spriteframes(
        atlas_path=atlas_path,
        atlas_metadata=atlas_metadata,
        animation_name=animation_name,
        fps=fps,
        loop=loop,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
