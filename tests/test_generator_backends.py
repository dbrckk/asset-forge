import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloudflare_backend import CloudflareGenerationError
from generator_backends import (
    GenerationError,
    build_generation_prompt,
    execute_generated_asset,
    execute_generated_3d_asset,
    generator_backend_status,
    imagen_codex_command,
    pollinations_command,
    select_generation_backend,
)


def job():
    return {
        "schema": "asset-forge/production-job/v1",
        "requestId": "hero-run",
        "assetType": "sprite-sheet",
        "instruction": "Create a four-frame hero running animation.",
        "requiresGenerator": True,
        "manifest": {
            "constraints": {
                "pixelArt": True,
                "frameWidth": 32,
                "frameHeight": 32,
                "expectedFrames": 4,
            }
        },
    }


class GeneratorBackendsTests(unittest.TestCase):
    def test_prompt_preserves_hard_sprite_constraints(self):
        prompt = build_generation_prompt(job())
        self.assertIn("32x32", prompt)
        self.assertIn("exactly 4 frames", prompt)
        self.assertIn("pixel art", prompt)

    def test_pollinations_command_never_contains_api_key(self):
        command = pollinations_command(
            job(),
            Path("out/generated.png"),
            model="flux",
            executable="/usr/bin/polli",
        )
        self.assertEqual(command[0:3], ["/usr/bin/polli", "gen", "image"])
        self.assertIn("--json", command)
        self.assertIn("--model", command)
        self.assertIn("--width", command)
        self.assertIn("--height", command)
        self.assertEqual(command[command.index("--width") + 1], "512")
        self.assertEqual(command[command.index("--height") + 1], "512")
        self.assertFalse(any("POLLINATIONS_API_KEY" in item for item in command))

    def test_vector_generation_defaults_to_recraft_svg_model(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        vector_job["instruction"] = "Create a clean game inventory icon."
        vector_job["manifest"]["constraints"] = {}
        command = pollinations_command(
            vector_job,
            Path("out/generated.svg"),
            executable="/usr/bin/polli",
        )
        self.assertIn("--model", command)
        self.assertEqual(
            command[command.index("--model") + 1],
            "recraft/recraft-v4.1-vector",
        )
        self.assertIn("valid SVG viewBox", build_generation_prompt(vector_job))

    def test_backend_status_reports_auth_without_secret_value(self):
        with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
            status = generator_backend_status(
                environ={"POLLINATIONS_API_KEY": "super-secret-value"},
                home=Path("/definitely/not/a/real/home"),
            )
        self.assertTrue(status["pollinations"]["authenticated"])
        self.assertTrue(status["pollinations"]["rasterVectorReady"])
        self.assertTrue(status["pollinations"]["threeDReady"])
        self.assertEqual(status["pollinations"]["credentialSource"], "environment")
        self.assertNotIn("super-secret-value", repr(status))

    def test_execute_generated_asset_uses_bounded_subprocess_and_output(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            def runner(command, **kwargs):
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Result:
                    returncode = 0
                    stdout = '{"ok":true}'
                    stderr = ""
                self.assertEqual(kwargs["timeout"], 30.0)
                self.assertTrue(kwargs["capture_output"])
                self.assertTrue(kwargs["text"])
                return Result()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="pollinations",
                    timeout_seconds=30,
                    runner=runner,
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {
                            "width": 64,
                            "height": 64,
                            "columns": 2,
                            "rows": 2,
                        }
                    ),
                )
            self.assertTrue(result["success"])
            self.assertEqual(result["sourceBytes"], 3)
            self.assertEqual(result["normalization"]["columns"], 2)
            self.assertEqual(result["normalization"]["rows"], 2)
            self.assertEqual(result["metadata"], {"ok": True})

    def test_generator_metadata_redacts_credentials_before_reporting(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            def runner(command, **kwargs):
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")

                class Result:
                    returncode = 0
                    stdout = (
                        '{"ok":true,"api_key":"top-secret",'
                        '"nested":{"access_token":"also-secret"}}'
                    )
                    stderr = ""

                return Result()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="pollinations",
                    runner=runner,
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                    ),
                    similarity_evaluator=lambda child, refs: {
                        "score": 0.91,
                        "bestReference": str(refs[0]),
                        "comparisons": [],
                    },
                )

        self.assertTrue(result["metadata"]["ok"])
        self.assertEqual(result["metadata"]["api_key"], "[REDACTED]")
        self.assertEqual(
            result["metadata"]["nested"]["access_token"],
            "[REDACTED]",
        )
        self.assertNotIn("top-secret", repr(result))
        self.assertNotIn("also-secret", repr(result))



    def test_backend_status_reports_imagen_codex_without_exposing_token(self):
        def which(name):
            return "/usr/bin/imagen" if name == "imagen" else None

        with patch("generator_backends.shutil.which", side_effect=which):
            status = generator_backend_status(
                environ={"CODEX_ACCESS_TOKEN": "codex-secret"},
                home=Path("/definitely/not/a/real/home"),
            )

        self.assertTrue(status["imagenCodex"]["installed"])
        self.assertTrue(status["imagenCodex"]["authenticated"])
        self.assertTrue(status["imagenCodex"]["rasterReady"])
        self.assertFalse(status["imagenCodex"]["vectorSvgReady"])
        self.assertNotIn("codex-secret", repr(status))

    def test_imagen_codex_command_uses_raster_output_and_no_token_argument(self):
        raster_job = job()
        raster_job["assetType"] = "sprite"
        command = imagen_codex_command(
            raster_job,
            Path("out"),
            executable="/usr/bin/imagen",
        )

        self.assertEqual(command[0], "/usr/bin/imagen")
        self.assertIn("codex-2", command)
        self.assertIn("--json", command)
        self.assertIn("generated-source", command)
        self.assertFalse(any("TOKEN" in part or "secret" in part for part in command))

    def test_imagen_codex_rejects_vector_generation(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        with self.assertRaisesRegex(GenerationError, "raster generated assets only"):
            imagen_codex_command(vector_job, Path("out"))

    def test_execute_generated_asset_supports_imagen_codex_raster(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            def runner(command, **kwargs):
                target = out / "generated-source.png"
                target.write_bytes(b"PNG")

                class Result:
                    returncode = 0
                    stdout = '{"files":["generated-source.png"],"provider":"codex"}'
                    stderr = ""

                return Result()

            def which(name):
                return "/usr/bin/imagen" if name == "imagen" else None

            with patch("generator_backends.shutil.which", side_effect=which):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="imagen-codex",
                    timeout_seconds=30,
                    runner=runner,
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {
                            "width": 64,
                            "height": 64,
                            "columns": 2,
                            "rows": 2,
                        }
                    ),
                )

            self.assertTrue(result["success"])
            self.assertEqual(result["backend"], "imagen-codex")
            self.assertEqual(result["model"], "codex-2")
            self.assertEqual(result["metadata"]["provider"], "codex")

    def test_imagen_codex_command_accepts_local_visual_references(self):
        raster_job = job()
        raster_job["assetType"] = "sprite"
        command = imagen_codex_command(
            raster_job,
            Path("out"),
            executable="/usr/bin/imagen",
            reference_paths=[Path("parent.png"), Path("palette.webp")],
        )

        self.assertEqual(command.count("--input-ref"), 2)
        self.assertIn("parent.png", command)
        self.assertIn("palette.webp", command)
        self.assertIn("strict visual identity anchor", command[-1])

    def test_execute_generated_asset_supports_imagen_visual_reference_and_retry(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            reference = out / "parent.png"
            reference.write_bytes(b"PNG")
            scores = iter([0.2, 0.83])
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                target = out / "generated-source.png"
                target.write_bytes(b"PNG")

                class Result:
                    returncode = 0
                    stdout = '{"files":["generated-source.png"],"provider":"codex"}'
                    stderr = ""

                return Result()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/imagen"):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="imagen-codex",
                    reference_paths=[reference],
                    timeout_seconds=30,
                    runner=runner,
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {
                            "width": 64,
                            "height": 64,
                            "columns": 2,
                            "rows": 2,
                        }
                    ),
                    similarity_evaluator=lambda child, refs: {
                        "score": next(scores),
                        "bestReference": str(refs[0]),
                        "comparisons": [],
                    },
                )

            self.assertEqual(len(calls), 2)
            self.assertIn("--input-ref", calls[0])
            self.assertEqual(calls[0][calls[0].index("--input-ref") + 1], str(reference))
            self.assertIn("drifted too far", calls[1][-1])
            self.assertTrue(result["visualSimilarity"]["passed"])
            self.assertEqual(result["references"][0]["transport"], "local-input-ref")
            self.assertIsNone(result["references"][0]["url"])

    def test_cloudflare_reference_routes_directly_to_kaggle_qwen(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            reference = out / "parent.png"
            reference.write_bytes(b"PNG")
            seen = {}

            def fake_kaggle(prompt, output, **kwargs):
                seen["prompt"] = prompt
                seen["reference_path"] = kwargs.get("reference_path")
                output.write_bytes(b"PNG")
                return {"provider": "kaggle", "model": "Qwen/Qwen-Image-2.1"}

            with patch(
                "generator_backends.generator_backend_status",
                return_value={"kaggleQwen": {"rasterReady": True}},
            ), patch(
                "generator_backends.kaggle_generate",
                side_effect=fake_kaggle,
            ), patch(
                "generator_backends.cloudflare_generate",
                side_effect=AssertionError("Cloudflare must not be called for referenced raster jobs"),
            ):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="cloudflare",
                    reference_paths=[reference],
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                    ),
                    similarity_evaluator=lambda child, refs: {
                        "score": 0.91,
                        "bestReference": str(refs[0]),
                        "comparisons": [],
                    },
                )

            self.assertEqual(result["backend"], "kaggle-qwen")
            self.assertEqual(seen["reference_path"], reference)

    def test_auto_cloudflare_failure_falls_back_to_kaggle_qwen(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            def fake_kaggle(prompt, output, **kwargs):
                output.write_bytes(b"PNG")
                return {
                    "provider": "kaggle",
                    "model": "Qwen/Qwen-Image-2.1",
                }

            with patch(
                "generator_backends.generator_backend_status",
                return_value={
                    "cloudflare": {"rasterReady": True},
                    "kaggleQwen": {"rasterReady": True},
                    "pollinations": {
                        "rasterVectorReady": False,
                        "threeDReady": False,
                    },
                    "imagenCodex": {"rasterReady": False},
                },
            ), patch(
                "generator_backends.cloudflare_generate",
                side_effect=CloudflareGenerationError("temporary failure"),
            ), patch(
                "generator_backends.kaggle_generate",
                side_effect=fake_kaggle,
            ):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="auto",
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                    ),
                )

            self.assertEqual(result["requestedBackend"], "auto")
            self.assertEqual(result["initialBackend"], "cloudflare")
            self.assertEqual(result["backend"], "kaggle-qwen")
            self.assertEqual(
                result["fallbacks"],
                [{
                    "from": "cloudflare",
                    "to": "kaggle-qwen",
                    "reason": "cloudflare-generation-error",
                    "attempt": 1,
                }],
            )

    def test_explicit_cloudflare_failure_does_not_silently_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            with patch(
                "generator_backends.generator_backend_status",
                return_value={
                    "cloudflare": {"rasterReady": True},
                    "kaggleQwen": {"rasterReady": True},
                },
            ), patch(
                "generator_backends.cloudflare_generate",
                side_effect=CloudflareGenerationError("temporary failure"),
            ), patch(
                "generator_backends.kaggle_generate",
            ) as kaggle:
                with self.assertRaisesRegex(
                    GenerationError,
                    "cloudflare generation failed",
                ):
                    execute_generated_asset(
                        job(),
                        out,
                        backend="cloudflare",
                    )

            kaggle.assert_not_called()

    def test_auto_backend_prefers_cloudflare_for_raster_when_ready(self):
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": True},
                "pollinations": {"rasterVectorReady": True, "threeDReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            self.assertEqual(select_generation_backend(job(), "auto"), "cloudflare")

    def test_auto_backend_uses_kaggle_when_cloudflare_unavailable(self):
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": False},
                "kaggleQwen": {"rasterReady": True},
                "pollinations": {"rasterVectorReady": True, "threeDReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            self.assertEqual(select_generation_backend(job(), "auto"), "kaggle-qwen")

    def test_auto_backend_does_not_fall_back_to_imagen_codex(self):
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": False},
                "kaggleQwen": {"rasterReady": False},
                "pollinations": {"rasterVectorReady": False, "threeDReady": False},
                "qwenColab": {"rasterReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            with self.assertRaisesRegex(GenerationError, "no authenticated free raster generation backend is ready"):
                select_generation_backend(job(), "auto")

    def test_auto_vector_prefers_vtracer_with_free_raster_source(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": True},
                "kaggleQwen": {"rasterReady": False},
                "vtracer": {"vectorSvgReady": True},
                "pollinations": {"rasterVectorReady": True, "threeDReady": False},
                "imagenCodex": {"rasterReady": False},
            },
        ):
            self.assertEqual(
                select_generation_backend(vector_job, "auto"),
                "vtracer",
            )

    def test_auto_vector_falls_back_to_pollinations_when_vtracer_unavailable(self):
        vector_job = job()
        vector_job["assetType"] = "logo"
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": False},
                "kaggleQwen": {"rasterReady": False},
                "vtracer": {"vectorSvgReady": False},
                "pollinations": {"rasterVectorReady": True, "threeDReady": False},
                "imagenCodex": {"rasterReady": False},
            },
        ):
            self.assertEqual(
                select_generation_backend(vector_job, "auto"),
                "pollinations",
            )

    def test_vtracer_vector_generation_uses_free_cloudflare_source(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        vector_job["manifest"]["constraints"] = {}

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            seen = {}

            def fake_cloudflare(prompt, output, **kwargs):
                seen["prompt"] = prompt
                seen["width"] = kwargs["width"]
                seen["height"] = kwargs["height"]
                output.write_bytes(b"PNG")
                return {"provider": "cloudflare"}

            def fake_vectorizer(source, output, **kwargs):
                seen["vector_source"] = source
                seen["preset"] = kwargs["preset"]
                output.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M0 0h64v64H0z"/></svg>',
                    encoding="utf-8",
                )
                return {"backend": "vtracer", "bytes": output.stat().st_size}

            with patch(
                "generator_backends.generator_backend_status",
                return_value={
                    "cloudflare": {"rasterReady": True},
                    "kaggleQwen": {"rasterReady": False},
                    "vtracer": {"vectorSvgReady": True},
                    "pollinations": {"rasterVectorReady": False, "threeDReady": False},
                    "imagenCodex": {"rasterReady": False},
                },
            ), patch(
                "generator_backends.cloudflare_generate",
                side_effect=fake_cloudflare,
            ):
                result = execute_generated_asset(
                    vector_job,
                    out,
                    backend="auto",
                    vectorizer=fake_vectorizer,
                )

            self.assertEqual(result["backend"], "vtracer")
            self.assertEqual(result["requestedBackend"], "auto")
            self.assertEqual(result["initialBackend"], "vtracer")
            self.assertEqual(result["model"], "visioncortex/vtracer")
            self.assertEqual(result["metadata"]["rasterBackend"], "cloudflare")
            self.assertEqual(seen["width"], 1024)
            self.assertEqual(seen["height"], 1024)
            self.assertEqual(seen["preset"], "poster")
            self.assertIn("vector-friendly source art", seen["prompt"])
            self.assertEqual(Path(result["sourcePath"]).suffix, ".svg")

    def test_vtracer_vector_source_falls_back_to_kaggle(self):
        vector_job = job()
        vector_job["assetType"] = "logo"
        vector_job["manifest"]["constraints"] = {}

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            def fake_kaggle(prompt, output, **kwargs):
                output.write_bytes(b"PNG")
                return {"provider": "kaggle"}

            def fake_vectorizer(source, output, **kwargs):
                output.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64"/></svg>',
                    encoding="utf-8",
                )
                return {"backend": "vtracer"}

            with patch(
                "generator_backends.generator_backend_status",
                return_value={
                    "cloudflare": {"rasterReady": True},
                    "kaggleQwen": {"rasterReady": True},
                    "vtracer": {"vectorSvgReady": True},
                    "pollinations": {"rasterVectorReady": False, "threeDReady": False},
                },
            ), patch(
                "generator_backends.cloudflare_generate",
                side_effect=CloudflareGenerationError("temporary failure"),
            ), patch(
                "generator_backends.kaggle_generate",
                side_effect=fake_kaggle,
            ):
                result = execute_generated_asset(
                    vector_job,
                    out,
                    backend="auto",
                    vectorizer=fake_vectorizer,
                )

            self.assertEqual(result["backend"], "vtracer")
            self.assertEqual(result["metadata"]["rasterBackend"], "kaggle-qwen")
            self.assertEqual(result["fallbacks"][0]["stage"], "vector-raster")
            self.assertEqual(
                result["fallbacks"][0]["reason"],
                "cloudflare-generation-error",
            )

    def test_auto_backend_rejects_vector_when_only_imagen_is_ready(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": False},
                "kaggleQwen": {"rasterReady": False},
                "vtracer": {"vectorSvgReady": False},
                "pollinations": {"rasterVectorReady": False, "threeDReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            with self.assertRaisesRegex(GenerationError, "no SVG generation backend"):
                select_generation_backend(vector_job, "auto")

    def test_required_alpha_runs_transparency_processor_before_normalization(self):
        alpha_job = job()
        alpha_job["manifest"]["constraints"]["requiresAlpha"] = True

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            calls = []

            def runner(command, **kwargs):
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Result:
                    returncode = 0
                    stdout = "{}"
                    stderr = ""
                return Result()

            def transparency(path, value, **kwargs):
                calls.append(("transparency", path.name))
                return {"required": True, "changed": True, "backend": "rembg"}

            def normalize(raw, output, value):
                calls.append(("normalize", raw.name))
                output.write_bytes(raw.read_bytes())
                return {"width": 64, "height": 64, "columns": 2, "rows": 2}

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_asset(
                    alpha_job,
                    out,
                    backend="pollinations",
                    runner=runner,
                    transparency_processor=transparency,
                    raster_normalizer=normalize,
                )

            self.assertEqual(calls[0][0], "transparency")
            self.assertEqual(calls[1][0], "normalize")
            self.assertEqual(result["transparency"]["backend"], "rembg")

    def test_3d_prompt_is_reference_image_oriented(self):
        three_d = job()
        three_d["assetType"] = "prop"
        three_d["instruction"] = "Create a stylized treasure chest."
        prompt = build_generation_prompt(three_d)
        self.assertIn("image-to-3D reference", prompt)
        self.assertIn("three-quarter view", prompt)

    def test_execute_generated_3d_uses_uploaded_reference_and_bearer_auth(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            seen = {}

            def generator(value, output_dir, **kwargs):
                source = Path(output_dir) / "generated-source.png"
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(b"PNG")
                return {"success": True, "sourcePath": str(source)}

            def upload_runner(command, **kwargs):
                self.assertEqual(command[1], "upload")
                self.assertIn("--json", command)
                class Result:
                    returncode = 0
                    stdout = '{"url":"https://media.pollinations.ai/ref-123","id":"ref-123"}'
                    stderr = ""
                return Result()

            class Response:
                status = 200
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc, tb):
                    return False
                def read(self, limit=-1):
                    return b"glTF" + b"\x02\x00\x00\x00" + b"\x0c\x00\x00\x00"

            def opener(request, timeout):
                seen["url"] = request.full_url
                seen["authorization"] = request.get_header("Authorization")
                seen["body"] = request.data
                seen["timeout"] = timeout
                return Response()

            three_d = job()
            three_d["assetType"] = "prop"
            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_3d_asset(
                    three_d,
                    root,
                    timeout_seconds=45,
                    environ={"POLLINATIONS_API_KEY": "secret-key"},
                    generator=generator,
                    upload_runner=upload_runner,
                    opener=opener,
                )

            self.assertTrue(result["success"])
            self.assertEqual(result["model"], "microsoft/trellis-2")
            self.assertEqual(result["resolution"], "low")
            self.assertTrue((root / "generated-source.glb").is_file())
            self.assertEqual(seen["authorization"], "Bearer secret-key")
            self.assertNotIn("secret-key", seen["url"])
            payload = __import__("json").loads(seen["body"].decode("utf-8"))
            self.assertEqual(payload["image"], "https://media.pollinations.ai/ref-123")
            self.assertEqual(payload["model"], "microsoft/trellis-2")

    def test_3d_generation_requires_server_api_key(self):
        three_d = job()
        three_d["assetType"] = "mesh"
        with self.assertRaisesRegex(GenerationError, "POLLINATIONS_API_KEY"):
            execute_generated_3d_asset(
                three_d,
                Path("unused"),
                environ={},
            )

    def test_unsupported_generated_type_fails_closed(self):
        bad = job()
        bad["assetType"] = "audio"
        with self.assertRaisesRegex(GenerationError, "unsupported generated asset type"):
            build_generation_prompt(bad)


    def test_raster_generation_uploads_and_passes_visual_reference(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            reference = out / "parent.png"
            reference.write_bytes(b"PNG")
            seen = []

            def runner(command, **kwargs):
                seen.append(command)
                if command[1] == "upload":
                    class Upload:
                        returncode = 0
                        stdout = '{"url":"https://media.pollinations.ai/parent-ref"}'
                        stderr = ""
                    return Upload()
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Generate:
                    returncode = 0
                    stdout = "{}"
                    stderr = ""
                return Generate()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="pollinations",
                    reference_paths=[reference],
                    runner=runner,
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                    ),
                    similarity_evaluator=lambda child, refs: {
                        "score": 0.91,
                        "bestReference": str(refs[0]),
                        "comparisons": [],
                    },
                )

            generate = [command for command in seen if command[1:3] == ["gen", "image"]][0]
            self.assertIn("--image", generate)
            self.assertEqual(
                generate[generate.index("--image") + 1],
                "https://media.pollinations.ai/parent-ref",
            )
            self.assertEqual(
                generate[generate.index("--model") + 1],
                "kontext",
            )
            self.assertEqual(result["references"][0]["path"], str(reference))
            self.assertEqual(
                result["references"][0]["url"],
                "https://media.pollinations.ai/parent-ref",
            )
            self.assertIn("strict visual identity anchor", generate[3])

    def test_visual_reference_rejects_vector_generation(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        vector_job["manifest"]["constraints"] = {}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reference = root / "parent.png"
            reference.write_bytes(b"PNG")
            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                with self.assertRaisesRegex(GenerationError, "raster generation only"):
                    execute_generated_asset(
                        vector_job,
                        root / "out",
                        backend="pollinations",
                        reference_paths=[reference],
                    )


    def test_visual_similarity_retries_until_threshold_passes(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            reference = out / "parent.png"
            reference.write_bytes(b"PNG")
            scores = iter([0.20, 0.73])
            generation_calls = []

            def runner(command, **kwargs):
                if command[1] == "upload":
                    class Upload:
                        returncode = 0
                        stdout = '{"url":"https://media.pollinations.ai/parent-ref"}'
                        stderr = ""
                    return Upload()
                generation_calls.append(command)
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Generate:
                    returncode = 0
                    stdout = "{}"
                    stderr = ""
                return Generate()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_asset(
                    job(),
                    out,
                    backend="pollinations",
                    reference_paths=[reference],
                    runner=runner,
                    raster_normalizer=lambda raw, output, value: (
                        output.write_bytes(raw.read_bytes())
                        and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                    ),
                    similarity_evaluator=lambda child, refs: {
                        "score": next(scores),
                        "bestReference": str(refs[0]),
                        "comparisons": [],
                    },
                )

            self.assertEqual(len(generation_calls), 2)
            self.assertFalse(result["visualSimilarity"]["attempts"][0]["passed"])
            self.assertTrue(result["visualSimilarity"]["attempts"][1]["passed"])
            self.assertTrue(result["visualSimilarity"]["passed"])
            self.assertIn("drifted too far", generation_calls[1][3])

    def test_visual_similarity_fails_after_retry_budget(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            reference = out / "parent.png"
            reference.write_bytes(b"PNG")
            value = job()
            value["manifest"]["constraints"]["visualSimilarityRetries"] = 1
            value["manifest"]["constraints"]["visualSimilarityMin"] = 0.8

            def runner(command, **kwargs):
                if command[1] == "upload":
                    class Upload:
                        returncode = 0
                        stdout = '{"url":"https://media.pollinations.ai/parent-ref"}'
                        stderr = ""
                    return Upload()
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Generate:
                    returncode = 0
                    stdout = "{}"
                    stderr = ""
                return Generate()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                with self.assertRaisesRegex(GenerationError, "visual consistency score"):
                    execute_generated_asset(
                        value,
                        out,
                        backend="pollinations",
                        reference_paths=[reference],
                        runner=runner,
                        raster_normalizer=lambda raw, output, job_value: (
                            output.write_bytes(raw.read_bytes())
                            and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                        ),
                        similarity_evaluator=lambda child, refs: {
                            "score": 0.1,
                            "bestReference": str(refs[0]),
                            "comparisons": [],
                        },
                    )


    def test_technical_quality_retries_without_visual_reference(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            value = job()
            value["manifest"]["constraints"]["technicalQualityMin"] = 0.6
            value["manifest"]["constraints"]["technicalQualityRetries"] = 2
            scores = iter([0.31, 0.74])
            generation_calls = []

            def runner(command, **kwargs):
                generation_calls.append(command)
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Generate:
                    returncode = 0
                    stdout = "{}"
                    stderr = ""
                return Generate()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                result = execute_generated_asset(
                    value,
                    out,
                    backend="pollinations",
                    runner=runner,
                    raster_normalizer=lambda raw, output, job_value: (
                        output.write_bytes(raw.read_bytes())
                        and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                    ),
                    technical_quality_evaluator=lambda child, manifest: {
                        "score": next(scores),
                        "metrics": {},
                        "errors": [],
                        "warnings": [],
                    },
                )

            self.assertEqual(len(generation_calls), 2)
            history = result["technicalQuality"]["attempts"]
            self.assertFalse(history[0]["passed"])
            self.assertTrue(history[1]["passed"])
            self.assertTrue(result["technicalQuality"]["passed"])
            self.assertIn("technical game-art quality", generation_calls[1][3])

    def test_technical_quality_rejects_after_retry_budget(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            value = job()
            value["manifest"]["constraints"]["technicalQualityMin"] = 0.75
            value["manifest"]["constraints"]["technicalQualityRetries"] = 1
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                target = Path(command[command.index("--output") + 1])
                target.write_bytes(b"PNG")
                class Generate:
                    returncode = 0
                    stdout = "{}"
                    stderr = ""
                return Generate()

            with patch("generator_backends.shutil.which", return_value="/usr/bin/polli"):
                with self.assertRaisesRegex(GenerationError, "technical art quality score"):
                    execute_generated_asset(
                        value,
                        out,
                        backend="pollinations",
                        runner=runner,
                        raster_normalizer=lambda raw, output, job_value: (
                            output.write_bytes(raw.read_bytes())
                            and {"width": 64, "height": 64, "columns": 2, "rows": 2}
                        ),
                        technical_quality_evaluator=lambda child, manifest: {
                            "score": 0.2,
                            "metrics": {},
                            "errors": [],
                            "warnings": [],
                        },
                    )
            self.assertEqual(len(calls), 2)

if __name__ == "__main__":
    unittest.main()
