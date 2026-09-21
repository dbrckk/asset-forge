import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from vector_backend import VectorizationError, status, vectorize_raster


class VectorBackendTests(unittest.TestCase):
    def test_status_reports_optional_dependency(self):
        with patch("vector_backend.importlib.util.find_spec", return_value=object()), patch(
            "vector_backend.metadata.version",
            return_value="1.0.0a4",
        ):
            result = status()

        self.assertTrue(result["installed"])
        self.assertTrue(result["vectorizeReady"])
        self.assertEqual(result["version"], "1.0.0a4")
        self.assertEqual(result["license"], "MIT")

    def test_config_api_vectorizes_to_svg(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.png"
            output = root / "asset.svg"
            source.write_bytes(b"PNG")

            class Config:
                @classmethod
                def poster(cls):
                    return cls()

                def convert_file(self, input_path, output_path):
                    Path(output_path).write_text(
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M0 0h64v64H0z"/></svg>',
                        encoding="utf-8",
                    )

            fake = SimpleNamespace(Config=Config)
            with patch("vector_backend.importlib.import_module", return_value=fake):
                result = vectorize_raster(source, output)

            self.assertEqual(result["backend"], "vtracer")
            self.assertEqual(result["engine"], "config-api")
            self.assertEqual(result["preset"], "poster")
            self.assertTrue(output.is_file())
            self.assertGreater(result["bytes"], 0)

    def test_legacy_api_remains_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.webp"
            output = root / "asset.svg"
            source.write_bytes(b"WEBP")

            def legacy(input_path, output_path, **kwargs):
                self.assertEqual(kwargs["colormode"], "color")
                Path(output_path).write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32"/></svg>',
                    encoding="utf-8",
                )

            fake = SimpleNamespace(convert_image_to_svg_py=legacy)
            with patch("vector_backend.importlib.import_module", return_value=fake):
                result = vectorize_raster(source, output)

            self.assertEqual(result["engine"], "legacy-api")
            self.assertTrue(output.is_file())

    def test_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(VectorizationError, "missing"):
                vectorize_raster(
                    Path(td) / "missing.png",
                    Path(td) / "asset.svg",
                )


if __name__ == "__main__":
    unittest.main()
