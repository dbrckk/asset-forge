import json
import tempfile
import unittest
from pathlib import Path

from backend_history import (
    SCHEMA,
    backend_score,
    choose_backend,
    empty_history,
    load_history,
    record_generation_result,
)


class BackendHistoryTests(unittest.TestCase):
    def test_missing_or_invalid_history_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing.json"
            self.assertEqual(load_history(missing), empty_history())

            invalid = root / "invalid.json"
            invalid.write_text("{not-json", encoding="utf-8")
            self.assertEqual(load_history(invalid), empty_history())

    def test_default_order_is_preserved_without_enough_samples(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            self.assertEqual(
                choose_backend(
                    ["cloudflare", "kaggle-qwen"],
                    history_path=path,
                    default_order=["cloudflare", "kaggle-qwen"],
                ),
                "cloudflare",
            )

    def test_repeated_cloudflare_failures_move_auto_route_to_kaggle(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            history = {
                "schema": SCHEMA,
                "backends": {
                    "cloudflare": {
                        "attempts": 3,
                        "successes": 0,
                        "failures": 3,
                        "qualitySamples": 0,
                        "qualitySum": 0.0,
                    },
                    "kaggle-qwen": {
                        "attempts": 3,
                        "successes": 3,
                        "failures": 0,
                        "qualitySamples": 3,
                        "qualitySum": 2.7,
                    },
                },
            }
            path.write_text(json.dumps(history), encoding="utf-8")

            self.assertEqual(
                choose_backend(
                    ["cloudflare", "kaggle-qwen"],
                    history_path=path,
                    default_order=["cloudflare", "kaggle-qwen"],
                ),
                "kaggle-qwen",
            )

    def test_reliable_observed_cloudflare_stays_ahead_of_unknown_kaggle(self):
        history = {
            "schema": SCHEMA,
            "backends": {
                "cloudflare": {
                    "attempts": 3,
                    "successes": 3,
                    "failures": 0,
                    "qualitySamples": 0,
                    "qualitySum": 0.0,
                }
            },
        }
        cloudflare = backend_score(history, "cloudflare", prior=1.0)
        unknown_kaggle = backend_score(history, "kaggle-qwen", prior=0.98)
        self.assertGreater(cloudflare, unknown_kaggle)

    def test_record_generation_result_tracks_fallback_and_quality(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            result = {
                "backend": "kaggle-qwen",
                "fallbacks": [{
                    "from": "cloudflare",
                    "to": "kaggle-qwen",
                    "reason": "cloudflare-generation-error",
                    "attempt": 1,
                }],
                "visualSimilarity": {
                    "attempts": [{"score": 0.8, "passed": True}],
                },
                "technicalQuality": {
                    "attempts": [{"score": 0.9, "passed": True}],
                },
            }

            history = record_generation_result(path, result)

            cloudflare = history["backends"]["cloudflare"]
            self.assertEqual(cloudflare["attempts"], 1)
            self.assertEqual(cloudflare["failures"], 1)
            self.assertEqual(cloudflare["fallbacksFrom"], 1)

            kaggle = history["backends"]["kaggle-qwen"]
            self.assertEqual(kaggle["attempts"], 1)
            self.assertEqual(kaggle["successes"], 1)
            self.assertEqual(kaggle["fallbacksTo"], 1)
            self.assertEqual(kaggle["qualitySamples"], 1)
            self.assertAlmostEqual(kaggle["qualitySum"], 0.85)

            persisted = load_history(path)
            self.assertEqual(persisted, history)

    def test_record_generation_result_tracks_regeneration_pressure(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            history = record_generation_result(path, {
                "backend": "cloudflare",
                "fallbacks": [],
                "visualSimilarity": {
                    "attempts": [
                        {"score": 0.4, "passed": False},
                        {"score": 0.6, "passed": False},
                        {"score": 0.82, "passed": True},
                    ],
                },
                "technicalQuality": {
                    "attempts": [
                        {"score": 0.5, "passed": False},
                        {"score": 0.9, "passed": True},
                    ],
                },
            })

            stats = history["backends"]["cloudflare"]
            self.assertEqual(stats["attempts"], 1)
            self.assertEqual(stats["successes"], 1)
            self.assertEqual(stats["regenerations"], 2)

    def test_3d_result_learns_from_nested_reference_generation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            history = record_generation_result(path, {
                "backend": "kaggle-triposr",
                "fallbacks": [],
                "referenceGeneration": {
                    "success": True,
                    "backend": "kaggle-qwen",
                    "visualSimilarity": {
                        "attempts": [{"score": 0.88, "passed": True}],
                    },
                    "technicalQuality": {
                        "attempts": [{"score": 0.92, "passed": True}],
                    },
                },
            })

            triposr = history["backends"]["kaggle-triposr"]
            self.assertEqual(triposr["successes"], 1)

            raster = history["backends"]["kaggle-qwen"]
            self.assertEqual(raster["attempts"], 1)
            self.assertEqual(raster["successes"], 1)
            self.assertEqual(raster["qualitySamples"], 1)
            self.assertAlmostEqual(raster["qualitySum"], 0.9)

    def test_vector_result_records_underlying_raster_backend(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            history = record_generation_result(path, {
                "backend": "vtracer",
                "fallbacks": [],
                "metadata": {"rasterBackend": "cloudflare"},
                "visualSimilarity": {"attempts": []},
                "technicalQuality": {"attempts": []},
            })

            self.assertEqual(history["backends"]["vtracer"]["successes"], 1)
            self.assertEqual(history["backends"]["cloudflare"]["successes"], 1)


if __name__ == "__main__":
    unittest.main()
