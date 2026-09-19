import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from raster_pack import decode_rgba, encode_rgba, inspect_png, inspect_webp, inspect_webp_bytes, pack_compact_atlas, pack_uniform_atlas, recompress_png


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def webp_chunk(kind: bytes, payload: bytes) -> bytes:
    padding = b"\x00" if len(payload) & 1 else b""
    return kind + struct.pack("<I", len(payload)) + payload + padding


def webp_file(*chunks: bytes) -> bytes:
    body = b"WEBP" + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


ADAM7_PASSES = (
    (0, 0, 8, 8),
    (4, 0, 8, 8),
    (0, 4, 4, 8),
    (2, 0, 4, 4),
    (0, 2, 2, 4),
    (1, 0, 2, 2),
    (0, 1, 1, 2),
)


def adam7_extent(size: int, start: int, step: int) -> int:
    if size <= start:
        return 0
    return (size - start + step - 1) // step


def pack_indexed_samples(samples: list[int], depth: int) -> bytes:
    per_byte = 8 // depth
    output = bytearray()
    for start in range(0, len(samples), per_byte):
        byte = 0
        group = samples[start : start + per_byte]
        for index, sample in enumerate(group):
            shift = 8 - depth * (index + 1)
            byte |= sample << shift
        output.append(byte)
    return bytes(output)


def adam7_raw(
    width: int,
    height: int,
    pixel_bytes,
) -> bytes:
    raw = bytearray()
    for x_start, y_start, x_step, y_step in ADAM7_PASSES:
        pass_width = adam7_extent(width, x_start, x_step)
        pass_height = adam7_extent(height, y_start, y_step)
        if not pass_width or not pass_height:
            continue
        for py in range(pass_height):
            raw.append(0)
            y = y_start + py * y_step
            for px in range(pass_width):
                x = x_start + px * x_step
                raw.extend(pixel_bytes(x, y))
    return bytes(raw)


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

    def test_adam7_rgba8_reconstructs_full_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "adam7-rgba.png"
            width = height = 8
            ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 1)

            def pixel(x, y):
                return bytes([x * 10, y * 20, (x + y) * 5, 255])

            raw = adam7_raw(width, height, pixel)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            w, h, pixels = decode_rgba(image)

        self.assertEqual((w, h), (8, 8))
        self.assertEqual(pixels[(5 * 8 + 3) * 4 : (5 * 8 + 3) * 4 + 4], pixel(3, 5))
        self.assertEqual(pixels[(7 * 8 + 7) * 4 : (7 * 8 + 7) * 4 + 4], pixel(7, 7))

    def test_adam7_indexed_1bit_reconstructs_checkerboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "adam7-indexed.png"
            width = height = 8
            ihdr = struct.pack(">IIBBBBB", width, height, 1, 3, 0, 0, 1)
            palette = bytes([0, 0, 0, 255, 255, 255])

            raw = bytearray()
            for x_start, y_start, x_step, y_step in ADAM7_PASSES:
                pass_width = adam7_extent(width, x_start, x_step)
                pass_height = adam7_extent(height, y_start, y_step)
                if not pass_width or not pass_height:
                    continue
                for py in range(pass_height):
                    y = y_start + py * y_step
                    samples = [
                        (x_start + px * x_step + y) % 2
                        for px in range(pass_width)
                    ]
                    raw.append(0)
                    raw.extend(pack_indexed_samples(samples, 1))

            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"PLTE", palette)
                + chunk(b"IDAT", zlib.compress(bytes(raw)))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        for y in range(height):
            for x in range(width):
                start = (y * width + x) * 4
                expected = 255 if (x + y) % 2 else 0
                self.assertEqual(
                    pixels[start : start + 4],
                    bytes([expected, expected, expected, 255]),
                )

    def test_adam7_rgba16_reconstructs_and_downconverts(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "adam7-rgba16.png"
            width = height = 5
            ihdr = struct.pack(">IIBBBBB", width, height, 16, 6, 0, 0, 1)

            def pixel16(x, y):
                return struct.pack(
                    ">HHHH",
                    x * 10000,
                    y * 12000,
                    (x + y) * 7000,
                    65535,
                )

            raw = adam7_raw(width, height, pixel16)
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b"")
            )
            _, _, pixels = decode_rgba(image)

        x, y = 4, 3
        start = (y * width + x) * 4
        expected16 = (x * 10000, y * 12000, (x + y) * 7000, 65535)
        expected = bytes([
            (expected16[0] * 255 + 32767) // 65535,
            (expected16[1] * 255 + 32767) // 65535,
            (expected16[2] * 255 + 32767) // 65535,
            255,
        ])
        self.assertEqual(pixels[start : start + 4], expected)

    def test_adam7_expected_size_is_bounded_and_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "adam7-truncated.png"
            width = height = 8
            ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 1)
            raw = adam7_raw(width, height, lambda x, y: bytes([x, y, 0, 255]))
            image.write_bytes(
                PNG_SIGNATURE
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw[:-1]))
                + chunk(b"IEND", b"")
            )
            with self.assertRaisesRegex(ValueError, "unexpected PNG scanline length|truncated"):
                decode_rgba(image)

    def test_webp_vp8x_dimensions_alpha_and_animation(self):
        payload = bytes([0x12, 0, 0, 0]) + (319).to_bytes(3, "little") + (199).to_bytes(3, "little")
        anmf = b"\x00" * 16
        data = webp_file(
            webp_chunk(b"VP8X", payload),
            webp_chunk(b"ANIM", b"\x00" * 6),
            webp_chunk(b"ANMF", anmf),
        )
        info = inspect_webp_bytes(data)

        self.assertEqual((info["width"], info["height"]), (320, 200))
        self.assertTrue(info["hasAlpha"])
        self.assertTrue(info["animated"])
        self.assertEqual(info["codec"], "vp8x")

    def test_webp_vp8l_dimensions_and_alpha(self):
        width, height = 17, 9
        bits = (width - 1) | ((height - 1) << 14) | (1 << 28)
        payload = b"\x2f" + bits.to_bytes(4, "little")
        data = webp_file(webp_chunk(b"VP8L", payload))
        info = inspect_webp_bytes(data)

        self.assertEqual((info["width"], info["height"]), (width, height))
        self.assertTrue(info["hasAlpha"])
        self.assertEqual(info["codec"], "vp8l")

    def test_webp_vp8_lossy_dimensions(self):
        width, height = 640, 360
        frame_tag = (0).to_bytes(3, "little")
        payload = (
            frame_tag
            + b"\x9d\x01\x2a"
            + width.to_bytes(2, "little")
            + height.to_bytes(2, "little")
        )
        data = webp_file(webp_chunk(b"VP8 ", payload))
        info = inspect_webp_bytes(data)

        self.assertEqual((info["width"], info["height"]), (width, height))
        self.assertFalse(info["hasAlpha"])
        self.assertEqual(info["codec"], "vp8")

    def test_webp_alpha_chunk_marks_alpha(self):
        width, height = 12, 7
        frame_tag = (0).to_bytes(3, "little")
        vp8 = (
            frame_tag
            + b"\x9d\x01\x2a"
            + width.to_bytes(2, "little")
            + height.to_bytes(2, "little")
        )
        vp8x = bytes([0, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
        data = webp_file(
            webp_chunk(b"VP8X", vp8x),
            webp_chunk(b"ALPH", b"\x00"),
            webp_chunk(b"VP8 ", vp8),
        )
        info = inspect_webp_bytes(data)

        self.assertTrue(info["hasAlpha"])
        self.assertIn("ALPH", info["chunks"])

    def test_webp_incomplete_vp8x_is_rejected(self):
        payload = bytes([0, 0, 0, 0]) + (9).to_bytes(3, "little") + (9).to_bytes(3, "little")
        data = webp_file(webp_chunk(b"VP8X", payload))
        with self.assertRaisesRegex(ValueError, "requires exactly one VP8 or VP8L"):
            inspect_webp_bytes(data)

    def test_webp_reserved_vp8x_bits_are_rejected(self):
        payload = bytes([0x01, 0, 0, 0]) + (9).to_bytes(3, "little") + (9).to_bytes(3, "little")
        vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + (10).to_bytes(2, "little") + (10).to_bytes(2, "little")
        data = webp_file(webp_chunk(b"VP8X", payload), webp_chunk(b"VP8 ", vp8))
        with self.assertRaisesRegex(ValueError, "reserved feature bits"):
            inspect_webp_bytes(data)

    def test_webp_vp8x_dimension_mismatch_is_rejected(self):
        vp8x = bytes([0, 0, 0, 0]) + (19).to_bytes(3, "little") + (9).to_bytes(3, "little")
        vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + (21).to_bytes(2, "little") + (10).to_bytes(2, "little")
        data = webp_file(webp_chunk(b"VP8X", vp8x), webp_chunk(b"VP8 ", vp8))
        with self.assertRaisesRegex(ValueError, "canvas dimensions"):
            inspect_webp_bytes(data)

    def test_webp_lossy_alpha_flag_requires_alph_chunk(self):
        width, height = 20, 10
        vp8x = bytes([0x10, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
        vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
        data = webp_file(webp_chunk(b"VP8X", vp8x), webp_chunk(b"VP8 ", vp8))
        with self.assertRaisesRegex(ValueError, "requires ALPH"):
            inspect_webp_bytes(data)

    def test_webp_bad_riff_size_is_rejected(self):
        data = bytearray(webp_file(webp_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")))
        data[4:8] = (1).to_bytes(4, "little")
        with self.assertRaisesRegex(ValueError, "RIFF size"):
            inspect_webp_bytes(bytes(data))

    def test_webp_file_inspection_reads_from_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.webp"
            width, height = 20, 10
            bits = (width - 1) | ((height - 1) << 14)
            path.write_bytes(webp_file(webp_chunk(b"VP8L", b"\x2f" + bits.to_bytes(4, "little"))))
            info = inspect_webp(path)

        self.assertEqual((info["width"], info["height"]), (20, 10))
        self.assertEqual(info["format"], "webp")

    def test_uniform_atlas_trim_records_source_offsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.png"
            second = root / "b.png"
            atlas = root / "atlas.png"

            pixels = bytearray(4 * 4 * 4)
            for y in range(1, 3):
                for x in range(1, 3):
                    start = (y * 4 + x) * 4
                    pixels[start : start + 4] = bytes([255, 0, 0, 255])
            from raster_pack import encode_rgba
            encode_rgba(first, 4, 4, bytes(pixels))
            encode_rgba(second, 4, 4, bytes(pixels))

            metadata = pack_uniform_atlas(
                [first, second],
                atlas,
                columns=2,
                trim=True,
            )

        self.assertEqual(metadata["frames"][0]["width"], 2)
        self.assertEqual(metadata["frames"][0]["height"], 2)
        self.assertEqual(metadata["frames"][0]["offsetX"], 1)
        self.assertEqual(metadata["frames"][0]["offsetY"], 1)
        self.assertEqual(metadata["frames"][0]["sourceWidth"], 4)
        self.assertEqual(metadata["frames"][0]["sourceHeight"], 4)

    def test_uniform_atlas_extrudes_edge_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "a.png"
            atlas = root / "atlas.png"
            write_rgba_png(source, 1, 1, bytes([7, 8, 9, 255]))

            metadata = pack_uniform_atlas(
                [source],
                atlas,
                columns=1,
                extrude=1,
            )
            width, height, pixels = decode_rgba(atlas)

        self.assertEqual((width, height), (3, 3))
        self.assertEqual(metadata["frames"][0]["x"], 1)
        self.assertEqual(metadata["frames"][0]["y"], 1)
        expected = bytes([7, 8, 9, 255])
        for y in range(3):
            for x in range(3):
                start = (y * 3 + x) * 4
                self.assertEqual(pixels[start : start + 4], expected)

    def test_compact_atlas_packs_variable_size_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            c = root / "c.png"
            atlas = root / "atlas.png"

            write_rgba_png(a, 3, 3, bytes([255, 0, 0, 255]))
            write_rgba_png(b, 2, 1, bytes([0, 255, 0, 255]))
            write_rgba_png(c, 1, 2, bytes([0, 0, 255, 255]))

            metadata = pack_compact_atlas(
                [a, b, c],
                atlas,
                max_width=5,
                padding=1,
                trim=False,
            )
            width, height, pixels = decode_rgba(atlas)

        self.assertEqual(width, metadata["imageWidth"])
        self.assertEqual(height, metadata["imageHeight"])
        self.assertEqual(metadata["frameCount"], 3)
        self.assertEqual(metadata["packing"], "maxrects-best-short-side-fit")
        self.assertLessEqual(metadata["contentWidth"], 5)
        self.assertEqual(
            [frame["name"] for frame in metadata["frames"]],
            ["a.png", "b.png", "c.png"],
        )
        for frame in metadata["frames"]:
            start = (frame["y"] * width + frame["x"]) * 4
            self.assertEqual(pixels[start + 3], 255)

    def test_compact_atlas_rejects_frame_wider_than_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "wide.png"
            write_rgba_png(source, 8, 1, bytes([1, 2, 3, 255]))
            with self.assertRaisesRegex(ValueError, "cannot fit max atlas width"):
                pack_compact_atlas(
                    [source],
                    root / "atlas.png",
                    max_width=4,
                    trim=False,
                )

    def test_recompress_png_keeps_original_when_candidate_is_larger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            output = root / "output.png"
            write_rgba_png(source, 1, 1, bytes([1, 2, 3, 255]))
            original = source.read_bytes()

            with patch(
                "raster_pack._png_bytes_rgba",
                return_value=original + b"definitely-larger",
            ):
                report = recompress_png(source, output)

            result = output.read_bytes()

        self.assertEqual(result, original)
        self.assertFalse(report["keptOptimized"])
        self.assertEqual(report["afterBytes"], report["beforeBytes"])
        self.assertGreater(report["candidateBytes"], report["beforeBytes"])

    def test_uniform_atlas_width_budget_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            write_rgba_png(a, 4, 4, bytes([1, 2, 3, 255]))
            write_rgba_png(b, 4, 4, bytes([4, 5, 6, 255]))
            with self.assertRaisesRegex(ValueError, "atlas width"):
                pack_uniform_atlas(
                    [a, b],
                    root / "atlas.png",
                    columns=2,
                    max_width=7,
                )

    def test_uniform_atlas_pixel_budget_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            write_rgba_png(a, 4, 4, bytes([1, 2, 3, 255]))
            with self.assertRaisesRegex(ValueError, "pixel count"):
                pack_uniform_atlas(
                    [a],
                    root / "atlas.png",
                    max_pixels=15,
                )

    def test_compact_atlas_height_budget_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            write_rgba_png(a, 4, 4, bytes([1, 2, 3, 255]))
            write_rgba_png(b, 4, 4, bytes([4, 5, 6, 255]))
            with self.assertRaisesRegex(ValueError, "atlas budgets"):
                pack_compact_atlas(
                    [a, b],
                    root / "atlas.png",
                    max_width=4,
                    max_height=7,
                    trim=False,
                )

    def test_atlas_byte_budget_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "a.png"
            output = root / "atlas.png"
            write_rgba_png(source, 4, 4, bytes([1, 2, 3, 255]))
            output.write_bytes(b"existing-atlas")

            with self.assertRaisesRegex(ValueError, "file size"):
                pack_uniform_atlas(
                    [source],
                    output,
                    max_bytes=1,
                )

            preserved = output.read_bytes()

        self.assertEqual(preserved, b"existing-atlas")

    def test_compact_atlas_reports_occupancy_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            c = root / "c.png"
            write_rgba_png(a, 4, 4, bytes([255, 0, 0, 255]))
            write_rgba_png(b, 2, 4, bytes([0, 255, 0, 255]))
            write_rgba_png(c, 2, 2, bytes([0, 0, 255, 255]))

            metadata = pack_compact_atlas(
                [a, b, c],
                root / "atlas.png",
                max_width=6,
                trim=False,
            )

        self.assertEqual(metadata["spriteArea"], 28)
        self.assertEqual(metadata["packedArea"], 28)
        self.assertEqual(metadata["contentArea"], metadata["contentWidth"] * metadata["contentHeight"])
        self.assertEqual(metadata["atlasArea"], metadata["imageWidth"] * metadata["imageHeight"])
        self.assertGreater(metadata["contentOccupancyPercent"], 0)
        self.assertLessEqual(metadata["contentOccupancyPercent"], 100)
        self.assertGreater(metadata["atlasOccupancyPercent"], 0)
        self.assertLessEqual(metadata["atlasOccupancyPercent"], 100)

    def test_compact_atlas_regions_do_not_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, (width, height) in enumerate([(5, 3), (3, 5), (4, 2), (2, 4), (3, 3)]):
                path = root / f"{index}.png"
                write_rgba_png(path, width, height, bytes([index + 1, 0, 0, 255]))
                paths.append(path)

            metadata = pack_compact_atlas(
                paths,
                root / "atlas.png",
                max_width=8,
                padding=1,
                extrude=1,
                trim=False,
            )

        frames = metadata["frames"]
        for i, first in enumerate(frames):
            first_left = first["x"] - first["extrude"]
            first_top = first["y"] - first["extrude"]
            first_right = first["x"] + first["width"] + first["extrude"]
            first_bottom = first["y"] + first["height"] + first["extrude"]
            for second in frames[i + 1 :]:
                second_left = second["x"] - second["extrude"]
                second_top = second["y"] - second["extrude"]
                second_right = second["x"] + second["width"] + second["extrude"]
                second_bottom = second["y"] + second["height"] + second["extrude"]
                separated = (
                    first_right <= second_left
                    or second_right <= first_left
                    or first_bottom <= second_top
                    or second_bottom <= first_top
                )
                self.assertTrue(separated)

    def test_maxrects_compacts_better_than_simple_shelf_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sizes = [(6, 2), (4, 4), (2, 4), (2, 2)]
            paths = []
            for index, (width, height) in enumerate(sizes):
                path = root / f"{index}.png"
                write_rgba_png(path, width, height, bytes([index + 1, 0, 0, 255]))
                paths.append(path)

            metadata = pack_compact_atlas(
                paths,
                root / "atlas.png",
                max_width=8,
                trim=False,
            )

        simple_shelf_area = 8 * 8
        self.assertLessEqual(metadata["contentArea"], simple_shelf_area)

    def test_compact_atlas_reports_wasted_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            write_rgba_png(a, 4, 4, bytes([1, 2, 3, 255]))
            write_rgba_png(b, 2, 2, bytes([4, 5, 6, 255]))

            metadata = pack_compact_atlas(
                [a, b],
                root / "atlas.png",
                max_width=8,
                trim=False,
            )

        self.assertEqual(
            metadata["wastedPixels"],
            metadata["atlasArea"] - metadata["packedArea"],
        )

    def test_compact_atlas_minimum_occupancy_can_fail_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            write_rgba_png(a, 4, 4, bytes([1, 2, 3, 255]))
            write_rgba_png(b, 1, 1, bytes([4, 5, 6, 255]))

            with self.assertRaisesRegex(ValueError, "below minimum"):
                pack_compact_atlas(
                    [a, b],
                    root / "atlas.png",
                    max_width=16,
                    power_of_two=True,
                    min_occupancy=90,
                    trim=False,
                )

    def test_compact_atlas_rejects_invalid_occupancy_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            write_rgba_png(a, 1, 1, bytes([1, 2, 3, 255]))

            with self.assertRaisesRegex(ValueError, "min occupancy"):
                pack_compact_atlas(
                    [a],
                    root / "atlas.png",
                    min_occupancy=0,
                    trim=False,
                )

    def test_compact_atlas_auto_selects_best_evaluated_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sizes = [(7, 2), (5, 4), (4, 3), (3, 6), (2, 5), (2, 2)]
            paths = []
            for index, (width, height) in enumerate(sizes):
                path = root / f"{index}.png"
                write_rgba_png(path, width, height, bytes([index + 1, 0, 0, 255]))
                paths.append(path)

            metadata = pack_compact_atlas(
                paths,
                root / "atlas.png",
                max_width=10,
                trim=False,
                heuristic="auto",
            )

        evaluated = metadata["evaluatedHeuristics"]
        self.assertEqual(len(evaluated), 3)
        best = min(
            (item for item in evaluated if item["withinBudgets"]),
            key=lambda item: (
                item["encodedBytes"],
                item["atlasArea"],
                item["contentArea"],
                item["contentHeight"],
                item["contentWidth"],
                item["heuristic"],
            ),
        )
        self.assertEqual(metadata["selectionMetric"], "encoded-png-bytes")
        self.assertEqual(metadata["selectedHeuristic"], best["heuristic"])
        self.assertEqual(metadata["outputBytes"], best["encodedBytes"])

    def test_compact_atlas_auto_skips_heuristic_outside_byte_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sizes = [(7, 2), (5, 4), (4, 3), (3, 6), (2, 5), (2, 2)]
            paths = []
            for index, (width, height) in enumerate(sizes):
                path = root / f"{index}.png"
                write_rgba_png(path, width, height, bytes([index * 20, 10, 255 - index * 20, 255]))
                paths.append(path)

            baseline = pack_compact_atlas(
                paths,
                root / "baseline.png",
                max_width=10,
                trim=False,
                heuristic="auto",
            )
            evaluated = sorted(
                baseline["evaluatedHeuristics"],
                key=lambda item: item["encodedBytes"],
            )
            if evaluated[0]["encodedBytes"] < evaluated[-1]["encodedBytes"]:
                budget = evaluated[-1]["encodedBytes"] - 1
                constrained = pack_compact_atlas(
                    paths,
                    root / "constrained.png",
                    max_width=10,
                    max_bytes=budget,
                    trim=False,
                    heuristic="auto",
                )
                selected = next(
                    item for item in constrained["evaluatedHeuristics"]
                    if item["heuristic"] == constrained["selectedHeuristic"]
                )
                self.assertTrue(selected["withinBudgets"])
                self.assertLessEqual(selected["encodedBytes"], budget)

    def test_compact_atlas_forced_heuristic_is_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            write_rgba_png(a, 4, 3, bytes([1, 2, 3, 255]))
            write_rgba_png(b, 2, 5, bytes([4, 5, 6, 255]))

            metadata = pack_compact_atlas(
                [a, b],
                root / "atlas.png",
                max_width=8,
                trim=False,
                heuristic="best-area-fit",
            )

        self.assertEqual(metadata["requestedHeuristic"], "best-area-fit")
        self.assertEqual(metadata["selectedHeuristic"], "best-area-fit")
        self.assertEqual(len(metadata["evaluatedHeuristics"]), 1)

    def test_compact_atlas_rejects_unknown_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            write_rgba_png(a, 1, 1, bytes([1, 2, 3, 255]))

            with self.assertRaisesRegex(ValueError, "unsupported compact atlas heuristic"):
                pack_compact_atlas(
                    [a],
                    root / "atlas.png",
                    heuristic="unknown",
                    trim=False,
                )

    def test_compact_atlas_rotation_can_fit_frame_that_is_too_wide(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "wide.png"
            atlas = root / "atlas.png"
            pixels = bytes([
                255, 0, 0, 255,
                0, 255, 0, 255,
                0, 0, 255, 255,
                255, 255, 0, 255,
                255, 0, 255, 255,
                0, 255, 255, 255,
                10, 20, 30, 255,
                40, 50, 60, 255,
            ])
            encode_rgba(source, 4, 2, pixels)

            metadata = pack_compact_atlas(
                [source],
                atlas,
                max_width=2,
                trim=False,
                allow_rotation=True,
                heuristic="best-short-side-fit",
            )
            width, height, packed = decode_rgba(atlas)

        frame = metadata["frames"][0]
        self.assertTrue(frame["rotated"])
        self.assertEqual(frame["rotationDegrees"], 90)
        self.assertEqual((frame["width"], frame["height"]), (2, 4))
        self.assertEqual((frame["sourceRegionWidth"], frame["sourceRegionHeight"]), (4, 2))
        self.assertEqual((width, height), (2, 4))
        self.assertEqual(
            packed,
            bytes([
                255, 0, 255, 255, 255, 0, 0, 255,
                0, 255, 255, 255, 0, 255, 0, 255,
                10, 20, 30, 255, 0, 0, 255, 255,
                40, 50, 60, 255, 255, 255, 0, 255,
            ]),
        )

    def test_compact_atlas_rotation_is_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "wide.png"
            write_rgba_png(source, 4, 2, bytes([1, 2, 3, 255]))
            with self.assertRaisesRegex(ValueError, "cannot fit max atlas width"):
                pack_compact_atlas(
                    [source],
                    root / "atlas.png",
                    max_width=2,
                    trim=False,
                )

    def test_compact_atlas_rotation_metadata_counts_rotated_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.png"
            b = root / "b.png"
            write_rgba_png(a, 4, 2, bytes([1, 2, 3, 255]))
            write_rgba_png(b, 1, 1, bytes([4, 5, 6, 255]))
            metadata = pack_compact_atlas(
                [a, b],
                root / "atlas.png",
                max_width=2,
                trim=False,
                allow_rotation=True,
            )

        self.assertTrue(metadata["rotationAllowed"])
        self.assertGreaterEqual(metadata["rotatedFrameCount"], 1)


if __name__ == "__main__":
    unittest.main()
