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
3d-quality-profile.schema.json
asset-manifest.schema.json
godot4-handoff-profile.schema.json
production-report.schema.json
production-request.schema.json
runtime-atlas.schema.json
vector-profile.schema.json
```

# Files

## File: __init__.py
```python
"""Packaged Asset Forge runtime resources."""
```

## File: 3d-quality-profile.schema.json
```json
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
```

## File: asset-manifest.schema.json
```json
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
```

## File: godot4-handoff-profile.schema.json
```json
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
```

## File: production-report.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "asset-forge production report",
  "type": "object",
  "required": [
    "schema",
    "requestId",
    "assetId",
    "assetType",
    "success",
    "generation",
    "validation",
    "artifact"
  ],
  "properties": {
    "schema": {
      "const": "asset-forge/production-report/v1"
    },
    "requestId": {
      "type": "string",
      "minLength": 1
    },
    "assetId": {
      "type": "string",
      "minLength": 1
    },
    "assetType": {
      "type": "string",
      "minLength": 1
    },
    "success": {
      "type": "boolean"
    },
    "generation": {
      "type": "object"
    },
    "provenance": {
      "type": "object",
      "properties": {
        "source": {
          "type": "object"
        },
        "license": {
          "type": "object"
        }
      },
      "additionalProperties": true
    },
    "processing": {
      "type": "object"
    },
    "validation": {
      "type": "object",
      "required": [
        "errors"
      ],
      "properties": {
        "errors": {
          "type": "array"
        }
      },
      "additionalProperties": true
    },
    "artifact": {
      "type": [
        "string",
        "null"
      ]
    },
    "engineHandoff": {
      "type": "object"
    },
    "routing": {
      "type": "object",
      "properties": {
        "requestedBackend": {
          "type": [
            "string",
            "null"
          ]
        },
        "initialBackend": {
          "type": [
            "string",
            "null"
          ]
        },
        "finalBackend": {
          "type": [
            "string",
            "null"
          ]
        },
        "fallbacks": {
          "type": "array",
          "items": {
            "type": "object"
          }
        },
        "fallbackCount": {
          "type": "integer",
          "minimum": 0
        },
        "retryCount": {
          "type": "integer",
          "minimum": 0
        },
        "retryStrategies": {
          "type": "object",
          "additionalProperties": {
            "type": "integer",
            "minimum": 0
          }
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true,
  "allOf": [
    {
      "if": {
        "properties": {
          "success": {
            "const": true
          }
        }
      },
      "then": {
        "properties": {
          "artifact": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "success": {
            "const": false
          }
        }
      },
      "then": {
        "properties": {
          "artifact": {
            "type": "null"
          }
        }
      }
    }
  ]
}
```

## File: production-request.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "asset-forge production request",
  "type": "object",
  "required": ["schema", "requestId", "instruction", "manifest"],
  "properties": {
    "schema": {"const": "asset-forge/production-request/v1"},
    "requestId": {"type": "string", "minLength": 1},
    "instruction": {"type": "string", "minLength": 1},
    "manifest": {"$ref": "asset-manifest.schema.json"},
    "delivery": {
      "type": "object",
      "properties": {
        "engine": {"type": ["string", "null"], "minLength": 1},
        "outputDir": {"type": ["string", "null"], "minLength": 1}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

## File: runtime-atlas.schema.json
```json
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
```

## File: vector-profile.schema.json
```json
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
```
