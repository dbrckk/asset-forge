import unittest
from pathlib import Path

import asset_forge
from production_contract import (
    JOB_SCHEMA,
    REPORT_SCHEMA,
    REQUEST_SCHEMA,
    build_production_job,
    validate_production_report,
    validate_production_request,
)


class ProductionContractTests(unittest.TestCase):
    def request(self):
        manifest = asset_forge.load_json(Path(__file__).resolve().parents[1] / "examples/asset-manifest.json")
        manifest["source"] = {"mode": "generated"}
        return {
            "schema": REQUEST_SCHEMA,
            "requestId": "deadline-zero-player-sprite",
            "instruction": "Create a production-ready player sprite sheet.",
            "manifest": manifest,
            "delivery": {"engine": "godot4", "outputDir": "build/player"},
        }

    def test_valid_request_builds_machine_readable_job(self):
        request = self.request()
        self.assertEqual(
            validate_production_request(request, asset_forge.validate_manifest),
            [],
        )
        plan = asset_forge.build_plan(request["manifest"], Path(__file__).resolve().parents[1])
        job = build_production_job(request, plan)
        self.assertEqual(job["schema"], JOB_SCHEMA)
        self.assertEqual(job["status"], "ready")
        self.assertTrue(job["requiresGenerator"])
        self.assertEqual(job["execution"]["strategy"], "generate-then-process")
        self.assertEqual(job["delivery"]["engine"], "godot4")
        self.assertEqual(job["delivery"]["reportPath"], "build/player/production-report.json")

    def test_valid_production_report_contract(self):
        report = {
            "schema": REPORT_SCHEMA,
            "requestId": "request-1",
            "assetId": "hero",
            "assetType": "sprite-sheet",
            "success": True,
            "generation": {"backend": "pollinations"},
            "validation": {"errors": [], "warnings": []},
            "artifact": "build/hero.png",
            "engineHandoff": {"engine": "godot4", "ready": True},
        }
        self.assertEqual(validate_production_report(report), [])

    def test_failed_report_cannot_claim_an_artifact(self):
        report = {
            "schema": REPORT_SCHEMA,
            "requestId": "request-1",
            "assetId": "hero",
            "assetType": "sprite-sheet",
            "success": False,
            "generation": {},
            "validation": {"errors": ["invalid"]},
            "artifact": "build/hero.png",
        }
        self.assertIn(
            "artifact: must be null when success=false",
            validate_production_report(report),
        )

    def test_invalid_request_is_rejected(self):
        request = self.request()
        request["instruction"] = ""
        request["manifest"]["license"]["commercialUse"] = False
        errors = validate_production_request(request, asset_forge.validate_manifest)
        self.assertIn("instruction: non-empty string required", errors)
        self.assertIn(
            "manifest.license.commercialUse: must be true for production-ready assets",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
