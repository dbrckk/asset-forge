from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


DEFAULT_MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
FLUX_KLEIN_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"


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



def _flux_multipart_payload(
    prompt: str,
    *,
    width: int,
    height: int,
    seed: int,
    guidance: float,
    references: list[Path],
) -> tuple[bytes, str]:
    """Workers AI FLUX.2 Klein 4B requires multipart, including prompt-only.

    Verify all references and limits locally, before contacting the provider.
    The hosted model accepts at most four PNG/JPEG images strictly below
    512 x 512. Do not silently shrink or modify user-provided reference art.
    """
    if not 256 <= width <= 1920 or not 256 <= height <= 1920:
        raise CloudflareGenerationError("FLUX.2 output dimensions must be 256..1920")
    if len(references) > 4:
        raise CloudflareGenerationError("FLUX.2 accepts at most four visual references")

    image_parts: list[tuple[str, str, bytes]] = []
    for index, source in enumerate(references):
        reference = Path(source)
        if not reference.is_file():
            raise CloudflareGenerationError("FLUX.2 reference file is missing")
        if reference.stat().st_size <= 0 or reference.stat().st_size > 5_000_000:
            raise CloudflareGenerationError("FLUX.2 reference size is outside safe bounds")
        try:
            from PIL import Image
            with Image.open(reference) as img:
                image_format = img.format
                ref_width, ref_height = img.size
                img.verify()
        except (ImportError, OSError, ValueError, SyntaxError) as exc:
            raise CloudflareGenerationError("FLUX.2 reference is not a readable image") from exc
        if image_format not in {"PNG", "JPEG"}:
            raise CloudflareGenerationError("FLUX.2 reference must be PNG or JPEG")
        if not 0 < ref_width < 512 or not 0 < ref_height < 512:
            raise CloudflareGenerationError(
                "FLUX.2 reference dimensions must each be smaller than 512"
            )
        mime = "image/png" if image_format == "PNG" else "image/jpeg"
        image_parts.append((f"input_image_{index}", mime, reference.read_bytes()))

    boundary = "asset-forge-" + uuid.uuid4().hex
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.extend([
            f"--{boundary}\r\n".encode("ascii"),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("ascii"),
            value.encode("utf-8"),
            b"\r\n",
        ])

    field("prompt", prompt)
    field("width", str(width))
    field("height", str(height))
    field("seed", str(seed))
    field("guidance", str(guidance))
    for field_name, mime, image_bytes in image_parts:
        parts.extend([
            f"--{boundary}\r\n".encode("ascii"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{field_name}.png"\r\n'
                f"Content-Type: {mime}\r\n\r\n"
            ).encode("ascii"),
            image_bytes,
            b"\r\n",
        ])
    parts.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(parts), "multipart/form-data; boundary=" + boundary


def generate(
    prompt: str,
    output: Path,
    *,
    width: int = 1024,
    height: int = 1024,
    seed: int = 0,
    steps: int = 20,
    reference_path: Path | None = None,
    reference_paths: list[Path] | None = None,
    strength: float = 0.55,
    guidance: float = 7.5,
    negative_prompt: str | None = None,
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

    flux = model == FLUX_KLEIN_MODEL
    width = int(width) if flux else max(256, min(2048, int(width)))
    height = int(height) if flux else max(256, min(2048, int(height)))
    steps = 4 if flux else max(1, min(20, int(steps)))
    references = (
        [Path(path) for path in reference_paths]
        if reference_paths is not None
        else ([Path(reference_path)] if reference_path is not None else [])
    )
    if reference_paths is not None and reference_path is not None and (
        not references or references[0] != Path(reference_path)
    ):
        raise CloudflareGenerationError("Conflicting Cloudflare reference inputs")
    if flux:
        if negative_prompt:
            raise CloudflareGenerationError("FLUX.2 does not accept negative_prompt")
        body, content_type = _flux_multipart_payload(
            str(prompt), width=width, height=height, seed=int(seed),
            guidance=float(guidance), references=references,
        )
    else:
        if len(references) > 1:
            raise CloudflareGenerationError(
                "SDXL does not support multiple visual references"
            )
        payload = {
            "prompt": str(prompt),
            "width": width,
            "height": height,
            "num_steps": steps,
            "guidance": float(guidance),
            "seed": int(seed),
        }
        if negative_prompt:
            payload["negative_prompt"] = str(negative_prompt)
        if references:
            reference = references[0]
            if not reference.is_file() or reference.stat().st_size <= 0:
                raise CloudflareGenerationError(f"reference file missing or empty: {reference}")
            payload["image_b64"] = base64.b64encode(reference.read_bytes()).decode("ascii")
            payload["strength"] = max(0.0, min(1.0, float(strength)))
        body = json.dumps(payload).encode("utf-8")
        content_type = "application/json"

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        + urllib.parse.quote(account, safe="")
        + "/ai/run/"
        + model
    )
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
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
        "reference": bool(references),
        "reference_count": len(references),
    }
