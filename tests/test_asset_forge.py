import json
import tempfile
import unittest
from pathlib import Path

import asset_forge


ROOT = Path(__file__).resolve().parents[1]


class AssetForgeTests(unittest.TestCase):
    def load_example(self):
        return asset_forge.load_json(ROOT / "examples/asset-manifest.json")

    def test_example_manifest_is_valid(self):
        self.assertEqual(asset_forge.validate_manifest(self.load_example()), [])

    def test_external_asset_requires_uri(self):
        manifest = self.load_example()
        manifest["source"] = {"mode": "external", "uri": None}
        errors = asset_forge.validate_manifest(manifest)
        self.assertIn("source.uri: required for external assets", errors)

    def test_incompatible_commercial_license_is_rejected(self):
        manifest = self.load_example()
        manifest["license"]["commercialUse"] = False
        errors = asset_forge.validate_manifest(manifest)
        self.assertIn(
            "license.commercialUse: must be true for production-ready assets",
            errors,
        )

    def test_plan_routes_sprite_to_2d_pipeline(self):
        manifest = self.load_example()
        plan = asset_forge.build_plan(manifest, ROOT)
        self.assertEqual(plan["pipeline"], "pipelines/sprite-2d.json")
        self.assertIn("validate-alpha-and-grid", plan["stages"])
        tool_ids = [item["id"] for item in plan["candidateTools"]]
        self.assertIn("pixelorama", tool_ids)

    def test_secondary_custom_asset_prompts_reuse_search(self):
        manifest = self.load_example()
        manifest["importance"] = "secondary"
        plan = asset_forge.build_plan(manifest, ROOT)
        self.assertEqual(
            plan["sourcingPolicy"],
            "search-approved-assets-before-custom-creation",
        )


if __name__ == "__main__":
    unittest.main()
