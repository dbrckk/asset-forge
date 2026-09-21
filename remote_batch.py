from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


RASTER_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}
AUTO_BACKEND_CIRCUIT_BREAKER_FAILURES = 2


class RemoteBatchError(RuntimeError):
    pass


def _fallback_count(routing: dict) -> int:
    raw = routing.get("fallbackCount") if isinstance(routing, dict) else None
    if isinstance(raw, int) and raw >= 0:
        return raw
    fallbacks = routing.get("fallbacks") if isinstance(routing, dict) else None
    return len(fallbacks) if isinstance(fallbacks, list) else 0


def _cloudflare_runtime_fallback_count(routing: dict) -> int:
    fallbacks = routing.get("fallbacks") if isinstance(routing, dict) else None
    if not isinstance(fallbacks, list):
        return 0
    return sum(
        1
        for item in fallbacks
        if isinstance(item, dict)
        and item.get("from") == "cloudflare"
        and item.get("to") == "kaggle-qwen"
        and item.get("reason") == "cloudflare-generation-error"
    )


def _safe_id(value: str) -> str:
    value = str(value or "").strip()
    if not value or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._" for ch in value):
        raise RemoteBatchError("batch item id must be filename-safe")
    return value


def _ordered_items(items: list[dict]) -> list[dict]:
    indexed: dict[str, dict] = {}
    order: list[str] = []
    for index, raw in enumerate(items):
        if not isinstance(raw, dict):
            raise RemoteBatchError("batch item must be an object")
        request = raw.get("request")
        if not isinstance(request, dict):
            raise RemoteBatchError("batch item request is required")
        item_id = _safe_id(raw.get("id") or request.get("requestId") or f"item-{index + 1}")
        if item_id in indexed:
            raise RemoteBatchError(f"duplicate batch item id: {item_id}")
        item = dict(raw)
        item["_id"] = item_id
        deps = item.get("depends_on") or []
        if isinstance(deps, str):
            deps = [deps]
        if not isinstance(deps, list):
            raise RemoteBatchError(f"depends_on for {item_id} must be a list")
        item["_deps"] = [str(dep).strip() for dep in deps if str(dep).strip()]
        indexed[item_id] = item
        order.append(item_id)

    indegree = {item_id: 0 for item_id in indexed}
    dependents = {item_id: [] for item_id in indexed}
    for item_id, item in indexed.items():
        seen = set()
        for dependency in item["_deps"]:
            if dependency == item_id:
                raise RemoteBatchError(f"batch item cannot depend on itself: {item_id}")
            if dependency not in indexed:
                raise RemoteBatchError(f"unknown dependency for {item_id}: {dependency}")
            if dependency in seen:
                continue
            seen.add(dependency)
            indegree[item_id] += 1
            dependents[dependency].append(item_id)

    ready = [item_id for item_id in order if indegree[item_id] == 0]
    result: list[dict] = []
    while ready:
        current = ready.pop(0)
        result.append(indexed[current])
        for child in dependents[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(result) != len(items):
        raise RemoteBatchError("cyclic batch dependencies")
    return result


def run(
    spec_path: Path,
    output_root: Path,
    *,
    backend: str = "auto",
    model: str | None = None,
    executable: str = "asset-forge",
) -> dict:
    payload = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        raise RemoteBatchError("batch spec must contain a non-empty items list")

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    bundle_root = output_root / "bundle"
    bundle_root.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, Path] = {}
    results = []
    auto_backend_override: str | None = None
    cloudflare_runtime_failures = 0
    for item in _ordered_items(items):
        item_id = item["_id"]
        request = item["request"]
        request_id = _safe_id(request.get("requestId") or item_id)
        target_path = str(item.get("target_path") or "").strip().replace("\\", "/").lstrip("/")
        if not target_path or any(part in {"", ".", ".."} for part in target_path.split("/")):
            raise RemoteBatchError(f"unsafe target_path for {item_id}")

        item_root = output_root / "jobs" / request_id
        item_root.mkdir(parents=True, exist_ok=True)
        request_path = item_root / "request.json"
        request_path.write_text(
            json.dumps(request, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        item_backend = auto_backend_override or backend
        cmd = [
            executable,
            "fulfill",
            str(request_path),
            "--output-dir",
            str(item_root),
            "--backend",
            item_backend,
        ]
        if model:
            cmd.extend(["--model", model])
        source_path = str(item.get("source_path") or "").strip()
        if source_path:
            cmd.extend(["--source", source_path])
        else:
            for dependency in item["_deps"]:
                parent = artifacts.get(dependency)
                if parent and parent.suffix.lower() in RASTER_SUFFIXES:
                    cmd.extend(["--reference", str(parent)])

        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RemoteBatchError(
                f"asset-forge failed for {item_id}"
                + (f": {detail[:1200]}" if detail else "")
            )

        report_path = item_root / "production-report.json"
        if not report_path.is_file():
            raise RemoteBatchError(f"missing production report for {item_id}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("success") is not True:
            raise RemoteBatchError(f"production report failed for {item_id}")
        artifact = Path(str(report.get("artifact") or ""))
        if not artifact.is_absolute():
            # Production reports may return either a path relative to the
            # per-job directory or a repository-relative path that already
            # includes output_root. Accept both, then enforce containment.
            local_candidate = item_root / artifact
            artifact = local_candidate if local_candidate.is_file() else artifact
        if not artifact.is_file():
            raise RemoteBatchError(f"missing artifact for {item_id}")
        artifact = artifact.resolve()
        if not artifact.is_relative_to(item_root.resolve()):
            raise RemoteBatchError(f"artifact escapes item output for {item_id}")

        bundled = bundle_root / f"{item_id}{artifact.suffix.lower()}"
        shutil.copyfile(artifact, bundled)
        digest = hashlib.sha256(bundled.read_bytes()).hexdigest()
        artifacts[item_id] = bundled

        additional_rows = []
        raw_additional = report.get("additionalArtifacts")
        if raw_additional is None:
            raw_additional = []
        if not isinstance(raw_additional, list):
            raise RemoteBatchError(f"invalid additionalArtifacts for {item_id}")
        for extra_index, raw_path in enumerate(raw_additional, start=1):
            extra = Path(str(raw_path or ""))
            if not extra.is_absolute():
                extra = item_root / extra
            extra = extra.resolve()
            if not extra.is_relative_to(item_root.resolve()):
                raise RemoteBatchError(
                    f"additional artifact escapes item output for {item_id}"
                )
            if not extra.is_file() or extra.stat().st_size <= 0:
                raise RemoteBatchError(
                    f"additional artifact missing for {item_id}"
                )
            extra_name = extra.name
            if extra_name.startswith(artifact.stem + "."):
                bundle_name = f"{item_id}{extra_name[len(artifact.stem):]}"
            else:
                bundle_name = f"{item_id}.extra{extra_index}{extra.suffix.lower()}"
            bundled_extra = bundle_root / bundle_name
            shutil.copyfile(extra, bundled_extra)
            additional_rows.append({
                "artifact": str(bundled_extra.relative_to(output_root)),
                "sha256": hashlib.sha256(bundled_extra.read_bytes()).hexdigest(),
                "source_name": extra_name,
            })

        generation = report.get("generation") if isinstance(report.get("generation"), dict) else {}
        validation = report.get("validation") if isinstance(report.get("validation"), dict) else {}
        routing = report.get("routing") if isinstance(report.get("routing"), dict) else {}
        if backend == "auto" and auto_backend_override is None:
            cloudflare_runtime_failures += _cloudflare_runtime_fallback_count(routing)
            if cloudflare_runtime_failures >= AUTO_BACKEND_CIRCUIT_BREAKER_FAILURES:
                auto_backend_override = "kaggle-qwen"
        results.append({
            "id": item_id,
            "depends_on": list(item["_deps"]),
            "request_id": request_id,
            "target_path": target_path,
            "artifact": str(bundled.relative_to(output_root)),
            "sha256": digest,
            "visual_similarity": (
                generation.get("visualSimilarity")
                if isinstance(generation.get("visualSimilarity"), dict)
                else None
            ),
            "technical_art": (
                validation.get("technicalArt")
                if isinstance(validation.get("technicalArt"), dict)
                else None
            ),
            "semantic_art": (
                validation.get("semanticArt")
                if isinstance(validation.get("semanticArt"), dict)
                else None
            ),
            "routing": routing or None,
            "additional_artifacts": additional_rows,
            "library": (
                report.get("library")
                if isinstance(report.get("library"), dict)
                else None
            ),
        })

    quality = [item["visual_similarity"] for item in results if item["visual_similarity"]]
    scores = [
        float(value["attempts"][-1]["score"])
        for value in quality
        if isinstance(value.get("attempts"), list)
        and value["attempts"]
        and isinstance(value["attempts"][-1].get("score"), (int, float))
    ]
    technical_quality = [
        item["technical_art"]
        for item in results
        if isinstance(item.get("technical_art"), dict)
        and isinstance(item["technical_art"].get("score"), (int, float))
    ]
    technical_scores = [
        float(value["score"])
        for value in technical_quality
    ]
    combined_scores = scores + technical_scores
    routed = [
        item["routing"]
        for item in results
        if isinstance(item.get("routing"), dict)
    ]
    final_backends: dict[str, int] = {}
    for routing in routed:
        final_backend = str(routing.get("finalBackend") or "").strip()
        if final_backend:
            final_backends[final_backend] = final_backends.get(final_backend, 0) + 1

    result = {
        "schema_version": "asset-forge/remote-batch-result/v1",
        "success": True,
        "count": len(results),
        "execution_order": [item["id"] for item in results],
        "routing_summary": {
            "reported": len(routed),
            "items_with_fallback": sum(
                1 for routing in routed
                if _fallback_count(routing) > 0
            ),
            "fallback_count": sum(
                _fallback_count(routing)
                for routing in routed
            ),
            "final_backends": final_backends,
            "circuit_breaker": {
                "threshold": AUTO_BACKEND_CIRCUIT_BREAKER_FAILURES,
                "cloudflare_runtime_failures": cloudflare_runtime_failures,
                "override": auto_backend_override,
                "open": auto_backend_override is not None,
            },
        },
        "quality_summary": {
            "checked": sum(
                1 for item in results
                if item.get("visual_similarity")
                or (
                    isinstance(item.get("technical_art"), dict)
                    and isinstance(item["technical_art"].get("score"), (int, float))
                )
            ),
            "visual_checked": len(quality),
            "technical_checked": len(technical_quality),
            "regenerated": sum(
                1 for value in quality
                if len(value.get("attempts") or []) > 1
            ),
            "minimum_score": min(combined_scores) if combined_scores else None,
            "minimum_visual_score": min(scores) if scores else None,
            "minimum_technical_score": (
                min(technical_scores) if technical_scores else None
            ),
        },
        "items": results,
    }
    (output_root / "batch-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run a dependency-aware Asset Forge batch")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--backend",
        choices=["auto", "cloudflare", "kaggle-qwen", "qwen-colab", "pollinations", "imagen-codex", "vtracer", "kaggle-triposr"],
        default="auto",
    )
    parser.add_argument("--model")
    args = parser.parse_args(argv)
    result = run(
        args.spec,
        args.output_root,
        backend=args.backend,
        model=args.model,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
