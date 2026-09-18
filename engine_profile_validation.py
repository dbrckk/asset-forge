from __future__ import annotations

import json
from pathlib import Path

ALLOWED_PROFILES = {"prop", "environment", "character"}
SCENE_KEYS = {
    "useNameSuffixes": bool,
    "useNodeTypeSuffixes": bool,
    "generateTangentsIfMissing": bool,
    "preferStaticScene": bool,
}
OPTIONAL_SCENE_KEYS = {"navigationCandidate": bool}
ANIMATION_KEYS = {
    "import": bool,
    "fps": int,
    "trimming": bool,
    "removeImmutableTracks": bool,
}
TEXTURE_KEYS = {
    "preferEmbeddedOrProjectLocal": bool,
    "remoteUrisAllowed": bool,
}


def _validate_object_keys(
    value,
    *,
    label: str,
    required: dict[str, type],
    optional: dict[str, type] | None = None,
) -> list[str]:
    errors: list[str] = []
    optional = optional or {}
    if not isinstance(value, dict):
        return [f"{label}: object required"]

    allowed = set(required) | set(optional)
    for key in value:
        if key not in allowed:
            errors.append(f"{label}.{key}: unknown field")

    for key, expected in required.items():
        if key not in value:
            errors.append(f"{label}.{key}: required")
            continue
        if type(value[key]) is not expected:
            errors.append(f"{label}.{key}: {expected.__name__} required")

    for key, expected in optional.items():
        if key in value and type(value[key]) is not expected:
            errors.append(f"{label}.{key}: {expected.__name__} required")
    return errors


def validate_godot_profile_data(data: dict, expected_profile: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root: object required"]

    allowed_top = {"id", "engine", "assetProfile", "sceneImport", "animation", "textures"}
    for key in data:
        if key not in allowed_top:
            errors.append(f"{key}: unknown field")

    profile_id = data.get("id")
    if not isinstance(profile_id, str) or not profile_id.strip():
        errors.append("id: non-empty string required")

    if data.get("engine") != "Godot 4":
        errors.append("engine: must be 'Godot 4'")

    asset_profile = data.get("assetProfile")
    if asset_profile not in ALLOWED_PROFILES:
        errors.append("assetProfile: must be prop, environment, or character")
    if expected_profile is not None and asset_profile != expected_profile:
        errors.append(f"assetProfile: expected {expected_profile}")

    errors.extend(
        _validate_object_keys(
            data.get("sceneImport"),
            label="sceneImport",
            required=SCENE_KEYS,
            optional=OPTIONAL_SCENE_KEYS,
        )
    )
    errors.extend(
        _validate_object_keys(
            data.get("animation"),
            label="animation",
            required=ANIMATION_KEYS,
        )
    )
    errors.extend(
        _validate_object_keys(
            data.get("textures"),
            label="textures",
            required=TEXTURE_KEYS,
        )
    )

    animation = data.get("animation")
    if isinstance(animation, dict):
        fps = animation.get("fps")
        if type(fps) is int and not (1 <= fps <= 240):
            errors.append("animation.fps: must be between 1 and 240")

    return errors


def validate_godot_profile_file(path: Path, expected_profile: str | None = None) -> tuple[dict | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [f"file: {exc}"]
    except json.JSONDecodeError as exc:
        return None, [f"json: {exc.msg} at line {exc.lineno} column {exc.colno}"]

    if not isinstance(data, dict):
        return None, ["root: object required"]
    return data, validate_godot_profile_data(data, expected_profile=expected_profile)


def validate_all_godot_profiles(root: Path) -> dict:
    profile_dir = root / "profiles" / "godot4"
    results = {}
    valid = True
    for profile in sorted(ALLOWED_PROFILES):
        path = profile_dir / f"{profile}.json"
        _, errors = validate_godot_profile_file(path, expected_profile=profile)
        results[profile] = {
            "path": str(path),
            "errors": errors,
            "valid": not errors,
        }
        valid = valid and not errors

    return {
        "valid": valid,
        "profiles": results,
        "schema": str(root / "schemas" / "godot4-handoff-profile.schema.json"),
    }
