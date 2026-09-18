import unittest
from pathlib import Path
from unittest.mock import patch

from toolchain_3d import (
    build_3d_pipeline,
    detect_3d_tools,
    execute_3d_pipeline,
    gltf_transform_command,
    gltfpack_command,
    validator_command,
)


class Toolchain3DTests(unittest.TestCase):
    def test_command_builders(self):
        self.assertIn(
            "--stdout model.glb",
            validator_command("gltf_validator", Path("model.glb")),
        )
        self.assertIn(
            "optimize input.glb output.glb",
            gltf_transform_command(
                "gltf-transform",
                Path("input.glb"),
                Path("output.glb"),
            ),
        )
        command = gltfpack_command(
            "gltfpack",
            Path("input.glb"),
            Path("output.glb"),
            compression=True,
        )
        self.assertIn("-i input.glb -o output.glb", command)
        self.assertIn("-cc", command)
        self.assertIn("-kn", command)
        self.assertIn("-km", command)

    @patch("toolchain_3d.shutil.which")
    def test_detect_tools(self, which):
        which.side_effect = lambda name: f"/usr/bin/{name}" if name in {"blender", "gltfpack"} else None
        tools = detect_3d_tools()

        self.assertTrue(tools["blender"]["available"])
        self.assertTrue(tools["gltfpack"]["available"])
        self.assertFalse(tools["gltf-transform"]["available"])

    @patch("toolchain_3d.detect_3d_tools")
    def test_pipeline_contains_export_validate_optimize_validate(self, detect):
        detect.return_value = {
            "blender": {"available": True, "path": "/bin/blender"},
            "gltf-validator": {"available": True, "path": "/bin/gltf_validator"},
            "gltf-transform": {"available": True, "path": "/bin/gltf-transform"},
            "gltfpack": {"available": False, "path": None},
        }

        plan = build_3d_pipeline(
            Path("source.blend"),
            Path("build/asset"),
            profile="character",
            optimizer="gltf-transform",
            texture_compress="webp",
        )

        self.assertEqual(
            [step["id"] for step in plan["steps"]],
            [
                "blender-export",
                "structural-validation",
                "quality-report",
                "khronos-validation",
                "optimize",
                "post-optimization-validation",
                "post-optimization-quality",
            ],
        )
        self.assertEqual(plan["finalOutput"], "build/asset/optimized.glb")
        self.assertIn("--texture-compress webp", plan["steps"][4]["command"])

    @patch("toolchain_3d.detect_3d_tools")
    def test_none_optimizer_keeps_raw_output(self, detect):
        detect.return_value = {
            "blender": {"available": False, "path": None},
            "gltf-validator": {"available": False, "path": None},
            "gltf-transform": {"available": False, "path": None},
            "gltfpack": {"available": False, "path": None},
        }

        plan = build_3d_pipeline(
            Path("source.blend"),
            Path("build/asset"),
            optimizer="none",
        )

        self.assertEqual(plan["finalOutput"], "build/asset/raw.glb")
        self.assertNotIn("optimize", [step["id"] for step in plan["steps"]])

    def test_invalid_optimizer_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "optimizer must be"):
            build_3d_pipeline(
                Path("source.blend"),
                Path("build/asset"),
                optimizer="invalid",
            )

    @patch("toolchain_3d.detect_3d_tools")
    def test_missing_optimizer_falls_back_to_raw_output(self, detect):
        detect.return_value = {
            "blender": {"available": True, "path": "/bin/blender"},
            "gltf-validator": {"available": False, "path": None},
            "gltf-transform": {"available": False, "path": None},
            "gltfpack": {"available": False, "path": None},
        }

        plan = build_3d_pipeline(
            Path("source.blend"),
            Path("build/asset"),
            optimizer="gltf-transform",
        )

        self.assertEqual(plan["finalOutput"], "build/asset/raw.glb")
        validation_steps = [
            step for step in plan["steps"]
            if step["id"] == "post-optimization-validation"
        ]
        self.assertEqual(len(validation_steps), 1)
        self.assertIn("raw.glb", validation_steps[0]["command"])

    @patch("toolchain_3d.execute_command")
    @patch("toolchain_3d.prepare_3d_pipeline")
    def test_execute_pipeline_skips_unavailable_optional_tools(self, prepare, execute):
        plan = {
            "workdir": "build/x",
            "finalOutput": "build/x/raw.glb",
            "steps": [
                {
                    "id": "blender-export",
                    "required": True,
                    "tool": "blender",
                    "available": True,
                    "command": "blender --background",
                    "output": "build/x/raw.glb",
                },
                {
                    "id": "khronos-validation",
                    "required": False,
                    "tool": "gltf-validator",
                    "available": False,
                    "command": "gltf_validator --stdout build/x/raw.glb",
                    "output": "build/x/report.json",
                },
            ],
        }
        execute.return_value = {"returnCode": 0, "stdout": "", "stderr": ""}

        result = execute_3d_pipeline(plan, Path("."))

        self.assertTrue(result["success"])
        self.assertEqual(result["results"][1]["status"], "skipped-unavailable")
        execute.assert_called_once()

    @patch("toolchain_3d.execute_command")
    @patch("toolchain_3d.prepare_3d_pipeline")
    def test_execute_pipeline_stops_on_required_failure(self, prepare, execute):
        plan = {
            "workdir": "build/x",
            "finalOutput": "build/x/raw.glb",
            "steps": [
                {
                    "id": "blender-export",
                    "required": True,
                    "tool": "blender",
                    "available": True,
                    "command": "blender --background",
                    "output": "build/x/raw.glb",
                }
            ],
        }
        execute.return_value = {"returnCode": 2, "stdout": "", "stderr": "failed"}

        result = execute_3d_pipeline(plan, Path("."))

        self.assertFalse(result["success"])
        self.assertEqual(result["results"][0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
