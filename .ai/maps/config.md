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
tooling.json
```

# Files

## File: __init__.py
```python
"""Packaged Asset Forge runtime resources."""
```

## File: tooling.json
```json
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
      "domains": [
        "3d",
        "rigging",
        "animation-3d",
        "rendering",
        "uv"
      ],
      "automation": [
        "python",
        "cli"
      ],
      "outputs": [
        "blend",
        "gltf",
        "glb",
        "fbx",
        "obj"
      ],
      "license": "GPL-2.0-or-later"
    },
    {
      "id": "gltf-validator",
      "name": "Khronos glTF Validator",
      "status": "candidate",
      "domains": [
        "3d-validation",
        "gltf"
      ],
      "automation": [
        "cli",
        "library"
      ],
      "outputs": [
        "validation-report"
      ],
      "license": "Apache-2.0"
    },
    {
      "id": "gltf-transform",
      "name": "glTF Transform",
      "status": "candidate",
      "domains": [
        "3d-optimization",
        "gltf",
        "texture-optimization"
      ],
      "automation": [
        "cli",
        "library"
      ],
      "outputs": [
        "gltf",
        "glb"
      ],
      "license": "MIT"
    },
    {
      "id": "meshoptimizer",
      "name": "meshoptimizer",
      "status": "candidate",
      "domains": [
        "mesh-optimization",
        "gltf"
      ],
      "automation": [
        "cli",
        "library"
      ],
      "outputs": [
        "optimized-mesh",
        "glb"
      ],
      "license": "MIT"
    },
    {
      "id": "pixelorama",
      "name": "Pixelorama",
      "status": "candidate",
      "domains": [
        "pixel-art",
        "sprites",
        "animation-2d"
      ],
      "automation": [],
      "outputs": [
        "png",
        "sprite-sheet"
      ],
      "license": "MIT"
    },
    {
      "id": "inkscape",
      "name": "Inkscape",
      "status": "candidate",
      "domains": [
        "vector",
        "svg",
        "ui"
      ],
      "automation": [
        "cli"
      ],
      "outputs": [
        "svg",
        "png",
        "pdf"
      ],
      "license": "GPL-2.0-or-later"
    },
    {
      "id": "vtracer",
      "name": "VTracer",
      "status": "preferred",
      "domains": [
        "vector",
        "svg",
        "raster-to-vector"
      ],
      "automation": [
        "python",
        "cli"
      ],
      "outputs": [
        "svg"
      ],
      "license": "MIT",
      "repository": "visioncortex/vtracer"
    },
    {
      "id": "triposr",
      "name": "TripoSR",
      "status": "preferred-fallback",
      "domains": [
        "3d",
        "image-to-3d",
        "mesh-reconstruction"
      ],
      "automation": [
        "python",
        "kaggle"
      ],
      "outputs": [
        "glb",
        "obj"
      ],
      "license": "MIT",
      "repository": "VAST-AI-Research/TripoSR",
      "notes": "Free lightweight 3D fallback; approximately 6 GB VRAM for one image. Premium/primary assets may prefer TRELLIS when available."
    }
  ]
}
```
