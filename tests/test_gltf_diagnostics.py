import base64
import json
import struct
import tempfile
import unittest
from pathlib import Path

from gltf_diagnostics import (
    deep_gltf_diagnostics,
    inspect_accessors,
    inspect_animation_consistency,
    inspect_skinning_consistency,
)


class GltfDiagnosticsTests(unittest.TestCase):
    def write(self, root: Path, data: dict) -> Path:
        path = root / "asset.gltf"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_accessor_byte_range_and_layout(self):
        payload = struct.pack("<9f", *[float(i) for i in range(9)])
        uri = "data:application/octet-stream;base64," + base64.b64encode(payload).decode("ascii")
        data = {
            "asset": {"version": "2.0"},
            "buffers": [{"byteLength": len(payload), "uri": uri}],
            "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(payload)}],
            "accessors": [
                {
                    "bufferView": 0,
                    "byteOffset": 0,
                    "componentType": 5126,
                    "count": 3,
                    "type": "VEC3",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_accessors(self.write(Path(tmp), data))

        self.assertEqual(report["errors"], [])
        self.assertTrue(report["items"][0]["dataAvailable"])
        self.assertEqual(report["items"][0]["elementBytes"], 12)
        self.assertEqual(report["items"][0]["requiredBytesInView"], 36)

    def test_accessor_overrun_is_rejected(self):
        data = {
            "asset": {"version": "2.0"},
            "buffers": [{"byteLength": 8}],
            "bufferViews": [{"buffer": 0, "byteLength": 8}],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5126,
                    "count": 3,
                    "type": "SCALAR",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_accessors(self.write(Path(tmp), data))

        self.assertTrue(any("requires 12 bytes" in item for item in report["errors"]))

    def test_skinning_requires_matching_vec4_attributes(self):
        data = {
            "asset": {"version": "2.0"},
            "meshes": [
                {
                    "primitives": [
                        {
                            "attributes": {
                                "POSITION": 0,
                                "JOINTS_0": 1,
                                "WEIGHTS_0": 2,
                            }
                        }
                    ]
                }
            ],
            "accessors": [
                {"componentType": 5126, "count": 10, "type": "VEC3"},
                {"componentType": 5123, "count": 10, "type": "VEC4"},
                {"componentType": 5126, "count": 9, "type": "VEC4"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_skinning_consistency(self.write(Path(tmp), data))

        self.assertTrue(any("counts differ" in item for item in report["errors"]))

    def test_animation_duration_reads_real_key_times(self):
        times = struct.pack("<3f", 0.0, 0.5, 2.0)
        output = struct.pack("<9f", *([0.0] * 9))
        payload = times + output
        uri = "data:application/octet-stream;base64," + base64.b64encode(payload).decode("ascii")
        data = {
            "asset": {"version": "2.0"},
            "nodes": [{}],
            "buffers": [{"byteLength": len(payload), "uri": uri}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": len(times)},
                {"buffer": 0, "byteOffset": len(times), "byteLength": len(output)},
            ],
            "accessors": [
                {"bufferView": 0, "componentType": 5126, "count": 3, "type": "SCALAR"},
                {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            ],
            "animations": [
                {
                    "name": "move",
                    "samplers": [{"input": 0, "output": 1}],
                    "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_animation_consistency(self.write(Path(tmp), data))

        self.assertEqual(report["errors"], [])
        self.assertEqual(report["items"][0]["durationSeconds"], 2.0)
        self.assertEqual(report["maxDurationSeconds"], 2.0)

    def test_non_increasing_animation_times_are_rejected(self):
        times = struct.pack("<3f", 0.0, 1.0, 1.0)
        output = struct.pack("<9f", *([0.0] * 9))
        payload = times + output
        uri = "data:application/octet-stream;base64," + base64.b64encode(payload).decode("ascii")
        data = {
            "asset": {"version": "2.0"},
            "nodes": [{}],
            "buffers": [{"byteLength": len(payload), "uri": uri}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": len(times)},
                {"buffer": 0, "byteOffset": len(times), "byteLength": len(output)},
            ],
            "accessors": [
                {"bufferView": 0, "componentType": 5126, "count": 3, "type": "SCALAR"},
                {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            ],
            "animations": [
                {
                    "samplers": [{"input": 0, "output": 1}],
                    "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_animation_consistency(self.write(Path(tmp), data))

        self.assertTrue(any("strictly increasing" in item for item in report["errors"]))

    def test_deep_report_has_all_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(Path(tmp), {"asset": {"version": "2.0"}})
            report = deep_gltf_diagnostics(path)

        self.assertIn("accessors", report)
        self.assertIn("skinning", report)
        self.assertIn("animations", report)


if __name__ == "__main__":
    unittest.main()
