from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable


class SemanticArtReviewError(RuntimeError):
    pass


def _credential_available(*, environ=None, home: Path | None = None) -> bool:
    env = os.environ if environ is None else environ
    if str(env.get("POLLINATIONS_API_KEY") or "").strip():
        return True
    root = Path.home() if home is None else Path(home)
    return (root / ".pollinations" / "credentials.json").is_file()


def _json_from_text(value: str) -> dict | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    candidates = [raw]
    fenced = re.search(r"\{[\s\S]*\}", raw)
    if fenced:
        candidates.append(fenced.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _extract_review(stdout: str) -> dict | None:
    outer = _json_from_text(stdout)
    if outer is None:
        return None
    required = {"overall", "anatomy", "artifacts", "textReadability", "styleConsistency"}
    if required.issubset(outer):
        return outer
    for key in ("text", "content", "response", "output", "message"):
        value = outer.get(key)
        if isinstance(value, str):
            nested = _json_from_text(value)
            if isinstance(nested, dict) and required.issubset(nested):
                return nested
        if isinstance(value, dict) and required.issubset(value):
            return value
    return None


def _number(value, name: str) -> float:
    if isinstance(value, bool):
        raise SemanticArtReviewError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SemanticArtReviewError(f"{name} must be numeric") from exc
    if not 0.0 <= result <= 1.0:
        raise SemanticArtReviewError(f"{name} must be between 0 and 1")
    return result


def review_raster_art(
    path: Path,
    manifest: dict,
    *,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    environ=None,
    home: Path | None = None,
    timeout_seconds: float = 120.0,
) -> dict:
    constraints = manifest.get("constraints") if isinstance(manifest, dict) else {}
    constraints = constraints if isinstance(constraints, dict) else {}
    enabled = constraints.get("semanticArtReview") is True
    required = constraints.get("semanticArtReviewRequired") is True
    threshold = _number(constraints.get("semanticQualityMin", 0.65), "semanticQualityMin")
    if not enabled and not required:
        return {
            "available": False,
            "enabled": False,
            "required": False,
            "passed": None,
            "threshold": threshold,
            "reason": "disabled",
        }

    executable = shutil.which("polli")
    authenticated = _credential_available(environ=environ, home=home)
    if not executable or not authenticated:
        if required:
            raise SemanticArtReviewError("semantic art review requires authenticated polli CLI")
        return {
            "available": False,
            "enabled": True,
            "required": False,
            "passed": None,
            "threshold": threshold,
            "reason": "provider_unavailable",
        }

    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 0:
        raise SemanticArtReviewError("semantic art review image is missing or empty")

    uploaded = runner(
        [executable, "upload", str(path), "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if uploaded.returncode != 0:
        if required:
            raise SemanticArtReviewError("semantic art review upload failed")
        return {
            "available": False,
            "enabled": True,
            "required": False,
            "passed": None,
            "threshold": threshold,
            "reason": "upload_failed",
        }
    upload_payload = _json_from_text(str(uploaded.stdout or "")) or {}
    image_url = str(
        upload_payload.get("url")
        or upload_payload.get("media_url")
        or upload_payload.get("mediaUrl")
        or ""
    ).strip()
    if not image_url.startswith("https://"):
        if required:
            raise SemanticArtReviewError("semantic art review upload returned no HTTPS URL")
        return {
            "available": False,
            "enabled": True,
            "required": False,
            "passed": None,
            "threshold": threshold,
            "reason": "upload_url_missing",
        }

    asset_type = str(manifest.get("type") or "visual asset")
    importance = str(manifest.get("importance") or "primary")
    prompt = (
        "Act as a strict senior game-art QA reviewer. Inspect the supplied image as a "
        f"{importance} {asset_type}. Score each field from 0 to 1. Detect broken anatomy "
        "or perspective, duplicated/malformed limbs or objects, generation artifacts, "
        "unreadable accidental text, clipping, inconsistent materials/lighting, and weak "
        "professional game-art finish. Return JSON only with keys: overall, anatomy, "
        "artifacts, textReadability, styleConsistency, issues. issues must be an array of "
        "short strings. Do not add markdown."
    )
    reviewed = runner(
        [executable, "gen", "text", prompt, "--image", image_url, "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if reviewed.returncode != 0:
        if required:
            raise SemanticArtReviewError("semantic art review model call failed")
        return {
            "available": False,
            "enabled": True,
            "required": False,
            "passed": None,
            "threshold": threshold,
            "reason": "review_failed",
        }

    value = _extract_review(str(reviewed.stdout or ""))
    if value is None:
        if required:
            raise SemanticArtReviewError("semantic art review returned invalid structured output")
        return {
            "available": False,
            "enabled": True,
            "required": False,
            "passed": None,
            "threshold": threshold,
            "reason": "invalid_output",
        }

    scores = {
        key: _number(value.get(key), key)
        for key in ("overall", "anatomy", "artifacts", "textReadability", "styleConsistency")
    }
    issues = value.get("issues")
    if not isinstance(issues, list):
        issues = []
    issues = [str(item)[:240] for item in issues[:12]]
    passed = scores["overall"] >= threshold
    return {
        "available": True,
        "enabled": True,
        "required": required,
        "passed": passed,
        "threshold": threshold,
        "scores": scores,
        "issues": issues,
        "provider": "pollinations-vision",
    }
