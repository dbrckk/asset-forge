from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path


LIBRARY_SCHEMA = "asset-forge/library/v1"


class AssetLibraryError(RuntimeError):
    pass


def default_library_path() -> Path:
    configured = str(os.environ.get("ASSET_FORGE_LIBRARY") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "asset-forge" / "library.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reference_rows(reference_paths: list[Path] | None) -> list[dict]:
    rows = []
    for path in reference_paths or []:
        candidate = Path(path)
        if not candidate.is_file():
            raise AssetLibraryError(f"reference file missing: {candidate}")
        rows.append({"sha256": _sha256(candidate), "suffix": candidate.suffix.lower()})
    return rows


def request_fingerprint(
    job: dict,
    *,
    backend: str = "auto",
    model: str | None = None,
    resolution: str = "low",
    reference_paths: list[Path] | None = None,
) -> str:
    payload = {
        "schema": "asset-forge/cache-key/v1",
        "project": job.get("project"),
        "assetId": job.get("assetId"),
        "assetType": job.get("assetType"),
        "instruction": job.get("instruction"),
        "manifest": job.get("manifest"),
        "backend": backend,
        "model": model,
        "resolution": resolution,
        "references": _reference_rows(reference_paths),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _empty() -> dict:
    return {"schema": LIBRARY_SCHEMA, "entries": []}


def load_library(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        return _empty()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssetLibraryError("asset library is unreadable") from exc
    if not isinstance(payload, dict) or payload.get("schema") != LIBRARY_SCHEMA:
        raise AssetLibraryError("unsupported asset library schema")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise AssetLibraryError("asset library entries must be a list")
    return payload


def lookup(
    path: Path,
    fingerprint: str,
) -> dict | None:
    library = load_library(path)
    for entry in reversed(library["entries"]):
        if not isinstance(entry, dict) or entry.get("fingerprint") != fingerprint:
            continue
        artifact = Path(str(entry.get("artifact") or ""))
        expected = str(entry.get("sha256") or "")
        if (
            artifact.is_file()
            and expected
            and _sha256(artifact) == expected
        ):
            return dict(entry)
    return None


def _next_version(entries: list[dict], project: str, asset_id: str) -> int:
    versions = [
        int(item.get("version") or 0)
        for item in entries
        if isinstance(item, dict)
        and item.get("project") == project
        and item.get("assetId") == asset_id
    ]
    return max(versions, default=0) + 1


def record_success(
    library_path: Path,
    *,
    fingerprint: str,
    job: dict,
    result: dict,
) -> dict:
    artifact = Path(str(result.get("artifact") or ""))
    if result.get("success") is not True or not artifact.is_file():
        raise AssetLibraryError("only successful artifacts can enter the library")

    library_path = Path(library_path)
    library_path.parent.mkdir(parents=True, exist_ok=True)
    store = library_path.parent / "objects"
    store.mkdir(parents=True, exist_ok=True)

    digest = _sha256(artifact)
    stored = store / (digest + artifact.suffix.lower())
    if not stored.is_file():
        shutil.copyfile(artifact, stored)

    project = str(job.get("project") or "")
    asset_id = str(job.get("assetId") or "")
    library = load_library(library_path)
    version = _next_version(library["entries"], project, asset_id)

    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    technical = validation.get("technicalArt") if isinstance(validation.get("technicalArt"), dict) else {}
    metrics = technical.get("metrics") if isinstance(technical.get("metrics"), dict) else {}
    generation = result.get("generation") if isinstance(result.get("generation"), dict) else {}
    visual = generation.get("visualSimilarity") if isinstance(generation.get("visualSimilarity"), dict) else {}
    attempts = visual.get("attempts") if isinstance(visual.get("attempts"), list) else []
    final_similarity = (
        attempts[-1].get("score")
        if attempts and isinstance(attempts[-1], dict)
        else None
    )

    entry = {
        "fingerprint": fingerprint,
        "project": project,
        "assetId": asset_id,
        "assetType": job.get("assetType"),
        "version": version,
        "sha256": digest,
        "artifact": str(stored),
        "bytes": stored.stat().st_size,
        "backend": generation.get("backend"),
        "model": generation.get("model"),
        "technicalQuality": technical.get("score"),
        "visualSimilarity": final_similarity,
        "perceptualHash": metrics.get("perceptualHash"),
        "averageRgb": metrics.get("averageRgb"),
    }
    library["entries"].append(entry)
    library_path.write_text(
        json.dumps(library, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return entry


def hamming_hex(left: str, right: str) -> int:
    if not left or not right or len(left) != len(right):
        return 10**9
    try:
        return (int(left, 16) ^ int(right, 16)).bit_count()
    except ValueError:
        return 10**9


def similar_entries(
    library_path: Path,
    *,
    project: str,
    asset_type: str,
    perceptual_hash: str,
    max_hamming: int = 12,
) -> list[dict]:
    library = load_library(library_path)
    rows = []
    for entry in library["entries"]:
        if not isinstance(entry, dict):
            continue
        if entry.get("project") != project or entry.get("assetType") != asset_type:
            continue
        distance = hamming_hex(str(entry.get("perceptualHash") or ""), perceptual_hash)
        if distance <= max_hamming:
            rows.append({**entry, "perceptualDistance": distance})
    rows.sort(key=lambda item: (item["perceptualDistance"], -int(item.get("version") or 0)))
    return rows
