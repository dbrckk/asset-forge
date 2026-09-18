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
