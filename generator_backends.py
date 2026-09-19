from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable


RASTER_GENERATED_TYPES = {"sprite", "sprite-sheet", "tileset", "pixel-art"}


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
    if asset_type not in RASTER_GENERATED_TYPES:
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
        "Create a production-ready game asset with a transparent background when appropriate.",
        "Do not include captions, watermarks, signatures, UI chrome, or mockup backgrounds.",
    ]
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
    command = [
        executable,
        "gen",
        "image",
        prompt,
        "--output",
        str(Path(output)),
        "--json",
    ]
    if model:
        command.extend(["--model", str(model)])
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
    if asset_type not in RASTER_GENERATED_TYPES:
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
    output = output_dir / "generated-source.png"
    command = pollinations_command(job, output, model=model, executable=executable)
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
        "model": model,
        "assetType": asset_type,
        "sourcePath": str(output),
        "sourceBytes": output.stat().st_size,
        "metadata": metadata,
    }
