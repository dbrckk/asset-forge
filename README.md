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
