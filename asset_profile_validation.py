from __future__ import annotations

import json
from pathlib import Path


THREED_PROFILES = {"prop", "environment", "character"}
VECTOR_PROFILES = {"icon", "ui", "logo"}

THREED_RULE_TYPES = {
    "maxMeshes": int,
    "maxPrimitives": int,
    "maxMaterials": int,
    "maxVertices": int,
    "maxTriangles": int,
    "maxTextures": int,
    "allowAnimations": bool,
    "requireSkin": bool,
    "requireNormals": bool,
    "requireUvWhenTextured": bool,
    "maxTextureDimension": int,
    "maxEstimatedTextureMipBytes": int,
    "maxJointsPerSkin": int,
    "strictBudgets": bool,
    "requirePbrMaterials": bool,
}

VECTOR_RULE_TYPES = {
    "requireViewBox": bool,
    "requireSquareViewBox": bool,
    "maxElements": int,
    "allowExternalReferences": bool,
    "removeMetadata": bool,
    "maxBytes": int,
    "maxDepth": int,
}


def _load_json(path: Path) -> tuple[dict | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [f"file: {exc}"]
    except json.JSONDecodeError as exc:
        return None, [f"json: {exc.msg} at line {exc.lineno} column {exc.colno}"]
    if not isinstance(data, dict):
        return None, ["root: object required"]
    return data, []


def _validate_rule_types(
    rules,
    expected: dict[str, type],
    label: str,
    *,
    optional: frozenset[str] = frozenset(),
) -> list[str]:
    errors: list[str] = []
    if not isinstance(rules, dict):
        return [f"{label}: object required"]

    for key in rules:
        if key not in expected:
            errors.append(f"{label}.{key}: unknown field")

    for key, expected_type in expected.items():
        if key not in rules:
            if key not in optional:
                errors.append(f"{label}.{key}: required")
            continue
        if type(rules[key]) is not expected_type:
            errors.append(f"{label}.{key}: {expected_type.__name__} required")

    return errors


def validate_3d_profile_data(data: dict, expected_profile: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root: object required"]

    allowed = {"id", "assetTypes", "rules"}
    for key in data:
        if key not in allowed:
            errors.append(f"{key}: unknown field")

    profile_id = data.get("id")
    if profile_id not in THREED_PROFILES:
        errors.append("id: must be prop, environment, or character")
    if expected_profile is not None and profile_id != expected_profile:
        errors.append(f"id: expected {expected_profile}")

    asset_types = data.get("assetTypes")
    if not isinstance(asset_types, list) or not asset_types or any(
        not isinstance(item, str) or not item for item in asset_types
    ):
        errors.append("assetTypes: non-empty string array required")

    rules = data.get("rules")
    errors.extend(
        _validate_rule_types(
            rules,
            THREED_RULE_TYPES,
            "rules",
            optional=frozenset({"strictBudgets", "requirePbrMaterials"}),
        )
    )
    if isinstance(rules, dict):
        positive_or_zero = {
            "maxMeshes",
            "maxPrimitives",
            "maxMaterials",
            "maxVertices",
            "maxTriangles",
            "maxTextures",
            "maxTextureDimension",
            "maxEstimatedTextureMipBytes",
            "maxJointsPerSkin",
        }
        for key in positive_or_zero:
            value = rules.get(key)
            if type(value) is int and value < 0:
                errors.append(f"rules.{key}: must be >= 0")
        for key in ("maxMeshes", "maxPrimitives", "maxMaterials", "maxVertices", "maxTriangles", "maxTextures", "maxTextureDimension", "maxEstimatedTextureMipBytes"):
            value = rules.get(key)
            if type(value) is int and value == 0:
                errors.append(f"rules.{key}: must be > 0")
    return errors


def validate_vector_profile_data(data: dict, expected_profile: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root: object required"]

    allowed = {"id", "assetTypes", "rules"}
    for key in data:
        if key not in allowed:
            errors.append(f"{key}: unknown field")

    profile_id = data.get("id")
    if profile_id not in VECTOR_PROFILES:
        errors.append("id: must be icon, ui, or logo")
    if expected_profile is not None and profile_id != expected_profile:
        errors.append(f"id: expected {expected_profile}")

    asset_types = data.get("assetTypes")
    if not isinstance(asset_types, list) or not asset_types or any(
        not isinstance(item, str) or not item for item in asset_types
    ):
        errors.append("assetTypes: non-empty string array required")

    rules = data.get("rules")
    errors.extend(_validate_rule_types(rules, VECTOR_RULE_TYPES, "rules"))
    if isinstance(rules, dict):
        for key in ("maxElements", "maxBytes", "maxDepth"):
            value = rules.get(key)
            if type(value) is int and value <= 0:
                errors.append(f"rules.{key}: must be > 0")
    return errors


def validate_profile_file(
    path: Path,
    *,
    kind: str,
    expected_profile: str,
) -> tuple[dict | None, list[str]]:
    data, errors = _load_json(path)
    if errors or data is None:
        return data, errors
    if kind == "3d":
        errors.extend(validate_3d_profile_data(data, expected_profile))
    elif kind == "vector":
        errors.extend(validate_vector_profile_data(data, expected_profile))
    else:
        errors.append(f"kind: unsupported profile kind {kind}")
    return data, errors


def load_3d_profile(profile: str, root: Path | None = None) -> dict:
    if profile not in THREED_PROFILES:
        raise ValueError(f"unknown 3D quality profile: {profile}")
    base = root or Path(__file__).resolve().parent
    path = base / "profiles" / "3d" / f"{profile}.json"
    data, errors = validate_profile_file(path, kind="3d", expected_profile=profile)
    if errors:
        raise ValueError("3D profile invalid: " + "; ".join(errors))
    assert data is not None
    return data


def load_vector_profile(profile: str, root: Path | None = None) -> dict:
    if profile not in VECTOR_PROFILES:
        raise ValueError(f"unknown SVG profile: {profile}")
    base = root or Path(__file__).resolve().parent
    path = base / "profiles" / "vector" / f"{profile}.json"
    data, errors = validate_profile_file(path, kind="vector", expected_profile=profile)
    if errors:
        raise ValueError("vector profile invalid: " + "; ".join(errors))
    assert data is not None
    return data


def validate_all_asset_profiles(root: Path) -> dict:
    groups = {}
    valid = True

    for kind, profiles, folder in (
        ("3d", THREED_PROFILES, "3d"),
        ("vector", VECTOR_PROFILES, "vector"),
    ):
        group = {}
        for profile in sorted(profiles):
            path = root / "profiles" / folder / f"{profile}.json"
            _, errors = validate_profile_file(
                path,
                kind=kind,
                expected_profile=profile,
            )
            group[profile] = {
                "path": str(path),
                "errors": errors,
                "valid": not errors,
            }
            valid = valid and not errors
        groups[kind] = group

    return {
        "valid": valid,
        "groups": groups,
    }
