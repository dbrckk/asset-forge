from __future__ import annotations

import json
import shlex
from pathlib import Path


DEFAULT_EXPORT_SETTINGS = {
    "export_format": "GLB",
    "export_apply": True,
    "export_yup": True,
    "export_texcoords": True,
    "export_normals": True,
    "export_tangents": True,
    "export_materials": "EXPORT",
    "export_animations": True,
}


def build_blender_export_job(
    source_blend: Path,
    output_glb: Path,
    *,
    selection_only: bool = False,
    animations: bool = True,
    apply_modifiers: bool = True,
) -> dict:
    settings = dict(DEFAULT_EXPORT_SETTINGS)
    settings["use_selection"] = bool(selection_only)
    settings["export_animations"] = bool(animations)
    settings["export_apply"] = bool(apply_modifiers)

    return {
        "source": str(source_blend),
        "output": str(output_glb),
        "settings": settings,
    }


def render_blender_python(job: dict) -> str:
    source = job["source"]
    output = job["output"]
    settings = job["settings"]

    return (
        "import bpy\n"
        f"source = {source!r}\n"
        f"output = {output!r}\n"
        "bpy.ops.wm.open_mainfile(filepath=source)\n"
        "bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None\n"
        "bpy.ops.export_scene.gltf(\n"
        f"    filepath=output,\n"
        f"    export_format={settings['export_format']!r},\n"
        f"    use_selection={settings['use_selection']!r},\n"
        f"    export_apply={settings['export_apply']!r},\n"
        f"    export_yup={settings['export_yup']!r},\n"
        f"    export_texcoords={settings['export_texcoords']!r},\n"
        f"    export_normals={settings['export_normals']!r},\n"
        f"    export_tangents={settings['export_tangents']!r},\n"
        f"    export_materials={settings['export_materials']!r},\n"
        f"    export_animations={settings['export_animations']!r},\n"
        ")\n"
    )


def write_blender_export_script(job: dict, output_script: Path) -> None:
    output_script.parent.mkdir(parents=True, exist_ok=True)
    output_script.write_text(render_blender_python(job), encoding="utf-8")


def render_blender_command(blender_executable: str, script_path: Path) -> str:
    return " ".join(
        shlex.quote(part)
        for part in [
            blender_executable,
            "--background",
            "--python",
            str(script_path),
        ]
    )


def write_job_manifest(job: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, indent=2, sort_keys=True) + "\n", encoding="utf-8")
