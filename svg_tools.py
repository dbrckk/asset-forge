from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from asset_profile_validation import load_vector_profile
from pathlib import Path
from urllib.parse import urlparse

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
DANGEROUS_TAGS = {"script", "foreignObject"}
METADATA_TAGS = {"metadata"}
EVENT_ATTRIBUTE = re.compile(r"^on[a-z]+$", re.IGNORECASE)
LENGTH = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)(px)?\s*$", re.IGNORECASE)

def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _is_external_reference(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith("#") or value.startswith("data:"):
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme or parsed.netloc)


def _parse_length(value: str | None) -> float | None:
    if not value:
        return None
    match = LENGTH.match(value)
    if not match:
        return None
    return float(match.group(1))


def _parse_viewbox(view_box: str | None) -> tuple[float, float, float, float] | None:
    if not view_box:
        return None
    parts = view_box.replace(",", " ").split()
    if len(parts) != 4:
        return None
    try:
        values = tuple(float(item) for item in parts)
    except ValueError:
        return None
    return values  # type: ignore[return-value]


def inspect_svg(path: Path) -> tuple[dict, list[str], list[str]]:
    raw = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    lowered = raw.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        return {}, ["DOCTYPE/ENTITY declarations are not allowed"], warnings

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return {}, [f"invalid XML: {exc}"], warnings

    if _local_name(root.tag) != "svg":
        errors.append("root element must be svg")

    width = root.attrib.get("width")
    height = root.attrib.get("height")
    view_box = root.attrib.get("viewBox")
    view_box_values = _parse_viewbox(view_box)

    if not view_box:
        warnings.append("viewBox is recommended for scalable project assets")
    elif view_box_values is None:
        errors.append("viewBox must contain four numbers")
    elif view_box_values[2] <= 0 or view_box_values[3] <= 0:
        errors.append("viewBox width and height must be > 0")

    for label, value in (("width", width), ("height", height)):
        if value and not LENGTH.match(value):
            warnings.append(f"{label} uses a non-pixel/non-numeric unit: {value}")

    width_value = _parse_length(width)
    height_value = _parse_length(height)
    if (
        width_value is not None
        and height_value is not None
        and view_box_values is not None
        and view_box_values[2] > 0
        and view_box_values[3] > 0
    ):
        pixel_ratio = width_value / height_value if height_value else None
        view_ratio = view_box_values[2] / view_box_values[3] if view_box_values[3] else None
        if pixel_ratio is not None and view_ratio is not None and abs(pixel_ratio - view_ratio) > 1e-6:
            warnings.append("width/height aspect ratio differs from viewBox aspect ratio")

    element_count = 0
    external_refs: list[str] = []
    dangerous_tags: list[str] = []
    event_attributes: list[str] = []
    metadata_elements = 0

    for element in root.iter():
        element_count += 1
        tag = _local_name(element.tag)
        if tag in DANGEROUS_TAGS:
            dangerous_tags.append(tag)
        if tag in METADATA_TAGS:
            metadata_elements += 1

        for key, value in element.attrib.items():
            local_key = _local_name(key)
            if EVENT_ATTRIBUTE.match(local_key):
                event_attributes.append(local_key)
            if local_key in {"href", "src"} and _is_external_reference(value):
                external_refs.append(value)

    if dangerous_tags:
        errors.append("disallowed executable/embedded tags: " + ", ".join(sorted(set(dangerous_tags))))
    if event_attributes:
        errors.append("event-handler attributes are not allowed: " + ", ".join(sorted(set(event_attributes))))
    if external_refs:
        errors.append("external references are not allowed: " + ", ".join(sorted(set(external_refs))))
    if metadata_elements:
        warnings.append(f"{metadata_elements} metadata element(s) can be removed for delivery")

    info = {
        "width": width,
        "height": height,
        "widthPx": width_value,
        "heightPx": height_value,
        "viewBox": view_box,
        "viewBoxValues": list(view_box_values) if view_box_values else None,
        "elements": element_count,
        "metadataElements": metadata_elements,
        "bytes": len(raw.encode("utf-8")),
    }
    return info, errors, warnings


def validate_svg_profile(path: Path, profile: str) -> tuple[dict, list[str], list[str]]:
    profile_data = load_vector_profile(profile)

    info, errors, warnings = inspect_svg(path)
    if not info:
        return info, errors, warnings

    rules = profile_data["rules"]
    view_box_values = info.get("viewBoxValues")

    if rules["requireViewBox"] and not view_box_values:
        errors.append(f"profile {profile}: viewBox is required")

    if rules["requireSquareViewBox"] and view_box_values:
        if abs(view_box_values[2] - view_box_values[3]) > 1e-6:
            errors.append(f"profile {profile}: square viewBox required")

    if info["elements"] > rules["maxElements"]:
        warnings.append(
            f"profile {profile}: element count {info['elements']} exceeds recommended {rules['maxElements']}"
        )

    return info, errors, warnings


def normalize_viewbox(input_path: Path, output_path: Path) -> dict:
    raw = input_path.read_text(encoding="utf-8")
    lowered = raw.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise ValueError("DOCTYPE/ENTITY declarations are not allowed")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML: {exc}") from exc

    if _local_name(root.tag) != "svg":
        raise ValueError("root element must be svg")

    current = _parse_viewbox(root.attrib.get("viewBox"))
    changed = False

    if current is None:
        width = _parse_length(root.attrib.get("width"))
        height = _parse_length(root.attrib.get("height"))
        if width is None or height is None or width <= 0 or height <= 0:
            raise ValueError("cannot infer viewBox without positive numeric width and height")
        root.set("viewBox", f"0 0 {width:g} {height:g}")
        changed = True

    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )

    info, errors, warnings = inspect_svg(output_path)
    if errors:
        raise ValueError("normalized SVG invalid: " + "; ".join(errors))

    return {
        "input": str(input_path),
        "output": str(output_path),
        "changed": changed,
        "viewBox": info.get("viewBox"),
        "warnings": warnings,
    }


def sanitize_svg(
    input_path: Path,
    output_path: Path,
    *,
    remove_metadata: bool = True,
) -> dict:
    raw = input_path.read_text(encoding="utf-8")
    lowered = raw.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise ValueError("DOCTYPE/ENTITY declarations are not allowed")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML: {exc}") from exc

    removed_elements = 0
    removed_attributes = 0

    def clean(parent: ET.Element) -> None:
        nonlocal removed_elements, removed_attributes
        for child in list(parent):
            local_tag = _local_name(child.tag)
            if local_tag in DANGEROUS_TAGS or (remove_metadata and local_tag in METADATA_TAGS):
                parent.remove(child)
                removed_elements += 1
                continue

            for key in list(child.attrib):
                local_key = _local_name(key)
                value = child.attrib[key]
                if EVENT_ATTRIBUTE.match(local_key):
                    del child.attrib[key]
                    removed_attributes += 1
                elif local_key in {"href", "src"} and _is_external_reference(value):
                    del child.attrib[key]
                    removed_attributes += 1
            clean(child)

    for key in list(root.attrib):
        local_key = _local_name(key)
        value = root.attrib[key]
        if EVENT_ATTRIBUTE.match(local_key):
            del root.attrib[key]
            removed_attributes += 1
        elif local_key in {"href", "src"} and _is_external_reference(value):
            del root.attrib[key]
            removed_attributes += 1

    clean(root)

    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )

    info, errors, warnings = inspect_svg(output_path)
    if errors:
        raise ValueError("sanitized SVG still invalid: " + "; ".join(errors))

    return {
        "input": str(input_path),
        "output": str(output_path),
        "removedElements": removed_elements,
        "removedAttributes": removed_attributes,
        "info": info,
        "warnings": warnings,
    }
