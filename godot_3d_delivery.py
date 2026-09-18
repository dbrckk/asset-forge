from __future__ import annotations

import re
from pathlib import Path

from gltf_quality import quality_report
from gltf_tools import load_gltf_json

GODOT_IMPORT_SUFFIXES = {
    "noimp",
    "navmesh",
    "vehicle",
    "wheel",
    "rigid",
    "loop",
    "cycle",
    "alpha",
    "vcol",
}

SAFE_NAME = re.compile(r"^[A-Za-z0-9_. $-]+$")


def _name_suffixes(name: str) -> list[str]:
    lowered = name.lower()
    found = []
    for suffix in sorted(GODOT_IMPORT_SUFFIXES):
        if (
            lowered.endswith("-" + suffix)
            or lowered.endswith("_" + suffix)
            or lowered.endswith("$" + suffix)
            or suffix in {"loop", "cycle"} and (lowered.startswith(suffix) or lowered.endswith(suffix))
        ):
            found.append(suffix)
    return found


def godot_3d_delivery_report(path: Path, profile: str = "prop") -> dict:
    data, container = load_gltf_json(path)
    quality = quality_report(path, profile)

    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if path.suffix.lower() != ".glb":
        warnings.append("Godot supports .gltf, but .glb is preferred for self-contained delivery")

    asset = data.get("asset", {})
    if not isinstance(asset, dict) or asset.get("version") != "2.0":
        errors.append("Godot delivery requires a valid glTF 2.0 asset")

    nodes = data.get("nodes", [])
    meshes = data.get("meshes", [])
    materials = data.get("materials", [])
    animations = data.get("animations", [])
    images = data.get("images", [])

    for key, value in (
        ("nodes", nodes),
        ("meshes", meshes),
        ("materials", materials),
        ("animations", animations),
        ("images", images),
    ):
        if not isinstance(value, list):
            errors.append(f"{key} must be an array")
    
    nodes = nodes if isinstance(nodes, list) else []
    meshes = meshes if isinstance(meshes, list) else []
    materials = materials if isinstance(materials, list) else []
    animations = animations if isinstance(animations, list) else []
    images = images if isinstance(images, list) else []

    unnamed_nodes = 0
    duplicate_names: dict[str, int] = {}
    suffix_usage: dict[str, int] = {}
    suspicious_names = []

    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = node.get("name")
        if not isinstance(name, str) or not name.strip():
            unnamed_nodes += 1
            continue
        duplicate_names[name] = duplicate_names.get(name, 0) + 1
        if not SAFE_NAME.match(name):
            suspicious_names.append(name)
        for suffix in _name_suffixes(name):
            suffix_usage[suffix] = suffix_usage.get(suffix, 0) + 1

    duplicates = sorted(name for name, count in duplicate_names.items() if count > 1)
    if unnamed_nodes:
        warnings.append(f"{unnamed_nodes} node(s) are unnamed; stable names improve scene integration")
    if duplicates:
        warnings.append("duplicate node names may make scripted lookup brittle: " + ", ".join(duplicates[:10]))
    if suspicious_names:
        warnings.append("some node names use unusual characters: " + ", ".join(suspicious_names[:10]))

    unnamed_animations = 0
    looping_hints = 0
    for animation in animations:
        if not isinstance(animation, dict):
            continue
        name = animation.get("name")
        if not isinstance(name, str) or not name.strip():
            unnamed_animations += 1
            continue
        suffixes = _name_suffixes(name)
        if "loop" in suffixes or "cycle" in suffixes:
            looping_hints += 1

    if animations and unnamed_animations:
        warnings.append(f"{unnamed_animations} animation(s) are unnamed")
    if animations and not looping_hints:
        recommendations.append(
            "for looping clips, consider Godot's loop/cycle naming hint or configure looping after import"
        )

    pbr_materials = 0
    double_sided = 0
    normal_mapped = 0
    for material in materials:
        if not isinstance(material, dict):
            continue
        if isinstance(material.get("pbrMetallicRoughness"), dict):
            pbr_materials += 1
        if material.get("doubleSided") is True:
            double_sided += 1
        if isinstance(material.get("normalTexture"), dict):
            normal_mapped += 1

    if materials and pbr_materials != len(materials):
        warnings.append(
            f"{len(materials) - pbr_materials} material(s) do not declare pbrMetallicRoughness"
        )
    if double_sided:
        warnings.append(
            f"{double_sided} double-sided material(s) may render more geometry than necessary in Godot"
        )

    attributes = quality.get("attributes", {})
    if normal_mapped and attributes.get("normalMappedPrimitivesWithTangent", 0) != attributes.get("normalMappedPrimitives", 0):
        warnings.append(
            "normal-mapped primitives without TANGENT may rely on Godot tangent generation"
        )

    remote_images = 0
    external_local_images = 0
    for image in quality.get("textures", {}).get("items", []):
        if image.get("source") == "remote":
            remote_images += 1
        elif image.get("source") == "external-local":
            external_local_images += 1

    if remote_images:
        errors.append(f"{remote_images} remote image(s) are unsuitable for deterministic project import")
    if external_local_images and path.suffix.lower() == ".glb":
        warnings.append(
            f"{external_local_images} external local image(s) make this GLB delivery less self-contained"
        )

    if profile == "character":
        rig = quality.get("rigAnimation", {})
        if not rig.get("skins"):
            errors.append("character delivery requires at least one skin")
        if animations and rig.get("animatedNodes", 0) == 0:
            warnings.append("animations exist but no animated target nodes were measured")

    evaluation = quality.get("evaluation", {})
    errors.extend(evaluation.get("errors", []))
    warnings.extend(evaluation.get("warnings", []))

    if suffix_usage:
        recommendations.append(
            "Godot import hints detected in names; keep nodes/use_name_suffixes enabled if this behavior is intended"
        )

    return {
        "file": str(path),
        "engine": "Godot 4",
        "format": container.get("container"),
        "profile": profile,
        "ready": not errors,
        "errors": errors,
        "warnings": warnings,
        "recommendations": recommendations,
        "scene": {
            "nodes": len(nodes),
            "meshes": len(meshes),
            "materials": len(materials),
            "animations": len(animations),
            "unnamedNodes": unnamed_nodes,
            "duplicateNodeNames": duplicates,
            "unnamedAnimations": unnamed_animations,
            "loopingAnimationHints": looping_hints,
            "godotNameSuffixes": suffix_usage,
        },
        "materials": {
            "pbrMetallicRoughness": pbr_materials,
            "doubleSided": double_sided,
            "normalMapped": normal_mapped,
        },
        "quality": quality,
    }
