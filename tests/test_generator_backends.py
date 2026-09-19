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
    pollinations_command,
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
