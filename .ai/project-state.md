# Project state

Status: active

## Working
- Repository is a central visual-asset production pipeline spanning raster 2D, SVG/vector, and 3D.
- PNG validation/decoding/atlas/optimization and Godot animation export are implemented for common non-interlaced and Adam7-interlaced workflows.
- Atlas packing supports optional transparent trim, original source offsets/dimensions, edge extrusion, and deterministic compact shelf packing for variable-size PNG/WebP inputs.
- PNG recompression is no-growth: the original bytes are retained whenever the adaptive candidate is not smaller, including in-place output.
- Indexed PNG decoding supports 1/2/4/8-bit palette indices with packed scanline layout, PNG filtering, row-padding handling, and tRNS palette alpha.
- Grayscale PNG decoding supports 1/2/4/8/16-bit non-interlaced samples, scales low-bit/16-bit luminance to RGBA8, ignores packed padding bits, and applies validated grayscale tRNS transparency.
- RGB, grayscale+alpha, and RGBA decode at both 8-bit and 16-bit depths for non-interlaced and Adam7 images; 16-bit samples are converted to RGBA8 with deterministic rounding and exact pre-conversion tRNS matching.
- Adam7 decoding calculates the exact decompressed byte count across seven passes, unfilters each pass independently, skips empty passes, and reconstructs final pixel coordinates through the shared row decoder.
- PNG parsing now enforces file/chunk/chunk-count/pixel/decompressed-byte ceilings before or during processing, validates IHDR/IDAT/IEND structure, PLTE/tRNS constraints, zlib completion, and exact decompressed scanline size.
- validate-raster now reuses the hardened raster_pack PNG inspector instead of maintaining a weaker duplicate parser.
- 8-bit truecolor tRNS transparency is now applied during RGB→RGBA decoding.
- SVG/vector pipeline validates, sanitizes, normalizes viewBox, removes metadata, and applies icon/ui/logo profiles.
- SVG reference policy now accepts internal fragments only; remote, relative, data URI, CSS @import, and non-fragment CSS url(...) references are rejected or removed by sanitization.
- Vector profiles enforce blocking maxElements/maxBytes/maxDepth budgets, with additional absolute byte/element/depth safety ceilings before recursive processing.
- normalize-svg now rejects malformed existing viewBox values instead of overwriting them.
- glTF/GLB structural inspection validates container/version/core arrays and core index references.
- glTF quality reporting measures accessor-derived vertices/triangles, primitive coverage for normals/UVs/tangents/skinning, PBR texture usage, image embedding/externality, materials, and textures.
- Binary-aware 3D metrics read locally available PNG/JPEG/WebP image dimensions, estimate decoded RGBA8 texture memory with mipmaps, and do not fetch remote URLs.
- WebP raster inspection is dependency-free and shared between raster validation and glTF metrics; VP8X/VP8L/VP8 dimensions, alpha/animation flags, RIFF/chunk structure, reserved fields, and extended canvas consistency are validated.
- Optional Pillow/libwebp backend enables real single-frame WebP→RGBA decoding, mixed PNG/WebP atlas inputs, and WebP encoding; runtime capability is exposed through raster-backend-status.
- CI keeps the primary dependency-free job and adds a separate Pillow-backed WebP job to exercise real decode/encode roundtrips.
- Rig/animation metrics report joints per skin, inverse bind matrices, animation channels/samplers, target paths, animated nodes, keyframe accessor counts, and readable animation durations.
- Deep glTF diagnostics validate accessor layouts/ranges, byteStride/component alignment, JOINTS_0/WEIGHTS_0 consistency, animation sampler/channel references, interpolation modes, target paths, output counts, and strictly increasing key times.
- Godot 4 3D delivery validation checks glTF suitability, stable names, import suffix hints, animation naming, PBR/double-sided materials, tangent needs, remote images, and existing quality-profile results.
- Godot handoff generation creates a minimal importable project with project.godot, copied GLB, manifest/import recommendations, and README.
- Handoff generation is strict by default: a Godot delivery report with ready=true is required unless an explicit debug override is used.
- Optional Asset Forge manifests are validated and embedded as provenance/license metadata in handoff.json.
- Versioned Godot 4 handoff profiles exist for prop, environment, and character assets under profiles/godot4/.
- godot_handoff.py now loads those JSON profiles directly at runtime; duplicated hardcoded profile rules were removed and tests prove file contents drive behavior.
- Engine handoff profiles have a formal JSON Schema plus dependency-free runtime validation for required fields, unknown fields, types, profile identity, and FPS bounds.
- CI runs `python asset_forge.py validate-engine-profiles` so malformed engine profiles fail before handoff generation.
- When a Godot editor binary is available, handoff validation uses headless --import to exercise the real importer; missing Godot remains non-blocking.
- 3D profiles for prop/environment/character include versioned geometry/material/texture budgets plus max texture dimension, estimated texture-memory budget, and character joint budgets.
- gltf_quality.py now loads profiles/3d/*.json directly; duplicated hardcoded 3D quality budgets were removed.
- svg_tools.py now loads profiles/vector/*.json directly; duplicated hardcoded SVG profile rules were removed.
- 3D/vector profile contracts have formal schemas plus dependency-free validation, and CI runs validate-asset-profiles.
- Blender adapter generates reproducible export jobs, Blender Python scripts, and background CLI commands for GLB export.
- 3D toolchain detects Blender, Khronos glTF Validator, glTF Transform, and gltfpack when installed.
- prepare-3d generates Blender → structural validation → quality report → optional Khronos validation → optimization → final validation/quality stages, with optional Godot 4 delivery gating.
- run-3d executes available stages, stops on blocking failures, falls back to validated raw.glb when an optional optimizer is absent, writes production-report.json, and for Godot 4 also emits a handoff project plus optional real import validation.
- production-report.json summarizes step status and raw-vs-final vertex/triangle/file-byte deltas when reports are available.
- star-list integration calls dbrckk/star-list's recommender through its JSON CLI.
- CI compiles all current modules, runs unit tests, checks manifest/plan paths, inspects the 3D toolchain, and smoke-tests the star-list bridge.

## Broken / blockers
- PNG decoding now covers Adam7; remaining raster format gap is primarily WebP pixel decoding/output and broader optimization behavior.
- WebP metadata/container validation is dependency-free. Pixel decode/atlas input/encoding are implemented through optional Pillow+libwebp; native dependency-free WebP pixel decoding is not implemented.
- Compact atlas packing currently does not rotate frames; trimmed source offsets are recorded, but the simple Godot SpriteFrames exporter does not yet reconstruct trimmed source offsets.
- SVG geometric path simplification and raster preview generation are not implemented yet.
- SVG CSS parsing is intentionally lightweight rather than a full CSS parser; current safety logic targets @import and url(...) references.
- Internal glTF validation is still intentionally narrower than Khronos glTF Validator's full specification validation.
- Blender execution itself requires a Blender runtime and cannot be exercised in this ChatGPT environment.
- External glTF optimization requires glTF Transform or gltfpack on the execution host.
- UV overlap/packing quality, geometric normal/tangent correctness, actual GPU compression formats, and rig deformation quality are not yet measured.
- Texture memory is an explicit RGBA8+mipmap estimate, not exact runtime VRAM for compressed formats.
- Direct git clone from this ChatGPT runtime is blocked by DNS.
- GitHub combined-status API has not exposed check entries for the newest commits, so the complete repository CI suite is not yet independently confirmed here.

## Current priority
- Extend atlas metadata/export consumers to understand trim offsets, then consider stronger bin-packing/optional rotation and explicit atlas dimension/byte budgets.

## Validation
- `python -m compileall -q asset_forge.py raster_pack.py godot_export.py starlist_bridge.py animation_infer.py svg_tools.py gltf_tools.py gltf_quality.py gltf_binary_metrics.py blender_adapter.py toolchain_3d.py tests`
- `python -m unittest discover -s tests -v`
- `python asset_forge.py validate examples/asset-manifest.json`
- `python asset_forge.py plan examples/asset-manifest.json`
- `python asset_forge.py validate-svg <input.svg> [--profile icon|ui|logo]`
- `python asset_forge.py validate-gltf <input.gltf|input.glb> [--profile prop|environment|character]`
- `python asset_forge.py diagnose-gltf <input.gltf|input.glb> [--output report.json]`
- `python asset_forge.py validate-godot-3d <input.gltf|input.glb> [--profile prop|environment|character] [--output report.json]`
- `python asset_forge.py prepare-godot-handoff <input.glb> <output_dir> [--profile ...] --delivery-report report.json [--asset-manifest manifest.json] [--allow-unvalidated]`
- `python asset_forge.py validate-godot-handoff <project_dir> [--godot executable]`
- `python asset_forge.py validate-engine-profiles`
- `python asset_forge.py validate-asset-profiles`
- `python asset_forge.py quality-gltf <input.gltf|input.glb> [--profile prop|environment|character] [--output report.json]`
- `python asset_forge.py 3d-toolchain-status`
- `python asset_forge.py prepare-3d <source.blend> <workdir> [--profile ...] [--optimizer ...] [--engine generic|godot4]`
- `python asset_forge.py run-3d <source.blend> <workdir> [--profile ...] [--optimizer ...] [--engine generic|godot4]`

## Last verified
- 2026-09-18: latest GitHub source inspected after adding trim/extrusion, deterministic variable-size shelf packing, CLI support, and no-growth PNG optimization.

<!-- AUTO:START -->
## Automatic repository state

Generated: 2026-09-18T20:24:23Z

### Git
- Branch: `main`
- Head: `a188aa0a6292`
- Commit date: 2026-09-18T22:24:12+02:00
- Commit: docs: record optional WebP pixel backend milestone
- Tracked files: 153

### Recently changed files
- `README.md`
- `tests/test_asset_forge.py`
- `tests/test_raster_backend.py`
- `.github/workflows/validate.yml`
- `asset_forge.py`

### Project signals
- No common build descriptor detected

> Generated by dbrckk/repo-standards. Keep manual priorities and blockers outside the AUTO markers.
<!-- AUTO:END -->
