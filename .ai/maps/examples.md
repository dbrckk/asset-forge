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
asset-manifest.json
deadline-zero-live-pilot-batch.json
godot-animations.json
production-request-live-raster.json
production-request-live-vector.json
production-request-strict-raster.json
production-request.json
runtime-atlas.json
```

# Files

## File: asset-manifest.json
```json
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
```

## File: deadline-zero-live-pilot-batch.json
```json
{
  "items": [
    {
      "id": "rex-pilot-anchor",
      "request": {
        "schema": "asset-forge/production-request/v1",
        "requestId": "deadline-zero-rex-pilot-anchor",
        "instruction": "Create a premium production-quality survivor identity anchor for Deadline Zero. Rex is a battle-worn near-future male survivor viewed from a slightly elevated 3/4 top-down gameplay camera, wearing a dark charcoal tactical jacket and armor, compact rifle clearly visible, restrained red-orange accent lights, realistic stylized proportions, strong readable silhouette at mobile scale, cinematic but game-ready lighting, transparent background, no text, no UI, no muzzle flash.",
        "manifest": {
          "schema": "asset-forge/manifest/v1",
          "id": "rex-pilot-anchor",
          "project": "deadline-zero",
          "type": "sprite-sheet",
          "importance": "primary",
          "source": {
            "mode": "generated"
          },
          "license": {
            "id": "project-owned",
            "commercialUse": true,
            "derivatives": true,
            "attributionRequired": false
          },
          "target": {
            "format": "png",
            "engine": "libgdx",
            "maxBytes": 8388608
          },
          "constraints": {
            "frameWidth": 96,
            "frameHeight": 96,
            "expectedFrames": 1,
            "requiresAlpha": true,
            "visualSimilarityMin": 0.55,
            "visualSimilarityRetries": 2,
            "technicalQualityMin": 0.6,
            "maxBorderAlphaRatio": 0.05
          }
        }
      },
      "target_path": "assets/art/pilot/rex-anchor.png"
    },
    {
      "id": "rex-pilot-run",
      "depends_on": [
        "rex-pilot-anchor"
      ],
      "request": {
        "schema": "asset-forge/production-request/v1",
        "requestId": "deadline-zero-rex-pilot-run",
        "instruction": "Create an 8-frame run-cycle spritesheet for Rex in Deadline Zero. Keep the exact same survivor identity, face, tactical outfit, compact rifle, proportions, palette and top-down 3/4 gameplay camera as the provided reference. Frames must form a readable grounded run cycle with stable foot contact, stable center/pivot, transparent background, no text, no UI, no muzzle flash. Each frame must remain readable at 96x96 mobile gameplay scale.",
        "manifest": {
          "schema": "asset-forge/manifest/v1",
          "id": "rex-pilot-run",
          "project": "deadline-zero",
          "type": "sprite-sheet",
          "importance": "primary",
          "source": {
            "mode": "generated"
          },
          "license": {
            "id": "project-owned",
            "commercialUse": true,
            "derivatives": true,
            "attributionRequired": false
          },
          "target": {
            "format": "png",
            "engine": "libgdx",
            "maxBytes": 8388608
          },
          "constraints": {
            "frameWidth": 96,
            "frameHeight": 96,
            "expectedFrames": 8,
            "requiresAlpha": true,
            "visualSimilarityMin": 0.55,
            "visualSimilarityRetries": 2,
            "technicalQualityMin": 0.6,
            "maxBorderAlphaRatio": 0.05,
            "minUniqueFrameRatio": 0.5,
            "maxFrameCenterDrift": 0.2
          }
        }
      },
      "target_path": "assets/art/pilot/rex-run.png"
    },
    {
      "id": "rex-pilot-attack",
      "depends_on": [
        "rex-pilot-anchor"
      ],
      "request": {
        "schema": "asset-forge/production-request/v1",
        "requestId": "deadline-zero-rex-pilot-attack",
        "instruction": "Create a 6-frame compact-rifle attack spritesheet for Rex in Deadline Zero. Preserve the exact reference identity, outfit, rifle design, proportions, palette and top-down 3/4 camera. Show anticipation, aim, recoil and recovery without baked muzzle flash. Stable feet/pivot, transparent background, no text or UI, readable at 96x96 mobile gameplay scale.",
        "manifest": {
          "schema": "asset-forge/manifest/v1",
          "id": "rex-pilot-attack",
          "project": "deadline-zero",
          "type": "sprite-sheet",
          "importance": "primary",
          "source": {
            "mode": "generated"
          },
          "license": {
            "id": "project-owned",
            "commercialUse": true,
            "derivatives": true,
            "attributionRequired": false
          },
          "target": {
            "format": "png",
            "engine": "libgdx",
            "maxBytes": 8388608
          },
          "constraints": {
            "frameWidth": 96,
            "frameHeight": 96,
            "expectedFrames": 6,
            "requiresAlpha": true,
            "visualSimilarityMin": 0.55,
            "visualSimilarityRetries": 2,
            "technicalQualityMin": 0.6,
            "maxBorderAlphaRatio": 0.05,
            "minUniqueFrameRatio": 0.5,
            "maxFrameCenterDrift": 0.2
          }
        }
      },
      "target_path": "assets/art/pilot/rex-attack.png"
    }
  ]
}
```

## File: godot-animations.json
```json
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
```

## File: production-request-live-raster.json
```json
{
  "schema": "asset-forge/production-request/v1",
  "requestId": "live-raster-smoke",
  "instruction": "Create a simple isolated sci-fi energy cell game sprite with a dark metallic body, one cyan emissive strip, no text, no watermark, and a plain neutral background.",
  "manifest": {
    "id": "live-raster-cell",
    "project": "asset-forge-live-smoke",
    "type": "sprite",
    "importance": "secondary",
    "source": {"mode": "generated"},
    "license": {
      "id": "project-owned",
      "commercialUse": true,
      "derivatives": true,
      "attributionRequired": false
    },
    "target": {
      "engine": null,
      "format": "png",
      "maxBytes": 4194304
    },
    "constraints": {
      "frameWidth": 96,
      "frameHeight": 96,
      "expectedFrames": 1
    }
  },
  "delivery": {
    "engine": null,
    "outputDir": "build/live-raster-smoke"
  }
}
```

## File: production-request-live-vector.json
```json
{
  "schema": "asset-forge/production-request/v1",
  "requestId": "live-vector-smoke",
  "instruction": "Create a clean simple geometric game UI icon with no text, no watermark, and a transparent or empty background.",
  "manifest": {
    "id": "live-vector-icon",
    "project": "asset-forge-live-smoke",
    "type": "icon",
    "importance": "primary",
    "source": {"mode": "generated"},
    "license": {
      "id": "project-owned",
      "commercialUse": true,
      "derivatives": true,
      "attributionRequired": false
    },
    "target": {
      "engine": null,
      "format": "svg",
      "maxBytes": 1048576
    },
    "constraints": {}
  },
  "delivery": {
    "engine": null,
    "outputDir": "build/live-vector-smoke"
  }
}
```

## File: production-request-strict-raster.json
```json
{
  "schema": "asset-forge/production-request/v1",
  "requestId": "strict-raster-qa-smoke",
  "instruction": "Create exactly ONE isolated science-fiction energy cell game sprite, centered and fully visible. One dark metallic cylindrical power cell, with exactly one cyan emissive strip, crisp silhouette and transparent empty space around it. No other cells, no repeated objects, no strips of tile patterns, no text, no watermark, no frame, no floor and NO opaque or painted background.",
  "manifest": {
    "id": "live-raster-cell",
    "project": "asset-forge-live-smoke",
    "type": "sprite",
    "importance": "secondary",
    "source": {
      "mode": "generated"
    },
    "license": {
      "id": "research-evaluation-only",
      "commercialUse": false,
      "derivatives": true,
      "attributionRequired": true
    },
    "target": {
      "engine": null,
      "format": "png",
      "maxBytes": 4194304
    },
    "constraints": {
      "frameWidth": 96,
      "frameHeight": 96,
      "expectedFrames": 1,
      "technicalQualityMin": 0.65,
      "semanticArtReview": true,
      "semanticArtReviewRequired": true,
      "semanticQualityMin": 0.72,
      "maxBorderAlphaRatio": 0.08,
      "requiresAlpha": true
    }
  },
  "delivery": {
    "engine": null,
    "outputDir": "build/strict-raster-qa-smoke"
  }
}
```

## File: production-request.json
```json
{
  "schema": "asset-forge/production-request/v1",
  "requestId": "demo-player-sprite",
  "instruction": "Create a production-ready player sprite sheet and prepare it for the target engine.",
  "manifest": {
    "id": "player",
    "project": "demo-game",
    "type": "sprite-sheet",
    "importance": "primary",
    "source": {
      "mode": "generated"
    },
    "license": {
      "id": "project-owned",
      "commercialUse": true,
      "derivatives": true,
      "attributionRequired": false
    },
    "target": {
      "engine": "godot4",
      "format": "png",
      "maxBytes": 8388608
    },
    "constraints": {
      "pixelArt": true,
      "interpolation": "nearest",
      "frameWidth": 32,
      "frameHeight": 32,
      "requiresAlpha": true
    }
  },
  "delivery": {
    "engine": "godot4",
    "outputDir": "build/demo-player-sprite"
  }
}
```

## File: runtime-atlas.json
```json
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
```
