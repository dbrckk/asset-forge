from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from gltf_quality import quality_report
from runtime_3d_plan import build_runtime_3d_plan


class LodGenerationError(RuntimeError):
    pass


def _ratios_for_profile(profile: str) -> list[float]:
    if profile == "character":
        return [0.60, 0.30, 0.12]
    if profile == "environment":
        return [0.50, 0.20, 0.08]
    return [0.50, 0.20]


def generate_lod_chain(
    source: Path,
    output_dir: Path,
    *,
    profile: str = "prop",
    executable: str | None = None,
    error: float = 0.01,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict:
    source = Path(source)
    if not source.is_file():
        raise LodGenerationError(f"source GLB does not exist: {source}")
    if source.suffix.lower() != ".glb":
        raise LodGenerationError("LOD generation requires a GLB source")
    if profile not in {"prop", "character", "environment"}:
        raise LodGenerationError("unsupported LOD profile")
    try:
        error = float(error)
    except (TypeError, ValueError) as exc:
        raise LodGenerationError("LOD error must be numeric") from exc
    if not 0.0 < error <= 1.0:
        raise LodGenerationError("LOD error must be in (0, 1]")

    source_quality = quality_report(source, profile)
    plan = build_runtime_3d_plan(source_quality, profile)
    if not plan["lod"]["required"]:
        return {
            "schema": "asset-forge/lod-generation/v1",
            "required": False,
            "available": True,
            "source": str(source),
            "sourceTriangles": int(source_quality["geometry"]["triangles"]),
            "outputs": [],
            "errors": [],
            "warnings": [],
        }

    executable = executable or shutil.which("gltf-transform")
    if not executable:
        return {
            "schema": "asset-forge/lod-generation/v1",
            "required": True,
            "available": False,
            "source": str(source),
            "sourceTriangles": int(source_quality["geometry"]["triangles"]),
            "outputs": [],
            "errors": [],
            "warnings": ["gltf-transform unavailable; LOD generation deferred"],
        }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    warnings = []
    source_triangles = int(source_quality["geometry"]["triangles"])

    for level, ratio in enumerate(_ratios_for_profile(profile), start=1):
        output = output_dir / f"{source.stem}.lod{level}.glb"
        command = [
            executable,
            "simplify",
            str(source),
            str(output),
            "--ratio",
            str(ratio),
            "--error",
            str(error),
        ]
        if profile == "environment":
            command.append("--lock-border")
        completed = runner(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise LodGenerationError(
                f"LOD {level} generation failed"
                + (f": {detail[:1200]}" if detail else "")
            )
        if not output.is_file() or output.stat().st_size <= 0:
            raise LodGenerationError(f"LOD {level} output missing")

        quality = quality_report(output, profile)
        triangles = int(quality["geometry"]["triangles"])
        target = int(round(source_triangles * ratio))
        if source_triangles and triangles >= source_triangles:
            raise LodGenerationError(
                f"LOD {level} did not reduce triangle count"
            )
        if target and triangles > int(target * 1.35):
            warnings.append(
                f"LOD {level} simplifier stopped above target: "
                f"{triangles} triangles vs target {target}"
            )
        outputs.append({
            "level": level,
            "ratio": ratio,
            "targetTriangles": target,
            "triangles": triangles,
            "path": str(output),
            "bytes": output.stat().st_size,
            "quality": quality,
        })

    report = {
        "schema": "asset-forge/lod-generation/v1",
        "required": True,
        "available": True,
        "source": str(source),
        "sourceTriangles": source_triangles,
        "outputs": outputs,
        "errors": [],
        "warnings": warnings,
    }
    (output_dir / "lod-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
