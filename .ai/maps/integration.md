This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.
The content has been processed where content has been compressed (code blocks are separated by ⋮---- delimiter).

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: **/*.{py,js,mjs,cjs,ts,tsx,jsx,java,kt,kts,gd,groovy,gradle,toml,json,yaml,yml,sql,sh}
- Files matching these patterns are excluded: .ai/**, **/node_modules/**, **/.gradle/**, **/build/**, **/dist/**, **/.venv/**, **/__pycache__/**, **/.pytest_cache/**, **/.git/**, **/coverage/**, **/*.lock, **/*.min.js, **/*.map, assets/**, art/**, art_sources/**, marketing/**, colab/**, kaggle/**, discovery-cache.json, health-snapshot.json, history.json
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
godot4_import_smoke.py
```

# Files

## File: godot4_import_smoke.py
```python
#!/usr/bin/env python3
"""Functional CI smoke: own PNG -> real Asset Forge CLI -> real Godot 4 loader.

No AI generation, credentials, paid inference, or external asset provenance.
Godot must be installed separately and GODOT_BIN must point to that executable.
This is an integration check, not a new unit-test suite.
"""
⋮----
ROOT = Path(__file__).resolve().parent.parent
⋮----
def run(command: list[str], *, cwd: Path, timeout: int) -> str
⋮----
completed = subprocess.run(
combined = completed.stdout + "\n" + completed.stderr
⋮----
GODOT_VALIDATOR = """extends SceneTree
⋮----
def main() -> int
⋮----
binary_value = os.environ.get("GODOT_BIN", "").strip()
⋮----
godot = Path(binary_value).resolve(strict=True)
⋮----
work = Path(td)
original = work / "original-source.png"
image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
brush = ImageDraw.Draw(image)
⋮----
request = json.loads(
⋮----
input_path = work / "production-request.json"
⋮----
output = work / "asset-forge-output"
⋮----
report_path = output / "production-report.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
⋮----
asset = Path(report["artifact"]).resolve(strict=True)
⋮----
atlas = json.loads((output / "atlas-metadata.json").read_text(encoding="utf-8"))
⋮----
tres = output / "player.tres"
⋮----
# Exercise the real batch coordinator with another fresh CLI fulfill,
# not a fake generator or an unexecuted sample. No GPU/network needed.
⋮----
wrapper = work / "asset-forge-cli"
⋮----
batch_spec = work / "batch-spec.json"
⋮----
batch_dir = work / "real-batch"
batch = run_remote_batch(batch_spec, batch_dir, executable=str(wrapper))
⋮----
row = batch["items"][0]
companions = {value["role"]: value for value in row["additional_artifacts"]}
⋮----
file = batch_dir / entry["artifact"]
⋮----
project = work / "godot4-project"
⋮----
# The editor performs the actual Texture2D import before the game
# runtime attempts to load the generated SpriteFrames resource.
⋮----
result = run(
```
