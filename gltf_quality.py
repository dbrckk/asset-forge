from __future__ import annotations

from pathlib import Path

from asset_profile_validation import load_3d_profile
from gltf_binary_metrics import inspect_images, inspect_rig_and_animation
from gltf_diagnostics import deep_gltf_diagnostics
from gltf_tools import load_gltf_json


def _accessor_count(accessors: list, index) -> int | None:
    if not isinstance(index, int) or index < 0 or index >= len(accessors):
        return None
    accessor = accessors[index]
    if not isinstance(accessor, dict):
        return None
    count = accessor.get("count")
    if not isinstance(count, int) or count < 0:
        return None
    return count


def _triangle_count(mode: int, element_count: int) -> int:
    if mode == 4:  # TRIANGLES
        return element_count // 3
    if mode in {5, 6}:  # TRIANGLE_STRIP / TRIANGLE_FAN
        return max(0, element_count - 2)
    return 0


def build_quality_report(path: Path) -> dict:
    data, container = load_gltf_json(path)
    accessors = data.get("accessors", [])
    meshes = data.get("meshes", [])
    materials = data.get("materials", [])
    textures = data.get("textures", [])
    images = data.get("images", [])

    if not isinstance(accessors, list):
        accessors = []
    if not isinstance(meshes, list):
        meshes = []
    if not isinstance(materials, list):
        materials = []
    if not isinstance(textures, list):
        textures = []
    if not isinstance(images, list):
        images = []

    material_usage = []
    for material in materials:
        if not isinstance(material, dict):
            material_usage.append({"textured": False, "normalMapped": False})
            continue
        pbr = material.get("pbrMetallicRoughness")
        textured = False
        if isinstance(pbr, dict):
            textured = any(
                isinstance(pbr.get(key), dict)
                for key in ("baseColorTexture", "metallicRoughnessTexture")
            )
        normal_mapped = isinstance(material.get("normalTexture"), dict)
        textured = textured or normal_mapped or isinstance(material.get("occlusionTexture"), dict) or isinstance(material.get("emissiveTexture"), dict)
        material_usage.append({"textured": textured, "normalMapped": normal_mapped})

    primitives = 0
    vertices = 0
    triangles = 0
    primitive_vertices_known = 0
    primitive_triangles_known = 0
    normals = 0
    tangents = 0
    uv0 = 0
    uv1 = 0
    colors = 0
    skinned = 0
    material_bound = 0
    textured_primitives = 0
    textured_primitives_with_uv0 = 0
    normal_mapped_primitives = 0
    normal_mapped_primitives_with_tangent = 0
    non_triangle_primitives = 0

    for mesh in meshes:
        if not isinstance(mesh, dict):
            continue
        mesh_primitives = mesh.get("primitives", [])
        if not isinstance(mesh_primitives, list):
            continue

        for primitive in mesh_primitives:
            if not isinstance(primitive, dict):
                continue
            primitives += 1
            attributes = primitive.get("attributes", {})
            if not isinstance(attributes, dict):
                attributes = {}

            position_count = _accessor_count(accessors, attributes.get("POSITION"))
            if position_count is not None:
                vertices += position_count
                primitive_vertices_known += 1

            mode = primitive.get("mode", 4)
            if not isinstance(mode, int):
                mode = 4

            element_count = None
            if "indices" in primitive:
                element_count = _accessor_count(accessors, primitive.get("indices"))
            if element_count is None:
                element_count = position_count

            if element_count is not None:
                triangles += _triangle_count(mode, element_count)
                primitive_triangles_known += 1
            if mode not in {4, 5, 6}:
                non_triangle_primitives += 1

            if "NORMAL" in attributes:
                normals += 1
            if "TANGENT" in attributes:
                tangents += 1
            if "TEXCOORD_0" in attributes:
                uv0 += 1
            if "TEXCOORD_1" in attributes:
                uv1 += 1
            if "COLOR_0" in attributes:
                colors += 1
            if "JOINTS_0" in attributes and "WEIGHTS_0" in attributes:
                skinned += 1
            if "material" in primitive:
                material_bound += 1
                material_index = primitive.get("material")
                if (
                    isinstance(material_index, int)
                    and 0 <= material_index < len(material_usage)
                ):
                    usage = material_usage[material_index]
                    if usage["textured"]:
                        textured_primitives += 1
                        if "TEXCOORD_0" in attributes:
                            textured_primitives_with_uv0 += 1
                    if usage["normalMapped"]:
                        normal_mapped_primitives += 1
                        if "TANGENT" in attributes:
                            normal_mapped_primitives_with_tangent += 1

    pbr_materials = 0
    base_color_textures = 0
    metallic_roughness_textures = 0
    normal_textures = 0
    occlusion_textures = 0
    emissive_textures = 0

    for material in materials:
        if not isinstance(material, dict):
            continue
        pbr = material.get("pbrMetallicRoughness")
        if isinstance(pbr, dict):
            pbr_materials += 1
            if isinstance(pbr.get("baseColorTexture"), dict):
                base_color_textures += 1
            if isinstance(pbr.get("metallicRoughnessTexture"), dict):
                metallic_roughness_textures += 1
        if isinstance(material.get("normalTexture"), dict):
            normal_textures += 1
        if isinstance(material.get("occlusionTexture"), dict):
            occlusion_textures += 1
        if isinstance(material.get("emissiveTexture"), dict):
            emissive_textures += 1

    external_images = 0
    embedded_images = 0
    data_uri_images = 0
    for image in images:
        if not isinstance(image, dict):
            continue
        if "bufferView" in image:
            embedded_images += 1
        uri = image.get("uri")
        if isinstance(uri, str):
            if uri.startswith("data:"):
                data_uri_images += 1
            else:
                external_images += 1

    image_metrics = inspect_images(path)
    rig_animation = inspect_rig_and_animation(path)
    diagnostics = deep_gltf_diagnostics(path)
    known_image_dimensions = [item for item in image_metrics if item.get("width") and item.get("height")]
    estimated_texture_bytes = sum(
        int(item.get("estimatedRgba8Bytes") or 0)
        for item in known_image_dimensions
    )
    estimated_texture_mip_bytes = sum(
        int(item.get("estimatedRgba8MipBytes") or 0)
        for item in known_image_dimensions
    )
    max_texture_width = max((int(item["width"]) for item in known_image_dimensions), default=0)
    max_texture_height = max((int(item["height"]) for item in known_image_dimensions), default=0)

    return {
        "file": str(path),
        "container": container,
        "geometry": {
            "meshes": len(meshes),
            "primitives": primitives,
            "vertices": vertices,
            "triangles": triangles,
            "primitiveVerticesKnown": primitive_vertices_known,
            "primitiveTrianglesKnown": primitive_triangles_known,
            "nonTrianglePrimitives": non_triangle_primitives,
        },
        "attributes": {
            "normals": normals,
            "tangents": tangents,
            "uv0": uv0,
            "uv1": uv1,
            "colors": colors,
            "skinned": skinned,
            "materialBound": material_bound,
            "texturedPrimitives": textured_primitives,
            "texturedPrimitivesWithUv0": textured_primitives_with_uv0,
            "normalMappedPrimitives": normal_mapped_primitives,
            "normalMappedPrimitivesWithTangent": normal_mapped_primitives_with_tangent,
        },
        "materials": {
            "count": len(materials),
            "pbrMetallicRoughness": pbr_materials,
            "baseColorTextures": base_color_textures,
            "metallicRoughnessTextures": metallic_roughness_textures,
            "normalTextures": normal_textures,
            "occlusionTextures": occlusion_textures,
            "emissiveTextures": emissive_textures,
        },
        "textures": {
            "count": len(textures),
            "images": len(images),
            "embeddedImages": embedded_images,
            "dataUriImages": data_uri_images,
            "externalImages": external_images,
            "knownDimensions": len(known_image_dimensions),
            "maxWidth": max_texture_width,
            "maxHeight": max_texture_height,
            "estimatedRgba8Bytes": estimated_texture_bytes,
            "estimatedRgba8MipBytes": estimated_texture_mip_bytes,
            "items": image_metrics,
        },
        "rigAnimation": rig_animation,
        "diagnostics": diagnostics,
    }


def evaluate_quality(report: dict, profile: str) -> dict:
    profile_data = load_3d_profile(profile)
    rules = profile_data["rules"]
    geometry = report["geometry"]
    attributes = report["attributes"]
    materials = report["materials"]
    textures = report["textures"]

    errors: list[str] = []
    warnings: list[str] = []
    primitive_count = geometry["primitives"]

    budget_messages = []
    for label, actual, maximum in (
        ("meshes", geometry["meshes"], rules["maxMeshes"]),
        ("primitives", geometry["primitives"], rules["maxPrimitives"]),
        ("vertices", geometry["vertices"], rules["maxVertices"]),
        ("triangles", geometry["triangles"], rules["maxTriangles"]),
        ("materials", materials["count"], rules["maxMaterials"]),
        ("textures", textures["count"], rules["maxTextures"]),
    ):
        if actual > maximum:
            budget_messages.append(
                f"{label} {actual} exceed profile budget {maximum}"
            )
    if rules["strictBudgets"]:
        errors.extend(budget_messages)
    else:
        warnings.extend(budget_messages)
    if max(textures.get("maxWidth", 0), textures.get("maxHeight", 0)) > rules["maxTextureDimension"]:
        warnings.append(
            "texture dimension "
            f"{max(textures.get('maxWidth', 0), textures.get('maxHeight', 0))} "
            f"exceeds profile budget {rules['maxTextureDimension']}"
        )
    if textures.get("estimatedRgba8MipBytes", 0) > rules["maxEstimatedTextureMipBytes"]:
        warnings.append(
            "estimated RGBA8+mip texture memory "
            f"{textures['estimatedRgba8MipBytes']} exceeds profile budget "
            f"{rules['maxEstimatedTextureMipBytes']}"
        )
    if geometry["primitiveVerticesKnown"] != primitive_count:
        warnings.append("vertex count is incomplete because some POSITION accessor counts are unavailable")
    if geometry["primitiveTrianglesKnown"] != primitive_count:
        warnings.append("triangle count is incomplete for some primitives")

    if rules["requireNormals"] and primitive_count and attributes["normals"] != primitive_count:
        errors.append(
            f"normals present on {attributes['normals']}/{primitive_count} primitives"
        )

    if (
        rules["requireUvWhenTextured"]
        and attributes["texturedPrimitives"] > 0
        and attributes["texturedPrimitivesWithUv0"] != attributes["texturedPrimitives"]
    ):
        errors.append(
            "TEXCOORD_0 present on "
            f"{attributes['texturedPrimitivesWithUv0']}/{attributes['texturedPrimitives']} "
            "textured primitives"
        )

    if rules["requireSkin"] and primitive_count and attributes["skinned"] == 0:
        errors.append("character profile requires JOINTS_0 and WEIGHTS_0 on skinned geometry")

    if (
        rules["requirePbrMaterials"]
        and materials["count"] > 0
        and materials["pbrMetallicRoughness"] != materials["count"]
    ):
        errors.append(
            "all runtime materials must declare glTF metallic-roughness PBR"
        )

    rig = report.get("rigAnimation", {})
    diagnostics = report.get("diagnostics", {})
    accessor_diag = diagnostics.get("accessors", {})
    skin_diag = diagnostics.get("skinning", {})
    animation_diag = diagnostics.get("animations", {})
    if not rules["allowAnimations"] and rig.get("animations", 0):
        errors.append(
            f"profile forbids animations but asset contains {rig['animations']} animation(s)"
        )
    if rules["maxJointsPerSkin"] and rig.get("maxJointsPerSkin", 0) > rules["maxJointsPerSkin"]:
        warnings.append(
            f"max joints per skin {rig['maxJointsPerSkin']} exceed profile budget "
            f"{rules['maxJointsPerSkin']}"
        )
    if profile == "character" and rig.get("skins", 0) and rig.get("skinsWithInverseBindMatrices", 0) == 0:
        warnings.append("character skin has no inverseBindMatrices accessor")
    if rig.get("invalidAnimationTargets", 0):
        errors.append(
            f"{rig['invalidAnimationTargets']} animation target field(s) are invalid"
        )

    errors.extend(accessor_diag.get("errors", []))
    warnings.extend(accessor_diag.get("warnings", []))
    errors.extend(skin_diag.get("errors", []))
    warnings.extend(skin_diag.get("warnings", []))
    errors.extend(animation_diag.get("errors", []))
    warnings.extend(animation_diag.get("warnings", []))

    if (
        attributes["normalMappedPrimitives"] > 0
        and attributes["normalMappedPrimitivesWithTangent"]
        != attributes["normalMappedPrimitives"]
    ):
        warnings.append(
            "normal-mapped primitives are missing TANGENT data; target runtime may need tangent generation"
        )

    if textures["externalImages"] > 0:
        warnings.append(
            f"{textures['externalImages']} external image(s) reduce GLB-style portability"
        )

    return {
        "profile": profile,
        "rules": rules,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def quality_report(path: Path, profile: str | None = None) -> dict:
    report = build_quality_report(path)
    if profile:
        report["evaluation"] = evaluate_quality(report, profile)
    return report
