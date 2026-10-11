# Raster production quality gate (fail closed)

## Portable batch destination uniqueness

Dependency-aware batches now reject duplicate item IDs or request IDs after
case-folding. They also compare delivery `target_path` values after
Unicode NFC normalization and case-folding. This is essential when the
production runner uses a case-sensitive Linux filesystem but a downstream
consumer may use Windows or a normalization/case-insensitive macOS volume.

These collisions are checked for the **entire batch before any output
directory is created or a generator is invoked**. The caller must choose
distinct portable IDs and target paths; the pipeline does not silently
rename assets or alter downstream request references.

The existing offline functional batch smoke checks four additional
scenarios: case-only item-ID collision, case-only physical request-ID
collision, case-only target-path collision, and canonical Unicode-equivalent
target paths. Each invalid later item must fail before generation or output.
[Code commit 4ea071e](https://github.com/dbrckk/asset-forge/commit/4ea071e012f9813f174a46ed4cb2ebc054e91274)
passed [CI 38128075034](https://github.com/dbrckk/asset-forge/actions/runs/38128075034)
at its exact HEAD (COMPLETED SUCCESS 4/4; batch smoke SUCCESS).
No remote image generation, paid probe, licensed model qualification or
actual Production-OS E2E delivery is implied by this check.

## Remote batch delivery integrity (offline-verified)

The dependency-aware remote batch validates all request IDs, target paths
and hosted source paths before starting a generator. Once artifacts exist,
it additionally rejects a zero-byte main deliverable and refuses to copy
an additional artifact or later main artifact onto a bundle filename used
by an earlier item. The collision check is case-insensitive for consumers
on Windows and other case-insensitive filesystems.

The existing GitHub Actions functional smoke deliberately supplies an empty
primary file, then a collision between the first item's additional file and
the next item's primary file. Both are rejected. For the collision, the smoke
also verifies that the previously bundled bytes remain unchanged and that
`batch-result.json` is not published as a successful result.

Evidence: [commit 30c9c84](https://github.com/dbrckk/asset-forge/commit/30c9c84da6131751b9e35394c149da2a3d1efd29)
and [CI 38123692654](https://github.com/dbrckk/asset-forge/actions/runs/38123692654)
(COMPLETED SUCCESS, 3/3 jobs; batch functional smoke SUCCESS).
This is a local orchestration integrity check only. A failure may leave
partial working files behind; it does not prove transactional rollback,
commercially licensed model output, independent semantic fidelity or
successful import/build in a consuming game. Do not publish or merge the
draft PR on this evidence alone.

This runbook covers **generated** sprites and other raster assets. A valid PNG
and a successful SHA-256 check demonstrate integrity, not that the image depicts
the requested subject.

## Strict opt-in request

Use [`examples/production-request-strict-raster.json`](../examples/production-request-strict-raster.json)
for a real production-gated raster smoke:

```bash
asset-forge fulfill examples/production-request-strict-raster.json --backend auto
asset-forge validate-production-report build/strict-raster-qa-smoke/production-report.json
```

The CLI uses the existing generation backend setup. Required semantic review
needs an authenticated `polli` CLI. Provision its credential only through
the runtime's secret manager; never put credentials in requests, commits or
logs. If review cannot run, the strict request must **fail**, not silently pass.

The example requires `technicalQualityMin=0.65`,
`semanticArtReviewRequired=true`, `semanticQualityMin=0.72`,
and `requiresAlpha=true`. This is an actual isolated sprite contract,
not an illustration on a neutral opaque background. A fully opaque image
cannot score higher than roughly 0.5 under the existing alpha-based
border/occupancy technical metric. Do not lower the threshold to make
such a result pass. If the generator emits an opaque image, the existing
`rembg` CLI fallback must be installed to isolate the subject or the
strict request must fail closed. The fallback cannot compensate for an
incorrect subject or multiple objects: the semantic fidelity gate remains
mandatory.
The technical score is a heuristic, not a human aesthetic judgment. The visual
review receives the original production instruction and must also return
`instructionFidelity` between 0 and 1. A generic, unrelated, malformed, or
prompt-inaccurate rendering fails the strict gate. Unavailable or invalid
structured semantic results are blockers for a required review.

For existing consumers, these constraints remain opt-in to preserve previously
declared request behavior. Do not treat legacy batch success as equivalent to
premium visual quality. Never promote an output without checking the actual
image, destination import, and applicable licensing.

## 2026-10-11 transparent visual-review preview (draft PR #13)

[Commit `c71373d`](https://github.com/dbrckk/asset-forge/commit/c71373df7a596f82711a17e6dc24eee1414e5a70) changes only the **vision-review upload** for requests that declare
`semanticArtReviewRequired=true` and `requiresAlpha=true`. If the
validated output has actual transparency, the reviewer receives a temporary
RGB rendering of the existing RGBA pixels composited on uniform neutral gray
(128/128/128), which is explicitly identified to the reviewer as synthetic.
The original PNG is **not** overwritten, regenerated, recolored, or copied
into the consumer. Original-alpha technical and border constraints are still
validated on the untouched deliverable; overall and instruction-fidelity
semantic thresholds are unchanged. The preview is deleted after upload,
and `reviewPreviewComposited` records the decision in the reviewer evidence.

This requires the existing optional Pillow generation dependency. A required
alpha review without Pillow fails closed. The previous Qwen one-shot failure
(38087387660) remains a **failure**; compositing is a transport hypothesis,
not retrospective evidence of semantic acceptance. The original one-shot
must not be rerun. No new Qwen/Kaggle generation is authorized by this
change. The Qwen Research License commercial-use prohibition remains in
force: this preview correction grants no rights over the model or its outputs.
The draft needs exact-head CI and, separately, a licensed real production
asset and verified consumer import before release.

## Commercial licensing covers indirect Qwen model calls

[Commit `4f7373b`](https://github.com/dbrckk/asset-forge/commit/4f7373b8be308a84bfb54266cc77dd220bd56231)
closes two indirect paths previously missed by the direct Qwen backend guard:

- A **Cloudflare raster request with references** may be redirected to
  Kaggle Qwen before inference. For a `manifest.license.commercialUse=true`
  request, this path now fails early instead of using unlicensed Qwen.
- A **VTracer SVG request** produces an intermediate raster using Cloudflare
  or Qwen. For commercial requests, Qwen is excluded from initial selection
  *and* fallback. Cloudflare is used only when ready; otherwise the request
  fails closed before any Qwen inference.

A caller-provided `--model` name or alternative model identifier does **not**
constitute a verified commercial license. Commit
[`9ebc80b`](https://github.com/dbrckk/asset-forge/commit/9ebc80b59728e3712327822013126a2da0fc0e59)
closes the explicit Kaggle/Colab commercial Qwen model-name override loophole:
Qwen backends refuse `commercialUse=true` independent of the string passed
to `--model`, since the Colab worker may still load its default model.
An alternative model can be made commercially available only through a
separately reviewed and verified rights/provenance pathway, not by renaming.

This does **not** grant commercial rights for Qwen or generated outputs.
Asset provenance, actual model rights, the output license and consuming-game
permissions must be separately verified before commercial release. These
conditions also apply to intermediate image generation for SVG delivery.
No existing failed probe is authorized to rerun by this change.

## Provider subprocess timeouts are explicit failures

Commit [`f76c682`](https://github.com/dbrckk/asset-forge/commit/f76c68289ba99abd48fb5829e9ac8b347ec71c0b)
converts `subprocess.TimeoutExpired` and local executable startup errors
(`OSError`) from either `polli upload` or `polli gen text` into a structured
`SemanticArtReviewError` for **required** semantic checks. The production
executor records this as a validation error: `success=false` and `artifact=null`;
a stalled service must not silently produce a qualified deliverable.

When semantic review is **optional**, the same faults produce
`available=false`, `passed=null`, and a provider-unavailable reason
(`upload_unavailable` or `review_unavailable`). The temporary alpha
preview, when present, still gets cleaned up on upload timeout or failure.
Neither code path weakens the technical, semantic, or fidelity thresholds.

The CI workflow includes a local executable subprocess smoke for the upload
and review timeout paths, in required and optional modes. This uses a local
placeholder credential and never invokes a hosted model or transmits an image.
A passing offline smoke establishes timeout-handling behavior only, not
the availability or fidelity of the real vision provider.

## 2026-10-11 offline transparent-preview integration smoke

The [`e40c86f`](https://github.com/dbrckk/asset-forge/commit/e40c86ff8eeeffb1b4bdb52a2aeffc960257c88c)
change adds a **functional smoke step**, not a new unit-test suite, to
`.github/workflows/validate.yml` under the pre-existing Pillow-enabled
`webp-backend` job. It constructs a real RGBA PNG with colored but invisible
pixels at the border and one opaque foreground pixel. The real
`review_raster_art` function composites and passes an RGB preview to a local
in-process reviewer substitute; no image is generated or transmitted externally.

Observed CI: [run **38121816485**](https://github.com/dbrckk/asset-forge/actions/runs/38121816485)
completed **SUCCESS** on exact commit `e40c86f`: **3/3 jobs passed**,
including `Smoke-check transparent semantic preview and fidelity threshold
offline`. The step checks the neutral RGB background, preservation of
foreground pixels, unchanged SHA-256 of the original PNG, removal of the
temporary preview, and rejection of simulated fidelity 0.35 versus acceptance
of simulated fidelity 0.94 under the unchanged 0.72 threshold.

**Scope:** proves actual alpha composition, file integrity, temp-file
cleanup and numerical gate wiring. The visual scores are fixtures and are
**not** independent aesthetic judgments. It does not prove remote vision
availability, Qwen commercial permission, or successful consumer import.
Do not use this offline smoke to release a historical failed sprite.

## 2026-10-11 Production-OS workflow input integrity

Two GitHub Actions entry points previously placed a caller-supplied model name
directly inside quoted **Bash source**: `.github/workflows/production-os-batch.yml`
and `.github/workflows/production-os-dispatch.yml`. A shell-quoting escape
in untrusted JSON/dispatch input could change the executed command. The batch
materializer also echoed model names to `GITHUB_OUTPUT` without filtering
newlines, risking additional step-output entries.

Fixes [`62bdb64`](https://github.com/dbrckk/asset-forge/commit/62bdb64a511bf5f0b6c42a95c15f21c0efe4f348)
(batch) and [`941679f`](https://github.com/dbrckk/asset-forge/commit/941679f425d4d53e59c78cef06fa16ba6cade75c)
(single request):

- Validate model identifiers as a bounded, single-line allowlisted string
  (letters, digits, slash, period, underscore, colon, plus, at-sign, hyphen).
  Batch input also requires an actual JSON string, not an object.
- Enforce the existing fixed backend allowlist.
- Hand validated `backend` and `model` to Bash through step environment
  variables with quoted shell array arguments, **never** by interpolating
  GitHub expressions directly into a `run:` program.
- Continue rejecting malformed requests **before** asset generation.

The existing CI workflow now executes the actual embedded Python request
materializers offline with safe model IDs, multiline strings, shell syntax,
oversized names and non-string batch input. It checks that invalid inputs
cannot produce a materialized request or tamper with `GITHUB_OUTPUT`, and
that dispatch Bash uses environment variables.

**Observed evidence:** [Actions run 38122046657](https://github.com/dbrckk/asset-forge/actions/runs/38122046657)
completed **SUCCESS, 3/3 jobs**, with the
`Smoke-check batch model request injection offline` step **SUCCESS** at
commit `db922d02a9fbeeef33d931d5920615a9b3f9c0a0`.
The smoke launches only local Python subprocesses: no production dispatch,
model generation, network inference or secret-value access.

This hardening is currently **only on draft PR #13**, not on `main`.
Existing production workflows are not considered remediated in deployment
until a separately qualified and authorized release includes the commits.
A green workflow-validation CI run is not proof of a real visual delivery.

## 2026-10-11 deterministic dispatch and safe batch routing

The single-asset GitHub Actions dispatch previously accepted a request's
`delivery.outputDir` but searched for reports only under `build/asset-forge`
using `find`. This caused report discovery mismatches and allowed
caller-controlled output directories in an ephemeral worker. Commit
[`23e0bc9`](https://github.com/dbrckk/asset-forge/commit/23e0bc9c741957beb8ad02cb2874f75fb6ce6cca)
now confines the dispatch output to
`build/asset-forge/production`, preserving any requested engine, and validates
exactly `build/asset-forge/production/production-report.json` rather than
selecting the first report found. Caller output paths are intentionally
overridden **only in this hosted dispatch workflow**; local CLI callers
retain their original `--output-dir` contract. Its real Python request
materializer was exercised offline against absolute, traversal and custom
paths and malformed `delivery` values in
[`0db027a`](https://github.com/dbrckk/asset-forge/commit/0db027a6bf3932e31ddc656e6c70b86f4fdae5a3).
[CI run 38122388766](https://github.com/dbrckk/asset-forge/actions/runs/38122388766)
completed SUCCESS 3/3.

`remote_batch.py` originally allowed dot-only identifiers and stripped the
leading slash from target paths. Commits
[`6cce793`](https://github.com/dbrckk/asset-forge/commit/6cce7933611ebc4be76d00de8371e4ab4cae3742)
and
[`4d51613`](https://github.com/dbrckk/asset-forge/commit/4d51613368dd445ecf38faea69922697ca9e5a59)
require safe production-style IDs and reject absolute, drive-qualified,
UNC, traversal and control-character target paths **before generation**.
The offline batch smoke verifies these rejections and one valid, locally
simulated bundle with artifact checksum. [CI run 38122502078](https://github.com/dbrckk/asset-forge/actions/runs/38122502078)
completed SUCCESS 3/3.

Separately, the Cloudflare-to-Qwen batch circuit breaker previously could
force the research-licensed Qwen backend for a subsequent commercial item.
The generator would refuse this route, failing the entire batch even when
the normal commercially filtered `auto` route remained available. Commit
[`41aa20f`](https://github.com/dbrckk/asset-forge/commit/41aa20f033209d0426d2032cc2ba85cb585ab616)
now exempts `commercialUse=true` items from the breaker override while
retaining the normal fail-closed Qwen model-rights check. The bundle
records `commercial_exemptions` for visibility. The existing research-use
breaker scenario was aligned with its intended noncommercial license
(maintaining the user instruction not to create new unit tests).
An offline mixed-license smoke exercises two research assets, one commercial
asset and a further research asset, ensuring backend selections
`auto, auto, auto, kaggle-qwen` without a real model call.

**Exact final source/CI evidence:**
[Actions 38122589855](https://github.com/dbrckk/asset-forge/actions/runs/38122589855),
commit `43ee5798b2a139b1f735aff45ee3f3fcf314450f`,
completed **SUCCESS 3/3 jobs**, including the offline batch-path
and mixed-license-routing smoke. These proofs establish local routing and
path handling only; no live provider call, legal commercial model grant,
consumer import or Production-OS end-to-end delivery was performed.
Draft PR #13 remains unmerged.

## 2026-10-11 preflight and real local-source to Godot export

The batch orchestrator once validated each item's request ID and consumer target
path **during** the generation loop. A malformed late item could waste
inference on earlier items, and two distinct batch IDs could reuse the same
request ID and overwrite the same `jobs/<requestId>` directory. Commit
[`3489c21`](https://github.com/dbrckk/asset-forge/commit/3489c21d252d7fef29ac23d11f6785b025e9ebfc)
now validates the complete dependency-ordered batch **before** creating
output directories or starting any subprocess, including unique, filename-safe
request IDs and nonduplicated normalized consumer target paths. Existing
allowed paths and execution order are preserved. The functional CI smoke
[`99acc61`](https://github.com/dbrckk/asset-forge/commit/99acc61ec7b7b278e378294a0e45e81bd8f74dc3)
exercises an invalid second or third asset and duplicate IDs/paths,
checks **zero generated jobs** and no destination directory, then executes
the previous valid and mixed-license fixtures.
[Run **38123072481**](https://github.com/dbrckk/asset-forge/actions/runs/38123072481)
completed SUCCESS **3/3** with the batch smoke SUCCESS.

The previous checks for semantic and licensing integrity were mostly
**offline reviewer/generator substitutes**, not a real production-CLI
asset transformation. A second integration smoke now authors an original
64 x 32 RGBA sprite sheet locally, declares source mode `custom` with
`project-owned` metadata, and invokes the **real** Asset Forge CLI:
`fulfill --source ... --output-dir ...`. The actual CLI validates the
manifest, stages and optimizes the PNG, writes its production report,
builds the 2-frame atlas, exports a Godot 4 `SpriteFrames` resource
(`player.tres`), and validates its report. The smoke checks the original
transparent pixels, frame count and generated files and computes SHA-256
from the actual exported PNG.

First version `1f19284` had an **incorrect smoke assertion** for
`provenance.sourceMode` (the actual report uses `provenance.source.mode`)
and CI 38123146327 failed at that fixture assertion **after real
`fulfill` succeeded**. This was corrected in
[`9241946`](https://github.com/dbrckk/asset-forge/commit/9241946a889d5fe556c0077c267519ef633aa7e7).
[Run **38123173929**](https://github.com/dbrckk/asset-forge/actions/runs/38123173929)
completed SUCCESS **3/3**; the real local-source CLI integration step
itself also passed. The optimized PNG SHA-256 observed in the job log was
`5e1b1f5a04287365f2dbf082e8156c5433c2dc59db06dc1cd06040dc543a0859`.

**Exact scope of proof:** actual processing of an original locally-authored
PNG and Godot-format export file creation, not a deployed or loaded Godot
runtime, not a customer-game import, and not commercial approval for the
Qwen model. The rendered sprite is a functional engineering fixture, not
an independently evaluated AAA game asset. These tests do not close the
real-provider semantic/rights or Production-OS full delivery gates. Draft
PR #13 remains nonmerged.

## 2026-10-11 hosted source-path trust boundary

The dependency-aware `remote_batch.py` accepted an arbitrary
`source_path` string and passed it to `asset-forge fulfill --source`.
The Asset Forge executor already rejects direct symlinks and enforces
file type and size, but the batch could discover an untrusted or missing
source only after spending generation time on earlier items.

Commits
[`9850fd4`](https://github.com/dbrckk/asset-forge/commit/9850fd4d6a056b920c6a7b59e52948219710a7a3)
and
[`6436f96`](https://github.com/dbrckk/asset-forge/commit/6436f9637bbe221af36622537e02c911e4ede766)
extend the whole-batch preflight: all explicit source paths must be
strings pointing to existing nonsymlinked files, and
`custom`/`external` items must actually supply a source. An optional,
explicit `ASSET_FORGE_BATCH_SOURCE_ROOT` environment variable also confines
those files to its resolved directory, including checking for parent
directory symlinks. The hosted batch workflow now sets it to the
GitHub-managed checkout directory (`github.workspace`) via
[`4450ae3`](https://github.com/dbrckk/asset-forge/commit/4450ae3e3304540743d0e933d05d9018a2683b13).
Local CLI usage retains its normal ability to read a separately approved
file outside the repository if no root limit was set.

The offline smoke
[`3d308fc`](https://github.com/dbrckk/asset-forge/commit/3d308fcb700ae9cc47db635e5bdafac2d7b3bfd2)
checks outside-checkout files, symlinks, missing files, absent source for
custom mode and nonscalar values in a *later* batch item. Rejected cases
must make **zero generator calls** and create no output directory. A real
local trusted source path, passed to a local simulated generator,
still succeeds and is supplied as an absolute resolved path.

This validates source trust-boundary enforcement, **not** a remotely
generated asset or any claimed model/output commercial license.
It must not be cited as an Asset Forge → Production-OS → consumer release.

## 2026-10-11 real Godot 4 engine import verification

The previous integration smoke proved a real Asset Forge CLI transformation
of a locally authored PNG into a `SpriteFrames` `.tres`, but **only checked
the resulting text/resource files**. That did not establish that the
engine could actually parse, import and instantiate the exported resource.

Draft PR #13 now includes the self-contained functional integration runner
[`integration/godot4_import_smoke.py`](../integration/godot4_import_smoke.py),
introduced in commit
[`1b81ac1`](https://github.com/dbrckk/asset-forge/commit/1b81ac13d8bd7c24a442c511c0e489a22855a676).
It creates an original two-frame (64×32 RGBA) sprite sheet and runs the
**actual Asset Forge CLI** `fulfill --source` to generate a production PNG,
two-frame atlas and `player.tres`. It checks the report, dimensions,
source provenance, alpha and frame count, and assembles a temporary Godot
project with the generated resources.

A new separate, non-GPU `godot4-import` CI job from
[`49cce7a`](https://github.com/dbrckk/asset-forge/commit/49cce7a4ee72dd9bdc882a3c09bd1c93bc9efb61)
downloads the **official Godot 4.4.1 Linux x86-64 editor** and verifies the
binary's SHA-512 digest against the official release `SHA512-SUMS.txt`
before extraction; the fixed-version archive is cacheable but verified
again on use. No token or external image model is needed.

The script invokes `godot --headless --path <project> --import` to
perform the **real editor texture import**, then executes a GDScript
validation via `--headless --script`. Godot must load the
`SpriteFrames` resource, find the `default` animation with exactly
two frames, expose two real `AtlasTexture` regions with the correct
32×32 rectangle coordinates, resolve the PNG as a 64×32 texture and allow
an `AnimatedSprite2D` to assign the resource and select frame 1.
Failures return a nonzero exit code and fail the CI job.

**Observed evidence:** [workflow run **38124010327**](https://github.com/dbrckk/asset-forge/actions/runs/38124010327)
at exact commit `49cce7a4ee72dd9bdc882a3c09bd1c93bc9efb61` completed
**SUCCESS 4/4 jobs**, including **Real Godot 4 SpriteFrames import**.
Its logs contain:
`PASS: actual Godot 4 editor import and runtime SpriteFrames load` and
`PASS: AtlasTexture regions, texture dimensions and AnimatedSprite2D assignment`.
The real exported PNG SHA-256 was
`5e1b1f5a04287365f2dbf082e8156c5433c2dc59db06dc1cd06040dc543a0859`.

This constitutes a genuine **Asset Forge → Godot 4 engine runtime import**
of a locally authored technical fixture, **not** a Roblox consumer build,
a paid model output, a commercial grant for Qwen, an independently reviewed
premium AAA asset or the complete Production-OS worker-delivery chain.
Draft PR #13 is still nonmerged.

## 2026-10-11 historical Qwen cache reuse guard

The generated-asset `fulfill` command can select a cached success entry
and supply its stored PNG as `source_path` to the processing executor.
That skips `execute_generated_asset` and therefore skips that
generator's *current* commercial model-license gate. The cache file
recorded a final backend and model, but an old successful record could
have been produced under earlier, incorrect commercial metadata.
A historical Qwen raster should not be promoted commercially merely
because its checksum remains intact.

Commit
[`9bde049`](https://github.com/dbrckk/asset-forge/commit/9bde049449b0151ed79c5f204f8629340257b1b0)
closes this alternate route for commercial generated requests:

- An explicitly requested `kaggle-qwen` or `qwen-colab` backend fails
  **before** selecting a cached artifact.
- Exact-key and cross-project library hits whose recorded backend is
  `kaggle-qwen`/`qwen-colab`, whose recorded model contains
  `qwen-image-2.1`, or which have no recorded backend are **cache misses**
  for commercial requests. The regular generator selector must then
  decide whether a permitted backend can satisfy the request; it
  must not treat stored bytes as new commercial authorization.
- Non-Qwen entries continue through the previous lookup path. That is
  a cache behavior guarantee, **not** verification of their provider
  contracts, asset provenance or commercial-use rights.

The no-GPU/no-network functional CI smoke uses a *real local asset-library
index* with a historical Qwen record, the actual `asset_forge.main`
CLI parser and cache-selection path, and a stub at the **generation
executor boundary**. It verifies a Qwen exact cache miss, an explicit
commercial Qwen refusal before generation, a cross-project commercial
cache miss and a non-Qwen entry that remains selectable. No real model
is invoked, no commercial rights are granted and no secret is read.

The first smoke `b788b07` failed at its harness call because the
CLI's `main()` reads `sys.argv` rather than accepting an `argv`
parameter. The harness was corrected in
[`b19ec63`](https://github.com/dbrckk/asset-forge/commit/b19ec63c3dc74115796d4c628c2891f4881b57ce)
without weakening the guard. [Actions **38124287234**](https://github.com/dbrckk/asset-forge/actions/runs/38124287234)
at that exact commit finished **SUCCESS 4/4 jobs**, including the
commercial-cache smoke and the real Godot 4 import job.

Release remains gated on genuine licensed visual production, independent
semantic fidelity evidence, and the complete Production-OS consumer
handoff. PR #13 stays draft and unmerged.

## Evidence to collect

Record: original instruction and manifest constraints; execution run ID;
selected generation backend; technical score and warnings; semantic overall
and instruction-fidelity scores; output file checksum; importing project's
successful integration/build. A draft PR alone is not a final release.

The historical Asset Forge batch run `37298791209` produced an integral PNG
but had `technical_art.score=0.476302` and `semantic_art=null`. It would not
satisfy the example's strict gate. This is historical evidence, not proof that
a new generation has passed.

## 2026-10-10 real-generation evidence

Two bounded one-shot runs were executed; neither qualifies the strict raster example:

- [Run 38078694657](https://github.com/dbrckk/asset-forge/actions/runs/38078694657): generation stopped at technical quality **0.500 < 0.650** after three attempts; initial example conflicted with alpha-based scoring.
- [Run 38079351985](https://github.com/dbrckk/asset-forge/actions/runs/38079351985): after requiring true alpha and installing the optional `rembg` fallback, the generated 96x96 PNG reached **technical score 1.000**, but the independent semantic reviewer rejected it: **overall 0.22 < 0.72**, **instruction fidelity 0.05 < 0.72**. The visual contains several stacked metallic/cyan elements rather than the requested single cylindrical cell. `production-report.json` records `success=false`, and `artifact=null` despite the PNG being preserved as diagnostic evidence. The archive is `strict-raster-alpha-real-20261010` (artifact ID `11680061505`).

**Engineering conclusion:** alpha removal solves only technical transparency. A score of 1.0 is not a release-grade visual score. The generator's one-frame request should avoid all sprite-sheet/grid/multiple-frame phrasing; generation and semantic fidelity must be improved and independently requalified before a consumer imports the image. Never treat the diagnostic PNG as a released asset, and do not rerun either completed one-shot workflow merely to repeat the same failure.


## 2026-10-10 single-frame prompt correction

[Commit `05c73e43a2ae99dbc5579bad2997a8b87950682f`](https://github.com/dbrckk/asset-forge/commit/05c73e43a2ae99dbc5579bad2997a8b87950682f)
corrects `generator_backends.build_generation_prompt` for an explicit one-frame
sprite or pixel-art request. It no longer demands an animation frame sequence,
a sprite sheet with one frame, or a 1x1 grid. Instead, it asks for a single
standalone image, faithful object count, and no duplicated objects or collages.
For `expectedFrames > 1`, existing sprite-sheet grid/sequence instructions
remain intact. The opt-in semantic and technical thresholds have **not** been
lowered.

[GitHub Actions run 38084846330](https://github.com/dbrckk/asset-forge/actions/runs/38084846330)
completed successfully on that exact source commit: `test`,
`vector-backend`, and `webp-backend` all passed. Existing tests were
executed; no new unit tests were created.

**Not yet qualified:** there is no new real raster generation/visual review
with this corrected prompt and no successful consumer import. Runs
`38078694657` and `38079351985` are historical terminal failures and must
not be re-run. A distinct bounded real-generation probe, inspected image,
technical + semantic scores, reproducible artifact checksum, and successful
consumer integration are required before promoting this work or merging PR #13.

## 2026-10-10 third one-shot failure

[Run 38084991532](https://github.com/dbrckk/asset-forge/actions/runs/38084991532),
job `114309536794`, is **completed/failure**, attempt 1. It executed
the corrected mono-frame prompt from `05c73e4`; its prompt preflight
passed. It must **never be rerun**. Diagnostic archive
`strict-raster-monoframe-real-20261010` (artifact ID `11682276035`).

Original `generated-raw.png`: 512×512, SHA-256
`ba12dc24eedc10bd05d7fdc0f2a8cc6b430288cb4d741d4f34ac71da5b66d516`.
Normalized 96×96 `live-raster-cell.png`: RGBA with alpha, SHA-256
`9b3a4ce6fbc177395a9209783de8c6dc6e2199100b9f652553e9afae084de683`.
The **actual pixels**, inspected from the archive, show a UI-like collection of
many glowing cells, rows, buttons and panels, not one isolated cylindrical cell.
Backend: Cloudflare `@cf/stabilityai/stable-diffusion-xl-base-1.0`.

Report: `success=false`, `artifact=null`. Technical `score=0.659407`
passed the previous aggregate minimum `0.65`, but **borderAlphaRatio=0.292105**
violated the explicit `maxBorderAlphaRatio=0.08` and was only a warning.
The required independent semantic review failed: `overall=0.18`,
`instructionFidelity=0.03` (each needs `>=0.72`). Thus no deliverable or
consumer import can be claimed, even though the output is a syntactically valid
transparent PNG.

Follow-up improvements (on PR #13, still draft and unmerged):

- `bbec118`: enforce a **hard failure** when explicit `maxBorderAlphaRatio`
  is violated together with an explicit technical minimum. Without that strict
  opt-in combination, retain the historical warning behavior.
- `f1937c4`: support Cloudflare SDXL's documented `negative_prompt` argument
  without changing its default request behavior.
- `0fa4cf6`: single-sprite positive instructions now focus on one coherent,
  centered subject instead of repeating undesirable collage/grid concepts in
  the positive text; pass exclusion motifs through `negative_prompt` only
  for SDXL single-frame sprite/pixel-art generation. The multi-frame path and
  other models remain unaffected.

[Source CI run 38085758492](https://github.com/dbrckk/asset-forge/actions/runs/38085758492)
has 3/3 existing CI jobs green on exact source SHA `0fa4cf6107179c17619dfd8e135f661f4c43f7a3`.
No new unit tests, changes to credentials, or weakening of acceptance thresholds.

**Still unqualified:** these changes need one separately identified fresh real
generation, exact CI on its tested commit, independent semantic acceptance,
technical acceptance (including border), inspection of actual pixels and a
consumer import/build before merging PR #13 or declaring delivery.

## 2026-10-10 fifth strict raster probe — model fidelity still blocked

[Run 38085943888](https://github.com/dbrckk/asset-forge/actions/runs/38085943888)
completed **failure**, one-shot attempt 1, job `114312341235`, on probe SHA
`c076e9469ff239bb5034946413a87d710006fecd`. It passed the corrected
single-frame prompt preflight and executed a real Cloudflare SDXL generation.
Artifact ZIP `11682352377` (`strict-raster-negative-prompt-fixed-real-20261010`)
was inspected, including its actual raw image and independent structured review.
**Never rerun this probe**, or any prior probe #1–#4.

- `generated-raw.png`: 512x512 RGBA, SHA-256
  `49f4c925e0f5af4e22691f8b2b16d150467d34f7d8c5e0620dbf81780d76870b`.
- `live-raster-cell.png`: 96x96 RGBA, SHA-256
  `52292bfd102b1a931f24d2586d94dd83b95564df2e1c521cbbd675fc65cc6cd2`.
- Technical quality **1.000 >= 0.650**; borderAlphaRatio **0.0 <= 0.08**.
- Semantic overall **0.74 >= 0.72**, but required
  `instructionFidelity=0.15 < 0.72` (**FAIL**).
- The inspected image is a square cyan-framed, multi-component interface-like
  icon, **not** the requested single dark metallic cylindrical power cell
  with one cyan emissive strip. Transparency alone does not fix subject fidelity.
- The final `production-report.json` has `success=false`,
  `artifact=null`; there is **no** successful consumer import or release.

**Stop-loss:** after repeated real SDXL failures on the same strict
single-subject contract, code commit
[`a56f1ba`](https://github.com/dbrckk/asset-forge/commit/a56f1ba921fb1d25b6ac33635a0eb64f9f666dba)
makes only `auto` routing for `semanticArtReviewRequired=true` and
`expectedFrames=1` sprite/pixel-art prefer available `kaggle-qwen`.
If Qwen is not configured/ready, it fails with an actionable message rather
than spending more SDXL requests. If Qwen fails, do not silently fall back to
the repeatedly inadequate SDXL route. All ordinary raster requests and
explicit backend choices retain existing behavior. This is a risk-mitigation
change, **not proof** that Kaggle/Qwen can now deliver a qualified image.

Next qualification requires exact CI on this routing change, a verified
available Qwen route, one *separate* authorized bounded generation, semantic
`overall` and `instructionFidelity` each >=0.72, full technical/alpha
checks, inspection of actual image, SHA and compatible consumer import/build.
Do not open another SDXL probe with the same specification and do not merge PR
#13 before real qualification.

## 2026-10-10 — Qwen-Image-2.1 model license checkpoint

Official source: [Qwen-Image-2.1 main license](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE)
and [model card](https://huggingface.co/Qwen/Qwen-Image-2.1).
The published **Qwen Research License Agreement** grants model-use rights for
research/noncommercial evaluation; commercial model use requires a separate
commercial license. A manifest's `license.id=project-owned` or
`commercialUse=true` is **not** evidence of rights to use this model in a
commercial production pipeline. Rights to the *generated image output* need
their own review and are **not** automatically resolved by model metadata.

Code [`1f69d7a`](https://github.com/dbrckk/asset-forge/commit/1f69d7a3b24e1b66c38a8e5e868a4957a70bc9b2)
now fails closed before default Qwen-Image-2.1 inference if a job
declares `manifest.license.commercialUse=true`. It also forbids a
commercial request from silently falling back from Cloudflare to Qwen.
For `auto` strict single-sprite mode, a commercial-use manifest is
rejected rather than auto-selected into the research-only Qwen default.
Explicit alternative models may have their own terms and require separate
verification. No license grant can be inferred from an API credential.

Example [`5e49628`](https://github.com/dbrckk/asset-forge/commit/5e49628b7ed626cc703eae0ba836f7b6ffcc2efc)
marks `examples/production-request-strict-raster.json` as
`research-evaluation-only`, `commercialUse=false`, and
`attributionRequired=true`. This is a **noncommercial diagnostic**, not
an approval to publish any Qwen-derived artwork into a monetized Roblox
game or another commercial product.

The independent one-shot Qwen generation [run 38087387660](https://github.com/dbrckk/asset-forge/actions/runs/38087387660)
was already launched on a distinct earlier probe SHA
`2ce97b860c98eb1285485b9ecfeac752bc14d3e2` and the *previous*
sample manifest, before this licensing correction. Do not rerun it.
Regardless of pixel-quality scores, that earlier run is **not** commercial
production qualification. Inspect its terminal report and real PNG only
as diagnostic research evidence. Consumer release remains blocked until
model and output rights have been independently confirmed and an actual
consumer integration/build succeeds.
