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
    webp_encode = bool(
        raster.get("webp", {}).get("encode", {}).get("available", False)
    )
    godot_executable = which("godot4") or which("godot")

    capabilities = {
        "rasterPng": bool(pollinations.get("rasterVectorReady")),
        "rasterWebp": bool(pollinations.get("rasterVectorReady")) and webp_encode,
        "vectorSvg": bool(pollinations.get("rasterVectorReady")),
        "threeDGlb": bool(pollinations.get("threeDReady")),
        "godotImport": godot_executable is not None,
    }

    blockers = []
    if not pollinations.get("installed"):
        blockers.append("polli CLI is not installed")
    elif not pollinations.get("authenticated"):
        blockers.append("Pollinations is not authenticated")
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
