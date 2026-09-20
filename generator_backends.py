from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from art_quality import ArtQualityError, evaluate_raster_art
from visual_similarity import compare_against_references


RASTER_GENERATED_TYPES = {"sprite", "sprite-sheet", "tileset", "pixel-art"}
VECTOR_GENERATED_TYPES = {"vector", "svg", "icon", "ui-vector", "logo"}
THREE_D_GENERATED_TYPES = {"mesh", "prop", "environment", "character-3d"}
SUPPORTED_GENERATED_TYPES = RASTER_GENERATED_TYPES | VECTOR_GENERATED_TYPES | THREE_D_GENERATED_TYPES
DEFAULT_VECTOR_MODEL = "recraft/recraft-v4.1-vector"
DEFAULT_REFERENCE_MODEL = "kontext"
DEFAULT_3D_MODEL = "microsoft/trellis-2"
MAX_3D_BYTES = 100 * 1024 * 1024
MAX_METADATA_ITEMS = 64
MAX_METADATA_STRING = 4096
MAX_METADATA_DEPTH = 6
_SENSITIVE_METADATA_KEY = re.compile(
    r"(?:api[-_]?key|token|secret|authorization|password|credential)",
    re.IGNORECASE,
)


def _sanitize_metadata(value, *, depth: int = 0):
    if depth >= MAX_METADATA_DEPTH:
        return "[TRUNCATED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:MAX_METADATA_STRING]
    if isinstance(value, list):
        return [
            _sanitize_metadata(item, depth=depth + 1)
            for item in value[:MAX_METADATA_ITEMS]
        ]
    if isinstance(value, dict):
        cleaned = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_METADATA_ITEMS:
                cleaned["_truncated"] = True
                break
            name = str(key)[:256]
            if _SENSITIVE_METADATA_KEY.search(name):
                cleaned[name] = "[REDACTED]"
            else:
                cleaned[name] = _sanitize_metadata(item, depth=depth + 1)
        return cleaned
    return str(value)[:MAX_METADATA_STRING]


class GenerationError(RuntimeError):
    pass


def generator_backend_status(*, environ=None, home: Path | None = None) -> dict:
    env = os.environ if environ is None else environ
    home_dir = Path.home() if home is None else Path(home)
    polli = shutil.which("polli")
    imagen = shutil.which("imagen")
    credentials = home_dir / ".pollinations" / "credentials.json"
    api_key_available = bool(str(env.get("POLLINATIONS_API_KEY") or "").strip())
    authenticated = api_key_available or credentials.is_file()
    codex_token_available = bool(
        str(
            env.get("CODEX_ACCESS_TOKEN")
            or env.get("CHATGPT_ACCESS_TOKEN")
            or ""
        ).strip()
    )
    return {
        "pollinations": {
            "installed": polli is not None,
            "executable": polli,
            "authenticated": authenticated,
            "rasterVectorReady": polli is not None and authenticated,
            "threeDReady": polli is not None and api_key_available,
            "credentialSource": (
                "environment"
                if api_key_available
                else "credential-store"
                if credentials.is_file()
                else None
            ),
        },
        "imagenCodex": {
            "installed": imagen is not None,
            "executable": imagen,
            "authenticated": codex_token_available,
            "rasterReady": imagen is not None and codex_token_available,
            "vectorSvgReady": False,
            "threeDReady": False,
            "credentialSource": "environment" if codex_token_available else None,
        },
    }


def _sprite_sheet_geometry(job: dict) -> tuple[int, int, int, int] | None:
    asset_type = str(job.get("assetType") or "")
    if asset_type not in RASTER_GENERATED_TYPES:
        return None
    manifest = job.get("manifest")
    if not isinstance(manifest, dict):
        return None
    constraints = manifest.get("constraints")
    if not isinstance(constraints, dict):
        return None
    frame_width = constraints.get("frameWidth")
    frame_height = constraints.get("frameHeight")
    frame_count = constraints.get("expectedFrames")
    if not (
        isinstance(frame_width, int)
        and frame_width > 0
        and isinstance(frame_height, int)
        and frame_height > 0
        and isinstance(frame_count, int)
        and frame_count > 0
    ):
        return None

    columns = max(1, math.ceil(math.sqrt(frame_count)))
    while columns < frame_count and frame_count % columns:
        columns += 1
    rows = frame_count // columns
    return (
        frame_width * columns,
        frame_height * rows,
        columns,
        rows,
    )


def _generation_dimensions(job: dict) -> tuple[int, int] | None:
    geometry = _sprite_sheet_geometry(job)
    if geometry is None:
        return None
    width, height, _, _ = geometry
    shortest = max(1, min(width, height))
    longest = max(width, height)
    desired_scale = max(1.0, 512.0 / shortest)
    scale = min(desired_scale, 2048.0 / max(1, longest))
    request_width = min(2048, max(64, int(round(width * scale))))
    request_height = min(2048, max(64, int(round(height * scale))))
    return request_width, request_height


def _ensure_transparency(
    path: Path,
    job: dict,
    *,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    timeout_seconds: float = 180.0,
) -> dict | None:
    manifest = job.get("manifest")
    constraints = manifest.get("constraints") if isinstance(manifest, dict) else None
    if not isinstance(constraints, dict) or constraints.get("requiresAlpha") is not True:
        return None

    try:
        from PIL import Image
    except ImportError as exc:
        raise GenerationError(
            "Pillow is required to inspect generated raster transparency"
        ) from exc

    try:
        with Image.open(path) as image:
            alpha = image.convert("RGBA").getchannel("A")
            minimum, maximum = alpha.getextrema()
    except (OSError, ValueError) as exc:
        raise GenerationError(
            f"generated raster transparency inspection failed: {type(exc).__name__}"
        ) from exc

    if minimum < 255:
        return {
            "required": True,
            "changed": False,
            "backend": None,
            "alphaRange": [minimum, maximum],
        }

    executable = shutil.which("rembg")
    if not executable:
        raise GenerationError(
            "generated raster requires transparency but rembg is unavailable"
        )

    temporary = path.with_name(path.stem + "-transparent.png")
    completed = runner(
        [executable, "i", str(path), str(temporary)],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        stderr = str(completed.stderr or "").strip()
        raise GenerationError(
            "rembg background removal failed"
            + (f": {stderr[:1000]}" if stderr else "")
        )
    if not temporary.is_file() or temporary.stat().st_size <= 0:
        raise GenerationError("rembg did not produce an output file")

    try:
        with Image.open(temporary) as image:
            alpha = image.convert("RGBA").getchannel("A")
            new_minimum, new_maximum = alpha.getextrema()
    except (OSError, ValueError) as exc:
        raise GenerationError(
            f"rembg output inspection failed: {type(exc).__name__}"
        ) from exc
    if new_minimum >= 255:
        temporary.unlink(missing_ok=True)
        raise GenerationError("rembg output is still fully opaque")

    temporary.replace(path)
    return {
        "required": True,
        "changed": True,
        "backend": "rembg",
        "alphaRange": [new_minimum, new_maximum],
    }


def _normalize_raster_geometry(raw: Path, output: Path, job: dict) -> dict | None:
    geometry = _sprite_sheet_geometry(job)
    if geometry is None:
        if raw.resolve() != output.resolve():
            shutil.copyfile(raw, output)
        return None

    target_width, target_height, columns, rows = geometry
    try:
        from PIL import Image
    except ImportError as exc:
        raise GenerationError(
            "Pillow is required to normalize generated sprite-sheet dimensions"
        ) from exc

    constraints = job.get("manifest", {}).get("constraints", {})
    pixel_art = isinstance(constraints, dict) and constraints.get("pixelArt") is True
    resampling = Image.Resampling.NEAREST if pixel_art else Image.Resampling.LANCZOS
    try:
        with Image.open(raw) as image:
            image.load()
            original = image.size
            normalized = image.convert("RGBA").resize(
                (target_width, target_height),
                resample=resampling,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            normalized.save(output, format="PNG", optimize=True)
    except (OSError, ValueError) as exc:
        raise GenerationError(
            f"generated raster normalization failed: {type(exc).__name__}"
        ) from exc

    return {
        "originalWidth": original[0],
        "originalHeight": original[1],
        "width": target_width,
        "height": target_height,
        "columns": columns,
        "rows": rows,
        "pixelArt": pixel_art,
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
    geometry = _sprite_sheet_geometry(job)
    if geometry is not None:
        _, _, columns, rows = geometry
        details.append(
            f"Arrange the frames on an exact {columns}-column by {rows}-row regular grid with no gutters."
        )
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
    reference_urls: list[str] | None = None,
) -> list[str]:
    prompt = build_generation_prompt(job)
    if reference_urls:
        prompt += (
            " Use the provided reference image as a strict visual identity anchor. "
            "Preserve the same subject identity, silhouette language, proportions, "
            "core palette, materials, and art direction while applying only the "
            "requested pose, animation, expression, or variant changes."
        )
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
    for reference_url in reference_urls or []:
        command.extend(["--image", reference_url])
    dimensions = _generation_dimensions(job)
    if dimensions is not None:
        command.extend(
            ["--width", str(dimensions[0]), "--height", str(dimensions[1])]
        )
    return command


def select_generation_backend(job: dict, requested: str = "auto") -> str:
    if requested in {"pollinations", "imagen-codex"}:
        return requested
    if requested != "auto":
        raise GenerationError(f"unsupported generator backend: {requested}")

    asset_type = str(job.get("assetType") or "")
    status = generator_backend_status()
    pollinations = status.get("pollinations", {})
    imagen_codex = status.get("imagenCodex", {})

    if asset_type in RASTER_GENERATED_TYPES:
        if pollinations.get("rasterVectorReady") is True:
            return "pollinations"
        if imagen_codex.get("rasterReady") is True:
            return "imagen-codex"
        raise GenerationError("no authenticated raster generation backend is ready")

    if asset_type in VECTOR_GENERATED_TYPES:
        if pollinations.get("rasterVectorReady") is True:
            return "pollinations"
        raise GenerationError(
            "no authenticated SVG generation backend is ready; imagen-codex is raster-only"
        )

    if asset_type in THREE_D_GENERATED_TYPES:
        if pollinations.get("threeDReady") is True:
            return "pollinations"
        raise GenerationError(
            "no authenticated 3D generation backend is ready; POLLINATIONS_API_KEY is required"
        )

    raise GenerationError(f"unsupported generated asset type: {asset_type or '<missing>'}")


def imagen_codex_command(
    job: dict,
    output_dir: Path,
    *,
    model: str | None = None,
    executable: str = "imagen",
    reference_paths: list[Path] | None = None,
    extra_guidance: str | None = None,
) -> list[str]:
    asset_type = str(job.get("assetType") or "")
    if asset_type not in RASTER_GENERATED_TYPES:
        raise GenerationError(
            "imagen-codex currently supports raster generated assets only"
        )
    prompt = build_generation_prompt(job)
    if reference_paths:
        prompt += (
            " Use the provided reference image as a strict visual identity anchor. "
            "Preserve the same subject identity, silhouette language, proportions, core palette, "
            "materials, camera language, and art direction while applying only the requested variant."
        )
    if extra_guidance:
        prompt += " " + str(extra_guidance).strip()
    constraints = job.get("manifest", {}).get("constraints", {})
    command = [
        executable,
        "-m",
        str(model or "codex-2"),
        "-o",
        "generated-source",
        "-d",
        str(Path(output_dir)),
        "--json",
    ]
    if isinstance(constraints, dict) and constraints.get("requiresAlpha") is True:
        command.append("-t")
    for reference in reference_paths or []:
        command.extend(["--input-ref", str(Path(reference))])
    command.append(prompt)
    return command


def _imagen_output_path(output_dir: Path, stdout: str) -> tuple[Path, dict | None]:
    metadata = None
    try:
        parsed = json.loads(stdout or "")
        if isinstance(parsed, dict):
            metadata = _sanitize_metadata(parsed)
            files = parsed.get("files")
            if isinstance(files, list) and files:
                first = files[0]
                if isinstance(first, str) and first.strip():
                    candidate = Path(first)
                    if not candidate.is_absolute():
                        candidate = Path(output_dir) / candidate
                    resolved_root = Path(output_dir).resolve()
                    resolved_candidate = candidate.resolve()
                    if (
                        resolved_candidate == resolved_root
                        or resolved_root not in resolved_candidate.parents
                    ):
                        raise GenerationError(
                            "imagen output path escapes output directory"
                        )
                    if resolved_candidate.is_file():
                        return resolved_candidate, metadata
    except json.JSONDecodeError:
        metadata = None

    fallback = Path(output_dir) / "generated-source.png"
    if fallback.is_file():
        return fallback, metadata
    matches = sorted(Path(output_dir).glob("generated-source*.png"))
    if matches:
        return matches[0], metadata
    raise GenerationError("imagen-codex did not produce a PNG output")


def execute_generated_asset(
    job: dict,
    output_dir: Path,
    *,
    backend: str = "auto",
    model: str | None = None,
    reference_paths: list[Path] | None = None,
    timeout_seconds: float = 180.0,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    raster_normalizer: Callable[[Path, Path, dict], dict | None] = _normalize_raster_geometry,
    transparency_processor: Callable[..., dict | None] = _ensure_transparency,
    similarity_evaluator: Callable[[Path, list[Path]], dict] = compare_against_references,
    technical_quality_evaluator: Callable[[Path, dict], dict] = evaluate_raster_art,
) -> dict:
    if job.get("requiresGenerator") is not True:
        raise GenerationError("production job does not require a generator")
    backend = select_generation_backend(job, backend)
    asset_type = str(job.get("assetType") or "")
    if asset_type not in SUPPORTED_GENERATED_TYPES:
        raise GenerationError(f"unsupported generated asset type: {asset_type or '<missing>'}")

    executable_name = "polli" if backend == "pollinations" else "imagen"
    executable = shutil.which(executable_name)
    if not executable:
        if backend == "pollinations":
            raise GenerationError("polli executable not found; install @pollinations/cli")
        raise GenerationError("imagen executable not found")

    try:
        timeout = float(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise GenerationError("timeout_seconds must be positive") from exc
    if timeout <= 0:
        raise GenerationError("timeout_seconds must be positive")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    vector = asset_type in VECTOR_GENERATED_TYPES
    constrained_raster = (
        asset_type in RASTER_GENERATED_TYPES
        and _sprite_sheet_geometry(job) is not None
    )
    output = output_dir / (
        "generated-source.svg"
        if vector
        else "generated-raw.png"
        if constrained_raster
        else "generated-source.png"
    )
    if backend == "imagen-codex" and vector:
        raise GenerationError(
            "imagen-codex does not emit editable SVG; use a raster target"
        )

    references = [Path(path) for path in (reference_paths or [])]
    if references and asset_type not in RASTER_GENERATED_TYPES:
        raise GenerationError("visual references are currently supported for raster generation only")
    if references and backend not in {"pollinations", "imagen-codex"}:
        raise GenerationError("selected backend does not support visual references")
    if len(references) > 4:
        raise GenerationError("at most 4 visual references are supported")
    for reference in references:
        if not reference.is_file() or reference.stat().st_size <= 0:
            raise GenerationError(f"visual reference file missing or empty: {reference}")

    effective_model = model or (
        DEFAULT_VECTOR_MODEL if backend == "pollinations" and vector else
        DEFAULT_REFERENCE_MODEL if backend == "pollinations" and references else
        "codex-2" if backend == "imagen-codex" else
        None
    )
    reference_urls = []
    if references and backend == "pollinations":
        for reference in references:
            reference_urls.append(
                _upload_reference_image(
                    reference,
                    executable=executable,
                    timeout_seconds=min(timeout, 120.0),
                    runner=runner,
                )
            )

    if backend == "pollinations":
        command = pollinations_command(
            job,
            output,
            model=effective_model,
            executable=executable,
            reference_urls=reference_urls,
        )
    else:
        command = imagen_codex_command(
            job,
            output_dir,
            model=effective_model,
            executable=executable,
            reference_paths=references,
        )

    constraints = job.get("manifest", {}).get("constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}
    similarity_threshold = constraints.get("visualSimilarityMin", 0.42)
    similarity_retries = constraints.get("visualSimilarityRetries", 2)
    technical_threshold = constraints.get("technicalQualityMin")
    technical_retries = constraints.get(
        "technicalQualityRetries",
        similarity_retries,
    )
    try:
        similarity_threshold = float(similarity_threshold)
        similarity_retries = int(similarity_retries)
        technical_retries = int(technical_retries)
        if technical_threshold is not None:
            technical_threshold = float(technical_threshold)
    except (TypeError, ValueError) as exc:
        raise GenerationError("visual and technical quality controls must be numeric") from exc
    if not 0.0 <= similarity_threshold <= 1.0:
        raise GenerationError("visualSimilarityMin must be between 0 and 1")
    if not 0 <= similarity_retries <= 4:
        raise GenerationError("visualSimilarityRetries must be between 0 and 4")
    if technical_threshold is not None and not 0.0 <= technical_threshold <= 1.0:
        raise GenerationError("technicalQualityMin must be between 0 and 1")
    if not 0 <= technical_retries <= 4:
        raise GenerationError("technicalQualityRetries must be between 0 and 4")

    retry_budget = max(
        similarity_retries if references else 0,
        technical_retries
        if technical_threshold is not None and asset_type in RASTER_GENERATED_TYPES
        else 0,
    )
    similarity_history = []
    technical_quality_history = []
    metadata = None
    transparency = None
    normalization = None
    final_output = output
    stdout = ""

    previous_similarity_failed = False
    previous_technical_failed = False
    for attempt in range(retry_budget + 1):
        attempt_command = list(command)
        if attempt > 0:
            retry_guidance = []
            if previous_similarity_failed:
                retry_guidance.append(
                    "The previous generated variant drifted too far from the reference. "
                    "Match the reference identity and art direction more closely."
                )
            if previous_technical_failed:
                retry_guidance.append(
                    "The previous variant failed technical game-art quality. "
                    "Keep all visible art away from image borders, preserve transparent padding, "
                    "use a clean readable silhouette, stable frame occupancy, and stronger local contrast."
                )
            if retry_guidance:
                guidance = " ".join(retry_guidance)
                if backend == "pollinations":
                    attempt_command[3] = attempt_command[3] + " " + guidance
                else:
                    attempt_command[-1] = attempt_command[-1] + " " + guidance
        completed = runner(
            attempt_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if completed.returncode != 0:
            stderr = str(completed.stderr or "").strip()
            raise GenerationError(
                f"{backend} generation failed"
                + (f": {stderr[:1000]}" if stderr else "")
            )

        stdout = str(completed.stdout or "").strip()
        metadata = None
        current_output = output
        if backend == "imagen-codex":
            current_output, metadata = _imagen_output_path(output_dir, stdout)
        elif not current_output.is_file() or current_output.stat().st_size <= 0:
            raise GenerationError("pollinations generation did not produce an output file")

        transparency = None
        if asset_type in RASTER_GENERATED_TYPES:
            transparency = transparency_processor(
                current_output,
                job,
                timeout_seconds=min(timeout, 180.0),
            )

        normalization = None
        final_output = current_output
        if constrained_raster:
            final_output = output_dir / "generated-source.png"
            normalization = raster_normalizer(current_output, final_output, job)
            if not final_output.is_file() or final_output.stat().st_size <= 0:
                raise GenerationError("raster normalization did not produce an output file")

        if backend == "pollinations":
            metadata = None
            if stdout:
                try:
                    parsed = json.loads(stdout)
                    if isinstance(parsed, dict):
                        metadata = _sanitize_metadata(parsed)
                except json.JSONDecodeError:
                    metadata = None

        similarity_passed = True
        previous_similarity_failed = False
        if references:
            similarity = similarity_evaluator(final_output, references)
            score = similarity.get("score") if isinstance(similarity, dict) else None
            if not isinstance(score, (int, float)):
                raise GenerationError("visual similarity evaluator returned no numeric score")
            similarity_passed = float(score) >= similarity_threshold
            previous_similarity_failed = not similarity_passed
            similarity_history.append({
                "attempt": attempt + 1,
                "score": round(float(score), 6),
                "threshold": similarity_threshold,
                "passed": similarity_passed,
                "bestReference": similarity.get("bestReference"),
                "comparisons": similarity.get("comparisons", []),
            })

        technical_passed = True
        previous_technical_failed = False
        if (
            technical_threshold is not None
            and asset_type in RASTER_GENERATED_TYPES
        ):
            try:
                technical = technical_quality_evaluator(
                    final_output,
                    job.get("manifest", {}),
                )
            except (ArtQualityError, OSError, ValueError) as exc:
                raise GenerationError(
                    f"technical art quality evaluation failed: {exc}"
                ) from exc
            technical_score = (
                technical.get("score")
                if isinstance(technical, dict)
                else None
            )
            if not isinstance(technical_score, (int, float)):
                raise GenerationError(
                    "technical art quality evaluator returned no numeric score"
                )
            technical_passed = (
                float(technical_score) >= technical_threshold
                and not list(technical.get("errors") or [])
            )
            previous_technical_failed = not technical_passed
            technical_quality_history.append({
                "attempt": attempt + 1,
                "score": round(float(technical_score), 6),
                "threshold": technical_threshold,
                "passed": technical_passed,
                "metrics": technical.get("metrics", {}),
                "errors": list(technical.get("errors") or []),
                "warnings": list(technical.get("warnings") or []),
            })

        if similarity_passed and technical_passed:
            break

        can_retry_similarity = (
            previous_similarity_failed and attempt < similarity_retries
        )
        can_retry_technical = (
            previous_technical_failed and attempt < technical_retries
        )
        if can_retry_similarity or can_retry_technical:
            continue

        failures = []
        if previous_similarity_failed and similarity_history:
            failures.append(
                "visual consistency score "
                f"{similarity_history[-1]['score']:.3f} is below required "
                f"{similarity_threshold:.3f}"
            )
        if previous_technical_failed and technical_quality_history:
            failures.append(
                "technical art quality score "
                f"{technical_quality_history[-1]['score']:.3f} is below required "
                f"{technical_threshold:.3f}"
            )
        raise GenerationError(
            "; ".join(failures)
            + f" after {attempt + 1} attempts"
        )

    return {
        "success": True,
        "backend": backend,
        "model": effective_model,
        "assetType": asset_type,
        "sourcePath": str(final_output),
        "sourceBytes": final_output.stat().st_size,
        "normalization": normalization,
        "transparency": transparency,
        "metadata": metadata,
        "references": [
            {
                "path": str(path),
                "url": (
                    reference_urls[index]
                    if index < len(reference_urls)
                    else None
                ),
                "transport": (
                    "uploaded-url"
                    if backend == "pollinations"
                    else "local-input-ref"
                ),
            }
            for index, path in enumerate(references)
        ],
        "visualSimilarity": {
            "threshold": similarity_threshold if references else None,
            "attempts": similarity_history,
            "passed": (
                similarity_history[-1]["passed"]
                if similarity_history
                else None
            ),
        },
        "technicalQuality": {
            "threshold": technical_threshold,
            "attempts": technical_quality_history,
            "passed": (
                technical_quality_history[-1]["passed"]
                if technical_quality_history
                else None
            ),
        },
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
        "referenceUpload": {"temporaryPublic": True},
        "sourcePath": str(output),
        "sourceBytes": len(raw),
    }
