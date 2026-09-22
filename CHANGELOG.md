# Changelog

## 1.0.0 - 2026-09-22

First stable Asset Forge release.

### Production pipeline

- End-to-end Production OS contract for raster, SVG/vector, and 3D assets.
- Free-first raster routing with Cloudflare Workers AI and Kaggle Qwen Image fallback.
- Local VTracer vector path and Kaggle TripoSR 3D path, with quality-aware fallback behavior.
- Dependency-aware batch execution, artifact bundling, circuit breaking, and engine handoff validation.

### Quality and reliability

- Structural, technical-art, semantic, visual-similarity, SVG, glTF/GLB, atlas, and engine validation gates.
- Premium/AAA prompt guards for production assets, alpha handling, sprite-sheet consistency, and animation-ready framing.
- Diagnostic-aware regeneration for border clearance, subject scale, contrast, frame diversity, frame anchoring, transparency, and general quality.
- Adaptive backend routing based on reliability, quality, fallback pressure, and regeneration pressure.
- Persistent learning of corrective retry effectiveness with bounded exploration of untried strategies.
- Per-asset and batch-level routing, fallback, retry, quality, and backend telemetry.

### Stability

- Production history persists safely between CI/Production OS runs.
- History failures are advisory and never invalidate an otherwise valid asset.
- Real live generation smoke tests and Deadline Zero visual pilot remain part of the release validation path.
- Packaged CLI and wheel resources are validated in CI.
