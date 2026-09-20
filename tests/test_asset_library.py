import json
import tempfile
import unittest
from pathlib import Path

from asset_library import (
    hamming_hex,
    lookup,
    record_success,
    request_fingerprint,
    reusable_content_fingerprint,
    lookup_reusable,
    similar_entries,
    preferred_entry,
)


class AssetLibraryTests(unittest.TestCase):
    def job(self):
        return {
            "project": "deadline-zero",
            "assetId": "rex",
            "assetType": "sprite-sheet",
            "instruction": "premium survivor sprite",
            "manifest": {
                "id": "rex",
                "project": "deadline-zero",
                "type": "sprite-sheet",
                "importance": "primary",
                "source": {"mode": "generated"},
                "license": {
                    "id": "project-owned",
                    "commercialUse": True,
                    "derivatives": True,
                    "attributionRequired": False,
                },
                "target": {"format": "png"},
                "constraints": {"expectedFrames": 1},
            },
        }

    def result(self, artifact: Path, *, perceptual_hash="0f0f"):
        return {
            "success": True,
            "artifact": str(artifact),
            "generation": {
                "backend": "pollinations",
                "model": "kontext",
                "visualSimilarity": {
                    "attempts": [{"score": 0.88, "passed": True}],
                },
            },
            "validation": {
                "technicalArt": {
                    "score": 0.91,
                    "metrics": {
                        "perceptualHash": perceptual_hash,
                        "averageRgb": [80, 90, 100],
                    },
                }
            },
        }

    def test_exact_fingerprint_reuses_validated_object(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            artifact = root / "rex.png"
            artifact.write_bytes(b"validated-rex")
            fingerprint = request_fingerprint(self.job(), backend="pollinations")
            entry = record_success(
                library,
                fingerprint=fingerprint,
                job=self.job(),
                result=self.result(artifact),
            )

            hit = lookup(library, fingerprint)

            self.assertIsNotNone(hit)
            self.assertEqual(hit["sha256"], entry["sha256"])
            self.assertTrue(Path(hit["artifact"]).is_file())
            self.assertEqual(hit["version"], 1)

    def test_new_validated_generation_increments_version(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            first = root / "first.png"
            second = root / "second.png"
            first.write_bytes(b"v1")
            second.write_bytes(b"v2")
            first_fp = request_fingerprint(self.job(), backend="pollinations")
            second_job = self.job()
            second_job["instruction"] = "premium survivor sprite revised"
            second_fp = request_fingerprint(second_job, backend="pollinations")

            one = record_success(
                library,
                fingerprint=first_fp,
                job=self.job(),
                result=self.result(first),
            )
            two = record_success(
                library,
                fingerprint=second_fp,
                job=second_job,
                result=self.result(second),
            )

            self.assertEqual(one["version"], 1)
            self.assertEqual(two["version"], 2)
            payload = json.loads(library.read_text())
            self.assertEqual(len(payload["entries"]), 2)

    def test_repeated_success_record_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            artifact = root / "rex.png"
            artifact.write_bytes(b"same-generation")
            fingerprint = request_fingerprint(self.job(), backend="pollinations")

            one = record_success(
                library,
                fingerprint=fingerprint,
                job=self.job(),
                result=self.result(artifact),
            )
            two = record_success(
                library,
                fingerprint=fingerprint,
                job=self.job(),
                result=self.result(artifact),
            )

            payload = json.loads(library.read_text())
            self.assertEqual(one, two)
            self.assertEqual(one["version"], 1)
            self.assertEqual(len(payload["entries"]), 1)

    def test_reference_sha_changes_cache_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = root / "parent.png"
            ref.write_bytes(b"parent-a")
            a = request_fingerprint(
                self.job(),
                backend="pollinations",
                reference_paths=[ref],
            )
            ref.write_bytes(b"parent-b")
            b = request_fingerprint(
                self.job(),
                backend="pollinations",
                reference_paths=[ref],
            )
            self.assertNotEqual(a, b)

    def test_reusable_content_key_ignores_project_identity(self):
        first = self.job()
        second = self.job()
        second["project"] = "another-game"
        second["assetId"] = "other-rex"
        second["manifest"] = dict(second["manifest"])
        second["manifest"]["project"] = "another-game"
        second["manifest"]["id"] = "other-rex"

        a = reusable_content_fingerprint(first, backend="pollinations")
        b = reusable_content_fingerprint(second, backend="pollinations")

        self.assertEqual(a, b)

    def test_cross_project_lookup_returns_content_compatible_asset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            artifact = root / "rex.png"
            artifact.write_bytes(b"reusable-secondary")
            content_fp = reusable_content_fingerprint(
                self.job(),
                backend="pollinations",
            )
            record_success(
                library,
                fingerprint=request_fingerprint(
                    self.job(),
                    backend="pollinations",
                ),
                content_fingerprint=content_fp,
                job=self.job(),
                result=self.result(artifact),
            )

            hit = lookup_reusable(library, content_fp)

            self.assertIsNotNone(hit)
            self.assertEqual(hit["contentFingerprint"], content_fp)

    def test_higher_quality_near_duplicate_becomes_preferred_version(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            first = root / "first.png"
            second = root / "second.png"
            first.write_bytes(b"v1")
            second.write_bytes(b"v2")

            low = self.result(first, perceptual_hash="0f0f")
            low["validation"]["technicalArt"]["score"] = 0.60
            low["generation"]["visualSimilarity"]["attempts"][-1]["score"] = 0.65
            one = record_success(
                library,
                fingerprint="a" * 64,
                job=self.job(),
                result=low,
            )

            high = self.result(second, perceptual_hash="0f0e")
            high["validation"]["technicalArt"]["score"] = 0.95
            high["generation"]["visualSimilarity"]["attempts"][-1]["score"] = 0.92
            two = record_success(
                library,
                fingerprint="b" * 64,
                job=self.job(),
                result=high,
            )

            payload = json.loads(library.read_text())
            old = next(item for item in payload["entries"] if item["sha256"] == one["sha256"])
            new = next(item for item in payload["entries"] if item["sha256"] == two["sha256"])
            self.assertFalse(old["preferred"])
            self.assertEqual(old["supersededBy"], new["sha256"])
            self.assertTrue(new["preferred"])
            self.assertIsNone(new["duplicateOf"])
            self.assertGreater(new["compositeQuality"], old["compositeQuality"])
            self.assertEqual(preferred_entry(
                library,
                project="deadline-zero",
                asset_id="rex",
            )["sha256"], new["sha256"])

    def test_lower_quality_near_duplicate_is_marked_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            first = root / "first.png"
            second = root / "second.png"
            first.write_bytes(b"v1")
            second.write_bytes(b"v2")

            high = self.result(first, perceptual_hash="0f0f")
            high["validation"]["technicalArt"]["score"] = 0.95
            high["generation"]["visualSimilarity"]["attempts"][-1]["score"] = 0.93
            one = record_success(
                library,
                fingerprint="c" * 64,
                job=self.job(),
                result=high,
            )

            low = self.result(second, perceptual_hash="0f0e")
            low["validation"]["technicalArt"]["score"] = 0.55
            low["generation"]["visualSimilarity"]["attempts"][-1]["score"] = 0.58
            two = record_success(
                library,
                fingerprint="d" * 64,
                job=self.job(),
                result=low,
            )

            self.assertFalse(two["preferred"])
            self.assertEqual(two["duplicateOf"], one["sha256"])
            self.assertEqual(two["perceptualDistance"], 1)

    def test_perceptual_deduplication_returns_near_matches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = root / "library.json"
            artifact = root / "rex.png"
            artifact.write_bytes(b"rex")
            fp = request_fingerprint(self.job())
            record_success(
                library,
                fingerprint=fp,
                job=self.job(),
                result=self.result(artifact, perceptual_hash="0f0f"),
            )

            rows = similar_entries(
                library,
                project="deadline-zero",
                asset_type="sprite-sheet",
                perceptual_hash="0f0e",
                max_hamming=2,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["perceptualDistance"], 1)
            self.assertEqual(hamming_hex("0f0f", "0f0e"), 1)


if __name__ == "__main__":
    unittest.main()
