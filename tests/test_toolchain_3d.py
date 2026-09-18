import unittest
from pathlib import Path
from unittest.mock import patch

from toolchain_3d import (
    build_3d_pipeline,
    detect_3d_tools,
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
                "khronos-validation",
                "optimize",
                "post-optimization-validation",
            ],
        )
        self.assertEqual(plan["finalOutput"], "build/asset/optimized.glb")
        self.assertIn("--texture-compress webp", plan["steps"][3]["command"])

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


if __name__ == "__main__":
    unittest.main()
