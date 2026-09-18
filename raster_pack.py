from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_FILE_BYTES = 256 * 1024 * 1024
MAX_PNG_CHUNK_BYTES = 64 * 1024 * 1024
MAX_PNG_CHUNKS = 10000
MAX_PNG_PIXELS = 100_000_000
MAX_DECOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_WEBP_FILE_BYTES = 256 * 1024 * 1024
MAX_WEBP_CHUNKS = 10000


def _read_webp_bytes(path: Path) -> bytes:
    size = path.stat().st_size
    if size > MAX_WEBP_FILE_BYTES:
        raise ValueError(f"WebP exceeds file limit {MAX_WEBP_FILE_BYTES}")
    return path.read_bytes()


def _webp_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if len(data) > MAX_WEBP_FILE_BYTES:
        raise ValueError(f"WebP exceeds file limit {MAX_WEBP_FILE_BYTES}")
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("file is not a valid WebP RIFF container")

    riff_size = struct.unpack("<I", data[4:8])[0]
    if riff_size + 8 != len(data):
        raise ValueError("WebP RIFF size does not match file length")

    chunks: list[tuple[bytes, bytes]] = []
    offset = 12
    while offset < len(data):
        if len(chunks) >= MAX_WEBP_CHUNKS:
            raise ValueError(f"WebP exceeds chunk count limit {MAX_WEBP_CHUNKS}")
        if offset + 8 > len(data):
            raise ValueError("truncated WebP chunk header")
        kind = data[offset : offset + 4]
        length = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
        payload_start = offset + 8
        payload_end = payload_start + length
        if payload_end > len(data):
            raise ValueError("truncated WebP chunk")
        chunks.append((kind, data[payload_start:payload_end]))
        offset = payload_end + (length & 1)

    if offset != len(data):
        raise ValueError("invalid WebP chunk padding")
    if not chunks:
        raise ValueError("WebP contains no chunks")
    return chunks


def _webp_vp8x_info(payload: bytes) -> dict:
    if len(payload) != 10:
        raise ValueError("WebP VP8X chunk must be 10 bytes")
    if payload[1:4] != b"\x00\x00\x00":
        raise ValueError("WebP VP8X reserved bytes must be zero")
    width = 1 + int.from_bytes(payload[4:7], "little")
    height = 1 + int.from_bytes(payload[7:10], "little")
    return {
        "width": width,
        "height": height,
        "hasAlpha": bool(payload[0] & 0x10),
        "animated": bool(payload[0] & 0x02),
        "extended": True,
        "codec": "vp8x",
    }


def _webp_vp8l_info(payload: bytes) -> dict:
    if len(payload) < 5 or payload[0] != 0x2F:
        raise ValueError("invalid WebP VP8L header")
    bits = int.from_bytes(payload[1:5], "little")
    version = (bits >> 29) & 0x7
    if version != 0:
        raise ValueError("unsupported WebP VP8L version")
    return {
        "width": (bits & 0x3FFF) + 1,
        "height": ((bits >> 14) & 0x3FFF) + 1,
        "hasAlpha": bool((bits >> 28) & 1),
        "animated": False,
        "extended": False,
        "codec": "vp8l",
    }


def _webp_vp8_info(payload: bytes) -> dict:
    if len(payload) < 10:
        raise ValueError("truncated WebP VP8 frame header")
    frame_tag = int.from_bytes(payload[:3], "little")
    if frame_tag & 1:
        raise ValueError("WebP VP8 still image must start with a key frame")
    if payload[3:6] != b"\x9d\x01\x2a":
        raise ValueError("invalid WebP VP8 key-frame signature")
    width = int.from_bytes(payload[6:8], "little") & 0x3FFF
    height = int.from_bytes(payload[8:10], "little") & 0x3FFF
    if width <= 0 or height <= 0:
        raise ValueError("WebP VP8 width and height must be > 0")
    return {
        "width": width,
        "height": height,
        "hasAlpha": False,
        "animated": False,
        "extended": False,
        "codec": "vp8",
    }


def inspect_webp(path: Path) -> dict:
    data = _read_webp_bytes(path)
    chunks = _webp_chunks(data)
    by_kind: dict[bytes, list[bytes]] = {}
    for kind, payload in chunks:
        by_kind.setdefault(kind, []).append(payload)

    if len(by_kind.get(b"VP8X", [])) > 1:
        raise ValueError("WebP contains duplicate VP8X")
    if b"VP8X" in by_kind:
        if chunks[0][0] != b"VP8X":
            raise ValueError("WebP VP8X must be the first chunk")
        info = _webp_vp8x_info(by_kind[b"VP8X"][0])
    elif b"VP8L" in by_kind:
        if len(by_kind[b"VP8L"]) != 1:
            raise ValueError("WebP contains duplicate VP8L image chunks")
        info = _webp_vp8l_info(by_kind[b"VP8L"][0])
    elif b"VP8 " in by_kind:
        if len(by_kind[b"VP8 "]) != 1:
            raise ValueError("WebP contains duplicate VP8 image chunks")
        info = _webp_vp8_info(by_kind[b"VP8 "][0])
    else:
        raise ValueError("WebP contains no VP8X, VP8L, or VP8 image header")

    if info["width"] * info["height"] > MAX_PNG_PIXELS:
        raise ValueError(f"WebP exceeds pixel limit {MAX_PNG_PIXELS}")

    if b"ALPH" in by_kind:
        info["hasAlpha"] = True
    if b"ANIM" in by_kind or b"ANMF" in by_kind:
        info["animated"] = True

    info.update(
        {
            "format": "webp",
            "bytes": len(data),
            "chunkCount": len(chunks),
            "chunks": [kind.decode("latin1") for kind, _ in chunks],
        }
    )
    return info


def _read_png_bytes(path: Path) -> bytes:
    size = path.stat().st_size
    if size > MAX_PNG_FILE_BYTES:
        raise ValueError(f"PNG exceeds file limit {MAX_PNG_FILE_BYTES}")
    return path.read_bytes()


def _chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if len(data) > MAX_PNG_FILE_BYTES:
        raise ValueError(f"PNG exceeds file limit {MAX_PNG_FILE_BYTES}")
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        raise ValueError("file is not a valid PNG")

    chunks: list[tuple[bytes, bytes]] = []
    offset = 8
    saw_iend = False
    saw_ihdr = False
    saw_idat = False
    idat_closed = False

    while offset < len(data):
        if len(chunks) >= MAX_PNG_CHUNKS:
            raise ValueError(f"PNG exceeds chunk count limit {MAX_PNG_CHUNKS}")
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")

        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        if length > MAX_PNG_CHUNK_BYTES:
            raise ValueError(f"PNG chunk exceeds size limit {MAX_PNG_CHUNK_BYTES}")
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")

        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("invalid PNG CRC")

        if not saw_ihdr:
            if kind != b"IHDR" or length != 13:
                raise ValueError("PNG must start with a 13-byte IHDR")
            saw_ihdr = True
        elif kind == b"IHDR":
            raise ValueError("PNG contains duplicate IHDR")

        if kind == b"IDAT":
            if idat_closed:
                raise ValueError("PNG IDAT chunks must be consecutive")
            saw_idat = True
        elif saw_idat and kind != b"IEND":
            idat_closed = True

        if kind == b"IEND":
            if length != 0:
                raise ValueError("PNG IEND must be empty")
            saw_iend = True
            offset = end
            if offset != len(data):
                raise ValueError("PNG contains trailing data after IEND")
            chunks.append((kind, payload))
            break

        chunks.append((kind, payload))
        offset = end

    if not saw_iend:
        raise ValueError("PNG is missing IEND")
    if not saw_idat:
        raise ValueError("PNG is missing IDAT")
    return chunks


def _validate_ihdr(payload: bytes) -> tuple[int, int, int, int, int, int, int]:
    if len(payload) != 13:
        raise ValueError("PNG IHDR must be 13 bytes")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", payload
    )
    if width <= 0 or height <= 0:
        raise ValueError("PNG width and height must be > 0")
    if width * height > MAX_PNG_PIXELS:
        raise ValueError(f"PNG exceeds pixel limit {MAX_PNG_PIXELS}")
    if compression != 0 or filtering != 0 or interlace not in {0, 1}:
        raise ValueError("unsupported PNG compression/filter/interlace method")
    valid_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if color_type not in valid_depths or depth not in valid_depths[color_type]:
        raise ValueError(f"invalid PNG bit depth {depth} for color type {color_type}")
    return width, height, depth, color_type, compression, filtering, interlace


def _validate_palette_transparency(
    chunks: list[tuple[bytes, bytes]],
    *,
    depth: int,
    color_type: int,
) -> tuple[list[tuple[int, int, int]], bytes]:
    palette: list[tuple[int, int, int]] = []
    transparency = b""
    saw_plte = False
    saw_trns = False
    saw_idat = False

    for kind, payload in chunks:
        if kind == b"IDAT":
            saw_idat = True
        elif kind == b"PLTE":
            if saw_plte:
                raise ValueError("PNG contains duplicate PLTE")
            if saw_idat:
                raise ValueError("PNG PLTE must appear before IDAT")
            if color_type in {0, 4}:
                raise ValueError("PNG PLTE is not allowed for grayscale color types")
            if not payload or len(payload) % 3 or len(payload) > 768:
                raise ValueError("invalid PLTE length")
            entries = len(payload) // 3
            if color_type == 3 and entries > (1 << depth):
                raise ValueError("PNG palette has more entries than indexed bit depth allows")
            palette = [
                (payload[i], payload[i + 1], payload[i + 2])
                for i in range(0, len(payload), 3)
            ]
            saw_plte = True
        elif kind == b"tRNS":
            if saw_trns:
                raise ValueError("PNG contains duplicate tRNS")
            if saw_idat:
                raise ValueError("PNG tRNS must appear before IDAT")
            if color_type == 3:
                if not saw_plte:
                    raise ValueError("indexed PNG tRNS requires preceding PLTE")
                if len(payload) > len(palette):
                    raise ValueError("indexed PNG tRNS exceeds palette length")
            elif color_type == 0:
                if len(payload) != 2:
                    raise ValueError("grayscale PNG tRNS must be 2 bytes")
                transparent_gray = struct.unpack(">H", payload)[0]
                if transparent_gray >= (1 << depth):
                    raise ValueError("grayscale PNG tRNS sample exceeds bit depth")
            elif color_type == 2:
                if len(payload) != 6:
                    raise ValueError("truecolor PNG tRNS must be 6 bytes")
                transparent_rgb = struct.unpack(">HHH", payload)
                max_sample = (1 << depth) - 1
                if any(sample > max_sample for sample in transparent_rgb):
                    raise ValueError("truecolor PNG tRNS sample exceeds bit depth")
            else:
                raise ValueError("PNG tRNS is not allowed for alpha color types")
            transparency = payload
            saw_trns = True

    if color_type == 3 and not saw_plte:
        raise ValueError("indexed PNG is missing PLTE")
    return palette, transparency


def _decompress_idat(data: bytes, expected_size: int) -> bytes:
    if expected_size < 0 or expected_size > MAX_DECOMPRESSED_BYTES:
        raise ValueError(f"PNG decompressed data exceeds limit {MAX_DECOMPRESSED_BYTES}")

    inflater = zlib.decompressobj()
    try:
        raw = inflater.decompress(data, expected_size + 1)
        if len(raw) > expected_size:
            raise ValueError("PNG decompressed data exceeds expected scanline size")

        while inflater.unconsumed_tail and not inflater.eof:
            before = len(inflater.unconsumed_tail)
            extra = inflater.decompress(inflater.unconsumed_tail, 1)
            if extra:
                raise ValueError("PNG decompressed data exceeds expected scanline size")
            if len(inflater.unconsumed_tail) >= before and not inflater.eof:
                raise ValueError("PNG zlib stream could not be fully consumed within bounds")
    except zlib.error as exc:
        raise ValueError(f"invalid PNG zlib stream: {exc}") from exc

    if len(raw) != expected_size:
        raise ValueError("unexpected PNG scanline length")
    if not inflater.eof:
        raise ValueError("truncated PNG zlib stream")
    if inflater.unused_data:
        raise ValueError("PNG IDAT contains trailing compressed data")
    return raw


def inspect_png(path: Path) -> dict:
    data = _read_png_bytes(path)
    chunks = _chunks(data)
    width, height, bit_depth, color_type, compression, filtering, interlace = _validate_ihdr(
        chunks[0][1]
    )
    palette, transparency = _validate_palette_transparency(
        chunks,
        depth=bit_depth,
        color_type=color_type,
    )
    return {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "hasAlpha": color_type in {4, 6} or bool(transparency),
        "paletteEntries": len(palette) if palette else None,
        "compressedImageBytes": sum(
            len(payload) for kind, payload in chunks if kind == b"IDAT"
        ),
        "compression": compression,
        "filter": filtering,
        "interlace": interlace,
        "bytes": len(data),
    }


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


def _unfilter_scanlines(raw: bytes, stride: int, height: int, filter_bpp: int) -> list[bytearray]:
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
            left = reconstructed[index - filter_bpp] if index >= filter_bpp else 0
            above = previous[index]
            upper_left = previous[index - filter_bpp] if index >= filter_bpp else 0

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

    return rows


def _scanline_layout(width: int, depth: int, color_type: int) -> tuple[int, int]:
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    bits_per_pixel = channels * depth
    stride = (width * bits_per_pixel + 7) // 8
    filter_bpp = max(1, (bits_per_pixel + 7) // 8)
    return stride, filter_bpp


def _unpack_packed_samples(row: bytes, width: int, depth: int) -> list[int]:
    if depth == 8:
        return list(row[:width])
    if depth not in {1, 2, 4}:
        raise ValueError(f"unsupported packed PNG bit depth {depth}")

    mask = (1 << depth) - 1
    values: list[int] = []
    for byte in row:
        shift = 8 - depth
        while shift >= 0 and len(values) < width:
            values.append((byte >> shift) & mask)
            shift -= depth
        if len(values) >= width:
            break
    if len(values) != width:
        raise ValueError("packed PNG row does not contain enough samples")
    return values


def _sample16_to_u8(value: int) -> int:
    return (value * 255 + 32767) // 65535


ADAM7_PASSES = (
    (0, 0, 8, 8),
    (4, 0, 8, 8),
    (0, 4, 4, 8),
    (2, 0, 4, 4),
    (0, 2, 2, 4),
    (1, 0, 2, 2),
    (0, 1, 1, 2),
)


def _adam7_extent(size: int, start: int, step: int) -> int:
    if size <= start:
        return 0
    return (size - start + step - 1) // step


def _decode_row_to_rgba(
    row: bytes,
    width: int,
    depth: int,
    color_type: int,
    palette: list[tuple[int, int, int]],
    transparency: bytes,
) -> bytes:
    rgba = bytearray(width * 4)
    destination = 0

    if color_type == 3:
        indexed_samples = _unpack_packed_samples(row, width, depth)
        for palette_index in indexed_samples:
            if palette_index >= len(palette):
                raise ValueError("palette index out of range")
            red, green, blue = palette[palette_index]
            alpha = transparency[palette_index] if palette_index < len(transparency) else 255
            rgba[destination : destination + 4] = bytes((red, green, blue, alpha))
            destination += 4
        return bytes(rgba)

    if color_type == 0 and depth in {1, 2, 4}:
        samples = _unpack_packed_samples(row, width, depth)
        max_sample = (1 << depth) - 1
        transparent_gray = (
            struct.unpack(">H", transparency)[0] if len(transparency) == 2 else None
        )
        for sample in samples:
            gray = (sample * 255 + max_sample // 2) // max_sample
            alpha = 0 if transparent_gray == sample else 255
            rgba[destination : destination + 4] = bytes((gray, gray, gray, alpha))
            destination += 4
        return bytes(rgba)

    if depth == 16:
        channels_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
        channels = channels_by_type[color_type]
        bpp = channels * 2
        transparent_gray = (
            struct.unpack(">H", transparency)[0]
            if color_type == 0 and len(transparency) == 2
            else None
        )
        transparent_rgb = (
            struct.unpack(">HHH", transparency)
            if color_type == 2 and len(transparency) == 6
            else None
        )
        for index in range(0, len(row), bpp):
            samples = [
                struct.unpack(">H", row[index + offset : index + offset + 2])[0]
                for offset in range(0, bpp, 2)
            ]
            if color_type == 0:
                gray16 = samples[0]
                gray = _sample16_to_u8(gray16)
                alpha = 0 if transparent_gray == gray16 else 255
                red = green = blue = gray
            elif color_type == 2:
                red16, green16, blue16 = samples
                red = _sample16_to_u8(red16)
                green = _sample16_to_u8(green16)
                blue = _sample16_to_u8(blue16)
                alpha = 0 if transparent_rgb == (red16, green16, blue16) else 255
            elif color_type == 4:
                gray16, alpha16 = samples
                gray = _sample16_to_u8(gray16)
                red = green = blue = gray
                alpha = _sample16_to_u8(alpha16)
            else:
                red16, green16, blue16, alpha16 = samples
                red = _sample16_to_u8(red16)
                green = _sample16_to_u8(green16)
                blue = _sample16_to_u8(blue16)
                alpha = _sample16_to_u8(alpha16)

            rgba[destination : destination + 4] = bytes((red, green, blue, alpha))
            destination += 4
        return bytes(rgba)

    bpp_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
    bpp = bpp_by_type[color_type]
    for index in range(0, len(row), bpp):
        if color_type == 0:
            gray = row[index]
            red = green = blue = gray
            alpha = 255
            if len(transparency) >= 2:
                transparent_gray = struct.unpack(">H", transparency[:2])[0]
                if gray == transparent_gray:
                    alpha = 0
        elif color_type == 2:
            red, green, blue = row[index : index + 3]
            alpha = 255
            if len(transparency) == 6:
                tr, tg, tb = struct.unpack(">HHH", transparency)
                if (red, green, blue) == (tr, tg, tb):
                    alpha = 0
        elif color_type == 4:
            gray, alpha = row[index : index + 2]
            red = green = blue = gray
        else:
            red, green, blue, alpha = row[index : index + 4]

        rgba[destination : destination + 4] = bytes((red, green, blue, alpha))
        destination += 4

    return bytes(rgba)


def _decode_adam7(
    raw: bytes,
    width: int,
    height: int,
    depth: int,
    color_type: int,
    palette: list[tuple[int, int, int]],
    transparency: bytes,
) -> bytes:
    rgba = bytearray(width * height * 4)
    position = 0

    for x_start, y_start, x_step, y_step in ADAM7_PASSES:
        pass_width = _adam7_extent(width, x_start, x_step)
        pass_height = _adam7_extent(height, y_start, y_step)
        if pass_width == 0 or pass_height == 0:
            continue

        stride, filter_bpp = _scanline_layout(pass_width, depth, color_type)
        pass_size = (stride + 1) * pass_height
        end = position + pass_size
        if end > len(raw):
            raise ValueError("truncated Adam7 pass data")

        rows = _unfilter_scanlines(
            raw[position:end],
            stride,
            pass_height,
            filter_bpp,
        )
        position = end

        for pass_y, row in enumerate(rows):
            row_rgba = _decode_row_to_rgba(
                row,
                pass_width,
                depth,
                color_type,
                palette,
                transparency,
            )
            target_y = y_start + pass_y * y_step
            for pass_x in range(pass_width):
                target_x = x_start + pass_x * x_step
                source_start = pass_x * 4
                target_start = (target_y * width + target_x) * 4
                rgba[target_start : target_start + 4] = row_rgba[
                    source_start : source_start + 4
                ]

    if position != len(raw):
        raise ValueError("unexpected trailing Adam7 pass data")
    return bytes(rgba)


def decode_rgba(path: Path) -> tuple[int, int, bytes]:
    chunks = _chunks(_read_png_bytes(path))
    width, height, depth, color_type, compression, filtering, interlace = _validate_ihdr(
        chunks[0][1]
    )
    if compression != 0 or filtering != 0:
        raise ValueError("unsupported PNG compression/filtering method")
    if depth not in {1, 2, 4, 8, 16}:
        raise ValueError(f"unsupported PNG bit depth {depth}")

    palette, transparency = _validate_palette_transparency(
        chunks,
        depth=depth,
        color_type=color_type,
    )
    compressed = b"".join(payload for kind, payload in chunks if kind == b"IDAT")

    if interlace == 0:
        stride, filter_bpp = _scanline_layout(width, depth, color_type)
        expected_size = (stride + 1) * height
        raw = _decompress_idat(compressed, expected_size)
        rows = _unfilter_scanlines(raw, stride, height, filter_bpp)
        rgba = bytearray(width * height * 4)
        destination = 0
        for row in rows:
            row_rgba = _decode_row_to_rgba(
                row,
                width,
                depth,
                color_type,
                palette,
                transparency,
            )
            rgba[destination : destination + len(row_rgba)] = row_rgba
            destination += len(row_rgba)
        return width, height, bytes(rgba)

    if interlace != 1:
        raise ValueError(f"unsupported PNG interlace method {interlace}")

    expected_size = 0
    for x_start, y_start, x_step, y_step in ADAM7_PASSES:
        pass_width = _adam7_extent(width, x_start, x_step)
        pass_height = _adam7_extent(height, y_start, y_step)
        if pass_width == 0 or pass_height == 0:
            continue
        stride, _ = _scanline_layout(pass_width, depth, color_type)
        expected_size += (stride + 1) * pass_height

    raw = _decompress_idat(compressed, expected_size)
    pixels = _decode_adam7(
        raw,
        width,
        height,
        depth,
        color_type,
        palette,
        transparency,
    )
    return width, height, pixels


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _filter_row(row: bytes, previous: bytes, bpp: int, filter_type: int) -> bytes:
    output = bytearray(len(row))
    for index, value in enumerate(row):
        left = row[index - bpp] if index >= bpp else 0
        above = previous[index]
        upper_left = previous[index - bpp] if index >= bpp else 0

        if filter_type == 0:
            predictor = 0
        elif filter_type == 1:
            predictor = left
        elif filter_type == 2:
            predictor = above
        elif filter_type == 3:
            predictor = (left + above) // 2
        elif filter_type == 4:
            predictor = _paeth(left, above, upper_left)
        else:
            raise ValueError(f"unsupported PNG filter {filter_type}")

        output[index] = (value - predictor) & 255
    return bytes(output)


def _filter_score(filtered: bytes) -> int:
    return sum(abs(value if value < 128 else value - 256) for value in filtered)


def _png_bytes_rgba(width: int, height: int, pixels: bytes, adaptive: bool = True) -> bytes:
    if len(pixels) != width * height * 4:
        raise ValueError("RGBA buffer size mismatch")

    rows: list[bytes] = []
    previous = bytes(width * 4)

    for y in range(height):
        start = y * width * 4
        row = pixels[start : start + width * 4]

        if adaptive:
            candidates = [
                (_filter_row(row, previous, 4, filter_type), filter_type)
                for filter_type in range(5)
            ]
            filtered, filter_type = min(candidates, key=lambda item: _filter_score(item[0]))
        else:
            filter_type = 0
            filtered = row

        rows.append(bytes([filter_type]) + filtered)
        previous = row

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + _chunk(b"IEND", b"")
    )


def encode_rgba(
    path: Path,
    width: int,
    height: int,
    pixels: bytes,
    adaptive: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_png_bytes_rgba(width, height, pixels, adaptive=adaptive))


def recompress_png(input_path: Path, output_path: Path) -> dict:
    before = input_path.stat().st_size
    width, height, pixels = decode_rgba(input_path)
    encode_rgba(output_path, width, height, pixels, adaptive=True)
    after = output_path.stat().st_size
    return {
        "input": str(input_path),
        "output": str(output_path),
        "width": width,
        "height": height,
        "beforeBytes": before,
        "afterBytes": after,
        "savedBytes": before - after,
        "savedPercent": round(((before - after) / before * 100.0), 2) if before else 0.0,
    }


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

    encode_rgba(output, atlas_width, atlas_height, bytes(canvas), adaptive=True)

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
