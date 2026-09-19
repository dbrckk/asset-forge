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
    semantic-refresh.yml
    validate.yml
config/
  tooling.json
examples/
  asset-manifest.json
  godot-animations.json
  runtime-atlas.json
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
  runtime-atlas.schema.json
  vector-profile.schema.json
tests/
  runtime_atlas_web.test.mjs
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
  test_raster_backend.py
  test_raster_pack.py
  test_runtime_atlas.py
  test_starlist_bridge.py
  test_svg_tools.py
  test_toolchain_3d.py
web/
  runtime_atlas.mjs
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
raster_backend.py
raster_pack.py
README.md
runtime_atlas.py
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

## File: .github/workflows/semantic-refresh.yml
````yaml
name: Precise semantic refresh

on:
  workflow_dispatch:
  schedule:
    - cron: "23 3 * * 1"

permissions:
  contents: write

concurrency:
  group: semantic-refresh-${{ github.repository }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  semantic:
    uses: dbrckk/repo-brain/.github/workflows/reusable-semantic.yml@main
    with:
      commit_changes: true
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
        run: python -m compileall -q asset_forge.py raster_pack.py raster_backend.py runtime_atlas.py godot_export.py godot_3d_delivery.py godot_handoff.py engine_profile_validation.py asset_profile_validation.py starlist_bridge.py animation_infer.py svg_tools.py gltf_tools.py gltf_quality.py gltf_binary_metrics.py gltf_diagnostics.py blender_adapter.py toolchain_3d.py tests
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
      - name: Validate runtime atlas example
        run: python asset_forge.py validate-runtime-atlas examples/runtime-atlas.json
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Smoke-test web runtime atlas consumer
        run: node tests/runtime_atlas_web.test.mjs
      - name: Smoke-test star-list bridge
        run: python asset_forge.py discover-tools star-list "pixel art sprites atlas" --top 3

  webp-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install optional WebP backend
        run: python -m pip install "Pillow>=12.2,<13"
      - name: Inspect raster backend
        run: python asset_forge.py raster-backend-status
      - name: WebP backend tests
        run: python -m unittest discover -s tests -p "test_raster_backend.py" -v
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

## File: examples/runtime-atlas.json
````json
{
  "format": "asset-forge-runtime-atlas",
  "version": 1,
  "image": "atlas.png",
  "imageSize": {
    "width": 64,
    "height": 64
  },
  "frameCount": 1,
  "capabilities": {
    "trimOffsets": true,
    "clockwise90Rotation": true
  },
  "frames": [
    {
      "index": 0,
      "name": "hero_0.png",
      "atlasRegion": {
        "x": 10,
        "y": 20,
        "width": 6,
        "height": 8
      },
      "uv": {
        "u0": 0.15625,
        "v0": 0.3125,
        "u1": 0.25,
        "v1": 0.4375
      },
      "sourceRegion": {
        "width": 8,
        "height": 6
      },
      "sourceSize": {
        "width": 12,
        "height": 10
      },
      "trimOffset": {
        "x": 2,
        "y": 1
      },
      "rotation": {
        "rotated": true,
        "degreesClockwise": 90
      }
    }
  ],
  "animations": [
    {
      "name": "hero",
      "fps": 8,
      "loop": true,
      "frames": [
        {
          "index": 0,
          "duration": 1
        }
      ],
      "events": [
        {
          "name": "footstep",
          "timeSeconds": 0.05,
          "payload": {
            "foot": "left"
          }
        }
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

## File: schemas/runtime-atlas.schema.json
````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://asset-forge.local/runtime-atlas.schema.json",
  "title": "Asset Forge Runtime Atlas",
  "type": "object",
  "required": ["format", "version", "image", "imageSize", "frameCount", "capabilities", "frames"],
  "additionalProperties": false,
  "properties": {
    "format": {"const": "asset-forge-runtime-atlas"},
    "version": {"const": 1},
    "image": {"type": "string", "minLength": 1},
    "imageSize": {
      "type": "object",
      "required": ["width", "height"],
      "additionalProperties": false,
      "properties": {
        "width": {"type": "integer", "minimum": 1},
        "height": {"type": "integer", "minimum": 1}
      }
    },
    "frameCount": {"type": "integer", "minimum": 1},
    "capabilities": {
      "type": "object",
      "required": ["trimOffsets", "clockwise90Rotation"],
      "additionalProperties": false,
      "properties": {
        "trimOffsets": {"const": true},
        "clockwise90Rotation": {"const": true}
      }
    },
    "animations": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "fps", "loop", "frames"],
        "additionalProperties": false,
        "properties": {
          "name": {"type": "string", "minLength": 1},
          "fps": {"type": "number", "exclusiveMinimum": 0},
          "loop": {"type": "boolean"},
          "frames": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["index", "duration"],
              "additionalProperties": false,
              "properties": {
                "index": {"type": "integer", "minimum": 0},
                "duration": {"type": "number", "exclusiveMinimum": 0}
              }
            }
          },
          "events": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name", "timeSeconds"],
              "additionalProperties": false,
              "properties": {
                "name": {"type": "string", "minLength": 1},
                "timeSeconds": {"type": "number", "minimum": 0},
                "payload": {"type": ["object", "null"]}
              }
            }
          }
        }
      }
    },
    "frames": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["index", "atlasRegion", "uv", "sourceRegion", "sourceSize", "trimOffset", "rotation"],
        "additionalProperties": false,
        "properties": {
          "index": {"type": "integer", "minimum": 0},
          "name": {"type": ["string", "null"]},
          "atlasRegion": {"$ref": "#/$defs/rect"},
          "uv": {
            "type": "object",
            "required": ["u0", "v0", "u1", "v1"],
            "additionalProperties": false,
            "properties": {
              "u0": {"type": "number", "minimum": 0, "maximum": 1},
              "v0": {"type": "number", "minimum": 0, "maximum": 1},
              "u1": {"type": "number", "minimum": 0, "maximum": 1},
              "v1": {"type": "number", "minimum": 0, "maximum": 1}
            }
          },
          "sourceRegion": {"$ref": "#/$defs/size"},
          "sourceSize": {"$ref": "#/$defs/size"},
          "trimOffset": {
            "type": "object",
            "required": ["x", "y"],
            "additionalProperties": false,
            "properties": {
              "x": {"type": "integer", "minimum": 0},
              "y": {"type": "integer", "minimum": 0}
            }
          },
          "rotation": {
            "type": "object",
            "required": ["rotated", "degreesClockwise"],
            "additionalProperties": false,
            "properties": {
              "rotated": {"type": "boolean"},
              "degreesClockwise": {"enum": [0, 90]}
            }
          }
        }
      }
    }
  },
  "$defs": {
    "size": {
      "type": "object",
      "required": ["width", "height"],
      "additionalProperties": false,
      "properties": {
        "width": {"type": "integer", "minimum": 1},
        "height": {"type": "integer", "minimum": 1}
      }
    },
    "rect": {
      "type": "object",
      "required": ["x", "y", "width", "height"],
      "additionalProperties": false,
      "properties": {
        "x": {"type": "integer", "minimum": 0},
        "y": {"type": "integer", "minimum": 0},
        "width": {"type": "integer", "minimum": 1},
        "height": {"type": "integer", "minimum": 1}
      }
    }
  }
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

## File: tests/runtime_atlas_web.test.mjs
````javascript
save()
restore()
translate(x, y)
rotate(angle)
drawImage(...args)
⋮----
translate(...args)
rotate(...args)
⋮----
onFrame(sample)
onFinish(sample)
⋮----
onLoop(event)
⋮----
onEvent(event)
⋮----
function createMockWebGL2()
⋮----
const object = (type) => (
⋮----
createShader(type)
shaderSource(shader, source)
compileShader(shader)
getShaderParameter(shader, parameter)
getShaderInfoLog()
deleteShader(shader)
createProgram()
attachShader(program, shader)
linkProgram(program)
getProgramParameter(program, parameter)
getProgramInfoLog()
deleteProgram(program)
createVertexArray()
deleteVertexArray(vao)
createBuffer()
createTexture()
deleteTexture(texture)
deleteBuffer(buffer)
bindVertexArray(vao)
bindBuffer(target, buffer)
bufferData(target, data, usage)
bufferSubData(target, offset, data)
enableVertexAttribArray(location)
vertexAttribPointer(location, size, type, normalized, stride, offset)
vertexAttribDivisor(location, divisor)
getUniformLocation(program, name)
enable(capability)
blendFunc(source, destination)
useProgram(program)
uniform2f(location, x, y)
activeTexture(texture)
bindTexture(target, texture)
pixelStorei(parameter, value)
texParameteri(target, parameter, value)
texImage2D(...args)
generateMipmap(target)
uniform1i(location, value)
drawElementsInstanced(mode, count, type, offset, instances)
⋮----
resolveTexture(textureKey, entry)
⋮----
const fakeFetch = async (url) =>
⋮----
async blob()
⋮----
const fakeCreateImageBitmap = async (blob, options) =>
⋮----
fetchImpl: async () => (
⋮----
fetchImpl: async (url) =>
createImageBitmapImpl: async (blob) => (
⋮----
fetchImpl: async (url) => (
⋮----
function createMockCanvas()
⋮----
addEventListener(type, handler)
removeEventListener(type, handler)
dispatch(type, event =
getContext()
⋮----
resizeGl.viewport = (...args)
⋮----
contextGlA.viewport = (...args)
⋮----
contextGlB.viewport = (...args)
⋮----
onContextLost()
onContextRestored()
⋮----
preventDefault()
⋮----
entityRuntimeGlA.viewport = (...args)
⋮----
entityRuntimeGlB.viewport = (...args)
⋮----
suppliedRuntimeGl.viewport = (...args)
⋮----
onFrame(event)
⋮----
animatedRuntimeGlA.viewport = (...args)
⋮----
animatedRuntimeGlB.viewport = (...args)
⋮----
hierarchyRuntimeGl.viewport = (...args)
⋮----
layerRuntimeGl.viewport = (...args)
⋮----
cameraRuntimeGl.viewport = (...args)
⋮----
followRuntimeGl.viewport = (...args)
⋮----
boundedRuntimeGl.viewport = (...args)
⋮----
pickingRuntimeGl.viewport = (...args)
⋮----
pick(x, y)
toWorld(x, y)
onEnter(event)
onLeave(event)
onDown(event)
onClick(event)
onDragStart(event)
onDrag(event)
onDragEnd(event)
onUp(event)
⋮----
pick()
⋮----
pointerRuntimeGl.viewport = (...args)
⋮----
autoDragGl.viewport = (...args)
⋮----
createImageBitmapImpl: async () => (
⋮----
constrainedDragGl.viewport = (...args)
⋮----
onChange(event)
⋮----
selectionRuntimeGl.viewport = (...args)
⋮----
groupDragGl.viewport = (...args)
⋮----
historyRuntimeGl.viewport = (...args)
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
def test_webp_raster_validation_supports_dimensions_and_alpha(self)
⋮----
vp8x = bytes([0x10, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
chunks = (
body = b"WEBP" + chunks
data = b"RIFF" + struct.pack("<I", len(body)) + body
⋮----
image = Path(tmp) / "sprite.webp"
⋮----
def test_webp_max_colors_constraint_is_rejected(self)
⋮----
width = height = 32
vp8x = bytes([0, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
⋮----
def test_raster_target_format_mismatch_is_reported(self)
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
def test_data_uri_webp_dimensions_use_shared_inspector(self)
⋮----
bits = (width - 1) | ((height - 1) << 14)
vp8l = b"\x2f" + bits.to_bytes(4, "little")
chunk_bytes = b"VP8L" + struct.pack("<I", len(vp8l)) + vp8l + b"\x00"
body = b"WEBP" + chunk_bytes
payload = b"RIFF" + struct.pack("<I", len(body)) + body
uri = "data:image/webp;base64," + base64.b64encode(payload).decode("ascii")
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
def test_trimmed_frame_emits_atlas_margin(self)
⋮----
metadata = {
rendered = render_spriteframes("res://atlas.png", metadata)
⋮----
def test_untrimmed_frame_does_not_emit_margin(self)
⋮----
rendered = render_spriteframes("res://atlas.png", self.metadata())
⋮----
def test_rejects_trim_metadata_that_does_not_fit_source(self)
⋮----
def test_rejects_frame_outside_known_atlas_bounds(self)
⋮----
def test_rejects_rotated_atlas_frame(self)
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

## File: tests/test_raster_backend.py
````python
class RasterBackendTests(unittest.TestCase)
⋮----
def test_backend_status_shape(self)
⋮----
status = detect_pillow_webp()
⋮----
def test_missing_backend_returns_clear_error(self)
⋮----
path = Path(tmp) / "image.webp"
⋮----
def test_real_webp_lossless_decode_to_rgba(self)
⋮----
image = Image.new("RGBA", (2, 1))
⋮----
def test_pack_atlas_accepts_mixed_png_and_webp(self)
⋮----
root = Path(tmp)
png = root / "a.png"
webp = root / "b.webp"
atlas = root / "atlas.png"
⋮----
image = Image.new("RGBA", (1, 1), (0, 255, 0, 255))
⋮----
report = pack_uniform_atlas([png, webp], atlas, columns=2)
⋮----
def test_animated_webp_is_rejected_for_atlas_decode(self)
⋮----
path = Path(tmp) / "animated.webp"
first = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
second = Image.new("RGBA", (1, 1), (0, 255, 0, 255))
⋮----
def test_webp_encoder_validates_quality_and_method_without_backend(self)
⋮----
output = Path(tmp) / "x.webp"
⋮----
def test_encode_webp_lossless_roundtrip(self)
⋮----
source = root / "source.png"
output = root / "output.webp"
pixels = bytes([
⋮----
report = encode_webp(source, output, lossless=True, quality=100, method=6)
⋮----
info = inspect_webp(output)
````

## File: tests/test_raster_pack.py
````python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
⋮----
def webp_chunk(kind: bytes, payload: bytes) -> bytes
⋮----
padding = b"\x00" if len(payload) & 1 else b""
⋮----
def webp_file(*chunks: bytes) -> bytes
⋮----
body = b"WEBP" + b"".join(chunks)
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
ADAM7_PASSES = (
⋮----
def adam7_extent(size: int, start: int, step: int) -> int
⋮----
def pack_indexed_samples(samples: list[int], depth: int) -> bytes
⋮----
per_byte = 8 // depth
output = bytearray()
⋮----
byte = 0
group = samples[start : start + per_byte]
⋮----
shift = 8 - depth * (index + 1)
⋮----
raw = bytearray()
⋮----
pass_width = adam7_extent(width, x_start, x_step)
pass_height = adam7_extent(height, y_start, y_step)
⋮----
y = y_start + py * y_step
⋮----
x = x_start + px * x_step
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
⋮----
def test_grayscale_1bit_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "gray1.png"
ihdr = struct.pack(">IIBBBBB", 8, 1, 1, 0, 0, 0, 0)
⋮----
def test_grayscale_2bit_png_scales_samples(self)
⋮----
image = Path(tmp) / "gray2.png"
ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 0, 0, 0, 0)
⋮----
def test_grayscale_4bit_png_ignores_padding_nibble(self)
⋮----
image = Path(tmp) / "gray4.png"
ihdr = struct.pack(">IIBBBBB", 3, 1, 4, 0, 0, 0, 0)
raw = b"\x00" + bytes([0x05, 0xAF])
⋮----
def test_grayscale_low_bit_depth_trns_is_applied_before_scaling(self)
⋮----
image = Path(tmp) / "gray2-trns.png"
⋮----
transparency = struct.pack(">H", 2)
⋮----
def test_grayscale_trns_out_of_range_is_rejected(self)
⋮----
image = Path(tmp) / "gray2-bad-trns.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 2, 0, 0, 0, 0)
⋮----
def test_grayscale_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "gray16.png"
ihdr = struct.pack(">IIBBBBB", 3, 1, 16, 0, 0, 0, 0)
raw = b"\x00" + struct.pack(">HHH", 0, 32768, 65535)
⋮----
def test_truecolor_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "rgb16.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0)
raw = b"\x00" + struct.pack(">HHH", 65535, 32768, 0)
⋮----
def test_grayscale_alpha_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "gray-alpha16.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 4, 0, 0, 0)
raw = b"\x00" + struct.pack(">HH", 32768, 16384)
⋮----
def test_rgba_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "rgba16.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 6, 0, 0, 0)
raw = b"\x00" + struct.pack(">HHHH", 65535, 32768, 0, 16384)
⋮----
def test_grayscale_16bit_trns_compares_original_sample(self)
⋮----
image = Path(tmp) / "gray16-trns.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 0, 0, 0, 0)
sample = 40000
⋮----
expected_gray = (sample * 255 + 32767) // 65535
⋮----
def test_truecolor_16bit_trns_compares_original_samples(self)
⋮----
image = Path(tmp) / "rgb16-trns.png"
⋮----
samples = (1000, 2000, 3000)
⋮----
expected = [
⋮----
def test_truecolor_8bit_trns_out_of_range_is_rejected(self)
⋮----
image = Path(tmp) / "rgb8-bad-trns.png"
⋮----
def test_adam7_rgba8_reconstructs_full_image(self)
⋮----
image = Path(tmp) / "adam7-rgba.png"
width = height = 8
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 1)
⋮----
def pixel(x, y)
⋮----
raw = adam7_raw(width, height, pixel)
⋮----
def test_adam7_indexed_1bit_reconstructs_checkerboard(self)
⋮----
image = Path(tmp) / "adam7-indexed.png"
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 1, 3, 0, 0, 1)
⋮----
samples = [
⋮----
start = (y * width + x) * 4
expected = 255 if (x + y) % 2 else 0
⋮----
def test_adam7_rgba16_reconstructs_and_downconverts(self)
⋮----
image = Path(tmp) / "adam7-rgba16.png"
width = height = 5
ihdr = struct.pack(">IIBBBBB", width, height, 16, 6, 0, 0, 1)
⋮----
def pixel16(x, y)
⋮----
raw = adam7_raw(width, height, pixel16)
⋮----
expected16 = (x * 10000, y * 12000, (x + y) * 7000, 65535)
expected = bytes([
⋮----
def test_adam7_expected_size_is_bounded_and_exact(self)
⋮----
image = Path(tmp) / "adam7-truncated.png"
⋮----
raw = adam7_raw(width, height, lambda x, y: bytes([x, y, 0, 255]))
⋮----
def test_webp_vp8x_dimensions_alpha_and_animation(self)
⋮----
payload = bytes([0x12, 0, 0, 0]) + (319).to_bytes(3, "little") + (199).to_bytes(3, "little")
anmf = b"\x00" * 16
data = webp_file(
info = inspect_webp_bytes(data)
⋮----
def test_webp_vp8l_dimensions_and_alpha(self)
⋮----
bits = (width - 1) | ((height - 1) << 14) | (1 << 28)
payload = b"\x2f" + bits.to_bytes(4, "little")
data = webp_file(webp_chunk(b"VP8L", payload))
⋮----
def test_webp_vp8_lossy_dimensions(self)
⋮----
frame_tag = (0).to_bytes(3, "little")
payload = (
data = webp_file(webp_chunk(b"VP8 ", payload))
⋮----
def test_webp_alpha_chunk_marks_alpha(self)
⋮----
vp8 = (
vp8x = bytes([0, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
⋮----
def test_webp_incomplete_vp8x_is_rejected(self)
⋮----
payload = bytes([0, 0, 0, 0]) + (9).to_bytes(3, "little") + (9).to_bytes(3, "little")
data = webp_file(webp_chunk(b"VP8X", payload))
⋮----
def test_webp_reserved_vp8x_bits_are_rejected(self)
⋮----
payload = bytes([0x01, 0, 0, 0]) + (9).to_bytes(3, "little") + (9).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + (10).to_bytes(2, "little") + (10).to_bytes(2, "little")
data = webp_file(webp_chunk(b"VP8X", payload), webp_chunk(b"VP8 ", vp8))
⋮----
def test_webp_vp8x_dimension_mismatch_is_rejected(self)
⋮----
vp8x = bytes([0, 0, 0, 0]) + (19).to_bytes(3, "little") + (9).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + (21).to_bytes(2, "little") + (10).to_bytes(2, "little")
data = webp_file(webp_chunk(b"VP8X", vp8x), webp_chunk(b"VP8 ", vp8))
⋮----
def test_webp_lossy_alpha_flag_requires_alph_chunk(self)
⋮----
vp8x = bytes([0x10, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
⋮----
def test_webp_bad_riff_size_is_rejected(self)
⋮----
data = bytearray(webp_file(webp_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")))
⋮----
def test_webp_file_inspection_reads_from_path(self)
⋮----
path = Path(tmp) / "image.webp"
⋮----
bits = (width - 1) | ((height - 1) << 14)
⋮----
info = inspect_webp(path)
⋮----
def test_uniform_atlas_trim_records_source_offsets(self)
⋮----
pixels = bytearray(4 * 4 * 4)
⋮----
start = (y * 4 + x) * 4
⋮----
def test_uniform_atlas_extrudes_edge_pixels(self)
⋮----
source = root / "a.png"
⋮----
expected = bytes([7, 8, 9, 255])
⋮----
start = (y * 3 + x) * 4
⋮----
def test_compact_atlas_packs_variable_size_frames(self)
⋮----
a = root / "a.png"
b = root / "b.png"
c = root / "c.png"
⋮----
metadata = pack_compact_atlas(
⋮----
start = (frame["y"] * width + frame["x"]) * 4
⋮----
def test_compact_atlas_rejects_frame_wider_than_budget(self)
⋮----
source = root / "wide.png"
⋮----
def test_recompress_png_keeps_original_when_candidate_is_larger(self)
⋮----
output = root / "output.png"
⋮----
original = source.read_bytes()
⋮----
report = recompress_png(source, output)
⋮----
result = output.read_bytes()
⋮----
def test_uniform_atlas_width_budget_is_enforced(self)
⋮----
def test_uniform_atlas_pixel_budget_is_enforced(self)
⋮----
def test_compact_atlas_height_budget_is_enforced(self)
⋮----
def test_atlas_byte_budget_preserves_existing_output(self)
⋮----
output = root / "atlas.png"
⋮----
preserved = output.read_bytes()
⋮----
def test_compact_atlas_reports_occupancy_metrics(self)
⋮----
def test_compact_atlas_regions_do_not_overlap(self)
⋮----
paths = []
⋮----
path = root / f"{index}.png"
⋮----
frames = metadata["frames"]
⋮----
first_left = first["x"] - first["extrude"]
first_top = first["y"] - first["extrude"]
first_right = first["x"] + first["width"] + first["extrude"]
first_bottom = first["y"] + first["height"] + first["extrude"]
⋮----
second_left = second["x"] - second["extrude"]
second_top = second["y"] - second["extrude"]
second_right = second["x"] + second["width"] + second["extrude"]
second_bottom = second["y"] + second["height"] + second["extrude"]
separated = (
⋮----
def test_maxrects_compacts_better_than_simple_shelf_case(self)
⋮----
sizes = [(6, 2), (4, 4), (2, 4), (2, 2)]
⋮----
simple_shelf_area = 8 * 8
⋮----
def test_compact_atlas_reports_wasted_pixels(self)
⋮----
def test_compact_atlas_minimum_occupancy_can_fail_build(self)
⋮----
def test_compact_atlas_rejects_invalid_occupancy_threshold(self)
⋮----
def test_compact_atlas_auto_selects_best_evaluated_heuristic(self)
⋮----
sizes = [(7, 2), (5, 4), (4, 3), (3, 6), (2, 5), (2, 2)]
⋮----
evaluated = metadata["evaluatedHeuristics"]
⋮----
best = min(
⋮----
def test_compact_atlas_auto_skips_heuristic_outside_byte_budget(self)
⋮----
baseline = pack_compact_atlas(
evaluated = sorted(
⋮----
budget = evaluated[-1]["encodedBytes"] - 1
constrained = pack_compact_atlas(
selected = next(
⋮----
def test_compact_atlas_forced_heuristic_is_respected(self)
⋮----
def test_compact_atlas_rejects_unknown_heuristic(self)
⋮----
def test_compact_atlas_rotation_can_fit_frame_that_is_too_wide(self)
⋮----
pixels = bytes([
⋮----
frame = metadata["frames"][0]
⋮----
def test_compact_atlas_rotation_is_disabled_by_default(self)
⋮----
def test_compact_atlas_rotation_metadata_counts_rotated_frames(self)
````

## File: tests/test_runtime_atlas.py
````python
class RuntimeAtlasTests(unittest.TestCase)
⋮----
def test_exports_trim_and_rotation_semantics(self)
⋮----
metadata = {
⋮----
result = build_runtime_atlas(metadata)
frame = result["frames"][0]
⋮----
def test_defaults_non_rotated_source_region(self)
⋮----
frame = build_runtime_atlas(metadata)["frames"][0]
⋮----
def test_rejects_rotation_dimension_mismatch(self)
⋮----
def test_rejects_source_trim_out_of_bounds(self)
⋮----
def test_rejects_duplicate_indices(self)
⋮----
def test_validator_accepts_generated_runtime_atlas(self)
⋮----
source = {
runtime = build_runtime_atlas(source)
⋮----
def test_validator_detects_uv_drift(self)
⋮----
errors = validate_runtime_atlas(runtime)
⋮----
def test_validator_detects_frame_count_mismatch(self)
⋮----
def test_validator_rejects_unknown_fields(self)
⋮----
def test_validator_rejects_boolean_integer_fields(self)
⋮----
def test_validator_rejects_unknown_nested_fields(self)
⋮----
def test_build_runtime_atlas_normalizes_animations(self)
⋮----
runtime = build_runtime_atlas(
⋮----
def test_build_runtime_atlas_rejects_missing_animation_frame(self)
⋮----
def test_validator_rejects_animation_frame_reference_drift(self)
⋮----
def test_validator_rejects_duplicate_animation_names(self)
⋮----
def test_build_runtime_atlas_normalizes_animation_events(self)
⋮----
def test_build_runtime_atlas_rejects_event_at_animation_end(self)
⋮----
def test_validator_rejects_unsorted_animation_events(self)
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

## File: web/runtime_atlas.mjs
````javascript
export function indexRuntimeAtlas(atlas)
⋮----
frame(indexOrName)
animation(name)
⋮----
export function frameQuad(frame)
⋮----
export function drawFrameCanvas2D(
  ctx,
  image,
  frame,
  destinationX = 0,
  destinationY = 0,
  options = {},
)
⋮----
// Atlas pixels are stored 90° clockwise. Rotate the destination context
// 90° counter-clockwise so the sprite is restored to source orientation.
⋮----
export function sourceOrientedUVs(frame)
⋮----
// Return UVs in source-orientation vertex order:
// top-left, top-right, bottom-right, bottom-left.
⋮----
export function animationFrameAtTime(indexedAtlas, animationOrName, timeSeconds)
⋮----
export function animationDurationSeconds(animation)
⋮----
export function animationEventsBetween(animation, startTimeSeconds, endTimeSeconds)
⋮----
const includeOccurrence = (event, absoluteTimeSeconds, loopCount, eventIndex) =>
⋮----
export function createAnimationPlayer(indexedAtlas, animationName, options =
⋮----
function emit(sample)
⋮----
function sample()
⋮----
get animation()
get timeSeconds()
get playing()
get playbackRate()
play()
pause()
seek(nextTimeSeconds)
setPlaybackRate(rate)
⋮----
update(deltaSeconds)
⋮----
export function drawAnimationPlayerCanvas2D(
  ctx,
  image,
  player,
  destinationX = 0,
  destinationY = 0,
  options = {},
)
⋮----
export function buildSpriteBatch(indexedAtlas, instances, options =
⋮----
export function drawSpriteBatchCanvas2D(ctx, image, indexedAtlas, instances)
⋮----
export function buildInstancedSpriteBatch(indexedAtlas, instances, options =
⋮----
// Per instance:
// visibleX, visibleY, visibleWidth, visibleHeight,
// u0, v0, u1, v1,
// atlasRotationFlag, sourceWidth, sourceHeight, spriteRotationRadians,
// pivotWorldX, pivotWorldY, reserved0, reserved1,
// tintR, tintG, tintB, alpha
⋮----
export function instancedSpriteUV(
  u0,
  v0,
  u1,
  v1,
  rotationFlag,
  unitX,
  unitY,
)
⋮----
// Packed texture is 90° clockwise. Convert source-oriented unit coords
// to stored atlas UV coordinates.
⋮----
export function instancedSpriteWebGL2Shaders()
⋮----
export function instancedSpriteAttributeViews(batch)
⋮----
export function createRuntimeAtlasPages(pages)
⋮----
page(id)
⋮----
export function buildTexturePageBatches(
  atlasPages,
  instances,
  options = {},
)
⋮----
function _compileWebGL2Shader(gl, type, source)
⋮----
function _linkWebGL2Program(gl, vertexSource, fragmentSource)
⋮----
export function createInstancedSpriteRendererWebGL2(gl, options =
⋮----
frame()
⋮----
function assertActive()
⋮----
function renderBatch(batch, texture, viewportWidth, viewportHeight)
⋮----
function renderPageBatches(pageBatches, viewportWidth, viewportHeight)
⋮----
function dispose()
⋮----
get disposed()
get uploadedCapacityBytes()
get alphaBlending()
⋮----
export function createWebGL2TextureCache(gl, options =
⋮----
function createTextureFromSource(source, textureOptions =
⋮----
function acquire(key, source, textureOptions =
⋮----
async function load(key, sourceOrFactory, textureOptions =
⋮----
function get(key)
⋮----
function has(key)
⋮----
function references(key)
⋮----
function release(key)
⋮----
function deleteTexture(key)
⋮----
function clear()
⋮----
get size()
get pendingCount()
⋮----
export async function loadImageBitmapSource(url, options =
⋮----
export async function preloadRuntimeAtlasPageTextures(
  atlasPages,
  textureCache,
  options = {},
)
⋮----
export function releaseRuntimeAtlasPageTextures(textureCache, preloadResult)
⋮----
export async function createWebGL2RuntimeAtlasScene(
  gl,
  pageDefinitions,
  options = {},
)
⋮----
resolveTexture(textureKey)
⋮----
buildBatches(instances, batchOptions =
render(instancesOrBatches, viewportWidth, viewportHeight, batchOptions =
dispose()
⋮----
export function spriteInstanceBounds(atlasPages, instance)
⋮----
function rotatedAabb(rx, ry, rw, rh)
⋮----
export function cullSpriteInstances(
  atlasPages,
  instances,
  viewport,
  options = {},
)
⋮----
export function stableSortSpriteInstances(instances, options =
⋮----
export function prepareSpriteSceneInstances(
  atlasPages,
  instances,
  options = {},
)
⋮----
export function resizeWebGL2Canvas(canvas, gl, options =
⋮----
export async function createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  options = {},
)
⋮----
function resize(resizeOptions =
⋮----
function clampRuntimeCamera(nextCamera)
⋮----
function pickRuntimeEntity(x, y, pickOptions =
⋮----
toWorld: (x, y)
onDrag(event)
⋮----
async function rebuildAfterContextRestore()
⋮----
function handleContextLost(event)
⋮----
function handleContextRestored()
⋮----
get visibilityMask()
setVisibilityMask(nextMask)
get camera()
get worldBounds()
⋮----
setWorldBounds(nextBounds)
setCamera(nextCamera =
updateCameraFollow(targetX, targetY, deltaSeconds)
updateCameraFollowEntity(entityId, deltaSeconds, followOptions =
shakeCamera(amplitude, durationSeconds, frequency)
clearCameraShake()
get gl()
get scene()
get contextLost()
get restoring()
⋮----
async waitForRestore()
⋮----
buildEntityBatches(batchOptions =
updateAnimations(deltaSeconds)
render(instancesOrBatches, batchOptions =
renderEntities(batchOptions =
screenToWorld(x, y)
worldToScreen(x, y, parallax =
pickEntity(x, y, pickOptions =
⋮----
selectEntity(entityId, selectOptions =
clearSelection()
duplicateSelection(duplicateOptions =
copySelection(copyOptions =
pasteEntities(clipboard, pasteOptions =
reparentEntity(entityId, parentId = null, reparentOptions =
removeEntity(entityId, removeOptions =
removeSelection(removeOptions =
undo()
redo()
selectEntitiesInRect(rect, selectOptions =
moveEntityByWorldDelta(entityId, deltaX, deltaY, moveOptions =
transformSelection(transformOptions =
moveSelectionByWorldDelta(deltaX, deltaY, moveOptions =
pointerMove(pointerId, x, y, pickOptions =
pointerDown(pointerId, x, y, pickOptions =
pointerUp(pointerId, x, y, pickOptions =
pointerCancel(pointerId)
async restore()
⋮----
export function createSpriteEntityStore(options =
⋮----
function normalizeId(id)
⋮----
function validateEntity(entity, label = "sprite entity")
⋮----
function cloneEntity(entity)
⋮----
function add(entity)
⋮----
function get(id)
⋮----
function has(id)
⋮----
function update(id, patch)
⋮----
function remove(id)
⋮----
function snapshot(options =
⋮----
function instances(options =
⋮----
function transact(callback)
⋮----
get version()
⋮----
export function duplicateSpriteEntities(
  entityStore,
  entityIds,
  options = {},
)
⋮----
export function copySpriteEntities(
  entityStore,
  entityIds,
  options = {},
)
⋮----
export function pasteSpriteEntities(
  entityStore,
  clipboard,
  options = {},
)
⋮----
export function reparentSpriteEntity(
  entityStore,
  entityId,
  parentId = null,
  options = {},
)
⋮----
export function removeSpriteEntityHierarchy(
  entityStore,
  entityId,
  options = {},
)
⋮----
const visit = (id) =>
⋮----
export function createSpriteEntityHistory(
  entityStore,
  options = {},
)
⋮----
const capture = () => entityStore.snapshot(
⋮----
function sameSnapshot(a, b)
⋮----
function restore(snapshot)
⋮----
function push(entry)
⋮----
begin(label = "edit")
commit()
cancel()
record(label, callback)
⋮----
clear()
get canUndo()
get canRedo()
get undoCount()
get redoCount()
get active()
⋮----
export function createSpriteAnimationSystem(
  atlasPages,
  entityStore,
  options = {},
)
⋮----
function ensureEntity(entityId)
⋮----
function bind(entityId, animationName, bindOptions =
⋮----
onFrame(sample)
onEvent(event)
onLoop(event)
onFinish(sample)
⋮----
seek(timeSeconds)
⋮----
sample()
⋮----
function get(entityId)
⋮----
function unbind(entityId)
⋮----
function update(deltaSeconds)
⋮----
function _stableSceneCacheKey(value, seen = new Set())
⋮----
export function createSpriteEntityBatchCache(
  runtimeScene,
  entityStore,
  options = {},
)
⋮----
function invalidate()
⋮----
function ensureVersion()
⋮----
function build(batchOptions =
⋮----
get stats()
⋮----
export function resolveSpriteEntityHierarchy(entityStore, options =
⋮----
function resolve(entity)
⋮----
export function applyCameraToSpriteInstances(
  instances,
  camera = {},
)
⋮----
export function filterSpriteInstancesByLayer(
  instances,
  visibilityMask = 0xffffffff,
)
⋮----
function _splitEntityHierarchyOptions(batchOptions =
⋮----
export function buildSpriteEntityInstances(entityStore, batchOptions =
⋮----
export function clampCameraToWorldBounds(
  camera,
  worldBounds,
  viewportWidth,
  viewportHeight,
)
⋮----
function clampAxis(value, min, size, visibleSize)
⋮----
export function createCamera2DController(initialCamera =
⋮----
function baseCamera()
⋮----
function shakenCamera()
⋮----
function update(targetX, targetY, deltaSeconds)
⋮----
function setCamera(nextCamera =
⋮----
function shake(amplitude, durationSeconds, frequency = 24)
⋮----
function clearShake()
⋮----
get baseCamera()
get shaking()
⋮----
export function worldToScreenPoint(x, y, camera =
⋮----
export function screenToWorldPoint(x, y, camera =
⋮----
export function pointHitsSpriteInstance(
  atlasPages,
  instance,
  pointX,
  pointY,
  options = {},
)
⋮----
export function pickSpriteInstances(
  atlasPages,
  instances,
  pointX,
  pointY,
  options = {},
)
⋮----
export function moveSpriteEntityByWorldDelta(
  entityStore,
  entityId,
  deltaX,
  deltaY,
  options = {},
)
⋮----
export function createSpritePointerInteractionController(options =
⋮----
function validatePointer(pointerId, x, y)
⋮----
function pickedEntity(hit)
⋮----
function makeEvent(type, state, hit, x, y, extra =
⋮----
function updateHover(state, hit, x, y)
⋮----
function move(pointerId, x, y, pickOptions =
⋮----
function down(pointerId, x, y, pickOptions =
⋮----
function up(pointerId, x, y, pickOptions =
⋮----
function cancel(pointerId)
⋮----
get hoverEntityId()
get activePointerCount()
pointerState(pointerId)
⋮----
export function transformSelectedSpriteEntities(
  entityStore,
  selectionModel,
  transform = {},
)
⋮----
export function moveSelectedSpriteEntitiesByWorldDelta(
  entityStore,
  selectionModel,
  deltaX,
  deltaY,
  options = {},
)
⋮----
export function createSpriteSelectionModel(options =
⋮----
function emit(reason)
⋮----
function select(entityId, selectOptions =
⋮----
function set(ids)
⋮----
function remove(entityId)
⋮----
has(entityId)
snapshot()
get primaryId()
⋮----
export function selectSpriteInstancesInRect(
  atlasPages,
  instances,
  rect,
  options = {},
)
````

## File: .repo-standards.yml
````yaml
source: dbrckk/repo-standards
ref: main
version: 20
adopted: true
workflow_mode: unified-single-commit
repo_brain: dbrckk/repo-brain@main
repo_brain_fallback: portable-full-rebuild
hotset_fallback: recent-project-state
graph_routing: compact-sharded-reverse-deps
graph_resolver: java-kotlin-tail-v2
graph_enrichment: unique-type-symbol-references-v1
context_budget: confidence-dynamic-3-6-12
routing_learning: deterministic-term-feedback-v1
auto_routing_learning: source-diff-success-v1
validation_memory: passed-failed-test-history-v1
regression_gate: repo-brain-core-tests-v1
benchmark: routing-benchmark-v1
stability_profile: stable-v1
benchmark_guard: avg-files-le-6-cache-required-v1
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
  brain_graph_enrichment: .ai/brain/graph-enrichment.json
  brain_graph_manifest: .ai/brain/graph-manifest.json
  brain_graph_shards: .ai/brain/graph-shards/
  brain_reverse_deps: .ai/brain/reverse-deps.json
  brain_architecture_mermaid: .ai/brain/architecture.mmd
  brain_semantic_plan: .ai/brain/semantic-plan.json
  brain_semantic_index: .ai/brain/semantic-index.json
  brain_search_manifest: .ai/brain/search-manifest.json
  brain_search_shards: .ai/brain/search-shards/
  brain_query_cache: .ai/brain/query-cache.json
  brain_routing_learning: .ai/brain/routing-learning.json
  brain_auto_learning: .ai/brain/auto-learning.json
  brain_validation_memory: .ai/brain/validation-memory.json
  brain_benchmark: .ai/brain/benchmark.json
  brain_benchmark_health: .ai/brain/benchmark-health.json
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
  semantic_refresh: .github/workflows/semantic-refresh.yml
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
"""Dependency-free asset-forge manifest validator, planner, raster inspector, and atlas metadata builder."""
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
info = inspect_raster(path)
constraints = manifest.get("constraints", {}) or {}
grid = sprite_grid(info, constraints)
frames = []
index = 0
⋮----
def validate_raster_file(path: Path, manifest: dict) -> tuple[dict, list[str]]
⋮----
target = manifest.get("target", {})
target_format = str(target.get("format", "")).lower()
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
raster = sub.add_parser("validate-raster", help="validate a PNG or WebP against an asset manifest")
⋮----
atlas = sub.add_parser("atlas-manifest", help="build uniform-grid atlas metadata from PNG or WebP")
⋮----
pack = sub.add_parser("pack-atlas", help="pack equal-size PNG/WebP frames into a PNG atlas")
⋮----
compact = sub.add_parser("pack-atlas-compact", help="pack variable-size PNG/WebP frames into a compact PNG atlas")
⋮----
optimize = sub.add_parser("optimize-png", help="losslessly recompress a supported PNG")
⋮----
webp_encode = sub.add_parser("encode-webp", help="encode PNG or WebP input as WebP via optional Pillow/libwebp")
⋮----
runtime_validate = sub.add_parser("validate-runtime-atlas", help="validate normalized runtime atlas JSON")
⋮----
runtime = sub.add_parser("export-runtime-atlas", help="export normalized rotation-aware runtime atlas JSON")
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
raster_status = sub.add_parser("raster-backend-status", help="detect optional raster pixel backends")
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
metadata = pack_compact_atlas(
⋮----
result = recompress_png(args.input, args.output)
⋮----
result = encode_webp(
⋮----
data = load_json(args.input)
⋮----
errors = validate_runtime_atlas(data)
⋮----
source = load_json(args.metadata)
animations = None
⋮----
animation_config = load_json(args.animations)
animations = animation_config.get("animations")
⋮----
inferred = infer_animations(
animations = inferred.get("animations")
runtime = build_runtime_atlas(source, animations=animations)
⋮----
metadata = load_json(args.metadata)
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
info = inspect_webp_bytes(data)
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
atlas_width = atlas_metadata.get("imageWidth")
atlas_height = atlas_metadata.get("imageHeight")
⋮----
atlas_width = int(atlas_width)
⋮----
atlas_height = int(atlas_height)
⋮----
normalized = []
⋮----
x = int(frame["x"])
y = int(frame["y"])
width = int(frame["width"])
height = int(frame["height"])
⋮----
rotated = bool(frame.get("rotated", False))
⋮----
source_width = int(frame.get("sourceWidth", width))
source_height = int(frame.get("sourceHeight", height))
offset_x = int(frame.get("offsetX", 0))
offset_y = int(frame.get("offsetY", 0))
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
resource_lines = [
extra_width = frame["sourceWidth"] - frame["width"]
extra_height = frame["sourceHeight"] - frame["height"]
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

## File: raster_backend.py
````python
def detect_pillow_webp() -> dict
⋮----
supported = bool(features.check_module("webp"))
⋮----
supported = False
⋮----
webp_version = None
⋮----
webp_version = features.version_module("webp")
⋮----
def decode_webp_rgba(path: Path, *, expected_width: int, expected_height: int) -> tuple[int, int, bytes]
⋮----
status = detect_pillow_webp()
⋮----
rgba = image.convert("RGBA")
pixels = rgba.tobytes()
⋮----
expected_bytes = expected_width * expected_height * 4
⋮----
image = Image.frombytes("RGBA", (width, height), pixels)
````

## File: raster_pack.py
````python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_FILE_BYTES = 256 * 1024 * 1024
MAX_PNG_CHUNK_BYTES = 64 * 1024 * 1024
MAX_PNG_CHUNKS = 10000
MAX_PNG_PIXELS = 100_000_000
MAX_DECOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_WEBP_FILE_BYTES = 256 * 1024 * 1024
MAX_WEBP_CHUNKS = 10000
⋮----
def _read_webp_bytes(path: Path) -> bytes
⋮----
size = path.stat().st_size
⋮----
def _webp_chunks(data: bytes) -> list[tuple[bytes, bytes]]
⋮----
riff_size = struct.unpack("<I", data[4:8])[0]
⋮----
chunks: list[tuple[bytes, bytes]] = []
offset = 12
⋮----
kind = data[offset : offset + 4]
length = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
payload_start = offset + 8
payload_end = payload_start + length
⋮----
offset = payload_end + (length & 1)
⋮----
def _webp_vp8x_info(payload: bytes) -> dict
⋮----
width = 1 + int.from_bytes(payload[4:7], "little")
height = 1 + int.from_bytes(payload[7:10], "little")
⋮----
def _webp_vp8l_info(payload: bytes) -> dict
⋮----
bits = int.from_bytes(payload[1:5], "little")
version = (bits >> 29) & 0x7
⋮----
def _webp_vp8_info(payload: bytes) -> dict
⋮----
frame_tag = int.from_bytes(payload[:3], "little")
⋮----
width = int.from_bytes(payload[6:8], "little") & 0x3FFF
height = int.from_bytes(payload[8:10], "little") & 0x3FFF
⋮----
def inspect_webp_bytes(data: bytes) -> dict
⋮----
chunks = _webp_chunks(data)
by_kind: dict[bytes, list[bytes]] = {}
⋮----
info = _webp_vp8x_info(by_kind[b"VP8X"][0])
⋮----
info = _webp_vp8l_info(by_kind[b"VP8L"][0])
⋮----
info = _webp_vp8_info(by_kind[b"VP8 "][0])
⋮----
image_kinds = [kind for kind in (b"VP8 ", b"VP8L") if kind in by_kind]
⋮----
image_kind = image_kinds[0]
⋮----
image_info = (
⋮----
def inspect_webp(path: Path) -> dict
⋮----
def _read_png_bytes(path: Path) -> bytes
⋮----
def _chunks(data: bytes) -> list[tuple[bytes, bytes]]
⋮----
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
transparent_gray = struct.unpack(">H", payload)[0]
⋮----
transparent_rgb = struct.unpack(">HHH", payload)
max_sample = (1 << depth) - 1
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
def inspect_raster(path: Path) -> dict
⋮----
header = path.read_bytes()[:12]
⋮----
info = inspect_png(path)
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
def _unpack_packed_samples(row: bytes, width: int, depth: int) -> list[int]
⋮----
mask = (1 << depth) - 1
values: list[int] = []
⋮----
shift = 8 - depth
⋮----
def _sample16_to_u8(value: int) -> int
⋮----
ADAM7_PASSES = (
⋮----
def _adam7_extent(size: int, start: int, step: int) -> int
⋮----
rgba = bytearray(width * 4)
destination = 0
⋮----
indexed_samples = _unpack_packed_samples(row, width, depth)
⋮----
alpha = transparency[palette_index] if palette_index < len(transparency) else 255
⋮----
samples = _unpack_packed_samples(row, width, depth)
⋮----
transparent_gray = (
⋮----
gray = (sample * 255 + max_sample // 2) // max_sample
alpha = 0 if transparent_gray == sample else 255
⋮----
channels_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
channels = channels_by_type[color_type]
bpp = channels * 2
⋮----
transparent_rgb = (
⋮----
samples = [
⋮----
gray16 = samples[0]
gray = _sample16_to_u8(gray16)
alpha = 0 if transparent_gray == gray16 else 255
red = green = blue = gray
⋮----
red = _sample16_to_u8(red16)
green = _sample16_to_u8(green16)
blue = _sample16_to_u8(blue16)
alpha = 0 if transparent_rgb == (red16, green16, blue16) else 255
⋮----
alpha = _sample16_to_u8(alpha16)
⋮----
bpp_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
bpp = bpp_by_type[color_type]
⋮----
gray = row[index]
⋮----
alpha = 255
⋮----
transparent_gray = struct.unpack(">H", transparency[:2])[0]
⋮----
alpha = 0
⋮----
rgba = bytearray(width * height * 4)
⋮----
pass_width = _adam7_extent(width, x_start, x_step)
pass_height = _adam7_extent(height, y_start, y_step)
⋮----
pass_size = (stride + 1) * pass_height
end = position + pass_size
⋮----
rows = _unfilter_scanlines(
position = end
⋮----
row_rgba = _decode_row_to_rgba(
target_y = y_start + pass_y * y_step
⋮----
target_x = x_start + pass_x * x_step
source_start = pass_x * 4
target_start = (target_y * width + target_x) * 4
⋮----
def decode_raster_rgba(path: Path) -> tuple[int, int, bytes]
⋮----
suffix = path.suffix.lower()
⋮----
info = inspect_webp(path)
⋮----
raw = path.read_bytes()[:12]
⋮----
def raster_backend_status() -> dict
⋮----
def decode_rgba(path: Path) -> tuple[int, int, bytes]
⋮----
chunks = _chunks(_read_png_bytes(path))
⋮----
compressed = b"".join(payload for kind, payload in chunks if kind == b"IDAT")
⋮----
expected_size = (stride + 1) * height
raw = _decompress_idat(compressed, expected_size)
rows = _unfilter_scanlines(raw, stride, height, filter_bpp)
⋮----
expected_size = 0
⋮----
pixels = _decode_adam7(
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
before = input_path.stat().st_size
⋮----
info = inspect_webp(output_path)
⋮----
after = output_path.stat().st_size
⋮----
def recompress_png(input_path: Path, output_path: Path) -> dict
⋮----
source_bytes = input_path.read_bytes()
⋮----
candidate = _png_bytes_rgba(width, height, pixels, adaptive=True)
⋮----
kept_optimized = len(candidate) < before
⋮----
def _alpha_bounds(width: int, height: int, pixels: bytes) -> tuple[int, int, int, int] | None
⋮----
min_x = width
min_y = height
max_x = -1
max_y = -1
⋮----
alpha = pixels[(y * width + x) * 4 + 3]
⋮----
min_x = min(min_x, x)
min_y = min(min_y, y)
max_x = max(max_x, x)
max_y = max(max_y, y)
⋮----
cropped_width = right - left
cropped_height = bottom - top
cropped = bytearray(cropped_width * cropped_height * 4)
⋮----
source_start = ((top + y) * width + left) * 4
source_end = source_start + cropped_width * 4
destination_start = y * cropped_width * 4
⋮----
source_start = source_y * width * 4
destination_start = ((y + source_y) * atlas_width + x) * 4
⋮----
left_x = x - offset
right_x = x + width - 1 + offset
⋮----
src = ((y + row) * atlas_width + x) * 4
dst = ((y + row) * atlas_width + left_x) * 4
⋮----
src = ((y + row) * atlas_width + x + width - 1) * 4
dst = ((y + row) * atlas_width + right_x) * 4
⋮----
top_y = y - offset
bottom_y = y + height - 1 + offset
⋮----
tx = x + column
⋮----
src_x = min(max(tx, x), x + width - 1)
src = (y * atlas_width + src_x) * 4
dst = (top_y * atlas_width + tx) * 4
⋮----
src = ((y + height - 1) * atlas_width + src_x) * 4
dst = (bottom_y * atlas_width + tx) * 4
⋮----
def _rotate_rgba_clockwise(width: int, height: int, pixels: bytes) -> tuple[int, int, bytes]
⋮----
rotated_width = height
rotated_height = width
rotated = bytearray(rotated_width * rotated_height * 4)
⋮----
source = (y * width + x) * 4
target_x = height - 1 - y
target_y = x
target = (target_y * rotated_width + target_x) * 4
⋮----
def _prepare_frame(path: Path, trim: bool) -> dict
⋮----
bounds = _alpha_bounds(source_width, source_height, pixels)
⋮----
offset_x = offset_y = 0
⋮----
pixels = width * height
⋮----
def _next_power_of_two(value: int) -> int
⋮----
def _rects_intersect(a: dict, b: dict) -> bool
⋮----
def _rect_contains(outer: dict, inner: dict) -> bool
⋮----
def _split_free_rect(free: dict, used: dict) -> list[dict]
⋮----
result = []
free_right = free["x"] + free["width"]
free_bottom = free["y"] + free["height"]
used_right = used["x"] + used["width"]
used_bottom = used["y"] + used["height"]
⋮----
def _prune_free_rects(rects: list[dict]) -> list[dict]
⋮----
pruned = []
⋮----
def _maxrects_score(free: dict, reserve_width: int, reserve_height: int, heuristic: str) -> tuple
⋮----
leftover_w = free["width"] - reserve_width
leftover_h = free["height"] - reserve_height
short_side = min(leftover_w, leftover_h)
long_side = max(leftover_w, leftover_h)
area_fit = free["width"] * free["height"] - reserve_width * reserve_height
⋮----
ordered = sorted(
⋮----
total_height = sum(
free_rects = [
placements: list[dict] = []
⋮----
orientations = [
⋮----
candidates = []
⋮----
packed_width = orientation["width"] + extrude * 2
packed_height = orientation["height"] + extrude * 2
⋮----
reserve_width = packed_width + padding
reserve_height = packed_height + padding
⋮----
free = free_rects[free_index]
⋮----
used = {
⋮----
new_free = []
⋮----
free_rects = _prune_free_rects(new_free)
⋮----
content_width = max(
content_height = max(
⋮----
MAXRECTS_HEURISTICS = (
⋮----
canvas = bytearray(width * height * 4)
⋮----
render_width = frame["width"]
render_height = frame["height"]
render_pixels = frame["pixels"]
⋮----
heuristics = MAXRECTS_HEURISTICS if heuristic == "auto" else (heuristic,)
⋮----
atlas_width = _next_power_of_two(content_width) if power_of_two else content_width
atlas_height = _next_power_of_two(content_height) if power_of_two else content_height
pixels = _render_compact_layout(
png_bytes = _png_bytes_rgba(
budget_errors = []
⋮----
atlas_area = atlas_width * atlas_height
⋮----
eligible = [item for item in candidates if item["withinBudgets"]]
⋮----
details = "; ".join(
⋮----
winner = min(
evaluated = [
⋮----
frames_data = [_prepare_frame(Path(path), trim=trim) for path in inputs]
⋮----
frames = []
⋮----
packed_area = sum(
⋮----
occupancy = packed_area / atlas_area * 100.0
⋮----
output_bytes = len(rendered_png)
⋮----
frame_count = len(frames_data)
column_count = columns or math.ceil(math.sqrt(frame_count))
⋮----
row_count = math.ceil(frame_count / column_count)
cell_width = frame_width + extrude * 2
cell_height = frame_height + extrude * 2
gap = padding
content_width = column_count * cell_width + max(0, column_count - 1) * gap
content_height = row_count * cell_height + max(0, row_count - 1) * gap
⋮----
canvas = bytearray(atlas_width * atlas_height * 4)
⋮----
column = index % column_count
row = index // column_count
cell_x = column * (cell_width + gap)
cell_y = row * (cell_height + gap)
x = cell_x + extrude
y = cell_y + extrude
⋮----
output_bytes = _enforce_atlas_file_budget(output, max_bytes)
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

Validate a PNG or WebP sprite sheet against its manifest:

```bash
python asset_forge.py validate-raster examples/asset-manifest.json path/to/sprite.png
python asset_forge.py validate-raster examples/webp-manifest.json path/to/sprite.webp
```

Generate uniform-grid atlas metadata:

```bash
python asset_forge.py atlas-manifest examples/asset-manifest.json path/to/sprite.png --output build/sprite.atlas.json
```

Pack separate equal-size PNG frames — or PNG/WebP frames when the optional WebP backend is available — into a real PNG atlas plus metadata:

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

The built-in PNG decoder supports the validated PNG depth/color/interlace combinations documented below and implements all five standard PNG scanline filters. Atlas output remains RGBA PNG. Atlas inputs may also be WebP when the optional Pillow/libwebp backend is available; the dependency-free core still handles PNG plus WebP container inspection without Pillow.

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


Low-bit grayscale decoding shares the packed-sample scanline path used by indexed PNGs. Samples are unpacked most-significant bits first, row padding is ignored, values are scaled to 8-bit luminance, and grayscale `tRNS` is matched against the original unscaled sample. Out-of-range `tRNS` samples are rejected.


16-bit PNG decoding is supported for grayscale, RGB, grayscale+alpha, and RGBA. Samples are read big-endian after PNG unfiltering and converted to RGBA8 with deterministic rounding. For grayscale/RGB `tRNS`, transparency matching is performed on the original 16-bit samples before down-conversion, preserving exact transparent-color semantics.


Adam7 decoding computes the exact byte budget for all seven passes before zlib decompression, unfilters each pass independently with that pass's scanline width, converts pass rows through the same bit-depth/color-type conversion path as non-interlaced PNGs, and scatters decoded pixels back into final image coordinates. Empty passes for small images are skipped safely.


### WebP raster inspection

Asset Forge now validates WebP RIFF containers without external dependencies. It understands simple lossy `VP8 `, lossless `VP8L`, and extended `VP8X` headers, reports dimensions/alpha/animation/chunk metadata, validates RIFF length and chunk padding, checks reserved VP8X fields, and cross-checks extended canvas dimensions against static image data. `validate-raster` accepts `target.format=webp` for metadata/grid/size/alpha validation, and glTF texture metrics reuse the same WebP parser.

This milestone is inspection/validation only: WebP pixel decoding, atlas input decoding, recompression, and WebP encoding are not implemented yet. PNG remains the decoded/encoded raster working format.


### Optional WebP pixel backend

The dependency-free core validates WebP containers without decoding their pixels. Pixel decode/encode is enabled when Pillow is installed with libwebp support. Pillow's documented WebP plugin reads and writes WebP, while `PIL.features.check_module("webp")` is used to detect runtime support.

Inspect availability:

```bash
python asset_forge.py raster-backend-status
```

Encode any supported decoded raster input as WebP:

```bash
python asset_forge.py encode-webp source.png build/source.webp
python asset_forge.py encode-webp source.png build/source-lossy.webp --lossy --quality 82 --method 6
```

Lossless is the default. The encoder validates quality `0..100` and method `0..6`, writes through Pillow/libwebp, then re-inspects the WebP container to verify output dimensions. Animated WebP is inspectable but intentionally rejected as a single-frame atlas input.


### Advanced atlas packing

Uniform atlas packing now supports transparent trim and edge extrusion:

```bash
python asset_forge.py pack-atlas build/atlas.png frames/*.png \
  --trim --extrude 1 --padding 1 --metadata build/atlas.json
```

Trim metadata records the original source dimensions plus `offsetX`/`offsetY`, while the stored `x`/`y`/`width`/`height` describe the trimmed atlas region. Edge extrusion duplicates border pixels around the packed region to reduce texture bleeding.

Variable-size sprites can use deterministic shelf packing:

```bash
python asset_forge.py pack-atlas-compact build/atlas.png frames/* \
  --max-width 2048 --padding 1 --extrude 1 --metadata build/atlas.json
```

The compact packer sorts by height/width for placement but restores original input order in metadata. Rotation is intentionally not implemented yet. Consumers that need original untrimmed positioning must use the source dimension/offset metadata; the existing simple Godot SpriteFrames export still consumes atlas regions only.

PNG optimization is now no-growth: `optimize-png` keeps the original bytes whenever the recompressed candidate is not smaller, including in-place optimization.


### Godot export for trimmed atlases

Trimmed atlas metadata is now mapped to Godot 4 `AtlasTexture.margin`. The atlas `region` remains the trimmed rectangle, while `margin = Rect2(offsetX, offsetY, sourceWidth - width, sourceHeight - height)` restores the original logical sprite size. Atlas bounds and trim/source consistency are validated before rendering the `.tres`.

### Atlas budgets

Both atlas packers accept explicit production budgets:

```bash
python asset_forge.py pack-atlas build/atlas.png frames/*.png \
  --max-width 2048 --max-height 2048 \
  --max-pixels 4194304 --max-bytes 8388608

python asset_forge.py pack-atlas-compact build/atlas.png frames/* \
  --max-width 2048 --max-height 2048 \
  --max-pixels 4194304 --max-bytes 8388608
```

Dimension/pixel limits are enforced before canvas allocation. The compressed byte budget is checked against the encoded PNG candidate before replacing the output file, so a failed budget check preserves any existing atlas.


### MaxRects compact packing and occupancy

`pack-atlas-compact` now uses deterministic MaxRects placement with a best-short-side-fit heuristic instead of shelf packing. Rotation remains disabled, so existing atlas consumers keep stable orientation semantics.

Compact atlas metadata reports:

```text
spriteArea
packedArea
contentArea
atlasArea
wastedPixels
contentOccupancyPercent
atlasOccupancyPercent
```

A minimum occupancy can be enforced in CI:

```bash
python asset_forge.py pack-atlas-compact build/atlas.png frames/* \
  --max-width 2048 \
  --min-occupancy 70
```

If final atlas occupancy falls below the requested percentage, packing fails before the output PNG is written.


### Automatic MaxRects heuristic selection

`pack-atlas-compact` now supports:

```text
auto
best-short-side-fit
best-long-side-fit
best-area-fit
```

The default `auto` mode evaluates all three deterministic MaxRects heuristics against the same prepared frames and selects the layout with the smallest content area, then smallest height, then smallest width. This optimizes atlas geometry, not compressed PNG byte size.

Force a specific strategy when reproducibility against a known layout matters:

```bash
python asset_forge.py pack-atlas-compact build/atlas.png frames/* \
  --heuristic best-area-fit
```

Metadata records `requestedHeuristic`, `selectedHeuristic`, and an `evaluatedHeuristics` summary containing width, height, and content area for each evaluated strategy.


### Encoded-size-aware atlas auto selection

Automatic compact-atlas selection now renders each MaxRects candidate in memory and encodes its PNG bytes before choosing a winner. No temporary atlas files are written during comparison.

Selection order is now:

```text
1. smallest encoded PNG byte size
2. smallest final atlas area
3. smallest content area
4. smallest content height
5. smallest content width
6. heuristic name as deterministic tie-break
```

Per-strategy audit metadata now also includes `atlasWidth`, `atlasHeight`, `atlasArea`, `encodedBytes`, `withinBudgets`, and `budgetErrors`.

When `max-height`, `max-pixels`, or `max-bytes` is supplied, `auto` excludes candidates that violate those budgets before selecting the winner. If no heuristic fits, packing fails without replacing the output file. The already-encoded bytes of the winning candidate are reused for the final write, avoiding a second PNG encode.


### Optional compact-atlas rotation

Compact MaxRects packing can now rotate sprites 90° clockwise when explicitly enabled:

```bash
python asset_forge.py pack-atlas-compact build/atlas.png frames/* \
  --allow-rotation
```

Rotation is disabled by default. When enabled, MaxRects evaluates both orientations for non-square frames and may select rotation when it improves fit or allows a frame to satisfy the width budget.

Per-frame metadata records:

```text
rotated
rotationDegrees
sourceRegionWidth
sourceRegionHeight
width
height
```

For rotated frames, `width`/`height` describe the stored atlas region after rotation, while `sourceRegionWidth`/`sourceRegionHeight` describe the trimmed region before rotation. Source canvas dimensions and trim offsets remain in `sourceWidth`, `sourceHeight`, `offsetX`, and `offsetY`.

The current Godot SpriteFrames exporter intentionally rejects rotated frames because Godot `AtlasTexture` regions do not automatically undo packed-image rotation. Use rotation only with consumers that explicitly understand the metadata.


### Rotation-aware runtime atlas export

A generic engine/runtime consumer can now be generated from Asset Forge atlas metadata:

```bash
python asset_forge.py export-runtime-atlas build/atlas.json build/runtime-atlas.json
```

The versioned `asset-forge-runtime-atlas` format is engine-neutral and preserves:

```text
atlasRegion
uv
sourceRegion
sourceSize
trimOffset
rotation
```

For a rotated frame, `atlasRegion` describes the stored 90°-rotated rectangle, `sourceRegion` describes the pre-rotation trimmed sprite, and `rotation.degreesClockwise=90` tells the consumer how to restore orientation. Normalized `u0/v0/u1/v1` coordinates are included for direct texture sampling.

The top-level `capabilities` object declares support for trim offsets and clockwise 90° rotation. The contract is documented in `schemas/runtime-atlas.schema.json`. This export is the rotation-aware alternative to the Godot SpriteFrames exporter, which intentionally rejects rotated regions.


### Runtime atlas validation

Normalized runtime atlas files can be validated independently:

```bash
python asset_forge.py validate-runtime-atlas examples/runtime-atlas.json
```

The dependency-free validator checks the versioned contract plus semantic relationships that JSON Schema alone does not express conveniently, including frame-count consistency, duplicate indices, UVs matching atlas regions, source/trim bounds, and rotation dimensions. Validation is strict about unknown fields and integer types, so booleans are not accepted as integers.

CI validates `examples/runtime-atlas.json` as a smoke test. The example is a rotated + trimmed frame and can be used as a reference implementation for runtime consumers.


### Web runtime consumer

A dependency-free ES module is available at `web/runtime_atlas.mjs`.

Canvas2D example:

```js
import {
  indexRuntimeAtlas,
  drawFrameCanvas2D,
} from "./web/runtime_atlas.mjs";

const atlasData = await fetch("./runtime-atlas.json").then((response) => response.json());
const image = new Image();
image.src = atlasData.image;
await image.decode();

const atlas = indexRuntimeAtlas(atlasData);
const frame = atlas.frame("hero_0.png");
drawFrameCanvas2D(context, image, frame, 32, 48);
```

`drawFrameCanvas2D` restores trim offsets and automatically undoes a stored 90° clockwise atlas rotation before drawing.

For WebGL/custom renderers, `sourceOrientedUVs(frame)` returns UV coordinates in source-vertex order — top-left, top-right, bottom-right, bottom-left — with rotation already accounted for. `frameQuad(frame)` exposes the raw normalized UV rectangle plus source-size/trim/rotation metadata.

The web helper is smoke-tested with Node 22 in CI against the versioned runtime atlas example.


### Runtime animations

Runtime atlas export can now include animations while keeping the base v1 format backward compatible.

Infer groups from frame filenames:

```bash
python asset_forge.py export-runtime-atlas build/atlas.json build/runtime-atlas.json \
  --infer-animations --fps 12
```

Or provide an explicit animation JSON file using the same `animations` structure already accepted by the Godot exporter:

```bash
python asset_forge.py export-runtime-atlas build/atlas.json build/runtime-atlas.json \
  --animations animations.json
```

`--animations` and `--infer-animations` are mutually exclusive. Runtime animations contain `name`, `fps`, `loop`, and normalized frame entries with `index` plus a positive `duration` multiplier. Frame references are validated against the atlas.

The web consumer indexes animations by name and exposes:

```js
const atlas = indexRuntimeAtlas(runtimeAtlas);
const sample = animationFrameAtTime(atlas, "run", elapsedSeconds);
drawFrameCanvas2D(ctx, image, sample.frame, x, y);
```

Looping animations wrap by total duration. Non-looping animations clamp to the final frame and return `finished: true`. Per-frame duration multipliers are interpreted in units of `1 / fps`.


### Runtime animation player controller

The web runtime now provides `createAnimationPlayer()` on top of the pure `animationFrameAtTime()` sampler.

```js
const atlas = indexRuntimeAtlas(runtimeAtlas);
const player = createAnimationPlayer(atlas, "run", {
  autoplay: true,
  playbackRate: 1,
  onFrame(sample) {
    // sample.frame changed
  },
  onLoop(event) {
    // event.loopCount
  },
  onFinish(sample) {
    // non-looping animation reached its final frame
  },
});

// in your game loop:
player.update(deltaSeconds);
drawAnimationPlayerCanvas2D(ctx, image, player, x, y);
```

The controller supports `play()`, `pause()`, `seek(seconds)`, `setPlaybackRate(rate)`, `sample()`, and `update(deltaSeconds)`. It never owns a timer or `requestAnimationFrame`, so timing remains deterministic and controlled by the host game loop.

`onFrame` fires when the sampled frame changes, `onLoop` reports every crossed loop boundary even when a large delta spans multiple loops, and `onFinish` fires once when a non-looping animation completes. Playback rate must remain positive.


### Animation event markers

Runtime animations can attach named timeline markers:

```json
{
  "name": "attack",
  "fps": 12,
  "loop": false,
  "frames": [
    {"index": 0, "duration": 1},
    {"index": 1, "duration": 1}
  ],
  "events": [
    {"name": "windup", "timeSeconds": 0.03},
    {"name": "attack-hit", "timeSeconds": 0.11, "payload": {"damage": 8}}
  ]
}
```

Each marker requires a non-empty `name` and a `timeSeconds` value in the range `0 <= timeSeconds < animationDuration`. An optional `payload` object can carry gameplay/audio metadata. Markers are normalized into ascending timeline order.

The web player accepts `onEvent`:

```js
const player = createAnimationPlayer(atlas, "attack", {
  autoplay: true,
  onEvent(event) {
    if (event.name === "attack-hit") {
      applyDamage(event.payload?.damage ?? 0);
    }
  },
});
```

Events fire only when `update(deltaSeconds)` advances playback; `seek()` and `sample()` do not replay crossed markers. A marker at `timeSeconds: 0` fires on the first positive advance from the start and again at every loop boundary. Large updates emit every crossed marker in deterministic chronological order, including markers from multiple loops. Event dispatch is capped at 10,000 markers per update to guard against pathological deltas.


### Sprite batching for WebGL and Canvas2D

The web runtime now exposes `buildSpriteBatch()` for one-atlas sprite batching.

```js
const batch = buildSpriteBatch(atlas, [
  { frame: "hero_idle_0.png", x: 32, y: 48, scale: 2 },
  { frame: "enemy_0.png", x: 120, y: 48, scaleX: 1.5, scaleY: 1 },
]);
```

The returned vertex buffer is a `Float32Array` with interleaved:

```text
[x, y, u, v]
```

using four source-oriented vertices per sprite in top-left, top-right, bottom-right, bottom-left order. Trim offsets are applied to positions, source-region dimensions define the visible quad, and rotated atlas frames use rotation-correct UV ordering.

Each sprite contributes six triangle indices:

```text
0, 1, 2, 0, 2, 3
```

with the proper per-sprite vertex offset. Index storage automatically uses `Uint16Array` while the vertex count fits 16 bits, then switches to `Uint32Array`. The result reports `indexType`, counts, layout metadata, and logical/visible bounds per instance.

A configurable `maxInstances` guard defaults to 100,000 to prevent accidental pathological allocations.

Canvas2D also has:

```js
drawSpriteBatchCanvas2D(ctx, image, atlas, instances);
```

This is an API convenience rather than a GPU draw-call batch: Canvas2D still issues one `drawImage` per sprite. Non-uniform scale is supported by the WebGL batch builder; the Canvas2D batch helper currently requires uniform scale per sprite.


### WebGL2 instanced sprite contract

For large sprite counts, `buildInstancedSpriteBatch()` avoids duplicating four full vertices per sprite. It stores one shared unit quad plus 12 floats per instance:

```text
visibleX
visibleY
visibleWidth
visibleHeight
u0
v0
u1
v1
rotationFlag
sourceWidth
sourceHeight
reserved
```

The instance buffer is therefore 48 bytes per sprite. The shared unit quad is:

```text
(0,0) (1,0) (1,1) (0,1)
```

with indices `0,1,2,0,2,3`.

`instancedSpriteWebGL2Shaders()` returns reference WebGL2 GLSL ES 3.00 vertex/fragment shader sources plus the expected attribute/uniform contract. The vertex shader handles source-space positioning and packed 90° rotation in UV space; `instancedSpriteAttributeViews()` returns byte offsets/divisors for the instance buffer.

This lets host projects create one static unit-quad VBO, one dynamic instance VBO, and render many sprites with `drawElementsInstanced` while keeping Asset Forge's trim/rotation semantics.


### Multi-atlas texture-page batching

The web runtime can now manage multiple runtime atlases as texture pages:

```js
const pages = createRuntimeAtlasPages([
  { id: "heroes", atlas: heroAtlas, texture: heroTexture },
  { id: "enemies", atlas: enemyAtlas, texture: enemyTexture },
]);

const grouped = buildTexturePageBatches(
  pages,
  [
    { page: "heroes", frame: "idle_0", x: 20, y: 40 },
    { page: "enemies", frame: "slime_0", x: 80, y: 40 },
    { page: "heroes", frame: "idle_1", x: 140, y: 40 },
  ],
  { mode: "instanced" },
);
```

By default, instances are grouped globally by texture page to minimize texture binding changes. Each output batch retains `inputIndices` so the host can relate optimized draw order back to logical instance order. Metrics include `inputTextureSwitches`, `outputTextureSwitches`, and `textureSwitchesSaved`.

When visual layering or blending requires strict submission order, use:

```js
{ preserveOrder: true }
```

In that mode, the runtime emits one batch per contiguous texture-page run instead of merging separated runs. For an input page sequence `A, B, A`, strict-order output remains `A | B | A`; optimized output may become `A,A | B`.

Both `classic` and `instanced` page-batch modes are supported. Page IDs must be unique, and a page may provide either raw runtime-atlas JSON or an already indexed atlas.


### WebGL2 instanced renderer helper

The web runtime now includes `createInstancedSpriteRendererWebGL2(gl, options)`, a dependency-free renderer built on the existing instanced sprite contract.

It creates and owns:

```text
shader program
VAO
static unit-quad vertex buffer
static unit-quad index buffer
dynamic instance buffer
```

Example:

```js
const renderer = createInstancedSpriteRendererWebGL2(gl, {
  resolveTexture(textureKey, pageBatch) {
    return gpuTextures.get(textureKey);
  },
});

const pageBatches = buildTexturePageBatches(pages, instances, {
  mode: "instanced",
});

renderer.renderPageBatches(
  pageBatches,
  canvas.width,
  canvas.height,
);
```

The renderer uploads a larger instance buffer with `bufferData(..., DYNAMIC_DRAW)` only when capacity must grow. Subsequent uploads that fit reuse the allocation through `bufferSubData`.

`renderBatch()` performs one `drawElementsInstanced` call. `renderPageBatches()` performs one draw call per texture-page batch and reports draw calls, rendered instance count, uploaded bytes, and texture switches.

Texture-page catalogues may store actual `WebGLTexture` objects or arbitrary asset keys. The optional `resolveTexture(texture, entry)` callback resolves those keys at render time, keeping GPU resource management separate from atlas metadata.

Call `dispose()` to release the VAO, buffers, and program. Rendering after disposal is rejected explicitly.


### WebGL2 texture cache

The web runtime now includes `createWebGL2TextureCache(gl, options)` for centralized GPU texture lifetime management.

```js
const textures = createWebGL2TextureCache(gl, {
  minFilter: gl.NEAREST,
  magFilter: gl.LINEAR,
  wrapS: gl.CLAMP_TO_EDGE,
  wrapT: gl.CLAMP_TO_EDGE,
  premultiplyAlpha: true,
});

const heroTexture = textures.acquire("hero", heroImageBitmap);
```

Repeated `acquire(key, source)` calls reuse the same `WebGLTexture` and increment a reference count. `release(key)` decrements it and deletes the GPU texture when the count reaches zero.

Asynchronous loads are deduplicated:

```js
const texture = await textures.load("hero", async () => {
  return await createImageBitmap(await fetch("hero.png").then(r => r.blob()));
});
```

If multiple callers request the same key while loading is still in flight, the source factory runs once, one GPU texture is created, and every caller receives the same texture with its own reference count.

Per-texture options can override filtering, wrapping, mipmap generation, and premultiplied-alpha upload behavior. `get()`, `has()`, `references()`, `delete()`, `clear()`, and `dispose()` are provided for explicit lifecycle control.

The cache is designed to plug directly into the renderer:

```js
const renderer = createInstancedSpriteRendererWebGL2(gl, {
  resolveTexture(textureKey) {
    return textures.get(textureKey);
  },
});
```

Disposal during an in-flight asynchronous load causes that load to fail rather than allocating a texture into an already-disposed cache.


### Browser loading and integrated WebGL2 runtime scene

For browser projects, Asset Forge now provides `loadImageBitmapSource()` plus a higher-level scene helper that wires page loading, texture caching, batching, and instanced rendering together.

```js
const scene = await createWebGL2RuntimeAtlasScene(
  gl,
  [
    { id: "heroes", atlas: heroAtlas, texture: "/assets/hero-atlas.png" },
    { id: "enemies", atlas: enemyAtlas, texture: "/assets/enemy-atlas.png" },
  ],
);

scene.render(
  [
    { page: "heroes", frame: "idle_0", x: 32, y: 48 },
    { page: "enemies", frame: "slime_0", x: 120, y: 48 },
  ],
  canvas.width,
  canvas.height,
);
```

`loadImageBitmapSource(url)` uses `fetch` + `createImageBitmap` and accepts injectable implementations for tests, workers, or custom environments.

`preloadRuntimeAtlasPageTextures()` loads every page through the shared texture cache. Pages that reference the same texture key share one network/image/GPU resource while retaining independent references. If any page fails to load, textures already acquired by that preload operation are released in reverse order before the error is rethrown.

`releaseRuntimeAtlasPageTextures()` releases the references acquired by a preload result.

`createWebGL2RuntimeAtlasScene()` owns a page catalogue, texture cache (unless an external cache is supplied), and instanced renderer. It exposes:

```text
scene.pages
scene.textureCache
scene.renderer
scene.buildBatches(instances, options)
scene.render(instancesOrBatches, viewportWidth, viewportHeight, options)
scene.dispose()
```

An internally created texture cache is disposed with the scene. An externally supplied cache remains alive; only references acquired by the scene are released. This allows several scenes to share GPU textures safely.


### Scene culling and stable depth sorting

The runtime scene can now remove off-screen sprites before batching and apply deterministic stable depth sorting.

Low-level helpers:

```js
spriteInstanceBounds(pages, instance)
cullSpriteInstances(pages, instances, viewport, options)
stableSortSpriteInstances(instances, options)
prepareSpriteSceneInstances(pages, instances, options)
```

Example:

```js
const batches = scene.buildBatches(sprites, {
  viewport: {
    x: 0,
    y: 0,
    width: canvas.width,
    height: canvas.height,
  },
  culling: {
    padding: 32,
    useVisibleBounds: true,
  },
  sort: true,
  sortKey: "z",
  sortDirection: "ascending",
  preserveOrder: true,
});
```

Culling uses the runtime atlas frame metadata, including source size, trim offsets, source region, and per-instance scale. By default it tests visible trimmed bounds; `useVisibleBounds: false` switches to full logical source bounds. Optional positive padding expands the viewport to reduce edge pop-in.

Sorting is stable: sprites with equal depth retain their original relative order. Missing sort values default to zero.

`scene.buildBatches()` returns normal texture-page batch data plus `scenePreparation`, including input/output counts, culling statistics, and the prepared instance order. `scene.render()` accepts the same preparation options when raw instances are passed.

Scene sorting is disabled by default for backward compatibility. Enable it explicitly with `sort: true`. When blending/layering order matters, pair sorting with `preserveOrder: true`; otherwise texture-page grouping may intentionally reorder instances to reduce texture switches.


### HiDPI canvas resize and WebGL2 context recovery

The browser runtime now includes `resizeWebGL2Canvas()` and `createWebGL2CanvasRuntime()`.

`resizeWebGL2Canvas(canvas, gl, options)` converts CSS dimensions into physical drawing-buffer dimensions using device pixel ratio, clamps DPR through `maxPixelRatio`, updates `canvas.width/height`, and calls `gl.viewport()`.

```js
resizeWebGL2Canvas(canvas, gl, {
  pixelRatio: window.devicePixelRatio,
  maxPixelRatio: 2,
});
```

`createWebGL2CanvasRuntime()` wraps the integrated atlas scene and browser canvas lifecycle:

```js
const runtime = await createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  {
    resizeOptions: { maxPixelRatio: 2 },
    onContextLost() {
      pauseGame();
    },
    onContextRestored() {
      resumeGame();
    },
  },
);

runtime.render(sprites, {
  viewport: {
    x: 0,
    y: 0,
    width: canvas.width,
    height: canvas.height,
  },
  sort: true,
  preserveOrder: true,
});
```

The wrapper registers `webglcontextlost` and `webglcontextrestored`. Context loss calls `preventDefault()`, marks rendering unavailable, and rejects render/build calls until restoration. On restore it reacquires WebGL2, recreates the atlas scene, recompiles shaders, recreates buffers/textures, reapplies canvas sizing, and only then exposes the restored scene.

It provides `resize()`, `render()`, `buildBatches()`, `restore()`, `waitForRestore()`, and `dispose()`, plus live `gl`, `scene`, `contextLost`, `restoring`, and `disposed` state.


### Persistent sprite entity store

For retained-mode 2D scenes, the web runtime now provides `createSpriteEntityStore()`.

```js
const entities = createSpriteEntityStore();

entities.add({
  id: "hero",
  page: "heroes",
  frame: "idle_0",
  x: 32,
  y: 48,
  z: 10,
});

entities.update("hero", { x: 40 });
entities.remove("hero");
```

IDs may be explicit strings/numbers or auto-generated positive integers. The store preserves insertion order, exposes a monotonically increasing `version`, validates render-critical fields, and returns cloned values so callers cannot mutate stored state accidentally.

`enabled: false` excludes an entity from normal `snapshot()` / `instances()` output without deleting it. Use `snapshot({ includeDisabled: true })` to inspect all entries.

Atomic multi-step edits are supported with `transact()`; if the callback throws, entity contents, generated-ID state, and version are rolled back.

```js
entities.transact((tx) => {
  tx.update("hero", { x: 64 });
  tx.add({
    id: "shadow",
    page: "effects",
    frame: "shadow",
  });
});
```

`createWebGL2CanvasRuntime()` now owns an entity store by default (or accepts `entityStore` in options) and exposes:

```text
runtime.entities
runtime.buildEntityBatches(options)
runtime.renderEntities(options)
```

The logical entity store is intentionally independent from GPU state. If WebGL2 context is lost and restored, shaders/buffers/textures are rebuilt while the same entity store survives unchanged.


### Animation binding for persistent entities

Persistent sprite entities can now be driven directly by runtime-atlas animations through `createSpriteAnimationSystem()`.

```js
const animations = createSpriteAnimationSystem(
  pages,
  entities,
  {
    onEvent(event) {
      if (event.name === "impact") {
        handleImpact(event.entityId, event.payload);
      }
    },
  },
);

animations.bind("hero", "run", {
  autoplay: true,
  playbackRate: 1,
});

animations.update(deltaSeconds);
```

Binding automatically updates the entity's `frame` as the animation advances. If the binding targets another page, the entity page is updated as well.

Bindings expose the underlying deterministic player controls:

```text
play()
pause()
seek(seconds)
setPlaybackRate(rate)
sample()
```

Global and per-binding callbacks can observe frame changes, timeline events, loops, and finish notifications. Animation events are enriched with `entityId`, `pageId`, and `animationName`.

If a bound entity is removed from the entity store, the next animation-system update automatically removes the stale binding. `unbind()` and `clear()` are also available explicitly.

`createWebGL2CanvasRuntime()` now exposes:

```text
runtime.animations
runtime.updateAnimations(deltaSeconds)
```

so retained-mode game loops can be written as:

```js
runtime.updateAnimations(deltaSeconds);
runtime.renderEntities({
  viewport,
  sort: true,
  preserveOrder: true,
});
```

Entity and animation state are CPU-side and survive WebGL2 context reconstruction. Logical animation updates may continue while the context is lost; only GPU rendering is blocked.

The animation-player finish path was also hardened: calling `play()` again on an already-finished non-looping clip no longer leaves the player incorrectly marked as playing.


### Parent-child sprite entity transforms

Persistent sprite entities now support an optional `parent` ID. Before culling/batching/rendering, `resolveSpriteEntityHierarchy()` converts local transforms into world-space instances.

```js
runtime.entities.add({
  id: "player",
  page: "heroes",
  frame: "body",
  x: 100,
  y: 50,
  z: 10,
  scale: 2,
});

runtime.entities.add({
  id: "weapon",
  parent: "player",
  page: "heroes",
  frame: "sword",
  x: 12,
  y: 4,
  z: 1,
});
```

The child transform resolves as:

```text
worldX = parent.worldX + localX * parent.worldScaleX
worldY = parent.worldY + localY * parent.worldScaleY
worldZ = parent.worldZ + localZ
worldScaleX = parent.worldScaleX * localScaleX
worldScaleY = parent.worldScaleY * localScaleY
```

Hierarchy resolution is recursive, preserves entity insertion order, rejects cycles, and rejects missing parents by default. `allowMissingParents: true` treats missing parents as roots.

Disabled state is inherited by descendants by default. Use `inheritDisabled: false` to disable that propagation or `includeDisabled: true` to inspect/render disabled branches explicitly.

`buildSpriteEntityInstances()` is the shared bridge used by entity rendering and the version-aware entity batch cache. Hierarchy resolution is enabled by default for entity rendering; pass `hierarchy: false` for legacy local-space behavior.

Because parent mutations increment `entityStore.version`, cached batches are invalidated automatically when a parent moves, scales, changes depth, or changes enabled state.


### Sprite rotation and pivots

Sprite entities and raw sprite instances now support:

```text
rotation   // radians, clockwise-positive in canvas pixel coordinates
pivotX
pivotY
```

`pivotX/pivotY` are expressed in the entity's unscaled logical source-space pixels. The world pivot is derived from entity position and scale.

Parent-child hierarchy resolution now rotates a child's local offset by the parent's world rotation before adding it to the parent position. World rotation is additive across the hierarchy:

```text
childWorldRotation = parentWorldRotation + childLocalRotation
```

The instanced WebGL buffer contract has expanded from 12 to 16 floats per sprite:

```text
visibleX
visibleY
visibleWidth
visibleHeight
u0
v0
u1
v1
atlasRotationFlag
sourceWidth
sourceHeight
spriteRotationRadians
pivotWorldX
pivotWorldY
reserved0
reserved1
```

This is a 64-byte instance record. The WebGL2 shader rotates each visible sprite quad around the world-space pivot while retaining the independent atlas-packing 90-degree UV rotation logic.

`instancedSpriteAttributeViews()` now exposes a fourth instanced attribute at location 4 (`aPivotAndReserved`). Existing location 0-3 meanings are preserved.

The classic CPU-generated quad batch also applies sprite rotation around the same pivot. `spriteInstanceBounds()` returns rotation-aware axis-aligned bounding boxes, so viewport culling remains correct for rotated sprites.

Because rotations and pivots live in the entity store, changing any of them increments `entityStore.version` and naturally invalidates the version-aware batch cache.


### Per-sprite tint and alpha

Instanced sprite rendering now supports per-instance color modulation without splitting batches:

```js
runtime.entities.add({
  id: "ghost",
  page: "characters",
  frame: "idle",
  tintR: 0.6,
  tintG: 0.8,
  tintB: 1.0,
  alpha: 0.45,
});
```

`tintR`, `tintG`, `tintB`, and `alpha` are normalized values in `[0, 1]`. Defaults are all `1`.

Color and alpha inherit multiplicatively through the parent-child hierarchy. A child with `alpha: 0.5` under a parent with `alpha: 0.5` resolves to world alpha `0.25`.

The instanced record is now 20 floats / 80 bytes:

```text
visibleX
visibleY
visibleWidth
visibleHeight
u0
v0
u1
v1
atlasRotationFlag
sourceWidth
sourceHeight
spriteRotationRadians
pivotWorldX
pivotWorldY
reserved0
reserved1
tintR
tintG
tintB
alpha
```

The WebGL2 shader exposes `aTint` at attribute location 5 and computes:

```glsl
outColor = texture(uTexture, vUv) * vTint;
```

The instanced renderer enables standard alpha blending by default:

```text
SRC_ALPHA
ONE_MINUS_SRC_ALPHA
```

Set `alphaBlending: false` when the host engine owns blend state itself.


### Sprite layers and runtime visibility masks

Persistent sprite entities now support a 32-bit `layerMask`:

```js
runtime.entities.add({
  id: "world-tree",
  page: "world",
  frame: "tree",
  layerMask: 0b0001,
});

runtime.entities.add({
  id: "hud",
  page: "ui",
  frame: "healthbar",
  layerMask: 0b0100,
});
```

An entity is visible when:

```text
(entity.layerMask & visibilityMask) !== 0
```

The default entity layer is bit 0 (`1`), while the default runtime visibility mask enables all 32 bits.

`createWebGL2CanvasRuntime()` exposes:

```js
runtime.visibilityMask
runtime.setVisibilityMask(mask)
```

Example:

```js
runtime.setVisibilityMask(0b0001 | 0b0010);
runtime.renderEntities();
```

A per-call `visibilityMask` overrides the runtime mask temporarily:

```js
runtime.renderEntities({
  visibilityMask: 0b0100,
});
```

`filterSpriteInstancesByLayer()` is also available as a low-level helper and reports input, visible, filtered counts, plus filtered indices.

Layer filtering happens after hierarchy world-transform resolution but before culling, sorting, texture grouping, and GPU batching. Parent transforms therefore remain available to visible descendants even when parent and child use different layer masks.

The version-aware entity batch cache includes `visibilityMask` in its stable cache key, so world/UI/effects views can coexist as separate cached batch variants without false cache hits.


### 2D camera, zoom, and parallax

Entity rendering can now apply a camera before culling and batching.

```js
const runtime = await createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  {
    camera: {
      x: 0,
      y: 0,
      zoom: 1,
    },
  },
);
```

The camera uses top-left world coordinates:

```text
screenX = (worldX - camera.x * parallaxX) * zoom
screenY = (worldY - camera.y * parallaxY) * zoom
```

Sprite scale is multiplied by camera zoom. Rotation, tint, alpha, depth, and hierarchy world transforms remain intact.

Entities may define:

```js
{
  parallaxX: 0.25,
  parallaxY: 0.25
}
```

Defaults are `1`, so normal world sprites track the camera fully. Values below `1` move more slowly and are suitable for distant backgrounds. Parallax values must be finite and non-negative.

Low-level helper:

```js
applyCameraToSpriteInstances(instances, camera)
```

The canvas runtime exposes:

```js
runtime.camera
runtime.setCamera({ x, y, zoom })
```

Partial updates preserve unspecified fields:

```js
runtime.setCamera({ x: player.x - 320 });
runtime.setCamera({ zoom: 1.5 });
```

A per-call camera overrides runtime camera state temporarily:

```js
runtime.renderEntities({
  camera: { x: 0, y: 0, zoom: 1 },
  visibilityMask: UI_LAYER,
});
```

Camera transforms happen after hierarchy resolution and layer filtering but before viewport culling, stable depth sorting, texture grouping, and GPU batching.

The version-aware entity batch cache includes the camera object in its stable options key, so different camera positions/zoom values produce distinct cached variants.


### Camera follow, dead zone, smoothing, and deterministic shake

The runtime now provides `createCamera2DController()` for game-style camera behavior on top of the base 2D camera.

```js
const controller = createCamera2DController(
  { x: 0, y: 0, zoom: 1 },
  {
    deadZoneWidth: 120,
    deadZoneHeight: 80,
    smoothing: 8,
  },
);
```

`update(targetX, targetY, deltaSeconds)` keeps the target inside the configured dead zone. When the target exits it, the camera moves only as far as required to bring the target back to the boundary.

With `smoothing > 0`, movement uses an exponential time-based interpolation:

```text
alpha = 1 - exp(-smoothing * deltaSeconds)
```

which avoids frame-rate-dependent lerp behavior.

Deterministic screen shake is available through:

```js
controller.shake(amplitude, durationSeconds, frequency);
```

Shake decays linearly over its duration and uses deterministic sine phases rather than randomness, making tests/replays reproducible.

The canvas runtime exposes the controller directly:

```js
runtime.cameraController
runtime.updateCameraFollow(targetX, targetY, deltaSeconds)
runtime.shakeCamera(amplitude, durationSeconds, frequency)
runtime.clearCameraShake()
```

Example game loop:

```js
runtime.updateAnimations(dt);
runtime.updateCameraFollow(player.x, player.y, dt);
runtime.renderEntities({
  viewport: {
    x: 0,
    y: 0,
    width: canvas.width,
    height: canvas.height,
  },
  sort: true,
  preserveOrder: true,
});
```

Camera follow/shake modifies the runtime camera used by the existing parallax, culling, batching, and render pipeline.


### Camera world bounds and direct entity follow

The 2D camera can now be constrained to finite world bounds.

```js
const runtime = await createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  {
    worldBounds: {
      x: 0,
      y: 0,
      width: 4096,
      height: 2048,
    },
  },
);
```

Low-level helper:

```js
clampCameraToWorldBounds(
  camera,
  worldBounds,
  viewportWidth,
  viewportHeight,
)
```

Clamping is zoom-aware. Visible world size is computed as:

```text
visibleWorldWidth = viewportWidth / zoom
visibleWorldHeight = viewportHeight / zoom
```

If the world is smaller than the visible viewport on an axis, the camera is centered on that world axis instead of exposing asymmetric empty space.

The canvas runtime exposes:

```js
runtime.worldBounds
runtime.setWorldBounds(bounds)
runtime.setWorldBounds(null)
```

Camera changes from `setCamera()`, target follow, and screen shake are clamped against the current world bounds.

Direct entity follow is also available:

```js
runtime.updateCameraFollowEntity(
  "player",
  deltaSeconds,
  {
    offsetX: 16,
    offsetY: 24,
  },
);
```

The entity target is resolved after parent-child hierarchy transforms, so following a child tracks its world-space position rather than its local coordinates. Offsets are useful for following an entity center or a custom focus point.

When world bounds are cleared, camera coordinates become unrestricted again.


### World/screen conversion and sprite picking

The web runtime now includes helpers for interaction and touch/click picking.

Coordinate conversion:

```js
worldToScreenPoint(x, y, camera, parallax)
screenToWorldPoint(x, y, camera)
```

The canvas runtime exposes convenience wrappers:

```js
runtime.worldToScreen(worldX, worldY)
runtime.screenToWorld(screenX, screenY)
```

Low-level hit testing:

```js
pointHitsSpriteInstance(
  atlasPages,
  instance,
  screenX,
  screenY,
  { useVisibleBounds: false },
)
```

Hit testing uses the sprite's logical source size by default. Set `useVisibleBounds: true` to use only the trimmed visible source region.

Rotation and pivot are handled by inverse-rotating the query point around the sprite's world pivot before testing its local rectangle.

Multiple instances can be queried with:

```js
pickSpriteInstances(
  atlasPages,
  instances,
  screenX,
  screenY,
  { all: true },
)
```

Hits are ordered from highest `z` to lowest. Equal-depth sprites use later input order as the top-most tie breaker, matching typical painter-style submission order.

The canvas runtime exposes:

```js
runtime.pickEntity(screenX, screenY)
runtime.pickEntity(screenX, screenY, { all: true })
```

`pickEntity()` reuses the normal entity preparation pipeline, so hierarchy transforms, layer visibility, runtime/per-call camera transforms, zoom, and parallax are applied before hit testing.

This makes pointer/touch interaction possible directly against the same transformed geometry used for rendering.


### Pointer, touch, hover, click, and drag interaction

The runtime now provides a retained pointer interaction controller on top of entity picking.

Low-level API:

```js
const pointer = createSpritePointerInteractionController({
  pick(x, y) {
    return pickSpriteInstances(...);
  },
  toWorld(x, y) {
    return screenToWorldPoint(x, y, camera);
  },
  dragThreshold: 4,
  onEnter(event) {},
  onLeave(event) {},
  onDown(event) {},
  onUp(event) {},
  onClick(event) {},
  onDragStart(event) {},
  onDrag(event) {},
  onDragEnd(event) {},
  onCancel(event) {},
});
```

The controller is DOM-independent. Pointer IDs may be strings or numbers, making it usable with mouse, pen, and multi-touch input.

It tracks:

```text
hover entity
pointer down state
captured entity id
drag threshold
dragging state
screen delta
total drag delta
world coordinates
```

Clicks are emitted only when pointer-down and pointer-up occur on the same entity without crossing the drag threshold.

When dragging starts, the entity selected on pointer-down remains available through `capturedEntityId` even if the pointer moves away from its visual bounds.

The canvas runtime exposes the controller directly:

```js
runtime.pointerInteractions
runtime.pointerMove(pointerId, x, y)
runtime.pointerDown(pointerId, x, y)
runtime.pointerUp(pointerId, x, y)
runtime.pointerCancel(pointerId)
```

Example DOM wiring:

```js
canvas.addEventListener("pointerdown", (event) => {
  canvas.setPointerCapture(event.pointerId);
  runtime.pointerDown(
    event.pointerId,
    event.offsetX,
    event.offsetY,
  );
});

canvas.addEventListener("pointermove", (event) => {
  runtime.pointerMove(
    event.pointerId,
    event.offsetX,
    event.offsetY,
  );
});

canvas.addEventListener("pointerup", (event) => {
  runtime.pointerUp(
    event.pointerId,
    event.offsetX,
    event.offsetY,
  );
});
```

Runtime pointer callbacks receive both screen and world coordinates. World coordinates use the current runtime camera and zoom. Entity selection reuses the normal hierarchy/layer/camera/parallax picking pipeline.

Multiple pointer IDs are tracked independently. `clear()` or runtime disposal cancels active pointer state.


### Hierarchy-safe entity dragging and automatic pointer movement

Entity movement can now be applied in world-space while preserving local coordinates inside parent-child hierarchies.

Low-level helper:

```js
moveSpriteEntityByWorldDelta(
  entityStore,
  entityId,
  deltaX,
  deltaY,
  {
    axis: "both", // "both" | "x" | "y"
  },
);
```

For root entities, world deltas map directly to local `x/y`. For child entities, the world-space delta is inverse-rotated by the parent world rotation and divided by the parent world scale before updating the child's local coordinates.

This means a child can be dragged visually in screen/world space even when its parent is translated, rotated, or non-uniformly scaled.

The canvas runtime exposes:

```js
runtime.moveEntityByWorldDelta(
  entityId,
  deltaX,
  deltaY,
  options,
)
```

Pointer-driven automatic movement is opt-in:

```js
const runtime = await createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  {
    pointerOptions: {
      dragThreshold: 4,
      autoDragEntities: true,
      dragAxis: "both",
    },
  },
);
```

When enabled, pointer drag screen deltas are divided by the current camera zoom and applied to the captured entity as world-space movement.

Available axis constraints:

```text
both
x
y
```

The user `onDrag` callback still runs after automatic movement. Its event includes:

```js
event.capturedEntityId
event.draggedEntity
event.dx
event.dy
event.totalDx
event.totalDy
```

Automatic dragging is disabled by default, so existing pointer-interaction users keep their previous behavior.

Each drag update goes through `entityStore.update()`, incrementing `entityStore.version`. Version-aware entity batch caches therefore invalidate naturally after movement.


### Drag snapping and movement bounds

World-space entity movement now supports snapping and positional bounds:

```js
moveSpriteEntityByWorldDelta(
  entityStore,
  "crate",
  dx,
  dy,
  {
    gridSize: 16,
    bounds: {
      x: 0,
      y: 0,
      width: 1024,
      height: 768,
    },
  },
);
```

`gridSize: 0` disables snapping. Positive values snap the entity's resulting world position to the nearest grid intersection.

Bounds clamp the resulting world position to the supplied rectangle. Snapping and clamping happen in world-space before the delta is converted back into local coordinates for parented entities.

This preserves predictable visual movement even under parent rotation and non-uniform scale.

Pointer auto-drag accepts:

```js
pointerOptions: {
  autoDragEntities: true,
  dragAxis: "both",
  dragGridSize: 16,
  dragBounds: {
    x: 0,
    y: 0,
    width: 2048,
    height: 2048,
  },
}
```

If `dragBounds` is omitted, the runtime automatically reuses `worldBounds` when available.

This allows editors and games to constrain draggable entities to the playable map without maintaining a second bounds configuration.


### Persistent selection and marquee rectangle selection

The runtime now includes a retained selection model:

```js
const selection = createSpriteSelectionModel();
selection.select("player");
selection.select("enemy", { additive: true });
selection.select("enemy", { toggle: true });
selection.clear();
```

Selection state tracks:

```text
ids
primaryId
count
```

`primaryId` is the most recently selected entity and is useful for inspector panels, gizmo ownership, or primary transform handles.

The low-level marquee helper:

```js
selectSpriteInstancesInRect(
  atlasPages,
  instances,
  rect,
  { mode: "intersect" },
)
```

supports:

```text
intersect
contain
```

Rectangle coordinates may be dragged in either direction; min/max normalization is automatic.

The canvas runtime exposes:

```js
runtime.selection
runtime.selectEntity(entityId, options)
runtime.clearSelection()
runtime.selectEntitiesInRect(rect, options)
```

Marquee selection reuses normal entity preparation, including hierarchy, visibility masks, camera, zoom, and parallax before testing sprite bounds.

Additive marquee selection is supported with:

```js
runtime.selectEntitiesInRect(rect, {
  additive: true,
});
```


### Multi-selection dragging

Selected entities can now move as one world-space group:

```js
runtime.moveSelectionByWorldDelta(dx, dy, {
  axis: "both",
  gridSize: 16,
  bounds: runtime.worldBounds,
});
```

`moveSelectedSpriteEntitiesByWorldDelta()` uses the selection primary entity as the snap anchor. If both a parent and its descendant are selected, only the highest selected ancestor is directly moved, preventing double movement while preserving every selected entity's visual offset.

Pointer group dragging is opt-in:

```js
pointerOptions: {
  autoDragEntities: true,
  dragSelection: true,
}
```

When the captured entity belongs to a multi-selection, the complete selection moves together. Otherwise the existing single-entity drag behavior is preserved.


### Transactional entity undo/redo

The retained entity runtime now provides bounded synchronous edit history:

```js
runtime.history.record("move selection", () => {
  runtime.moveSelectionByWorldDelta(16, 0);
});

runtime.undo();
runtime.redo();
```

For interactive gestures, an edit can span multiple updates:

```js
runtime.history.begin("drag");
// many entity updates...
runtime.history.commit();
```

`cancel()` restores the pre-edit snapshot. History restores additions, removals, and property changes transactionally, clears redo entries after a new committed edit, and rejects asynchronous callbacks so rollback semantics remain deterministic.


### Safe hierarchy reparenting and deletion

`reparentSpriteEntity()` changes a parent while preserving world position, depth, rotation, and scale by default. It rejects self-parenting, missing parents, and hierarchy cycles.

Hierarchy deletion supports three explicit child policies:

```text
detach   keep direct children and preserve their world transforms
cascade  recursively remove descendants
reject   refuse deletion when children exist
```

The canvas runtime exposes `reparentEntity()`, `removeEntity()`, and `removeSelection()`. Removed IDs are also removed from the retained selection model.


### Hierarchy-aware duplicate, copy, and paste

The retained editor runtime can duplicate selected entities and preserve internal parent-child relationships. `includeDescendants: true` expands a selected hierarchy automatically. Offsets apply only to duplicated roots, so child local transforms remain unchanged.

```js
runtime.duplicateSelection({
  includeDescendants: true,
  offsetX: 16,
  offsetY: 16,
});

const clipboard = runtime.copySelection({
  includeDescendants: true,
});

runtime.pasteEntities(clipboard, {
  offsetX: 32,
  offsetY: 32,
});
```

Clipboard payloads use the versioned `asset-forge-sprite-clipboard` format. Pasted entities receive fresh IDs, internal parent references are remapped, and the newly created entities become the active selection.


### Hierarchy-aware duplicate, copy, and paste

Selections and entity trees can now be duplicated or copied into a portable in-memory clipboard:

```js
const copy = runtime.copySelection({ includeDescendants: true });
const pasted = runtime.pasteEntities(copy, { offsetX: 16, offsetY: 16 });
```

`runtime.duplicateSelection()` performs the same operation directly inside the current entity store and selects the new entities.

Internal parent-child links are remapped to the newly allocated IDs. Only top-level copied roots receive the paste offset, so descendant local transforms remain unchanged and the duplicated hierarchy preserves its shape.

The clipboard contract is versioned as `asset-forge-sprite-clipboard` version 1.
````

## File: runtime_atlas.py
````python
def _positive_int(value, field: str) -> int
⋮----
result = value
⋮----
def _non_negative_int(value, field: str) -> int
⋮----
normalized = []
seen_names: set[str] = set()
⋮----
name = animation.get("name")
⋮----
fps = animation.get("fps", 12.0)
⋮----
loop = animation.get("loop", True)
⋮----
raw_frames = animation.get("frames")
⋮----
frames = []
⋮----
index = raw
duration = 1.0
⋮----
index = raw.get("index")
duration = raw.get("duration", 1.0)
⋮----
duration_seconds = sum(frame["duration"] for frame in frames) / float(fps)
raw_events = animation.get("events", [])
⋮----
events = []
⋮----
event_name = event.get("name")
⋮----
time_seconds = event.get("timeSeconds")
⋮----
payload = event.get("payload")
⋮----
normalized_event = {
⋮----
normalized_animation = {
⋮----
frames = atlas_metadata.get("frames")
⋮----
image = atlas_metadata.get("image")
⋮----
atlas_width = _positive_int(atlas_metadata.get("imageWidth"), "imageWidth")
atlas_height = _positive_int(atlas_metadata.get("imageHeight"), "imageHeight")
⋮----
runtime_frames = []
seen_indices: set[int] = set()
⋮----
index = _non_negative_int(frame.get("index", fallback_index), f"frame {fallback_index}.index")
⋮----
x = _non_negative_int(frame.get("x"), f"frame {index}.x")
y = _non_negative_int(frame.get("y"), f"frame {index}.y")
width = _positive_int(frame.get("width"), f"frame {index}.width")
height = _positive_int(frame.get("height"), f"frame {index}.height")
⋮----
rotated = bool(frame.get("rotated", False))
rotation_degrees = int(frame.get("rotationDegrees", 90 if rotated else 0))
⋮----
source_region_width = _positive_int(
source_region_height = _positive_int(
⋮----
expected_width = source_region_height if rotated else source_region_width
expected_height = source_region_width if rotated else source_region_height
⋮----
source_width = _positive_int(
source_height = _positive_int(
offset_x = _non_negative_int(frame.get("offsetX", 0), f"frame {index}.offsetX")
offset_y = _non_negative_int(frame.get("offsetY", 0), f"frame {index}.offsetY")
⋮----
result = {
normalized_animations = _normalize_runtime_animations(animations, seen_indices)
⋮----
def validate_runtime_atlas(data: dict) -> list[str]
⋮----
errors: list[str] = []
⋮----
allowed_top = {
unknown_top = sorted(set(data) - allowed_top)
⋮----
image = data.get("image")
⋮----
image_size = data.get("imageSize")
⋮----
atlas_width = atlas_height = None
⋮----
atlas_width = _positive_int(image_size.get("width"), "imageSize.width")
atlas_height = _positive_int(image_size.get("height"), "imageSize.height")
⋮----
capabilities = data.get("capabilities")
⋮----
frames = data.get("frames")
⋮----
frame_count = data.get("frameCount")
⋮----
allowed_frame = {
⋮----
index = frame.get("index")
⋮----
index_label = position
⋮----
index_label = index
⋮----
name = frame.get("name")
⋮----
atlas_region = frame.get("atlasRegion")
⋮----
region = None
⋮----
x = _non_negative_int(atlas_region.get("x"), f"frame {index_label}.atlasRegion.x")
y = _non_negative_int(atlas_region.get("y"), f"frame {index_label}.atlasRegion.y")
width = _positive_int(atlas_region.get("width"), f"frame {index_label}.atlasRegion.width")
height = _positive_int(atlas_region.get("height"), f"frame {index_label}.atlasRegion.height")
region = (x, y, width, height)
⋮----
def read_size(field_name: str)
⋮----
obj = frame.get(field_name)
⋮----
source_region = read_size("sourceRegion")
source_size = read_size("sourceSize")
⋮----
trim_offset = frame.get("trimOffset")
⋮----
offset = None
⋮----
offset = (
⋮----
rotation = frame.get("rotation")
⋮----
rotated = None
degrees = None
⋮----
rotated = rotation.get("rotated")
degrees = rotation.get("degreesClockwise")
⋮----
uv = frame.get("uv")
⋮----
values = []
⋮----
value = uv.get(key)
⋮----
expected = (
⋮----
animations = data.get("animations")
⋮----
seen_animation_names: set[str] = set()
valid_indices = set(seen_indices)
allowed_animation = {"name", "fps", "loop", "frames", "events"}
allowed_animation_frame = {"index", "duration"}
allowed_animation_event = {"name", "timeSeconds", "payload"}
⋮----
name_label = animation_position
⋮----
name_label = name
⋮----
fps = animation.get("fps")
⋮----
loop = animation.get("loop")
⋮----
animation_frames = animation.get("frames")
⋮----
normalized_duration_units = 0.0
⋮----
index = animation_frame.get("index")
⋮----
duration = animation_frame.get("duration")
⋮----
animation_duration = None
⋮----
animation_duration = normalized_duration_units / float(fps)
⋮----
animation_events = animation.get("events", [])
⋮----
previous_time = -1.0
⋮----
event_time = event.get("timeSeconds")
⋮----
event_time = float(event_time)
⋮----
previous_time = event_time
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
