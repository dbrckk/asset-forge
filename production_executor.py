from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from generator_backends import execute_generated_asset


class ProductionExecutionError(RuntimeError):
    pass


def execute_generated_raster_job(
    job: dict,
    output_dir: Path,
    *,
    validator: Callable,
    png_optimizer: Callable,
    webp_encoder: Callable,
    generator: Callable = execute_generated_asset,
    backend: str = "pollinations",
    model: str | None = None,
    timeout_seconds: float = 180.0,
) -> dict:
    if job.get("schema") != "asset-forge/production-job/v1":
        raise ProductionExecutionError("unsupported production job schema")
    if job.get("requiresGenerator") is not True:
        raise ProductionExecutionError("production job does not require generation")

    manifest = job.get("manifest")
    if not isinstance(manifest, dict):
        raise ProductionExecutionError("production job manifest missing")
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise ProductionExecutionError("production job target missing")
    target_format = str(target.get("format") or "").lower()
    if target_format not in {"png", "webp"}:
        raise ProductionExecutionError(
            f"generated raster production does not support target format: {target_format or '<missing>'}"
        )

    asset_id = str(job.get("assetId") or manifest.get("id") or "").strip()
    if not asset_id:
        raise ProductionExecutionError("production job asset id missing")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    generation = generator(
        job,
        out,
        backend=backend,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    source = Path(str(generation.get("sourcePath") or ""))
    if not source.is_file():
        raise ProductionExecutionError("generator result source file missing")

    final = out / f"{asset_id}.{target_format}"
    if target_format == "png":
        processing = png_optimizer(source, final)
    else:
        processing = webp_encoder(source, final, lossless=True)

    try:
        info, errors = validator(final, manifest)
    except (OSError, ValueError) as exc:
        raise ProductionExecutionError(f"generated asset validation failed: {exc}") from exc

    report = {
        "schema": "asset-forge/production-report/v1",
        "requestId": job.get("requestId"),
        "assetId": asset_id,
        "assetType": job.get("assetType"),
        "success": not errors,
        "generation": generation,
        "processing": processing,
        "validation": {
            "file": str(final),
            "info": info,
            "errors": errors,
        },
        "artifact": str(final) if not errors else None,
    }
    report_path = out / "production-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["reportPath"] = str(report_path)
    return report
