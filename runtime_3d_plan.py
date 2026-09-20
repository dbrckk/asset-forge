from __future__ import annotations


def build_runtime_3d_plan(report: dict, profile: str) -> dict:
    geometry = report.get("geometry") if isinstance(report, dict) else {}
    materials = report.get("materials") if isinstance(report, dict) else {}
    attributes = report.get("attributes") if isinstance(report, dict) else {}
    textures = report.get("textures") if isinstance(report, dict) else {}
    geometry = geometry if isinstance(geometry, dict) else {}
    materials = materials if isinstance(materials, dict) else {}
    attributes = attributes if isinstance(attributes, dict) else {}
    textures = textures if isinstance(textures, dict) else {}

    triangles = max(0, int(geometry.get("triangles") or 0))
    meshes = max(0, int(geometry.get("meshes") or 0))
    material_count = max(0, int(materials.get("count") or 0))
    textured = max(0, int(attributes.get("texturedPrimitives") or 0))
    textured_uv = max(0, int(attributes.get("texturedPrimitivesWithUv0") or 0))
    pbr_materials = max(0, int(materials.get("pbrMetallicRoughness") or 0))

    if profile == "character":
        lod_ratios = [1.0, 0.60, 0.30, 0.12]
        collision = {
            "strategy": "capsule-or-compound",
            "meshCollisionRecommended": False,
            "godotImportHint": None,
            "reason": "animated characters should use stable primitive collision rather than render-mesh collision",
        }
    elif profile == "environment":
        lod_ratios = [1.0, 0.50, 0.20, 0.08]
        collision = {
            "strategy": "simplified-static-mesh",
            "meshCollisionRecommended": True,
            "godotImportHint": "-colonly",
            "fallbackGodotImportHint": "-col",
            "reason": "large static environments benefit from dedicated simplified collision geometry",
        }
    else:
        lod_ratios = [1.0, 0.50, 0.20]
        collision = {
            "strategy": "convex-or-simplified-static",
            "meshCollisionRecommended": triangles <= 5000,
            "godotImportHint": "-convcol",
            "fallbackGodotImportHint": "-col",
            "reason": "props should prefer convex or simplified static collision; full mesh is acceptable only for small static geometry",
        }

    lod = []
    for index, ratio in enumerate(lod_ratios):
        target = int(round(triangles * ratio)) if triangles else 0
        lod.append({
            "level": index,
            "ratio": ratio,
            "targetTriangles": target,
            "screenRelativeHint": [1.0, 0.55, 0.28, 0.12][min(index, 3)],
        })

    pbr = {
        "materials": material_count,
        "pbrMaterials": pbr_materials,
        "allMaterialsPbr": material_count == 0 or pbr_materials == material_count,
        "texturedPrimitives": textured,
        "texturedPrimitivesWithUv0": textured_uv,
        "allTexturedPrimitivesHaveUv0": textured == 0 or textured_uv == textured,
        "normalTextures": int(materials.get("normalTextures") or 0),
        "metallicRoughnessTextures": int(materials.get("metallicRoughnessTextures") or 0),
    }

    recommendations = []
    if triangles > 10000:
        recommendations.append("generate and ship explicit lower-detail LOD meshes")
    if not pbr["allMaterialsPbr"]:
        recommendations.append("convert every runtime material to glTF metallic-roughness PBR")
    if not pbr["allTexturedPrimitivesHaveUv0"]:
        recommendations.append("repair TEXCOORD_0 before texture delivery")
    if textures.get("externalImages", 0):
        recommendations.append("embed external textures for deterministic runtime delivery")

    return {
        "schema": "asset-forge/runtime-3d-plan/v1",
        "profile": profile,
        "source": {
            "meshes": meshes,
            "triangles": triangles,
        },
        "lod": {
            "required": triangles > 10000,
            "levels": lod,
        },
        "collision": collision,
        "pbr": pbr,
        "recommendations": recommendations,
    }
