from __future__ import annotations

import json
import struct
from pathlib import Path

GLB_MAGIC = 0x46546C67
GLB_JSON_CHUNK = 0x4E4F534A
GLB_BIN_CHUNK = 0x004E4942


def load_gltf_json(path: Path) -> tuple[dict, dict]:
    suffix = path.suffix.lower()
    if suffix == ".gltf":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("glTF root must be a JSON object")
        return data, {"container": "gltf", "bytes": path.stat().st_size}

    if suffix != ".glb":
        raise ValueError("expected .gltf or .glb")

    raw = path.read_bytes()
    if len(raw) < 12:
        raise ValueError("GLB header is truncated")

    magic, version, total_length = struct.unpack("<III", raw[:12])
    if magic != GLB_MAGIC:
        raise ValueError("invalid GLB magic")
    if version != 2:
        raise ValueError(f"unsupported GLB version {version}")
    if total_length != len(raw):
        raise ValueError("GLB declared length does not match file length")

    offset = 12
    json_chunk = None
    bin_bytes = 0
    chunk_count = 0

    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError("truncated GLB chunk header")
        chunk_length, chunk_type = struct.unpack("<II", raw[offset : offset + 8])
        offset += 8
        end = offset + chunk_length
        if end > len(raw):
            raise ValueError("truncated GLB chunk")
        payload = raw[offset:end]
        offset = end
        chunk_count += 1

        if chunk_type == GLB_JSON_CHUNK:
            if json_chunk is not None:
                raise ValueError("GLB contains multiple JSON chunks")
            json_chunk = payload
        elif chunk_type == GLB_BIN_CHUNK:
            bin_bytes += len(payload)

    if json_chunk is None:
        raise ValueError("GLB is missing JSON chunk")

    try:
        data = json.loads(json_chunk.decode("utf-8").rstrip(" \t\r\n\x00"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("GLB JSON chunk is invalid") from exc

    if not isinstance(data, dict):
        raise ValueError("GLB JSON root must be an object")

    return data, {
        "container": "glb",
        "bytes": len(raw),
        "chunks": chunk_count,
        "binaryBytes": bin_bytes,
    }


def _count_primitives(data: dict) -> tuple[int, int]:
    meshes = data.get("meshes", [])
    if not isinstance(meshes, list):
        return 0, 0
    primitive_count = 0
    indexed_primitive_count = 0
    for mesh in meshes:
        if not isinstance(mesh, dict):
            continue
        primitives = mesh.get("primitives", [])
        if not isinstance(primitives, list):
            continue
        primitive_count += len(primitives)
        for primitive in primitives:
            if isinstance(primitive, dict) and "indices" in primitive:
                indexed_primitive_count += 1
    return primitive_count, indexed_primitive_count



def _validate_index_references(data: dict) -> list[str]:
    errors: list[str] = []
    nodes = data.get("nodes", [])
    meshes = data.get("meshes", [])
    materials = data.get("materials", [])
    accessors = data.get("accessors", [])
    buffer_views = data.get("bufferViews", [])
    buffers = data.get("buffers", [])
    textures = data.get("textures", [])
    images = data.get("images", [])
    samplers = data.get("samplers", [])
    skins = data.get("skins", [])

    def check(value, size, label):
        if not isinstance(value, int) or value < 0 or value >= size:
            errors.append(f"{label} index {value!r} is out of range")

    if isinstance(nodes, list):
        for node_index, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            if "mesh" in node and isinstance(meshes, list):
                check(node["mesh"], len(meshes), f"nodes[{node_index}].mesh")
            if "skin" in node and isinstance(skins, list):
                check(node["skin"], len(skins), f"nodes[{node_index}].skin")
            children = node.get("children", [])
            if isinstance(children, list):
                for child_pos, child in enumerate(children):
                    check(child, len(nodes), f"nodes[{node_index}].children[{child_pos}]")

    if isinstance(meshes, list):
        for mesh_index, mesh in enumerate(meshes):
            if not isinstance(mesh, dict):
                continue
            primitives = mesh.get("primitives", [])
            if not isinstance(primitives, list):
                continue
            for primitive_index, primitive in enumerate(primitives):
                if not isinstance(primitive, dict):
                    continue
                attributes = primitive.get("attributes", {})
                if isinstance(attributes, dict) and isinstance(accessors, list):
                    for semantic, accessor_index in attributes.items():
                        check(
                            accessor_index,
                            len(accessors),
                            f"meshes[{mesh_index}].primitives[{primitive_index}].attributes.{semantic}",
                        )
                if "indices" in primitive and isinstance(accessors, list):
                    check(
                        primitive["indices"],
                        len(accessors),
                        f"meshes[{mesh_index}].primitives[{primitive_index}].indices",
                    )
                if "material" in primitive and isinstance(materials, list):
                    check(
                        primitive["material"],
                        len(materials),
                        f"meshes[{mesh_index}].primitives[{primitive_index}].material",
                    )

    if isinstance(accessors, list) and isinstance(buffer_views, list):
        for accessor_index, accessor in enumerate(accessors):
            if isinstance(accessor, dict) and "bufferView" in accessor:
                check(
                    accessor["bufferView"],
                    len(buffer_views),
                    f"accessors[{accessor_index}].bufferView",
                )

    if isinstance(buffer_views, list) and isinstance(buffers, list):
        for view_index, view in enumerate(buffer_views):
            if isinstance(view, dict) and "buffer" in view:
                check(
                    view["buffer"],
                    len(buffers),
                    f"bufferViews[{view_index}].buffer",
                )

    if isinstance(textures, list):
        for texture_index, texture in enumerate(textures):
            if not isinstance(texture, dict):
                continue
            if "source" in texture and isinstance(images, list):
                check(texture["source"], len(images), f"textures[{texture_index}].source")
            if "sampler" in texture and isinstance(samplers, list):
                check(texture["sampler"], len(samplers), f"textures[{texture_index}].sampler")

    if isinstance(skins, list) and isinstance(nodes, list):
        for skin_index, skin in enumerate(skins):
            if not isinstance(skin, dict):
                continue
            joints = skin.get("joints", [])
            if isinstance(joints, list):
                for joint_pos, joint in enumerate(joints):
                    check(joint, len(nodes), f"skins[{skin_index}].joints[{joint_pos}]")
            if "skeleton" in skin:
                check(skin["skeleton"], len(nodes), f"skins[{skin_index}].skeleton")

    return errors


def inspect_gltf(path: Path) -> tuple[dict, list[str], list[str]]:
    try:
        data, container = load_gltf_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {}, [str(exc)], []

    errors: list[str] = []
    warnings: list[str] = []

    asset = data.get("asset")
    if not isinstance(asset, dict):
        errors.append("asset object is required")
        version = None
    else:
        version = asset.get("version")
        if version != "2.0":
            errors.append("asset.version must be 2.0")

    scenes = data.get("scenes", [])
    nodes = data.get("nodes", [])
    meshes = data.get("meshes", [])
    materials = data.get("materials", [])
    textures = data.get("textures", [])
    images = data.get("images", [])
    skins = data.get("skins", [])
    animations = data.get("animations", [])
    accessors = data.get("accessors", [])
    buffer_views = data.get("bufferViews", [])
    buffers = data.get("buffers", [])

    for label, value in (
        ("scenes", scenes),
        ("nodes", nodes),
        ("meshes", meshes),
        ("materials", materials),
        ("textures", textures),
        ("images", images),
        ("skins", skins),
        ("animations", animations),
        ("accessors", accessors),
        ("bufferViews", buffer_views),
        ("buffers", buffers),
    ):
        if value is not None and not isinstance(value, list):
            errors.append(f"{label} must be an array")

    if isinstance(meshes, list) and not meshes:
        warnings.append("asset contains no meshes")

    primitive_count, indexed_primitive_count = _count_primitives(data)
    errors.extend(_validate_index_references(data))

    extensions_used = data.get("extensionsUsed", [])
    extensions_required = data.get("extensionsRequired", [])
    if extensions_used is not None and not isinstance(extensions_used, list):
        errors.append("extensionsUsed must be an array")
    if extensions_required is not None and not isinstance(extensions_required, list):
        errors.append("extensionsRequired must be an array")

    if isinstance(extensions_required, list):
        unknown_required = [
            item for item in extensions_required
            if not isinstance(item, str)
        ]
        if unknown_required:
            errors.append("extensionsRequired entries must be strings")

    info = {
        **container,
        "version": version,
        "scenes": len(scenes) if isinstance(scenes, list) else None,
        "nodes": len(nodes) if isinstance(nodes, list) else None,
        "meshes": len(meshes) if isinstance(meshes, list) else None,
        "primitives": primitive_count,
        "indexedPrimitives": indexed_primitive_count,
        "materials": len(materials) if isinstance(materials, list) else None,
        "textures": len(textures) if isinstance(textures, list) else None,
        "images": len(images) if isinstance(images, list) else None,
        "skins": len(skins) if isinstance(skins, list) else None,
        "animations": len(animations) if isinstance(animations, list) else None,
        "accessors": len(accessors) if isinstance(accessors, list) else None,
        "bufferViews": len(buffer_views) if isinstance(buffer_views, list) else None,
        "buffers": len(buffers) if isinstance(buffers, list) else None,
        "extensionsUsed": extensions_used if isinstance(extensions_used, list) else None,
        "extensionsRequired": extensions_required if isinstance(extensions_required, list) else None,
    }
    return info, errors, warnings


PROFILES = {
    "prop": {
        "maxMeshes": 8,
        "maxPrimitives": 16,
        "maxMaterials": 8,
        "allowAnimations": False,
        "requireSkin": False,
    },
    "environment": {
        "maxMeshes": 256,
        "maxPrimitives": 1024,
        "maxMaterials": 128,
        "allowAnimations": False,
        "requireSkin": False,
    },
    "character": {
        "maxMeshes": 16,
        "maxPrimitives": 64,
        "maxMaterials": 16,
        "allowAnimations": True,
        "requireSkin": True,
    },
}


def validate_gltf_profile(path: Path, profile: str) -> tuple[dict, list[str], list[str]]:
    if profile not in PROFILES:
        raise ValueError(f"unknown 3D profile: {profile}")

    info, errors, warnings = inspect_gltf(path)
    if not info:
        return info, errors, warnings

    rules = PROFILES[profile]

    if info["meshes"] is not None and info["meshes"] > rules["maxMeshes"]:
        warnings.append(
            f"profile {profile}: mesh count {info['meshes']} exceeds recommended {rules['maxMeshes']}"
        )
    if info["primitives"] > rules["maxPrimitives"]:
        warnings.append(
            f"profile {profile}: primitive count {info['primitives']} exceeds recommended {rules['maxPrimitives']}"
        )
    if info["materials"] is not None and info["materials"] > rules["maxMaterials"]:
        warnings.append(
            f"profile {profile}: material count {info['materials']} exceeds recommended {rules['maxMaterials']}"
        )

    if not rules["allowAnimations"] and info["animations"]:
        warnings.append(f"profile {profile}: animations are unusual for this asset type")

    if rules["requireSkin"] and not info["skins"]:
        errors.append(f"profile {profile}: at least one skin is required")

    return info, errors, warnings
