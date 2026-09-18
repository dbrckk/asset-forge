import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import asset_forge


ROOT = Path(__file__).resolve().parents[1]


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_png(
    path: Path,
    width: int,
    height: int,
    color_type: int = 6,
    palette_entries: int | None = None,
    transparency: bool = False,
) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    parts = [signature, chunk(b"IHDR", ihdr_data)]

    if palette_entries is not None:
        palette = bytearray()
        for index in range(palette_entries):
            value = index % 256
            palette.extend((value, value, value))
        parts.append(chunk(b"PLTE", bytes(palette)))
        if transparency:
            parts.append(chunk(b"tRNS", bytes([255] * max(1, palette_entries - 1) + [0])))

    channels = {2: 3, 6: 4}.get(color_type, 1)
    row = b"\x00" + (b"\x00" * width * channels)
    parts.append(chunk(b"IDAT", zlib.compress(row * height)))
    parts.append(chunk(b"IEND", b""))
    path.write_bytes(b"".join(parts))


class AssetForgeTests(unittest.TestCase):
    def load_example(self):
        return asset_forge.load_json(ROOT / "examples/asset-manifest.json")

    def test_example_manifest_is_valid(self):
        self.assertEqual(asset_forge.validate_manifest(self.load_example()), [])

    def test_pixel_art_rejects_non_nearest_interpolation(self):
        manifest = self.load_example()
        manifest["constraints"]["interpolation"] = "linear"
        self.assertIn(
            "constraints.interpolation: pixelArt assets must use nearest",
            asset_forge.validate_manifest(manifest),
        )

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
        manifest["constraints"]["expectedFrames"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 64, 32)
            info, errors = asset_forge.validate_raster_file(image, manifest)
        self.assertEqual(errors, [])
        self.assertEqual(info["grid"]["frameCount"], 2)
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
        self.assertIn("PNG does not contain transparency", errors)

    def test_palette_transparency_and_max_colors(self):
        manifest = self.load_example()
        manifest["constraints"]["requiresAlpha"] = True
        manifest["constraints"]["maxColors"] = 4
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 32, 32, color_type=3, palette_entries=8, transparency=True)
            info, errors = asset_forge.validate_raster_file(image, manifest)
        self.assertTrue(info["hasAlpha"])
        self.assertEqual(info["paletteEntries"], 8)
        self.assertIn("palette has 8 entries, exceeds maxColors 4", errors)

    def test_power_of_two_atlas(self):
        manifest = self.load_example()
        manifest["constraints"]["powerOfTwoAtlas"] = True
        manifest["constraints"]["frameWidth"] = 30
        manifest["constraints"]["frameHeight"] = 32
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 60, 32)
            _, errors = asset_forge.validate_raster_file(image, manifest)
        self.assertIn("atlas dimensions must be powers of two", errors)

    def test_atlas_manifest_contains_frame_rectangles(self):
        manifest = self.load_example()
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.png"
            write_png(image, 64, 64)
            atlas = asset_forge.build_atlas_manifest(image, manifest)
        self.assertEqual(atlas["columns"], 2)
        self.assertEqual(atlas["rows"], 2)
        self.assertEqual(atlas["frameCount"], 4)
        self.assertEqual(
            atlas["frames"][3],
            {"index": 3, "x": 32, "y": 32, "width": 32, "height": 32},
        )

    def test_webp_raster_validation_supports_dimensions_and_alpha(self):
        manifest = self.load_example()
        manifest["target"]["format"] = "webp"
        manifest["constraints"]["frameWidth"] = 32
        manifest["constraints"]["frameHeight"] = 32
        manifest["constraints"]["expectedFrames"] = 2
        manifest["constraints"]["requiresAlpha"] = True
        manifest["constraints"].pop("maxColors", None)

        width, height = 64, 32
        vp8x = bytes([0x10, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
        vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
        chunks = (
            b"VP8X" + struct.pack("<I", len(vp8x)) + vp8x
            + b"VP8 " + struct.pack("<I", len(vp8)) + vp8
        )
        body = b"WEBP" + chunks
        data = b"RIFF" + struct.pack("<I", len(body)) + body

        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.webp"
            image.write_bytes(data)
            info, errors = asset_forge.validate_raster_file(image, manifest)

        self.assertEqual(errors, [])
        self.assertEqual(info["format"], "webp")
        self.assertEqual(info["grid"]["frameCount"], 2)
        self.assertTrue(info["hasAlpha"])

    def test_webp_max_colors_constraint_is_rejected(self):
        manifest = self.load_example()
        manifest["target"]["format"] = "webp"
        manifest["constraints"]["maxColors"] = 4

        width = height = 32
        vp8x = bytes([0, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
        vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
        chunks = (
            b"VP8X" + struct.pack("<I", len(vp8x)) + vp8x
            + b"VP8 " + struct.pack("<I", len(vp8)) + vp8
        )
        body = b"WEBP" + chunks
        data = b"RIFF" + struct.pack("<I", len(body)) + body

        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sprite.webp"
            image.write_bytes(data)
            _, errors = asset_forge.validate_raster_file(image, manifest)

        self.assertIn("maxColors is only enforceable for indexed PNG assets", errors)

    def test_invalid_png_crc_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            write_png(image, 32, 32)
            data = bytearray(image.read_bytes())
            data[-1] ^= 0x01
            image.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "invalid CRC"):
                asset_forge.inspect_png(image)


if __name__ == "__main__":
    unittest.main()
