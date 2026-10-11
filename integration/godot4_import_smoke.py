#!/usr/bin/env python3
"""Functional CI smoke: own PNG -> real Asset Forge CLI -> real Godot 4 loader.

No AI generation, credentials, paid inference, or external asset provenance.
Godot must be installed separately and GODOT_BIN must point to that executable.
This is an integration check, not a new unit-test suite.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str], *, cwd: Path, timeout: int) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    combined = completed.stdout + "\n" + completed.stderr
    if completed.returncode != 0:
        raise RuntimeError(
            "Integration command failed (exit "
            + str(completed.returncode)
            + "): "
            + " ".join(Path(arg).name if idx == 0 else arg for idx, arg in enumerate(command[:4]))
            + "\n"
            + combined[-3000:]
        )
    return combined


GODOT_VALIDATOR = """extends SceneTree

func _init() -> void:
    var frames: SpriteFrames = load("res://player.tres")
    if frames == null:
        push_error("Cannot load SpriteFrames resource")
        quit(1)
        return
    if not frames.has_animation("default"):
        push_error("Missing default animation")
        quit(2)
        return
    if frames.get_frame_count("default") != 2:
        push_error("Expected exactly two imported frames")
        quit(3)
        return
    var expected_regions = [
        Rect2(0, 0, 32, 32),
        Rect2(32, 0, 32, 32),
    ]
    for index in range(2):
        var texture := frames.get_frame_texture("default", index)
        if not (texture is AtlasTexture):
            push_error("Expected an imported AtlasTexture")
            quit(4)
            return
        if texture.region != expected_regions[index]:
            push_error("Invalid exported atlas region")
            quit(5)
            return
        if texture.atlas == null:
            push_error("Atlas PNG was not imported")
            quit(6)
            return
        if texture.atlas.get_width() != 64 or texture.atlas.get_height() != 32:
            push_error("Unexpected imported atlas dimensions")
            quit(7)
            return
    var node := AnimatedSprite2D.new()
    node.sprite_frames = frames
    node.animation = "default"
    node.frame = 1
    if node.frame != 1:
        push_error("SpriteFrames cannot be used by AnimatedSprite2D")
        quit(8)
        return
    node.free()
    print("GODOT_ASSET_FORGE_IMPORT_OK frames=2 dimensions=64x32")
    quit()
"""


def main() -> int:
    binary_value = os.environ.get("GODOT_BIN", "").strip()
    if not binary_value:
        raise RuntimeError("GODOT_BIN must name the checked Godot 4 binary")
    godot = Path(binary_value).resolve(strict=True)
    with TemporaryDirectory(prefix="asset-forge-godot4-import-") as td:
        work = Path(td)
        original = work / "original-source.png"
        image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        brush = ImageDraw.Draw(image)
        brush.ellipse((7, 5, 24, 25), fill=(30, 180, 220, 255))
        brush.rectangle((39, 6, 57, 25), fill=(240, 100, 35, 255))
        image.save(original, format="PNG")

        request = json.loads(
            (ROOT / "examples/production-request.json").read_text(encoding="utf-8")
        )
        request["requestId"] = "godot4-real-engine-integration"
        request["instruction"] = "Validate two original frames for a real Godot engine import"
        request["manifest"]["source"] = {"mode": "custom", "author": "original-ci"}
        request["manifest"]["license"] = {
            "id": "project-owned",
            "commercialUse": True,
            "derivatives": True,
            "attributionRequired": False,
        }
        request["manifest"]["constraints"].update(
            {
                "frameWidth": 32,
                "frameHeight": 32,
                "expectedFrames": 2,
                "pixelArt": True,
                "interpolation": "nearest",
                "requiresAlpha": True,
            }
        )
        input_path = work / "production-request.json"
        input_path.write_text(json.dumps(request), encoding="utf-8")
        output = work / "asset-forge-output"
        run(
            [
                sys.executable,
                str(ROOT / "asset_forge.py"),
                "fulfill",
                str(input_path),
                "--source",
                str(original),
                "--output-dir",
                str(output),
            ],
            cwd=ROOT,
            timeout=90,
        )
        report_path = output / "production-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["success"] is True
        assert report["provenance"]["source"]["mode"] == "custom"
        assert report["generation"]["backend"] == "provided"
        assert report["engineHandoff"]["type"] == "spriteframes"
        assert report["engineHandoff"]["ready"] is True

        asset = Path(report["artifact"]).resolve(strict=True)
        assert asset.parent == output.resolve()
        with Image.open(asset) as png:
            assert png.size == (64, 32)
            assert png.convert("RGBA").getpixel((0, 0))[3] == 0

        atlas = json.loads((output / "atlas-metadata.json").read_text(encoding="utf-8"))
        assert atlas["frameCount"] == 2
        tres = output / "player.tres"
        assert tres.is_file()
        assert {Path(name).name for name in report["additionalArtifacts"]} == {
            "atlas-metadata.json", "player.tres"
        }

        # Exercise the real batch coordinator with another fresh CLI fulfill,
        # not a fake generator or an unexecuted sample. No GPU/network needed.
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from remote_batch import run as run_remote_batch
        wrapper = work / "asset-forge-cli"
        wrapper.write_text(
            "#!/bin/sh\nexec " + shlex.quote(sys.executable) + " "
            + shlex.quote(str(ROOT / "asset_forge.py")) + ' "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o700)
        batch_spec = work / "batch-spec.json"
        batch_spec.write_text(json.dumps({"items": [{
            "id": "bundled-player",
            "request": request,
            "source_path": str(original),
            "target_path": "assets/art/bundled-player.png",
        }]}), encoding="utf-8")
        batch_dir = work / "real-batch"
        batch = run_remote_batch(batch_spec, batch_dir, executable=str(wrapper))
        assert batch["success"] is True and batch["count"] == 1
        row = batch["items"][0]
        companions = {value["role"]: value for value in row["additional_artifacts"]}
        assert set(companions) == {"godot-spriteframes", "godot-atlas-metadata"}
        assert {Path(companions[role]["artifact"]).name for role in companions} == {
            "bundled-player.tres", "bundled-player.atlas-metadata.json"
        }
        for entry in [row, *companions.values()]:
            file = batch_dir / entry["artifact"]
            assert file.is_file() and file.stat().st_size > 0
            assert hashlib.sha256(file.read_bytes()).hexdigest() == entry["sha256"]
        print("PASS: real Asset Forge batch includes hashed Godot SpriteFrames and atlas metadata")

        project = work / "godot4-project"
        project.mkdir()
        shutil.copy2(asset, project / "player.png")
        shutil.copy2(tres, project / "player.tres")
        (project / "project.godot").write_text(
            'config_version=5\n'
            '[application]\n'
            'config/name="Asset Forge Godot 4 Import Smoke"\n'
            '[rendering]\n'
            'renderer/rendering_method="gl_compatibility"\n',
            encoding="utf-8",
        )
        (project / "verify.gd").write_text(GODOT_VALIDATOR, encoding="utf-8")

        # The editor performs the actual Texture2D import before the game
        # runtime attempts to load the generated SpriteFrames resource.
        run([str(godot), "--headless", "--path", str(project), "--import"], cwd=work, timeout=120)
        result = run(
            [str(godot), "--headless", "--path", str(project), "--script", "res://verify.gd"],
            cwd=work,
            timeout=60,
        )
        if "GODOT_ASSET_FORGE_IMPORT_OK" not in result:
            raise RuntimeError("Godot returned success without the import verification marker")
        print("PASS: actual Godot 4 editor import and runtime SpriteFrames load")
        print("PASS: AtlasTexture regions, texture dimensions and AnimatedSprite2D assignment")
        print("asset SHA256:", hashlib.sha256(asset.read_bytes()).hexdigest())
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
