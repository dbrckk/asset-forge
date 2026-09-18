import tempfile
import unittest
from pathlib import Path

from godot_export import render_spriteframes, write_spriteframes


class GodotExportTests(unittest.TestCase):
    def metadata(self):
        return {
            "frames": [
                {"index": 0, "x": 0, "y": 0, "width": 32, "height": 32},
                {"index": 1, "x": 32, "y": 0, "width": 32, "height": 32},
            ]
        }

    def test_render_spriteframes_uses_atlas_regions(self):
        rendered = render_spriteframes(
            "res://art/player.png",
            self.metadata(),
            animation_name="run",
            fps=10,
            loop=False,
        )

        self.assertIn('[gd_resource type="SpriteFrames"', rendered)
        self.assertIn('[ext_resource type="Texture2D" path="res://art/player.png"', rendered)
        self.assertIn('[sub_resource type="AtlasTexture" id="AtlasTexture_0"]', rendered)
        self.assertIn("region = Rect2(32, 0, 32, 32)", rendered)
        self.assertIn('"name": &"run"', rendered)
        self.assertIn('"speed": 10.0', rendered)
        self.assertIn('"loop": false', rendered)
        self.assertIn('SubResource("AtlasTexture_1")', rendered)

    def test_trimmed_frame_emits_atlas_margin(self):
        metadata = {
            "imageWidth": 64,
            "imageHeight": 64,
            "frames": [
                {
                    "index": 0,
                    "x": 10,
                    "y": 20,
                    "width": 8,
                    "height": 6,
                    "sourceWidth": 16,
                    "sourceHeight": 12,
                    "offsetX": 3,
                    "offsetY": 2,
                }
            ],
        }
        rendered = render_spriteframes("res://atlas.png", metadata)

        self.assertIn("region = Rect2(10, 20, 8, 6)", rendered)
        self.assertIn("margin = Rect2(3, 2, 8, 6)", rendered)

    def test_untrimmed_frame_does_not_emit_margin(self):
        rendered = render_spriteframes("res://atlas.png", self.metadata())
        self.assertNotIn("margin = Rect2", rendered)

    def test_rejects_trim_metadata_that_does_not_fit_source(self):
        metadata = {
            "frames": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 8,
                    "height": 8,
                    "sourceWidth": 8,
                    "sourceHeight": 8,
                    "offsetX": 1,
                    "offsetY": 0,
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "does not fit source dimensions"):
            render_spriteframes("res://atlas.png", metadata)

    def test_rejects_frame_outside_known_atlas_bounds(self):
        metadata = {
            "imageWidth": 16,
            "imageHeight": 16,
            "frames": [{"x": 10, "y": 0, "width": 8, "height": 8}],
        }
        with self.assertRaisesRegex(ValueError, "exceeds atlas width"):
            render_spriteframes("res://atlas.png", metadata)

    def test_multiple_animations(self):
        rendered = render_spriteframes(
            "res://art/player.png",
            self.metadata(),
            animations=[
                {"name": "idle", "fps": 6, "loop": True, "frames": [0]},
                {
                    "name": "attack",
                    "fps": 12,
                    "loop": False,
                    "frames": [
                        {"index": 1, "duration": 0.5},
                        {"index": 0, "duration": 1.5},
                    ],
                },
            ],
        )

        self.assertIn('"name": &"idle"', rendered)
        self.assertIn('"name": &"attack"', rendered)
        self.assertIn('"speed": 6.0', rendered)
        self.assertIn('"speed": 12.0', rendered)
        self.assertIn('"loop": false', rendered)
        self.assertIn('"duration": 0.5', rendered)
        self.assertIn('"duration": 1.5', rendered)

    def test_rejects_duplicate_animation_names(self):
        with self.assertRaisesRegex(ValueError, "duplicate animation name"):
            render_spriteframes(
                "res://a.png",
                self.metadata(),
                animations=[
                    {"name": "idle", "frames": [0]},
                    {"name": "idle", "frames": [1]},
                ],
            )

    def test_rejects_out_of_range_animation_frame(self):
        with self.assertRaisesRegex(ValueError, "out of range"):
            render_spriteframes(
                "res://a.png",
                self.metadata(),
                animations=[{"name": "run", "frames": [2]}],
            )

    def test_write_spriteframes_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "player.tres"
            write_spriteframes(
                output,
                "res://player.png",
                self.metadata(),
            )
            rendered = output.read_text(encoding="utf-8")

        self.assertIn("[resource]", rendered)
        self.assertIn("animations = [{", rendered)

    def test_rejects_empty_metadata(self):
        with self.assertRaisesRegex(ValueError, "at least one frame"):
            render_spriteframes("res://a.png", {"frames": []})

    def test_rejects_invalid_fps(self):
        with self.assertRaisesRegex(ValueError, "fps must be > 0"):
            render_spriteframes("res://a.png", self.metadata(), fps=0)


if __name__ == "__main__":
    unittest.main()
