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
  godot-animations.json
pipelines/
  model-3d.json
  sprite-2d.json
  vector-svg.json
profiles/
  3d/
    character.json
    environment.json
    prop.json
  vector/
    icon.json
    logo.json
    ui.json
schemas/
  asset-manifest.schema.json
tests/
  test_animation_infer.py
  test_asset_forge.py
  test_blender_adapter.py
  test_gltf_binary_metrics.py
  test_gltf_quality.py
  test_gltf_tools.py
  test_godot_export.py
  test_raster_pack.py
  test_starlist_bridge.py
  test_svg_tools.py
  test_toolchain_3d.py
AGENTS.md
animation_infer.py
asset_forge.py
blender_adapter.py
gltf_binary_metrics.py
gltf_quality.py
gltf_tools.py
godot_export.py
raster_pack.py
README.md
starlist_bridge.py
svg_tools.py
toolchain_3d.py
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
        run: python -m compileall -q asset_forge.py raster_pack.py godot_export.py starlist_bridge.py animation_infer.py svg_tools.py gltf_tools.py gltf_quality.py gltf_binary_metrics.py blender_adapter.py toolchain_3d.py tests
      - name: Unit tests
        run: python -m unittest discover -s tests -v
      - name: Validate example manifest
        run: python asset_forge.py validate examples/asset-manifest.json
      - name: Build example plan
        run: python asset_forge.py plan examples/asset-manifest.json
      - name: Inspect 3D toolchain
        run: python asset_forge.py 3d-toolchain-status
      - name: Checkout star-list
        uses: actions/checkout@v4
        with:
          repository: dbrckk/star-list
          path: star-list
      - name: Smoke-test star-list bridge
        run: python asset_forge.py discover-tools star-list "pixel art sprites atlas" --top 3
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

## File: examples/godot-animations.json
````json
{
  "animations": [
    {
      "name": "idle",
      "fps": 6,
      "loop": true,
      "frames": [0, 1]
    },
    {
      "name": "run",
      "fps": 12,
      "loop": true,
      "frames": [2, 3, 4, 5]
    },
    {
      "name": "attack",
      "fps": 14,
      "loop": false,
      "frames": [
        {"index": 6, "duration": 0.75},
        {"index": 7, "duration": 1.0},
        {"index": 8, "duration": 1.25}
      ]
    }
  ]
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

## File: pipelines/vector-svg.json
````json
{
  "id": "vector-svg",
  "assetTypes": ["vector", "svg", "icon", "ui-vector", "logo"],
  "stages": [
    "read-project-art-direction",
    "resolve-source-or-create",
    "validate-svg-xml",
    "reject-executable-content",
    "reject-external-references",
    "validate-viewbox-and-dimensions",
    "sanitize-svg",
    "optimize-vector-structure",
    "record-provenance-and-license",
    "validate-target-import"
  ],
  "defaults": {
    "masterFormat": "svg",
    "requireViewBox": true,
    "allowExternalReferences": false
  }
}
````

## File: profiles/3d/character.json
````json
{
  "id": "character",
  "assetTypes": [
    "character-3d"
  ],
  "rules": {
    "maxMeshes": 16,
    "maxPrimitives": 64,
    "maxMaterials": 16,
    "maxVertices": 150000,
    "maxTriangles": 200000,
    "maxTextures": 32,
    "allowAnimations": true,
    "requireSkin": true,
    "requireNormals": true,
    "requireUvWhenTextured": true,
    "maxTextureDimension": 4096,
    "maxEstimatedTextureMipBytes": 268435456,
    "maxJointsPerSkin": 128
  }
}
````

## File: profiles/3d/environment.json
````json
{
  "id": "environment",
  "assetTypes": [
    "environment"
  ],
  "rules": {
    "maxMeshes": 256,
    "maxPrimitives": 1024,
    "maxMaterials": 128,
    "maxVertices": 2000000,
    "maxTriangles": 2000000,
    "maxTextures": 256,
    "allowAnimations": false,
    "requireSkin": false,
    "requireNormals": true,
    "requireUvWhenTextured": true,
    "maxTextureDimension": 8192,
    "maxEstimatedTextureMipBytes": 1073741824,
    "maxJointsPerSkin": 0
  }
}
````

## File: profiles/3d/prop.json
````json
{
  "id": "prop",
  "assetTypes": [
    "prop",
    "mesh"
  ],
  "rules": {
    "maxMeshes": 8,
    "maxPrimitives": 16,
    "maxMaterials": 8,
    "maxVertices": 100000,
    "maxTriangles": 100000,
    "maxTextures": 16,
    "allowAnimations": false,
    "requireSkin": false,
    "requireNormals": true,
    "requireUvWhenTextured": true,
    "maxTextureDimension": 4096,
    "maxEstimatedTextureMipBytes": 134217728,
    "maxJointsPerSkin": 0
  }
}
````

## File: profiles/vector/icon.json
````json
{
  "id": "icon",
  "assetTypes": ["icon"],
  "rules": {
    "requireViewBox": true,
    "requireSquareViewBox": true,
    "maxElements": 256,
    "allowExternalReferences": false,
    "removeMetadata": true
  }
}
````

## File: profiles/vector/logo.json
````json
{
  "id": "logo",
  "assetTypes": ["logo"],
  "rules": {
    "requireViewBox": true,
    "requireSquareViewBox": false,
    "maxElements": 800,
    "allowExternalReferences": false,
    "removeMetadata": true
  }
}
````

## File: profiles/vector/ui.json
````json
{
  "id": "ui",
  "assetTypes": ["ui-vector", "vector"],
  "rules": {
    "requireViewBox": true,
    "requireSquareViewBox": false,
    "maxElements": 1200,
    "allowExternalReferences": false,
    "removeMetadata": true
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

## File: tests/test_animation_infer.py
````python
class AnimationInferTests(unittest.TestCase)
⋮----
def test_groups_numbered_filenames(self)
⋮----
metadata = {
⋮----
result = infer_animations(metadata, default_fps=8)
animations = {item["name"]: item for item in result["animations"]}
⋮----
def test_uses_stem_when_no_numeric_suffix(self)
⋮----
result = infer_animations(metadata)
⋮----
def test_missing_names_fall_back_to_default(self)
⋮----
result = infer_animations(metadata, default_loop=False)
⋮----
def test_rejects_invalid_fps(self)
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

## File: tests/test_blender_adapter.py
````python
class BlenderAdapterTests(unittest.TestCase)
⋮----
def test_build_export_job_defaults(self)
⋮----
job = build_blender_export_job(
⋮----
def test_selection_and_animation_flags(self)
⋮----
def test_rendered_script_opens_source_and_exports(self)
⋮----
script = render_blender_python(job)
⋮----
def test_render_command_uses_background_mode(self)
⋮----
command = render_blender_command("blender", Path("build/export.py"))
````

## File: tests/test_gltf_binary_metrics.py
````python
PNG_SIG = b"\x89PNG\r\n\x1a\n"
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
def tiny_png(width=2, height=4)
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
raw = b"".join(b"\x00" + (b"\x00\x00\x00\xff" * width) for _ in range(height))
⋮----
class GltfBinaryMetricsTests(unittest.TestCase)
⋮----
def test_data_uri_png_dimensions_and_memory(self)
⋮----
payload = tiny_png(2, 4)
uri = "data:image/png;base64," + base64.b64encode(payload).decode("ascii")
data = {
⋮----
path = Path(tmp) / "asset.gltf"
⋮----
items = inspect_images(path)
⋮----
def test_local_external_png_dimensions(self)
⋮----
root = Path(tmp)
⋮----
path = root / "asset.gltf"
⋮----
def test_animation_and_rig_metrics(self)
⋮----
metrics = inspect_rig_and_animation(path)
⋮----
def test_quality_report_includes_binary_metrics(self)
⋮----
payload = tiny_png(4, 4)
⋮----
report = quality_report(path, "prop")
````

## File: tests/test_gltf_quality.py
````python
class GltfQualityTests(unittest.TestCase)
⋮----
def write(self, root: Path, data: dict) -> Path
⋮----
path = root / "asset.gltf"
⋮----
def base(self)
⋮----
def test_counts_vertices_and_triangles(self)
⋮----
report = build_quality_report(self.write(Path(tmp), self.base()))
⋮----
def test_triangle_strip_count(self)
⋮----
data = self.base()
⋮----
report = build_quality_report(self.write(Path(tmp), data))
⋮----
def test_character_quality_requires_skin_attributes(self)
⋮----
evaluation = evaluate_quality(report, "character")
⋮----
def test_textured_primitive_requires_uv(self)
⋮----
report = quality_report(self.write(Path(tmp), data), "prop")
⋮----
def test_normal_map_without_tangent_warns(self)
⋮----
def test_external_image_is_reported(self)
⋮----
report = quality_report(self.write(Path(tmp), self.base()), "prop")
⋮----
def test_untextured_primitive_does_not_require_uv(self)
````

## File: tests/test_gltf_tools.py
````python
def make_glb(data: dict) -> bytes
⋮----
payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
padding = (4 - (len(payload) % 4)) % 4
⋮----
total = 12 + 8 + len(payload)
⋮----
class GltfToolsTests(unittest.TestCase)
⋮----
def base(self)
⋮----
def test_valid_gltf(self)
⋮----
path = Path(tmp) / "asset.gltf"
⋮----
def test_invalid_version(self)
⋮----
data = self.base()
⋮----
def test_glb_json_chunk(self)
⋮----
path = Path(tmp) / "asset.glb"
⋮----
def test_character_requires_skin(self)
⋮----
path = Path(tmp) / "character.gltf"
⋮----
def test_character_with_skin_passes(self)
⋮----
def test_out_of_range_mesh_reference_is_rejected(self)
⋮----
path = Path(tmp) / "bad.gltf"
⋮----
def test_out_of_range_accessor_reference_is_rejected(self)
⋮----
def test_valid_skin_joint_reference_passes(self)
⋮----
path = Path(tmp) / "skin.gltf"
````

## File: tests/test_godot_export.py
````python
class GodotExportTests(unittest.TestCase)
⋮----
def metadata(self)
⋮----
def test_render_spriteframes_uses_atlas_regions(self)
⋮----
rendered = render_spriteframes(
⋮----
def test_multiple_animations(self)
⋮----
def test_rejects_duplicate_animation_names(self)
⋮----
def test_rejects_out_of_range_animation_frame(self)
⋮----
def test_write_spriteframes_creates_file(self)
⋮----
output = Path(tmp) / "player.tres"
⋮----
rendered = output.read_text(encoding="utf-8")
⋮----
def test_rejects_empty_metadata(self)
⋮----
def test_rejects_invalid_fps(self)
````

## File: tests/test_raster_pack.py
````python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
def write_rgba_png(path: Path, width: int, height: int, pixel: bytes) -> None
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
row = pixel * width
raw = b"".join(b"\x00" + row for _ in range(height))
⋮----
class RasterPackTests(unittest.TestCase)
⋮----
def test_pack_uniform_atlas_writes_png_and_metadata(self)
⋮----
root = Path(tmp)
red = root / "red.png"
green = root / "green.png"
atlas = root / "atlas.png"
⋮----
metadata = pack_uniform_atlas(
⋮----
def test_pack_rejects_mixed_frame_sizes(self)
⋮----
first = root / "a.png"
second = root / "b.png"
⋮----
def test_rgb_png_is_promoted_to_opaque_rgba(self)
⋮----
image = root / "rgb.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
raw = b"\x00" + bytes([7, 8, 9])
⋮----
def test_recompress_png_preserves_pixels(self)
⋮----
source = root / "source.png"
optimized = root / "optimized.png"
⋮----
before = decode_rgba(source)
report = recompress_png(source, optimized)
after = decode_rgba(optimized)
output_exists = optimized.exists()
⋮----
def test_recompress_png_reports_sizes(self)
⋮----
def test_grayscale_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "gray.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
⋮----
def test_grayscale_alpha_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "gray-alpha.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 4, 0, 0, 0)
⋮----
def test_indexed_png_with_transparency_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "indexed.png"
ihdr = struct.pack(">IIBBBBB", 2, 1, 8, 3, 0, 0, 0)
palette = bytes([255, 0, 0, 0, 255, 0])
transparency = bytes([255, 64])
````

## File: tests/test_starlist_bridge.py
````python
FAKE_RECOMMENDER = r'''#!/usr/bin/env python3
⋮----
class StarListBridgeTests(unittest.TestCase)
⋮----
def make_fake_star_list(self, root: Path) -> None
⋮----
scripts = root / "scripts"
⋮----
def test_run_recommender_parses_json(self)
⋮----
root = Path(tmp)
⋮----
result = run_starlist_recommender(root, "pixel art sprites", top=3)
⋮----
def test_full_report_runs_visual_queries(self)
⋮----
report = build_visual_discovery_report(root)
⋮----
def test_missing_recommender_is_rejected(self)
````

## File: tests/test_svg_tools.py
````python
class SvgToolsTests(unittest.TestCase)
⋮----
def test_valid_svg_passes(self)
⋮----
path = Path(tmp) / "icon.svg"
⋮----
def test_missing_viewbox_warns(self)
⋮----
def test_script_and_events_are_rejected(self)
⋮----
path = Path(tmp) / "bad.svg"
⋮----
def test_external_href_is_rejected(self)
⋮----
def test_sanitize_removes_dangerous_content(self)
⋮----
source = Path(tmp) / "source.svg"
output = Path(tmp) / "clean.svg"
⋮----
report = sanitize_svg(source, output)
⋮----
rendered = output.read_text(encoding="utf-8")
⋮----
def test_icon_profile_requires_square_viewbox(self)
⋮----
def test_ui_profile_accepts_non_square_viewbox(self)
⋮----
path = Path(tmp) / "ui.svg"
⋮----
def test_aspect_ratio_mismatch_warns(self)
⋮----
path = Path(tmp) / "mismatch.svg"
⋮----
def test_normalize_viewbox_from_dimensions(self)
⋮----
output = Path(tmp) / "normalized.svg"
⋮----
report = normalize_viewbox(source, output)
⋮----
def test_sanitize_removes_metadata(self)
````

## File: tests/test_toolchain_3d.py
````python
class Toolchain3DTests(unittest.TestCase)
⋮----
def test_command_builders(self)
⋮----
command = gltfpack_command(
⋮----
@patch("toolchain_3d.shutil.which")
    def test_detect_tools(self, which)
⋮----
tools = detect_3d_tools()
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_pipeline_contains_export_validate_optimize_validate(self, detect)
⋮----
plan = build_3d_pipeline(
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_none_optimizer_keeps_raw_output(self, detect)
⋮----
def test_invalid_optimizer_is_rejected(self)
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_missing_optimizer_falls_back_to_raw_output(self, detect)
⋮----
validation_steps = [
⋮----
@patch("toolchain_3d.execute_command")
@patch("toolchain_3d.prepare_3d_pipeline")
    def test_execute_pipeline_skips_unavailable_optional_tools(self, prepare, execute)
⋮----
plan = {
⋮----
result = execute_3d_pipeline(plan, Path("."))
⋮----
@patch("toolchain_3d.execute_command")
@patch("toolchain_3d.prepare_3d_pipeline")
    def test_execute_pipeline_stops_on_required_failure(self, prepare, execute)
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

## File: animation_infer.py
````python
FRAME_SUFFIX = re.compile(r"^(?P<name>.+?)(?:[_\-. ]?)(?P<number>\d+)$")
⋮----
frames = atlas_metadata.get("frames")
⋮----
groups: dict[str, list[tuple[int, int]]] = {}
⋮----
index = frame.get("index", fallback_index)
⋮----
raw_name = frame.get("name")
⋮----
animation_name = "default"
order = index
⋮----
stem = raw_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
⋮----
stem = stem.rsplit(".", 1)[0]
⋮----
match = FRAME_SUFFIX.match(stem)
⋮----
animation_name = match.group("name").rstrip("_-. ").strip() or "default"
order = int(match.group("number"))
⋮----
animation_name = stem.strip() or "default"
⋮----
animations = []
⋮----
ordered = sorted(groups[name], key=lambda item: (item[0], item[1]))
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
pack = sub.add_parser("pack-atlas", help="pack equal-size RGB/RGBA PNG frames into an atlas")
⋮----
optimize = sub.add_parser("optimize-png", help="losslessly recompress a supported PNG")
⋮----
godot = sub.add_parser("export-godot", help="export Godot 4 SpriteFrames .tres from atlas metadata")
⋮----
discover = sub.add_parser("discover-tools", help="query dbrckk/star-list for visual tooling")
⋮----
infer = sub.add_parser("infer-animations", help="infer animation groups from atlas frame filenames")
⋮----
svg_validate = sub.add_parser("validate-svg", help="validate an SVG for safe project use")
⋮----
svg_sanitize = sub.add_parser("sanitize-svg", help="remove unsafe SVG content")
⋮----
svg_normalize = sub.add_parser("normalize-svg", help="ensure SVG has a usable viewBox")
⋮----
gltf_validate = sub.add_parser("validate-gltf", help="validate glTF/GLB structure")
⋮----
gltf_quality = sub.add_parser("quality-gltf", help="measure glTF/GLB production quality")
⋮----
blender_job = sub.add_parser("blender-export-job", help="create a reproducible Blender GLB export job")
⋮----
toolchain_status = sub.add_parser("3d-toolchain-status", help="detect available external 3D tools")
⋮----
pipeline3d = sub.add_parser("prepare-3d", help="prepare Blender to GLB validation/optimization pipeline")
⋮----
run3d = sub.add_parser("run-3d", help="run Blender to GLB validation/optimization pipeline")
⋮----
def main() -> int
⋮----
args = parser().parse_args()
root = Path(__file__).resolve().parent
⋮----
metadata = pack_uniform_atlas(
⋮----
rendered = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
⋮----
result = recompress_png(args.input, args.output)
⋮----
metadata = load_json(args.metadata)
animations = None
⋮----
animation_config = load_json(args.animations)
animations = animation_config.get("animations")
⋮----
result = build_visual_discovery_report(args.star_list_root)
⋮----
result = run_starlist_recommender(
⋮----
rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
⋮----
result = infer_animations(
⋮----
result = {"file": str(args.input), "info": info, "errors": errors, "warnings": warnings}
⋮----
result = sanitize_svg(args.input, args.output)
⋮----
result = normalize_viewbox(args.input, args.output)
⋮----
result = quality_report(args.input, args.profile)
⋮----
evaluation = result.get("evaluation")
⋮----
job = build_blender_export_job(
⋮----
result = {
⋮----
plan = build_3d_pipeline(
⋮----
result = execute_3d_pipeline(plan, root)
````

## File: blender_adapter.py
````python
DEFAULT_EXPORT_SETTINGS = {
⋮----
settings = dict(DEFAULT_EXPORT_SETTINGS)
⋮----
def render_blender_python(job: dict) -> str
⋮----
source = job["source"]
output = job["output"]
settings = job["settings"]
⋮----
def write_blender_export_script(job: dict, output_script: Path) -> None
⋮----
def render_blender_command(blender_executable: str, script_path: Path) -> str
⋮----
def write_job_manifest(job: dict, path: Path) -> None
````

## File: gltf_binary_metrics.py
````python
def _decode_data_uri(uri: str) -> bytes
⋮----
def _safe_local_path(model_path: Path, uri: str) -> Path
⋮----
base = model_path.resolve().parent
candidate = (base / unquote(uri)).resolve()
⋮----
def _glb_bin_chunk(path: Path) -> bytes | None
⋮----
raw = path.read_bytes()
⋮----
offset = 12
⋮----
end = offset + chunk_length
⋮----
payload = raw[offset:end]
offset = end
⋮----
def load_buffer_payloads(path: Path, data: dict) -> list[bytes | None]
⋮----
buffers = data.get("buffers", [])
⋮----
glb_bin = _glb_bin_chunk(path) if path.suffix.lower() == ".glb" else None
payloads: list[bytes | None] = []
⋮----
uri = buffer.get("uri")
⋮----
payload = _decode_data_uri(uri)
⋮----
payload = _safe_local_path(path, uri).read_bytes()
⋮----
payload = glb_bin
⋮----
payload = None
⋮----
views = data.get("bufferViews", [])
⋮----
view = views[view_index]
⋮----
buffer_index = view.get("buffer")
⋮----
payload = payloads[buffer_index]
⋮----
offset = view.get("byteOffset", 0)
length = view.get("byteLength")
⋮----
end = offset + length
⋮----
def _png_dimensions(data: bytes) -> tuple[int, int] | None
⋮----
def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None
⋮----
offset = 2
⋮----
marker = data[offset + 1]
⋮----
length = struct.unpack(">H", data[offset : offset + 2])[0]
⋮----
def _webp_dimensions(data: bytes) -> tuple[int, int] | None
⋮----
kind = data[12:16]
⋮----
width = 1 + int.from_bytes(data[24:27], "little")
height = 1 + int.from_bytes(data[27:30], "little")
⋮----
bits = int.from_bytes(data[21:25], "little")
width = (bits & 0x3FFF) + 1
height = ((bits >> 14) & 0x3FFF) + 1
⋮----
def image_dimensions(data: bytes) -> tuple[int, int, str] | None
⋮----
dimensions = parser(data)
⋮----
def inspect_images(path: Path) -> list[dict]
⋮----
images = data.get("images", [])
⋮----
payloads = load_buffer_payloads(path, data)
result = []
⋮----
item = {
⋮----
uri = image.get("uri")
⋮----
payload = buffer_view_bytes(data, payloads, image["bufferView"])
⋮----
dimensions = image_dimensions(payload)
⋮----
rgba = width * height * 4
⋮----
def inspect_rig_and_animation(path: Path) -> dict
⋮----
skins = data.get("skins", [])
animations = data.get("animations", [])
accessors = data.get("accessors", [])
⋮----
skins = []
⋮----
animations = []
⋮----
accessors = []
⋮----
joint_counts = []
inverse_bind_matrices = 0
⋮----
joints = skin.get("joints", [])
⋮----
channels = 0
samplers = 0
target_paths: dict[str, int] = {}
animated_nodes: set[int] = set()
keyframe_counts = []
invalid_targets = 0
⋮----
animation_samplers = animation.get("samplers", [])
animation_channels = animation.get("channels", [])
⋮----
input_index = sampler.get("input")
⋮----
accessor = accessors[input_index]
⋮----
target = channel.get("target")
⋮----
node = target.get("node")
path_name = target.get("path")
````

## File: gltf_quality.py
````python
QUALITY_PROFILES = {
⋮----
def _accessor_count(accessors: list, index) -> int | None
⋮----
accessor = accessors[index]
⋮----
count = accessor.get("count")
⋮----
def _triangle_count(mode: int, element_count: int) -> int
⋮----
if mode == 4:  # TRIANGLES
⋮----
if mode in {5, 6}:  # TRIANGLE_STRIP / TRIANGLE_FAN
⋮----
def build_quality_report(path: Path) -> dict
⋮----
accessors = data.get("accessors", [])
meshes = data.get("meshes", [])
materials = data.get("materials", [])
textures = data.get("textures", [])
images = data.get("images", [])
⋮----
accessors = []
⋮----
meshes = []
⋮----
materials = []
⋮----
textures = []
⋮----
images = []
⋮----
material_usage = []
⋮----
pbr = material.get("pbrMetallicRoughness")
textured = False
⋮----
textured = any(
normal_mapped = isinstance(material.get("normalTexture"), dict)
textured = textured or normal_mapped or isinstance(material.get("occlusionTexture"), dict) or isinstance(material.get("emissiveTexture"), dict)
⋮----
primitives = 0
vertices = 0
triangles = 0
primitive_vertices_known = 0
primitive_triangles_known = 0
normals = 0
tangents = 0
uv0 = 0
uv1 = 0
colors = 0
skinned = 0
material_bound = 0
textured_primitives = 0
textured_primitives_with_uv0 = 0
normal_mapped_primitives = 0
normal_mapped_primitives_with_tangent = 0
non_triangle_primitives = 0
⋮----
mesh_primitives = mesh.get("primitives", [])
⋮----
attributes = primitive.get("attributes", {})
⋮----
attributes = {}
⋮----
position_count = _accessor_count(accessors, attributes.get("POSITION"))
⋮----
mode = primitive.get("mode", 4)
⋮----
mode = 4
⋮----
element_count = None
⋮----
element_count = _accessor_count(accessors, primitive.get("indices"))
⋮----
element_count = position_count
⋮----
material_index = primitive.get("material")
⋮----
usage = material_usage[material_index]
⋮----
pbr_materials = 0
base_color_textures = 0
metallic_roughness_textures = 0
normal_textures = 0
occlusion_textures = 0
emissive_textures = 0
⋮----
external_images = 0
embedded_images = 0
data_uri_images = 0
⋮----
uri = image.get("uri")
⋮----
image_metrics = inspect_images(path)
rig_animation = inspect_rig_and_animation(path)
known_image_dimensions = [item for item in image_metrics if item.get("width") and item.get("height")]
estimated_texture_bytes = sum(
estimated_texture_mip_bytes = sum(
max_texture_width = max((int(item["width"]) for item in known_image_dimensions), default=0)
max_texture_height = max((int(item["height"]) for item in known_image_dimensions), default=0)
⋮----
def evaluate_quality(report: dict, profile: str) -> dict
⋮----
rules = QUALITY_PROFILES[profile]
geometry = report["geometry"]
attributes = report["attributes"]
materials = report["materials"]
textures = report["textures"]
⋮----
errors: list[str] = []
warnings: list[str] = []
primitive_count = geometry["primitives"]
⋮----
rig = report.get("rigAnimation", {})
⋮----
def quality_report(path: Path, profile: str | None = None) -> dict
⋮----
report = build_quality_report(path)
````

## File: gltf_tools.py
````python
GLB_MAGIC = 0x46546C67
GLB_JSON_CHUNK = 0x4E4F534A
GLB_BIN_CHUNK = 0x004E4942
⋮----
def load_gltf_json(path: Path) -> tuple[dict, dict]
⋮----
suffix = path.suffix.lower()
⋮----
data = json.loads(path.read_text(encoding="utf-8"))
⋮----
raw = path.read_bytes()
⋮----
offset = 12
json_chunk = None
bin_bytes = 0
chunk_count = 0
⋮----
end = offset + chunk_length
⋮----
payload = raw[offset:end]
offset = end
⋮----
json_chunk = payload
⋮----
data = json.loads(json_chunk.decode("utf-8").rstrip(" \t\r\n\x00"))
⋮----
def _count_primitives(data: dict) -> tuple[int, int]
⋮----
meshes = data.get("meshes", [])
⋮----
primitive_count = 0
indexed_primitive_count = 0
⋮----
primitives = mesh.get("primitives", [])
⋮----
def _validate_index_references(data: dict) -> list[str]
⋮----
errors: list[str] = []
nodes = data.get("nodes", [])
⋮----
materials = data.get("materials", [])
accessors = data.get("accessors", [])
buffer_views = data.get("bufferViews", [])
buffers = data.get("buffers", [])
textures = data.get("textures", [])
images = data.get("images", [])
samplers = data.get("samplers", [])
skins = data.get("skins", [])
⋮----
def check(value, size, label)
⋮----
children = node.get("children", [])
⋮----
attributes = primitive.get("attributes", {})
⋮----
joints = skin.get("joints", [])
⋮----
def inspect_gltf(path: Path) -> tuple[dict, list[str], list[str]]
⋮----
warnings: list[str] = []
⋮----
asset = data.get("asset")
⋮----
version = None
⋮----
version = asset.get("version")
⋮----
scenes = data.get("scenes", [])
⋮----
animations = data.get("animations", [])
⋮----
extensions_used = data.get("extensionsUsed", [])
extensions_required = data.get("extensionsRequired", [])
⋮----
unknown_required = [
⋮----
info = {
⋮----
PROFILES = {
⋮----
def validate_gltf_profile(path: Path, profile: str) -> tuple[dict, list[str], list[str]]
⋮----
rules = PROFILES[profile]
````

## File: godot_export.py
````python
def _godot_string(value: str) -> str
⋮----
def _validate_frames(atlas_metadata: dict) -> list[dict]
⋮----
frames = atlas_metadata.get("frames")
⋮----
normalized = []
⋮----
x = int(frame["x"])
y = int(frame["y"])
width = int(frame["width"])
height = int(frame["height"])
⋮----
seen_names: set[str] = set()
⋮----
name = animation.get("name")
⋮----
speed = animation.get("fps", fps)
⋮----
raw_frames = animation.get("frames")
⋮----
animation_frames = []
⋮----
frame_index = raw
duration = 1.0
⋮----
frame_index = int(raw["index"])
⋮----
duration = raw.get("duration", 1.0)
⋮----
duration = float(duration)
⋮----
"""Render a Godot 4 SpriteFrames .tres backed by AtlasTexture regions."""
frames = _validate_frames(atlas_metadata)
animation_defs = _normalize_animations(
⋮----
lines = [
⋮----
resource_ids: list[str] = []
⋮----
index = frame["index"]
resource_id = f"AtlasTexture_{index}"
⋮----
rendered_animations = []
⋮----
frame_lines = []
⋮----
resource_id = resource_ids[frame["index"]]
⋮----
rendered = render_spriteframes(
````

## File: raster_pack.py
````python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
⋮----
def _chunks(data: bytes) -> list[tuple[bytes, bytes]]
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
def _paeth(a: int, b: int, c: int) -> int
⋮----
prediction = a + b - c
pa = abs(prediction - a)
pb = abs(prediction - b)
pc = abs(prediction - c)
⋮----
def _unfilter_scanlines(raw: bytes, width: int, height: int, bpp: int) -> list[bytearray]
⋮----
stride = width * bpp
⋮----
rows: list[bytearray] = []
previous = bytearray(stride)
position = 0
⋮----
filter_type = raw[position]
⋮----
scanline = bytearray(raw[position : position + stride])
⋮----
reconstructed = bytearray(stride)
⋮----
left = reconstructed[index - bpp] if index >= bpp else 0
above = previous[index]
upper_left = previous[index - bpp] if index >= bpp else 0
⋮----
reconstructed_value = value
⋮----
reconstructed_value = (value + left) & 255
⋮----
reconstructed_value = (value + above) & 255
⋮----
reconstructed_value = (value + ((left + above) // 2)) & 255
⋮----
reconstructed_value = (value + _paeth(left, above, upper_left)) & 255
⋮----
previous = reconstructed
⋮----
def decode_rgba(path: Path) -> tuple[int, int, bytes]
⋮----
chunks = _chunks(path.read_bytes())
⋮----
bpp_by_type = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
bpp = bpp_by_type[color_type]
raw = zlib.decompress(b"".join(payload for kind, payload in chunks if kind == b"IDAT"))
rows = _unfilter_scanlines(raw, width, height, bpp)
⋮----
palette: list[tuple[int, int, int]] = []
transparency = b""
⋮----
palette = [
⋮----
transparency = payload
⋮----
rgba = bytearray(width * height * 4)
destination = 0
⋮----
gray = row[index]
red = green = blue = gray
alpha = 255
⋮----
transparent_gray = struct.unpack(">H", transparency[:2])[0] & 0xFF
⋮----
alpha = 0
⋮----
palette_index = row[index]
⋮----
alpha = transparency[palette_index] if palette_index < len(transparency) else 255
⋮----
def _chunk(kind: bytes, payload: bytes) -> bytes
⋮----
def _filter_row(row: bytes, previous: bytes, bpp: int, filter_type: int) -> bytes
⋮----
output = bytearray(len(row))
⋮----
left = row[index - bpp] if index >= bpp else 0
⋮----
predictor = 0
⋮----
predictor = left
⋮----
predictor = above
⋮----
predictor = (left + above) // 2
⋮----
predictor = _paeth(left, above, upper_left)
⋮----
def _filter_score(filtered: bytes) -> int
⋮----
def _png_bytes_rgba(width: int, height: int, pixels: bytes, adaptive: bool = True) -> bytes
⋮----
rows: list[bytes] = []
previous = bytes(width * 4)
⋮----
start = y * width * 4
row = pixels[start : start + width * 4]
⋮----
candidates = [
⋮----
filter_type = 0
filtered = row
⋮----
previous = row
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
⋮----
def recompress_png(input_path: Path, output_path: Path) -> dict
⋮----
before = input_path.stat().st_size
⋮----
after = output_path.stat().st_size
⋮----
def _next_power_of_two(value: int) -> int
⋮----
decoded = [decode_rgba(Path(path)) for path in inputs]
⋮----
frame_count = len(decoded)
column_count = columns or math.ceil(math.sqrt(frame_count))
⋮----
row_count = math.ceil(frame_count / column_count)
content_width = column_count * frame_width + max(0, column_count - 1) * padding
content_height = row_count * frame_height + max(0, row_count - 1) * padding
⋮----
atlas_width = _next_power_of_two(content_width) if power_of_two else content_width
atlas_height = _next_power_of_two(content_height) if power_of_two else content_height
⋮----
canvas = bytearray(atlas_width * atlas_height * 4)
frames = []
⋮----
column = index % column_count
row = index // column_count
x = column * (frame_width + padding)
y = row * (frame_height + padding)
⋮----
source_start = source_y * frame_width * 4
destination_start = ((y + source_y) * atlas_width + x) * 4
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

Pack separate equal-size PNG frames into a real atlas image plus metadata:

```bash
python asset_forge.py pack-atlas build/atlas.png frames/*.png --metadata build/atlas.json --padding 1 --power-of-two
```

Losslessly recompress a supported PNG:

```bash
python asset_forge.py optimize-png build/atlas.png build/atlas.optimized.png
```

Export atlas metadata as a Godot 4 SpriteFrames resource:

```bash
python asset_forge.py export-godot build/atlas.json build/player.tres --atlas-path res://art/atlas.png --animation run --fps 12
```

Infer animation groups automatically from filenames such as `idle_01.png`, `idle_02.png`, `run_01.png`:

```bash
python asset_forge.py infer-animations build/atlas.json --fps 12 --output build/animations.json
```

Export several animations from the same atlas:

```bash
python asset_forge.py export-godot build/atlas.json build/player.tres \
  --atlas-path res://art/atlas.png \
  --animations build/animations.json
```

The animation config can define per-animation FPS, loop behavior, frame order, and optional per-frame duration multipliers. A versioned example is available at `examples/godot-animations.json`.

The built-in packer currently supports non-interlaced 8-bit RGB/RGBA PNG inputs and implements all five standard PNG scanline filters. It writes an RGBA PNG atlas without external image libraries. The optimizer uses adaptive per-row PNG filtering and zlib level 9 while preserving decoded pixels.

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

Run a targeted star-list query against a local checkout:

```bash
python asset_forge.py discover-tools ../star-list "pixel art sprites atlas" --top 8
```

Generate the standard visual tooling discovery report:

```bash
python asset_forge.py discover-tools ../star-list --full-report --output build/visual-tools.json
```

The bridge invokes star-list's own recommender and consumes its JSON result instead of maintaining a second ranking implementation.

Discovery is advisory: a newly discovered repository is never trusted automatically.

## SVG/vector workflow

Validate an SVG before it enters a project:

```bash
python asset_forge.py validate-svg path/to/icon.svg
```

Create a sanitized copy that removes executable/unsafe SVG content, editor metadata, and external references:

```bash
python asset_forge.py sanitize-svg path/to/icon.svg build/icon.safe.svg
```

Normalize a missing viewBox from positive numeric width/height values:

```bash
python asset_forge.py normalize-svg source.svg build/source.normalized.svg
```

Apply a production profile:

```bash
python asset_forge.py validate-svg icon.svg --profile icon
python asset_forge.py validate-svg hud.svg --profile ui
python asset_forge.py validate-svg brand.svg --profile logo
```

The current vector validator checks XML validity, SVG root type, viewBox shape, width/height consistency, scripts/foreignObject, event-handler attributes, external href/src references, editor metadata, and profile-specific complexity/shape rules. Versioned profile descriptions live under `profiles/vector/`.

## 3D / Blender workflow

Validate glTF/GLB structure:

```bash
python asset_forge.py validate-gltf model.glb
```

Apply a 3D structural profile:

```bash
python asset_forge.py validate-gltf prop.glb --profile prop
python asset_forge.py validate-gltf level.glb --profile environment
python asset_forge.py validate-gltf character.glb --profile character
```

Measure production quality and budgets:

```bash
python asset_forge.py quality-gltf prop.glb --profile prop --output build/prop-quality.json
```

The quality report derives vertex and triangle counts from accessor metadata, measures primitive coverage for normals/UVs/tangents/skinning, summarizes PBR texture usage, identifies external images, and evaluates the versioned profile budgets under `profiles/3d/`.

When image bytes are locally available, the report also reads PNG/JPEG/WebP dimensions and estimates decoded RGBA8 texture memory with mipmaps. Remote URLs are not fetched. Rig/animation metrics include joints per skin, inverse bind matrices, animation channels/samplers, target paths, animated nodes, and keyframe accessor counts.

Create a reproducible Blender export job and script:

```bash
python asset_forge.py blender-export-job source.blend build/model.glb \
  --script build/export_blender.py \
  --job-manifest build/export_job.json
```

Inspect external 3D tool availability:

```bash
python asset_forge.py 3d-toolchain-status
```

Prepare a complete production pipeline:

```bash
python asset_forge.py prepare-3d source.blend build/model \
  --profile prop \
  --optimizer gltf-transform \
  --texture-compress webp
```

Run it end to end when the required local tools are available:

```bash
python asset_forge.py run-3d source.blend build/model \
  --profile prop \
  --optimizer gltf-transform
```

The generated chain is Blender export → internal structural validation → quality/budget report → optional Khronos validation → optional optimization → post-optimization structural validation → final quality report. If an optional optimizer is unavailable, the pipeline keeps the validated raw GLB as the final output instead of pointing to a file that was never generated.

A completed run also writes `production-report.json`, which records step status and compares raw vs final vertices, triangles, and file bytes when both quality reports are available.

## Initial interoperability

- glTF/GLB for portable 3D delivery
- SVG for vector master assets
- PNG/WebP for raster delivery
- sprite sheets/atlases for 2D animation

The repository starts deliberately small. Tooling is added only after validation.
````

## File: starlist_bridge.py
````python
"""Run dbrckk/star-list's recommender without duplicating its ranking logic."""
script = star_list_root / "scripts" / "recommend.py"
⋮----
command = [
⋮----
completed = subprocess.run(
⋮----
detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
⋮----
result = json.loads(completed.stdout)
⋮----
recommendations = result.get("recommendations")
⋮----
def build_visual_discovery_report(star_list_root: Path) -> dict
⋮----
tasks = {
⋮----
report = {
⋮----
result = run_starlist_recommender(
````

## File: svg_tools.py
````python
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
DANGEROUS_TAGS = {"script", "foreignObject"}
METADATA_TAGS = {"metadata"}
EVENT_ATTRIBUTE = re.compile(r"^on[a-z]+$", re.IGNORECASE)
LENGTH = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)(px)?\s*$", re.IGNORECASE)
⋮----
PROFILES = {
⋮----
def _local_name(name: str) -> str
⋮----
def _is_external_reference(value: str) -> bool
⋮----
value = value.strip()
⋮----
parsed = urlparse(value)
⋮----
def _parse_length(value: str | None) -> float | None
⋮----
match = LENGTH.match(value)
⋮----
def _parse_viewbox(view_box: str | None) -> tuple[float, float, float, float] | None
⋮----
parts = view_box.replace(",", " ").split()
⋮----
values = tuple(float(item) for item in parts)
⋮----
return values  # type: ignore[return-value]
⋮----
def inspect_svg(path: Path) -> tuple[dict, list[str], list[str]]
⋮----
raw = path.read_text(encoding="utf-8")
errors: list[str] = []
warnings: list[str] = []
⋮----
lowered = raw.lower()
⋮----
root = ET.fromstring(raw)
⋮----
width = root.attrib.get("width")
height = root.attrib.get("height")
view_box = root.attrib.get("viewBox")
view_box_values = _parse_viewbox(view_box)
⋮----
width_value = _parse_length(width)
height_value = _parse_length(height)
⋮----
pixel_ratio = width_value / height_value if height_value else None
view_ratio = view_box_values[2] / view_box_values[3] if view_box_values[3] else None
⋮----
element_count = 0
external_refs: list[str] = []
dangerous_tags: list[str] = []
event_attributes: list[str] = []
metadata_elements = 0
⋮----
tag = _local_name(element.tag)
⋮----
local_key = _local_name(key)
⋮----
info = {
⋮----
def validate_svg_profile(path: Path, profile: str) -> tuple[dict, list[str], list[str]]
⋮----
rules = PROFILES[profile]
view_box_values = info.get("viewBoxValues")
⋮----
def normalize_viewbox(input_path: Path, output_path: Path) -> dict
⋮----
raw = input_path.read_text(encoding="utf-8")
⋮----
current = _parse_viewbox(root.attrib.get("viewBox"))
changed = False
⋮----
width = _parse_length(root.attrib.get("width"))
height = _parse_length(root.attrib.get("height"))
⋮----
changed = True
⋮----
removed_elements = 0
removed_attributes = 0
⋮----
def clean(parent: ET.Element) -> None
⋮----
local_tag = _local_name(child.tag)
⋮----
value = child.attrib[key]
⋮----
value = root.attrib[key]
````

## File: toolchain_3d.py
````python
def detect_3d_tools() -> dict
⋮----
candidates = {
result = {}
⋮----
found = None
⋮----
path = shutil.which(name)
⋮----
found = path
⋮----
def _quote(parts: list[str]) -> str
⋮----
def validator_command(executable: str, input_path: Path) -> str
⋮----
parts = [executable, "optimize", str(input_path), str(output_path)]
⋮----
parts = [executable, "-i", str(input_path), "-o", str(output_path)]
⋮----
workdir = Path(workdir)
raw_glb = workdir / "raw.glb"
optimized_glb = workdir / "optimized.glb"
blender_script = workdir / "export_blender.py"
⋮----
blender_job = build_blender_export_job(
⋮----
tools = detect_3d_tools()
commands = []
⋮----
validator = tools["gltf-validator"]
⋮----
final_glb = raw_glb
optimizer_available = False
⋮----
tool = tools["gltf-transform"]
optimizer_available = bool(tool["available"])
⋮----
final_glb = optimized_glb
⋮----
tool = tools["gltfpack"]
⋮----
def prepare_3d_pipeline(plan: dict) -> None
⋮----
workdir = Path(plan["workdir"])
⋮----
def execute_command(command: str, cwd: Path | None = None) -> dict
⋮----
completed = subprocess.run(
⋮----
def _read_json_if_exists(path: Path) -> dict | None
⋮----
data = json.loads(path.read_text(encoding="utf-8"))
⋮----
def _build_production_summary(plan: dict, success: bool, results: list[dict]) -> dict
⋮----
raw_report = _read_json_if_exists(workdir / "quality-raw.json")
final_report = _read_json_if_exists(workdir / "quality-final.json") or raw_report
⋮----
summary = {
⋮----
raw_geometry = raw_report.get("geometry", {})
final_geometry = final_report.get("geometry", {})
raw_container = raw_report.get("container", {})
final_container = final_report.get("container", {})
⋮----
def execute_3d_pipeline(plan: dict, repo_root: Path) -> dict
⋮----
results = []
success = True
⋮----
result = {
⋮----
success = False
⋮----
executed = execute_command(step["command"], cwd=repo_root)
⋮----
report_path = Path(step["output"])
⋮----
summary = _build_production_summary(plan, success, results)
report_path = Path(plan["workdir"]) / "production-report.json"
````
