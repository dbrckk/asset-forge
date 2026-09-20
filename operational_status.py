from __future__ import annotations

import shutil

from generator_backends import generator_backend_status
from raster_pack import raster_backend_status
from toolchain_3d import detect_3d_tools


def build_operational_status(*, environ=None, home=None, which=shutil.which) -> dict:
    generation = generator_backend_status(environ=environ, home=home)
    raster = raster_backend_status()
    tools_3d = detect_3d_tools()

    pollinations = generation["pollinations"]
    imagen_codex = generation.get("imagenCodex", {})
    imagen_installed = bool(imagen_codex.get("installed"))
    imagen_authenticated = bool(imagen_codex.get("authenticated"))
    webp_encode = bool(
        raster.get("webp", {}).get("encode", {}).get("available", False)
    )
    godot_executable = which("godot4") or which("godot")

    capabilities = {
        "rasterPng": bool(
            pollinations.get("rasterVectorReady")
            or imagen_codex.get("rasterReady")
        ),
        "rasterWebp": bool(
            pollinations.get("rasterVectorReady")
            or imagen_codex.get("rasterReady")
        ) and webp_encode,
        "vectorSvg": bool(pollinations.get("rasterVectorReady")),
        "threeDGlb": bool(pollinations.get("threeDReady")),
        "godotImport": godot_executable is not None,
        "imagenCodexRaster": bool(imagen_codex.get("rasterReady")),
    }

    blockers = []
    if not pollinations.get("installed") and not imagen_installed:
        blockers.append("no image generation CLI is installed (polli or imagen)")
    if (
        not pollinations.get("authenticated")
        and not imagen_authenticated
    ):
        blockers.append("no image generation backend is authenticated")
    if imagen_installed and not imagen_authenticated:
        blockers.append(
            "imagen-codex requires CODEX_ACCESS_TOKEN or CHATGPT_ACCESS_TOKEN; IMAGEN_API_KEY is not used"
        )
    if not webp_encode:
        blockers.append("Pillow/libwebp is unavailable for WebP output")
    if not pollinations.get("threeDReady"):
        blockers.append("POLLINATIONS_API_KEY is required for server-side 3D generation")
    if godot_executable is None:
        blockers.append("Godot executable is unavailable for real import validation")

    return {
        "schema": "asset-forge/operational-status/v1",
        "ready": {
            "anyGeneratedAsset": any(
                capabilities[name]
                for name in ("rasterPng", "rasterWebp", "vectorSvg", "threeDGlb")
            ),
            "rasterVector": capabilities["rasterPng"] and capabilities["vectorSvg"],
            "threeD": capabilities["threeDGlb"],
            "full": (
                capabilities["rasterPng"]
                and capabilities["rasterWebp"]
                and capabilities["vectorSvg"]
                and capabilities["threeDGlb"]
                and capabilities["godotImport"]
            ),
        },
        "capabilities": capabilities,
        "generation": generation,
        "raster": raster,
        "tools3d": tools_3d,
        "godot": {
            "installed": godot_executable is not None,
            "executable": godot_executable,
        },
        "blockers": blockers,
    }
