from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from generator_backends import VECTOR_GENERATED_TYPES, execute_generated_asset


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


def execute_generated_vector_job(
    job: dict,
    output_dir: Path,
    *,
    sanitizer: Callable,
    normalizer: Callable,
    profile_validator: Callable,
    generic_validator: Callable,
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
    if target_format != "svg":
        raise ProductionExecutionError(
            f"generated vector production requires target format svg, got: {target_format or '<missing>'}"
        )

    asset_type = str(job.get("assetType") or "")
    if asset_type not in VECTOR_GENERATED_TYPES:
        raise ProductionExecutionError(
            f"generated vector production does not support asset type: {asset_type or '<missing>'}"
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

    sanitized = out / "generated-sanitized.svg"
    final = out / f"{asset_id}.svg"
    sanitize_result = sanitizer(source, sanitized)
    normalize_result = normalizer(sanitized, final)

    profile = {
        "icon": "icon",
        "logo": "logo",
        "ui-vector": "ui",
    }.get(asset_type)
    try:
        if profile is None:
            info, errors, warnings = generic_validator(final)
        else:
            info, errors, warnings = profile_validator(final, profile)
    except (OSError, ValueError) as exc:
        raise ProductionExecutionError(f"generated vector validation failed: {exc}") from exc

    report = {
        "schema": "asset-forge/production-report/v1",
        "requestId": job.get("requestId"),
        "assetId": asset_id,
        "assetType": asset_type,
        "success": not errors,
        "generation": generation,
        "processing": {
            "sanitize": sanitize_result,
            "normalize": normalize_result,
        },
        "validation": {
            "file": str(final),
            "profile": profile,
            "info": info,
            "errors": errors,
            "warnings": warnings,
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
