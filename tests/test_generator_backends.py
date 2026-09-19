import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from generator_backends import (
    GenerationError,
    build_generation_prompt,
    execute_generated_asset,
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
        status = generator_backend_status(
            environ={"POLLINATIONS_API_KEY": "super-secret-value"},
            home=Path("/definitely/not/a/real/home"),
        )
        self.assertTrue(status["pollinations"]["authenticated"])
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
                )
            self.assertTrue(result["success"])
            self.assertEqual(result["sourceBytes"], 3)
            self.assertEqual(result["metadata"], {"ok": True})

    def test_unsupported_generated_type_fails_closed(self):
        bad = job()
        bad["assetType"] = "character-3d"
        with self.assertRaisesRegex(GenerationError, "unsupported generated asset type"):
            build_generation_prompt(bad)


if __name__ == "__main__":
    unittest.main()
