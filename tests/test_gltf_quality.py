import json
import tempfile
import unittest
from pathlib import Path

from gltf_quality import build_quality_report, evaluate_quality, quality_report


class GltfQualityTests(unittest.TestCase):
    def write(self, root: Path, data: dict) -> Path:
        path = root / "asset.gltf"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def base(self):
        return {
            "asset": {"version": "2.0"},
            "meshes": [
                {
                    "primitives": [
                        {
                            "attributes": {
                                "POSITION": 0,
                                "NORMAL": 1,
                                "TEXCOORD_0": 2,
                            },
                            "indices": 3,
                            "material": 0,
                        }
                    ]
                }
            ],
            "accessors": [
                {"componentType": 5126, "count": 100, "type": "VEC3"},
                {"componentType": 5126, "count": 100, "type": "VEC3"},
                {"componentType": 5126, "count": 100, "type": "VEC2"},
                {"componentType": 5123, "count": 300, "type": "SCALAR"},
            ],
            "materials": [
                {
                    "pbrMetallicRoughness": {
                        "baseColorTexture": {"index": 0}
                    }
                }
            ],
            "textures": [{"source": 0}],
            "images": [{"uri": "albedo.png"}],
        }

    def test_counts_vertices_and_triangles(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_quality_report(self.write(Path(tmp), self.base()))

        self.assertEqual(report["geometry"]["vertices"], 100)
        self.assertEqual(report["geometry"]["triangles"], 100)
        self.assertEqual(report["attributes"]["normals"], 1)
        self.assertEqual(report["attributes"]["uv0"], 1)

    def test_triangle_strip_count(self):
        data = self.base()
        data["meshes"][0]["primitives"][0]["mode"] = 5
        data["accessors"][3]["count"] = 10
        with tempfile.TemporaryDirectory() as tmp:
            report = build_quality_report(self.write(Path(tmp), data))

        self.assertEqual(report["geometry"]["triangles"], 8)

    def test_character_quality_requires_skin_attributes(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_quality_report(self.write(Path(tmp), self.base()))
            evaluation = evaluate_quality(report, "character")

        self.assertFalse(evaluation["passed"])
        self.assertTrue(any("JOINTS_0" in item for item in evaluation["errors"]))

    def test_textured_primitive_requires_uv(self):
        data = self.base()
        del data["meshes"][0]["primitives"][0]["attributes"]["TEXCOORD_0"]
        with tempfile.TemporaryDirectory() as tmp:
            report = quality_report(self.write(Path(tmp), data), "prop")

        self.assertFalse(report["evaluation"]["passed"])
        self.assertTrue(any("TEXCOORD_0" in item for item in report["evaluation"]["errors"]))

    def test_normal_map_without_tangent_warns(self):
        data = self.base()
        data["materials"][0]["normalTexture"] = {"index": 0}
        with tempfile.TemporaryDirectory() as tmp:
            report = quality_report(self.write(Path(tmp), data), "prop")

        self.assertTrue(any("TANGENT" in item for item in report["evaluation"]["warnings"]))

    def test_external_image_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = quality_report(self.write(Path(tmp), self.base()), "prop")

        self.assertEqual(report["textures"]["externalImages"], 1)
        self.assertTrue(any("external image" in item for item in report["evaluation"]["warnings"]))

    def test_untextured_primitive_does_not_require_uv(self):
        data = self.base()
        data["materials"] = [{}]
        data["textures"] = []
        data["images"] = []
        del data["meshes"][0]["primitives"][0]["attributes"]["TEXCOORD_0"]
        with tempfile.TemporaryDirectory() as tmp:
            report = quality_report(self.write(Path(tmp), data), "prop")

        self.assertTrue(report["evaluation"]["passed"])


    def test_strict_prop_budget_is_blocking(self):
        report = {
            "geometry": {
                "meshes": 9,
                "primitives": 1,
                "vertices": 10,
                "triangles": 10,
                "primitiveVerticesKnown": 1,
                "primitiveTrianglesKnown": 1,
            },
            "attributes": {
                "normals": 1,
                "uv0": 0,
                "skinned": 0,
                "texturedPrimitives": 0,
                "texturedPrimitivesWithUv0": 0,
                "normalMappedPrimitives": 0,
                "normalMappedPrimitivesWithTangent": 0,
            },
            "materials": {
                "count": 0,
                "pbrMetallicRoughness": 0,
            },
            "textures": {
                "count": 0,
                "maxWidth": 0,
                "maxHeight": 0,
                "estimatedRgba8MipBytes": 0,
                "externalImages": 0,
            },
            "rigAnimation": {
                "animations": 0,
                "maxJointsPerSkin": 0,
            },
            "diagnostics": {
                "accessors": {"errors": [], "warnings": []},
                "skinning": {"errors": [], "warnings": []},
                "animations": {"errors": [], "warnings": []},
            },
        }
        evaluation = evaluate_quality(report, "prop")
        self.assertFalse(evaluation["passed"])
        self.assertTrue(any("meshes 9 exceed" in value for value in evaluation["errors"]))

    def test_prop_rejects_non_pbr_materials_and_animations(self):
        report = {
            "geometry": {
                "meshes": 1,
                "primitives": 1,
                "vertices": 10,
                "triangles": 10,
                "primitiveVerticesKnown": 1,
                "primitiveTrianglesKnown": 1,
            },
            "attributes": {
                "normals": 1,
                "uv0": 0,
                "skinned": 0,
                "texturedPrimitives": 0,
                "texturedPrimitivesWithUv0": 0,
                "normalMappedPrimitives": 0,
                "normalMappedPrimitivesWithTangent": 0,
            },
            "materials": {
                "count": 1,
                "pbrMetallicRoughness": 0,
            },
            "textures": {
                "count": 0,
                "maxWidth": 0,
                "maxHeight": 0,
                "estimatedRgba8MipBytes": 0,
                "externalImages": 0,
            },
            "rigAnimation": {
                "animations": 1,
                "maxJointsPerSkin": 0,
            },
            "diagnostics": {
                "accessors": {"errors": [], "warnings": []},
                "skinning": {"errors": [], "warnings": []},
                "animations": {"errors": [], "warnings": []},
            },
        }
        evaluation = evaluate_quality(report, "prop")
        self.assertFalse(evaluation["passed"])
        self.assertTrue(any("metallic-roughness PBR" in value for value in evaluation["errors"]))
        self.assertTrue(any("forbids animations" in value for value in evaluation["errors"]))

if __name__ == "__main__":
    unittest.main()
