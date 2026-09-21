import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from kaggle_3d_backend import (
    DEFAULT_MODEL,
    TRIPOSR_COMMIT,
    Kaggle3DGenerationError,
    _runner_source,
    generate,
    status,
)


class Kaggle3DBackendTests(unittest.TestCase):
    def test_status_requires_cli_and_kaggle_credentials(self):
        with patch("kaggle_3d_backend.shutil.which", return_value="/usr/bin/kaggle"):
            self.assertFalse(status(environ={})["threeDReady"])
            ready = status(environ={
                "KAGGLE_API_TOKEN": "token",
                "KAGGLE_USERNAME": "user",
            })
        self.assertTrue(ready["threeDReady"])
        self.assertEqual(ready["model"], DEFAULT_MODEL)
        self.assertEqual(ready["license"], "MIT")
        self.assertEqual(ready["estimatedVramGb"], 6)

    def test_runner_is_pinned_and_requires_glb_output(self):
        source = _runner_source()
        self.assertIn(TRIPOSR_COMMIT, source.replace("__ASSET_FORGE_TRIPOSR_COMMIT__", TRIPOSR_COMMIT))
        self.assertIn('"--model-save-format"', source)
        self.assertIn('"glb"', source)
        self.assertIn('asset.glb', source)
        self.assertIn('raw[:4] != b"glTF"', source)

    def test_generate_orchestrates_private_gpu_kernel_and_downloads_glb(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reference = root / "reference.png"
            reference.write_bytes(b"PNG")
            output = root / "asset.glb"
            commands = []

            def runner(command, **kwargs):
                commands.append(list(command))
                if command[1:3] == ["kernels", "status"]:
                    return SimpleNamespace(
                        returncode=0,
                        stdout="status: complete",
                        stderr="",
                    )
                if command[1:3] == ["kernels", "output"]:
                    download = Path(command[command.index("-p") + 1])
                    download.mkdir(parents=True, exist_ok=True)
                    (download / "asset.glb").write_bytes(
                        b"glTF" + b"\x02\x00\x00\x00" + b"\x0c\x00\x00\x00"
                    )
                    (download / "result.json").write_text(
                        json.dumps({
                            "success": True,
                            "model": DEFAULT_MODEL,
                            "mcResolution": 256,
                        }),
                        encoding="utf-8",
                    )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("kaggle_3d_backend.shutil.which", return_value="/usr/bin/kaggle"):
                result = generate(
                    reference,
                    output,
                    environ={
                        "KAGGLE_API_TOKEN": "token",
                        "KAGGLE_USERNAME": "user",
                    },
                    runner=runner,
                    timeout_seconds=30,
                )

            self.assertTrue(output.is_file())
            self.assertEqual(output.read_bytes()[:4], b"glTF")
            self.assertEqual(result["backend"], "kaggle-triposr")
            self.assertEqual(result["model"], DEFAULT_MODEL)
            self.assertEqual(result["license"], "MIT")
            push = next(command for command in commands if command[1:3] == ["kernels", "push"])
            self.assertIn("--accelerator", push)
            self.assertTrue(any(command[1:3] == ["kernels", "delete"] for command in commands))

    def test_generate_rejects_unapproved_model_override(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "reference.png"
            source.write_bytes(b"PNG")
            with patch("kaggle_3d_backend.shutil.which", return_value="/usr/bin/kaggle"):
                with self.assertRaisesRegex(
                    Kaggle3DGenerationError,
                    "only supports",
                ):
                    generate(
                        source,
                        Path(td) / "asset.glb",
                        model="other/model",
                        environ={
                            "KAGGLE_API_TOKEN": "token",
                            "KAGGLE_USERNAME": "user",
                        },
                    )


if __name__ == "__main__":
    unittest.main()
