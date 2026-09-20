import tempfile
import unittest
from pathlib import Path

from visual_similarity import compare_visuals


class VisualSimilarityTests(unittest.TestCase):
    def test_identical_images_score_higher_than_different_images(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parent = root / "parent.png"
            same = root / "same.png"
            different = root / "different.png"

            Image.new("RGBA", (32, 32), (220, 40, 40, 255)).save(parent)
            Image.new("RGBA", (32, 32), (220, 40, 40, 255)).save(same)
            Image.new("RGBA", (32, 32), (20, 40, 220, 255)).save(different)

            same_score = compare_visuals(parent, same)["score"]
            different_score = compare_visuals(parent, different)["score"]

            self.assertGreaterEqual(same_score, 0.99)
            self.assertGreater(same_score, different_score)
            self.assertLess(different_score, 0.85)


    def test_subject_repositioning_stays_similar(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parent = root / "parent.png"
            moved = root / "moved.png"

            a = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(a)
            draw.rectangle((8, 16, 28, 48), fill=(220, 60, 40, 255))
            a.save(parent)

            b = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(b)
            draw.rectangle((30, 10, 50, 42), fill=(220, 60, 40, 255))
            b.save(moved)

            score = compare_visuals(parent, moved)["score"]
            self.assertGreaterEqual(score, 0.80)

    def test_shape_and_palette_change_is_penalized(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parent = root / "parent.png"
            changed = root / "changed.png"

            a = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(a)
            draw.rectangle((12, 12, 44, 52), fill=(220, 60, 40, 255))
            a.save(parent)

            b = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(b)
            draw.ellipse((8, 8, 56, 56), fill=(30, 70, 220, 255))
            b.save(changed)

            score = compare_visuals(parent, changed)["score"]
            self.assertLess(score, 0.75)


    def test_sprite_sheet_scoring_is_frame_aware(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parent = root / "parent-sheet.png"
            child = root / "child-sheet.png"

            p = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(p)
            for i in range(4):
                x = i * 32
                draw.rectangle((x + 6, 6, x + 24, 26), fill=(210, 60, 40, 255))
            p.save(parent)

            q = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(q)
            for i in range(4):
                x = i * 32
                offset = (i % 2) * 3
                draw.rectangle((x + 6 + offset, 5, x + 24 + offset, 27), fill=(210, 60, 40, 255))
            q.save(child)

            result = compare_visuals(parent, child)
            self.assertEqual(result["parentFrameCount"], 4)
            self.assertEqual(result["childFrameCount"], 4)
            self.assertEqual(len(result["frameScores"]), 4)
            self.assertGreaterEqual(result["score"], 0.75)


if __name__ == "__main__":
    unittest.main()
