import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from raster_backend import decode_webp_rgba, detect_pillow_webp, encode_webp_rgba
from raster_pack import decode_raster_rgba, encode_rgba, encode_webp, inspect_webp, pack_uniform_atlas


class RasterBackendTests(unittest.TestCase):
    def test_backend_status_shape(self):
        status = detect_pillow_webp()
        self.assertEqual(status["backend"], "pillow")
        self.assertIn("available", status)
        self.assertIn("pillowVersion", status)
        self.assertIn("webpVersion", status)

    def test_missing_backend_returns_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.webp"
            path.write_bytes(b"not-used")
            with patch(
                "raster_backend.detect_pillow_webp",
                return_value={
                    "available": False,
                    "backend": "pillow",
                    "pillowVersion": None,
                    "webpVersion": None,
                    "reason": "missing",
                },
            ):
                with self.assertRaisesRegex(ValueError, "optional Pillow"):
                    decode_webp_rgba(path, expected_width=1, expected_height=1)

    @unittest.skipUnless(
        detect_pillow_webp()["available"],
        "Pillow with WebP support is not installed",
    )
    def test_real_webp_lossless_decode_to_rgba(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.webp"
            image = Image.new("RGBA", (2, 1))
            image.putdata([(10, 20, 30, 255), (40, 50, 60, 128)])
            image.save(path, "WEBP", lossless=True, exact=True)

            width, height, pixels = decode_raster_rgba(path)

        self.assertEqual((width, height), (2, 1))
        self.assertEqual(
            pixels,
            bytes([10, 20, 30, 255, 40, 50, 60, 128]),
        )

    @unittest.skipUnless(
        detect_pillow_webp()["available"],
        "Pillow with WebP support is not installed",
    )
    def test_pack_atlas_accepts_mixed_png_and_webp(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            png = root / "a.png"
            webp = root / "b.webp"
            atlas = root / "atlas.png"

            encode_rgba(png, 1, 1, bytes([255, 0, 0, 255]))
            image = Image.new("RGBA", (1, 1), (0, 255, 0, 255))
            image.save(webp, "WEBP", lossless=True, exact=True)

            report = pack_uniform_atlas([png, webp], atlas, columns=2)
            width, height, pixels = decode_raster_rgba(atlas)

        self.assertEqual((width, height), (2, 1))
        self.assertEqual(report["frameCount"], 2)
        self.assertEqual(pixels[:4], bytes([255, 0, 0, 255]))
        self.assertEqual(pixels[4:8], bytes([0, 255, 0, 255]))

    @unittest.skipUnless(
        detect_pillow_webp()["available"],
        "Pillow with WebP support is not installed",
    )
    def test_animated_webp_is_rejected_for_atlas_decode(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "animated.webp"
            first = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
            second = Image.new("RGBA", (1, 1), (0, 255, 0, 255))
            first.save(
                path,
                "WEBP",
                save_all=True,
                append_images=[second],
                duration=[50, 50],
                loop=0,
                lossless=True,
            )

            with self.assertRaisesRegex(ValueError, "animated WebP"):
                decode_raster_rgba(path)

    def test_webp_encoder_validates_quality_and_method_without_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "x.webp"
            with patch(
                "raster_backend.detect_pillow_webp",
                return_value={
                    "available": True,
                    "backend": "pillow",
                    "pillowVersion": "test",
                    "webpVersion": "test",
                    "reason": None,
                },
            ):
                with self.assertRaisesRegex(ValueError, "quality"):
                    encode_webp_rgba(
                        output,
                        1,
                        1,
                        bytes([0, 0, 0, 255]),
                        quality=101,
                    )
                with self.assertRaisesRegex(ValueError, "method"):
                    encode_webp_rgba(
                        output,
                        1,
                        1,
                        bytes([0, 0, 0, 255]),
                        method=7,
                    )

    @unittest.skipUnless(
        detect_pillow_webp()["available"],
        "Pillow with WebP support is not installed",
    )
    def test_encode_webp_lossless_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            output = root / "output.webp"
            pixels = bytes([
                10, 20, 30, 255,
                40, 50, 60, 128,
            ])
            encode_rgba(source, 2, 1, pixels)
            report = encode_webp(source, output, lossless=True, quality=100, method=6)
            width, height, decoded = decode_raster_rgba(output)
            info = inspect_webp(output)

        self.assertEqual((width, height), (2, 1))
        self.assertEqual(decoded, pixels)
        self.assertEqual((info["width"], info["height"]), (2, 1))
        self.assertTrue(report["lossless"])
        self.assertGreater(report["afterBytes"], 0)


if __name__ == "__main__":
    unittest.main()
