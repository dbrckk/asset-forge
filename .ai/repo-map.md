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
    ai-repo-map.yml
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
  godot4/
    character.json
    environment.json
    prop.json
  vector/
    icon.json
    logo.json
    ui.json
schemas/
  3d-quality-profile.schema.json
  asset-manifest.schema.json
  godot4-handoff-profile.schema.json
  vector-profile.schema.json
tests/
  test_animation_infer.py
  test_asset_forge.py
  test_asset_profile_validation.py
  test_blender_adapter.py
  test_engine_profile_validation.py
  test_gltf_binary_metrics.py
  test_gltf_diagnostics.py
  test_gltf_quality.py
  test_gltf_tools.py
  test_godot_3d_delivery.py
  test_godot_export.py
  test_godot_handoff.py
  test_raster_pack.py
  test_starlist_bridge.py
  test_svg_tools.py
  test_toolchain_3d.py
.repo-standards.yml
AGENTS.md
animation_infer.py
asset_forge.py
asset_profile_validation.py
blender_adapter.py
engine_profile_validation.py
gltf_binary_metrics.py
gltf_diagnostics.py
gltf_quality.py
gltf_tools.py
godot_3d_delivery.py
godot_export.py
godot_handoff.py
raster_pack.py
README.md
starlist_bridge.py
svg_tools.py
toolchain_3d.py
````

# Files

## File: .github/workflows/ai-repo-map.yml
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
    uses: dbrckk/repo-standards/.github/workflows/reusable-unified.yml@main
````

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
        run: python -m compileall -q asset_forge.py raster_pack.py godot_export.py godot_3d_delivery.py godot_handoff.py engine_profile_validation.py asset_profile_validation.py starlist_bridge.py animation_infer.py svg_tools.py gltf_tools.py gltf_quality.py gltf_binary_metrics.py gltf_diagnostics.py blender_adapter.py toolchain_3d.py tests
      - name: Unit tests
        run: python -m unittest discover -s tests -v
      - name: Validate example manifest
        run: python asset_forge.py validate examples/asset-manifest.json
      - name: Build example plan
        run: python asset_forge.py plan examples/asset-manifest.json
      - name: Inspect 3D toolchain
        run: python asset_forge.py 3d-toolchain-status
      - name: Validate engine handoff profiles
        run: python asset_forge.py validate-engine-profiles
      - name: Validate 3D and vector profiles
        run: python asset_forge.py validate-asset-profiles
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

## File: profiles/godot4/character.json
````json
{
  "id": "godot4-character",
  "engine": "Godot 4",
  "assetProfile": "character",
  "sceneImport": {
    "useNameSuffixes": true,
    "useNodeTypeSuffixes": true,
    "generateTangentsIfMissing": true,
    "preferStaticScene": false
  },
  "animation": {
    "import": true,
    "fps": 60,
    "trimming": false,
    "removeImmutableTracks": false
  },
  "textures": {
    "preferEmbeddedOrProjectLocal": true,
    "remoteUrisAllowed": false
  }
}
````

## File: profiles/godot4/environment.json
````json
{
  "id": "godot4-environment",
  "engine": "Godot 4",
  "assetProfile": "environment",
  "sceneImport": {
    "useNameSuffixes": true,
    "useNodeTypeSuffixes": true,
    "generateTangentsIfMissing": true,
    "preferStaticScene": true,
    "navigationCandidate": true
  },
  "animation": {
    "import": false,
    "fps": 30,
    "trimming": true,
    "removeImmutableTracks": true
  },
  "textures": {
    "preferEmbeddedOrProjectLocal": true,
    "remoteUrisAllowed": false
  }
}
````

## File: profiles/godot4/prop.json
````json
{
  "id": "godot4-prop",
  "engine": "Godot 4",
  "assetProfile": "prop",
  "sceneImport": {
    "useNameSuffixes": true,
    "useNodeTypeSuffixes": true,
    "generateTangentsIfMissing": true,
    "preferStaticScene": true
  },
  "animation": {
    "import": false,
    "fps": 30,
    "trimming": true,
    "removeImmutableTracks": true
  },
  "textures": {
    "preferEmbeddedOrProjectLocal": true,
    "remoteUrisAllowed": false
  }
}
````

## File: profiles/vector/icon.json
````json
{
  "id": "icon",
  "assetTypes": [
    "icon"
  ],
  "rules": {
    "requireViewBox": true,
    "requireSquareViewBox": true,
    "maxElements": 256,
    "allowExternalReferences": false,
    "removeMetadata": true,
    "maxBytes": 262144,
    "maxDepth": 32
  }
}
````

## File: profiles/vector/logo.json
````json
{
  "id": "logo",
  "assetTypes": [
    "logo"
  ],
  "rules": {
    "requireViewBox": true,
    "requireSquareViewBox": false,
    "maxElements": 800,
    "allowExternalReferences": false,
    "removeMetadata": true,
    "maxBytes": 524288,
    "maxDepth": 48
  }
}
````

## File: profiles/vector/ui.json
````json
{
  "id": "ui",
  "assetTypes": [
    "ui-vector",
    "vector"
  ],
  "rules": {
    "requireViewBox": true,
    "requireSquareViewBox": false,
    "maxElements": 1200,
    "allowExternalReferences": false,
    "removeMetadata": true,
    "maxBytes": 1048576,
    "maxDepth": 64
  }
}
````

## File: schemas/3d-quality-profile.schema.json
````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "asset-forge 3D quality profile",
  "type": "object",
  "required": ["id", "assetTypes", "rules"],
  "properties": {
    "id": {"enum": ["prop", "environment", "character"]},
    "assetTypes": {
      "type": "array",
      "minItems": 1,
      "items": {"type": "string", "minLength": 1}
    },
    "rules": {
      "type": "object",
      "required": [
        "maxMeshes", "maxPrimitives", "maxMaterials", "maxVertices",
        "maxTriangles", "maxTextures", "allowAnimations", "requireSkin",
        "requireNormals", "requireUvWhenTextured", "maxTextureDimension",
        "maxEstimatedTextureMipBytes", "maxJointsPerSkin"
      ],
      "properties": {
        "maxMeshes": {"type": "integer", "minimum": 1},
        "maxPrimitives": {"type": "integer", "minimum": 1},
        "maxMaterials": {"type": "integer", "minimum": 1},
        "maxVertices": {"type": "integer", "minimum": 1},
        "maxTriangles": {"type": "integer", "minimum": 1},
        "maxTextures": {"type": "integer", "minimum": 1},
        "allowAnimations": {"type": "boolean"},
        "requireSkin": {"type": "boolean"},
        "requireNormals": {"type": "boolean"},
        "requireUvWhenTextured": {"type": "boolean"},
        "maxTextureDimension": {"type": "integer", "minimum": 1},
        "maxEstimatedTextureMipBytes": {"type": "integer", "minimum": 1},
        "maxJointsPerSkin": {"type": "integer", "minimum": 0}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
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

## File: schemas/godot4-handoff-profile.schema.json
````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "asset-forge Godot 4 handoff profile",
  "type": "object",
  "required": ["id", "engine", "assetProfile", "sceneImport", "animation", "textures"],
  "properties": {
    "id": {"type": "string", "minLength": 1},
    "engine": {"const": "Godot 4"},
    "assetProfile": {"enum": ["prop", "environment", "character"]},
    "sceneImport": {
      "type": "object",
      "required": [
        "useNameSuffixes",
        "useNodeTypeSuffixes",
        "generateTangentsIfMissing",
        "preferStaticScene"
      ],
      "properties": {
        "useNameSuffixes": {"type": "boolean"},
        "useNodeTypeSuffixes": {"type": "boolean"},
        "generateTangentsIfMissing": {"type": "boolean"},
        "preferStaticScene": {"type": "boolean"},
        "navigationCandidate": {"type": "boolean"}
      },
      "additionalProperties": false
    },
    "animation": {
      "type": "object",
      "required": ["import", "fps", "trimming", "removeImmutableTracks"],
      "properties": {
        "import": {"type": "boolean"},
        "fps": {"type": "integer", "minimum": 1, "maximum": 240},
        "trimming": {"type": "boolean"},
        "removeImmutableTracks": {"type": "boolean"}
      },
      "additionalProperties": false
    },
    "textures": {
      "type": "object",
      "required": ["preferEmbeddedOrProjectLocal", "remoteUrisAllowed"],
      "properties": {
        "preferEmbeddedOrProjectLocal": {"type": "boolean"},
        "remoteUrisAllowed": {"type": "boolean"}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
````

## File: schemas/vector-profile.schema.json
````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "asset-forge vector validation profile",
  "type": "object",
  "required": [
    "id",
    "assetTypes",
    "rules"
  ],
  "properties": {
    "id": {
      "enum": [
        "icon",
        "ui",
        "logo"
      ]
    },
    "assetTypes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "rules": {
      "type": "object",
      "required": [
        "requireViewBox",
        "requireSquareViewBox",
        "maxElements",
        "allowExternalReferences",
        "removeMetadata",
        "maxBytes",
        "maxDepth"
      ],
      "properties": {
        "requireViewBox": {
          "type": "boolean"
        },
        "requireSquareViewBox": {
          "type": "boolean"
        },
        "maxElements": {
          "type": "integer",
          "minimum": 1
        },
        "allowExternalReferences": {
          "type": "boolean"
        },
        "removeMetadata": {
          "type": "boolean"
        },
        "maxBytes": {
          "type": "integer",
          "minimum": 1
        },
        "maxDepth": {
          "type": "integer",
          "minimum": 1
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
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

## File: tests/test_asset_profile_validation.py
````python
class AssetProfileValidationTests(unittest.TestCase)
⋮----
def test_repository_profiles_all_validate(self)
⋮----
root = Path(__file__).resolve().parents[1]
report = validate_all_asset_profiles(root)
⋮----
def test_3d_loader_reads_versioned_budget(self)
⋮----
profile = load_3d_profile("character")
⋮----
def test_vector_loader_reads_versioned_budget(self)
⋮----
profile = load_vector_profile("icon")
⋮----
def test_invalid_3d_unknown_rule_fails(self)
⋮----
data = {
errors = validate_3d_profile_data(data, "prop")
⋮----
def test_invalid_vector_type_fails(self)
⋮----
errors = validate_vector_profile_data(data, "icon")
⋮----
def test_3d_loader_uses_file_as_source_of_truth(self)
⋮----
root = Path(tmp)
profile_dir = root / "profiles" / "3d"
⋮----
loaded = load_3d_profile("prop", root=root)
⋮----
def test_vector_loader_uses_file_as_source_of_truth(self)
⋮----
profile_dir = root / "profiles" / "vector"
⋮----
loaded = load_vector_profile("icon", root=root)
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

## File: tests/test_engine_profile_validation.py
````python
class EngineProfileValidationTests(unittest.TestCase)
⋮----
def valid_profile(self)
⋮----
def test_valid_profile_passes(self)
⋮----
def test_missing_required_field_fails(self)
⋮----
data = self.valid_profile()
⋮----
errors = validate_godot_profile_data(data, "prop")
⋮----
def test_unknown_field_fails(self)
⋮----
def test_wrong_type_fails(self)
⋮----
def test_invalid_fps_fails(self)
⋮----
def test_profile_name_mismatch_fails(self)
⋮----
errors = validate_godot_profile_data(data, "character")
⋮----
def test_invalid_json_file_fails(self)
⋮----
path = Path(tmp) / "prop.json"
⋮----
def test_repository_profiles_all_validate(self)
⋮----
root = Path(__file__).resolve().parents[1]
report = validate_all_godot_profiles(root)
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

## File: tests/test_gltf_diagnostics.py
````python
class GltfDiagnosticsTests(unittest.TestCase)
⋮----
def write(self, root: Path, data: dict) -> Path
⋮----
path = root / "asset.gltf"
⋮----
def test_accessor_byte_range_and_layout(self)
⋮----
payload = struct.pack("<9f", *[float(i) for i in range(9)])
uri = "data:application/octet-stream;base64," + base64.b64encode(payload).decode("ascii")
data = {
⋮----
report = inspect_accessors(self.write(Path(tmp), data))
⋮----
def test_accessor_overrun_is_rejected(self)
⋮----
def test_skinning_requires_matching_vec4_attributes(self)
⋮----
report = inspect_skinning_consistency(self.write(Path(tmp), data))
⋮----
def test_animation_duration_reads_real_key_times(self)
⋮----
times = struct.pack("<3f", 0.0, 0.5, 2.0)
output = struct.pack("<9f", *([0.0] * 9))
payload = times + output
⋮----
report = inspect_animation_consistency(self.write(Path(tmp), data))
⋮----
def test_non_increasing_animation_times_are_rejected(self)
⋮----
times = struct.pack("<3f", 0.0, 1.0, 1.0)
⋮----
def test_deep_report_has_all_sections(self)
⋮----
path = self.write(Path(tmp), {"asset": {"version": "2.0"}})
report = deep_gltf_diagnostics(path)
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

## File: tests/test_godot_3d_delivery.py
````python
class Godot3DDeliveryTests(unittest.TestCase)
⋮----
def write(self, root: Path, data: dict, suffix: str = ".glb.json") -> Path
⋮----
path = root / ("asset.gltf" if suffix == ".gltf" else "asset.gltf")
⋮----
def base(self)
⋮----
def test_detects_godot_name_suffixes(self)
⋮----
report = godot_3d_delivery_report(
⋮----
def test_duplicate_node_names_warn(self)
⋮----
data = self.base()
⋮----
report = godot_3d_delivery_report(self.write(Path(tmp), data), "prop")
⋮----
def test_loop_animation_hint_detected(self)
⋮----
def test_remote_image_blocks_delivery(self)
⋮----
def test_double_sided_material_warns(self)
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

## File: tests/test_godot_handoff.py
````python
class GodotHandoffTests(unittest.TestCase)
⋮----
def test_recommendations_disable_animation_for_prop_without_clips(self)
⋮----
recommendations = build_import_recommendations(
⋮----
def test_profiles_are_loaded_from_versioned_json(self)
⋮----
prop = load_godot_profile("prop")
environment = load_godot_profile("environment")
character = load_godot_profile("character")
⋮----
def test_recommendations_report_profile_source(self)
⋮----
recommendations = build_import_recommendations("character")
⋮----
def test_profile_loader_uses_file_contents_as_source_of_truth(self)
⋮----
root = Path(tmp)
profile_dir = root / "profiles" / "godot4"
⋮----
loaded = load_godot_profile("prop", root=root)
⋮----
def test_prepare_handoff_copies_glb_and_writes_project(self)
⋮----
source = root / "model.glb"
⋮----
report = {"ready": True, "scene": {"animations": 0, "godotNameSuffixes": {}}}
⋮----
asset_manifest = {
result = prepare_godot_handoff(
⋮----
project_dir = Path(result["projectDir"])
copied = Path(result["asset"])
manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
⋮----
def test_missing_delivery_report_is_rejected(self)
⋮----
def test_failed_delivery_report_is_rejected(self)
⋮----
def test_allow_unvalidated_override(self)
⋮----
def test_non_glb_is_rejected(self)
⋮----
source = root / "model.gltf"
⋮----
def test_import_command_uses_headless_import(self)
⋮----
command = godot_import_command("godot", Path("project"))
⋮----
@patch("godot_handoff.detect_godot")
    def test_missing_godot_is_non_blocking(self, detect)
⋮----
project = Path(tmp)
⋮----
result = validate_godot_handoff(project)
⋮----
@patch("godot_handoff.subprocess.run")
@patch("godot_handoff.detect_godot")
    def test_available_godot_import_passes(self, detect, run)
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
⋮----
def test_rejects_invalid_ihdr_length(self)
⋮----
image = Path(tmp) / "bad.png"
⋮----
def test_rejects_zero_dimensions(self)
⋮----
ihdr = struct.pack(">IIBBBBB", 0, 1, 8, 6, 0, 0, 0)
⋮----
def test_rejects_duplicate_ihdr(self)
⋮----
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
⋮----
def test_rejects_non_consecutive_idat(self)
⋮----
compressed = zlib.compress(b"\x00\x00\x00\x00\xff")
split = max(1, len(compressed) // 2)
⋮----
def test_rejects_trailing_data_after_iend(self)
⋮----
def test_rejects_indexed_trns_longer_than_palette(self)
⋮----
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
⋮----
def test_rejects_trns_for_rgba(self)
⋮----
def test_truecolor_trns_is_applied(self)
⋮----
image = Path(tmp) / "rgb-trns.png"
⋮----
transparency = struct.pack(">HHH", 7, 8, 9)
⋮----
def test_rejects_decompressed_data_larger_than_expected(self)
⋮----
image = Path(tmp) / "bomb.png"
⋮----
raw = b"\x00\x00\x00\x00\xff" + (b"x" * 1000)
⋮----
def test_hardened_inspector_reports_palette_and_transparency(self)
⋮----
info = inspect_png(image)
⋮----
def test_oversized_file_is_rejected_before_read(self)
⋮----
image = Path(tmp) / "small.png"
⋮----
def test_indexed_1bit_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "indexed1.png"
ihdr = struct.pack(">IIBBBBB", 8, 1, 1, 3, 0, 0, 0)
palette = bytes([0, 0, 0, 255, 255, 255])
# samples: 0,1,0,1,1,0,1,0 => 0b01011010
raw = b"\x00" + bytes([0b01011010])
⋮----
def test_indexed_2bit_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "indexed2.png"
ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 3, 0, 0, 0)
palette = bytes([
# samples 0,1,2,3 => 00 01 10 11
raw = b"\x00" + bytes([0b00011011])
⋮----
def test_indexed_4bit_png_ignores_padding_nibble(self)
⋮----
image = Path(tmp) / "indexed4.png"
ihdr = struct.pack(">IIBBBBB", 3, 1, 4, 3, 0, 0, 0)
palette = b"".join(bytes([i, 0, 0]) for i in range(16))
# samples 1,2,3; low nibble of second byte is row padding and must be ignored
raw = b"\x00" + bytes([0x12, 0x3F])
⋮----
def test_indexed_low_bit_depth_transparency_is_applied(self)
⋮----
image = Path(tmp) / "indexed-trns.png"
ihdr = struct.pack(">IIBBBBB", 2, 1, 1, 3, 0, 0, 0)
palette = bytes([10, 20, 30, 40, 50, 60])
transparency = bytes([255, 0])
raw = b"\x00" + bytes([0b01000000])
⋮----
def test_indexed_low_bit_depth_palette_limit_is_enforced(self)
⋮----
image = Path(tmp) / "bad-indexed.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 1, 3, 0, 0, 0)
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
⋮----
def test_data_uri_reference_is_rejected(self)
⋮----
def test_relative_reference_is_rejected(self)
⋮----
def test_internal_fragment_reference_is_allowed(self)
⋮----
path = Path(tmp) / "ok.svg"
⋮----
def test_css_external_url_is_rejected(self)
⋮----
def test_presentation_attribute_external_url_is_rejected(self)
⋮----
def test_css_import_is_rejected(self)
⋮----
def test_sanitize_removes_unsafe_css(self)
⋮----
def test_profile_depth_limit_is_blocking(self)
⋮----
path = Path(tmp) / "deep.svg"
inner = '<rect width="1" height="1"/>'
⋮----
inner = f"<g>{inner}</g>"
⋮----
def test_profile_element_limit_is_blocking(self)
⋮----
path = Path(tmp) / "complex.svg"
body = "".join('<rect width="1" height="1"/>' for _ in range(260))
⋮----
def test_profile_file_size_limit_is_blocking(self)
⋮----
path = Path(tmp) / "large.svg"
payload = "x" * 270000
⋮----
def test_existing_malformed_viewbox_is_not_overwritten(self)
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
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_godot4_target_adds_delivery_stage(self, detect)
⋮----
def test_invalid_target_engine_is_rejected(self)
````

## File: .repo-standards.yml
````yaml
source: dbrckk/repo-standards
ref: main
version: 12
adopted: true
workflow_mode: unified-single-commit
repo_brain: dbrckk/repo-brain@main
repo_brain_fallback: portable-full-rebuild
hotset_fallback: recent-project-state
graph_routing: compact-sharded-reverse-deps
ai_context:
  index: .ai/index.md
  project_state: .ai/project-state.md
  change_impact: .ai/change-impact.md
  architecture: .ai/architecture.json
  dependency_map: .ai/dependency-map.json
  commands: .ai/commands.json
  ci_status: .ai/ci-status.md
  security_signals: .ai/security-signals.json
  repo_health: .ai/repo-health.md
  brain_summary: .ai/brain/summary.md
  brain_incremental_state: .ai/brain/incremental-state.json
  brain_impact: .ai/brain/impact.json
  brain_selected_tests: .ai/brain/selected-tests.json
  brain_references: .ai/brain/references.json
  brain_symbol_dependencies: .ai/brain/symbol-dependencies.json
  brain_capabilities: .ai/brain/capabilities.json
  brain_ast_routing: .ai/brain/ast-routing.json
  brain_ast_symbols: .ai/brain/ast-symbols/
  brain_file_outlines: .ai/brain/file-outlines/
  brain_lookup: .ai/brain/lookup.json
  brain_symbols: .ai/brain/symbols.json
  brain_graph: .ai/brain/code-graph.json
  brain_graph_index: .ai/brain/graph-index.json
  brain_graph_manifest: .ai/brain/graph-manifest.json
  brain_graph_shards: .ai/brain/graph-shards/
  brain_reverse_deps: .ai/brain/reverse-deps.json
  brain_architecture_mermaid: .ai/brain/architecture.mmd
  brain_hotset: .ai/brain/hotset.json
  brain_context_manifest: .ai/brain/context-manifest.json
  brain_context_packets: .ai/brain/context/
  brain_hash_cache: .ai/brain/hash-cache.json
  session_state: .ai/session-state.json
  repo_map: .ai/repo-map.md
  segmented_maps: .ai/maps/
workflow:
  file: .github/workflows/ai-repo-map.yml
  reusable_unified: .github/workflows/reusable-unified.yml
````

## File: AGENTS.md
````markdown
# Shared repository intelligence

This repository uses `dbrckk/repo-standards` and `dbrckk/repo-brain`. Before substantial work, follow `.repo-standards.yml` and the bounded-context reading order from the central standards. Preserve the repository-specific instructions below.

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
gltf_diagnose = sub.add_parser("diagnose-gltf", help="run deep accessor, skinning, and animation diagnostics")
⋮----
godot3d = sub.add_parser("validate-godot-3d", help="validate a glTF/GLB delivery for Godot 4")
⋮----
godot_handoff = sub.add_parser("prepare-godot-handoff", help="prepare a self-contained Godot 4 handoff project")
⋮----
godot_import = sub.add_parser("validate-godot-handoff", help="run Godot headless import validation on a handoff")
⋮----
engine_profiles = sub.add_parser("validate-engine-profiles", help="validate versioned engine handoff profiles")
asset_profiles = sub.add_parser("validate-asset-profiles", help="validate versioned 3D and vector asset profiles")
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
result = deep_gltf_diagnostics(args.input)
⋮----
has_errors = any(
⋮----
result = godot_3d_delivery_report(args.input, args.profile)
⋮----
delivery = load_json(args.delivery_report) if args.delivery_report else None
asset_manifest = load_json(args.asset_manifest) if args.asset_manifest else None
⋮----
manifest_errors = validate_manifest(asset_manifest)
⋮----
result = prepare_godot_handoff(
⋮----
result = validate_godot_handoff(args.project_dir, executable=args.godot)
⋮----
result = validate_all_godot_profiles(root)
⋮----
result = validate_all_asset_profiles(root)
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

## File: asset_profile_validation.py
````python
THREED_PROFILES = {"prop", "environment", "character"}
VECTOR_PROFILES = {"icon", "ui", "logo"}
⋮----
THREED_RULE_TYPES = {
⋮----
VECTOR_RULE_TYPES = {
⋮----
def _load_json(path: Path) -> tuple[dict | None, list[str]]
⋮----
data = json.loads(path.read_text(encoding="utf-8"))
⋮----
def _validate_rule_types(rules, expected: dict[str, type], label: str) -> list[str]
⋮----
errors: list[str] = []
⋮----
def validate_3d_profile_data(data: dict, expected_profile: str | None = None) -> list[str]
⋮----
allowed = {"id", "assetTypes", "rules"}
⋮----
profile_id = data.get("id")
⋮----
asset_types = data.get("assetTypes")
⋮----
rules = data.get("rules")
⋮----
positive_or_zero = {
⋮----
value = rules.get(key)
⋮----
def validate_vector_profile_data(data: dict, expected_profile: str | None = None) -> list[str]
⋮----
def load_3d_profile(profile: str, root: Path | None = None) -> dict
⋮----
base = root or Path(__file__).resolve().parent
path = base / "profiles" / "3d" / f"{profile}.json"
⋮----
def load_vector_profile(profile: str, root: Path | None = None) -> dict
⋮----
path = base / "profiles" / "vector" / f"{profile}.json"
⋮----
def validate_all_asset_profiles(root: Path) -> dict
⋮----
groups = {}
valid = True
⋮----
group = {}
⋮----
path = root / "profiles" / folder / f"{profile}.json"
⋮----
valid = valid and not errors
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

## File: engine_profile_validation.py
````python
ALLOWED_PROFILES = {"prop", "environment", "character"}
SCENE_KEYS = {
OPTIONAL_SCENE_KEYS = {"navigationCandidate": bool}
ANIMATION_KEYS = {
TEXTURE_KEYS = {
⋮----
errors: list[str] = []
optional = optional or {}
⋮----
allowed = set(required) | set(optional)
⋮----
def validate_godot_profile_data(data: dict, expected_profile: str | None = None) -> list[str]
⋮----
allowed_top = {"id", "engine", "assetProfile", "sceneImport", "animation", "textures"}
⋮----
profile_id = data.get("id")
⋮----
asset_profile = data.get("assetProfile")
⋮----
animation = data.get("animation")
⋮----
fps = animation.get("fps")
⋮----
def validate_godot_profile_file(path: Path, expected_profile: str | None = None) -> tuple[dict | None, list[str]]
⋮----
data = json.loads(path.read_text(encoding="utf-8"))
⋮----
def validate_all_godot_profiles(root: Path) -> dict
⋮----
profile_dir = root / "profiles" / "godot4"
results = {}
valid = True
⋮----
path = profile_dir / f"{profile}.json"
⋮----
valid = valid and not errors
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

## File: gltf_diagnostics.py
````python
COMPONENT_INFO = {
⋮----
TYPE_COMPONENTS = {
⋮----
def accessor_layout(accessor: dict) -> dict
⋮----
component_type = accessor.get("componentType")
accessor_type = accessor.get("type")
count = accessor.get("count")
⋮----
info = COMPONENT_INFO.get(component_type)
components = TYPE_COMPONENTS.get(accessor_type)
⋮----
component_bytes = info[1]
element_bytes = component_bytes * components
⋮----
def inspect_accessors(path: Path) -> dict
⋮----
accessors = data.get("accessors", [])
buffer_views = data.get("bufferViews", [])
buffers = data.get("buffers", [])
⋮----
accessors = []
⋮----
buffer_views = []
⋮----
buffers = []
⋮----
payloads = load_buffer_payloads(path, data)
items = []
errors: list[str] = []
warnings: list[str] = []
total_packed_bytes = 0
⋮----
item = {"index": index}
⋮----
layout = accessor_layout(accessor)
⋮----
view_index = accessor.get("bufferView")
byte_offset = accessor.get("byteOffset", 0)
⋮----
view = buffer_views[view_index]
⋮----
stride = view.get("byteStride", layout["elementBytes"])
⋮----
required = byte_offset
⋮----
view_length = view.get("byteLength")
⋮----
buffer_index = view.get("buffer")
⋮----
payload = payloads[buffer_index]
⋮----
view_offset = view.get("byteOffset", 0)
⋮----
start = view_offset + byte_offset
end = start + (stride * (layout["count"] - 1) + layout["elementBytes"] if layout["count"] else 0)
⋮----
def _read_scalar_accessor(path: Path, accessor_index: int) -> list[float] | None
⋮----
views = data.get("bufferViews", [])
⋮----
accessor = accessors[accessor_index]
⋮----
view = views[view_index]
⋮----
fmt = COMPONENT_INFO[accessor["componentType"]][0]
⋮----
accessor_offset = accessor.get("byteOffset", 0)
⋮----
start = view_offset + accessor_offset
⋮----
values = []
⋮----
offset = start + i * stride
end = offset + layout["componentBytes"]
⋮----
value = struct.unpack_from("<" + fmt, payload, offset)[0]
⋮----
def inspect_skinning_consistency(path: Path) -> dict
⋮----
meshes = data.get("meshes", [])
⋮----
meshes = []
⋮----
skinned_primitives = 0
⋮----
primitives = mesh.get("primitives", [])
⋮----
attrs = primitive.get("attributes", {})
⋮----
joints_index = attrs.get("JOINTS_0")
weights_index = attrs.get("WEIGHTS_0")
⋮----
label = f"mesh {mesh_index} primitive {primitive_index}"
⋮----
joints = accessors[joints_index]
weights = accessors[weights_index]
⋮----
joints_count = joints.get("count")
weights_count = weights.get("count")
⋮----
position_index = attrs.get("POSITION")
⋮----
position = accessors[position_index]
⋮----
def inspect_animation_consistency(path: Path) -> dict
⋮----
animations = data.get("animations", [])
⋮----
nodes = data.get("nodes", [])
⋮----
animations = []
⋮----
nodes = []
⋮----
samplers = animation.get("samplers", [])
channels = animation.get("channels", [])
⋮----
samplers = []
⋮----
channels = []
⋮----
animation_start = None
animation_end = None
used_samplers = set()
⋮----
input_index = sampler.get("input")
output_index = sampler.get("output")
interpolation = sampler.get("interpolation", "LINEAR")
⋮----
input_accessor = accessors[input_index]
⋮----
input_count = input_accessor.get("count")
output_accessor = accessors[output_index]
output_count = output_accessor.get("count") if isinstance(output_accessor, dict) else None
expected_multiplier = 3 if interpolation == "CUBICSPLINE" else 1
⋮----
values = _read_scalar_accessor(path, input_index)
⋮----
start = values[0]
end = values[-1]
animation_start = start if animation_start is None else min(animation_start, start)
animation_end = end if animation_end is None else max(animation_end, end)
⋮----
sampler_index = channel.get("sampler")
⋮----
target = channel.get("target")
⋮----
node = target.get("node")
target_path = target.get("path")
⋮----
unused = sorted(set(range(len(samplers))) - used_samplers)
⋮----
duration = None
⋮----
duration = max(0.0, animation_end - animation_start)
⋮----
durations = [item["durationSeconds"] for item in items if item["durationSeconds"] is not None]
⋮----
def deep_gltf_diagnostics(path: Path) -> dict
````

## File: gltf_quality.py
````python
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
diagnostics = deep_gltf_diagnostics(path)
known_image_dimensions = [item for item in image_metrics if item.get("width") and item.get("height")]
estimated_texture_bytes = sum(
estimated_texture_mip_bytes = sum(
max_texture_width = max((int(item["width"]) for item in known_image_dimensions), default=0)
max_texture_height = max((int(item["height"]) for item in known_image_dimensions), default=0)
⋮----
def evaluate_quality(report: dict, profile: str) -> dict
⋮----
profile_data = load_3d_profile(profile)
rules = profile_data["rules"]
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
diagnostics = report.get("diagnostics", {})
accessor_diag = diagnostics.get("accessors", {})
skin_diag = diagnostics.get("skinning", {})
animation_diag = diagnostics.get("animations", {})
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

## File: godot_3d_delivery.py
````python
GODOT_IMPORT_SUFFIXES = {
⋮----
SAFE_NAME = re.compile(r"^[A-Za-z0-9_. $-]+$")
⋮----
def _name_suffixes(name: str) -> list[str]
⋮----
lowered = name.lower()
found = []
⋮----
def godot_3d_delivery_report(path: Path, profile: str = "prop") -> dict
⋮----
quality = quality_report(path, profile)
⋮----
errors: list[str] = []
warnings: list[str] = []
recommendations: list[str] = []
⋮----
asset = data.get("asset", {})
⋮----
nodes = data.get("nodes", [])
meshes = data.get("meshes", [])
materials = data.get("materials", [])
animations = data.get("animations", [])
images = data.get("images", [])
⋮----
nodes = nodes if isinstance(nodes, list) else []
meshes = meshes if isinstance(meshes, list) else []
materials = materials if isinstance(materials, list) else []
animations = animations if isinstance(animations, list) else []
images = images if isinstance(images, list) else []
⋮----
unnamed_nodes = 0
duplicate_names: dict[str, int] = {}
suffix_usage: dict[str, int] = {}
suspicious_names = []
⋮----
name = node.get("name")
⋮----
duplicates = sorted(name for name, count in duplicate_names.items() if count > 1)
⋮----
unnamed_animations = 0
looping_hints = 0
⋮----
name = animation.get("name")
⋮----
suffixes = _name_suffixes(name)
⋮----
pbr_materials = 0
double_sided = 0
normal_mapped = 0
⋮----
attributes = quality.get("attributes", {})
⋮----
remote_images = 0
external_local_images = 0
⋮----
rig = quality.get("rigAnimation", {})
⋮----
evaluation = quality.get("evaluation", {})
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

## File: godot_handoff.py
````python
def detect_godot() -> dict
⋮----
path = shutil.which(name)
⋮----
def load_godot_profile(profile: str, root: Path | None = None) -> dict
⋮----
base = root or Path(__file__).resolve().parent
path = base / "profiles" / "godot4" / f"{profile}.json"
⋮----
def build_import_recommendations(profile: str, delivery_report: dict | None = None) -> dict
⋮----
profile_data = load_godot_profile(profile)
scene_import = dict(profile_data["sceneImport"])
animation = dict(profile_data["animation"])
textures = dict(profile_data["textures"])
⋮----
recommendations = {
⋮----
scene = delivery_report.get("scene", {})
⋮----
source_glb = Path(source_glb)
output_dir = Path(output_dir)
⋮----
project_dir = output_dir / "godot-handoff"
asset_dir = project_dir / "assets"
⋮----
destination = asset_dir / source_glb.name
⋮----
project_file = project_dir / "project.godot"
⋮----
recommendations = build_import_recommendations(profile, delivery_report)
⋮----
provenance = None
⋮----
source = asset_manifest.get("source", {})
license_data = asset_manifest.get("license", {})
provenance = {
⋮----
manifest = {
⋮----
manifest_path = project_dir / "handoff.json"
⋮----
readme = project_dir / "README.md"
⋮----
def godot_import_command(executable: str, project_dir: Path) -> list[str]
⋮----
def validate_godot_handoff(project_dir: Path, executable: str | None = None) -> dict
⋮----
project_dir = Path(project_dir)
⋮----
detected = detect_godot()
chosen = executable or detected["path"]
⋮----
command = godot_import_command(chosen, project_dir)
completed = subprocess.run(
````

## File: raster_pack.py
````python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_FILE_BYTES = 256 * 1024 * 1024
MAX_PNG_CHUNK_BYTES = 64 * 1024 * 1024
MAX_PNG_CHUNKS = 10000
MAX_PNG_PIXELS = 100_000_000
MAX_DECOMPRESSED_BYTES = 512 * 1024 * 1024
⋮----
def _read_png_bytes(path: Path) -> bytes
⋮----
size = path.stat().st_size
⋮----
def _chunks(data: bytes) -> list[tuple[bytes, bytes]]
⋮----
chunks: list[tuple[bytes, bytes]] = []
offset = 8
saw_iend = False
saw_ihdr = False
saw_idat = False
idat_closed = False
⋮----
length = struct.unpack(">I", data[offset : offset + 4])[0]
kind = data[offset + 4 : offset + 8]
⋮----
end = offset + 12 + length
⋮----
payload = data[offset + 8 : offset + 8 + length]
expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
⋮----
saw_ihdr = True
⋮----
saw_idat = True
⋮----
idat_closed = True
⋮----
saw_iend = True
offset = end
⋮----
def _validate_ihdr(payload: bytes) -> tuple[int, int, int, int, int, int, int]
⋮----
valid_depths = {
⋮----
palette: list[tuple[int, int, int]] = []
transparency = b""
saw_plte = False
saw_trns = False
⋮----
entries = len(payload) // 3
⋮----
palette = [
saw_plte = True
⋮----
transparency = payload
saw_trns = True
⋮----
def _decompress_idat(data: bytes, expected_size: int) -> bytes
⋮----
inflater = zlib.decompressobj()
⋮----
raw = inflater.decompress(data, expected_size + 1)
⋮----
before = len(inflater.unconsumed_tail)
extra = inflater.decompress(inflater.unconsumed_tail, 1)
⋮----
def inspect_png(path: Path) -> dict
⋮----
data = _read_png_bytes(path)
chunks = _chunks(data)
⋮----
def _paeth(a: int, b: int, c: int) -> int
⋮----
prediction = a + b - c
pa = abs(prediction - a)
pb = abs(prediction - b)
pc = abs(prediction - c)
⋮----
def _unfilter_scanlines(raw: bytes, stride: int, height: int, filter_bpp: int) -> list[bytearray]
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
left = reconstructed[index - filter_bpp] if index >= filter_bpp else 0
above = previous[index]
upper_left = previous[index - filter_bpp] if index >= filter_bpp else 0
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
def _scanline_layout(width: int, depth: int, color_type: int) -> tuple[int, int]
⋮----
channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
bits_per_pixel = channels * depth
stride = (width * bits_per_pixel + 7) // 8
filter_bpp = max(1, (bits_per_pixel + 7) // 8)
⋮----
def _unpack_indexed_row(row: bytes, width: int, depth: int) -> list[int]
⋮----
mask = (1 << depth) - 1
values: list[int] = []
⋮----
shift = 8 - depth
⋮----
def decode_rgba(path: Path) -> tuple[int, int, bytes]
⋮----
chunks = _chunks(_read_png_bytes(path))
⋮----
expected_size = (stride + 1) * height
compressed = b"".join(payload for kind, payload in chunks if kind == b"IDAT")
raw = _decompress_idat(compressed, expected_size)
rows = _unfilter_scanlines(raw, stride, height, filter_bpp)
⋮----
rgba = bytearray(width * height * 4)
destination = 0
⋮----
indexed_samples = _unpack_indexed_row(row, width, depth)
⋮----
alpha = transparency[palette_index] if palette_index < len(transparency) else 255
⋮----
bpp_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
bpp = bpp_by_type[color_type]
⋮----
gray = row[index]
red = green = blue = gray
alpha = 255
⋮----
transparent_gray = struct.unpack(">H", transparency[:2])[0]
⋮----
alpha = 0
⋮----
def _chunk(kind: bytes, payload: bytes) -> bytes
⋮----
def _filter_row(row: bytes, previous: bytes, bpp: int, filter_type: int) -> bytes
⋮----
output = bytearray(len(row))
⋮----
left = row[index - bpp] if index >= bpp else 0
⋮----
upper_left = previous[index - bpp] if index >= bpp else 0
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

An existing malformed `viewBox` is now rejected rather than silently replaced from width/height.

Apply a production profile:

```bash
python asset_forge.py validate-svg icon.svg --profile icon
python asset_forge.py validate-svg hud.svg --profile ui
python asset_forge.py validate-svg brand.svg --profile logo
```

The current vector validator checks XML validity, SVG root type, viewBox shape, width/height consistency, scripts/foreignObject, event-handler attributes, references, editor metadata, and profile-specific complexity/shape rules. Versioned profiles under `profiles/vector/` are the runtime source of truth; `svg_tools.py` loads them directly instead of duplicating their rules.

SVG delivery now uses a strict reference policy: only internal fragment references such as `#gradient` and `url(#gradient)` are accepted. Remote URLs, relative file paths, `data:` references, CSS `@import`, and non-fragment CSS `url(...)` references are rejected. Sanitization removes unsafe reference attributes and unsafe style blocks/attributes.

Vector profiles also define blocking resource caps for element count, UTF-8 file bytes, and XML depth. Current repository policy is icon: 256 elements / 256 KiB / depth 32, UI: 1200 elements / 1 MiB / depth 64, and logo: 800 elements / 512 KiB / depth 48. These are repository policy limits, not universal SVG standards. A larger absolute safety ceiling is also enforced before recursive processing.

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

Run deep accessor/skinning/animation diagnostics:

```bash
python asset_forge.py diagnose-gltf model.glb --output build/model-diagnostics.json
```

Measure production quality and budgets:

```bash
python asset_forge.py quality-gltf prop.glb --profile prop --output build/prop-quality.json
```

The quality report derives vertex and triangle counts from accessor metadata, measures primitive coverage for normals/UVs/tangents/skinning, summarizes PBR texture usage, identifies external images, and evaluates the versioned profile budgets under `profiles/3d/`. These JSON profiles are now the runtime source of truth for 3D quality budgets; `gltf_quality.py` loads them directly.

When image bytes are locally available, the report also reads PNG/JPEG/WebP dimensions and estimates decoded RGBA8 texture memory with mipmaps. Remote URLs are not fetched. Rig/animation metrics include joints per skin, inverse bind matrices, animation channels/samplers, target paths, animated nodes, keyframe accessor counts, and duration when animation time accessors are locally readable.

Deep diagnostics additionally check accessor layout/ranges, byteStride alignment, JOINTS_0/WEIGHTS_0 type and count consistency, animation sampler input/output counts, interpolation modes, sampler/channel references, target nodes/paths, unused samplers, and strictly increasing key times.

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

For a Godot 4 handoff, add the engine target:

```bash
python asset_forge.py run-3d source.blend build/model \
  --profile character \
  --optimizer gltf-transform \
  --engine godot4
```

You can also validate an already exported asset directly:

```bash
python asset_forge.py validate-godot-3d character.glb \
  --profile character \
  --output build/godot4-delivery.json
```

Prepare a self-contained Godot handoff project:

```bash
python asset_forge.py prepare-godot-handoff character.glb build/handoff \
  --profile character \
  --delivery-report build/godot4-delivery.json
```

The handoff is strict by default: the delivery report must exist and contain `ready: true`. For controlled debugging only, `--allow-unvalidated` bypasses this gate.

Attach Asset Forge provenance/licensing metadata when available:

```bash
python asset_forge.py prepare-godot-handoff character.glb build/handoff \
  --profile character \
  --delivery-report build/godot4-delivery.json \
  --asset-manifest manifests/character.json
```

The manifest is validated before use. Source mode/URI/author, asset identity, project, importance, license ID, commercial-use/derivative permissions, and attribution requirements are copied into `handoff.json`.

If a Godot editor executable is installed, validate the generated project with Godot's headless importer:

```bash
python asset_forge.py validate-godot-handoff build/handoff/godot-handoff
```

The generated handoff contains a minimal `project.godot`, a copied GLB under `assets/`, `handoff.json` with import recommendations/provenance, and a short README. Versioned engine handoff profiles live in `profiles/godot4/` for prop, environment, and character assets. These JSON files are the runtime source of truth for handoff recommendations; the Python code loads and validates them instead of duplicating their settings.

Validate all engine profiles directly:

```bash
python asset_forge.py validate-engine-profiles
```

Validate the versioned 3D and vector asset profiles:

```bash
python asset_forge.py validate-asset-profiles
```

The Godot handoff contract is documented by `schemas/godot4-handoff-profile.schema.json`. The same pattern is used for `schemas/3d-quality-profile.schema.json` and `schemas/vector-profile.schema.json`. Runtime validation rejects malformed profile structures before they reach the consumers, and CI validates all three profile families on every change. When Godot is available, handoff validation also runs the documented headless `--import` workflow.

The Godot delivery report checks glTF 2.0 suitability, stable/duplicate names, Godot import suffix hints, animation naming, PBR materials, double-sided materials, normal-map tangents, remote/external images, and the existing 3D quality profile.

The generated chain is Blender export → internal structural validation → quality/budget report → optional Khronos validation → optional optimization → post-optimization structural validation → final quality report. With `--engine godot4`, a final Godot delivery gate is appended; after a successful run, Asset Forge also creates a self-contained Godot handoff project and attempts a headless Godot import check when the editor executable is available. If an optional optimizer is unavailable, the pipeline keeps the validated raw GLB as the final output instead of pointing to a file that was never generated.

A completed run also writes `production-report.json`, which records step status and compares raw vs final vertices, triangles, and file bytes when both quality reports are available.

## Initial interoperability

- glTF/GLB for portable 3D delivery
- SVG for vector master assets
- PNG/WebP for raster delivery
- sprite sheets/atlases for 2D animation

The repository starts deliberately small. Tooling is added only after validation.


### Hardened PNG parsing

PNG parsing now applies repository safety caps to total file bytes, chunk bytes/count, pixel count, and decompressed scanline bytes. IHDR/IDAT/IEND structure, PLTE/tRNS rules, zlib completion, and expected scanline size are validated consistently by raster validation, packing, and recompression.


Indexed PNG decoding now calculates packed scanline byte widths correctly, applies PNG filters with the proper byte-distance rule, unpacks 1/2/4-bit palette indices most-significant bits first, ignores row padding bits beyond the declared width, and preserves palette transparency through RGBA conversion.
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
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
CSS_IMPORT = re.compile(r"@import\b", re.IGNORECASE)
ABSOLUTE_MAX_BYTES = 8 * 1024 * 1024
ABSOLUTE_MAX_ELEMENTS = 100_000
ABSOLUTE_MAX_DEPTH = 256
⋮----
def _local_name(name: str) -> str
⋮----
def _is_unsafe_reference(value: str) -> bool
⋮----
value = value.strip()
⋮----
def _unsafe_css_references(value: str) -> list[str]
⋮----
unsafe = []
⋮----
target = match.group(2).strip()
⋮----
def _max_depth(root: ET.Element) -> int
⋮----
maximum = 0
stack = [(root, 1)]
⋮----
maximum = max(maximum, depth)
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
raw_bytes = len(raw.encode("utf-8"))
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
css_refs: list[str] = []
dangerous_tags: list[str] = []
event_attributes: list[str] = []
metadata_elements = 0
⋮----
tag = _local_name(element.tag)
⋮----
local_key = _local_name(key)
⋮----
maximum_depth = _max_depth(root)
⋮----
info = {
⋮----
def validate_svg_profile(path: Path, profile: str) -> tuple[dict, list[str], list[str]]
⋮----
profile_data = load_vector_profile(profile)
⋮----
rules = profile_data["rules"]
view_box_values = info.get("viewBoxValues")
⋮----
def normalize_viewbox(input_path: Path, output_path: Path) -> dict
⋮----
raw = input_path.read_text(encoding="utf-8")
⋮----
existing_viewbox = root.attrib.get("viewBox")
current = _parse_viewbox(existing_viewbox)
changed = False
⋮----
width = _parse_length(root.attrib.get("width"))
height = _parse_length(root.attrib.get("height"))
⋮----
changed = True
⋮----
depth = _max_depth(root)
⋮----
element_count = sum(1 for _ in root.iter())
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
handoff = None
godot_validation = None
⋮----
delivery_report = _read_json_if_exists(workdir / "godot4-delivery.json")
⋮----
handoff = prepare_godot_handoff(
godot_validation = validate_godot_handoff(Path(handoff["projectDir"]))
⋮----
godot_validation = {
⋮----
summary = _build_production_summary(plan, success, results)
⋮----
report_path = Path(plan["workdir"]) / "production-report.json"
````
