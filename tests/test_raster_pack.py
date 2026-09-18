import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from raster_pack import decode_rgba, pack_uniform_atlas, recompress_png


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, pixel: bytes) -> None:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = pixel * width
    raw = b"".join(b"\x00" + row for _ in range(height))
    path.write_bytes(
        PNG_SIGNATURE
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


class RasterPackTests(unittest.TestCase):
    def test_pack_uniform_atlas_writes_png_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            red = root / "red.png"
            green = root / "green.png"
            atlas = root / "atlas.png"

            write_rgba_png(red, 2, 2, bytes([255, 0, 0, 255]))
            write_rgba_png(green, 2, 2, bytes([0, 255, 0, 255]))

            metadata = pack_uniform_atlas(
                [red, green],
                atlas,
                columns=2,
                padding=1,
                power_of_two=True,
            )

            width, height, pixels = decode_rgba(atlas)

        self.assertEqual((width, height), (8, 2))
        self.assertEqual(metadata["frameCount"], 2)
        self.assertEqual(metadata["contentWidth"], 5)
        self.assertEqual(metadata["frames"][1]["x"], 3)
        self.assertEqual(pixels[0:4], bytes([255, 0, 0, 255]))
        self.assertEqual(pixels[3 * 4 : 4 * 4], bytes([0, 255, 0, 255]))

    def test_pack_rejects_mixed_frame_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.png"
            second = root / "b.png"
            write_rgba_png(first, 2, 2, bytes([1, 2, 3, 255]))
            write_rgba_png(second, 3, 2, bytes([4, 5, 6, 255]))

            with self.assertRaisesRegex(ValueError, "identical dimensions"):
                pack_uniform_atlas([first, second], root / "atlas.png")

    def test_rgb_png_is_promoted_to_opaque_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "rgb.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            raw = b"\x00" + bytes([7, 8, 9])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )

            width, height, pixels = decode_rgba(image)

        self.assertEqual((width, height), (1, 1))
        self.assertEqual(pixels, bytes([7, 8, 9, 255]))

    def test_recompress_png_preserves_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            optimized = root / "optimized.png"

            write_rgba_png(source, 4, 4, bytes([10, 20, 30, 255]))
            before = decode_rgba(source)
            report = recompress_png(source, optimized)
            after = decode_rgba(optimized)

        self.assertEqual(before, after)
        self.assertEqual(report["width"], 4)
        self.assertEqual(report["height"], 4)
        self.assertTrue(optimized.exists())

    def test_recompress_png_reports_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            optimized = root / "optimized.png"

            write_rgba_png(source, 8, 8, bytes([0, 0, 0, 0]))
            report = recompress_png(source, optimized)

        self.assertGreater(report["beforeBytes"], 0)
        self.assertGreater(report["afterBytes"], 0)
        self.assertEqual(
            report["savedBytes"],
            report["beforeBytes"] - report["afterBytes"],
        )


if __name__ == "__main__":
    unittest.main()
