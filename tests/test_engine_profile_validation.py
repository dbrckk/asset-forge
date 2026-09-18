import json
import tempfile
import unittest
from pathlib import Path

from engine_profile_validation import (
    validate_all_godot_profiles,
    validate_godot_profile_data,
    validate_godot_profile_file,
)


class EngineProfileValidationTests(unittest.TestCase):
    def valid_profile(self):
        return {
            "id": "godot4-prop",
            "engine": "Godot 4",
            "assetProfile": "prop",
            "sceneImport": {
                "useNameSuffixes": True,
                "useNodeTypeSuffixes": True,
                "generateTangentsIfMissing": True,
                "preferStaticScene": True,
            },
            "animation": {
                "import": False,
                "fps": 30,
                "trimming": True,
                "removeImmutableTracks": True,
            },
            "textures": {
                "preferEmbeddedOrProjectLocal": True,
                "remoteUrisAllowed": False,
            },
        }

    def test_valid_profile_passes(self):
        self.assertEqual(validate_godot_profile_data(self.valid_profile(), "prop"), [])

    def test_missing_required_field_fails(self):
        data = self.valid_profile()
        del data["animation"]["fps"]
        errors = validate_godot_profile_data(data, "prop")
        self.assertTrue(any("animation.fps: required" in error for error in errors))

    def test_unknown_field_fails(self):
        data = self.valid_profile()
        data["sceneImport"]["mystery"] = True
        errors = validate_godot_profile_data(data, "prop")
        self.assertTrue(any("sceneImport.mystery: unknown field" in error for error in errors))

    def test_wrong_type_fails(self):
        data = self.valid_profile()
        data["animation"]["import"] = "yes"
        errors = validate_godot_profile_data(data, "prop")
        self.assertTrue(any("animation.import: bool required" in error for error in errors))

    def test_invalid_fps_fails(self):
        data = self.valid_profile()
        data["animation"]["fps"] = 0
        errors = validate_godot_profile_data(data, "prop")
        self.assertTrue(any("animation.fps: must be between 1 and 240" in error for error in errors))

    def test_profile_name_mismatch_fails(self):
        data = self.valid_profile()
        errors = validate_godot_profile_data(data, "character")
        self.assertTrue(any("assetProfile: expected character" in error for error in errors))

    def test_invalid_json_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prop.json"
            path.write_text("{bad", encoding="utf-8")
            _, errors = validate_godot_profile_file(path, "prop")
        self.assertTrue(any(error.startswith("json:") for error in errors))

    def test_repository_profiles_all_validate(self):
        root = Path(__file__).resolve().parents[1]
        report = validate_all_godot_profiles(root)
        self.assertTrue(report["valid"], report)


if __name__ == "__main__":
    unittest.main()
