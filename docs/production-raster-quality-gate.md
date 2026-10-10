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
