import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kaggle_backend import KaggleGenerationError, _runner_source, status


class KaggleBackendTests(unittest.TestCase):
    def test_status_requires_cli_token_and_username(self):
        with patch("kaggle_backend.shutil.which", return_value="/usr/bin/kaggle"):
            self.assertFalse(status(environ={})["rasterReady"])
            self.assertTrue(status(environ={
                "KAGGLE_API_TOKEN": "token",
                "KAGGLE_USERNAME": "user",
            })["rasterReady"])

    def test_status_rejects_missing_cli(self):
        with patch("kaggle_backend.shutil.which", return_value=None):
            value = status(environ={
                "KAGGLE_API_TOKEN": "token",
                "KAGGLE_USERNAME": "user",
            })
            self.assertFalse(value["rasterReady"])
            self.assertFalse(value["installed"])


    def test_runner_quantizes_transformer_only(self):
        source = _runner_source()
        self.assertIn('components_to_quantize=["transformer"]', source)
        self.assertNotIn('components_to_quantize=["transformer", "text_encoder"]', source)
        self.assertIn("pipe.enable_model_cpu_offload()", source)


if __name__ == "__main__":
    unittest.main()
