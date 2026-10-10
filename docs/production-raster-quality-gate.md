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
