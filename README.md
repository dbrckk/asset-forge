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


Low-bit grayscale decoding shares the packed-sample scanline path used by indexed PNGs. Samples are unpacked most-significant bits first, row padding is ignored, values are scaled to 8-bit luminance, and grayscale `tRNS` is matched against the original unscaled sample. Out-of-range `tRNS` samples are rejected.


16-bit PNG decoding is supported for grayscale, RGB, grayscale+alpha, and RGBA. Samples are read big-endian after PNG unfiltering and converted to RGBA8 with deterministic rounding. For grayscale/RGB `tRNS`, transparency matching is performed on the original 16-bit samples before down-conversion, preserving exact transparent-color semantics.


Adam7 decoding computes the exact byte budget for all seven passes before zlib decompression, unfilters each pass independently with that pass's scanline width, converts pass rows through the same bit-depth/color-type conversion path as non-interlaced PNGs, and scatters decoded pixels back into final image coordinates. Empty passes for small images are skipped safely.


### WebP raster inspection

Asset Forge now validates WebP RIFF containers without external dependencies. It understands simple lossy `VP8 `, lossless `VP8L`, and extended `VP8X` headers, reports dimensions/alpha/animation/chunk metadata, validates RIFF length and chunk padding, checks reserved VP8X fields, and cross-checks extended canvas dimensions against static image data. `validate-raster` accepts `target.format=webp` for metadata/grid/size/alpha validation, and glTF texture metrics reuse the same WebP parser.

This milestone is inspection/validation only: WebP pixel decoding, atlas input decoding, recompression, and WebP encoding are not implemented yet. PNG remains the decoded/encoded raster working format.
