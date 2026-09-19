import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import asset_forge


ROOT = Path(__file__).resolve().parents[1]


class FulfillCommandTests(unittest.TestCase):
    def test_parser_accepts_end_to_end_fulfill_command(self):
        args = asset_forge.parser().parse_args(
            [
                "fulfill",
                "examples/production-request.json",
                "--output-dir",
                "build/visual-job",
                "--timeout",
                "45",
            ]
        )
        self.assertEqual(args.command, "fulfill")
        self.assertEqual(args.request, Path("examples/production-request.json"))
        self.assertEqual(args.output_dir, Path("build/visual-job"))
        self.assertEqual(args.timeout, 45.0)

    def test_production_inputs_are_persisted_for_handoff_and_audit(self):
        request = asset_forge.load_json(ROOT / "examples/production-request.json")
        plan = asset_forge.build_plan(request["manifest"], ROOT)
        job = asset_forge.build_production_job(request, plan)

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            asset_forge._write_production_inputs(out, job)

            written_job = json.loads((out / "production-job.json").read_text())
            written_manifest = json.loads((out / "asset-manifest.json").read_text())
            written_plan = json.loads((out / "production-plan.json").read_text())

        self.assertEqual(written_job["requestId"], request["requestId"])
        self.assertEqual(written_manifest["id"], request["manifest"]["id"])
        self.assertEqual(written_plan["assetId"], request["manifest"]["id"])

    def test_compiled_job_routes_raster_to_generated_raster_executor(self):
        job = {
            "schema": "asset-forge/production-job/v1",
            "requestId": "sprite-job",
            "assetId": "hero",
            "assetType": "sprite-sheet",
            "requiresGenerator": True,
            "manifest": {"target": {"format": "png"}},
        }
        expected = {"success": True, "artifact": "hero.png"}

        with patch(
            "asset_forge.execute_generated_raster_job",
            return_value=expected,
        ) as execute:
            result = asset_forge.execute_compiled_production_job(
                job,
                Path("build/job"),
                backend="pollinations",
                model="flux",
                timeout_seconds=30,
            )

        self.assertEqual(result, expected)
        execute.assert_called_once()
        self.assertEqual(execute.call_args.args[0], job)
        self.assertEqual(execute.call_args.args[1], Path("build/job"))
        self.assertEqual(execute.call_args.kwargs["backend"], "pollinations")
        self.assertEqual(execute.call_args.kwargs["model"], "flux")
        self.assertEqual(execute.call_args.kwargs["timeout_seconds"], 30)


    def test_godot_sprite_sheet_gets_engine_handoff(self):
        job = {
            "assetId": "hero",
            "assetType": "sprite-sheet",
            "manifest": {
                "id": "hero",
                "target": {"engine": "godot4", "format": "png"},
                "constraints": {"frameWidth": 32, "frameHeight": 32},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            artifact = out / "hero.png"
            artifact.write_bytes(b"PNG")
            report = out / "production-report.json"
            report.write_text("{}\n", encoding="utf-8")
            result = {
                "success": True,
                "artifact": str(artifact),
                "reportPath": str(report),
            }
            atlas = {
                "assetId": "hero",
                "image": "hero.png",
                "imageWidth": 32,
                "imageHeight": 32,
                "columns": 1,
                "rows": 1,
                "frameCount": 1,
                "frames": [
                    {"index": 0, "x": 0, "y": 0, "width": 32, "height": 32}
                ],
            }

            with patch("asset_forge.build_atlas_manifest", return_value=atlas), \
                 patch("asset_forge.write_spriteframes") as write:
                enriched = asset_forge._enrich_engine_handoff(job, result, out)

            self.assertTrue(enriched["engineHandoff"]["ready"])
            self.assertEqual(enriched["engineHandoff"]["type"], "spriteframes")
            self.assertTrue((out / "atlas-metadata.json").is_file())
            write.assert_called_once()
            persisted = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(persisted["engineHandoff"]["engine"], "godot4")

    def test_godot_3d_gets_handoff_and_import_validation(self):
        job = {
            "assetId": "crate",
            "assetType": "prop",
            "manifest": {
                "id": "crate",
                "project": "demo",
                "type": "prop",
                "importance": "primary",
                "source": {"mode": "generated"},
                "license": {
                    "id": "project-owned",
                    "commercialUse": True,
                    "derivatives": True,
                },
                "target": {"engine": "godot4", "format": "glb"},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            artifact = out / "crate.glb"
            artifact.write_bytes(b"glTF")
            report = out / "production-report.json"
            report.write_text("{}\n", encoding="utf-8")
            result = {
                "success": True,
                "artifact": str(artifact),
                "reportPath": str(report),
                "validation": {"godot": {"ready": True}},
            }
            handoff = {"projectDir": str(out / "godot-handoff")}

            with patch(
                "asset_forge.prepare_godot_handoff",
                return_value=handoff,
            ) as prepare, patch(
                "asset_forge.validate_godot_handoff",
                return_value={"available": False, "passed": None},
            ) as validate:
                enriched = asset_forge._enrich_engine_handoff(job, result, out)

            self.assertTrue(enriched["success"])
            self.assertTrue(enriched["engineHandoff"]["ready"])
            self.assertEqual(enriched["engineHandoff"]["type"], "3d-project")
            prepare.assert_called_once()
            validate.assert_called_once()

if __name__ == "__main__":
    unittest.main()
