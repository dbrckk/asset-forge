from __future__ import annotations

import importlib
import importlib.util
from importlib import metadata
from pathlib import Path


SUPPORTED_INPUT_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


class VectorizationError(RuntimeError):
    pass


def status() -> dict:
    installed = importlib.util.find_spec("vtracer") is not None
    package_version = None
    if installed:
        try:
            package_version = metadata.version("vtracer")
        except metadata.PackageNotFoundError:
            package_version = None
    return {
        "installed": installed,
        "vectorizeReady": installed,
        "version": package_version,
        "engine": "visioncortex/vtracer",
        "license": "MIT",
        "mode": "local-raster-to-svg",
    }


def _validate_input(path: Path) -> Path:
    source = Path(path)
    if source.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        raise VectorizationError(
            "vtracer input must be PNG, JPEG, WebP, BMP, or GIF"
        )
    if not source.is_file():
        raise VectorizationError("vtracer input file is missing")
    if source.is_symlink():
        raise VectorizationError("vtracer input must not be a symlink")
    size = source.stat().st_size
    if size <= 0:
        raise VectorizationError("vtracer input file is empty")
    if size > 64 * 1024 * 1024:
        raise VectorizationError("vtracer input exceeds 64 MiB safety limit")
    return source


def _validate_output(path: Path) -> dict:
    output = Path(path)
    if not output.is_file() or output.stat().st_size <= 0:
        raise VectorizationError("vtracer did not produce an SVG output")
    try:
        head = output.read_text(encoding="utf-8")[:4096].lower()
    except UnicodeDecodeError as exc:
        raise VectorizationError("vtracer output is not UTF-8 SVG") from exc
    if "<svg" not in head:
        raise VectorizationError("vtracer output does not contain an SVG root")
    return {
        "output": str(output),
        "bytes": output.stat().st_size,
    }


def vectorize_raster(
    input_path: Path,
    output_path: Path,
    *,
    preset: str = "poster",
) -> dict:
    source = _validate_input(Path(input_path))
    output = Path(output_path)
    if output.suffix.lower() != ".svg":
        raise VectorizationError("vtracer output path must use .svg")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        vtracer = importlib.import_module("vtracer")
    except ImportError as exc:
        raise VectorizationError(
            "vtracer Python package is unavailable; install asset-forge[generation]"
        ) from exc

    engine = None
    try:
        config_type = getattr(vtracer, "Config", None)
        if config_type is not None:
            factory = getattr(config_type, preset, None)
            if callable(factory):
                config = factory()
            else:
                config = config_type(mode="polygon", hierarchical="cutout")
            result = config.convert_file(str(source), str(output))
            if isinstance(result, str) and not output.is_file():
                output.write_text(result, encoding="utf-8")
            engine = "config-api"
        else:
            legacy = getattr(vtracer, "convert_image_to_svg_py", None)
            if not callable(legacy):
                raise VectorizationError(
                    "installed vtracer package exposes no supported Python API"
                )
            legacy(
                str(source),
                str(output),
                colormode="color",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=4,
                color_precision=6,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=8,
            )
            engine = "legacy-api"
    except VectorizationError:
        raise
    except Exception as exc:
        raise VectorizationError(
            f"vtracer vectorization failed: {type(exc).__name__}: {exc}"
        ) from exc

    result = _validate_output(output)
    result.update({
        "backend": "vtracer",
        "engine": engine,
        "preset": preset,
        "input": str(source),
    })
    return result
