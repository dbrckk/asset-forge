from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from pathlib import Path

from blender_adapter import (
    build_blender_export_job,
    render_blender_command,
    write_blender_export_script,
)


def detect_3d_tools() -> dict:
    candidates = {
        "blender": ["blender"],
        "gltf-validator": ["gltf_validator", "gltf-validator"],
        "gltf-transform": ["gltf-transform"],
        "gltfpack": ["gltfpack"],
    }
    result = {}
    for tool_id, names in candidates.items():
        found = None
        for name in names:
            path = shutil.which(name)
            if path:
                found = path
                break
        result[tool_id] = {
            "available": found is not None,
            "path": found,
        }
    return result


def _quote(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def validator_command(executable: str, input_path: Path) -> str:
    return _quote([executable, "--stdout", str(input_path)])


def gltf_transform_command(
    executable: str,
    input_path: Path,
    output_path: Path,
    *,
    texture_compress: str | None = None,
) -> str:
    parts = [executable, "optimize", str(input_path), str(output_path)]
    if texture_compress:
        parts.extend(["--texture-compress", texture_compress])
    return _quote(parts)


def gltfpack_command(
    executable: str,
    input_path: Path,
    output_path: Path,
    *,
    compression: bool = False,
    keep_names: bool = True,
    keep_materials: bool = True,
) -> str:
    parts = [executable, "-i", str(input_path), "-o", str(output_path)]
    if compression:
        parts.append("-cc")
    if keep_names:
        parts.append("-kn")
    if keep_materials:
        parts.append("-km")
    return _quote(parts)


def build_3d_pipeline(
    source_blend: Path,
    workdir: Path,
    *,
    profile: str = "prop",
    optimizer: str = "gltf-transform",
    texture_compress: str | None = None,
    mesh_compression: bool = False,
    animations: bool = True,
    target_engine: str = "generic",
) -> dict:
    if profile not in {"prop", "environment", "character"}:
        raise ValueError("profile must be prop, environment, or character")
    if optimizer not in {"none", "gltf-transform", "gltfpack"}:
        raise ValueError("optimizer must be none, gltf-transform, or gltfpack")
    if target_engine not in {"generic", "godot4"}:
        raise ValueError("target_engine must be generic or godot4")

    workdir = Path(workdir)
    raw_glb = workdir / "raw.glb"
    optimized_glb = workdir / "optimized.glb"
    blender_script = workdir / "export_blender.py"

    blender_job = build_blender_export_job(
        source_blend,
        raw_glb,
        animations=animations,
    )

    tools = detect_3d_tools()
    commands = []
    commands.append(
        {
            "id": "blender-export",
            "required": True,
            "tool": "blender",
            "available": tools["blender"]["available"],
            "command": render_blender_command(
                tools["blender"]["path"] or "blender",
                blender_script,
            ),
            "output": str(raw_glb),
        }
    )

    commands.append(
        {
            "id": "structural-validation",
            "required": True,
            "tool": "asset-forge",
            "available": True,
            "command": _quote(
                [
                    "python",
                    "asset_forge.py",
                    "validate-gltf",
                    str(raw_glb),
                    "--profile",
                    profile,
                ]
            ),
            "output": None,
        }
    )

    commands.append(
        {
            "id": "quality-report",
            "required": True,
            "tool": "asset-forge",
            "available": True,
            "command": _quote(
                [
                    "python",
                    "asset_forge.py",
                    "quality-gltf",
                    str(raw_glb),
                    "--profile",
                    profile,
                    "--output",
                    str(workdir / "quality-raw.json"),
                ]
            ),
            "output": str(workdir / "quality-raw.json"),
        }
    )

    validator = tools["gltf-validator"]
    commands.append(
        {
            "id": "khronos-validation",
            "required": False,
            "tool": "gltf-validator",
            "available": validator["available"],
            "command": validator_command(
                validator["path"] or "gltf_validator",
                raw_glb,
            ),
            "output": str(workdir / "validator-report.json"),
        }
    )

    final_glb = raw_glb
    optimizer_available = False
    if optimizer == "gltf-transform":
        tool = tools["gltf-transform"]
        optimizer_available = bool(tool["available"])
        commands.append(
            {
                "id": "optimize",
                "required": False,
                "tool": "gltf-transform",
                "available": tool["available"],
                "command": gltf_transform_command(
                    tool["path"] or "gltf-transform",
                    raw_glb,
                    optimized_glb,
                    texture_compress=texture_compress,
                ),
                "output": str(optimized_glb),
            }
        )
        if optimizer_available:
            final_glb = optimized_glb
    elif optimizer == "gltfpack":
        tool = tools["gltfpack"]
        optimizer_available = bool(tool["available"])
        commands.append(
            {
                "id": "optimize",
                "required": False,
                "tool": "gltfpack",
                "available": tool["available"],
                "command": gltfpack_command(
                    tool["path"] or "gltfpack",
                    raw_glb,
                    optimized_glb,
                    compression=mesh_compression,
                ),
                "output": str(optimized_glb),
            }
        )
        if optimizer_available:
            final_glb = optimized_glb

    if optimizer != "none":
        commands.append(
            {
                "id": "post-optimization-validation",
                "required": True,
                "tool": "asset-forge",
                "available": True,
                "command": _quote(
                    [
                        "python",
                        "asset_forge.py",
                        "validate-gltf",
                        str(final_glb),
                        "--profile",
                        profile,
                    ]
                ),
                "output": None,
            }
        )
        commands.append(
            {
                "id": "post-optimization-quality",
                "required": True,
                "tool": "asset-forge",
                "available": True,
                "command": _quote(
                    [
                        "python",
                        "asset_forge.py",
                        "quality-gltf",
                        str(final_glb),
                        "--profile",
                        profile,
                        "--output",
                        str(workdir / "quality-final.json"),
                    ]
                ),
                "output": str(workdir / "quality-final.json"),
            }
        )

    if target_engine == "godot4":
        commands.append(
            {
                "id": "godot4-delivery",
                "required": True,
                "tool": "asset-forge",
                "available": True,
                "command": _quote(
                    [
                        "python",
                        "asset_forge.py",
                        "validate-godot-3d",
                        str(final_glb),
                        "--profile",
                        profile,
                        "--output",
                        str(workdir / "godot4-delivery.json"),
                    ]
                ),
                "output": str(workdir / "godot4-delivery.json"),
            }
        )

    return {
        "source": str(source_blend),
        "workdir": str(workdir),
        "profile": profile,
        "optimizer": optimizer,
        "targetEngine": target_engine,
        "tools": tools,
        "blenderJob": blender_job,
        "blenderScript": str(blender_script),
        "rawOutput": str(raw_glb),
        "finalOutput": str(final_glb),
        "steps": commands,
    }


def prepare_3d_pipeline(plan: dict) -> None:
    workdir = Path(plan["workdir"])
    workdir.mkdir(parents=True, exist_ok=True)
    write_blender_export_script(
        plan["blenderJob"],
        Path(plan["blenderScript"]),
    )
    (workdir / "pipeline.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def execute_command(command: str, cwd: Path | None = None) -> dict:
    completed = subprocess.run(
        shlex.split(command),
        cwd=cwd,
        shell=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": command,
        "returnCode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _build_production_summary(plan: dict, success: bool, results: list[dict]) -> dict:
    workdir = Path(plan["workdir"])
    raw_report = _read_json_if_exists(workdir / "quality-raw.json")
    final_report = _read_json_if_exists(workdir / "quality-final.json") or raw_report

    summary = {
        "success": success,
        "profile": plan.get("profile"),
        "optimizer": plan.get("optimizer"),
        "targetEngine": plan.get("targetEngine"),
        "rawOutput": plan.get("rawOutput"),
        "finalOutput": plan.get("finalOutput"),
        "steps": [
            {
                "id": item["id"],
                "status": item["status"],
                "tool": item["tool"],
                "returnCode": item.get("returnCode"),
            }
            for item in results
        ],
        "quality": {
            "raw": raw_report,
            "final": final_report,
            "delta": None,
        },
    }

    if raw_report and final_report:
        raw_geometry = raw_report.get("geometry", {})
        final_geometry = final_report.get("geometry", {})
        raw_container = raw_report.get("container", {})
        final_container = final_report.get("container", {})
        summary["quality"]["delta"] = {
            "vertices": final_geometry.get("vertices", 0) - raw_geometry.get("vertices", 0),
            "triangles": final_geometry.get("triangles", 0) - raw_geometry.get("triangles", 0),
            "bytes": final_container.get("bytes", 0) - raw_container.get("bytes", 0),
        }

    return summary


def execute_3d_pipeline(plan: dict, repo_root: Path) -> dict:
    prepare_3d_pipeline(plan)
    results = []
    success = True

    for step in plan["steps"]:
        if not step["available"]:
            result = {
                "id": step["id"],
                "status": "missing-required" if step["required"] else "skipped-unavailable",
                "tool": step["tool"],
                "returnCode": None,
            }
            results.append(result)
            if step["required"]:
                success = False
                break
            continue

        executed = execute_command(step["command"], cwd=repo_root)
        result = {
            "id": step["id"],
            "status": "passed" if executed["returnCode"] == 0 else "failed",
            "tool": step["tool"],
            "returnCode": executed["returnCode"],
            "stdout": executed["stdout"],
            "stderr": executed["stderr"],
        }

        if step["id"] == "khronos-validation" and step.get("output") and executed["stdout"]:
            report_path = Path(step["output"])
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(executed["stdout"], encoding="utf-8")

        results.append(result)
        if executed["returnCode"] != 0:
            success = False
            if step["required"] or step["id"] in {"khronos-validation", "optimize"}:
                break

    summary = _build_production_summary(plan, success, results)
    report_path = Path(plan["workdir"]) / "production-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "success": success,
        "finalOutput": plan["finalOutput"],
        "productionReport": str(report_path),
        "summary": summary,
        "results": results,
    }
