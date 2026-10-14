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
runtime_atlas_web.test.mjs
test_animation_infer.py
test_art_quality.py
test_asset_forge.py
test_asset_library.py
test_asset_profile_validation.py
test_backend_history.py
test_blender_adapter.py
test_cloudflare_backend.py
test_colab_queue.py
test_engine_profile_validation.py
test_fulfill.py
test_generator_backends.py
test_gltf_binary_metrics.py
test_gltf_diagnostics.py
test_gltf_quality.py
test_gltf_tools.py
test_godot_3d_delivery.py
test_godot_export.py
test_godot_handoff.py
test_kaggle_3d_backend.py
test_kaggle_backend.py
test_operational_status.py
test_production_contract.py
test_production_executor.py
test_production_os_ai_dev_server_live_e2e_workflow.py
test_raster_backend.py
test_raster_pack.py
test_remote_batch.py
test_runtime_atlas.py
test_semantic_art_review.py
test_starlist_bridge.py
test_svg_tools.py
test_toolchain_3d.py
test_vector_backend.py
test_visual_similarity.py
```

# Files

## File: runtime_atlas_web.test.mjs
```javascript
save()
restore()
translate(x, y)
rotate(angle)
drawImage(...args)
⋮----
translate(...args)
rotate(...args)
⋮----
onFrame(sample)
onFinish(sample)
⋮----
onLoop(event)
⋮----
onEvent(event)
⋮----
function createMockWebGL2()
⋮----
const object = (type) => (
⋮----
createShader(type)
shaderSource(shader, source)
compileShader(shader)
getShaderParameter(shader, parameter)
getShaderInfoLog()
deleteShader(shader)
createProgram()
attachShader(program, shader)
linkProgram(program)
getProgramParameter(program, parameter)
getProgramInfoLog()
deleteProgram(program)
createVertexArray()
deleteVertexArray(vao)
createBuffer()
createTexture()
deleteTexture(texture)
deleteBuffer(buffer)
bindVertexArray(vao)
bindBuffer(target, buffer)
bufferData(target, data, usage)
bufferSubData(target, offset, data)
enableVertexAttribArray(location)
vertexAttribPointer(location, size, type, normalized, stride, offset)
vertexAttribDivisor(location, divisor)
getUniformLocation(program, name)
enable(capability)
blendFunc(source, destination)
useProgram(program)
uniform2f(location, x, y)
activeTexture(texture)
bindTexture(target, texture)
pixelStorei(parameter, value)
texParameteri(target, parameter, value)
texImage2D(...args)
generateMipmap(target)
uniform1i(location, value)
drawElementsInstanced(mode, count, type, offset, instances)
⋮----
resolveTexture(textureKey, entry)
⋮----
const fakeFetch = async (url) =>
⋮----
async blob()
⋮----
const fakeCreateImageBitmap = async (blob, options) =>
⋮----
fetchImpl: async () => (
⋮----
fetchImpl: async (url) =>
createImageBitmapImpl: async (blob) => (
⋮----
fetchImpl: async (url) => (
⋮----
function createMockCanvas()
⋮----
addEventListener(type, handler)
removeEventListener(type, handler)
dispatch(type, event =
getContext()
⋮----
resizeGl.viewport = (...args)
⋮----
contextGlA.viewport = (...args)
⋮----
contextGlB.viewport = (...args)
⋮----
onContextLost()
onContextRestored()
⋮----
preventDefault()
⋮----
entityRuntimeGlA.viewport = (...args)
⋮----
entityRuntimeGlB.viewport = (...args)
⋮----
suppliedRuntimeGl.viewport = (...args)
⋮----
onFrame(event)
⋮----
animatedRuntimeGlA.viewport = (...args)
⋮----
animatedRuntimeGlB.viewport = (...args)
⋮----
hierarchyRuntimeGl.viewport = (...args)
⋮----
layerRuntimeGl.viewport = (...args)
⋮----
cameraRuntimeGl.viewport = (...args)
⋮----
followRuntimeGl.viewport = (...args)
⋮----
boundedRuntimeGl.viewport = (...args)
⋮----
pickingRuntimeGl.viewport = (...args)
⋮----
pick(x, y)
toWorld(x, y)
onEnter(event)
onLeave(event)
onDown(event)
onClick(event)
onDragStart(event)
onDrag(event)
onDragEnd(event)
onUp(event)
⋮----
pick()
⋮----
pointerRuntimeGl.viewport = (...args)
⋮----
autoDragGl.viewport = (...args)
⋮----
createImageBitmapImpl: async () => (
⋮----
constrainedDragGl.viewport = (...args)
⋮----
onChange(event)
⋮----
selectionRuntimeGl.viewport = (...args)
⋮----
groupDragGl.viewport = (...args)
⋮----
historyRuntimeGl.viewport = (...args)
```

## File: test_animation_infer.py
```python
class AnimationInferTests(unittest.TestCase)
⋮----
def test_groups_numbered_filenames(self)
⋮----
metadata = {
⋮----
result = infer_animations(metadata, default_fps=8)
animations = {item["name"]: item for item in result["animations"]}
⋮----
def test_uses_stem_when_no_numeric_suffix(self)
⋮----
result = infer_animations(metadata)
⋮----
def test_missing_names_fall_back_to_default(self)
⋮----
result = infer_animations(metadata, default_loop=False)
⋮----
def test_rejects_invalid_fps(self)
```

## File: test_art_quality.py
```python
class ArtQualityTests(unittest.TestCase)
⋮----
def _image(self, path, *, box, color=(210, 70, 45, 255), size=(96, 96))
⋮----
image = Image.new("RGBA", size, (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
⋮----
def test_centered_transparent_sprite_passes_reasonable_quality_gate(self)
⋮----
path = Path(td) / "sprite.png"
⋮----
result = evaluate_raster_art(path, {
⋮----
def test_clipped_sprite_reports_border_warning(self)
⋮----
path = Path(td) / "clipped.png"
⋮----
def test_fully_opaque_raster_fails_alpha_requirement(self)
⋮----
path = Path(td) / "opaque.png"
⋮----
def test_unstable_sprite_sheet_frame_occupancy_reduces_consistency(self)
⋮----
path = Path(td) / "sheet.png"
image = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
⋮----
def test_duplicate_animation_frames_can_fail_strict_diversity_gate(self)
⋮----
path = Path(td) / "duplicate-sheet.png"
⋮----
x = col * 96
y = row * 96
⋮----
def test_unstable_animation_center_can_fail_pivot_gate(self)
⋮----
path = Path(td) / "drift-sheet.png"
image = Image.new("RGBA", (192, 96), (0, 0, 0, 0))
```

## File: test_asset_forge.py
```python
ROOT = Path(__file__).resolve().parents[1]
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
signature = b"\x89PNG\r\n\x1a\n"
ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
parts = [signature, chunk(b"IHDR", ihdr_data)]
⋮----
palette = bytearray()
⋮----
value = index % 256
⋮----
channels = {2: 3, 6: 4}.get(color_type, 1)
row = b"\x00" + (b"\x00" * width * channels)
⋮----
class AssetForgeTests(unittest.TestCase)
⋮----
def load_example(self)
⋮----
def test_example_manifest_is_valid(self)
⋮----
def test_pixel_art_rejects_non_nearest_interpolation(self)
⋮----
manifest = self.load_example()
⋮----
def test_external_asset_requires_uri(self)
⋮----
errors = asset_forge.validate_manifest(manifest)
⋮----
def test_incompatible_commercial_license_is_rejected(self)
⋮----
def test_plan_routes_sprite_to_2d_pipeline(self)
⋮----
plan = asset_forge.build_plan(manifest, ROOT)
⋮----
tool_ids = [item["id"] for item in plan["candidateTools"]]
⋮----
def test_secondary_custom_asset_prompts_reuse_search(self)
⋮----
def test_png_sprite_grid_validation_passes(self)
⋮----
image = Path(tmp) / "sprite.png"
⋮----
def test_png_sprite_grid_validation_rejects_bad_width(self)
⋮----
def test_png_alpha_requirement(self)
⋮----
def test_palette_transparency_and_max_colors(self)
⋮----
def test_power_of_two_atlas(self)
⋮----
def test_atlas_manifest_contains_frame_rectangles(self)
⋮----
atlas = asset_forge.build_atlas_manifest(image, manifest)
⋮----
def test_webp_raster_validation_supports_dimensions_and_alpha(self)
⋮----
vp8x = bytes([0x10, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
alpha = b"\x00\x00"
chunks = (
body = b"WEBP" + chunks
data = b"RIFF" + struct.pack("<I", len(body)) + body
⋮----
image = Path(tmp) / "sprite.webp"
⋮----
def test_webp_max_colors_constraint_is_rejected(self)
⋮----
width = height = 32
vp8x = bytes([0, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
⋮----
def test_raster_target_format_mismatch_is_reported(self)
⋮----
def test_invalid_png_crc_is_rejected(self)
⋮----
image = Path(tmp) / "bad.png"
⋮----
data = bytearray(image.read_bytes())
```

## File: test_asset_library.py
```python
class AssetLibraryTests(unittest.TestCase)
⋮----
def job(self)
⋮----
def result(self, artifact: Path, *, perceptual_hash="0f0f")
⋮----
def test_exact_fingerprint_reuses_validated_object(self)
⋮----
root = Path(td)
library = root / "library.json"
artifact = root / "rex.png"
⋮----
fingerprint = request_fingerprint(self.job(), backend="pollinations")
entry = record_success(
⋮----
hit = lookup(library, fingerprint)
⋮----
def test_new_validated_generation_increments_version(self)
⋮----
first = root / "first.png"
second = root / "second.png"
⋮----
first_fp = request_fingerprint(self.job(), backend="pollinations")
second_job = self.job()
⋮----
second_fp = request_fingerprint(second_job, backend="pollinations")
⋮----
one = record_success(
two = record_success(
⋮----
payload = json.loads(library.read_text())
⋮----
def test_repeated_success_record_is_idempotent(self)
⋮----
def test_reference_sha_changes_cache_key(self)
⋮----
ref = root / "parent.png"
⋮----
a = request_fingerprint(
⋮----
b = request_fingerprint(
⋮----
def test_reusable_content_key_ignores_project_identity(self)
⋮----
first = self.job()
second = self.job()
⋮----
a = reusable_content_fingerprint(first, backend="pollinations")
b = reusable_content_fingerprint(second, backend="pollinations")
⋮----
def test_cross_project_lookup_returns_content_compatible_asset(self)
⋮----
content_fp = reusable_content_fingerprint(
⋮----
hit = lookup_reusable(library, content_fp)
⋮----
def test_higher_quality_near_duplicate_becomes_preferred_version(self)
⋮----
low = self.result(first, perceptual_hash="0f0f")
⋮----
high = self.result(second, perceptual_hash="0f0e")
⋮----
old = next(item for item in payload["entries"] if item["sha256"] == one["sha256"])
new = next(item for item in payload["entries"] if item["sha256"] == two["sha256"])
⋮----
def test_lower_quality_near_duplicate_is_marked_duplicate(self)
⋮----
high = self.result(first, perceptual_hash="0f0f")
⋮----
low = self.result(second, perceptual_hash="0f0e")
⋮----
def test_perceptual_deduplication_returns_near_matches(self)
⋮----
fp = request_fingerprint(self.job())
⋮----
rows = similar_entries(
```

## File: test_asset_profile_validation.py
```python
class AssetProfileValidationTests(unittest.TestCase)
⋮----
def test_repository_profiles_all_validate(self)
⋮----
root = Path(__file__).resolve().parents[1]
report = validate_all_asset_profiles(root)
⋮----
def test_3d_loader_reads_versioned_budget(self)
⋮----
profile = load_3d_profile("character")
⋮----
def test_vector_loader_reads_versioned_budget(self)
⋮----
profile = load_vector_profile("icon")
⋮----
def test_invalid_3d_unknown_rule_fails(self)
⋮----
data = {
errors = validate_3d_profile_data(data, "prop")
⋮----
def test_invalid_vector_type_fails(self)
⋮----
errors = validate_vector_profile_data(data, "icon")
⋮----
def test_3d_loader_uses_file_as_source_of_truth(self)
⋮----
root = Path(tmp)
profile_dir = root / "profiles" / "3d"
⋮----
loaded = load_3d_profile("prop", root=root)
⋮----
def test_vector_loader_uses_file_as_source_of_truth(self)
⋮----
profile_dir = root / "profiles" / "vector"
⋮----
loaded = load_vector_profile("icon", root=root)
```

## File: test_backend_history.py
```python
class BackendHistoryTests(unittest.TestCase)
⋮----
def test_missing_or_invalid_history_falls_back_safely(self)
⋮----
root = Path(td)
missing = root / "missing.json"
⋮----
invalid = root / "invalid.json"
⋮----
def test_default_order_is_preserved_without_enough_samples(self)
⋮----
path = Path(td) / "history.json"
⋮----
def test_repeated_cloudflare_failures_move_auto_route_to_kaggle(self)
⋮----
history = {
⋮----
def test_reliable_observed_cloudflare_stays_ahead_of_unknown_kaggle(self)
⋮----
cloudflare = backend_score(history, "cloudflare", prior=1.0)
unknown_kaggle = backend_score(history, "kaggle-qwen", prior=0.98)
⋮----
def test_record_generation_result_tracks_fallback_and_quality(self)
⋮----
result = {
⋮----
history = record_generation_result(path, result)
⋮----
cloudflare = history["backends"]["cloudflare"]
⋮----
kaggle = history["backends"]["kaggle-qwen"]
⋮----
persisted = load_history(path)
⋮----
def test_record_generation_result_tracks_regeneration_pressure(self)
⋮----
history = record_generation_result(path, {
⋮----
stats = history["backends"]["cloudflare"]
⋮----
def test_retry_strategy_effectiveness_is_learned(self)
⋮----
strategies = history["backends"]["kaggle-qwen"]["retryStrategies"]
⋮----
def test_retry_strategy_ranking_prefers_proven_corrections(self)
⋮----
ranked = rank_retry_strategies(
⋮----
def test_3d_result_learns_from_nested_reference_generation(self)
⋮----
triposr = history["backends"]["kaggle-triposr"]
⋮----
raster = history["backends"]["kaggle-qwen"]
⋮----
def test_vector_result_records_underlying_raster_backend(self)
```

## File: test_blender_adapter.py
```python
class BlenderAdapterTests(unittest.TestCase)
⋮----
def test_build_export_job_defaults(self)
⋮----
job = build_blender_export_job(
⋮----
def test_selection_and_animation_flags(self)
⋮----
def test_rendered_script_opens_source_and_exports(self)
⋮----
script = render_blender_python(job)
⋮----
def test_render_command_uses_background_mode(self)
⋮----
command = render_blender_command("blender", Path("build/export.py"))
```

## File: test_cloudflare_backend.py
```python
class Headers
⋮----
def __init__(self, content_type)
def get(self, name)
⋮----
class Response
⋮----
def __init__(self, body, content_type="image/png")
def __enter__(self)
def __exit__(self, exc_type, exc, tb)
def read(self)
⋮----
class CloudflareBackendTests(unittest.TestCase)
⋮----
def test_status_requires_both_credentials(self)
⋮----
def test_extracts_base64_json_image(self)
⋮----
raw = json.dumps({"result": {"image": base64.b64encode(b"PNG").decode()}}).encode()
⋮----
def test_generate_sends_img2img_payload(self)
⋮----
root = Path(td)
ref = root / "ref.png"
⋮----
out = root / "out.png"
seen = {}
⋮----
def opener(request, timeout)
⋮----
result = generate(
⋮----
# Official FLUX.2 Klein Workers AI protocol uses multipart binary
# input_image_0..3, not SDXL JSON image_b64. Verify two references
# and the Apache-2.0 4B endpoint without any network call.
⋮----
# The base no-deps suite retains its historical dependencies.
# CI separately reruns this test after installing Pillow.
⋮----
ref2 = root / "ref2.png"
⋮----
seen_flux = {}
⋮----
def flux_opener(request, timeout)
⋮----
# Reject disallowed reference geometry before any chargeable call.
⋮----
def test_generate_rejects_missing_credentials(self)
```

## File: test_colab_queue.py
```python
class ColabQueueTests(unittest.TestCase)
⋮----
def base_job(self)
⋮----
def test_build_job_is_deterministic(self)
⋮----
one = build_colab_job(self.base_job())
two = build_colab_job(self.base_job())
⋮----
def test_build_job_limits_references_to_ten(self)
⋮----
refs = [f"https://example.com/{index}.png" for index in range(12)]
value = build_colab_job(self.base_job(), reference_urls=refs)
⋮----
def test_missing_instruction_is_rejected(self)
⋮----
def test_job_id_changes_with_semantic_input(self)
⋮----
first = build_colab_job(self.base_job())
changed = self.base_job()
⋮----
second = build_colab_job(changed)
⋮----
def test_job_id_is_short_content_hash(self)
⋮----
value = job_id({"x": 1})
```

## File: test_engine_profile_validation.py
```python
class EngineProfileValidationTests(unittest.TestCase)
⋮----
def valid_profile(self)
⋮----
def test_valid_profile_passes(self)
⋮----
def test_missing_required_field_fails(self)
⋮----
data = self.valid_profile()
⋮----
errors = validate_godot_profile_data(data, "prop")
⋮----
def test_unknown_field_fails(self)
⋮----
def test_wrong_type_fails(self)
⋮----
def test_invalid_fps_fails(self)
⋮----
def test_profile_name_mismatch_fails(self)
⋮----
errors = validate_godot_profile_data(data, "character")
⋮----
def test_invalid_json_file_fails(self)
⋮----
path = Path(tmp) / "prop.json"
⋮----
def test_repository_profiles_all_validate(self)
⋮----
root = Path(__file__).resolve().parents[1]
report = validate_all_godot_profiles(root)
```

## File: test_fulfill.py
```python
ROOT = Path(__file__).resolve().parents[1]
⋮----
class FulfillCommandTests(unittest.TestCase)
⋮----
def test_parser_accepts_end_to_end_fulfill_command(self)
⋮----
args = asset_forge.parser().parse_args(
⋮----
def test_parser_accepts_provided_source(self)
⋮----
def test_production_inputs_are_persisted_for_handoff_and_audit(self)
⋮----
request = asset_forge.load_json(ROOT / "examples/production-request.json")
plan = asset_forge.build_plan(request["manifest"], ROOT)
job = asset_forge.build_production_job(request, plan)
⋮----
out = Path(td)
⋮----
written_job = json.loads((out / "production-job.json").read_text())
written_manifest = json.loads((out / "asset-manifest.json").read_text())
written_plan = json.loads((out / "production-plan.json").read_text())
⋮----
def test_compiled_job_routes_raster_to_generated_raster_executor(self)
⋮----
job = {
expected = {"success": True, "artifact": "hero.png"}
⋮----
result = asset_forge.execute_compiled_production_job(
⋮----
def test_compiled_job_forwards_provided_source(self)
⋮----
source = Path("downloads/icon.svg")
expected = {"success": True, "artifact": "icon.svg"}
⋮----
def test_godot_sprite_sheet_gets_engine_handoff(self)
⋮----
artifact = out / "hero.png"
⋮----
report = out / "production-report.json"
⋮----
result = {
atlas = {
⋮----
enriched = asset_forge._enrich_engine_handoff(job, result, out)
⋮----
persisted = json.loads(report.read_text(encoding="utf-8"))
⋮----
def test_godot_3d_gets_handoff_and_import_validation(self)
⋮----
artifact = out / "crate.glb"
⋮----
handoff = {"projectDir": str(out / "godot-handoff")}
```

## File: test_generator_backends.py
```python
def job()
⋮----
class GeneratorBackendsTests(unittest.TestCase)
⋮----
def test_prompt_preserves_hard_sprite_constraints(self)
⋮----
prompt = build_generation_prompt(job())
⋮----
def test_prompt_adds_alpha_and_premium_quality_guards(self)
⋮----
value = job()
⋮----
prompt = build_generation_prompt(value)
⋮----
def test_technical_retry_guidance_targets_measured_failures(self)
⋮----
guidance = _technical_retry_guidance({
⋮----
def test_pollinations_command_never_contains_api_key(self)
⋮----
command = pollinations_command(
⋮----
def test_vector_generation_defaults_to_recraft_svg_model(self)
⋮----
vector_job = job()
⋮----
def test_backend_status_reports_auth_without_secret_value(self)
⋮----
status = generator_backend_status(
⋮----
def test_execute_generated_asset_uses_bounded_subprocess_and_output(self)
⋮----
out = Path(td)
def runner(command, **kwargs)
⋮----
target = Path(command[command.index("--output") + 1])
⋮----
class Result
⋮----
returncode = 0
stdout = '{"ok":true}'
stderr = ""
⋮----
result = execute_generated_asset(
⋮----
def test_generator_metadata_redacts_credentials_before_reporting(self)
⋮----
stdout = (
⋮----
def test_backend_status_reports_imagen_codex_without_exposing_token(self)
⋮----
def which(name)
⋮----
def test_imagen_codex_command_uses_raster_output_and_no_token_argument(self)
⋮----
raster_job = job()
⋮----
command = imagen_codex_command(
⋮----
def test_imagen_codex_rejects_vector_generation(self)
⋮----
def test_execute_generated_asset_supports_imagen_codex_raster(self)
⋮----
target = out / "generated-source.png"
⋮----
stdout = '{"files":["generated-source.png"],"provider":"codex"}'
⋮----
def test_imagen_codex_command_accepts_local_visual_references(self)
⋮----
def test_execute_generated_asset_supports_imagen_visual_reference_and_retry(self)
⋮----
reference = out / "parent.png"
⋮----
scores = iter([0.2, 0.83])
calls = []
⋮----
def test_cloudflare_reference_routes_directly_to_kaggle_qwen(self)
⋮----
seen = {}
⋮----
def fake_kaggle(prompt, output, **kwargs)
⋮----
# Commercial references cannot be sent to research-licensed
# Qwen; Cloudflare must use FLUX.2 Klein 4B Apache-2.0 and
# preserve ALL refs. This offline stub creates no provider usage.
⋮----
second = out / "style.png"
⋮----
commercial = job()
⋮----
flux_seen = {}
⋮----
def fake_flux(prompt, output, **kwargs)
⋮----
generated = execute_generated_asset(
⋮----
# Merely claiming a custom model name cannot bypass licensing.
⋮----
def test_auto_cloudflare_failure_falls_back_to_kaggle_qwen(self)
⋮----
def test_explicit_cloudflare_failure_does_not_silently_fallback(self)
⋮----
def test_auto_backend_uses_adaptive_history_after_enough_samples(self)
⋮----
history_path = Path(td) / "backend-history.json"
⋮----
def test_auto_kaggle_failure_can_fall_back_to_cloudflare(self)
⋮----
def fake_cloudflare(prompt, output, **kwargs)
⋮----
def test_successful_generation_persists_backend_history(self)
⋮----
root = Path(td)
out = root / "out"
history_path = root / "backend-history.json"
⋮----
history = load_history(history_path)
⋮----
def test_auto_backend_prefers_cloudflare_for_raster_when_ready(self)
⋮----
def test_auto_backend_uses_kaggle_when_cloudflare_unavailable(self)
⋮----
def test_auto_backend_does_not_fall_back_to_imagen_codex(self)
⋮----
def test_auto_vector_prefers_vtracer_with_free_raster_source(self)
⋮----
def test_auto_vector_falls_back_to_pollinations_when_vtracer_unavailable(self)
⋮----
def test_vtracer_vector_generation_uses_free_cloudflare_source(self)
⋮----
def fake_vectorizer(source, output, **kwargs)
⋮----
def test_vtracer_vector_source_falls_back_to_kaggle(self)
⋮----
def test_auto_backend_rejects_vector_when_only_imagen_is_ready(self)
⋮----
def test_required_alpha_runs_transparency_processor_before_normalization(self)
⋮----
alpha_job = job()
⋮----
stdout = "{}"
⋮----
def transparency(path, value, **kwargs)
⋮----
def normalize(raw, output, value)
⋮----
def test_3d_prompt_is_reference_image_oriented(self)
⋮----
three_d = job()
⋮----
prompt = build_generation_prompt(three_d)
⋮----
def test_execute_generated_3d_uses_uploaded_reference_and_bearer_auth(self)
⋮----
def generator(value, output_dir, **kwargs)
⋮----
source = Path(output_dir) / "generated-source.png"
⋮----
def upload_runner(command, **kwargs)
⋮----
stdout = '{"url":"https://media.pollinations.ai/ref-123","id":"ref-123"}'
⋮----
class Response
⋮----
status = 200
def __enter__(self)
def __exit__(self, exc_type, exc, tb)
def read(self, limit=-1)
⋮----
def opener(request, timeout)
⋮----
result = execute_generated_3d_asset(
⋮----
payload = __import__("json").loads(seen["body"].decode("utf-8"))
⋮----
def test_3d_generation_requires_configured_backend(self)
⋮----
def test_auto_3d_secondary_prefers_free_kaggle_triposr(self)
⋮----
def kaggle_generator(reference_path, output, **kwargs)
⋮----
def test_3d_generation_persists_backend_history(self)
⋮----
history = __import__("json").loads(history_path.read_text())
⋮----
def test_auto_3d_primary_prefers_pollinations_trellis(self)
⋮----
stdout = '{"url":"https://media.pollinations.ai/primary-ref"}'
⋮----
def test_auto_3d_triposr_failure_falls_back_to_pollinations(self)
⋮----
stdout = '{"url":"https://media.pollinations.ai/fallback-ref"}'
⋮----
def test_unsupported_generated_type_fails_closed(self)
⋮----
bad = job()
⋮----
def test_raster_generation_uploads_and_passes_visual_reference(self)
⋮----
seen = []
⋮----
class Upload
⋮----
stdout = '{"url":"https://media.pollinations.ai/parent-ref"}'
⋮----
class Generate
⋮----
generate = [command for command in seen if command[1:3] == ["gen", "image"]][0]
⋮----
def test_visual_reference_rejects_vector_generation(self)
⋮----
reference = root / "parent.png"
⋮----
def test_visual_similarity_retries_until_threshold_passes(self)
⋮----
scores = iter([0.20, 0.73])
generation_calls = []
⋮----
def test_visual_similarity_fails_after_retry_budget(self)
⋮----
def test_technical_quality_retries_without_visual_reference(self)
⋮----
scores = iter([0.31, 0.74])
⋮----
history = result["technicalQuality"]["attempts"]
⋮----
def test_technical_quality_rejects_after_retry_budget(self)
```

## File: test_gltf_binary_metrics.py
```python
PNG_SIG = b"\x89PNG\r\n\x1a\n"
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
def tiny_png(width=2, height=4)
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
raw = b"".join(b"\x00" + (b"\x00\x00\x00\xff" * width) for _ in range(height))
⋮----
class GltfBinaryMetricsTests(unittest.TestCase)
⋮----
def test_data_uri_png_dimensions_and_memory(self)
⋮----
payload = tiny_png(2, 4)
uri = "data:image/png;base64," + base64.b64encode(payload).decode("ascii")
data = {
⋮----
path = Path(tmp) / "asset.gltf"
⋮----
items = inspect_images(path)
⋮----
def test_local_external_png_dimensions(self)
⋮----
root = Path(tmp)
⋮----
path = root / "asset.gltf"
⋮----
def test_data_uri_webp_dimensions_use_shared_inspector(self)
⋮----
bits = (width - 1) | ((height - 1) << 14)
vp8l = b"\x2f" + bits.to_bytes(4, "little")
chunk_bytes = b"VP8L" + struct.pack("<I", len(vp8l)) + vp8l + b"\x00"
body = b"WEBP" + chunk_bytes
payload = b"RIFF" + struct.pack("<I", len(body)) + body
uri = "data:image/webp;base64," + base64.b64encode(payload).decode("ascii")
⋮----
def test_animation_and_rig_metrics(self)
⋮----
metrics = inspect_rig_and_animation(path)
⋮----
def test_quality_report_includes_binary_metrics(self)
⋮----
payload = tiny_png(4, 4)
⋮----
report = quality_report(path, "prop")
```

## File: test_gltf_diagnostics.py
```python
class GltfDiagnosticsTests(unittest.TestCase)
⋮----
def write(self, root: Path, data: dict) -> Path
⋮----
path = root / "asset.gltf"
⋮----
def test_accessor_byte_range_and_layout(self)
⋮----
payload = struct.pack("<9f", *[float(i) for i in range(9)])
uri = "data:application/octet-stream;base64," + base64.b64encode(payload).decode("ascii")
data = {
⋮----
report = inspect_accessors(self.write(Path(tmp), data))
⋮----
def test_accessor_overrun_is_rejected(self)
⋮----
def test_skinning_requires_matching_vec4_attributes(self)
⋮----
report = inspect_skinning_consistency(self.write(Path(tmp), data))
⋮----
def test_animation_duration_reads_real_key_times(self)
⋮----
times = struct.pack("<3f", 0.0, 0.5, 2.0)
output = struct.pack("<9f", *([0.0] * 9))
payload = times + output
⋮----
report = inspect_animation_consistency(self.write(Path(tmp), data))
⋮----
def test_non_increasing_animation_times_are_rejected(self)
⋮----
times = struct.pack("<3f", 0.0, 1.0, 1.0)
⋮----
def test_deep_report_has_all_sections(self)
⋮----
path = self.write(Path(tmp), {"asset": {"version": "2.0"}})
report = deep_gltf_diagnostics(path)
```

## File: test_gltf_quality.py
```python
class GltfQualityTests(unittest.TestCase)
⋮----
def write(self, root: Path, data: dict) -> Path
⋮----
path = root / "asset.gltf"
⋮----
def base(self)
⋮----
def test_counts_vertices_and_triangles(self)
⋮----
report = build_quality_report(self.write(Path(tmp), self.base()))
⋮----
def test_triangle_strip_count(self)
⋮----
data = self.base()
⋮----
report = build_quality_report(self.write(Path(tmp), data))
⋮----
def test_character_quality_requires_skin_attributes(self)
⋮----
evaluation = evaluate_quality(report, "character")
⋮----
def test_textured_primitive_requires_uv(self)
⋮----
report = quality_report(self.write(Path(tmp), data), "prop")
⋮----
def test_normal_map_without_tangent_warns(self)
⋮----
def test_external_image_is_reported(self)
⋮----
report = quality_report(self.write(Path(tmp), self.base()), "prop")
⋮----
def test_untextured_primitive_does_not_require_uv(self)
⋮----
def test_strict_prop_budget_is_blocking(self)
⋮----
report = {
evaluation = evaluate_quality(report, "prop")
⋮----
def test_prop_rejects_non_pbr_materials_and_animations(self)
```

## File: test_gltf_tools.py
```python
def make_glb(data: dict) -> bytes
⋮----
payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
padding = (4 - (len(payload) % 4)) % 4
⋮----
total = 12 + 8 + len(payload)
⋮----
class GltfToolsTests(unittest.TestCase)
⋮----
def base(self)
⋮----
def test_valid_gltf(self)
⋮----
path = Path(tmp) / "asset.gltf"
⋮----
def test_invalid_version(self)
⋮----
data = self.base()
⋮----
def test_glb_json_chunk(self)
⋮----
path = Path(tmp) / "asset.glb"
⋮----
def test_character_requires_skin(self)
⋮----
path = Path(tmp) / "character.gltf"
⋮----
def test_character_with_skin_passes(self)
⋮----
def test_out_of_range_mesh_reference_is_rejected(self)
⋮----
path = Path(tmp) / "bad.gltf"
⋮----
def test_out_of_range_accessor_reference_is_rejected(self)
⋮----
def test_valid_skin_joint_reference_passes(self)
⋮----
path = Path(tmp) / "skin.gltf"
```

## File: test_godot_3d_delivery.py
```python
class Godot3DDeliveryTests(unittest.TestCase)
⋮----
def write(self, root: Path, data: dict, suffix: str = ".glb.json") -> Path
⋮----
path = root / ("asset.gltf" if suffix == ".gltf" else "asset.gltf")
⋮----
def base(self)
⋮----
def test_detects_godot_name_suffixes(self)
⋮----
report = godot_3d_delivery_report(
⋮----
def test_detects_collision_import_hints(self)
⋮----
data = self.base()
⋮----
def test_duplicate_node_names_warn(self)
⋮----
report = godot_3d_delivery_report(self.write(Path(tmp), data), "prop")
⋮----
def test_loop_animation_hint_detected(self)
⋮----
def test_remote_image_blocks_delivery(self)
⋮----
def test_double_sided_material_warns(self)
⋮----
def test_delivery_report_includes_runtime_lod_collision_and_pbr_plan(self)
⋮----
path = self.write(Path(tmp), data)
result = godot_3d_delivery_report(path, "prop")
⋮----
plan = result["runtimePlan"]
```

## File: test_godot_export.py
```python
class GodotExportTests(unittest.TestCase)
⋮----
def metadata(self)
⋮----
def test_render_spriteframes_uses_atlas_regions(self)
⋮----
rendered = render_spriteframes(
⋮----
def test_trimmed_frame_emits_atlas_margin(self)
⋮----
metadata = {
rendered = render_spriteframes("res://atlas.png", metadata)
⋮----
def test_untrimmed_frame_does_not_emit_margin(self)
⋮----
rendered = render_spriteframes("res://atlas.png", self.metadata())
⋮----
def test_rejects_trim_metadata_that_does_not_fit_source(self)
⋮----
def test_rejects_frame_outside_known_atlas_bounds(self)
⋮----
def test_rejects_rotated_atlas_frame(self)
⋮----
def test_multiple_animations(self)
⋮----
def test_rejects_duplicate_animation_names(self)
⋮----
def test_rejects_out_of_range_animation_frame(self)
⋮----
def test_write_spriteframes_creates_file(self)
⋮----
output = Path(tmp) / "player.tres"
⋮----
rendered = output.read_text(encoding="utf-8")
⋮----
def test_rejects_empty_metadata(self)
⋮----
def test_rejects_invalid_fps(self)
```

## File: test_godot_handoff.py
```python
class GodotHandoffTests(unittest.TestCase)
⋮----
def test_recommendations_disable_animation_for_prop_without_clips(self)
⋮----
recommendations = build_import_recommendations(
⋮----
def test_profiles_are_loaded_from_versioned_json(self)
⋮----
prop = load_godot_profile("prop")
environment = load_godot_profile("environment")
character = load_godot_profile("character")
⋮----
def test_recommendations_report_profile_source(self)
⋮----
recommendations = build_import_recommendations("character")
⋮----
def test_profile_loader_uses_file_contents_as_source_of_truth(self)
⋮----
root = Path(tmp)
profile_dir = root / "profiles" / "godot4"
⋮----
loaded = load_godot_profile("prop", root=root)
⋮----
def test_prepare_handoff_copies_glb_and_writes_project(self)
⋮----
source = root / "model.glb"
⋮----
report = {"ready": True, "scene": {"animations": 0, "godotNameSuffixes": {}}}
⋮----
asset_manifest = {
result = prepare_godot_handoff(
⋮----
project_dir = Path(result["projectDir"])
copied = Path(result["asset"])
manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
⋮----
def test_missing_delivery_report_is_rejected(self)
⋮----
def test_failed_delivery_report_is_rejected(self)
⋮----
def test_allow_unvalidated_override(self)
⋮----
def test_non_glb_is_rejected(self)
⋮----
source = root / "model.gltf"
⋮----
def test_import_command_uses_headless_import(self)
⋮----
command = godot_import_command("godot", Path("project"))
⋮----
@patch("godot_handoff.detect_godot")
    def test_missing_godot_is_non_blocking(self, detect)
⋮----
project = Path(tmp)
⋮----
result = validate_godot_handoff(project)
⋮----
@patch("godot_handoff.subprocess.run")
@patch("godot_handoff.detect_godot")
    def test_available_godot_import_passes(self, detect, run)
```

## File: test_kaggle_3d_backend.py
```python
class Kaggle3DBackendTests(unittest.TestCase)
⋮----
def test_status_requires_cli_and_kaggle_credentials(self)
⋮----
ready = status(environ={
⋮----
def test_runner_is_pinned_and_requires_glb_output(self)
⋮----
source = _runner_source()
⋮----
def test_generate_orchestrates_private_gpu_kernel_and_downloads_glb(self)
⋮----
root = Path(td)
reference = root / "reference.png"
⋮----
output = root / "asset.glb"
commands = []
⋮----
def runner(command, **kwargs)
⋮----
download = Path(command[command.index("-p") + 1])
⋮----
result = generate(
⋮----
push = next(command for command in commands if command[1:3] == ["kernels", "push"])
⋮----
def test_generate_rejects_unapproved_model_override(self)
⋮----
source = Path(td) / "reference.png"
```

## File: test_kaggle_backend.py
```python
class KaggleBackendTests(unittest.TestCase)
⋮----
def test_status_requires_cli_token_and_username(self)
⋮----
def test_status_rejects_missing_cli(self)
⋮----
value = status(environ={
⋮----
def test_runner_quantizes_transformer_and_text_encoder(self)
⋮----
source = _runner_source()
```

## File: test_operational_status.py
```python
class OperationalStatusTests(unittest.TestCase)
⋮----
def test_ready_matrix_is_machine_readable(self)
⋮----
def which(name)
⋮----
mapping = {
⋮----
status = build_operational_status(
⋮----
def test_missing_optional_tools_are_reported_without_crashing(self)
⋮----
def test_imagen_codex_reports_required_token_names(self)
⋮----
def test_cloudflare_free_raster_is_reported_as_ready_without_cli(self)
⋮----
def test_free_vtracer_vector_route_is_reported(self)
⋮----
def test_free_kaggle_triposr_3d_route_is_reported(self)
⋮----
def test_manual_raster_backend_is_not_reported_as_auto_route(self)
⋮----
def test_qwen_colab_queue_counts_as_queued_generation_capability(self)
```

## File: test_production_contract.py
```python
class ProductionContractTests(unittest.TestCase)
⋮----
def request(self)
⋮----
manifest = asset_forge.load_json(Path(__file__).resolve().parents[1] / "examples/asset-manifest.json")
⋮----
def test_valid_request_builds_machine_readable_job(self)
⋮----
request = self.request()
⋮----
plan = asset_forge.build_plan(request["manifest"], Path(__file__).resolve().parents[1])
job = build_production_job(request, plan)
⋮----
def test_valid_production_report_contract(self)
⋮----
report = {
⋮----
def test_failed_report_cannot_claim_an_artifact(self)
⋮----
def test_invalid_request_is_rejected(self)
⋮----
errors = validate_production_request(request, asset_forge.validate_manifest)
```

## File: test_production_executor.py
```python
def job(target_format="png")
⋮----
class ProductionExecutorTests(unittest.TestCase)
⋮----
def test_generated_png_flows_through_processing_validation_and_report(self)
⋮----
root = Path(td)
⋮----
def generator(value, output_dir, **kwargs)
⋮----
source = Path(output_dir) / "generated-source.png"
⋮----
def optimizer(source, output)
⋮----
def validator(path, manifest)
⋮----
report = execute_generated_raster_job(
⋮----
def test_generated_png_fits_max_bytes_before_validation(self)
⋮----
constrained = job()
⋮----
calls = []
⋮----
def fitter(source, output, max_bytes)
⋮----
def test_raster_report_exposes_backend_routing(self)
⋮----
def test_webp_target_encodes_before_validation(self)
⋮----
def encode(source, output, **kwargs)
⋮----
def test_validation_errors_block_artifact_promotion(self)
⋮----
def test_generated_vector_is_sanitized_normalized_and_validated(self)
⋮----
vector_job = job("svg")
⋮----
source = Path(output_dir) / "generated-source.svg"
⋮----
def sanitizer(source, output)
⋮----
def normalizer(source, output)
⋮----
def profile_validator(path, profile)
⋮----
report = execute_generated_vector_job(
⋮----
def test_vector_validation_errors_block_promotion(self)
⋮----
def copy_step(source, output)
⋮----
def test_generated_3d_flows_through_profile_quality_and_godot_gates(self)
⋮----
three_d = job("glb")
⋮----
source = Path(output_dir) / "generated-source.glb"
⋮----
def quality(path, profile)
⋮----
def godot(path, profile)
⋮----
report = execute_generated_3d_job(
⋮----
def test_3d_backend_and_model_are_forwarded_to_generator(self)
⋮----
seen = {}
⋮----
def test_godot_3d_emits_runtime_plan_sidecar(self)
⋮----
runtime_plan = {
⋮----
sidecars = [Path(value) for value in report["additionalArtifacts"] if value.endswith(".runtime-3d.json")]
⋮----
def test_generated_character_3d_fails_when_profile_quality_fails(self)
⋮----
def test_provided_png_source_skips_generator_and_is_staged(self)
⋮----
provided_job = job()
⋮----
source = Path(source_td) / "licensed.png"
⋮----
def optimizer(input_path, output_path)
⋮----
def test_provided_source_symlink_is_rejected(self)
⋮----
real = Path(source_td) / "real.png"
⋮----
link = Path(source_td) / "linked.png"
⋮----
def test_generator_source_must_stay_inside_job_output(self)
⋮----
outside = Path(outside_td) / "outside.png"
⋮----
def test_asset_id_cannot_escape_job_output(self)
⋮----
bad = job()
⋮----
def test_non_raster_target_fails_closed(self)
⋮----
def test_generated_3d_reports_lod_artifacts_when_enabled(self)
⋮----
def lod_reporter(source, output_dir, profile)
⋮----
lod = output_dir / "hero-run.lod1.glb"
⋮----
def test_required_collision_blocks_godot_prop_without_collision_node(self)
⋮----
def test_required_lod_toolchain_unavailable_blocks_3d_promotion(self)
```

## File: test_production_os_ai_dev_server_live_e2e_workflow.py
```python
WORKFLOW = Path(
⋮----
def test_cross_repo_live_e2e_uses_current_collaborators()
⋮----
def test_cross_repo_live_e2e_requires_real_asset_backend()
⋮----
# Live generation can be metered: a change/push must NEVER run it.
⋮----
def test_cross_repo_live_e2e_generates_and_compiles_target()
⋮----
def test_cross_repo_live_e2e_persists_evidence()
⋮----
# Prove the completed boundaries accurately: the studio request is local,
# not evidence of a hosted Production-OS execution or target PR delivery.
⋮----
def test_cross_repo_live_e2e_scopes_credentials_and_records_exact_revisions()
⋮----
pre_generation = WORKFLOW.split("- name: Select live generation backend", 1)[0]
```

## File: test_raster_backend.py
```python
class RasterBackendTests(unittest.TestCase)
⋮----
def test_backend_status_shape(self)
⋮----
status = detect_pillow_webp()
⋮----
def test_missing_backend_returns_clear_error(self)
⋮----
path = Path(tmp) / "image.webp"
⋮----
def test_real_webp_lossless_decode_to_rgba(self)
⋮----
image = Image.new("RGBA", (2, 1))
⋮----
def test_pack_atlas_accepts_mixed_png_and_webp(self)
⋮----
root = Path(tmp)
png = root / "a.png"
webp = root / "b.webp"
atlas = root / "atlas.png"
⋮----
image = Image.new("RGBA", (1, 1), (0, 255, 0, 255))
⋮----
report = pack_uniform_atlas([png, webp], atlas, columns=2)
⋮----
def test_animated_webp_is_rejected_for_atlas_decode(self)
⋮----
path = Path(tmp) / "animated.webp"
first = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
second = Image.new("RGBA", (1, 1), (0, 255, 0, 255))
⋮----
def test_webp_encoder_validates_quality_and_method_without_backend(self)
⋮----
output = Path(tmp) / "x.webp"
⋮----
def test_encode_webp_lossless_roundtrip(self)
⋮----
source = root / "source.png"
output = root / "output.webp"
pixels = bytes([
⋮----
report = encode_webp(source, output, lossless=True, quality=100, method=6)
⋮----
info = inspect_webp(output)
```

## File: test_raster_pack.py
```python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
⋮----
def webp_chunk(kind: bytes, payload: bytes) -> bytes
⋮----
padding = b"\x00" if len(payload) & 1 else b""
⋮----
def webp_file(*chunks: bytes) -> bytes
⋮----
body = b"WEBP" + b"".join(chunks)
⋮----
def chunk(kind: bytes, payload: bytes) -> bytes
⋮----
ADAM7_PASSES = (
⋮----
def adam7_extent(size: int, start: int, step: int) -> int
⋮----
def pack_indexed_samples(samples: list[int], depth: int) -> bytes
⋮----
per_byte = 8 // depth
output = bytearray()
⋮----
byte = 0
group = samples[start : start + per_byte]
⋮----
shift = 8 - depth * (index + 1)
⋮----
raw = bytearray()
⋮----
pass_width = adam7_extent(width, x_start, x_step)
pass_height = adam7_extent(height, y_start, y_step)
⋮----
y = y_start + py * y_step
⋮----
x = x_start + px * x_step
⋮----
def write_rgba_png(path: Path, width: int, height: int, pixel: bytes) -> None
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
row = pixel * width
raw = b"".join(b"\x00" + row for _ in range(height))
⋮----
class RasterPackTests(unittest.TestCase)
⋮----
def test_pack_uniform_atlas_writes_png_and_metadata(self)
⋮----
root = Path(tmp)
red = root / "red.png"
green = root / "green.png"
atlas = root / "atlas.png"
⋮----
metadata = pack_uniform_atlas(
⋮----
def test_pack_rejects_mixed_frame_sizes(self)
⋮----
first = root / "a.png"
second = root / "b.png"
⋮----
def test_rgb_png_is_promoted_to_opaque_rgba(self)
⋮----
image = root / "rgb.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
raw = b"\x00" + bytes([7, 8, 9])
⋮----
def test_recompress_png_preserves_pixels(self)
⋮----
source = root / "source.png"
optimized = root / "optimized.png"
⋮----
before = decode_rgba(source)
report = recompress_png(source, optimized)
after = decode_rgba(optimized)
output_exists = optimized.exists()
⋮----
def test_recompress_png_reports_sizes(self)
⋮----
def test_fit_png_to_max_bytes_downscales_until_under_limit(self)
⋮----
fitted = root / "fitted.png"
⋮----
width = 128
height = 128
rng = random.Random(12345)
pixels = bytes(
⋮----
recompressed = root / "recompressed.png"
⋮----
max_bytes = max(256, int(recompressed.stat().st_size * 0.9))
⋮----
report = fit_png_to_max_bytes(
⋮----
def test_grayscale_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "gray.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
⋮----
def test_grayscale_alpha_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "gray-alpha.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 4, 0, 0, 0)
⋮----
def test_indexed_png_with_transparency_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "indexed.png"
ihdr = struct.pack(">IIBBBBB", 2, 1, 8, 3, 0, 0, 0)
palette = bytes([255, 0, 0, 0, 255, 0])
transparency = bytes([255, 64])
⋮----
def test_rejects_invalid_ihdr_length(self)
⋮----
image = Path(tmp) / "bad.png"
⋮----
def test_rejects_zero_dimensions(self)
⋮----
ihdr = struct.pack(">IIBBBBB", 0, 1, 8, 6, 0, 0, 0)
⋮----
def test_rejects_duplicate_ihdr(self)
⋮----
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
⋮----
def test_rejects_non_consecutive_idat(self)
⋮----
compressed = zlib.compress(b"\x00\x00\x00\x00\xff")
split = max(1, len(compressed) // 2)
⋮----
def test_rejects_trailing_data_after_iend(self)
⋮----
def test_rejects_indexed_trns_longer_than_palette(self)
⋮----
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
⋮----
def test_rejects_trns_for_rgba(self)
⋮----
def test_truecolor_trns_is_applied(self)
⋮----
image = Path(tmp) / "rgb-trns.png"
⋮----
transparency = struct.pack(">HHH", 7, 8, 9)
⋮----
def test_rejects_decompressed_data_larger_than_expected(self)
⋮----
image = Path(tmp) / "bomb.png"
⋮----
raw = b"\x00\x00\x00\x00\xff" + (b"x" * 1000)
⋮----
def test_hardened_inspector_reports_palette_and_transparency(self)
⋮----
info = inspect_png(image)
⋮----
def test_oversized_file_is_rejected_before_read(self)
⋮----
image = Path(tmp) / "small.png"
⋮----
def test_indexed_1bit_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "indexed1.png"
ihdr = struct.pack(">IIBBBBB", 8, 1, 1, 3, 0, 0, 0)
palette = bytes([0, 0, 0, 255, 255, 255])
# samples: 0,1,0,1,1,0,1,0 => 0b01011010
raw = b"\x00" + bytes([0b01011010])
⋮----
def test_indexed_2bit_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "indexed2.png"
ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 3, 0, 0, 0)
palette = bytes([
# samples 0,1,2,3 => 00 01 10 11
raw = b"\x00" + bytes([0b00011011])
⋮----
def test_indexed_4bit_png_ignores_padding_nibble(self)
⋮----
image = Path(tmp) / "indexed4.png"
ihdr = struct.pack(">IIBBBBB", 3, 1, 4, 3, 0, 0, 0)
palette = b"".join(bytes([i, 0, 0]) for i in range(16))
# samples 1,2,3; low nibble of second byte is row padding and must be ignored
raw = b"\x00" + bytes([0x12, 0x3F])
⋮----
def test_indexed_low_bit_depth_transparency_is_applied(self)
⋮----
image = Path(tmp) / "indexed-trns.png"
ihdr = struct.pack(">IIBBBBB", 2, 1, 1, 3, 0, 0, 0)
palette = bytes([10, 20, 30, 40, 50, 60])
transparency = bytes([255, 0])
raw = b"\x00" + bytes([0b01000000])
⋮----
def test_indexed_low_bit_depth_palette_limit_is_enforced(self)
⋮----
image = Path(tmp) / "bad-indexed.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 1, 3, 0, 0, 0)
⋮----
def test_grayscale_1bit_png_decodes_to_rgba(self)
⋮----
image = Path(tmp) / "gray1.png"
ihdr = struct.pack(">IIBBBBB", 8, 1, 1, 0, 0, 0, 0)
⋮----
def test_grayscale_2bit_png_scales_samples(self)
⋮----
image = Path(tmp) / "gray2.png"
ihdr = struct.pack(">IIBBBBB", 4, 1, 2, 0, 0, 0, 0)
⋮----
def test_grayscale_4bit_png_ignores_padding_nibble(self)
⋮----
image = Path(tmp) / "gray4.png"
ihdr = struct.pack(">IIBBBBB", 3, 1, 4, 0, 0, 0, 0)
raw = b"\x00" + bytes([0x05, 0xAF])
⋮----
def test_grayscale_low_bit_depth_trns_is_applied_before_scaling(self)
⋮----
image = Path(tmp) / "gray2-trns.png"
⋮----
transparency = struct.pack(">H", 2)
⋮----
def test_grayscale_trns_out_of_range_is_rejected(self)
⋮----
image = Path(tmp) / "gray2-bad-trns.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 2, 0, 0, 0, 0)
⋮----
def test_grayscale_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "gray16.png"
ihdr = struct.pack(">IIBBBBB", 3, 1, 16, 0, 0, 0, 0)
raw = b"\x00" + struct.pack(">HHH", 0, 32768, 65535)
⋮----
def test_truecolor_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "rgb16.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0)
raw = b"\x00" + struct.pack(">HHH", 65535, 32768, 0)
⋮----
def test_grayscale_alpha_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "gray-alpha16.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 4, 0, 0, 0)
raw = b"\x00" + struct.pack(">HH", 32768, 16384)
⋮----
def test_rgba_16bit_png_decodes_to_rgba8(self)
⋮----
image = Path(tmp) / "rgba16.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 6, 0, 0, 0)
raw = b"\x00" + struct.pack(">HHHH", 65535, 32768, 0, 16384)
⋮----
def test_grayscale_16bit_trns_compares_original_sample(self)
⋮----
image = Path(tmp) / "gray16-trns.png"
ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 0, 0, 0, 0)
sample = 40000
⋮----
expected_gray = (sample * 255 + 32767) // 65535
⋮----
def test_truecolor_16bit_trns_compares_original_samples(self)
⋮----
image = Path(tmp) / "rgb16-trns.png"
⋮----
samples = (1000, 2000, 3000)
⋮----
expected = [
⋮----
def test_truecolor_8bit_trns_out_of_range_is_rejected(self)
⋮----
image = Path(tmp) / "rgb8-bad-trns.png"
⋮----
def test_adam7_rgba8_reconstructs_full_image(self)
⋮----
image = Path(tmp) / "adam7-rgba.png"
width = height = 8
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 1)
⋮----
def pixel(x, y)
⋮----
raw = adam7_raw(width, height, pixel)
⋮----
def test_adam7_indexed_1bit_reconstructs_checkerboard(self)
⋮----
image = Path(tmp) / "adam7-indexed.png"
⋮----
ihdr = struct.pack(">IIBBBBB", width, height, 1, 3, 0, 0, 1)
⋮----
samples = [
⋮----
start = (y * width + x) * 4
expected = 255 if (x + y) % 2 else 0
⋮----
def test_adam7_rgba16_reconstructs_and_downconverts(self)
⋮----
image = Path(tmp) / "adam7-rgba16.png"
width = height = 5
ihdr = struct.pack(">IIBBBBB", width, height, 16, 6, 0, 0, 1)
⋮----
def pixel16(x, y)
⋮----
raw = adam7_raw(width, height, pixel16)
⋮----
expected16 = (x * 10000, y * 12000, (x + y) * 7000, 65535)
expected = bytes([
⋮----
def test_adam7_expected_size_is_bounded_and_exact(self)
⋮----
image = Path(tmp) / "adam7-truncated.png"
⋮----
raw = adam7_raw(width, height, lambda x, y: bytes([x, y, 0, 255]))
⋮----
def test_webp_vp8x_dimensions_alpha_and_animation(self)
⋮----
payload = bytes([0x12, 0, 0, 0]) + (319).to_bytes(3, "little") + (199).to_bytes(3, "little")
anmf = b"\x00" * 16
data = webp_file(
info = inspect_webp_bytes(data)
⋮----
def test_webp_vp8l_dimensions_and_alpha(self)
⋮----
bits = (width - 1) | ((height - 1) << 14) | (1 << 28)
payload = b"\x2f" + bits.to_bytes(4, "little")
data = webp_file(webp_chunk(b"VP8L", payload))
⋮----
def test_webp_vp8_lossy_dimensions(self)
⋮----
frame_tag = (0).to_bytes(3, "little")
payload = (
data = webp_file(webp_chunk(b"VP8 ", payload))
⋮----
def test_webp_alpha_chunk_marks_alpha(self)
⋮----
vp8 = (
vp8x = bytes([0, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
⋮----
def test_webp_incomplete_vp8x_is_rejected(self)
⋮----
payload = bytes([0, 0, 0, 0]) + (9).to_bytes(3, "little") + (9).to_bytes(3, "little")
data = webp_file(webp_chunk(b"VP8X", payload))
⋮----
def test_webp_reserved_vp8x_bits_are_rejected(self)
⋮----
payload = bytes([0x01, 0, 0, 0]) + (9).to_bytes(3, "little") + (9).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + (10).to_bytes(2, "little") + (10).to_bytes(2, "little")
data = webp_file(webp_chunk(b"VP8X", payload), webp_chunk(b"VP8 ", vp8))
⋮----
def test_webp_vp8x_dimension_mismatch_is_rejected(self)
⋮----
vp8x = bytes([0, 0, 0, 0]) + (19).to_bytes(3, "little") + (9).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + (21).to_bytes(2, "little") + (10).to_bytes(2, "little")
data = webp_file(webp_chunk(b"VP8X", vp8x), webp_chunk(b"VP8 ", vp8))
⋮----
def test_webp_lossy_alpha_flag_requires_alph_chunk(self)
⋮----
vp8x = bytes([0x10, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
vp8 = (0).to_bytes(3, "little") + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
⋮----
def test_webp_bad_riff_size_is_rejected(self)
⋮----
data = bytearray(webp_file(webp_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")))
⋮----
def test_webp_file_inspection_reads_from_path(self)
⋮----
path = Path(tmp) / "image.webp"
⋮----
bits = (width - 1) | ((height - 1) << 14)
⋮----
info = inspect_webp(path)
⋮----
def test_uniform_atlas_trim_records_source_offsets(self)
⋮----
pixels = bytearray(4 * 4 * 4)
⋮----
start = (y * 4 + x) * 4
⋮----
def test_uniform_atlas_extrudes_edge_pixels(self)
⋮----
source = root / "a.png"
⋮----
expected = bytes([7, 8, 9, 255])
⋮----
start = (y * 3 + x) * 4
⋮----
def test_compact_atlas_packs_variable_size_frames(self)
⋮----
a = root / "a.png"
b = root / "b.png"
c = root / "c.png"
⋮----
metadata = pack_compact_atlas(
⋮----
start = (frame["y"] * width + frame["x"]) * 4
⋮----
def test_compact_atlas_rejects_frame_wider_than_budget(self)
⋮----
source = root / "wide.png"
⋮----
def test_recompress_png_keeps_original_when_candidate_is_larger(self)
⋮----
output = root / "output.png"
⋮----
original = source.read_bytes()
⋮----
report = recompress_png(source, output)
⋮----
result = output.read_bytes()
⋮----
def test_uniform_atlas_width_budget_is_enforced(self)
⋮----
def test_uniform_atlas_pixel_budget_is_enforced(self)
⋮----
def test_compact_atlas_height_budget_is_enforced(self)
⋮----
def test_atlas_byte_budget_preserves_existing_output(self)
⋮----
output = root / "atlas.png"
⋮----
preserved = output.read_bytes()
⋮----
def test_compact_atlas_reports_occupancy_metrics(self)
⋮----
def test_compact_atlas_regions_do_not_overlap(self)
⋮----
paths = []
⋮----
path = root / f"{index}.png"
⋮----
frames = metadata["frames"]
⋮----
first_left = first["x"] - first["extrude"]
first_top = first["y"] - first["extrude"]
first_right = first["x"] + first["width"] + first["extrude"]
first_bottom = first["y"] + first["height"] + first["extrude"]
⋮----
second_left = second["x"] - second["extrude"]
second_top = second["y"] - second["extrude"]
second_right = second["x"] + second["width"] + second["extrude"]
second_bottom = second["y"] + second["height"] + second["extrude"]
separated = (
⋮----
def test_maxrects_compacts_better_than_simple_shelf_case(self)
⋮----
sizes = [(6, 2), (4, 4), (2, 4), (2, 2)]
⋮----
simple_shelf_area = 8 * 8
⋮----
def test_compact_atlas_reports_wasted_pixels(self)
⋮----
def test_compact_atlas_minimum_occupancy_can_fail_build(self)
⋮----
def test_compact_atlas_rejects_invalid_occupancy_threshold(self)
⋮----
def test_compact_atlas_auto_selects_best_evaluated_heuristic(self)
⋮----
sizes = [(7, 2), (5, 4), (4, 3), (3, 6), (2, 5), (2, 2)]
⋮----
evaluated = metadata["evaluatedHeuristics"]
⋮----
best = min(
⋮----
def test_compact_atlas_auto_skips_heuristic_outside_byte_budget(self)
⋮----
baseline = pack_compact_atlas(
evaluated = sorted(
⋮----
budget = evaluated[-1]["encodedBytes"] - 1
constrained = pack_compact_atlas(
selected = next(
⋮----
def test_compact_atlas_forced_heuristic_is_respected(self)
⋮----
def test_compact_atlas_rejects_unknown_heuristic(self)
⋮----
def test_compact_atlas_rotation_can_fit_frame_that_is_too_wide(self)
⋮----
pixels = bytes([
⋮----
frame = metadata["frames"][0]
⋮----
def test_compact_atlas_rotation_is_disabled_by_default(self)
⋮----
def test_compact_atlas_rotation_metadata_counts_rotated_frames(self)
```

## File: test_remote_batch.py
```python
def request(request_id, asset_id, expected_frames=1)
⋮----
class RemoteBatchTests(unittest.TestCase)
⋮----
def test_dependency_order_and_reference_are_preserved(self)
⋮----
root = Path(td)
spec = root / "spec.json"
⋮----
commands = []
⋮----
def fake_run(cmd, **kwargs)
⋮----
request_path = Path(cmd[cmd.index("fulfill") + 1])
payload = json.loads(request_path.read_text())
output = Path(cmd[cmd.index("--output-dir") + 1])
⋮----
artifact = output / (payload["manifest"]["id"] + ".png")
⋮----
class Result
⋮----
returncode = 0
stdout = ""
stderr = ""
⋮----
result = run(spec, root / "out")
⋮----
reference = Path(commands[1][commands[1].index("--reference") + 1])
⋮----
def test_cached_assets_count_as_quality_checked_from_technical_validation(self)
⋮----
artifact = output / "cached.png"
⋮----
quality = result["quality_summary"]
⋮----
def test_auto_batch_opens_circuit_breaker_after_repeated_cloudflare_failures(self)
⋮----
# This legacy breaker scenario tests research-use fallback. Commercial
# assets must never be routed to the Qwen backend by the breaker.
def research_request(request_id, asset_id)
⋮----
payload = request(request_id, asset_id)
⋮----
backends = []
⋮----
selected_backend = cmd[cmd.index("--backend") + 1]
⋮----
routing = {
⋮----
result = run(spec, root / "out", backend="auto")
⋮----
breaker = result["routing_summary"]["circuit_breaker"]
⋮----
def test_remote_batch_propagates_library_version_metadata(self)
⋮----
library = result["items"][0]["library"]
```

## File: test_runtime_atlas.py
```python
class RuntimeAtlasTests(unittest.TestCase)
⋮----
def test_exports_trim_and_rotation_semantics(self)
⋮----
metadata = {
⋮----
result = build_runtime_atlas(metadata)
frame = result["frames"][0]
⋮----
def test_defaults_non_rotated_source_region(self)
⋮----
frame = build_runtime_atlas(metadata)["frames"][0]
⋮----
def test_rejects_rotation_dimension_mismatch(self)
⋮----
def test_rejects_source_trim_out_of_bounds(self)
⋮----
def test_rejects_duplicate_indices(self)
⋮----
def test_validator_accepts_generated_runtime_atlas(self)
⋮----
source = {
runtime = build_runtime_atlas(source)
⋮----
def test_validator_detects_uv_drift(self)
⋮----
errors = validate_runtime_atlas(runtime)
⋮----
def test_validator_detects_frame_count_mismatch(self)
⋮----
def test_validator_rejects_unknown_fields(self)
⋮----
def test_validator_rejects_boolean_integer_fields(self)
⋮----
def test_validator_rejects_unknown_nested_fields(self)
⋮----
def test_build_runtime_atlas_normalizes_animations(self)
⋮----
runtime = build_runtime_atlas(
⋮----
def test_build_runtime_atlas_rejects_missing_animation_frame(self)
⋮----
def test_validator_rejects_animation_frame_reference_drift(self)
⋮----
def test_validator_rejects_duplicate_animation_names(self)
⋮----
def test_build_runtime_atlas_normalizes_animation_events(self)
⋮----
def test_build_runtime_atlas_rejects_event_at_animation_end(self)
⋮----
def test_validator_rejects_unsorted_animation_events(self)
```

## File: test_semantic_art_review.py
```python
class SemanticArtReviewTests(unittest.TestCase)
⋮----
def manifest(self, *, required=False)
⋮----
def test_unavailable_provider_is_non_blocking_when_optional(self)
⋮----
root = Path(td)
image = root / "asset.png"
⋮----
result = review_raster_art(
⋮----
def test_required_provider_fails_closed_when_unavailable(self)
⋮----
def test_structured_vision_review_is_scored(self)
⋮----
credentials = root / ".pollinations"
⋮----
calls = []
⋮----
def runner(command, **kwargs)
⋮----
class Result
⋮----
returncode = 0
stderr = ""
stdout = ""
result = Result()
⋮----
def test_low_semantic_score_fails_threshold(self)
```

## File: test_starlist_bridge.py
```python
FAKE_RECOMMENDER = r'''#!/usr/bin/env python3
⋮----
class StarListBridgeTests(unittest.TestCase)
⋮----
def make_fake_star_list(self, root: Path) -> None
⋮----
scripts = root / "scripts"
⋮----
def test_run_recommender_parses_json(self)
⋮----
root = Path(tmp)
⋮----
result = run_starlist_recommender(root, "pixel art sprites", top=3)
⋮----
def test_full_report_runs_visual_queries(self)
⋮----
report = build_visual_discovery_report(root)
⋮----
def test_missing_recommender_is_rejected(self)
```

## File: test_svg_tools.py
```python
class SvgToolsTests(unittest.TestCase)
⋮----
def test_valid_svg_passes(self)
⋮----
path = Path(tmp) / "icon.svg"
⋮----
def test_missing_viewbox_warns(self)
⋮----
def test_script_and_events_are_rejected(self)
⋮----
path = Path(tmp) / "bad.svg"
⋮----
def test_external_href_is_rejected(self)
⋮----
def test_sanitize_removes_dangerous_content(self)
⋮----
source = Path(tmp) / "source.svg"
output = Path(tmp) / "clean.svg"
⋮----
report = sanitize_svg(source, output)
⋮----
rendered = output.read_text(encoding="utf-8")
⋮----
def test_icon_profile_requires_square_viewbox(self)
⋮----
def test_ui_profile_accepts_non_square_viewbox(self)
⋮----
path = Path(tmp) / "ui.svg"
⋮----
def test_aspect_ratio_mismatch_warns(self)
⋮----
path = Path(tmp) / "mismatch.svg"
⋮----
def test_normalize_viewbox_from_dimensions(self)
⋮----
output = Path(tmp) / "normalized.svg"
⋮----
report = normalize_viewbox(source, output)
⋮----
def test_sanitize_removes_metadata(self)
⋮----
def test_data_uri_reference_is_rejected(self)
⋮----
def test_relative_reference_is_rejected(self)
⋮----
def test_internal_fragment_reference_is_allowed(self)
⋮----
path = Path(tmp) / "ok.svg"
⋮----
def test_css_external_url_is_rejected(self)
⋮----
def test_presentation_attribute_external_url_is_rejected(self)
⋮----
def test_css_import_is_rejected(self)
⋮----
def test_sanitize_removes_unsafe_css(self)
⋮----
def test_profile_depth_limit_is_blocking(self)
⋮----
path = Path(tmp) / "deep.svg"
inner = '<rect width="1" height="1"/>'
⋮----
inner = f"<g>{inner}</g>"
⋮----
def test_profile_element_limit_is_blocking(self)
⋮----
path = Path(tmp) / "complex.svg"
body = "".join('<rect width="1" height="1"/>' for _ in range(260))
⋮----
def test_profile_file_size_limit_is_blocking(self)
⋮----
path = Path(tmp) / "large.svg"
payload = "x" * 270000
⋮----
def test_existing_malformed_viewbox_is_not_overwritten(self)
```

## File: test_toolchain_3d.py
```python
class Toolchain3DTests(unittest.TestCase)
⋮----
def test_command_builders(self)
⋮----
command = gltfpack_command(
⋮----
@patch("toolchain_3d.shutil.which")
    def test_detect_tools(self, which)
⋮----
tools = detect_3d_tools()
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_pipeline_contains_export_validate_optimize_validate(self, detect)
⋮----
plan = build_3d_pipeline(
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_none_optimizer_keeps_raw_output(self, detect)
⋮----
def test_invalid_optimizer_is_rejected(self)
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_missing_optimizer_falls_back_to_raw_output(self, detect)
⋮----
validation_steps = [
⋮----
@patch("toolchain_3d.execute_command")
@patch("toolchain_3d.prepare_3d_pipeline")
    def test_execute_pipeline_skips_unavailable_optional_tools(self, prepare, execute)
⋮----
plan = {
⋮----
result = execute_3d_pipeline(plan, Path("."))
⋮----
@patch("toolchain_3d.execute_command")
@patch("toolchain_3d.prepare_3d_pipeline")
    def test_execute_pipeline_stops_on_required_failure(self, prepare, execute)
⋮----
@patch("toolchain_3d.detect_3d_tools")
    def test_godot4_target_adds_delivery_stage(self, detect)
⋮----
def test_invalid_target_engine_is_rejected(self)
```

## File: test_vector_backend.py
```python
class VectorBackendTests(unittest.TestCase)
⋮----
def test_status_reports_optional_dependency(self)
⋮----
result = status()
⋮----
def test_config_api_vectorizes_to_svg(self)
⋮----
root = Path(td)
source = root / "source.png"
output = root / "asset.svg"
⋮----
class Config
⋮----
@classmethod
                def poster(cls)
⋮----
def convert_file(self, input_path, output_path)
⋮----
fake = SimpleNamespace(Config=Config)
⋮----
result = vectorize_raster(source, output)
⋮----
def test_legacy_api_remains_supported(self)
⋮----
source = root / "source.webp"
⋮----
def legacy(input_path, output_path, **kwargs)
⋮----
fake = SimpleNamespace(convert_image_to_svg_py=legacy)
⋮----
def test_rust_panic_is_wrapped_as_vectorization_error(self)
⋮----
class PanicLike(BaseException)
⋮----
def legacy(*args, **kwargs)
⋮----
def test_missing_input_fails_closed(self)
```

## File: test_visual_similarity.py
```python
class VisualSimilarityTests(unittest.TestCase)
⋮----
def test_identical_images_score_higher_than_different_images(self)
⋮----
root = Path(td)
parent = root / "parent.png"
same = root / "same.png"
different = root / "different.png"
⋮----
same_score = compare_visuals(parent, same)["score"]
different_score = compare_visuals(parent, different)["score"]
⋮----
def test_subject_repositioning_stays_similar(self)
⋮----
moved = root / "moved.png"
⋮----
a = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(a)
⋮----
b = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(b)
⋮----
score = compare_visuals(parent, moved)["score"]
⋮----
def test_shape_and_palette_change_is_penalized(self)
⋮----
changed = root / "changed.png"
⋮----
score = compare_visuals(parent, changed)["score"]
⋮----
def test_sprite_sheet_scoring_is_frame_aware(self)
⋮----
parent = root / "parent-sheet.png"
child = root / "child-sheet.png"
⋮----
p = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(p)
⋮----
x = i * 32
⋮----
q = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(q)
⋮----
offset = (i % 2) * 3
⋮----
result = compare_visuals(parent, child)
```
