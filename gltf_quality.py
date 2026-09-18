from __future__ import annotations

from pathlib import Path

from gltf_tools import load_gltf_json


QUALITY_PROFILES = {
    "prop": {
        "maxVertices": 100_000,
        "maxTriangles": 100_000,
        "maxTextures": 16,
        "maxMaterials": 8,
        "requireNormals": True,
        "requireUvWhenTextured": True,
        "requireSkinning": False,
    },
    "environment": {
        "maxVertices": 2_000_000,
        "maxTriangles": 2_000_000,
        "maxTextures": 256,
        "maxMaterials": 128,
        "requireNormals": True,
        "requireUvWhenTextured": True,
        "requireSkinning": False,
    },
    "character": {
        "maxVertices": 150_000,
        "maxTriangles": 200_000,
        "maxTextures": 32,
        "maxMaterials": 16,
        "requireNormals": True,
        "requireUvWhenTextured": True,
        "requireSkinning": True,
    },
}


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
        },
    }


def evaluate_quality(report: dict, profile: str) -> dict:
    if profile not in QUALITY_PROFILES:
        raise ValueError(f"unknown 3D quality profile: {profile}")

    rules = QUALITY_PROFILES[profile]
    geometry = report["geometry"]
    attributes = report["attributes"]
    materials = report["materials"]
    textures = report["textures"]

    errors: list[str] = []
    warnings: list[str] = []
    primitive_count = geometry["primitives"]

    if geometry["vertices"] > rules["maxVertices"]:
        warnings.append(
            f"vertices {geometry['vertices']} exceed profile budget {rules['maxVertices']}"
        )
    if geometry["triangles"] > rules["maxTriangles"]:
        warnings.append(
            f"triangles {geometry['triangles']} exceed profile budget {rules['maxTriangles']}"
        )
    if textures["count"] > rules["maxTextures"]:
        warnings.append(
            f"textures {textures['count']} exceed profile budget {rules['maxTextures']}"
        )
    if materials["count"] > rules["maxMaterials"]:
        warnings.append(
            f"materials {materials['count']} exceed profile budget {rules['maxMaterials']}"
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
        and textures["count"] > 0
        and primitive_count
        and attributes["uv0"] != primitive_count
    ):
        errors.append(
            f"TEXCOORD_0 present on {attributes['uv0']}/{primitive_count} textured primitives"
        )

    if rules["requireSkinning"] and primitive_count and attributes["skinned"] == 0:
        errors.append("character profile requires JOINTS_0 and WEIGHTS_0 on skinned geometry")

    if materials["normalTextures"] > 0 and attributes["tangents"] != primitive_count:
        warnings.append(
            "normal maps are present but not every primitive provides TANGENT; target runtime may need tangent generation"
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
