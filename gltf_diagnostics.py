from __future__ import annotations

import math
import struct
from pathlib import Path

from gltf_binary_metrics import load_buffer_payloads
from gltf_tools import load_gltf_json


COMPONENT_INFO = {
    5120: ("b", 1, True),
    5121: ("B", 1, False),
    5122: ("h", 2, True),
    5123: ("H", 2, False),
    5125: ("I", 4, False),
    5126: ("f", 4, None),
}

TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def accessor_layout(accessor: dict) -> dict:
    component_type = accessor.get("componentType")
    accessor_type = accessor.get("type")
    count = accessor.get("count")

    info = COMPONENT_INFO.get(component_type)
    components = TYPE_COMPONENTS.get(accessor_type)
    if info is None or components is None or not isinstance(count, int) or count < 0:
        return {
            "valid": False,
            "componentType": component_type,
            "type": accessor_type,
            "count": count,
        }

    component_bytes = info[1]
    element_bytes = component_bytes * components
    return {
        "valid": True,
        "componentType": component_type,
        "type": accessor_type,
        "count": count,
        "components": components,
        "componentBytes": component_bytes,
        "elementBytes": element_bytes,
        "packedBytes": element_bytes * count,
        "normalized": bool(accessor.get("normalized", False)),
        "sparse": isinstance(accessor.get("sparse"), dict),
    }


def inspect_accessors(path: Path) -> dict:
    data, _ = load_gltf_json(path)
    accessors = data.get("accessors", [])
    buffer_views = data.get("bufferViews", [])
    buffers = data.get("buffers", [])
    if not isinstance(accessors, list):
        accessors = []
    if not isinstance(buffer_views, list):
        buffer_views = []
    if not isinstance(buffers, list):
        buffers = []

    payloads = load_buffer_payloads(path, data)
    items = []
    errors: list[str] = []
    warnings: list[str] = []
    total_packed_bytes = 0

    for index, accessor in enumerate(accessors):
        item = {"index": index}
        if not isinstance(accessor, dict):
            item["valid"] = False
            errors.append(f"accessor {index}: object required")
            items.append(item)
            continue

        layout = accessor_layout(accessor)
        item.update(layout)
        if not layout.get("valid"):
            errors.append(f"accessor {index}: invalid componentType/type/count")
            items.append(item)
            continue

        total_packed_bytes += layout["packedBytes"]
        view_index = accessor.get("bufferView")
        byte_offset = accessor.get("byteOffset", 0)
        item["bufferView"] = view_index
        item["byteOffset"] = byte_offset
        item["dataAvailable"] = False
        item["byteStride"] = None
        item["requiredBytesInView"] = None

        if layout["sparse"]:
            warnings.append(f"accessor {index}: sparse accessors are not fully decoded")

        if view_index is None:
            if not layout["sparse"]:
                warnings.append(f"accessor {index}: no bufferView and not sparse")
            items.append(item)
            continue

        if not isinstance(view_index, int) or view_index < 0 or view_index >= len(buffer_views):
            errors.append(f"accessor {index}: bufferView index out of range")
            items.append(item)
            continue

        view = buffer_views[view_index]
        if not isinstance(view, dict):
            errors.append(f"accessor {index}: bufferView {view_index} is invalid")
            items.append(item)
            continue

        if not isinstance(byte_offset, int) or byte_offset < 0:
            errors.append(f"accessor {index}: byteOffset must be a non-negative integer")
            items.append(item)
            continue

        stride = view.get("byteStride", layout["elementBytes"])
        if not isinstance(stride, int) or stride < layout["elementBytes"]:
            errors.append(
                f"accessor {index}: byteStride {stride!r} is smaller than element size {layout['elementBytes']}"
            )
            items.append(item)
            continue
        if stride % layout["componentBytes"] != 0:
            errors.append(f"accessor {index}: byteStride is not aligned to component size")

        item["byteStride"] = stride
        required = byte_offset
        if layout["count"] > 0:
            required += stride * (layout["count"] - 1) + layout["elementBytes"]
        item["requiredBytesInView"] = required

        view_length = view.get("byteLength")
        if isinstance(view_length, int) and required > view_length:
            errors.append(
                f"accessor {index}: requires {required} bytes but bufferView has {view_length}"
            )

        buffer_index = view.get("buffer")
        if not isinstance(buffer_index, int) or buffer_index < 0 or buffer_index >= len(payloads):
            items.append(item)
            continue
        payload = payloads[buffer_index]
        if payload is None:
            items.append(item)
            continue

        view_offset = view.get("byteOffset", 0)
        if not isinstance(view_offset, int) or view_offset < 0:
            errors.append(f"bufferView {view_index}: invalid byteOffset")
            items.append(item)
            continue

        start = view_offset + byte_offset
        end = start + (stride * (layout["count"] - 1) + layout["elementBytes"] if layout["count"] else 0)
        if end <= len(payload):
            item["dataAvailable"] = True
        else:
            errors.append(f"accessor {index}: resolved payload exceeds buffer length")

        items.append(item)

    return {
        "count": len(accessors),
        "totalPackedBytes": total_packed_bytes,
        "items": items,
        "errors": errors,
        "warnings": warnings,
    }


def _read_scalar_accessor(path: Path, accessor_index: int) -> list[float] | None:
    data, _ = load_gltf_json(path)
    accessors = data.get("accessors", [])
    views = data.get("bufferViews", [])
    if not isinstance(accessors, list) or not isinstance(views, list):
        return None
    if accessor_index < 0 or accessor_index >= len(accessors):
        return None

    accessor = accessors[accessor_index]
    if not isinstance(accessor, dict) or accessor.get("type") != "SCALAR":
        return None
    layout = accessor_layout(accessor)
    if not layout.get("valid") or layout.get("sparse"):
        return None

    view_index = accessor.get("bufferView")
    if not isinstance(view_index, int) or view_index < 0 or view_index >= len(views):
        return None
    view = views[view_index]
    if not isinstance(view, dict):
        return None

    payloads = load_buffer_payloads(path, data)
    buffer_index = view.get("buffer")
    if not isinstance(buffer_index, int) or buffer_index < 0 or buffer_index >= len(payloads):
        return None
    payload = payloads[buffer_index]
    if payload is None:
        return None

    fmt = COMPONENT_INFO[accessor["componentType"]][0]
    stride = view.get("byteStride", layout["elementBytes"])
    if not isinstance(stride, int) or stride < layout["elementBytes"]:
        return None

    view_offset = view.get("byteOffset", 0)
    accessor_offset = accessor.get("byteOffset", 0)
    if (
        not isinstance(view_offset, int)
        or view_offset < 0
        or not isinstance(accessor_offset, int)
        or accessor_offset < 0
    ):
        return None
    start = view_offset + accessor_offset

    values = []
    for i in range(layout["count"]):
        offset = start + i * stride
        end = offset + layout["componentBytes"]
        if end > len(payload):
            return None
        value = struct.unpack_from("<" + fmt, payload, offset)[0]
        values.append(float(value))
    return values


def inspect_skinning_consistency(path: Path) -> dict:
    data, _ = load_gltf_json(path)
    accessors = data.get("accessors", [])
    meshes = data.get("meshes", [])
    if not isinstance(accessors, list):
        accessors = []
    if not isinstance(meshes, list):
        meshes = []

    errors: list[str] = []
    warnings: list[str] = []
    skinned_primitives = 0

    for mesh_index, mesh in enumerate(meshes):
        if not isinstance(mesh, dict):
            continue
        primitives = mesh.get("primitives", [])
        if not isinstance(primitives, list):
            continue
        for primitive_index, primitive in enumerate(primitives):
            if not isinstance(primitive, dict):
                continue
            attrs = primitive.get("attributes", {})
            if not isinstance(attrs, dict):
                continue
            joints_index = attrs.get("JOINTS_0")
            weights_index = attrs.get("WEIGHTS_0")
            if joints_index is None and weights_index is None:
                continue
            skinned_primitives += 1
            label = f"mesh {mesh_index} primitive {primitive_index}"

            if not isinstance(joints_index, int) or not isinstance(weights_index, int):
                errors.append(f"{label}: JOINTS_0 and WEIGHTS_0 must both be present")
                continue
            if not (0 <= joints_index < len(accessors)) or not (0 <= weights_index < len(accessors)):
                errors.append(f"{label}: skin accessor index out of range")
                continue

            joints = accessors[joints_index]
            weights = accessors[weights_index]
            if not isinstance(joints, dict) or not isinstance(weights, dict):
                errors.append(f"{label}: skin accessors must be objects")
                continue

            if joints.get("type") != "VEC4":
                errors.append(f"{label}: JOINTS_0 must use VEC4")
            if weights.get("type") != "VEC4":
                errors.append(f"{label}: WEIGHTS_0 must use VEC4")
            if joints.get("componentType") not in {5121, 5123}:
                errors.append(f"{label}: JOINTS_0 must use UNSIGNED_BYTE or UNSIGNED_SHORT")
            if weights.get("componentType") not in {5126, 5121, 5123}:
                errors.append(f"{label}: WEIGHTS_0 uses unsupported component type")
            if weights.get("componentType") in {5121, 5123} and weights.get("normalized") is not True:
                errors.append(f"{label}: integer WEIGHTS_0 must be normalized")

            joints_count = joints.get("count")
            weights_count = weights.get("count")
            if joints_count != weights_count:
                errors.append(f"{label}: JOINTS_0 and WEIGHTS_0 counts differ")

            position_index = attrs.get("POSITION")
            if isinstance(position_index, int) and 0 <= position_index < len(accessors):
                position = accessors[position_index]
                if isinstance(position, dict) and position.get("count") != joints_count:
                    errors.append(f"{label}: skin attribute count differs from POSITION count")

    return {
        "skinnedPrimitives": skinned_primitives,
        "errors": errors,
        "warnings": warnings,
    }


def inspect_animation_consistency(path: Path) -> dict:
    data, _ = load_gltf_json(path)
    animations = data.get("animations", [])
    accessors = data.get("accessors", [])
    nodes = data.get("nodes", [])
    if not isinstance(animations, list):
        animations = []
    if not isinstance(accessors, list):
        accessors = []
    if not isinstance(nodes, list):
        nodes = []

    errors: list[str] = []
    warnings: list[str] = []
    items = []

    for animation_index, animation in enumerate(animations):
        if not isinstance(animation, dict):
            errors.append(f"animation {animation_index}: object required")
            continue

        samplers = animation.get("samplers", [])
        channels = animation.get("channels", [])
        if not isinstance(samplers, list):
            errors.append(f"animation {animation_index}: samplers must be an array")
            samplers = []
        if not isinstance(channels, list):
            errors.append(f"animation {animation_index}: channels must be an array")
            channels = []

        animation_start = None
        animation_end = None
        used_samplers = set()

        for sampler_index, sampler in enumerate(samplers):
            if not isinstance(sampler, dict):
                errors.append(f"animation {animation_index} sampler {sampler_index}: object required")
                continue
            input_index = sampler.get("input")
            output_index = sampler.get("output")
            interpolation = sampler.get("interpolation", "LINEAR")

            if interpolation not in {"LINEAR", "STEP", "CUBICSPLINE"}:
                errors.append(
                    f"animation {animation_index} sampler {sampler_index}: invalid interpolation {interpolation!r}"
                )

            if not isinstance(input_index, int) or not (0 <= input_index < len(accessors)):
                errors.append(f"animation {animation_index} sampler {sampler_index}: invalid input accessor")
                continue
            input_accessor = accessors[input_index]
            if not isinstance(input_accessor, dict):
                errors.append(f"animation {animation_index} sampler {sampler_index}: invalid input accessor")
                continue
            if input_accessor.get("type") != "SCALAR" or input_accessor.get("componentType") != 5126:
                errors.append(
                    f"animation {animation_index} sampler {sampler_index}: input accessor must be FLOAT SCALAR"
                )

            if not isinstance(output_index, int) or not (0 <= output_index < len(accessors)):
                errors.append(f"animation {animation_index} sampler {sampler_index}: invalid output accessor")
                continue

            input_count = input_accessor.get("count")
            output_accessor = accessors[output_index]
            output_count = output_accessor.get("count") if isinstance(output_accessor, dict) else None
            expected_multiplier = 3 if interpolation == "CUBICSPLINE" else 1
            if (
                isinstance(input_count, int)
                and isinstance(output_count, int)
                and output_count != input_count * expected_multiplier
            ):
                errors.append(
                    f"animation {animation_index} sampler {sampler_index}: output count {output_count} "
                    f"does not match expected {input_count * expected_multiplier}"
                )

            values = _read_scalar_accessor(path, input_index)
            if values:
                if any(not math.isfinite(value) for value in values):
                    errors.append(f"animation {animation_index} sampler {sampler_index}: non-finite key time")
                if any(values[i] >= values[i + 1] for i in range(len(values) - 1)):
                    errors.append(
                        f"animation {animation_index} sampler {sampler_index}: key times must be strictly increasing"
                    )
                start = values[0]
                end = values[-1]
                animation_start = start if animation_start is None else min(animation_start, start)
                animation_end = end if animation_end is None else max(animation_end, end)

        for channel_index, channel in enumerate(channels):
            if not isinstance(channel, dict):
                errors.append(f"animation {animation_index} channel {channel_index}: object required")
                continue
            sampler_index = channel.get("sampler")
            if not isinstance(sampler_index, int) or not (0 <= sampler_index < len(samplers)):
                errors.append(f"animation {animation_index} channel {channel_index}: sampler index out of range")
            else:
                used_samplers.add(sampler_index)

            target = channel.get("target")
            if not isinstance(target, dict):
                errors.append(f"animation {animation_index} channel {channel_index}: target required")
                continue
            node = target.get("node")
            target_path = target.get("path")
            if not isinstance(node, int) or not (0 <= node < len(nodes)):
                errors.append(f"animation {animation_index} channel {channel_index}: target node out of range")
            if target_path not in {"translation", "rotation", "scale", "weights"}:
                errors.append(
                    f"animation {animation_index} channel {channel_index}: invalid target path {target_path!r}"
                )

        unused = sorted(set(range(len(samplers))) - used_samplers)
        if unused:
            warnings.append(f"animation {animation_index}: unused samplers {unused}")

        duration = None
        if animation_start is not None and animation_end is not None:
            duration = max(0.0, animation_end - animation_start)

        items.append(
            {
                "index": animation_index,
                "name": animation.get("name"),
                "samplers": len(samplers),
                "channels": len(channels),
                "startSeconds": animation_start,
                "endSeconds": animation_end,
                "durationSeconds": duration,
            }
        )

    durations = [item["durationSeconds"] for item in items if item["durationSeconds"] is not None]
    return {
        "animations": len(animations),
        "items": items,
        "maxDurationSeconds": max(durations, default=0.0),
        "errors": errors,
        "warnings": warnings,
    }


def deep_gltf_diagnostics(path: Path) -> dict:
    return {
        "accessors": inspect_accessors(path),
        "skinning": inspect_skinning_consistency(path),
        "animations": inspect_animation_consistency(path),
    }
