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
- Only files matching these patterns are included: **/*.{py,js,mjs,cjs,ts,tsx,jsx,java,kt,kts,gd,groovy,gradle,toml,json,yaml,yml,sql,sh}, README.md, AGENTS.md, PROJECT_*.md
- Files matching these patterns are excluded: .ai/**, **/node_modules/**, **/.gradle/**, **/build/**, **/dist/**, **/.venv/**, **/__pycache__/**, **/.pytest_cache/**, **/.git/**, **/coverage/**, **/*.lock, **/*.min.js, **/*.map, assets/**, art/**, art_sources/**, marketing/**, colab/**, kaggle/**, discovery-cache.json, health-snapshot.json, history.json
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
.github/
  workflows/
    repo-standards.yml
    validate.yml
config/
  tooling.json
examples/
  asset-manifest.json
pipelines/
  model-3d.json
  sprite-2d.json
schemas/
  asset-manifest.schema.json
tests/
  test_asset_forge.py
AGENTS.md
asset_forge.py
README.md
````

# Files

## File: .github/workflows/repo-standards.yml
````yaml
name: Repository standards

on:
  push:
    branches: [main]
    paths-ignore:
      - ".ai/**"
  workflow_dispatch:

permissions:
  contents: write
  actions: read

concurrency:
  group: repo-standards-${{ github.repository }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  repository-standards:
    uses: dbrckk/repo-standards/.github/workflows/reusable-unified.yml@v10
````

## File: .github/workflows/validate.yml
````yaml
name: Validate asset-forge

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Compile
        run: python -m compileall -q asset_forge.py tests
      - name: Unit tests
        run: python -m unittest discover -s tests -v
      - name: Validate example manifest
        run: python asset_forge.py validate examples/asset-manifest.json
      - name: Build example plan
        run: python asset_forge.py plan examples/asset-manifest.json
````

## File: config/tooling.json
````json
{
  "version": 1,
  "selectionPolicy": {
    "preferOpenSource": true,
    "requireKnownLicense": true,
    "discoveryOrder": [
      "approved-registry",
      "dbrckk/star-list",
      "github",
      "web"
    ]
  },
  "tools": [
    {
      "id": "blender",
      "name": "Blender",
      "status": "preferred",
      "domains": ["3d", "rigging", "animation-3d", "rendering", "uv"],
      "automation": ["python", "cli"],
      "outputs": ["blend", "gltf", "glb", "fbx", "obj"],
      "license": "GPL-2.0-or-later"
    },
    {
      "id": "gltf-validator",
      "name": "Khronos glTF Validator",
      "status": "candidate",
      "domains": ["3d-validation", "gltf"],
      "automation": ["cli", "library"],
      "outputs": ["validation-report"],
      "license": "Apache-2.0"
    },
    {
      "id": "gltf-transform",
      "name": "glTF Transform",
      "status": "candidate",
      "domains": ["3d-optimization", "gltf", "texture-optimization"],
      "automation": ["cli", "library"],
      "outputs": ["gltf", "glb"],
      "license": "MIT"
    },
    {
      "id": "meshoptimizer",
      "name": "meshoptimizer",
      "status": "candidate",
      "domains": ["mesh-optimization", "gltf"],
      "automation": ["cli", "library"],
      "outputs": ["optimized-mesh", "glb"],
      "license": "MIT"
    },
    {
      "id": "pixelorama",
      "name": "Pixelorama",
      "status": "candidate",
      "domains": ["pixel-art", "sprites", "animation-2d"],
      "automation": [],
      "outputs": ["png", "sprite-sheet"],
      "license": "MIT"
    },
    {
      "id": "inkscape",
      "name": "Inkscape",
      "status": "candidate",
      "domains": ["vector", "svg", "ui"],
      "automation": ["cli"],
      "outputs": ["svg", "png", "pdf"],
      "license": "GPL-2.0-or-later"
    }
  ]
}
````

## File: examples/asset-manifest.json
````json
{
  "id": "deadline-zero-player-idle",
  "project": "deadline-zero",
  "type": "sprite",
  "importance": "primary",
  "source": {
    "mode": "custom",
    "uri": null,
    "author": null
  },
  "license": {
    "id": "project-owned",
    "commercialUse": true,
    "derivatives": true,
    "attributionRequired": false
  },
  "target": {
    "engine": "godot",
    "format": "png",
    "maxBytes": 524288
  },
  "constraints": {
    "pixelArt": true,
    "frameWidth": 32,
    "frameHeight": 32,
    "interpolation": "nearest"
  }
}
````

## File: pipelines/model-3d.json
````json
{
  "id": "model-3d",
  "assetTypes": ["mesh", "prop", "environment", "character-3d"],
  "stages": [
    "read-project-art-direction",
    "resolve-source-or-create",
    "normalize-scale-and-origin",
    "validate-topology-and-normals",
    "validate-uv",
    "validate-materials-and-textures",
    "validate-rig-and-animation-if-present",
    "export-glb",
    "optimize-glb",
    "validate-gltf",
    "record-provenance-and-license",
    "validate-target-import"
  ],
  "defaults": {
    "masterFormat": "blend",
    "deliveryFormat": "glb",
    "embedTextures": true
  }
}
````

## File: pipelines/sprite-2d.json
````json
{
  "id": "sprite-2d",
  "assetTypes": ["sprite", "sprite-sheet", "tileset", "pixel-art"],
  "stages": [
    "read-project-art-direction",
    "resolve-source-or-create",
    "normalize-canvas-and-scale",
    "validate-png-integrity",
    "validate-alpha-palette-and-grid",
    "validate-frame-count-and-atlas-budget",
    "build-animation-frames",
    "emit-atlas-metadata",
    "pack-atlas-if-requested",
    "optimize-delivery-format",
    "record-provenance-and-license",
    "validate-target-import"
  ],
  "defaults": {
    "masterFormat": "png",
    "interpolation": "nearest",
    "powerOfTwoAtlas": false
  }
}
````

## File: schemas/asset-manifest.schema.json
````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "asset-forge asset manifest",
  "type": "object",
  "required": ["id", "project", "type", "importance", "source", "license", "target"],
  "properties": {
    "id": {"type": "string", "minLength": 1},
    "project": {"type": "string", "minLength": 1},
    "type": {"type": "string", "minLength": 1},
    "importance": {"enum": ["primary", "secondary"]},
    "source": {
      "type": "object",
      "required": ["mode"],
      "properties": {
        "mode": {"enum": ["custom", "external", "generated"]},
        "uri": {"type": ["string", "null"]},
        "author": {"type": ["string", "null"]}
      },
      "additionalProperties": true
    },
    "license": {
      "type": "object",
      "required": ["id", "commercialUse", "derivatives"],
      "properties": {
        "id": {"type": "string", "minLength": 1},
        "commercialUse": {"type": "boolean"},
        "derivatives": {"type": "boolean"},
        "attributionRequired": {"type": "boolean"}
      },
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "required": ["format"],
      "properties": {
        "engine": {"type": ["string", "null"]},
        "format": {"type": "string", "minLength": 1},
        "maxBytes": {"type": ["integer", "null"], "minimum": 1}
      },
      "additionalProperties": true
    },
    "constraints": {"type": "object"}
  },
  "additionalProperties": true
}
````

## File: tests/test_asset_forge.py
````python
ROOT = Path(__file__).resolve().parents[1]
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
signature = b"\x89PNG\r\n\x1a\n"
ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
parts = [signature, chunk(b"IHDR", ihdr_data)]
⋮----
palette = bytearray()
⋮----
value = index % 256
⋮----
channels = {2: 3, 6: 4}.get(color_type, 1)
row = b"\x00" + (b"\x00" * width * channels)
⋮----
class AssetForgeTests(unittest.TestCase)
⋮----
def load_example(self)
⋮----
def test_example_manifest_is_valid(self)
⋮----
def test_pixel_art_rejects_non_nearest_interpolation(self)
⋮----
manifest = self.load_example()
⋮----
def test_external_asset_requires_uri(self)
⋮----
errors = asset_forge.validate_manifest(manifest)
⋮----
def test_incompatible_commercial_license_is_rejected(self)
⋮----
def test_plan_routes_sprite_to_2d_pipeline(self)
⋮----
plan = asset_forge.build_plan(manifest, ROOT)
⋮----
tool_ids = [item["id"] for item in plan["candidateTools"]]
⋮----
def test_secondary_custom_asset_prompts_reuse_search(self)
⋮----
def test_png_sprite_grid_validation_passes(self)
⋮----
image = Path(tmp) / "sprite.png"
⋮----
def test_png_sprite_grid_validation_rejects_bad_width(self)
⋮----
def test_png_alpha_requirement(self)
⋮----
def test_palette_transparency_and_max_colors(self)
⋮----
def test_power_of_two_atlas(self)
⋮----
def test_atlas_manifest_contains_frame_rectangles(self)
⋮----
atlas = asset_forge.build_atlas_manifest(image, manifest)
⋮----
def test_invalid_png_crc_is_rejected(self)
⋮----
image = Path(tmp) / "bad.png"
⋮----
data = bytearray(image.read_bytes())
````

## File: AGENTS.md
````markdown
# asset-forge agent instructions

This repository inherits global conventions from `dbrckk/repo-standards`.

## Context order

1. Read `.ai/project-state.md`.
2. Read task-relevant pipeline definitions.
3. Read `config/tooling.json` when selecting production tools.
4. Read the manifest/schema relevant to the requested asset.
5. Fetch only implementation files required for the task.

## Production rules

- Treat this repository as production infrastructure, not an asset dump.
- Do not store large reusable binary libraries in Git unless explicitly justified.
- Prefer deterministic transformations and reproducible commands.
- Preserve source/master assets separately from optimized delivery assets.
- Every external asset must have source and license metadata.
- Important identity-bearing assets default to custom creation rather than approximate stock substitution.
- Secondary assets may be sourced externally when style, quality, license, and technical constraints match.
- Never silently change the consuming project's art direction.

## Tool selection

Selection order:

1. approved tool in `config/tooling.json`;
2. candidate from `dbrckk/star-list`;
3. broader GitHub/web discovery;
4. custom implementation only when existing tools are insufficient.

A discovered tool must be reviewed before being marked approved.

## Definition of done

A workflow is complete only when provenance is known, licensing is compatible, technical validation passes, export is reproducible, and the consuming project can import the result.
````

## File: asset_forge.py
````python
#!/usr/bin/env python3
"""Dependency-free asset-forge manifest validator, planner, PNG inspector, and atlas metadata builder."""
⋮----
PIPELINES = {
⋮----
TOOL_DOMAINS = {
⋮----
ALLOWED_IMPORTANCE = {"primary", "secondary"}
ALLOWED_SOURCE_MODES = {"custom", "external", "generated"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
⋮----
def load_json(path: Path) -> dict
⋮----
data = json.load(handle)
⋮----
def validate_manifest(manifest: dict) -> list[str]
⋮----
errors: list[str] = []
⋮----
value = manifest.get(field)
⋮----
source = manifest.get("source")
⋮----
mode = source.get("mode")
⋮----
license_data = manifest.get("license")
⋮----
license_id = license_data.get("id")
⋮----
target = manifest.get("target")
⋮----
output_format = target.get("format")
⋮----
max_bytes = target.get("maxBytes")
⋮----
constraints = manifest.get("constraints", {})
⋮----
value = constraints.get(field)
⋮----
def is_power_of_two(value: int) -> bool
⋮----
def parse_png_chunks(data: bytes) -> list[tuple[bytes, bytes]]
⋮----
chunks: list[tuple[bytes, bytes]] = []
offset = 8
saw_iend = False
⋮----
length = struct.unpack(">I", data[offset : offset + 4])[0]
kind = data[offset + 4 : offset + 8]
end = offset + 12 + length
⋮----
payload = data[offset + 8 : offset + 8 + length]
expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
⋮----
offset = end
⋮----
saw_iend = True
⋮----
def inspect_png(path: Path) -> dict
⋮----
data = path.read_bytes()
chunks = parse_png_chunks(data)
⋮----
palette_entries = None
has_trns = False
idat_bytes = 0
⋮----
palette_entries = len(payload) // 3
⋮----
has_trns = True
⋮----
has_alpha = color_type in {4, 6} or has_trns
⋮----
def sprite_grid(info: dict, constraints: dict) -> dict
⋮----
frame_width = constraints.get("frameWidth")
frame_height = constraints.get("frameHeight")
⋮----
columns = info["width"] // frame_width
rows = info["height"] // frame_height
⋮----
def build_atlas_manifest(path: Path, manifest: dict) -> dict
⋮----
info = inspect_png(path)
constraints = manifest.get("constraints", {}) or {}
grid = sprite_grid(info, constraints)
frames = []
index = 0
⋮----
def validate_raster_file(path: Path, manifest: dict) -> tuple[dict, list[str]]
⋮----
target = manifest.get("target", {})
⋮----
max_colors = constraints.get("maxColors")
⋮----
expected_frames = constraints.get("expectedFrames")
⋮----
def select_tools(asset_type: str, registry: dict) -> list[dict]
⋮----
wanted = TOOL_DOMAINS.get(asset_type, set())
matches = []
⋮----
overlap = sorted(wanted & set(tool.get("domains", [])))
⋮----
status_rank = {"preferred": 0, "approved": 1, "candidate": 2}
⋮----
def build_plan(manifest: dict, root: Path) -> dict
⋮----
asset_type = manifest["type"]
pipeline_path = PIPELINES.get(asset_type)
source_mode = manifest["source"]["mode"]
importance = manifest["importance"]
⋮----
sourcing_policy = "review-external-or-replace-with-custom"
⋮----
sourcing_policy = "search-approved-assets-before-custom-creation"
⋮----
sourcing_policy = "follow-requested-source-mode"
⋮----
pipeline = load_json(root / pipeline_path) if pipeline_path else None
registry = load_json(root / "config/tooling.json")
⋮----
def load_valid_manifest(path: Path) -> tuple[dict | None, int]
⋮----
manifest = load_json(path)
⋮----
errors = validate_manifest(manifest)
⋮----
def cmd_validate(path: Path) -> int
⋮----
def cmd_plan(path: Path, root: Path) -> int
⋮----
def cmd_validate_raster(manifest_path: Path, asset_path: Path) -> int
⋮----
result = {"file": str(asset_path), "info": info, "errors": errors}
⋮----
def cmd_atlas_manifest(manifest_path: Path, asset_path: Path, output: Path | None) -> int
⋮----
atlas = build_atlas_manifest(asset_path, manifest)
⋮----
rendered = json.dumps(atlas, indent=2, sort_keys=True) + "\n"
⋮----
def parser() -> argparse.ArgumentParser
⋮----
result = argparse.ArgumentParser(prog="asset-forge")
sub = result.add_subparsers(dest="command", required=True)
⋮----
validate = sub.add_parser("validate", help="validate an asset manifest")
⋮----
plan = sub.add_parser("plan", help="build a deterministic asset production plan")
⋮----
raster = sub.add_parser("validate-raster", help="validate a PNG against an asset manifest")
⋮----
atlas = sub.add_parser("atlas-manifest", help="build uniform-grid atlas metadata from a PNG")
⋮----
def main() -> int
⋮----
args = parser().parse_args()
root = Path(__file__).resolve().parent
````

## File: README.md
````markdown
# asset-forge

Central visual-asset production pipeline for dbrckk projects.

## Mission

asset-forge standardizes how projects request, source, create, validate, optimize, license, and export professional visual assets.

Supported domains include 2D illustration, pixel-art sprites and tilesets, vector/SVG graphics, UI, textures and PBR materials, 3D meshes, rigs and animation, and engine-ready exports.

## Principles

1. Reuse a suitable licensed asset when it is visually secondary.
2. Create project-specific assets when identity, readability, consistency, or gameplay depends on them.
3. Prefer free/open-source tooling when it meets production requirements.
4. Never accept an asset with unknown or incompatible licensing.
5. Validate every generated or imported asset before integration.
6. Keep project art direction in the consuming project and reusable production logic here.

## Quick start

Validate a manifest:

```bash
python asset_forge.py validate examples/asset-manifest.json
```

Build its deterministic production plan:

```bash
python asset_forge.py plan examples/asset-manifest.json
```

Validate a PNG/sprite sheet against its manifest:

```bash
python asset_forge.py validate-raster examples/asset-manifest.json path/to/sprite.png
```

Generate uniform-grid atlas metadata:

```bash
python asset_forge.py atlas-manifest examples/asset-manifest.json path/to/sprite.png --output build/sprite.atlas.json
```

Run the offline test suite:

```bash
python -m unittest discover -s tests -v
```

## Current 2D validation

The dependency-free PNG validator checks:

- PNG signature, chunk boundaries, IEND presence, and chunk CRCs;
- dimensions and file-size budget;
- frame width/height divisibility;
- derived rows, columns, and frame count;
- expected frame count;
- alpha/transparency requirements;
- indexed-palette size when a PLTE chunk exists;
- power-of-two atlas dimensions when required;
- nearest-neighbor interpolation policy for pixel-art manifests.

`atlas-manifest` emits deterministic frame rectangles for uniform sprite sheets.

## Repository layout

```text
asset_forge.py
config/tooling.json
pipelines/
schemas/
examples/
tests/
.ai/project-state.md
```

## Discovery workflow

1. Read the consuming project's art direction and technical constraints.
2. Check the approved tool registry.
3. Query `dbrckk/star-list` for relevant capabilities.
4. If coverage is insufficient, discover candidates on GitHub/web.
5. Review licensing, maintenance, automation support, and output quality.
6. Create/source the asset.
7. Validate, optimize, record provenance, and export it for the target project.

Discovery is advisory: a newly discovered repository is never trusted automatically.

## Initial interoperability

- glTF/GLB for portable 3D delivery
- SVG for vector master assets
- PNG/WebP for raster delivery
- sprite sheets/atlases for 2D animation

The repository starts deliberately small. Tooling is added only after validation.
````
