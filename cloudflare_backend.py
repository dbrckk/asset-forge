from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"


class CloudflareGenerationError(RuntimeError):
    pass


def status(*, environ=None) -> dict:
    env = os.environ if environ is None else environ
    token = str(env.get("CLOUDFLARE_API_TOKEN") or "").strip()
    account = str(env.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()
    ready = bool(token and account)
    return {
        "authenticated": ready,
        "rasterReady": ready,
        "vectorSvgReady": False,
        "threeDReady": False,
        "credentialSource": "environment" if ready else None,
        "model": DEFAULT_MODEL,
    }


def _extract_image_bytes(raw: bytes, content_type: str) -> bytes:
    if content_type.startswith("image/"):
        return raw
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CloudflareGenerationError(
            "Cloudflare Workers AI returned neither image bytes nor JSON"
        ) from exc

    if isinstance(payload, dict) and payload.get("success") is False:
        errors = payload.get("errors")
        raise CloudflareGenerationError(
            "Cloudflare Workers AI request failed"
            + (f": {errors}" if errors else "")
        )

    candidates = []
    if isinstance(payload, dict):
        result = payload.get("result")
        if isinstance(result, str):
            candidates.append(result)
        elif isinstance(result, dict):
            for key in ("image", "data", "b64_json", "base64"):
                value = result.get(key)
                if isinstance(value, str):
                    candidates.append(value)
        for key in ("image", "data", "b64_json", "base64"):
            value = payload.get(key)
            if isinstance(value, str):
                candidates.append(value)

    for candidate in candidates:
        value = candidate.strip()
        if value.startswith("data:image") and "," in value:
            value = value.split(",", 1)[1]
        try:
            decoded = base64.b64decode(value, validate=True)
        except ValueError:
            continue
        if decoded:
            return decoded

    raise CloudflareGenerationError("Cloudflare Workers AI JSON response contained no image")


def generate(
    prompt: str,
    output: Path,
    *,
    width: int = 1024,
    height: int = 1024,
    seed: int = 0,
    steps: int = 20,
    reference_path: Path | None = None,
    strength: float = 0.55,
    guidance: float = 7.5,
    model: str = DEFAULT_MODEL,
    timeout_seconds: float = 180.0,
    environ=None,
    opener=urllib.request.urlopen,
) -> dict:
    env = os.environ if environ is None else environ
    token = str(env.get("CLOUDFLARE_API_TOKEN") or "").strip()
    account = str(env.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()
    if not token or not account:
        raise CloudflareGenerationError(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID are required"
        )
    if not str(prompt or "").strip():
        raise CloudflareGenerationError("prompt is required")

    width = max(256, min(2048, int(width)))
    height = max(256, min(2048, int(height)))
    steps = max(1, min(20, int(steps)))
    payload = {
        "prompt": str(prompt),
        "width": width,
        "height": height,
        "num_steps": steps,
        "guidance": float(guidance),
        "seed": int(seed),
    }
    if reference_path is not None:
        reference = Path(reference_path)
        if not reference.is_file() or reference.stat().st_size <= 0:
            raise CloudflareGenerationError(f"reference file missing or empty: {reference}")
        payload["image_b64"] = base64.b64encode(reference.read_bytes()).decode("ascii")
        payload["strength"] = max(0.0, min(1.0, float(strength)))

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        + urllib.parse.quote(account, safe="")
        + "/ai/run/"
        + model
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "image/*, application/json",
            "User-Agent": "asset-forge-cloudflare",
        },
    )
    try:
        with opener(request, timeout=float(timeout_seconds)) as response:
            raw = response.read()
            content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
    except urllib.error.HTTPError as exc:
        detail = exc.read(4000).decode("utf-8", errors="replace")
        raise CloudflareGenerationError(
            f"Cloudflare Workers AI HTTP {exc.code}: {detail[:1000]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise CloudflareGenerationError(f"Cloudflare Workers AI network error: {exc}") from exc

    image = _extract_image_bytes(raw, content_type)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    return {
        "provider": "cloudflare-workers-ai",
        "model": model,
        "width": width,
        "height": height,
        "steps": steps,
        "seed": int(seed),
        "reference": reference_path is not None,
    }
