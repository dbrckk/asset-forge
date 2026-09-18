import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from raster_pack import decode_rgba, inspect_png, pack_uniform_atlas, recompress_png


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
            output_exists = optimized.exists()

        self.assertEqual(before, after)
        self.assertEqual(report["width"], 4)
        self.assertEqual(report["height"], 4)
        self.assertTrue(output_exists)

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

    def test_grayscale_png_decodes_to_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(b"\x00\x7f"))
                + chunk(b"IEND", b"")
            )
            width, height, pixels = decode_rgba(image)

        self.assertEqual((width, height), (1, 1))
        self.assertEqual(pixels, bytes([127, 127, 127, 255]))

    def test_grayscale_alpha_png_decodes_to_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray-alpha.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 4, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(b"\x00\x44\x80"))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(pixels, bytes([68, 68, 68, 128]))

    def test_indexed_png_with_transparency_decodes_to_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "indexed.png"
            ihdr = struct.pack(">IIBBBBB", 2, 1, 8, 3, 0, 0, 0)
            palette = bytes([255, 0, 0, 0, 255, 0])
            transparency = bytes([255, 64])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"tRNS", transparency)
                + chunk(b"IDAT", zlib.compress(b"\x00\x00\x01"))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([255, 0, 0, 255, 0, 255, 0, 64]),
        )

    def test_rejects_invalid_ihdr_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", b"short")
                + chunk(b"IDAT", zlib.compress(b""))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "13-byte IHDR|IHDR must be 13 bytes"):
                decode_rgba(image)

    def test_rejects_zero_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            ihdr = struct.pack(">IIBBBBB", 0, 1, 8, 6, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(b""))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "width and height must be > 0"):
                decode_rgba(image)

    def test_rejects_duplicate_ihdr(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "duplicate IHDR"):
                decode_rgba(image)

    def test_rejects_non_consecutive_idat(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
            compressed = zlib.compress(b"\x00\x00\x00\x00\xff")
            split = max(1, len(compressed) // 2)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", compressed[:split])
                + chunk(b"tEXt", b"k\x00v")
                + chunk(b"IDAT", compressed[split:])
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "IDAT chunks must be consecutive"):
                decode_rgba(image)

    def test_rejects_trailing_data_after_iend(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            write_rgba_png(image, 1, 1, bytes([1, 2, 3, 255]))
            image.write_bytes(image.read_bytes() + b"trailing")
            with self.assertRaisesRegex(ValueError, "trailing data after IEND"):
                decode_rgba(image)

    def test_rejects_indexed_trns_longer_than_palette(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", bytes([255, 0, 0]))
                + chunk(b"tRNS", bytes([255, 128]))
                + chunk(b"IDAT", zlib.compress(b"\x00\x00"))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "tRNS exceeds palette length"):
                decode_rgba(image)

    def test_rejects_trns_for_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", b"\x00")
                + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "tRNS is not allowed"):
                decode_rgba(image)

    def test_truecolor_trns_is_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "rgb-trns.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            transparency = struct.pack(">HHH", 7, 8, 9)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", transparency)
                + chunk(b"IDAT", zlib.compress(b"\x00\x07\x08\x09"))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(pixels, bytes([7, 8, 9, 0]))

    def test_rejects_decompressed_data_larger_than_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bomb.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
            raw = b"\x00\x00\x00\x00\xff" + (b"x" * 1000)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "exceeds expected scanline size"):
                decode_rgba(image)

    def test_hardened_inspector_reports_palette_and_transparency(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "indexed.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", bytes([255, 0, 0]))
                + chunk(b"tRNS", bytes([128]))
                + chunk(b"IDAT", zlib.compress(b"\x00\x00"))
                + chunk(b"IEND", b"")
            )
            info = inspect_png(image)

        self.assertEqual(info["paletteEntries"], 1)
        self.assertTrue(info["hasAlpha"])
        self.assertGreater(info["compressedImageBytes"], 0)

    def test_oversized_file_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "small.png"
            write_rgba_png(image, 1, 1, bytes([1, 2, 3, 255]))
            with patch("raster_pack.MAX_PNG_FILE_BYTES", 1):
                with self.assertRaisesRegex(ValueError, "exceeds file limit"):
                    inspect_png(image)

    def test_indexed_1bit_png_decodes_to_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "indexed1.png"
            ihdr = struct.pack(">IIBBBBB", 8, 1, 1, 3, 0, 0, 0)
            palette = bytes([0, 0, 0, 255, 255, 255])
            # samples: 0,1,0,1,1,0,1,0 => 0b01011010
            raw = b"\x00" + bytes([0b01011010])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            width, height, pixels = decode_rgba(image)

        self.assertEqual((width, height), (8, 1))
        self.assertEqual(
            pixels,
            b"".join(
                bytes([255, 255, 255, 255]) if bit else bytes([0, 0, 0, 255])
                for bit in [0, 1, 0, 1, 1, 0, 1, 0]
            ),
        )

    def test_indexed_2bit_png_decodes_to_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "indexed2.png"
            ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 3, 0, 0, 0)
            palette = bytes([
                255, 0, 0,
                0, 255, 0,
                0, 0, 255,
                255, 255, 0,
            ])
            # samples 0,1,2,3 => 00 01 10 11
            raw = b"\x00" + bytes([0b00011011])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                255, 0, 0, 255,
                0, 255, 0, 255,
                0, 0, 255, 255,
                255, 255, 0, 255,
            ]),
        )

    def test_indexed_4bit_png_ignores_padding_nibble(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "indexed4.png"
            ihdr = struct.pack(">IIBBBBB", 3, 1, 4, 3, 0, 0, 0)
            palette = b"".join(bytes([i, 0, 0]) for i in range(16))
            # samples 1,2,3; low nibble of second byte is row padding and must be ignored
            raw = b"\x00" + bytes([0x12, 0x3F])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                1, 0, 0, 255,
                2, 0, 0, 255,
                3, 0, 0, 255,
            ]),
        )

    def test_indexed_low_bit_depth_transparency_is_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "indexed-trns.png"
            ihdr = struct.pack(">IIBBBBB", 2, 1, 1, 3, 0, 0, 0)
            palette = bytes([10, 20, 30, 40, 50, 60])
            transparency = bytes([255, 0])
            raw = b"\x00" + bytes([0b01000000])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"tRNS", transparency)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                10, 20, 30, 255,
                40, 50, 60, 0,
            ]),
        )

    def test_indexed_low_bit_depth_palette_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "bad-indexed.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 1, 3, 0, 0, 0)
            palette = bytes([
                0, 0, 0,
                1, 1, 1,
                2, 2, 2,
            ])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"IDAT", zlib.compress(b"\x00\x00"))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "more entries than indexed bit depth allows"):
                decode_rgba(image)

    def test_grayscale_1bit_png_decodes_to_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray1.png"
            ihdr = struct.pack(">IIBBBBB", 8, 1, 1, 0, 0, 0, 0)
            raw = b"\x00" + bytes([0b01011010])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            b"".join(
                bytes([255, 255, 255, 255]) if bit else bytes([0, 0, 0, 255])
                for bit in [0, 1, 0, 1, 1, 0, 1, 0]
            ),
        )

    def test_grayscale_2bit_png_scales_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray2.png"
            ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 0, 0, 0, 0)
            raw = b"\x00" + bytes([0b00011011])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                0, 0, 0, 255,
                85, 85, 85, 255,
                170, 170, 170, 255,
                255, 255, 255, 255,
            ]),
        )

    def test_grayscale_4bit_png_ignores_padding_nibble(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray4.png"
            ihdr = struct.pack(">IIBBBBB", 3, 1, 4, 0, 0, 0, 0)
            raw = b"\x00" + bytes([0x05, 0xAF])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                0, 0, 0, 255,
                85, 85, 85, 255,
                170, 170, 170, 255,
            ]),
        )

    def test_grayscale_low_bit_depth_trns_is_applied_before_scaling(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray2-trns.png"
            ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 0, 0, 0, 0)
            transparency = struct.pack(">H", 2)
            raw = b"\x00" + bytes([0b00011011])
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", transparency)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                0, 0, 0, 255,
                85, 85, 85, 255,
                170, 170, 170, 0,
                255, 255, 255, 255,
            ]),
        )

    def test_grayscale_trns_out_of_range_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray2-bad-trns.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 2, 0, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", struct.pack(">H", 4))
                + chunk(b"IDAT", zlib.compress(b"\x00\x00"))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "tRNS sample exceeds bit depth"):
                decode_rgba(image)

    def test_grayscale_16bit_png_decodes_to_rgba8(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray16.png"
            ihdr = struct.pack(">IIBBBBB", 3, 1, 16, 0, 0, 0, 0)
            raw = b"\x00" + struct.pack(">HHH", 0, 32768, 65535)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(
            pixels,
            bytes([
                0, 0, 0, 255,
                128, 128, 128, 255,
                255, 255, 255, 255,
            ]),
        )

    def test_truecolor_16bit_png_decodes_to_rgba8(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "rgb16.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0)
            raw = b"\x00" + struct.pack(">HHH", 65535, 32768, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(pixels, bytes([255, 128, 0, 255]))

    def test_grayscale_alpha_16bit_png_decodes_to_rgba8(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray-alpha16.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 4, 0, 0, 0)
            raw = b"\x00" + struct.pack(">HH", 32768, 16384)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(pixels, bytes([128, 128, 128, 64]))

    def test_rgba_16bit_png_decodes_to_rgba8(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "rgba16.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 6, 0, 0, 0)
            raw = b"\x00" + struct.pack(">HHHH", 65535, 32768, 0, 16384)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        self.assertEqual(pixels, bytes([255, 128, 0, 64]))

    def test_grayscale_16bit_trns_compares_original_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "gray16-trns.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 0, 0, 0, 0)
            sample = 40000
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", struct.pack(">H", sample))
                + chunk(b"IDAT", zlib.compress(b"\x00" + struct.pack(">H", sample)))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        expected_gray = (sample * 255 + 32767) // 65535
        self.assertEqual(pixels, bytes([expected_gray, expected_gray, expected_gray, 0]))

    def test_truecolor_16bit_trns_compares_original_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "rgb16-trns.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0)
            samples = (1000, 2000, 3000)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", struct.pack(">HHH", *samples))
                + chunk(b"IDAT", zlib.compress(b"\x00" + struct.pack(">HHH", *samples)))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        expected = [
            (value * 255 + 32767) // 65535
            for value in samples
        ]
        self.assertEqual(pixels, bytes(expected + [0]))

    def test_truecolor_8bit_trns_out_of_range_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "rgb8-bad-trns.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"tRNS", struct.pack(">HHH", 256, 0, 0))
                + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "tRNS sample exceeds bit depth"):
                decode_rgba(image)


if __name__ == "__main__":
    unittest.main()
