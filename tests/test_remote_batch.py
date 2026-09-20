import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from remote_batch import run


def request(request_id, asset_id, expected_frames=1):
    return {
        "schema": "asset-forge/production-request/v1",
        "requestId": request_id,
        "instruction": "premium game asset",
        "manifest": {
            "schema": "asset-forge/manifest/v1",
            "id": asset_id,
            "project": "deadline-zero",
            "type": "sprite-sheet",
            "importance": "primary",
            "source": {"mode": "generated"},
            "license": {
                "id": "project-owned",
                "commercialUse": True,
                "derivatives": True,
            },
            "target": {"format": "png", "engine": "libgdx"},
            "constraints": {
                "frameWidth": 96,
                "frameHeight": 96,
                "expectedFrames": expected_frames,
            },
        },
    }


class RemoteBatchTests(unittest.TestCase):
    def test_dependency_order_and_reference_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = root / "spec.json"
            spec.write_text(json.dumps({"items": [
                {
                    "id": "run",
                    "depends_on": ["hero"],
                    "request": request("run-request", "run", 8),
                    "target_path": "assets/art/pilot/run.png",
                },
                {
                    "id": "hero",
                    "request": request("hero-request", "hero"),
                    "target_path": "assets/art/pilot/hero.png",
                },
            ]}))
            commands = []

            def fake_run(cmd, **kwargs):
                commands.append(list(cmd))
                request_path = Path(cmd[cmd.index("fulfill") + 1])
                payload = json.loads(request_path.read_text())
                output = Path(cmd[cmd.index("--output-dir") + 1])
                output.mkdir(parents=True, exist_ok=True)
                artifact = output / (payload["manifest"]["id"] + ".png")
                artifact.write_bytes(payload["manifest"]["id"].encode())
                (output / "production-report.json").write_text(json.dumps({
                    "success": True,
                    "artifact": str(artifact),
                    "generation": {
                        "visualSimilarity": (
                            {
                                "passed": True,
                                "attempts": [{"score": 0.8, "passed": True}],
                            }
                            if payload["manifest"]["id"] == "run"
                            else None
                        )
                    },
                }))
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""
                return Result()

            with patch("remote_batch.subprocess.run", side_effect=fake_run):
                result = run(spec, root / "out")

            self.assertEqual(result["execution_order"], ["hero", "run"])
            self.assertEqual(result["quality_summary"]["checked"], 1)
            self.assertEqual(result["quality_summary"]["minimum_score"], 0.8)
            self.assertNotIn("--reference", commands[0])
            self.assertIn("--reference", commands[1])
            reference = Path(commands[1][commands[1].index("--reference") + 1])
            self.assertEqual(reference.name, "hero.png")
            self.assertTrue((root / "out" / "batch-result.json").is_file())

    def test_remote_batch_propagates_library_version_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = root / "spec.json"
            spec.write_text(json.dumps({"items": [{
                "id": "hero",
                "request": request("hero-request", "hero"),
                "target_path": "assets/art/pilot/hero.png",
            }]}))

            def fake_run(cmd, **kwargs):
                request_path = Path(cmd[cmd.index("fulfill") + 1])
                payload = json.loads(request_path.read_text())
                output = Path(cmd[cmd.index("--output-dir") + 1])
                output.mkdir(parents=True, exist_ok=True)
                artifact = output / (payload["manifest"]["id"] + ".png")
                artifact.write_bytes(b"hero")
                (output / "production-report.json").write_text(json.dumps({
                    "success": True,
                    "artifact": str(artifact),
                    "generation": {},
                    "validation": {},
                    "library": {
                        "schema": "asset-forge/library-receipt/v1",
                        "cacheHit": False,
                        "reuseScope": "new",
                        "entry": {
                            "version": 3,
                            "preferred": True,
                            "duplicateOf": None,
                            "compositeQuality": 0.91,
                        },
                    },
                }))
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""
                return Result()

            with patch("remote_batch.subprocess.run", side_effect=fake_run):
                result = run(spec, root / "out")

            library = result["items"][0]["library"]
            self.assertEqual(library["entry"]["version"], 3)
            self.assertTrue(library["entry"]["preferred"])
            self.assertEqual(library["entry"]["compositeQuality"], 0.91)


if __name__ == "__main__":
    unittest.main()
