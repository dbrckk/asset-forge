import unittest

from runtime_atlas import build_runtime_atlas


class RuntimeAtlasTests(unittest.TestCase):
    def test_exports_trim_and_rotation_semantics(self):
        metadata = {
            "image": "atlas.png",
            "imageWidth": 64,
            "imageHeight": 64,
            "frames": [
                {
                    "index": 0,
                    "name": "hero.png",
                    "x": 10,
                    "y": 20,
                    "width": 6,
                    "height": 8,
                    "sourceRegionWidth": 8,
                    "sourceRegionHeight": 6,
                    "sourceWidth": 12,
                    "sourceHeight": 10,
                    "offsetX": 2,
                    "offsetY": 1,
                    "rotated": True,
                    "rotationDegrees": 90,
                }
            ],
        }

        result = build_runtime_atlas(metadata)
        frame = result["frames"][0]

        self.assertEqual(result["format"], "asset-forge-runtime-atlas")
        self.assertEqual(result["version"], 1)
        self.assertEqual(frame["atlasRegion"], {"x": 10, "y": 20, "width": 6, "height": 8})
        self.assertEqual(frame["sourceRegion"], {"width": 8, "height": 6})
        self.assertEqual(frame["sourceSize"], {"width": 12, "height": 10})
        self.assertEqual(frame["trimOffset"], {"x": 2, "y": 1})
        self.assertEqual(frame["rotation"], {"rotated": True, "degreesClockwise": 90})

    def test_defaults_non_rotated_source_region(self):
        metadata = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 0, "y": 0, "width": 4, "height": 5}],
        }
        frame = build_runtime_atlas(metadata)["frames"][0]

        self.assertEqual(frame["sourceRegion"], {"width": 4, "height": 5})
        self.assertEqual(frame["sourceSize"], {"width": 4, "height": 5})
        self.assertEqual(frame["rotation"]["degreesClockwise"], 0)

    def test_rejects_rotation_dimension_mismatch(self):
        metadata = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 8,
                    "height": 6,
                    "sourceRegionWidth": 8,
                    "sourceRegionHeight": 6,
                    "rotated": True,
                    "rotationDegrees": 90,
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "do not match rotation metadata"):
            build_runtime_atlas(metadata)

    def test_rejects_source_trim_out_of_bounds(self):
        metadata = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 8,
                    "height": 8,
                    "sourceWidth": 8,
                    "sourceHeight": 8,
                    "offsetX": 1,
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "source region exceeds sourceWidth"):
            build_runtime_atlas(metadata)

    def test_rejects_duplicate_indices(self):
        metadata = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [
                {"index": 1, "x": 0, "y": 0, "width": 1, "height": 1},
                {"index": 1, "x": 1, "y": 0, "width": 1, "height": 1},
            ],
        }
        with self.assertRaisesRegex(ValueError, "duplicate frame index"):
            build_runtime_atlas(metadata)


if __name__ == "__main__":
    unittest.main()
