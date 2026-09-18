import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import asset_forge


ROOT = Path(__file__).resolve().parents[1]


def write_png(path: Path, width: int, height: int, color_type: int = 6) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data
    ihdr += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    channels = 4 if color_type == 6 else 3
    row = b"\x00" + (b"\x00" * width * channels)
    raw = row * height
    idat_data = zlib.compress(raw)
    idat = struct.pack(">I", len(idat_data)) + b"IDAT" + idat_data
    idat += struct.pack(">I", zlib.crc32(b"IDAT" + idat_data) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    path.write_bytes(signature + ihdr + idat + iend)


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

    def test_png_sprite_grid_validation_passes(self):
        manifest = self.load_example()
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 64, 32)
            info, errors = asset_forge.validate_raster_file(image, manifest)
        self.assertEqual(errors, [])
        self.assertEqual(info["width"], 64)
        self.assertEqual(info["height"], 32)
        self.assertTrue(info["hasAlpha"])

    def test_png_sprite_grid_validation_rejects_bad_width(self):
        manifest = self.load_example()
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 50, 32)
            _, errors = asset_forge.validate_raster_file(image, manifest)
        self.assertIn("width 50 is not divisible by frameWidth 32", errors)

    def test_png_alpha_requirement(self):
        manifest = self.load_example()
        manifest["constraints"]["requiresAlpha"] = True
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 32, 32, color_type=2)
            _, errors = asset_forge.validate_raster_file(image, manifest)
        self.assertIn("PNG does not contain an alpha channel", errors)


if __name__ == "__main__":
    unittest.main()
