from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
DANGEROUS_TAGS = {"script", "foreignObject"}
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

    if not view_box:
        warnings.append("viewBox is recommended for scalable project assets")
    else:
        parts = view_box.replace(",", " ").split()
        if len(parts) != 4:
            errors.append("viewBox must contain four numbers")
        else:
            try:
                values = [float(item) for item in parts]
                if values[2] <= 0 or values[3] <= 0:
                    errors.append("viewBox width and height must be > 0")
            except ValueError:
                errors.append("viewBox must contain numeric values")

    for label, value in (("width", width), ("height", height)):
        if value and not LENGTH.match(value):
            warnings.append(f"{label} uses a non-pixel/non-numeric unit: {value}")

    element_count = 0
    external_refs: list[str] = []
    dangerous_tags: list[str] = []
    event_attributes: list[str] = []

    for element in root.iter():
        element_count += 1
        tag = _local_name(element.tag)
        if tag in DANGEROUS_TAGS:
            dangerous_tags.append(tag)

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

    info = {
        "width": width,
        "height": height,
        "viewBox": view_box,
        "elements": element_count,
        "bytes": len(raw.encode("utf-8")),
    }
    return info, errors, warnings


def sanitize_svg(input_path: Path, output_path: Path) -> dict:
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
            if _local_name(child.tag) in DANGEROUS_TAGS:
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
