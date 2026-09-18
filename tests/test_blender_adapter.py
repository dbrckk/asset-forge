import unittest
from pathlib import Path

from blender_adapter import (
    build_blender_export_job,
    render_blender_command,
    render_blender_python,
)


class BlenderAdapterTests(unittest.TestCase):
    def test_build_export_job_defaults(self):
        job = build_blender_export_job(
            Path("character.blend"),
            Path("build/character.glb"),
        )

        self.assertEqual(job["source"], "character.blend")
        self.assertEqual(job["output"], "build/character.glb")
        self.assertTrue(job["settings"]["export_yup"])
        self.assertTrue(job["settings"]["export_apply"])
        self.assertTrue(job["settings"]["export_animations"])

    def test_selection_and_animation_flags(self):
        job = build_blender_export_job(
            Path("prop.blend"),
            Path("prop.glb"),
            selection_only=True,
            animations=False,
            apply_modifiers=False,
        )

        self.assertTrue(job["settings"]["use_selection"])
        self.assertFalse(job["settings"]["export_animations"])
        self.assertFalse(job["settings"]["export_apply"])

    def test_rendered_script_opens_source_and_exports(self):
        job = build_blender_export_job(
            Path("scene.blend"),
            Path("scene.glb"),
        )
        script = render_blender_python(job)

        self.assertIn("bpy.ops.wm.open_mainfile", script)
        self.assertIn("bpy.ops.export_scene.gltf", script)
        self.assertIn("scene.blend", script)
        self.assertIn("scene.glb", script)

    def test_render_command_uses_background_mode(self):
        command = render_blender_command("blender", Path("build/export.py"))

        self.assertIn("--background", command)
        self.assertIn("--python", command)
        self.assertIn("build/export.py", command)


if __name__ == "__main__":
    unittest.main()
