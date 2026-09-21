from __future__ import annotations

import shutil

from generator_backends import generator_backend_status
from raster_pack import raster_backend_status
from toolchain_3d import detect_3d_tools


def _first_ready_backend(*candidates: tuple[str, dict]) -> str | None:
    for name, status in candidates:
        if isinstance(status, dict) and status.get("rasterReady") is True:
            return name
    return None


def build_operational_status(*, environ=None, home=None, which=shutil.which) -> dict:
    generation = generator_backend_status(environ=environ, home=home)
    raster = raster_backend_status()
    tools_3d = detect_3d_tools()

    cloudflare = generation.get("cloudflare", {})
    kaggle_qwen = generation.get("kaggleQwen", {})
    pollinations = generation.get("pollinations", {})
    imagen_codex = generation.get("imagenCodex", {})
    qwen_colab = generation.get("qwenColab", {})
    vtracer = generation.get("vtracer", {})

    cloudflare_raster = bool(cloudflare.get("rasterReady"))
    kaggle_raster = bool(kaggle_qwen.get("rasterReady"))
    pollinations_raster = bool(pollinations.get("rasterVectorReady"))
    pollinations_vector = bool(pollinations.get("rasterVectorReady"))
    vtracer_vector = bool(vtracer.get("vectorSvgReady"))
    imagen_raster = bool(imagen_codex.get("rasterReady"))
    queued_qwen = bool(qwen_colab.get("queueReady"))

    direct_raster_ready = any(
        (
            cloudflare_raster,
            kaggle_raster,
            pollinations_raster,
            imagen_raster,
        )
    )
    free_raster_ready = cloudflare_raster or kaggle_raster

    webp_encode = bool(
        raster.get("webp", {}).get("encode", {}).get("available", False)
    )
    godot_executable = which("godot4") or which("godot")

    capabilities = {
        "rasterPng": direct_raster_ready,
        "rasterWebp": direct_raster_ready and webp_encode,
        "vectorSvg": vtracer_vector or pollinations_vector,
        "freeVectorSvg": vtracer_vector,
        "vtracerVector": vtracer_vector,
        "pollinationsVector": pollinations_vector,
        "threeDGlb": bool(pollinations.get("threeDReady")),
        "godotImport": godot_executable is not None,
        "cloudflareRaster": cloudflare_raster,
        "kaggleQwenRaster": kaggle_raster,
        "freeRaster": free_raster_ready,
        "autoRaster": free_raster_ready,
        "qwenColabQueue": queued_qwen,
        "pollinationsRaster": pollinations_raster,
        "imagenCodexRaster": imagen_raster,
    }

    # Keep this aligned with select_generation_backend(..., "auto"):
    # automatic raster production is intentionally free-first and only uses
    # Cloudflare Workers AI, then Kaggle Qwen.
    preferred_raster_backend = _first_ready_backend(
        ("cloudflare", cloudflare),
        ("kaggle-qwen", kaggle_qwen),
    )
    preferred_vector_backend = (
        "vtracer"
        if vtracer_vector
        else "pollinations"
        if pollinations_vector
        else None
    )

    blockers = []
    if not capabilities["rasterPng"]:
        if queued_qwen:
            blockers.append(
                "no direct raster backend is ready; Qwen Colab batch queue is available"
            )
        else:
            blockers.append(
                "no authenticated raster generation backend is ready "
                "(Cloudflare, Kaggle Qwen, Pollinations, or imagen-codex)"
            )
    if capabilities["rasterPng"] and not capabilities["autoRaster"]:
        blockers.append(
            "automatic free raster routing is unavailable; "
            "configure Cloudflare or Kaggle Qwen, or select another backend explicitly"
        )
    if capabilities["rasterPng"] and not webp_encode:
        blockers.append("Pillow/libwebp is unavailable for WebP output")
    if not capabilities["vectorSvg"]:
        blockers.append(
            "no SVG generation backend is ready; install VTracer with a free raster "
            "backend or configure Pollinations"
        )
    if not capabilities["threeDGlb"]:
        blockers.append(
            "no authenticated 3D generation backend is ready"
        )
    if godot_executable is None:
        blockers.append("Godot executable is unavailable for real import validation")

    imagen_installed = bool(imagen_codex.get("installed"))
    imagen_authenticated = bool(imagen_codex.get("authenticated"))
    if (
        imagen_installed
        and not imagen_authenticated
        and not direct_raster_ready
        and not queued_qwen
    ):
        blockers.append(
            "imagen-codex requires CODEX_ACCESS_TOKEN or CHATGPT_ACCESS_TOKEN; "
            "IMAGEN_API_KEY is not used"
        )

    return {
        "schema": "asset-forge/operational-status/v1",
        "ready": {
            "anyGeneratedAsset": direct_raster_ready
            or capabilities["vectorSvg"]
            or capabilities["threeDGlb"]
            or queued_qwen,
            "raster": direct_raster_ready,
            "autoRaster": free_raster_ready,
            "queuedRaster": queued_qwen,
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
        "routing": {
            "preferredRasterBackend": preferred_raster_backend,
            "queuedRasterBackend": "qwen-colab" if queued_qwen else None,
            "preferredVectorBackend": preferred_vector_backend,
            "freeRasterReady": free_raster_ready,
            "autoRasterReady": free_raster_ready,
            "freeVectorReady": vtracer_vector,
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
