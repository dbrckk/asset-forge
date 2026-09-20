import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from semantic_art_review import SemanticArtReviewError, review_raster_art


class SemanticArtReviewTests(unittest.TestCase):
    def manifest(self, *, required=False):
        return {
            "type": "sprite-sheet",
            "importance": "primary",
            "constraints": {
                "semanticArtReview": True,
                "semanticArtReviewRequired": required,
                "semanticQualityMin": 0.68,
            },
        }

    def test_unavailable_provider_is_non_blocking_when_optional(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "asset.png"
            image.write_bytes(b"png")
            with patch("semantic_art_review.shutil.which", return_value=None):
                result = review_raster_art(
                    image,
                    self.manifest(),
                    environ={},
                    home=root,
                )
        self.assertFalse(result["available"])
        self.assertIsNone(result["passed"])
        self.assertEqual(result["reason"], "provider_unavailable")

    def test_required_provider_fails_closed_when_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "asset.png"
            image.write_bytes(b"png")
            with patch("semantic_art_review.shutil.which", return_value=None):
                with self.assertRaisesRegex(
                    SemanticArtReviewError,
                    "authenticated polli CLI",
                ):
                    review_raster_art(
                        image,
                        self.manifest(required=True),
                        environ={},
                        home=root,
                    )

    def test_structured_vision_review_is_scored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "asset.png"
            image.write_bytes(b"png")
            credentials = root / ".pollinations"
            credentials.mkdir()
            (credentials / "credentials.json").write_text("{}")
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                class Result:
                    returncode = 0
                    stderr = ""
                    stdout = ""
                result = Result()
                if command[1] == "upload":
                    result.stdout = json.dumps({
                        "url": "https://media.pollinations.ai/example"
                    })
                else:
                    result.stdout = json.dumps({
                        "content": json.dumps({
                            "overall": 0.84,
                            "anatomy": 0.82,
                            "artifacts": 0.9,
                            "textReadability": 0.8,
                            "styleConsistency": 0.86,
                            "issues": ["minor hand detail"],
                        })
                    })
                return result

            with patch(
                "semantic_art_review.shutil.which",
                return_value="/usr/bin/polli",
            ):
                result = review_raster_art(
                    image,
                    self.manifest(),
                    runner=runner,
                    environ={},
                    home=root,
                )

        self.assertTrue(result["available"])
        self.assertTrue(result["passed"])
        self.assertEqual(result["scores"]["overall"], 0.84)
        self.assertEqual(len(calls), 2)
        self.assertIn("--image", calls[1])

    def test_low_semantic_score_fails_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "asset.png"
            image.write_bytes(b"png")
            credentials = root / ".pollinations"
            credentials.mkdir()
            (credentials / "credentials.json").write_text("{}")

            def runner(command, **kwargs):
                class Result:
                    returncode = 0
                    stderr = ""
                    stdout = ""
                result = Result()
                if command[1] == "upload":
                    result.stdout = '{"url":"https://media.pollinations.ai/example"}'
                else:
                    result.stdout = json.dumps({
                        "overall": 0.41,
                        "anatomy": 0.35,
                        "artifacts": 0.45,
                        "textReadability": 0.7,
                        "styleConsistency": 0.5,
                        "issues": ["broken anatomy"],
                    })
                return result

            with patch(
                "semantic_art_review.shutil.which",
                return_value="/usr/bin/polli",
            ):
                result = review_raster_art(
                    image,
                    self.manifest(),
                    runner=runner,
                    environ={},
                    home=root,
                )

        self.assertFalse(result["passed"])
        self.assertEqual(result["issues"], ["broken anatomy"])


if __name__ == "__main__":
    unittest.main()
