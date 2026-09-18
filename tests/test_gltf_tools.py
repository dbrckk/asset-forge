import json
import struct
import tempfile
import unittest
from pathlib import Path

from gltf_tools import inspect_gltf, validate_gltf_profile


def make_glb(data: dict) -> bytes:
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    padding = (4 - (len(payload) % 4)) % 4
    payload += b" " * padding
    total = 12 + 8 + len(payload)
    return (
        struct.pack("<III", 0x46546C67, 2, total)
        + struct.pack("<II", len(payload), 0x4E4F534A)
        + payload
    )


class GltfToolsTests(unittest.TestCase):
    def base(self):
        return {
            "asset": {"version": "2.0"},
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
            "accessors": [{}],
        }

    def test_valid_gltf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.gltf"
            path.write_text(json.dumps(self.base()), encoding="utf-8")
            info, errors, warnings = inspect_gltf(path)

        self.assertEqual(errors, [])
        self.assertEqual(info["version"], "2.0")
        self.assertEqual(info["meshes"], 1)
        self.assertEqual(info["primitives"], 1)
        self.assertEqual(warnings, [])

    def test_invalid_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.gltf"
            data = self.base()
            data["asset"]["version"] = "1.0"
            path.write_text(json.dumps(data), encoding="utf-8")
            _, errors, _ = inspect_gltf(path)

        self.assertIn("asset.version must be 2.0", errors)

    def test_glb_json_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.glb"
            path.write_bytes(make_glb(self.base()))
            info, errors, _ = inspect_gltf(path)

        self.assertEqual(errors, [])
        self.assertEqual(info["container"], "glb")
        self.assertEqual(info["chunks"], 1)

    def test_character_requires_skin(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "character.gltf"
            path.write_text(json.dumps(self.base()), encoding="utf-8")
            _, errors, _ = validate_gltf_profile(path, "character")

        self.assertIn("profile character: at least one skin is required", errors)

    def test_character_with_skin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "character.gltf"
            data = self.base()
            data["skins"] = [{"joints": [0]}]
            path.write_text(json.dumps(data), encoding="utf-8")
            _, errors, _ = validate_gltf_profile(path, "character")

        self.assertEqual(errors, [])

    def test_out_of_range_mesh_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.gltf"
            data = self.base()
            data["nodes"][0]["mesh"] = 4
            path.write_text(json.dumps(data), encoding="utf-8")
            _, errors, _ = inspect_gltf(path)

        self.assertTrue(any("nodes[0].mesh" in error for error in errors))

    def test_out_of_range_accessor_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.gltf"
            data = self.base()
            data["meshes"][0]["primitives"][0]["attributes"]["POSITION"] = 8
            path.write_text(json.dumps(data), encoding="utf-8")
            _, errors, _ = inspect_gltf(path)

        self.assertTrue(any("attributes.POSITION" in error for error in errors))

    def test_valid_skin_joint_reference_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "skin.gltf"
            data = self.base()
            data["skins"] = [{"joints": [0]}]
            data["nodes"][0]["skin"] = 0
            path.write_text(json.dumps(data), encoding="utf-8")
            _, errors, _ = inspect_gltf(path)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
