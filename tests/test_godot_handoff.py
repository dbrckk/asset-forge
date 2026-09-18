import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from godot_handoff import (
    build_import_recommendations,
    godot_import_command,
    prepare_godot_handoff,
    validate_godot_handoff,
)


class GodotHandoffTests(unittest.TestCase):
    def test_recommendations_disable_animation_for_prop_without_clips(self):
        recommendations = build_import_recommendations(
            "prop",
            {"scene": {"animations": 0, "godotNameSuffixes": {}}},
        )

        self.assertFalse(recommendations["animation"]["import"])
        self.assertTrue(recommendations["sceneImport"]["useNameSuffixes"])

    def test_prepare_handoff_copies_glb_and_writes_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.glb"
            source.write_bytes(b"glb-data")
            report = {"ready": True, "scene": {"animations": 0, "godotNameSuffixes": {}}}

            result = prepare_godot_handoff(
                source,
                root / "build",
                profile="prop",
                delivery_report=report,
            )

            project_dir = Path(result["projectDir"])
            copied = Path(result["asset"])
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))

            self.assertEqual(copied.read_bytes(), b"glb-data")
            self.assertTrue((project_dir / "project.godot").is_file())
            self.assertEqual(manifest["asset"], "res://assets/model.glb")
            self.assertTrue(manifest["deliveryReady"])

    def test_non_glb_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.gltf"
            source.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expects a .glb"):
                prepare_godot_handoff(source, root / "build", profile="prop")

    def test_import_command_uses_headless_import(self):
        command = godot_import_command("godot", Path("project"))

        self.assertEqual(
            command,
            ["godot", "--headless", "--path", "project", "--import"],
        )

    @patch("godot_handoff.detect_godot")
    def test_missing_godot_is_non_blocking(self, detect):
        detect.return_value = {"available": False, "path": None}
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            result = validate_godot_handoff(project)

        self.assertFalse(result["available"])
        self.assertIsNone(result["passed"])

    @patch("godot_handoff.subprocess.run")
    @patch("godot_handoff.detect_godot")
    def test_available_godot_import_passes(self, detect, run):
        detect.return_value = {"available": True, "path": "/usr/bin/godot"}
        run.return_value.returncode = 0
        run.return_value.stdout = "imported"
        run.return_value.stderr = ""

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            result = validate_godot_handoff(project)

        self.assertTrue(result["available"])
        self.assertTrue(result["passed"])
        self.assertIn("--import", result["command"])


if __name__ == "__main__":
    unittest.main()
