from __future__ import annotations

import json
from pathlib import Path


SCHEMA = "asset-forge/backend-history/v1"
MIN_SAMPLES_FOR_ADAPTIVE_ROUTING = 3
DEFAULT_QUALITY = 0.5


def empty_history() -> dict:
    return {
        "schema": SCHEMA,
        "backends": {},
    }


def load_history(path: Path | str | None) -> dict:
    if path is None:
        return empty_history()
    target = Path(path)
    if not target.is_file():
        return empty_history()
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return empty_history()
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        return empty_history()
    backends = value.get("backends")
    if not isinstance(backends, dict):
        value["backends"] = {}
    return value


def _stats(history: dict, backend: str) -> dict:
    backends = history.setdefault("backends", {})
    value = backends.get(backend)
    if not isinstance(value, dict):
        value = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "qualitySamples": 0,
            "qualitySum": 0.0,
        }
        backends[backend] = value
    return value


def _quality_from_generation(result: dict) -> float | None:
    samples = []
    for key in ("visualSimilarity", "technicalQuality"):
        value = result.get(key)
        if not isinstance(value, dict):
            continue
        attempts = value.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            continue
        score = attempts[-1].get("score") if isinstance(attempts[-1], dict) else None
        if isinstance(score, (int, float)):
            samples.append(float(score))
    if not samples:
        return None
    return max(0.0, min(1.0, sum(samples) / len(samples)))


def _record(
    history: dict,
    backend: str,
    *,
    success: bool,
    quality: float | None = None,
) -> None:
    name = str(backend or "").strip()
    if not name:
        return
    stats = _stats(history, name)
    stats["attempts"] = int(stats.get("attempts") or 0) + 1
    if success:
        stats["successes"] = int(stats.get("successes") or 0) + 1
    else:
        stats["failures"] = int(stats.get("failures") or 0) + 1
    if isinstance(quality, (int, float)):
        bounded = max(0.0, min(1.0, float(quality)))
        stats["qualitySamples"] = int(stats.get("qualitySamples") or 0) + 1
        stats["qualitySum"] = float(stats.get("qualitySum") or 0.0) + bounded


def record_generation_result(path: Path | str | None, result: dict) -> dict:
    history = load_history(path)
    quality = _quality_from_generation(result)

    failed_backends = set()
    fallbacks = result.get("fallbacks")
    if isinstance(fallbacks, list):
        for fallback in fallbacks:
            if not isinstance(fallback, dict):
                continue
            reason = str(fallback.get("reason") or "")
            source = str(fallback.get("from") or "").strip()
            if source and "error" in reason:
                _record(history, source, success=False)
                failed_backends.add(source)

    final_backend = str(result.get("backend") or "").strip()
    if final_backend:
        _record(history, final_backend, success=True, quality=quality)

    reference_generation = result.get("referenceGeneration")
    if isinstance(reference_generation, dict):
        reference_backend = str(reference_generation.get("backend") or "").strip()
        if reference_backend:
            reference_quality = _quality_from_generation(reference_generation)
            _record(
                history,
                reference_backend,
                success=reference_generation.get("success") is True,
                quality=reference_quality,
            )

    metadata = result.get("metadata")
    raster_backend = (
        str(metadata.get("rasterBackend") or "").strip()
        if isinstance(metadata, dict)
        else ""
    )
    if (
        raster_backend
        and raster_backend != final_backend
        and raster_backend not in failed_backends
    ):
        _record(history, raster_backend, success=True, quality=quality)

    if path is not None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(history, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
    return history


def backend_score(history: dict, backend: str, *, prior: float) -> float:
    value = history.get("backends", {}).get(backend)
    if not isinstance(value, dict):
        return prior
    attempts = int(value.get("attempts") or 0)
    if attempts < MIN_SAMPLES_FOR_ADAPTIVE_ROUTING:
        # Keep the configured order while a backend is unproven, but give
        # sufficiently observed reliable backends room to outrank unknown
        # alternatives. This avoids needless provider churn after a few
        # successful production runs.
        return 0.8 * prior

    successes = int(value.get("successes") or 0)
    quality_samples = int(value.get("qualitySamples") or 0)
    quality_sum = float(value.get("qualitySum") or 0.0)

    reliability = max(0.0, min(1.0, successes / max(1, attempts)))
    quality = (
        max(0.0, min(1.0, quality_sum / quality_samples))
        if quality_samples > 0
        else None
    )
    if quality is None:
        # Do not penalize a backend merely because older successful runs did
        # not yet emit quality telemetry. Reliability plus configured priority
        # must still be able to outrank an entirely unknown alternative.
        return 0.90 * reliability + 0.10 * prior
    return 0.72 * reliability + 0.23 * quality + 0.05 * prior


def choose_backend(
    ready_backends: list[str],
    *,
    history_path: Path | str | None = None,
    default_order: list[str] | None = None,
) -> str | None:
    ready = [str(value) for value in ready_backends if str(value)]
    if not ready:
        return None

    order = list(default_order or ready)
    priority = {
        name: 1.0 - min(index, 20) * 0.02
        for index, name in enumerate(order)
    }
    history = load_history(history_path)

    candidates = []
    for index, backend in enumerate(ready):
        prior = priority.get(backend, 0.5)
        score = backend_score(history, backend, prior=prior)
        candidates.append((score, -index, backend))
    candidates.sort(reverse=True)
    return candidates[0][2]
