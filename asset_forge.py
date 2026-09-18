#!/usr/bin/env python3
"""Dependency-free asset-forge manifest validator, planner, and PNG inspector."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

PIPELINES = {
    "sprite": "pipelines/sprite-2d.json",
    "sprite-sheet": "pipelines/sprite-2d.json",
    "tileset": "pipelines/sprite-2d.json",
    "pixel-art": "pipelines/sprite-2d.json",
    "mesh": "pipelines/model-3d.json",
    "prop": "pipelines/model-3d.json",
    "environment": "pipelines/model-3d.json",
    "character-3d": "pipelines/model-3d.json",
}

TOOL_DOMAINS = {
    "sprite": {"pixel-art", "sprites", "animation-2d"},
    "sprite-sheet": {"pixel-art", "sprites", "animation-2d"},
    "tileset": {"pixel-art", "sprites"},
    "pixel-art": {"pixel-art", "sprites"},
    "mesh": {"3d", "mesh-optimization", "3d-validation"},
    "prop": {"3d", "mesh-optimization", "3d-validation"},
    "environment": {"3d", "mesh-optimization", "3d-validation"},
    "character-3d": {"3d", "rigging", "animation-3d", "3d-validation"},
}

ALLOWED_IMPORTANCE = {"primary", "secondary"}
ALLOWED_SOURCE_MODES = {"custom", "external", "generated"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    for field in ("id", "project", "type"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}: non-empty string required")

    if manifest.get("importance") not in ALLOWED_IMPORTANCE:
        errors.append("importance: must be primary or secondary")

    source = manifest.get("source")
    if not isinstance(source, dict):
        errors.append("source: object required")
    else:
        mode = source.get("mode")
        if mode not in ALLOWED_SOURCE_MODES:
            errors.append("source.mode: must be custom, external, or generated")
        if mode == "external" and not source.get("uri"):
            errors.append("source.uri: required for external assets")

    license_data = manifest.get("license")
    if not isinstance(license_data, dict):
        errors.append("license: object required")
    else:
        license_id = license_data.get("id")
        if not isinstance(license_id, str) or not license_id.strip():
            errors.append("license.id: non-empty string required")
        if license_data.get("commercialUse") is not True:
            errors.append("license.commercialUse: must be true for production-ready assets")
        if license_data.get("derivatives") is not True:
            errors.append("license.derivatives: must be true for production-ready assets")

    target = manifest.get("target")
    if not isinstance(target, dict):
        errors.append("target: object required")
    else:
        output_format = target.get("format")
        if not isinstance(output_format, str) or not output_format.strip():
            errors.append("target.format: non-empty string required")
        max_bytes = target.get("maxBytes")
        if max_bytes is not None and (not isinstance(max_bytes, int) or max_bytes <= 0):
            errors.append("target.maxBytes: positive integer or null required")

    constraints = manifest.get("constraints", {})
    if constraints is not None and not isinstance(constraints, dict):
        errors.append("constraints: object required when present")
    return errors


def inspect_png(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != PNG_SIGNATURE:
        raise ValueError("file is not a valid PNG")
    length = struct.unpack(">I", data[8:12])[0]
    if data[12:16] != b"IHDR" or length != 13:
        raise ValueError("PNG is missing a valid IHDR chunk")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    return {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "hasAlpha": color_type in {4, 6},
        "compression": compression,
        "filter": filtering,
        "interlace": interlace,
        "bytes": len(data),
    }


def validate_raster_file(path: Path, manifest: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    target = manifest.get("target", {})
    if str(target.get("format", "")).lower() != "png":
        return {}, ["raster validation currently supports target.format=png only"]

    info = inspect_png(path)
    constraints = manifest.get("constraints", {}) or {}
    frame_width = constraints.get("frameWidth")
    frame_height = constraints.get("frameHeight")

    if isinstance(frame_width, int) and frame_width > 0 and info["width"] % frame_width != 0:
        errors.append(f"width {info['width']} is not divisible by frameWidth {frame_width}")
    if isinstance(frame_height, int) and frame_height > 0 and info["height"] % frame_height != 0:
        errors.append(f"height {info['height']} is not divisible by frameHeight {frame_height}")

    max_bytes = target.get("maxBytes")
    if isinstance(max_bytes, int) and info["bytes"] > max_bytes:
        errors.append(f"file size {info['bytes']} exceeds maxBytes {max_bytes}")

    if constraints.get("requiresAlpha") is True and not info["hasAlpha"]:
        errors.append("PNG does not contain an alpha channel")

    return info, errors


def select_tools(asset_type: str, registry: dict) -> list[dict]:
    wanted = TOOL_DOMAINS.get(asset_type, set())
    matches = []
    for tool in registry.get("tools", []):
        overlap = sorted(wanted & set(tool.get("domains", [])))
        if overlap:
            matches.append({"id": tool.get("id"), "status": tool.get("status"), "matchedDomains": overlap})
    status_rank = {"preferred": 0, "approved": 1, "candidate": 2}
    matches.sort(key=lambda item: (status_rank.get(item.get("status"), 9), item.get("id") or ""))
    return matches


def build_plan(manifest: dict, root: Path) -> dict:
    asset_type = manifest["type"]
    pipeline_path = PIPELINES.get(asset_type)
    source_mode = manifest["source"]["mode"]
    importance = manifest["importance"]

    if importance == "primary" and source_mode == "external":
        sourcing_policy = "review-external-or-replace-with-custom"
    elif importance == "secondary" and source_mode == "custom":
        sourcing_policy = "search-approved-assets-before-custom-creation"
    else:
        sourcing_policy = "follow-requested-source-mode"

    pipeline = load_json(root / pipeline_path) if pipeline_path else None
    registry = load_json(root / "config/tooling.json")
    return {
        "assetId": manifest["id"],
        "project": manifest["project"],
        "type": asset_type,
        "importance": importance,
        "sourcingPolicy": sourcing_policy,
        "pipeline": pipeline_path,
        "stages": pipeline.get("stages", []) if pipeline else [],
        "candidateTools": select_tools(asset_type, registry),
        "target": manifest["target"],
        "constraints": manifest.get("constraints", {}),
    }


def load_valid_manifest(path: Path) -> tuple[dict | None, int]:
    try:
        manifest = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return None, 2
    errors = validate_manifest(manifest)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return None, 1
    return manifest, 0


def cmd_validate(path: Path) -> int:
    manifest, code = load_valid_manifest(path)
    if manifest is None:
        return code
    print("VALID")
    return 0


def cmd_plan(path: Path, root: Path) -> int:
    manifest, code = load_valid_manifest(path)
    if manifest is None:
        return code
    print(json.dumps(build_plan(manifest, root), indent=2, sort_keys=True))
    return 0


def cmd_validate_raster(manifest_path: Path, asset_path: Path) -> int:
    manifest, code = load_valid_manifest(manifest_path)
    if manifest is None:
        return code
    try:
        info, errors = validate_raster_file(asset_path, manifest)
    except (OSError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    result = {"file": str(asset_path), "info": info, "errors": errors}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="asset-forge")
    sub = result.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate an asset manifest")
    validate.add_argument("manifest", type=Path)

    plan = sub.add_parser("plan", help="build a deterministic asset production plan")
    plan.add_argument("manifest", type=Path)

    raster = sub.add_parser("validate-raster", help="validate a PNG against an asset manifest")
    raster.add_argument("manifest", type=Path)
    raster.add_argument("asset", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    root = Path(__file__).resolve().parent
    if args.command == "validate":
        return cmd_validate(args.manifest)
    if args.command == "plan":
        return cmd_plan(args.manifest, root)
    if args.command == "validate-raster":
        return cmd_validate_raster(args.manifest, args.asset)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
