from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable


RASTER_GENERATED_TYPES = {"sprite", "sprite-sheet", "tileset", "pixel-art"}
VECTOR_GENERATED_TYPES = {"vector", "svg", "icon", "ui-vector", "logo"}
THREE_D_GENERATED_TYPES = {"mesh", "prop", "environment", "character-3d"}
SUPPORTED_GENERATED_TYPES = RASTER_GENERATED_TYPES | VECTOR_GENERATED_TYPES | THREE_D_GENERATED_TYPES
DEFAULT_VECTOR_MODEL = "recraft/recraft-v4.1-vector"
DEFAULT_3D_MODEL = "microsoft/trellis-2"
MAX_3D_BYTES = 100 * 1024 * 1024


class GenerationError(RuntimeError):
    pass


def generator_backend_status(*, environ=None, home: Path | None = None) -> dict:
    env = os.environ if environ is None else environ
    home_dir = Path.home() if home is None else Path(home)
    polli = shutil.which("polli")
    credentials = home_dir / ".pollinations" / "credentials.json"
    authenticated = bool(str(env.get("POLLINATIONS_API_KEY") or "").strip()) or credentials.is_file()
    return {
        "pollinations": {
            "installed": polli is not None,
            "executable": polli,
            "authenticated": authenticated,
            "credentialSource": (
                "environment"
                if bool(str(env.get("POLLINATIONS_API_KEY") or "").strip())
                else "credential-store"
                if credentials.is_file()
                else None
            ),
        }
    }


def build_generation_prompt(job: dict) -> str:
    instruction = str(job.get("instruction") or "").strip()
    asset_type = str(job.get("assetType") or "").strip()
    if not instruction:
        raise GenerationError("production job instruction missing")
    if asset_type not in SUPPORTED_GENERATED_TYPES:
        raise GenerationError(f"unsupported generated asset type: {asset_type or '<missing>'}")

    manifest = job.get("manifest")
    if not isinstance(manifest, dict):
        raise GenerationError("production job manifest missing")
    constraints = manifest.get("constraints")
    if not isinstance(constraints, dict):
        constraints = {}

    details = [
        instruction,
        f"Asset type: {asset_type}.",
        "Create a production-ready project asset.",
        "Do not include captions, watermarks, signatures, UI chrome, or mockup backgrounds unless explicitly requested.",
    ]
    if asset_type in VECTOR_GENERATED_TYPES:
        details.append(
            "Return clean editable vector artwork with a valid SVG viewBox, compact paths, and no embedded external resources."
        )
    elif asset_type in THREE_D_GENERATED_TYPES:
        details.append(
            "Create one clearly isolated subject suitable as an image-to-3D reference, shown fully in frame from a useful three-quarter view, with simple lighting and a clean neutral background."
        )
    else:
        details.append("Use a transparent background when appropriate.")
    if constraints.get("pixelArt") is True:
        details.append("Use crisp pixel art with no anti-aliased scaling and nearest-neighbour-friendly edges.")
    fw = constraints.get("frameWidth")
    fh = constraints.get("frameHeight")
    frames = constraints.get("expectedFrames")
    if isinstance(fw, int) and isinstance(fh, int):
        details.append(f"Each animation frame must be exactly {fw}x{fh} pixels.")
    if isinstance(frames, int):
        details.append(f"The sprite sheet must contain exactly {frames} frames.")
    if isinstance(fw, int) and isinstance(fh, int) and isinstance(frames, int):
        details.append("Arrange frames on a clean regular grid with no gutters unless the request says otherwise.")
    prompt = " ".join(details)
    if len(prompt) > 16000:
        raise GenerationError("generation prompt exceeds 16000 characters")
    return prompt


def pollinations_command(
    job: dict,
    output: Path,
    *,
    model: str | None = None,
    executable: str = "polli",
) -> list[str]:
    prompt = build_generation_prompt(job)
    asset_type = str(job.get("assetType") or "")
    effective_model = model
    if effective_model is None and asset_type in VECTOR_GENERATED_TYPES:
        effective_model = DEFAULT_VECTOR_MODEL
    command = [
        executable,
        "gen",
        "image",
        prompt,
        "--output",
        str(Path(output)),
        "--json",
    ]
    if effective_model:
        command.extend(["--model", str(effective_model)])
    return command


def execute_generated_asset(
    job: dict,
    output_dir: Path,
    *,
    backend: str = "pollinations",
    model: str | None = None,
    timeout_seconds: float = 180.0,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict:
    if job.get("requiresGenerator") is not True:
        raise GenerationError("production job does not require a generator")
    if backend != "pollinations":
        raise GenerationError(f"unsupported generator backend: {backend}")
    asset_type = str(job.get("assetType") or "")
    if asset_type not in SUPPORTED_GENERATED_TYPES:
        raise GenerationError(f"unsupported generated asset type: {asset_type or '<missing>'}")

    executable = shutil.which("polli")
    if not executable:
        raise GenerationError("polli executable not found; install @pollinations/cli")

    try:
        timeout = float(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise GenerationError("timeout_seconds must be positive") from exc
    if timeout <= 0:
        raise GenerationError("timeout_seconds must be positive")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    vector = asset_type in VECTOR_GENERATED_TYPES
    output = output_dir / ("generated-source.svg" if vector else "generated-source.png")
    effective_model = model or (DEFAULT_VECTOR_MODEL if vector else None)
    command = pollinations_command(job, output, model=effective_model, executable=executable)
    completed = runner(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        stderr = str(completed.stderr or "").strip()
        raise GenerationError(
            "pollinations generation failed"
            + (f": {stderr[:1000]}" if stderr else "")
        )
    if not output.is_file() or output.stat().st_size <= 0:
        raise GenerationError("pollinations generation did not produce an output file")

    stdout = str(completed.stdout or "").strip()
    metadata = None
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                metadata = parsed
        except json.JSONDecodeError:
            metadata = None

    return {
        "success": True,
        "backend": backend,
        "model": effective_model,
        "assetType": asset_type,
        "sourcePath": str(output),
        "sourceBytes": output.stat().st_size,
        "metadata": metadata,
    }



class _NoCredentialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GenerationError("credential-bearing 3D redirects are refused")


def _default_3d_opener(request, timeout):
    return urllib.request.build_opener(_NoCredentialRedirect()).open(
        request,
        timeout=timeout,
    )


def _upload_reference_image(
    path: Path,
    *,
    executable: str,
    timeout_seconds: float,
    runner: Callable[..., subprocess.CompletedProcess],
) -> str:
    completed = runner(
        [executable, "upload", str(Path(path)), "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        stderr = str(completed.stderr or "").strip()
        raise GenerationError(
            "pollinations reference upload failed"
            + (f": {stderr[:1000]}" if stderr else "")
        )
    try:
        payload = json.loads(str(completed.stdout or ""))
    except json.JSONDecodeError as exc:
        raise GenerationError("pollinations upload returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise GenerationError("pollinations upload response must be an object")
    url = payload.get("url")
    if not isinstance(url, str) or not url.startswith("https://media.pollinations.ai/"):
        raise GenerationError("pollinations upload response missing trusted media URL")
    return url


def execute_generated_3d_asset(
    job: dict,
    output_dir: Path,
    *,
    model: str = DEFAULT_3D_MODEL,
    resolution: str = "low",
    timeout_seconds: float = 600.0,
    environ=None,
    generator: Callable = execute_generated_asset,
    upload_runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    opener: Callable = _default_3d_opener,
) -> dict:
    if job.get("requiresGenerator") is not True:
        raise GenerationError("production job does not require a generator")
    asset_type = str(job.get("assetType") or "")
    if asset_type not in THREE_D_GENERATED_TYPES:
        raise GenerationError(
            f"unsupported generated 3D asset type: {asset_type or '<missing>'}"
        )
    if model != DEFAULT_3D_MODEL:
        raise GenerationError(
            "only microsoft/trellis-2 is enabled by default for free-first 3D production"
        )
    if resolution not in {"low", "medium", "high"}:
        raise GenerationError("3D resolution must be low, medium, or high")

    env = os.environ if environ is None else environ
    api_key = str(env.get("POLLINATIONS_API_KEY") or "").strip()
    if not api_key:
        raise GenerationError(
            "POLLINATIONS_API_KEY is required for server-side 3D generation"
        )

    executable = shutil.which("polli")
    if not executable:
        raise GenerationError("polli executable not found; install @pollinations/cli")

    try:
        timeout = float(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise GenerationError("timeout_seconds must be positive") from exc
    if timeout <= 0:
        raise GenerationError("timeout_seconds must be positive")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    reference_dir = out / "reference"
    reference = generator(
        job,
        reference_dir,
        backend="pollinations",
        model=None,
        timeout_seconds=min(timeout, 180.0),
    )
    reference_path = Path(str(reference.get("sourcePath") or ""))
    if not reference_path.is_file():
        raise GenerationError("3D reference generation did not produce an image")

    image_url = _upload_reference_image(
        reference_path,
        executable=executable,
        timeout_seconds=min(timeout, 120.0),
        runner=upload_runner,
    )

    endpoint = "https://gen.pollinations.ai/3d/no_prompt_for_trellis_needed"
    body = json.dumps(
        {
            "model": model,
            "image": image_url,
            "resolution": resolution,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "model/gltf-binary,application/octet-stream",
        },
    )
    try:
        with opener(request, timeout) as response:
            status = int(getattr(response, "status", 200))
            if status != 200:
                raise GenerationError(f"Pollinations 3D returned HTTP {status}")
            raw = response.read(MAX_3D_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise GenerationError(
            f"Pollinations 3D returned HTTP {exc.code}"
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GenerationError(
            f"Pollinations 3D unavailable: {type(exc).__name__}"
        ) from None

    if len(raw) > MAX_3D_BYTES:
        raise GenerationError("generated GLB exceeds 100MB safety limit")
    if len(raw) < 12 or raw[:4] != b"glTF":
        raise GenerationError("Pollinations 3D response is not a GLB")

    output = out / "generated-source.glb"
    output.write_bytes(raw)
    return {
        "success": True,
        "backend": "pollinations",
        "model": model,
        "resolution": resolution,
        "assetType": asset_type,
        "referencePath": str(reference_path),
        "referenceUrl": image_url,
        "sourcePath": str(output),
        "sourceBytes": len(raw),
    }
