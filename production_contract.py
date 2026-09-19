from __future__ import annotations

from pathlib import Path
from typing import Callable


REQUEST_SCHEMA = "asset-forge/production-request/v1"
JOB_SCHEMA = "asset-forge/production-job/v1"


def validate_production_request(request: dict, validate_manifest: Callable[[dict], list[str]]) -> list[str]:
    errors: list[str] = []
    if request.get("schema") != REQUEST_SCHEMA:
        errors.append(f"schema: must be {REQUEST_SCHEMA}")

    request_id = request.get("requestId")
    if not isinstance(request_id, str) or not request_id.strip():
        errors.append("requestId: non-empty string required")

    instruction = request.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip():
        errors.append("instruction: non-empty string required")

    manifest = request.get("manifest")
    if not isinstance(manifest, dict):
        errors.append("manifest: object required")
    else:
        errors.extend(f"manifest.{error}" for error in validate_manifest(manifest))

    delivery = request.get("delivery", {})
    if delivery is not None and not isinstance(delivery, dict):
        errors.append("delivery: object required when present")
    elif isinstance(delivery, dict):
        output_dir = delivery.get("outputDir")
        if output_dir is not None and (not isinstance(output_dir, str) or not output_dir.strip()):
            errors.append("delivery.outputDir: non-empty string or null required")
        engine = delivery.get("engine")
        if engine is not None and (not isinstance(engine, str) or not engine.strip()):
            errors.append("delivery.engine: non-empty string or null required")

    return errors


def build_production_job(
    request: dict,
    plan: dict,
    *,
    default_output_dir: str = "build/asset-forge",
) -> dict:
    manifest = request["manifest"]
    source_mode = manifest["source"]["mode"]
    delivery = request.get("delivery") or {}
    output_dir = delivery.get("outputDir") or str(Path(default_output_dir) / request["requestId"])

    requires_generator = source_mode == "generated"
    return {
        "schema": JOB_SCHEMA,
        "requestId": request["requestId"],
        "project": manifest["project"],
        "assetId": manifest["id"],
        "assetType": manifest["type"],
        "instruction": request["instruction"],
        "status": "ready",
        "sourceMode": source_mode,
        "requiresGenerator": requires_generator,
        "execution": {
            "strategy": "generate-then-process" if requires_generator else "source-then-process",
            "pipeline": plan.get("pipeline"),
            "stages": plan.get("stages", []),
            "candidateTools": plan.get("candidateTools", []),
        },
        "delivery": {
            "engine": delivery.get("engine") or manifest.get("target", {}).get("engine"),
            "format": manifest.get("target", {}).get("format"),
            "outputDir": output_dir,
            "manifestPath": str(Path(output_dir) / "asset-manifest.json"),
            "planPath": str(Path(output_dir) / "production-plan.json"),
            "reportPath": str(Path(output_dir) / "production-report.json"),
        },
        "manifest": manifest,
        "plan": plan,
    }
