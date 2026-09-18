# Project state

Status: active

## Working
- Repository is a central visual-asset production pipeline spanning raster 2D, SVG/vector, and 3D.
- PNG validation/decoding/atlas/optimization and Godot animation export are implemented for common 8-bit non-interlaced workflows.
- SVG/vector pipeline validates, sanitizes, normalizes viewBox, removes metadata, and applies icon/ui/logo profiles.
- glTF/GLB structural inspection validates container/version/core arrays and core index references.
- glTF quality reporting measures accessor-derived vertices/triangles, primitive coverage for normals/UVs/tangents/skinning, PBR texture usage, image embedding/externality, materials, and textures.
- Binary-aware 3D metrics read locally available PNG/JPEG/WebP image dimensions, estimate decoded RGBA8 texture memory with mipmaps, and do not fetch remote URLs.
- Rig/animation metrics report joints per skin, inverse bind matrices, animation channels/samplers, target paths, animated nodes, keyframe accessor counts, and readable animation durations.
- Deep glTF diagnostics validate accessor layouts/ranges, byteStride/component alignment, JOINTS_0/WEIGHTS_0 consistency, animation sampler/channel references, interpolation modes, target paths, output counts, and strictly increasing key times.
- Godot 4 3D delivery validation checks glTF suitability, stable names, import suffix hints, animation naming, PBR/double-sided materials, tangent needs, remote images, and existing quality-profile results.
- Godot handoff generation creates a minimal importable project with project.godot, copied GLB, manifest/import recommendations, and README.
- Handoff generation is strict by default: a Godot delivery report with ready=true is required unless an explicit debug override is used.
- Optional Asset Forge manifests are validated and embedded as provenance/license metadata in handoff.json.
- Versioned Godot 4 handoff profiles exist for prop, environment, and character assets under profiles/godot4/.
- godot_handoff.py now loads those JSON profiles directly at runtime; duplicated hardcoded profile rules were removed and tests prove file contents drive behavior.
- When a Godot editor binary is available, handoff validation uses headless --import to exercise the real importer; missing Godot remains non-blocking.
- 3D profiles for prop/environment/character include versioned geometry/material/texture budgets plus max texture dimension, estimated texture-memory budget, and character joint budgets.
- Blender adapter generates reproducible export jobs, Blender Python scripts, and background CLI commands for GLB export.
- 3D toolchain detects Blender, Khronos glTF Validator, glTF Transform, and gltfpack when installed.
- prepare-3d generates Blender → structural validation → quality report → optional Khronos validation → optimization → final validation/quality stages, with optional Godot 4 delivery gating.
- run-3d executes available stages, stops on blocking failures, falls back to validated raw.glb when an optional optimizer is absent, writes production-report.json, and for Godot 4 also emits a handoff project plus optional real import validation.
- production-report.json summarizes step status and raw-vs-final vertex/triangle/file-byte deltas when reports are available.
- star-list integration calls dbrckk/star-list's recommender through its JSON CLI.
- CI compiles all current modules, runs unit tests, checks manifest/plan paths, inspects the 3D toolchain, and smoke-tests the star-list bridge.

## Broken / blockers
- PNG decoding still does not support 16-bit or interlaced PNGs.
- WebP raster output is not implemented yet.
- SVG geometric path simplification and raster preview generation are not implemented yet.
- Internal glTF validation is still intentionally narrower than Khronos glTF Validator's full specification validation.
- Blender execution itself requires a Blender runtime and cannot be exercised in this ChatGPT environment.
- External glTF optimization requires glTF Transform or gltfpack on the execution host.
- UV overlap/packing quality, geometric normal/tangent correctness, actual GPU compression formats, and rig deformation quality are not yet measured.
- Texture memory is an explicit RGBA8+mipmap estimate, not exact runtime VRAM for compressed formats.
- Direct git clone from this ChatGPT runtime is blocked by DNS.
- GitHub combined-status API has not exposed check entries for the newest commits, so the complete repository CI suite is not yet independently confirmed here.

## Current priority
- Add explicit schema validation for engine handoff profiles and only add another engine adapter when a consuming project requires it.

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
- `python asset_forge.py quality-gltf <input.gltf|input.glb> [--profile prop|environment|character] [--output report.json]`
- `python asset_forge.py 3d-toolchain-status`
- `python asset_forge.py prepare-3d <source.blend> <workdir> [--profile ...] [--optimizer ...] [--engine generic|godot4]`
- `python asset_forge.py run-3d <source.blend> <workdir> [--profile ...] [--optimizer ...] [--engine generic|godot4]`

## Last verified
- 2026-09-18: latest GitHub source inspected after making versioned Godot JSON profiles the runtime source of truth and fixing the missing-delivery-report test.

<!-- AUTO:START -->
## Automatic repository state

Generated: 2026-09-18T18:28:10Z

### Git
- Branch: `main`
- Head: `e53aa55e8be7`
- Commit date: 2026-09-18T20:28:01+02:00
- Commit: docs: record Godot handoff milestone
- Tracked files: 93

### Recently changed files
- `README.md`
- `.github/workflows/validate.yml`
- `tests/test_godot_handoff.py`
- `toolchain_3d.py`

### Project signals
- No common build descriptor detected

> Generated by dbrckk/repo-standards. Keep manual priorities and blockers outside the AUTO markers.
<!-- AUTO:END -->
