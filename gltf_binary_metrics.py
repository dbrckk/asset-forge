from __future__ import annotations

import base64
import struct
from pathlib import Path
from urllib.parse import unquote

from gltf_tools import GLB_BIN_CHUNK, GLB_JSON_CHUNK, GLB_MAGIC, load_gltf_json
from raster_pack import inspect_webp_bytes


def _decode_data_uri(uri: str) -> bytes:
    if not uri.startswith("data:") or "," not in uri:
        raise ValueError("invalid data URI")
    header, payload = uri.split(",", 1)
    if ";base64" in header:
        try:
            return base64.b64decode(payload, validate=True)
        except ValueError as exc:
            raise ValueError("invalid base64 data URI") from exc
    return unquote(payload).encode("latin1")


def _safe_local_path(model_path: Path, uri: str) -> Path:
    if "://" in uri:
        raise ValueError("remote URI is not read by binary metrics")
    base = model_path.resolve().parent
    candidate = (base / unquote(uri)).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError("external URI escapes model directory") from exc
    return candidate


def _glb_bin_chunk(path: Path) -> bytes | None:
    raw = path.read_bytes()
    if len(raw) < 12:
        return None
    magic, version, total_length = struct.unpack("<III", raw[:12])
    if magic != GLB_MAGIC or version != 2 or total_length != len(raw):
        return None

    offset = 12
    while offset + 8 <= len(raw):
        chunk_length, chunk_type = struct.unpack("<II", raw[offset : offset + 8])
        offset += 8
        end = offset + chunk_length
        if end > len(raw):
            return None
        payload = raw[offset:end]
        offset = end
        if chunk_type == GLB_BIN_CHUNK:
            return payload
    return None


def load_buffer_payloads(path: Path, data: dict) -> list[bytes | None]:
    buffers = data.get("buffers", [])
    if not isinstance(buffers, list):
        return []

    glb_bin = _glb_bin_chunk(path) if path.suffix.lower() == ".glb" else None
    payloads: list[bytes | None] = []

    for index, buffer in enumerate(buffers):
        if not isinstance(buffer, dict):
            payloads.append(None)
            continue

        uri = buffer.get("uri")
        try:
            if isinstance(uri, str):
                if uri.startswith("data:"):
                    payload = _decode_data_uri(uri)
                else:
                    payload = _safe_local_path(path, uri).read_bytes()
            elif index == 0 and glb_bin is not None:
                payload = glb_bin
            else:
                payload = None
        except (OSError, ValueError):
            payload = None

        payloads.append(payload)

    return payloads


def buffer_view_bytes(
    data: dict,
    payloads: list[bytes | None],
    view_index: int,
) -> bytes | None:
    views = data.get("bufferViews", [])
    if not isinstance(views, list) or view_index < 0 or view_index >= len(views):
        return None
    view = views[view_index]
    if not isinstance(view, dict):
        return None

    buffer_index = view.get("buffer")
    if not isinstance(buffer_index, int) or buffer_index < 0 or buffer_index >= len(payloads):
        return None
    payload = payloads[buffer_index]
    if payload is None:
        return None

    offset = view.get("byteOffset", 0)
    length = view.get("byteLength")
    if not isinstance(offset, int) or offset < 0:
        return None
    if not isinstance(length, int) or length < 0:
        return None
    end = offset + length
    if end > len(payload):
        return None
    return payload[offset:end]


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        width, height = struct.unpack(">II", data[16:24])
        return (width, height) if width > 0 and height > 0 else None
    return None


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(data):
            return None
        length = struct.unpack(">H", data[offset : offset + 2])[0]
        if length < 2 or offset + length > len(data):
            return None
        if marker in {
            0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
        } and length >= 7:
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            return (width, height) if width > 0 and height > 0 else None
        offset += length
    return None


def _webp_dimensions(data: bytes) -> tuple[int, int] | None:
    try:
        info = inspect_webp_bytes(data)
    except ValueError:
        return None
    return info["width"], info["height"]


def image_dimensions(data: bytes) -> tuple[int, int, str] | None:
    for fmt, parser in (
        ("png", _png_dimensions),
        ("jpeg", _jpeg_dimensions),
        ("webp", _webp_dimensions),
    ):
        dimensions = parser(data)
        if dimensions:
            return dimensions[0], dimensions[1], fmt
    return None


def inspect_images(path: Path) -> list[dict]:
    data, _ = load_gltf_json(path)
    images = data.get("images", [])
    if not isinstance(images, list):
        return []

    payloads = load_buffer_payloads(path, data)
    result = []

    for index, image in enumerate(images):
        item = {
            "index": index,
            "name": None,
            "source": "unknown",
            "available": False,
            "bytes": None,
            "width": None,
            "height": None,
            "format": None,
            "estimatedRgba8Bytes": None,
            "estimatedRgba8MipBytes": None,
        }
        if not isinstance(image, dict):
            result.append(item)
            continue

        item["name"] = image.get("name")
        payload = None
        uri = image.get("uri")
        if isinstance(uri, str):
            if uri.startswith("data:"):
                item["source"] = "data-uri"
                try:
                    payload = _decode_data_uri(uri)
                except ValueError:
                    payload = None
            elif "://" in uri:
                item["source"] = "remote"
            else:
                item["source"] = "external-local"
                try:
                    payload = _safe_local_path(path, uri).read_bytes()
                except (OSError, ValueError):
                    payload = None
        elif isinstance(image.get("bufferView"), int):
            item["source"] = "buffer-view"
            payload = buffer_view_bytes(data, payloads, image["bufferView"])

        if payload is not None:
            item["available"] = True
            item["bytes"] = len(payload)
            dimensions = image_dimensions(payload)
            if dimensions:
                width, height, image_format = dimensions
                item["width"] = width
                item["height"] = height
                item["format"] = image_format
                rgba = width * height * 4
                item["estimatedRgba8Bytes"] = rgba
                item["estimatedRgba8MipBytes"] = (rgba * 4 + 2) // 3

        result.append(item)

    return result


def inspect_rig_and_animation(path: Path) -> dict:
    data, _ = load_gltf_json(path)
    skins = data.get("skins", [])
    animations = data.get("animations", [])
    accessors = data.get("accessors", [])

    if not isinstance(skins, list):
        skins = []
    if not isinstance(animations, list):
        animations = []
    if not isinstance(accessors, list):
        accessors = []

    joint_counts = []
    inverse_bind_matrices = 0
    for skin in skins:
        if not isinstance(skin, dict):
            continue
        joints = skin.get("joints", [])
        joint_counts.append(len(joints) if isinstance(joints, list) else 0)
        if isinstance(skin.get("inverseBindMatrices"), int):
            inverse_bind_matrices += 1

    channels = 0
    samplers = 0
    target_paths: dict[str, int] = {}
    animated_nodes: set[int] = set()
    keyframe_counts = []
    invalid_targets = 0

    for animation in animations:
        if not isinstance(animation, dict):
            continue
        animation_samplers = animation.get("samplers", [])
        animation_channels = animation.get("channels", [])
        if isinstance(animation_samplers, list):
            samplers += len(animation_samplers)
            for sampler in animation_samplers:
                if not isinstance(sampler, dict):
                    continue
                input_index = sampler.get("input")
                if isinstance(input_index, int) and 0 <= input_index < len(accessors):
                    accessor = accessors[input_index]
                    if isinstance(accessor, dict) and isinstance(accessor.get("count"), int):
                        keyframe_counts.append(accessor["count"])
        if isinstance(animation_channels, list):
            channels += len(animation_channels)
            for channel in animation_channels:
                if not isinstance(channel, dict):
                    continue
                target = channel.get("target")
                if not isinstance(target, dict):
                    invalid_targets += 1
                    continue
                node = target.get("node")
                path_name = target.get("path")
                if isinstance(node, int):
                    animated_nodes.add(node)
                else:
                    invalid_targets += 1
                if isinstance(path_name, str):
                    target_paths[path_name] = target_paths.get(path_name, 0) + 1
                else:
                    invalid_targets += 1

    return {
        "skins": len(skins),
        "jointsPerSkin": joint_counts,
        "maxJointsPerSkin": max(joint_counts, default=0),
        "skinsWithInverseBindMatrices": inverse_bind_matrices,
        "animations": len(animations),
        "animationChannels": channels,
        "animationSamplers": samplers,
        "animatedNodes": len(animated_nodes),
        "targetPaths": target_paths,
        "keyframeAccessorCounts": keyframe_counts,
        "maxKeyframesPerSampler": max(keyframe_counts, default=0),
        "invalidAnimationTargets": invalid_targets,
    }
