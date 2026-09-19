import tempfile
import unittest
from pathlib import Path

from production_executor import (
    ProductionExecutionError,
    execute_generated_raster_job,
)


def job(target_format="png"):
    return {
        "schema": "asset-forge/production-job/v1",
        "requestId": "hero",
        "assetId": "hero-run",
        "assetType": "sprite-sheet",
        "requiresGenerator": True,
        "manifest": {
            "id": "hero-run",
            "target": {"format": target_format},
        },
    }


class ProductionExecutorTests(unittest.TestCase):
    def test_generated_png_flows_through_processing_validation_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.png"
                source.write_bytes(b"source")
                return {"success": True, "sourcePath": str(source), "backend": "pollinations"}

            def optimizer(source, output):
                output.write_bytes(b"png")
                return {"output": str(output), "bytes": 3}

            def validator(path, manifest):
                self.assertEqual(path.name, "hero-run.png")
                return {"format": "png", "bytes": 3}, []

            report = execute_generated_raster_job(
                job(),
                root,
                validator=validator,
                png_optimizer=optimizer,
                webp_encoder=lambda *a, **k: self.fail("webp encoder must not run"),
                generator=generator,
            )

            self.assertTrue(report["success"])
            self.assertEqual(report["artifact"], str(root / "hero-run.png"))
            self.assertTrue((root / "production-report.json").is_file())

    def test_webp_target_encodes_before_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.png"
                source.write_bytes(b"source")
                return {"success": True, "sourcePath": str(source)}

            def encode(source, output, **kwargs):
                self.assertTrue(kwargs["lossless"])
                output.write_bytes(b"webp")
                return {"output": str(output)}

            def validator(path, manifest):
                self.assertEqual(path.suffix, ".webp")
                return {"format": "webp"}, []

            report = execute_generated_raster_job(
                job("webp"),
                root,
                validator=validator,
                png_optimizer=lambda *a, **k: self.fail("png optimizer must not run"),
                webp_encoder=encode,
                generator=generator,
            )
            self.assertTrue(report["success"])

    def test_validation_errors_block_artifact_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.png"
                source.write_bytes(b"source")
                return {"success": True, "sourcePath": str(source)}

            def optimizer(source, output):
                output.write_bytes(b"png")
                return {}

            report = execute_generated_raster_job(
                job(),
                root,
                validator=lambda p, m: ({"format": "png"}, ["frameCount mismatch"]),
                png_optimizer=optimizer,
                webp_encoder=lambda *a, **k: None,
                generator=generator,
            )
            self.assertFalse(report["success"])
            self.assertIsNone(report["artifact"])
            self.assertEqual(report["validation"]["errors"], ["frameCount mismatch"])

    def test_non_raster_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ProductionExecutionError, "target format"):
                execute_generated_raster_job(
                    job("glb"),
                    Path(td),
                    validator=lambda *a: ({}, []),
                    png_optimizer=lambda *a: {},
                    webp_encoder=lambda *a, **k: {},
                    generator=lambda *a, **k: {},
                )


if __name__ == "__main__":
    unittest.main()
