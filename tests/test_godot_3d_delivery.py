import json
import tempfile
import unittest
from pathlib import Path

from godot_3d_delivery import godot_3d_delivery_report


class Godot3DDeliveryTests(unittest.TestCase):
    def write(self, root: Path, data: dict, suffix: str = ".glb.json") -> Path:
        path = root / ("asset.gltf" if suffix == ".gltf" else "asset.gltf")
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def base(self):
        return {
            "asset": {"version": "2.0"},
            "nodes": [{"name": "Root"}, {"name": "Crate-rigid"}],
            "meshes": [],
            "materials": [],
            "animations": [],
            "accessors": [],
            "images": [],
        }

    def test_detects_godot_name_suffixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = godot_3d_delivery_report(
                self.write(Path(tmp), self.base()),
                "prop",
            )

        self.assertEqual(report["scene"]["godotNameSuffixes"]["rigid"], 1)

    def test_detects_collision_import_hints(self):
        data = self.base()
        data["nodes"] = [
            {"name": "Crate-convcol"},
            {"name": "LevelCollision-colonly"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            report = godot_3d_delivery_report(
                self.write(Path(tmp), data),
                "prop",
            )

        self.assertEqual(report["scene"]["godotNameSuffixes"]["convcol"], 1)
        self.assertEqual(report["scene"]["godotNameSuffixes"]["colonly"], 1)

    def test_duplicate_node_names_warn(self):
        data = self.base()
        data["nodes"] = [{"name": "Bone"}, {"name": "Bone"}]
        with tempfile.TemporaryDirectory() as tmp:
            report = godot_3d_delivery_report(self.write(Path(tmp), data), "prop")

        self.assertTrue(any("duplicate node names" in item for item in report["warnings"]))

    def test_loop_animation_hint_detected(self):
        data = self.base()
        data["animations"] = [{"name": "Run-loop", "samplers": [], "channels": []}]
        with tempfile.TemporaryDirectory() as tmp:
            report = godot_3d_delivery_report(self.write(Path(tmp), data), "prop")

        self.assertEqual(report["scene"]["loopingAnimationHints"], 1)

    def test_remote_image_blocks_delivery(self):
        data = self.base()
        data["images"] = [{"uri": "https://example.com/albedo.png"}]
        data["textures"] = [{"source": 0}]
        with tempfile.TemporaryDirectory() as tmp:
            report = godot_3d_delivery_report(self.write(Path(tmp), data), "prop")

        self.assertFalse(report["ready"])
        self.assertTrue(any("remote image" in item for item in report["errors"]))

    def test_double_sided_material_warns(self):
        data = self.base()
        data["materials"] = [
            {
                "pbrMetallicRoughness": {},
                "doubleSided": True,
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            report = godot_3d_delivery_report(self.write(Path(tmp), data), "prop")

        self.assertTrue(any("double-sided" in item for item in report["warnings"]))


    def test_delivery_report_includes_runtime_lod_collision_and_pbr_plan(self):
        data = self.base()
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(Path(tmp), data)
            result = godot_3d_delivery_report(path, "prop")

        plan = result["runtimePlan"]
        self.assertEqual(plan["schema"], "asset-forge/runtime-3d-plan/v1")
        self.assertEqual(plan["profile"], "prop")
        self.assertIn("levels", plan["lod"])
        self.assertIn("strategy", plan["collision"])
        self.assertEqual(plan["collision"]["godotImportHint"], "-convcol")
        self.assertIn("allMaterialsPbr", plan["pbr"])

if __name__ == "__main__":
    unittest.main()
