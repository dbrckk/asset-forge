import base64
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from gltf_binary_metrics import inspect_images, inspect_rig_and_animation
from gltf_quality import quality_report


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def tiny_png(width=2, height=4):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + (b"\x00\x00\x00\xff" * width) for _ in range(height))
    return PNG_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class GltfBinaryMetricsTests(unittest.TestCase):
    def test_data_uri_png_dimensions_and_memory(self):
        payload = tiny_png(2, 4)
        uri = "data:image/png;base64," + base64.b64encode(payload).decode("ascii")
        data = {
            "asset": {"version": "2.0"},
            "images": [{"uri": uri}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.gltf"
            path.write_text(json.dumps(data), encoding="utf-8")
            items = inspect_images(path)

        self.assertEqual(items[0]["width"], 2)
        self.assertEqual(items[0]["height"], 4)
        self.assertEqual(items[0]["format"], "png")
        self.assertEqual(items[0]["estimatedRgba8Bytes"], 32)
        self.assertEqual(items[0]["estimatedRgba8MipBytes"], 43)

    def test_local_external_png_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "albedo.png").write_bytes(tiny_png(8, 8))
            path = root / "asset.gltf"
            path.write_text(
                json.dumps({"asset": {"version": "2.0"}, "images": [{"uri": "albedo.png"}]}),
                encoding="utf-8",
            )
            items = inspect_images(path)

        self.assertTrue(items[0]["available"])
        self.assertEqual(items[0]["width"], 8)
        self.assertEqual(items[0]["source"], "external-local")

    def test_animation_and_rig_metrics(self):
        data = {
            "asset": {"version": "2.0"},
            "nodes": [{}, {}, {}],
            "skins": [{"joints": [0, 1, 2], "inverseBindMatrices": 0}],
            "accessors": [{"count": 3}, {"count": 24}],
            "animations": [
                {
                    "samplers": [{"input": 1, "output": 1}],
                    "channels": [
                        {"sampler": 0, "target": {"node": 1, "path": "rotation"}}
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.gltf"
            path.write_text(json.dumps(data), encoding="utf-8")
            metrics = inspect_rig_and_animation(path)

        self.assertEqual(metrics["maxJointsPerSkin"], 3)
        self.assertEqual(metrics["animations"], 1)
        self.assertEqual(metrics["animationChannels"], 1)
        self.assertEqual(metrics["targetPaths"]["rotation"], 1)
        self.assertEqual(metrics["maxKeyframesPerSampler"], 24)

    def test_quality_report_includes_binary_metrics(self):
        payload = tiny_png(4, 4)
        uri = "data:image/png;base64," + base64.b64encode(payload).decode("ascii")
        data = {
            "asset": {"version": "2.0"},
            "meshes": [],
            "accessors": [],
            "images": [{"uri": uri}],
            "textures": [{"source": 0}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.gltf"
            path.write_text(json.dumps(data), encoding="utf-8")
            report = quality_report(path, "prop")

        self.assertEqual(report["textures"]["knownDimensions"], 1)
        self.assertEqual(report["textures"]["maxWidth"], 4)
        self.assertIn("rigAnimation", report)


if __name__ == "__main__":
    unittest.main()
