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
__init__.py
```

# Files

## File: 3d/character.json
```json
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
    "maxJointsPerSkin": 128,
    "strictBudgets": true,
    "requirePbrMaterials": true
  }
}
```

## File: 3d/environment.json
```json
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
    "maxJointsPerSkin": 0,
    "strictBudgets": true,
    "requirePbrMaterials": true
  }
}
```

## File: 3d/prop.json
```json
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
    "maxJointsPerSkin": 0,
    "strictBudgets": true,
    "requirePbrMaterials": true
  }
}
```

## File: godot4/character.json
```json
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
```

## File: godot4/environment.json
```json
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
```

## File: godot4/prop.json
```json
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
```

## File: vector/icon.json
```json
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
```

## File: vector/logo.json
```json
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
```

## File: vector/ui.json
```json
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
```

## File: __init__.py
```python
"""Packaged Asset Forge runtime resources."""
```
