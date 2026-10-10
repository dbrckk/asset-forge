# Raster production quality gate (fail closed)

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
