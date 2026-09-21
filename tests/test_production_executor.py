import tempfile
import unittest
from pathlib import Path

from production_executor import (
    ProductionExecutionError,
    execute_generated_raster_job,
    execute_generated_vector_job,
    execute_generated_3d_job,
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
            self.assertEqual(report["provenance"]["source"]["mode"], None)
            self.assertTrue((root / "production-report.json").is_file())

    def test_raster_report_exposes_backend_routing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.png"
                source.write_bytes(b"source")
                return {
                    "success": True,
                    "sourcePath": str(source),
                    "backend": "kaggle-qwen",
                    "requestedBackend": "auto",
                    "initialBackend": "cloudflare",
                    "fallbacks": [{
                        "from": "cloudflare",
                        "to": "kaggle-qwen",
                        "reason": "cloudflare-generation-error",
                        "attempt": 1,
                    }],
                }

            report = execute_generated_raster_job(
                job(),
                root,
                validator=lambda path, manifest: ({"format": "png"}, []),
                png_optimizer=lambda source, output: (
                    output.write_bytes(b"png") and {"output": str(output)}
                ),
                webp_encoder=lambda *a, **k: self.fail("webp encoder must not run"),
                generator=generator,
                art_quality_reporter=lambda path, manifest: {
                    "errors": [],
                    "warnings": [],
                },
            )

            self.assertEqual(report["routing"]["requestedBackend"], "auto")
            self.assertEqual(report["routing"]["initialBackend"], "cloudflare")
            self.assertEqual(report["routing"]["finalBackend"], "kaggle-qwen")
            self.assertEqual(report["routing"]["fallbackCount"], 1)
            self.assertEqual(
                report["routing"]["fallbacks"][0]["reason"],
                "cloudflare-generation-error",
            )

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

    def test_generated_vector_is_sanitized_normalized_and_validated(self):
        vector_job = job("svg")
        vector_job["assetType"] = "icon"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.svg"
                source.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64"/></svg>',
                    encoding="utf-8",
                )
                return {"success": True, "sourcePath": str(source)}

            def sanitizer(source, output):
                output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                return {"output": str(output)}

            def normalizer(source, output):
                output.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64"/></svg>',
                    encoding="utf-8",
                )
                return {"output": str(output), "viewBox": "0 0 64 64"}

            def profile_validator(path, profile):
                self.assertEqual(profile, "icon")
                return {"viewBox": "0 0 64 64"}, [], []

            report = execute_generated_vector_job(
                vector_job,
                root,
                sanitizer=sanitizer,
                normalizer=normalizer,
                profile_validator=profile_validator,
                generic_validator=lambda p: self.fail("generic validator must not run"),
                generator=generator,
            )

            self.assertTrue(report["success"])
            self.assertEqual(report["artifact"], str(root / "hero-run.svg"))
            self.assertEqual(report["validation"]["profile"], "icon")

    def test_vector_validation_errors_block_promotion(self):
        vector_job = job("svg")
        vector_job["assetType"] = "logo"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.svg"
                source.write_text("<svg/>", encoding="utf-8")
                return {"success": True, "sourcePath": str(source)}

            def copy_step(source, output):
                output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                return {"output": str(output)}

            report = execute_generated_vector_job(
                vector_job,
                root,
                sanitizer=copy_step,
                normalizer=copy_step,
                profile_validator=lambda p, profile: ({}, ["logo too complex"], []),
                generic_validator=lambda p: ({}, [], []),
                generator=generator,
            )

            self.assertFalse(report["success"])
            self.assertIsNone(report["artifact"])
            self.assertEqual(report["validation"]["errors"], ["logo too complex"])

    def test_generated_3d_flows_through_profile_quality_and_godot_gates(self):
        three_d = job("glb")
        three_d["assetType"] = "prop"
        three_d["manifest"]["target"]["engine"] = "godot4"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {
                    "success": True,
                    "sourcePath": str(source),
                    "model": "microsoft/trellis-2",
                }

            def profile_validator(path, profile):
                self.assertEqual(profile, "prop")
                self.assertEqual(path.name, "hero-run.glb")
                return {"container": "glb"}, [], ["minor structural warning"]

            def quality(path, profile):
                return {
                    "evaluation": {
                        "passed": True,
                        "errors": [],
                        "warnings": ["quality warning"],
                    }
                }

            def godot(path, profile):
                self.assertEqual(profile, "prop")
                return {"ready": True, "errors": [], "warnings": []}

            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: self.fail("generic validator must not run"),
                profile_validator=profile_validator,
                quality_reporter=quality,
                godot_delivery_reporter=godot,
                generator=generator,
            )

            self.assertTrue(report["success"])
            self.assertEqual(report["artifact"], str(root / "hero-run.glb"))
            self.assertIn("quality warning", report["validation"]["warnings"])
            self.assertTrue((root / "production-report.json").is_file())

    def test_3d_backend_and_model_are_forwarded_to_generator(self):
        three_d = job("glb")
        three_d["assetType"] = "prop"
        seen = {}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                seen.update(kwargs)
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {
                    "success": True,
                    "backend": kwargs.get("backend"),
                    "model": kwargs.get("model"),
                    "sourcePath": str(source),
                }

            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: ({}, [], []),
                profile_validator=lambda p, profile: ({}, [], []),
                quality_reporter=lambda p, profile: {
                    "evaluation": {"passed": True, "errors": [], "warnings": []}
                },
                godot_delivery_reporter=lambda p, profile: {
                    "ready": True,
                    "errors": [],
                    "warnings": [],
                },
                generator=generator,
                backend="kaggle-triposr",
                model="stabilityai/TripoSR",
                resolution="medium",
                timeout_seconds=321,
            )

            self.assertTrue(report["success"])
            self.assertEqual(seen["backend"], "kaggle-triposr")
            self.assertEqual(seen["model"], "stabilityai/TripoSR")
            self.assertEqual(seen["resolution"], "medium")
            self.assertEqual(seen["timeout_seconds"], 321)
            self.assertEqual(
                report["routing"]["finalBackend"],
                "kaggle-triposr",
            )

    def test_godot_3d_emits_runtime_plan_sidecar(self):
        three_d = job("glb")
        three_d["assetType"] = "prop"
        three_d["manifest"]["target"]["engine"] = "godot4"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {"success": True, "sourcePath": str(source)}

            runtime_plan = {
                "schema": "asset-forge/runtime-3d-plan/v1",
                "profile": "prop",
                "lod": {"required": False, "levels": []},
                "collision": {"strategy": "convex-or-simplified-static"},
                "pbr": {"allMaterialsPbr": True},
                "recommendations": [],
            }
            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: ({}, [], []),
                profile_validator=lambda p, profile: ({}, [], []),
                quality_reporter=lambda p, profile: {
                    "evaluation": {"passed": True, "errors": [], "warnings": []}
                },
                godot_delivery_reporter=lambda p, profile: {
                    "ready": True,
                    "errors": [],
                    "warnings": [],
                    "scene": {"collisionNodes": 1},
                    "runtimePlan": runtime_plan,
                },
                generator=generator,
            )

            sidecars = [Path(value) for value in report["additionalArtifacts"] if value.endswith(".runtime-3d.json")]
            self.assertEqual(len(sidecars), 1)
            self.assertTrue(sidecars[0].is_file())
            self.assertEqual(
                __import__("json").loads(sidecars[0].read_text())["collision"]["strategy"],
                "convex-or-simplified-static",
            )

    def test_generated_character_3d_fails_when_profile_quality_fails(self):
        three_d = job("glb")
        three_d["assetType"] = "character-3d"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {"success": True, "sourcePath": str(source)}

            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: ({}, [], []),
                profile_validator=lambda p, profile: ({}, [], []),
                quality_reporter=lambda p, profile: {
                    "evaluation": {
                        "passed": False,
                        "errors": ["character joint or skin requirements not met"],
                        "warnings": [],
                    }
                },
                godot_delivery_reporter=lambda p, profile: {"ready": True, "errors": [], "warnings": []},
                generator=generator,
            )

            self.assertFalse(report["success"])
            self.assertIsNone(report["artifact"])
            self.assertIn(
                "character joint or skin requirements not met",
                report["validation"]["errors"],
            )

    def test_provided_png_source_skips_generator_and_is_staged(self):
        provided_job = job()
        provided_job["requiresGenerator"] = False

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as source_td:
            root = Path(td)
            source = Path(source_td) / "licensed.png"
            source.write_bytes(b"source")

            def optimizer(input_path, output_path):
                self.assertEqual(input_path.name, "provided-source.png")
                output_path.write_bytes(b"png")
                return {"output": str(output_path)}

            report = execute_generated_raster_job(
                provided_job,
                root,
                validator=lambda path, manifest: ({"format": "png"}, []),
                png_optimizer=optimizer,
                webp_encoder=lambda *a, **k: self.fail("webp must not run"),
                generator=lambda *a, **k: self.fail("generator must not run"),
                source_path=source,
            )

            self.assertTrue(report["success"])
            self.assertEqual(report["generation"]["backend"], "provided")
            self.assertIn("provenance", report)
            self.assertTrue((root / "provided-source.png").is_file())
            self.assertEqual(report["artifact"], str(root / "hero-run.png"))

    def test_provided_source_symlink_is_rejected(self):
        provided_job = job()
        provided_job["requiresGenerator"] = False

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as source_td:
            root = Path(td)
            real = Path(source_td) / "real.png"
            real.write_bytes(b"source")
            link = Path(source_td) / "linked.png"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")

            with self.assertRaisesRegex(
                ProductionExecutionError,
                "must not be a symlink",
            ):
                execute_generated_raster_job(
                    provided_job,
                    root,
                    validator=lambda p, m: ({}, []),
                    png_optimizer=lambda *a: {},
                    webp_encoder=lambda *a, **k: {},
                    generator=lambda *a, **k: self.fail("generator must not run"),
                    source_path=link,
                )

    def test_generator_source_must_stay_inside_job_output(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside_td:
            root = Path(td)
            outside = Path(outside_td) / "outside.png"
            outside.write_bytes(b"source")

            def generator(value, output_dir, **kwargs):
                return {"success": True, "sourcePath": str(outside)}

            with self.assertRaisesRegex(
                ProductionExecutionError,
                "escapes output directory",
            ):
                execute_generated_raster_job(
                    job(),
                    root,
                    validator=lambda p, m: ({}, []),
                    png_optimizer=lambda *a: {},
                    webp_encoder=lambda *a, **k: {},
                    generator=generator,
                )

    def test_asset_id_cannot_escape_job_output(self):
        bad = job()
        bad["assetId"] = "../escape"

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(
                ProductionExecutionError,
                "safe filename",
            ):
                execute_generated_raster_job(
                    bad,
                    Path(td),
                    validator=lambda p, m: ({}, []),
                    png_optimizer=lambda *a: {},
                    webp_encoder=lambda *a, **k: {},
                    generator=lambda *a, **k: {},
                )

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


    def test_generated_3d_reports_lod_artifacts_when_enabled(self):
        three_d = job("glb")
        three_d["assetType"] = "prop"
        three_d["manifest"]["constraints"] = {
            "generateLods": True,
            "requireLods": False,
        }

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {"success": True, "sourcePath": str(source)}

            def lod_reporter(source, output_dir, profile):
                output_dir.mkdir(parents=True, exist_ok=True)
                lod = output_dir / "hero-run.lod1.glb"
                lod.write_bytes(b"lod")
                return {
                    "schema": "asset-forge/lod-generation/v1",
                    "required": True,
                    "available": True,
                    "outputs": [{"level": 1, "path": str(lod), "triangles": 100}],
                    "errors": [],
                    "warnings": [],
                }

            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: ({}, [], []),
                profile_validator=lambda p, profile: ({}, [], []),
                quality_reporter=lambda p, profile: {
                    "evaluation": {"passed": True, "errors": [], "warnings": []}
                },
                godot_delivery_reporter=lambda p, profile: {
                    "ready": True, "errors": [], "warnings": []
                },
                lod_reporter=lod_reporter,
                generator=generator,
            )

            self.assertTrue(report["success"])
            self.assertEqual(len(report["additionalArtifacts"]), 1)
            self.assertTrue(report["additionalArtifacts"][0].endswith(".lod1.glb"))
            self.assertTrue(report["validation"]["lods"]["available"])

    def test_required_collision_blocks_godot_prop_without_collision_node(self):
        three_d = job("glb")
        three_d["assetType"] = "prop"
        three_d["manifest"]["target"]["engine"] = "godot4"
        three_d["manifest"]["constraints"] = {"requireCollision": True}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {"success": True, "sourcePath": str(source)}

            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: ({}, [], []),
                profile_validator=lambda p, profile: ({}, [], []),
                quality_reporter=lambda p, profile: {
                    "evaluation": {"passed": True, "errors": [], "warnings": []}
                },
                godot_delivery_reporter=lambda p, profile: {
                    "ready": True,
                    "errors": [],
                    "warnings": [],
                    "scene": {"collisionNodes": 0},
                },
                generator=generator,
            )

            self.assertFalse(report["success"])
            self.assertIn("required runtime collision is missing", report["validation"]["errors"])

    def test_required_lod_toolchain_unavailable_blocks_3d_promotion(self):
        three_d = job("glb")
        three_d["assetType"] = "prop"
        three_d["manifest"]["constraints"] = {
            "generateLods": True,
            "requireLods": True,
        }

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.glb"
                source.write_bytes(b"glTF" + b"\x00" * 16)
                return {"success": True, "sourcePath": str(source)}

            report = execute_generated_3d_job(
                three_d,
                root,
                structural_validator=lambda p: ({}, [], []),
                profile_validator=lambda p, profile: ({}, [], []),
                quality_reporter=lambda p, profile: {
                    "evaluation": {"passed": True, "errors": [], "warnings": []}
                },
                godot_delivery_reporter=lambda p, profile: {
                    "ready": True, "errors": [], "warnings": []
                },
                lod_reporter=lambda source, output_dir, profile: {
                    "schema": "asset-forge/lod-generation/v1",
                    "required": True,
                    "available": False,
                    "outputs": [],
                    "errors": [],
                    "warnings": ["gltf-transform unavailable"],
                },
                generator=generator,
            )

            self.assertFalse(report["success"])
            self.assertIsNone(report["artifact"])
            self.assertTrue(any("LOD" in value for value in report["validation"]["errors"]))

if __name__ == "__main__":
    unittest.main()
