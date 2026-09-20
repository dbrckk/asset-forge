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


if __name__ == "__main__":
    unittest.main()
