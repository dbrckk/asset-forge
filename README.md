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
