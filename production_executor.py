from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable

from art_quality import ArtQualityError, evaluate_raster_art
from semantic_art_review import SemanticArtReviewError, review_raster_art
from generator_backends import THREE_D_GENERATED_TYPES, VECTOR_GENERATED_TYPES, execute_generated_3d_asset, execute_generated_asset
from lod_3d import LodGenerationError, generate_lod_chain


class ProductionExecutionError(RuntimeError):
    pass


def _safe_asset_id(value) -> str:
    asset_id = str(value or "").strip()
    if (
        not asset_id
        or asset_id in {".", ".."}
        or "/" in asset_id
        or "\\" in asset_id
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in asset_id)
        or len(asset_id) > 128
    ):
        raise ProductionExecutionError("production job asset id is not a safe filename")
    return asset_id


def _trusted_generated_source(output_dir: Path, generation: dict, *, label: str = "generator") -> Path:
    raw = generation.get("sourcePath") if isinstance(generation, dict) else None
    source = Path(str(raw or ""))
    if not source.is_file():
        raise ProductionExecutionError(f"{label} result source file missing")
    try:
        resolved_out = Path(output_dir).resolve()
        resolved_source = source.resolve()
    except OSError as exc:
        raise ProductionExecutionError(f"{label} source path cannot be resolved") from exc
    if not resolved_source.is_relative_to(resolved_out):
        raise ProductionExecutionError(f"{label} source path escapes output directory")
    if source.is_symlink():
        raise ProductionExecutionError(f"{label} source file must not be a symlink")
    return source


def _provenance_from_manifest(manifest: dict) -> dict:
    source = manifest.get("source") if isinstance(manifest, dict) else None
    license_data = manifest.get("license") if isinstance(manifest, dict) else None
    source = source if isinstance(source, dict) else {}
    license_data = license_data if isinstance(license_data, dict) else {}
    return {
        "source": {
            "mode": source.get("mode"),
            "uri": source.get("uri"),
            "author": source.get("author"),
        },
        "license": {
            "id": license_data.get("id"),
            "commercialUse": license_data.get("commercialUse"),
            "derivatives": license_data.get("derivatives"),
            "attributionRequired": license_data.get("attributionRequired"),
        },
    }


def _stage_provided_source(source_path: Path, output_dir: Path, *, suffix: str) -> dict:
    source = Path(source_path)
    if not source.is_file():
        raise ProductionExecutionError("provided source file missing")
    if source.is_symlink():
        raise ProductionExecutionError("provided source file must not be a symlink")
    size = source.stat().st_size
    if size <= 0:
        raise ProductionExecutionError("provided source file is empty")
    if size > 100 * 1024 * 1024:
        raise ProductionExecutionError("provided source file exceeds 100 MiB safety limit")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    staged = out / f"provided-source{suffix}"
    if source.resolve() != staged.resolve():
        shutil.copyfile(source, staged)
    return {
        "success": True,
        "backend": "provided",
        "model": None,
        "sourcePath": str(staged),
        "sourceBytes": staged.stat().st_size,
        "metadata": None,
    }


def execute_generated_raster_job(
    job: dict,
    output_dir: Path,
    *,
    validator: Callable,
    png_optimizer: Callable,
    webp_encoder: Callable,
    generator: Callable = execute_generated_asset,
    backend: str = "auto",
    model: str | None = None,
    timeout_seconds: float = 180.0,
    source_path: Path | None = None,
    reference_paths: list[Path] | None = None,
    art_quality_reporter: Callable = evaluate_raster_art,
    semantic_reviewer: Callable = review_raster_art,
) -> dict:
    if job.get("schema") != "asset-forge/production-job/v1":
        raise ProductionExecutionError("unsupported production job schema")
    if source_path is None and job.get("requiresGenerator") is not True:
        raise ProductionExecutionError("production job requires --source or generation")

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

    asset_id = _safe_asset_id(job.get("assetId") or manifest.get("id"))

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if source_path is None:
        generation = generator(
            job,
            out,
            backend=backend,
            model=model,
            timeout_seconds=timeout_seconds,
            reference_paths=reference_paths,
        )
        source = _trusted_generated_source(out, generation)
    else:
        if target_format == "png" and Path(source_path).suffix.lower() != ".png":
            raise ProductionExecutionError("provided PNG target requires a PNG source")
        generation = _stage_provided_source(
            source_path,
            out,
            suffix=Path(source_path).suffix.lower(),
        )
        source = _trusted_generated_source(out, generation, label="provided source")

    final = out / f"{asset_id}.{target_format}"
    if target_format == "png":
        processing = png_optimizer(source, final)
    else:
        processing = webp_encoder(source, final, lossless=True)

    try:
        info, errors = validator(final, manifest)
    except (OSError, ValueError) as exc:
        raise ProductionExecutionError(f"generated asset validation failed: {exc}") from exc

    technical_quality = None
    technical_errors = []
    technical_warnings = []
    try:
        technical_quality = art_quality_reporter(final, manifest)
        if isinstance(technical_quality, dict):
            technical_errors = list(technical_quality.get("errors") or [])
            technical_warnings = list(technical_quality.get("warnings") or [])
    except (ArtQualityError, OSError, ValueError) as exc:
        constraints = manifest.get("constraints")
        strict = (
            isinstance(constraints, dict)
            and constraints.get("technicalQualityMin") is not None
        )
        if strict:
            technical_errors.append(f"technical art quality check failed: {exc}")
        else:
            technical_warnings.append(f"technical art quality unavailable: {type(exc).__name__}")

    semantic_quality = None
    semantic_errors = []
    semantic_warnings = []
    constraints = manifest.get("constraints")
    semantic_enabled = (
        isinstance(constraints, dict)
        and (
            constraints.get("semanticArtReview") is True
            or constraints.get("semanticArtReviewRequired") is True
        )
    )
    if semantic_enabled and source_path is None:
        try:
            semantic_quality = semantic_reviewer(final, manifest)
            if isinstance(semantic_quality, dict):
                if semantic_quality.get("passed") is False:
                    semantic_errors.append(
                        "semantic art quality score is below required threshold"
                    )
                elif semantic_quality.get("available") is False:
                    semantic_warnings.append(
                        "semantic art quality review unavailable: "
                        + str(semantic_quality.get("reason") or "unknown")
                    )
        except (SemanticArtReviewError, OSError, ValueError) as exc:
            required = (
                isinstance(constraints, dict)
                and constraints.get("semanticArtReviewRequired") is True
            )
            if required:
                semantic_errors.append(f"semantic art quality check failed: {exc}")
            else:
                semantic_warnings.append(
                    f"semantic art quality unavailable: {type(exc).__name__}"
                )

    combined_errors = list(errors) + technical_errors + semantic_errors

    report = {
        "schema": "asset-forge/production-report/v1",
        "requestId": job.get("requestId"),
        "assetId": asset_id,
        "assetType": job.get("assetType"),
        "provenance": _provenance_from_manifest(manifest),
        "success": not combined_errors,
        "generation": generation,
        "processing": processing,
        "validation": {
            "file": str(final),
            "info": info,
            "errors": combined_errors,
            "warnings": technical_warnings + semantic_warnings,
            "technicalArt": technical_quality,
            "semanticArt": semantic_quality,
        },
        "artifact": str(final) if not combined_errors else None,
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
    backend: str = "auto",
    model: str | None = None,
    timeout_seconds: float = 180.0,
    source_path: Path | None = None,
) -> dict:
    if job.get("schema") != "asset-forge/production-job/v1":
        raise ProductionExecutionError("unsupported production job schema")
    if source_path is None and job.get("requiresGenerator") is not True:
        raise ProductionExecutionError("production job requires --source or generation")

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

    asset_id = _safe_asset_id(job.get("assetId") or manifest.get("id"))

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if source_path is None:
        generation = generator(
            job,
            out,
            backend=backend,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        source = _trusted_generated_source(out, generation)
    else:
        if Path(source_path).suffix.lower() != ".svg":
            raise ProductionExecutionError("provided vector source must be SVG")
        generation = _stage_provided_source(source_path, out, suffix=".svg")
        source = _trusted_generated_source(out, generation, label="provided source")

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
        "provenance": _provenance_from_manifest(manifest),
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


def execute_generated_3d_job(
    job: dict,
    output_dir: Path,
    *,
    structural_validator: Callable,
    profile_validator: Callable,
    quality_reporter: Callable,
    godot_delivery_reporter: Callable,
    lod_reporter: Callable = generate_lod_chain,
    generator: Callable = execute_generated_3d_asset,
    model: str = "microsoft/trellis-2",
    resolution: str = "low",
    timeout_seconds: float = 600.0,
    source_path: Path | None = None,
) -> dict:
    if job.get("schema") != "asset-forge/production-job/v1":
        raise ProductionExecutionError("unsupported production job schema")
    if source_path is None and job.get("requiresGenerator") is not True:
        raise ProductionExecutionError("production job requires --source or generation")

    manifest = job.get("manifest")
    if not isinstance(manifest, dict):
        raise ProductionExecutionError("production job manifest missing")
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise ProductionExecutionError("production job target missing")
    target_format = str(target.get("format") or "").lower()
    if target_format not in {"glb", "gltf"}:
        raise ProductionExecutionError(
            f"generated 3D production requires target format glb/gltf, got: {target_format or '<missing>'}"
        )

    asset_type = str(job.get("assetType") or "")
    if asset_type not in THREE_D_GENERATED_TYPES:
        raise ProductionExecutionError(
            f"generated 3D production does not support asset type: {asset_type or '<missing>'}"
        )
    if target_format != "glb":
        raise ProductionExecutionError(
            "generated 3D production currently emits self-contained GLB only"
        )

    asset_id = _safe_asset_id(job.get("assetId") or manifest.get("id"))

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if source_path is None:
        generation = generator(
            job,
            out,
            model=model,
            resolution=resolution,
            timeout_seconds=timeout_seconds,
        )
        source = _trusted_generated_source(out, generation, label="3D generator")
    else:
        if Path(source_path).suffix.lower() != ".glb":
            raise ProductionExecutionError("provided 3D source must be a GLB")
        generation = _stage_provided_source(source_path, out, suffix=".glb")
        source = _trusted_generated_source(out, generation, label="provided source")

    final = out / f"{asset_id}.glb"
    if source.resolve() != final.resolve():
        shutil.copyfile(source, final)

    profile = {
        "prop": "prop",
        "environment": "environment",
        "character-3d": "character",
    }.get(asset_type)

    try:
        if profile is None:
            info, errors, warnings = structural_validator(final)
        else:
            info, errors, warnings = profile_validator(final, profile)
        quality = quality_reporter(final, profile)
    except (OSError, ValueError) as exc:
        raise ProductionExecutionError(f"generated 3D validation failed: {exc}") from exc

    evaluation = quality.get("evaluation") if isinstance(quality, dict) else None
    quality_errors = []
    quality_warnings = []
    if isinstance(evaluation, dict):
        quality_errors = list(evaluation.get("errors") or [])
        quality_warnings = list(evaluation.get("warnings") or [])

    constraints = manifest.get("constraints")
    constraints = constraints if isinstance(constraints, dict) else {}
    generate_lods = constraints.get("generateLods") is True
    require_lods = constraints.get("requireLods") is True
    lods = None
    lod_errors = []
    lod_warnings = []
    if generate_lods and profile is not None:
        try:
            lods = lod_reporter(
                final,
                out / "lods",
                profile=profile,
            )
        except (LodGenerationError, OSError, ValueError) as exc:
            if require_lods:
                lod_errors.append(f"LOD generation failed: {exc}")
            else:
                lod_warnings.append(f"LOD generation unavailable: {exc}")
        if isinstance(lods, dict):
            lod_warnings.extend(list(lods.get("warnings") or []))
            lod_errors.extend(list(lods.get("errors") or []))
            if require_lods and lods.get("required") is True and lods.get("available") is not True:
                lod_errors.append("required LOD generation toolchain is unavailable")

    engine = str(target.get("engine") or "").lower()
    godot_delivery = None
    if engine in {"godot", "godot4", "godot-4"}:
        try:
            godot_delivery = godot_delivery_reporter(
                final,
                profile or "prop",
            )
        except (OSError, ValueError) as exc:
            raise ProductionExecutionError(
                f"generated 3D Godot delivery validation failed: {exc}"
            ) from exc

    combined_errors = list(errors) + quality_errors + lod_errors
    combined_warnings = list(warnings) + quality_warnings + lod_warnings
    if isinstance(godot_delivery, dict):
        combined_errors.extend(list(godot_delivery.get("errors") or []))
        combined_warnings.extend(list(godot_delivery.get("warnings") or []))
        scene = godot_delivery.get("scene") if isinstance(godot_delivery.get("scene"), dict) else {}
        if constraints.get("requireCollision") is True and int(scene.get("collisionNodes") or 0) <= 0:
            combined_errors.append("required runtime collision is missing")
        if godot_delivery.get("ready") is not True and not godot_delivery.get("errors"):
            combined_errors.append("Godot delivery report is not ready")

    runtime_sidecar = None
    runtime_plan = (
        godot_delivery.get("runtimePlan")
        if isinstance(godot_delivery, dict)
        and isinstance(godot_delivery.get("runtimePlan"), dict)
        else None
    )
    if runtime_plan is not None:
        runtime_sidecar = out / f"{asset_id}.runtime-3d.json"
        runtime_sidecar.write_text(
            json.dumps(runtime_plan, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    report = {
        "schema": "asset-forge/production-report/v1",
        "requestId": job.get("requestId"),
        "assetId": asset_id,
        "assetType": asset_type,
        "provenance": _provenance_from_manifest(manifest),
        "success": not combined_errors,
        "generation": generation,
        "validation": {
            "file": str(final),
            "profile": profile,
            "info": info,
            "errors": combined_errors,
            "warnings": combined_warnings,
            "quality": quality,
            "godot": godot_delivery,
            "lods": lods,
        },
        "additionalArtifacts": (
            (
                [str(item["path"]) for item in lods.get("outputs", [])]
                if isinstance(lods, dict)
                else []
            )
            + ([str(runtime_sidecar)] if runtime_sidecar is not None else [])
        ),
        "artifact": str(final) if not combined_errors else None,
    }
    report_path = out / "production-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["reportPath"] = str(report_path)
    return report
