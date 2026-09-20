import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_auto_backend_prefers_pollinations_for_raster_when_ready(self):
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "pollinations": {"rasterVectorReady": True, "threeDReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            self.assertEqual(select_generation_backend(job(), "auto"), "pollinations")

    def test_auto_backend_falls_back_to_imagen_codex_for_raster(self):
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "pollinations": {"rasterVectorReady": False, "threeDReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            self.assertEqual(select_generation_backend(job(), "auto"), "imagen-codex")

    def test_auto_backend_rejects_vector_when_only_imagen_is_ready(self):
        vector_job = job()
        vector_job["assetType"] = "icon"
        with patch(
            "generator_backends.generator_backend_status",
            return_value={
                "pollinations": {"rasterVectorReady": False, "threeDReady": False},
                "imagenCodex": {"rasterReady": True},
            },
        ):
            with self.assertRaisesRegex(GenerationError, "raster-only"):
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


if __name__ == "__main__":
    unittest.main()


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
