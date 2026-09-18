#!/usr/bin/env python3
"""Dependency-free asset-forge manifest validator, planner, PNG inspector, and atlas metadata builder."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

from animation_infer import infer_animations
from blender_adapter import build_blender_export_job, render_blender_command, write_blender_export_script, write_job_manifest
from gltf_diagnostics import deep_gltf_diagnostics
from gltf_quality import quality_report
from gltf_tools import inspect_gltf, validate_gltf_profile
from godot_export import write_spriteframes
from raster_pack import pack_uniform_atlas, recompress_png
from starlist_bridge import build_visual_discovery_report, run_starlist_recommender
from toolchain_3d import build_3d_pipeline, detect_3d_tools, execute_3d_pipeline, prepare_3d_pipeline
from svg_tools import inspect_svg, normalize_viewbox, sanitize_svg, validate_svg_profile

PIPELINES = {
    "sprite": "pipelines/sprite-2d.json",
    "sprite-sheet": "pipelines/sprite-2d.json",
    "tileset": "pipelines/sprite-2d.json",
    "pixel-art": "pipelines/sprite-2d.json",
    "mesh": "pipelines/model-3d.json",
    "prop": "pipelines/model-3d.json",
    "environment": "pipelines/model-3d.json",
    "character-3d": "pipelines/model-3d.json",
    "vector": "pipelines/vector-svg.json",
    "svg": "pipelines/vector-svg.json",
    "icon": "pipelines/vector-svg.json",
    "ui-vector": "pipelines/vector-svg.json",
    "logo": "pipelines/vector-svg.json",
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
    "vector": {"vector", "svg", "ui"},
    "svg": {"vector", "svg", "ui"},
    "icon": {"vector", "svg", "ui"},
    "ui-vector": {"vector", "svg", "ui"},
    "logo": {"vector", "svg"},
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
    elif isinstance(constraints, dict):
        if constraints.get("pixelArt") is True and constraints.get("interpolation", "nearest") != "nearest":
            errors.append("constraints.interpolation: pixelArt assets must use nearest")
        for field in ("frameWidth", "frameHeight", "maxColors", "expectedFrames"):
            value = constraints.get(field)
            if value is not None and (not isinstance(value, int) or value <= 0):
                errors.append(f"constraints.{field}: positive integer required when present")

    return errors


def is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def parse_png_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if len(data) < 33 or data[:8] != PNG_SIGNATURE:
        raise ValueError("file is not a valid PNG")

    chunks: list[tuple[bytes, bytes]] = []
    offset = 8
    saw_iend = False

    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("PNG contains a truncated chunk header")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError(f"PNG chunk {kind.decode('latin1')} is truncated")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise ValueError(f"PNG chunk {kind.decode('latin1')} has invalid CRC")
        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND":
            saw_iend = True
            break

    if not saw_iend:
        raise ValueError("PNG is missing IEND")
    return chunks


def inspect_png(path: Path) -> dict:
    data = path.read_bytes()
    chunks = parse_png_chunks(data)
    if not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        raise ValueError("PNG is missing a valid IHDR chunk")

    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", chunks[0][1]
    )
    palette_entries = None
    has_trns = False
    idat_bytes = 0

    for kind, payload in chunks[1:]:
        if kind == b"PLTE":
            if len(payload) % 3 != 0:
                raise ValueError("PNG PLTE chunk length must be divisible by 3")
            palette_entries = len(payload) // 3
        elif kind == b"tRNS":
            has_trns = True
        elif kind == b"IDAT":
            idat_bytes += len(payload)

    has_alpha = color_type in {4, 6} or has_trns
    return {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "hasAlpha": has_alpha,
        "paletteEntries": palette_entries,
        "compressedImageBytes": idat_bytes,
        "compression": compression,
        "filter": filtering,
        "interlace": interlace,
        "bytes": len(data),
    }


def sprite_grid(info: dict, constraints: dict) -> dict:
    frame_width = constraints.get("frameWidth")
    frame_height = constraints.get("frameHeight")
    if not isinstance(frame_width, int) or frame_width <= 0:
        raise ValueError("frameWidth is required to derive a sprite grid")
    if not isinstance(frame_height, int) or frame_height <= 0:
        raise ValueError("frameHeight is required to derive a sprite grid")
    if info["width"] % frame_width != 0 or info["height"] % frame_height != 0:
        raise ValueError("sprite dimensions are not divisible by frame dimensions")

    columns = info["width"] // frame_width
    rows = info["height"] // frame_height
    return {
        "frameWidth": frame_width,
        "frameHeight": frame_height,
        "columns": columns,
        "rows": rows,
        "frameCount": columns * rows,
    }


def build_atlas_manifest(path: Path, manifest: dict) -> dict:
    info = inspect_png(path)
    constraints = manifest.get("constraints", {}) or {}
    grid = sprite_grid(info, constraints)
    frames = []
    index = 0
    for row in range(grid["rows"]):
        for column in range(grid["columns"]):
            frames.append(
                {
                    "index": index,
                    "x": column * grid["frameWidth"],
                    "y": row * grid["frameHeight"],
                    "width": grid["frameWidth"],
                    "height": grid["frameHeight"],
                }
            )
            index += 1

    return {
        "assetId": manifest["id"],
        "image": path.name,
        "imageWidth": info["width"],
        "imageHeight": info["height"],
        "columns": grid["columns"],
        "rows": grid["rows"],
        "frameCount": grid["frameCount"],
        "frames": frames,
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
        errors.append("PNG does not contain transparency")

    max_colors = constraints.get("maxColors")
    if isinstance(max_colors, int) and info["paletteEntries"] is not None and info["paletteEntries"] > max_colors:
        errors.append(f"palette has {info['paletteEntries']} entries, exceeds maxColors {max_colors}")

    if constraints.get("powerOfTwoAtlas") is True:
        if not is_power_of_two(info["width"]) or not is_power_of_two(info["height"]):
            errors.append("atlas dimensions must be powers of two")

    if (
        isinstance(frame_width, int)
        and frame_width > 0
        and isinstance(frame_height, int)
        and frame_height > 0
        and info["width"] % frame_width == 0
        and info["height"] % frame_height == 0
    ):
        grid = sprite_grid(info, constraints)
        info["grid"] = grid
        expected_frames = constraints.get("expectedFrames")
        if isinstance(expected_frames, int) and grid["frameCount"] != expected_frames:
            errors.append(
                f"frameCount {grid['frameCount']} does not match expectedFrames {expected_frames}"
            )

    return info, errors


def select_tools(asset_type: str, registry: dict) -> list[dict]:
    wanted = TOOL_DOMAINS.get(asset_type, set())
    matches = []
    for tool in registry.get("tools", []):
        overlap = sorted(wanted & set(tool.get("domains", [])))
        if overlap:
            matches.append(
                {
                    "id": tool.get("id"),
                    "status": tool.get("status"),
                    "matchedDomains": overlap,
                }
            )
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


def cmd_atlas_manifest(manifest_path: Path, asset_path: Path, output: Path | None) -> int:
    manifest, code = load_valid_manifest(manifest_path)
    if manifest is None:
        return code
    try:
        _, errors = validate_raster_file(asset_path, manifest)
        if errors:
            print(json.dumps({"errors": errors}, indent=2), file=sys.stderr)
            return 1
        atlas = build_atlas_manifest(asset_path, manifest)
    except (OSError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(atlas, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(str(output))
    return 0


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

    atlas = sub.add_parser("atlas-manifest", help="build uniform-grid atlas metadata from a PNG")
    atlas.add_argument("manifest", type=Path)
    atlas.add_argument("asset", type=Path)
    atlas.add_argument("--output", type=Path)

    pack = sub.add_parser("pack-atlas", help="pack equal-size RGB/RGBA PNG frames into an atlas")
    pack.add_argument("output", type=Path)
    pack.add_argument("inputs", type=Path, nargs="+")
    pack.add_argument("--metadata", type=Path)
    pack.add_argument("--columns", type=int)
    pack.add_argument("--padding", type=int, default=0)
    pack.add_argument("--power-of-two", action="store_true")

    optimize = sub.add_parser("optimize-png", help="losslessly recompress a supported PNG")
    optimize.add_argument("input", type=Path)
    optimize.add_argument("output", type=Path)

    godot = sub.add_parser("export-godot", help="export Godot 4 SpriteFrames .tres from atlas metadata")
    godot.add_argument("metadata", type=Path)
    godot.add_argument("output", type=Path)
    godot.add_argument("--atlas-path", required=True)
    godot.add_argument("--animation", default="default")
    godot.add_argument("--fps", type=float, default=12.0)
    godot.add_argument("--no-loop", action="store_true")
    godot.add_argument("--animations", type=Path, help="JSON file defining multiple animations")

    discover = sub.add_parser("discover-tools", help="query dbrckk/star-list for visual tooling")
    discover.add_argument("star_list_root", type=Path)
    discover.add_argument("query", nargs="?")
    discover.add_argument("--top", type=int, default=8)
    discover.add_argument("--domain", default="graphics")
    discover.add_argument("--max-complexity", choices=["low", "medium", "high"], default="medium")
    discover.add_argument("--full-report", action="store_true")
    discover.add_argument("--output", type=Path)

    infer = sub.add_parser("infer-animations", help="infer animation groups from atlas frame filenames")
    infer.add_argument("metadata", type=Path)
    infer.add_argument("--fps", type=float, default=12.0)
    infer.add_argument("--no-loop", action="store_true")
    infer.add_argument("--output", type=Path)

    svg_validate = sub.add_parser("validate-svg", help="validate an SVG for safe project use")
    svg_validate.add_argument("input", type=Path)
    svg_validate.add_argument("--profile", choices=["icon", "ui", "logo"])

    svg_sanitize = sub.add_parser("sanitize-svg", help="remove unsafe SVG content")
    svg_sanitize.add_argument("input", type=Path)
    svg_sanitize.add_argument("output", type=Path)

    svg_normalize = sub.add_parser("normalize-svg", help="ensure SVG has a usable viewBox")
    svg_normalize.add_argument("input", type=Path)
    svg_normalize.add_argument("output", type=Path)

    gltf_validate = sub.add_parser("validate-gltf", help="validate glTF/GLB structure")
    gltf_validate.add_argument("input", type=Path)
    gltf_validate.add_argument("--profile", choices=["prop", "environment", "character"])

    gltf_quality = sub.add_parser("quality-gltf", help="measure glTF/GLB production quality")
    gltf_quality.add_argument("input", type=Path)
    gltf_quality.add_argument("--profile", choices=["prop", "environment", "character"])
    gltf_quality.add_argument("--output", type=Path)

    gltf_diagnose = sub.add_parser("diagnose-gltf", help="run deep accessor, skinning, and animation diagnostics")
    gltf_diagnose.add_argument("input", type=Path)
    gltf_diagnose.add_argument("--output", type=Path)

    blender_job = sub.add_parser("blender-export-job", help="create a reproducible Blender GLB export job")
    blender_job.add_argument("source_blend", type=Path)
    blender_job.add_argument("output_glb", type=Path)
    blender_job.add_argument("--script", type=Path, required=True)
    blender_job.add_argument("--job-manifest", type=Path)
    blender_job.add_argument("--blender", default="blender")
    blender_job.add_argument("--selection-only", action="store_true")
    blender_job.add_argument("--no-animations", action="store_true")
    blender_job.add_argument("--no-apply-modifiers", action="store_true")

    toolchain_status = sub.add_parser("3d-toolchain-status", help="detect available external 3D tools")

    pipeline3d = sub.add_parser("prepare-3d", help="prepare Blender to GLB validation/optimization pipeline")
    pipeline3d.add_argument("source_blend", type=Path)
    pipeline3d.add_argument("workdir", type=Path)
    pipeline3d.add_argument("--profile", choices=["prop", "environment", "character"], default="prop")
    pipeline3d.add_argument("--optimizer", choices=["none", "gltf-transform", "gltfpack"], default="gltf-transform")
    pipeline3d.add_argument("--texture-compress", choices=["webp"])
    pipeline3d.add_argument("--mesh-compression", action="store_true")
    pipeline3d.add_argument("--no-animations", action="store_true")

    run3d = sub.add_parser("run-3d", help="run Blender to GLB validation/optimization pipeline")
    run3d.add_argument("source_blend", type=Path)
    run3d.add_argument("workdir", type=Path)
    run3d.add_argument("--profile", choices=["prop", "environment", "character"], default="prop")
    run3d.add_argument("--optimizer", choices=["none", "gltf-transform", "gltfpack"], default="gltf-transform")
    run3d.add_argument("--texture-compress", choices=["webp"])
    run3d.add_argument("--mesh-compression", action="store_true")
    run3d.add_argument("--no-animations", action="store_true")
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
    if args.command == "atlas-manifest":
        return cmd_atlas_manifest(args.manifest, args.asset, args.output)
    if args.command == "pack-atlas":
        try:
            metadata = pack_uniform_atlas(
                args.inputs,
                args.output,
                columns=args.columns,
                padding=args.padding,
                power_of_two=args.power_of_two,
            )
        except (OSError, ValueError, zlib.error) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        rendered = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        if args.metadata:
            args.metadata.parent.mkdir(parents=True, exist_ok=True)
            args.metadata.write_text(rendered, encoding="utf-8")
            print(str(args.metadata))
        else:
            print(rendered, end="")
        return 0
    if args.command == "optimize-png":
        try:
            result = recompress_png(args.input, args.output)
        except (OSError, ValueError, zlib.error) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "export-godot":
        try:
            metadata = load_json(args.metadata)
            animations = None
            if args.animations:
                animation_config = load_json(args.animations)
                animations = animation_config.get("animations")
            write_spriteframes(
                output=args.output,
                atlas_path=args.atlas_path,
                atlas_metadata=metadata,
                animation_name=args.animation,
                fps=args.fps,
                loop=not args.no_loop,
                animations=animations,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(str(args.output))
        return 0
    if args.command == "discover-tools":
        try:
            if args.full_report:
                result = build_visual_discovery_report(args.star_list_root)
            else:
                if not args.query:
                    raise ValueError("query is required unless --full-report is used")
                result = run_starlist_recommender(
                    args.star_list_root,
                    args.query,
                    top=args.top,
                    domain=args.domain,
                    max_complexity=args.max_complexity,
                )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(str(args.output))
        else:
            print(rendered, end="")
        return 0
    if args.command == "infer-animations":
        try:
            metadata = load_json(args.metadata)
            result = infer_animations(
                metadata,
                default_fps=args.fps,
                default_loop=not args.no_loop,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(str(args.output))
        else:
            print(rendered, end="")
        return 0
    if args.command == "validate-svg":
        try:
            if args.profile:
                info, errors, warnings = validate_svg_profile(args.input, args.profile)
            else:
                info, errors, warnings = inspect_svg(args.input)
        except OSError as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        result = {"file": str(args.input), "info": info, "errors": errors, "warnings": warnings}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if errors else 0
    if args.command == "sanitize-svg":
        try:
            result = sanitize_svg(args.input, args.output)
        except (OSError, ValueError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "normalize-svg":
        try:
            result = normalize_viewbox(args.input, args.output)
        except (OSError, ValueError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "validate-gltf":
        try:
            if args.profile:
                info, errors, warnings = validate_gltf_profile(args.input, args.profile)
            else:
                info, errors, warnings = inspect_gltf(args.input)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        result = {"file": str(args.input), "info": info, "errors": errors, "warnings": warnings}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if errors else 0
    if args.command == "diagnose-gltf":
        try:
            result = deep_gltf_diagnostics(args.input)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(str(args.output))
        else:
            print(rendered, end="")
        has_errors = any(
            result.get(section, {}).get("errors")
            for section in ("accessors", "skinning", "animations")
        )
        return 1 if has_errors else 0
    if args.command == "quality-gltf":
        try:
            result = quality_report(args.input, args.profile)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(str(args.output))
        else:
            print(rendered, end="")
        evaluation = result.get("evaluation")
        return 1 if evaluation and not evaluation.get("passed", False) else 0
    if args.command == "blender-export-job":
        try:
            job = build_blender_export_job(
                args.source_blend,
                args.output_glb,
                selection_only=args.selection_only,
                animations=not args.no_animations,
                apply_modifiers=not args.no_apply_modifiers,
            )
            write_blender_export_script(job, args.script)
            if args.job_manifest:
                write_job_manifest(job, args.job_manifest)
            result = {
                "job": job,
                "script": str(args.script),
                "command": render_blender_command(args.blender, args.script),
            }
        except (OSError, ValueError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "3d-toolchain-status":
        print(json.dumps(detect_3d_tools(), indent=2, sort_keys=True))
        return 0
    if args.command == "prepare-3d":
        try:
            plan = build_3d_pipeline(
                args.source_blend,
                args.workdir,
                profile=args.profile,
                optimizer=args.optimizer,
                texture_compress=args.texture_compress,
                mesh_compression=args.mesh_compression,
                animations=not args.no_animations,
            )
            prepare_3d_pipeline(plan)
        except (OSError, ValueError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    if args.command == "run-3d":
        try:
            plan = build_3d_pipeline(
                args.source_blend,
                args.workdir,
                profile=args.profile,
                optimizer=args.optimizer,
                texture_compress=args.texture_compress,
                mesh_compression=args.mesh_compression,
                animations=not args.no_animations,
            )
            result = execute_3d_pipeline(plan, root)
        except (OSError, ValueError) as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["success"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
