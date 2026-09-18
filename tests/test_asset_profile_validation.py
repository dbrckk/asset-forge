import json
import tempfile
import unittest
from pathlib import Path

from asset_profile_validation import (
    load_3d_profile,
    load_vector_profile,
    validate_3d_profile_data,
    validate_all_asset_profiles,
    validate_vector_profile_data,
)


class AssetProfileValidationTests(unittest.TestCase):
    def test_repository_profiles_all_validate(self):
        root = Path(__file__).resolve().parents[1]
        report = validate_all_asset_profiles(root)
        self.assertTrue(report["valid"], report)

    def test_3d_loader_reads_versioned_budget(self):
        profile = load_3d_profile("character")
        self.assertEqual(profile["rules"]["maxJointsPerSkin"], 128)
        self.assertTrue(profile["rules"]["requireSkin"])

    def test_vector_loader_reads_versioned_budget(self):
        profile = load_vector_profile("icon")
        self.assertEqual(profile["rules"]["maxElements"], 256)
        self.assertTrue(profile["rules"]["requireSquareViewBox"])

    def test_invalid_3d_unknown_rule_fails(self):
        data = {
            "id": "prop",
            "assetTypes": ["prop"],
            "rules": {
                "maxMeshes": 1,
                "maxPrimitives": 1,
                "maxMaterials": 1,
                "maxVertices": 1,
                "maxTriangles": 1,
                "maxTextures": 1,
                "allowAnimations": False,
                "requireSkin": False,
                "requireNormals": True,
                "requireUvWhenTextured": True,
                "maxTextureDimension": 1,
                "maxEstimatedTextureMipBytes": 1,
                "maxJointsPerSkin": 0,
                "mystery": 1
            },
        }
        errors = validate_3d_profile_data(data, "prop")
        self.assertTrue(any("rules.mystery: unknown field" in error for error in errors))

    def test_invalid_vector_type_fails(self):
        data = {
            "id": "icon",
            "assetTypes": ["icon"],
            "rules": {
                "requireViewBox": True,
                "requireSquareViewBox": True,
                "maxElements": "256",
                "allowExternalReferences": False,
                "removeMetadata": True,
            },
        }
        errors = validate_vector_profile_data(data, "icon")
        self.assertTrue(any("rules.maxElements: int required" in error for error in errors))

    def test_3d_loader_uses_file_as_source_of_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_dir = root / "profiles" / "3d"
            profile_dir.mkdir(parents=True)
            data = {
                "id": "prop",
                "assetTypes": ["prop"],
                "rules": {
                    "maxMeshes": 8,
                    "maxPrimitives": 16,
                    "maxMaterials": 8,
                    "maxVertices": 42,
                    "maxTriangles": 43,
                    "maxTextures": 16,
                    "allowAnimations": False,
                    "requireSkin": False,
                    "requireNormals": True,
                    "requireUvWhenTextured": True,
                    "maxTextureDimension": 4096,
                    "maxEstimatedTextureMipBytes": 134217728,
                    "maxJointsPerSkin": 0,
                },
            }
            (profile_dir / "prop.json").write_text(json.dumps(data), encoding="utf-8")
            loaded = load_3d_profile("prop", root=root)

        self.assertEqual(loaded["rules"]["maxVertices"], 42)
        self.assertEqual(loaded["rules"]["maxTriangles"], 43)

    def test_vector_loader_uses_file_as_source_of_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_dir = root / "profiles" / "vector"
            profile_dir.mkdir(parents=True)
            data = {
                "id": "icon",
                "assetTypes": ["icon"],
                "rules": {
                    "requireViewBox": True,
                    "requireSquareViewBox": False,
                    "maxElements": 99,
                    "allowExternalReferences": False,
                    "removeMetadata": True,
                },
            }
            (profile_dir / "icon.json").write_text(json.dumps(data), encoding="utf-8")
            loaded = load_vector_profile("icon", root=root)

        self.assertEqual(loaded["rules"]["maxElements"], 99)
        self.assertFalse(loaded["rules"]["requireSquareViewBox"])


if __name__ == "__main__":
    unittest.main()
