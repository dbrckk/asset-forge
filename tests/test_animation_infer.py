import unittest

from animation_infer import infer_animations


class AnimationInferTests(unittest.TestCase):
    def test_groups_numbered_filenames(self):
        metadata = {
            "frames": [
                {"index": 0, "name": "idle_02.png"},
                {"index": 1, "name": "run_01.png"},
                {"index": 2, "name": "idle_01.png"},
                {"index": 3, "name": "run_02.png"},
            ]
        }

        result = infer_animations(metadata, default_fps=8)
        animations = {item["name"]: item for item in result["animations"]}

        self.assertEqual(animations["idle"]["frames"], [2, 0])
        self.assertEqual(animations["run"]["frames"], [1, 3])
        self.assertEqual(animations["idle"]["fps"], 8.0)

    def test_uses_stem_when_no_numeric_suffix(self):
        metadata = {
            "frames": [
                {"index": 0, "name": "hurt.png"},
                {"index": 1, "name": "hurt.png"},
            ]
        }

        result = infer_animations(metadata)

        self.assertEqual(result["animations"][0]["name"], "hurt")
        self.assertEqual(result["animations"][0]["frames"], [0, 1])

    def test_missing_names_fall_back_to_default(self):
        metadata = {
            "frames": [
                {"index": 0},
                {"index": 1},
            ]
        }

        result = infer_animations(metadata, default_loop=False)

        self.assertEqual(result["animations"][0]["name"], "default")
        self.assertFalse(result["animations"][0]["loop"])

    def test_rejects_invalid_fps(self):
        with self.assertRaisesRegex(ValueError, "default_fps must be > 0"):
            infer_animations({"frames": [{"index": 0}]}, default_fps=0)


if __name__ == "__main__":
    unittest.main()
