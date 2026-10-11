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
__init__.py
model-3d.json
sprite-2d.json
vector-svg.json
```

# Files

## File: __init__.py
```python
"""Packaged Asset Forge runtime resources."""
```

## File: model-3d.json
```json
{
  "id": "model-3d",
  "assetTypes": [
    "mesh",
    "prop",
    "environment",
    "character-3d"
  ],
  "stages": [
    "read-project-art-direction",
    "resolve-source-or-create",
    "select-quality-aware-3d-backend",
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
    "embedTextures": true,
    "freeFallbackBackend": "kaggle-triposr",
    "premiumBackend": "pollinations-trellis",
    "premiumFirstForPrimary": true
  }
}
```

## File: sprite-2d.json
```json
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
```

## File: vector-svg.json
```json
{
  "id": "vector-svg",
  "assetTypes": [
    "vector",
    "svg",
    "icon",
    "ui-vector",
    "logo"
  ],
  "stages": [
    "read-project-art-direction",
    "resolve-source-or-create",
    "free-raster-to-vector-fallback",
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
    "allowExternalReferences": false,
    "freeFirstVectorization": true,
    "preferredVectorizer": "vtracer"
  }
}
```
