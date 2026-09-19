import unittest

from runtime_atlas import build_runtime_atlas, validate_runtime_atlas


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
        self.assertEqual(
            result["capabilities"],
            {"trimOffsets": True, "clockwise90Rotation": True},
        )
        self.assertEqual(frame["atlasRegion"], {"x": 10, "y": 20, "width": 6, "height": 8})
        self.assertEqual(
            frame["uv"],
            {
                "u0": 10 / 64,
                "v0": 20 / 64,
                "u1": 16 / 64,
                "v1": 28 / 64,
            },
        )
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

    def test_validator_accepts_generated_runtime_atlas(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 0, "y": 0, "width": 4, "height": 5}],
        }
        runtime = build_runtime_atlas(source)
        self.assertEqual(validate_runtime_atlas(runtime), [])

    def test_validator_detects_uv_drift(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 4, "y": 4, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(source)
        runtime["frames"][0]["uv"]["u0"] = 0.0
        errors = validate_runtime_atlas(runtime)
        self.assertTrue(any("uv.u0 does not match atlasRegion" in error for error in errors))

    def test_validator_detects_frame_count_mismatch(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 0, "y": 0, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(source)
        runtime["frameCount"] = 2
        errors = validate_runtime_atlas(runtime)
        self.assertTrue(any("does not match frames length" in error for error in errors))

    def test_validator_rejects_unknown_fields(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 0, "y": 0, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(source)
        runtime["extra"] = True
        errors = validate_runtime_atlas(runtime)
        self.assertIn("unknown top-level field: extra", errors)

    def test_validator_rejects_boolean_integer_fields(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 0, "y": 0, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(source)
        runtime["imageSize"]["width"] = True
        errors = validate_runtime_atlas(runtime)
        self.assertIn("imageSize.width: integer required", errors)

    def test_validator_rejects_unknown_nested_fields(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 0, "y": 0, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(source)
        runtime["frames"][0]["uv"]["extra"] = 1
        runtime["frames"][0]["rotation"]["extra"] = 1
        errors = validate_runtime_atlas(runtime)
        self.assertIn("frame 0: unknown uv field extra", errors)
        self.assertIn("frame 0: unknown rotation field extra", errors)

    def test_build_runtime_atlas_normalizes_animations(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [
                {"index": 0, "x": 0, "y": 0, "width": 4, "height": 4},
                {"index": 1, "x": 4, "y": 0, "width": 4, "height": 4},
            ],
        }
        runtime = build_runtime_atlas(
            source,
            animations=[
                {
                    "name": "run",
                    "fps": 10,
                    "loop": True,
                    "frames": [0, {"index": 1, "duration": 2}],
                }
            ],
        )

        self.assertEqual(
            runtime["animations"],
            [
                {
                    "name": "run",
                    "fps": 10.0,
                    "loop": True,
                    "frames": [
                        {"index": 0, "duration": 1.0},
                        {"index": 1, "duration": 2.0},
                    ],
                }
            ],
        )
        self.assertEqual(validate_runtime_atlas(runtime), [])

    def test_build_runtime_atlas_rejects_missing_animation_frame(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"index": 0, "x": 0, "y": 0, "width": 4, "height": 4}],
        }
        with self.assertRaisesRegex(ValueError, "index 1 not found"):
            build_runtime_atlas(
                source,
                animations=[
                    {
                        "name": "run",
                        "fps": 10,
                        "loop": True,
                        "frames": [1],
                    }
                ],
            )

    def test_validator_rejects_animation_frame_reference_drift(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"index": 0, "x": 0, "y": 0, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(
            source,
            animations=[
                {
                    "name": "idle",
                    "fps": 5,
                    "loop": False,
                    "frames": [0],
                }
            ],
        )
        runtime["animations"][0]["frames"][0]["index"] = 3
        errors = validate_runtime_atlas(runtime)
        self.assertTrue(any("index 3 not found" in error for error in errors))

    def test_validator_rejects_duplicate_animation_names(self):
        source = {
            "image": "atlas.png",
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"index": 0, "x": 0, "y": 0, "width": 4, "height": 4}],
        }
        runtime = build_runtime_atlas(source)
        runtime["animations"] = [
            {
                "name": "idle",
                "fps": 5.0,
                "loop": True,
                "frames": [{"index": 0, "duration": 1.0}],
            },
            {
                "name": "idle",
                "fps": 5.0,
                "loop": True,
                "frames": [{"index": 0, "duration": 1.0}],
            },
        ]
        errors = validate_runtime_atlas(runtime)
        self.assertIn("duplicate animation name: idle", errors)


if __name__ == "__main__":
    unittest.main()
