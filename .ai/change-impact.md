# Change impact

Base: 23bb23af53cdccf16a6a024bb41dc6513b7b628b
Head: 17e6c395faba61eb7eb2c5f6e30e0fa9b2df8df7

## Changed files
- M .github/workflows/production-os-batch.yml
- M .github/workflows/production-os-dispatch.yml
- M .github/workflows/validate.yml
- M art_quality.py
- M asset_forge.py
- M cloudflare_backend.py
- A docs/production-raster-quality-gate.md
- A examples/production-request-strict-raster.json
- M generator_backends.py
- A integration/godot4_import_smoke.py
- M production_executor.py
- M remote_batch.py
- M semantic_art_review.py
- M tests/test_remote_batch.py

## Affected areas
- .github
- (root)
- docs
- examples
- integration
- tests

## Related test candidates
- tests/test_art_quality.py
- tests/test_asset_forge.py
- tests/test_cloudflare_backend.py
- tests/test_generator_backends.py
- tests/test_production_executor.py
- tests/test_remote_batch.py
- tests/test_semantic_art_review.py

## Agent guidance
- Read this file before broad repository exploration.
- Inspect only the affected areas first.
- Use .ai/commands.json to choose validation commands.
- Expand scope only if the change crosses module boundaries or tests fail.
