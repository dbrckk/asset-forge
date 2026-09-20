import tempfile
import unittest
from pathlib import Path

from art_quality import evaluate_raster_art


class ArtQualityTests(unittest.TestCase):
    def _image(self, path, *, box, color=(210, 70, 45, 255), size=(96, 96)):
        from PIL import Image, ImageDraw
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle(box, fill=color)
        image.save(path)

    def test_centered_transparent_sprite_passes_reasonable_quality_gate(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sprite.png"
            self._image(path, box=(20, 12, 75, 84))
            result = evaluate_raster_art(path, {
                "constraints": {
                    "requiresAlpha": True,
                    "technicalQualityMin": 0.45,
                    "maxBorderAlphaRatio": 0.05,
                }
            })
            self.assertTrue(result["passed"])
            self.assertGreaterEqual(result["score"], 0.45)
            self.assertEqual(result["metrics"]["borderAlphaRatio"], 0.0)

    def test_clipped_sprite_reports_border_warning(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "clipped.png"
            self._image(path, box=(0, 0, 95, 80))
            result = evaluate_raster_art(path, {
                "constraints": {
                    "requiresAlpha": True,
                    "maxBorderAlphaRatio": 0.02,
                }
            })
            self.assertTrue(result["warnings"])
            self.assertGreater(result["metrics"]["borderAlphaRatio"], 0.02)

    def test_fully_opaque_raster_fails_alpha_requirement(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "opaque.png"
            Image.new("RGBA", (64, 64), (100, 120, 140, 255)).save(path)
            result = evaluate_raster_art(path, {
                "constraints": {"requiresAlpha": True}
            })
            self.assertFalse(result["passed"])
            self.assertIn("fully opaque", result["errors"][0])

    def test_unstable_sprite_sheet_frame_occupancy_reduces_consistency(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sheet.png"
            image = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.rectangle((8, 8, 88, 88), fill=(220, 80, 40, 255))
            draw.rectangle((104, 8, 120, 24), fill=(220, 80, 40, 255))
            draw.rectangle((8, 104, 88, 184), fill=(220, 80, 40, 255))
            draw.rectangle((104, 104, 120, 120), fill=(220, 80, 40, 255))
            image.save(path)
            result = evaluate_raster_art(path, {
                "constraints": {
                    "expectedFrames": 4,
                    "frameWidth": 96,
                    "frameHeight": 96,
                }
            })
            self.assertEqual(len(result["metrics"]["frameOccupancies"]), 4)
            self.assertLess(result["metrics"]["frameConsistency"], 0.8)


    def test_duplicate_animation_frames_can_fail_strict_diversity_gate(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "duplicate-sheet.png"
            image = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
            for row in range(2):
                for col in range(2):
                    draw = ImageDraw.Draw(image)
                    x = col * 96
                    y = row * 96
                    draw.rectangle((x + 20, y + 16, x + 74, y + 82), fill=(220, 80, 40, 255))
            image.save(path)
            result = evaluate_raster_art(path, {
                "constraints": {
                    "expectedFrames": 4,
                    "frameWidth": 96,
                    "frameHeight": 96,
                    "minUniqueFrameRatio": 0.75,
                }
            })
            self.assertFalse(result["passed"])
            self.assertEqual(result["metrics"]["uniqueFrameRatio"], 0.25)
            self.assertTrue(any("unique frame ratio" in value for value in result["errors"]))

    def test_unstable_animation_center_can_fail_pivot_gate(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "drift-sheet.png"
            image = Image.new("RGBA", (192, 96), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.rectangle((8, 24, 34, 72), fill=(220, 80, 40, 255))
            draw.rectangle((96 + 58, 24, 96 + 86, 72), fill=(220, 80, 40, 255))
            image.save(path)
            result = evaluate_raster_art(path, {
                "constraints": {
                    "expectedFrames": 2,
                    "frameWidth": 96,
                    "frameHeight": 96,
                    "maxFrameCenterDrift": 0.15,
                }
            })
            self.assertFalse(result["passed"])
            self.assertGreater(result["metrics"]["maxFrameCenterDrift"], 0.15)
            self.assertTrue(any("center drift" in value for value in result["errors"]))


if __name__ == "__main__":
    unittest.main()
