from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("file is not a valid PNG")

    chunks: list[tuple[bytes, bytes]] = []
    offset = 8
    saw_iend = False

    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")

        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")

        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("invalid PNG CRC")

        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND":
            saw_iend = True
            break

    if not saw_iend:
        raise ValueError("PNG is missing IEND")
    return chunks


def _paeth(a: int, b: int, c: int) -> int:
    prediction = a + b - c
    pa = abs(prediction - a)
    pb = abs(prediction - b)
    pc = abs(prediction - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_rgba(path: Path) -> tuple[int, int, bytes]:
    chunks = _chunks(path.read_bytes())
    if not chunks or chunks[0][0] != b"IHDR":
        raise ValueError("PNG is missing IHDR")

    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", chunks[0][1]
    )
    if (
        depth != 8
        or color_type not in {2, 6}
        or compression != 0
        or filtering != 0
        or interlace != 0
    ):
        raise ValueError("packing supports non-interlaced 8-bit RGB/RGBA PNG only")

    bytes_per_pixel = 4 if color_type == 6 else 3
    stride = width * bytes_per_pixel
    raw = zlib.decompress(b"".join(payload for kind, payload in chunks if kind == b"IDAT"))

    if len(raw) != (stride + 1) * height:
        raise ValueError("unexpected PNG scanline length")

    rows: list[bytearray] = []
    previous = bytearray(stride)
    position = 0

    for _ in range(height):
        filter_type = raw[position]
        position += 1
        scanline = bytearray(raw[position : position + stride])
        position += stride
        reconstructed = bytearray(stride)

        for index, value in enumerate(scanline):
            left = reconstructed[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0

            if filter_type == 0:
                reconstructed_value = value
            elif filter_type == 1:
                reconstructed_value = (value + left) & 255
            elif filter_type == 2:
                reconstructed_value = (value + above) & 255
            elif filter_type == 3:
                reconstructed_value = (value + ((left + above) // 2)) & 255
            elif filter_type == 4:
                reconstructed_value = (value + _paeth(left, above, upper_left)) & 255
            else:
                raise ValueError(f"unsupported PNG filter {filter_type}")

            reconstructed[index] = reconstructed_value

        rows.append(reconstructed)
        previous = reconstructed

    rgba = bytearray(width * height * 4)
    destination = 0

    for row in rows:
        for index in range(0, len(row), bytes_per_pixel):
            rgba[destination : destination + 3] = row[index : index + 3]
            rgba[destination + 3] = row[index + 3] if bytes_per_pixel == 4 else 255
            destination += 4

    return width, height, bytes(rgba)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def encode_rgba(path: Path, width: int, height: int, pixels: bytes) -> None:
    if len(pixels) != width * height * 4:
        raise ValueError("RGBA buffer size mismatch")

    rows = []
    for y in range(height):
        start = y * width * 4
        rows.append(b"\x00" + pixels[start : start + width * 4])

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + _chunk(b"IEND", b"")
    )


def _next_power_of_two(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (value - 1).bit_length()


def pack_uniform_atlas(
    inputs: list[Path],
    output: Path,
    columns: int | None = None,
    padding: int = 0,
    power_of_two: bool = False,
) -> dict:
    if not inputs:
        raise ValueError("at least one input PNG is required")
    if padding < 0:
        raise ValueError("padding must be >= 0")

    decoded = [decode_rgba(Path(path)) for path in inputs]
    frame_width, frame_height = decoded[0][0], decoded[0][1]

    if any((width, height) != (frame_width, frame_height) for width, height, _ in decoded):
        raise ValueError("all frames must have identical dimensions")

    frame_count = len(decoded)
    column_count = columns or math.ceil(math.sqrt(frame_count))
    if column_count <= 0:
        raise ValueError("columns must be > 0")

    row_count = math.ceil(frame_count / column_count)
    content_width = column_count * frame_width + max(0, column_count - 1) * padding
    content_height = row_count * frame_height + max(0, row_count - 1) * padding

    atlas_width = _next_power_of_two(content_width) if power_of_two else content_width
    atlas_height = _next_power_of_two(content_height) if power_of_two else content_height

    canvas = bytearray(atlas_width * atlas_height * 4)
    frames = []

    for index, (_, _, pixels) in enumerate(decoded):
        column = index % column_count
        row = index // column_count
        x = column * (frame_width + padding)
        y = row * (frame_height + padding)

        for source_y in range(frame_height):
            source_start = source_y * frame_width * 4
            destination_start = ((y + source_y) * atlas_width + x) * 4
            canvas[destination_start : destination_start + frame_width * 4] = pixels[
                source_start : source_start + frame_width * 4
            ]

        frames.append(
            {
                "index": index,
                "name": Path(inputs[index]).name,
                "x": x,
                "y": y,
                "width": frame_width,
                "height": frame_height,
            }
        )

    encode_rgba(output, atlas_width, atlas_height, bytes(canvas))

    return {
        "image": output.name,
        "imageWidth": atlas_width,
        "imageHeight": atlas_height,
        "contentWidth": content_width,
        "contentHeight": content_height,
        "columns": column_count,
        "rows": row_count,
        "frameCount": frame_count,
        "padding": padding,
        "frames": frames,
    }
