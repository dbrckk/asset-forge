from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from kaggle_backend import (
    _extract_kaggle_diagnostic,
    _run,
    _slug,
    DEFAULT_ACCELERATOR,
)


DEFAULT_MODEL = "stabilityai/TripoSR"
TRIPOSR_REPOSITORY = "https://github.com/VAST-AI-Research/TripoSR.git"
TRIPOSR_COMMIT = "107cefdc244c39106fa830359024f6a2f1c78871"
MAX_REFERENCE_BYTES = 20 * 1024 * 1024
MAX_GLB_BYTES = 100 * 1024 * 1024


class Kaggle3DGenerationError(RuntimeError):
    pass


def status(*, environ=None) -> dict:
    env = os.environ if environ is None else environ
    token = str(env.get("KAGGLE_API_TOKEN") or "").strip()
    username = str(env.get("KAGGLE_USERNAME") or "").strip()
    executable = shutil.which("kaggle")
    ready = bool(token and username and executable)
    return {
        "installed": executable is not None,
        "executable": executable,
        "authenticated": bool(token and username),
        "threeDReady": ready,
        "credentialSource": "environment" if token and username else None,
        "model": DEFAULT_MODEL,
        "accelerator": DEFAULT_ACCELERATOR,
        "license": "MIT",
        "mode": "kaggle-image-to-3d",
        "estimatedVramGb": 6,
    }


def _runner_source() -> str:
    return r'''import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

REFERENCE_B64 = __ASSET_FORGE_REFERENCE_B64__
MC_RESOLUTION = __ASSET_FORGE_MC_RESOLUTION__
TRIPOSR_COMMIT = "__ASSET_FORGE_TRIPOSR_COMMIT__"

work = Path("/kaggle/working")
repo = work / "TripoSR"
reference = work / "reference.png"
output_root = work / "triposr-output"

reference.write_bytes(base64.b64decode(REFERENCE_B64))

subprocess.run(["git", "init", str(repo)], check=True)
subprocess.run(
    ["git", "-C", str(repo), "remote", "add", "origin",
     "https://github.com/VAST-AI-Research/TripoSR.git"],
    check=True,
)
subprocess.run(
    ["git", "-C", str(repo), "fetch", "--depth", "1", "origin", TRIPOSR_COMMIT],
    check=True,
)
subprocess.run(
    ["git", "-C", str(repo), "checkout", "--detach", "FETCH_HEAD"],
    check=True,
)
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "--upgrade", "setuptools"],
    check=True,
)
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "-r", str(repo / "requirements.txt")],
    check=True,
)

try:
    subprocess.run(
        [
            sys.executable,
            str(repo / "run.py"),
            str(reference),
            "--output-dir",
            str(output_root),
            "--model-save-format",
            "glb",
            "--mc-resolution",
            str(MC_RESOLUTION),
        ],
        cwd=str(repo),
        check=True,
    )
except Exception as exc:
    import traceback
    Path("/kaggle/working/error.json").write_text(
        json.dumps({
            "success": False,
            "exceptionType": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    raise

generated = output_root / "0" / "mesh.glb"
if not generated.is_file() or generated.stat().st_size <= 0:
    raise RuntimeError("TripoSR produced no mesh.glb")
raw = generated.read_bytes()
if len(raw) < 12 or raw[:4] != b"glTF":
    raise RuntimeError("TripoSR output is not a GLB")
if len(raw) > 100 * 1024 * 1024:
    raise RuntimeError("TripoSR GLB exceeds 100 MiB")

target = Path("/kaggle/working/asset.glb")
shutil.copyfile(generated, target)
Path("/kaggle/working/result.json").write_text(
    json.dumps({
        "success": True,
        "model": "stabilityai/TripoSR",
        "triposrCommit": TRIPOSR_COMMIT,
        "mcResolution": MC_RESOLUTION,
        "bytes": target.stat().st_size,
        "textured": False,
        "colorMode": "vertex-color",
    }, indent=2) + "\n",
    encoding="utf-8",
)
'''


def _validate_reference(path: Path) -> Path:
    source = Path(path)
    if not source.is_file():
        raise Kaggle3DGenerationError("3D reference image is missing")
    if source.is_symlink():
        raise Kaggle3DGenerationError("3D reference image must not be a symlink")
    size = source.stat().st_size
    if size <= 0:
        raise Kaggle3DGenerationError("3D reference image is empty")
    if size > MAX_REFERENCE_BYTES:
        raise Kaggle3DGenerationError("3D reference image exceeds 20 MiB")
    if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise Kaggle3DGenerationError("3D reference image must be PNG, JPEG, or WebP")
    return source


def generate(
    reference_path: Path,
    output: Path,
    *,
    mc_resolution: int = 256,
    model: str = DEFAULT_MODEL,
    accelerator: str = DEFAULT_ACCELERATOR,
    timeout_seconds: float = 1800.0,
    environ=None,
    runner=subprocess.run,
) -> dict:
    env = os.environ if environ is None else environ
    token = str(env.get("KAGGLE_API_TOKEN") or "").strip()
    username = str(env.get("KAGGLE_USERNAME") or "").strip()
    executable = shutil.which("kaggle")
    if not token or not username:
        raise Kaggle3DGenerationError(
            "KAGGLE_API_TOKEN and KAGGLE_USERNAME are required"
        )
    if not executable:
        raise Kaggle3DGenerationError("kaggle CLI is not installed")
    if model != DEFAULT_MODEL:
        raise Kaggle3DGenerationError(
            f"kaggle TripoSR only supports {DEFAULT_MODEL}"
        )

    source = _validate_reference(reference_path)
    try:
        resolution = int(mc_resolution)
    except (TypeError, ValueError) as exc:
        raise Kaggle3DGenerationError("mc_resolution must be an integer") from exc
    if resolution not in {128, 192, 256, 320, 384}:
        raise Kaggle3DGenerationError(
            "mc_resolution must be one of 128, 192, 256, 320, 384"
        )

    try:
        timeout = float(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise Kaggle3DGenerationError("timeout_seconds must be positive") from exc
    if timeout <= 0:
        raise Kaggle3DGenerationError("timeout_seconds must be positive")

    job_tag = _slug(f"asset-forge-triposr-{int(time.time())}-{os.getpid()}")
    kernel_id = f"{_slug(username)}/{job_tag}"

    with tempfile.TemporaryDirectory(prefix="asset-forge-kaggle-3d-") as td:
        root = Path(td)
        script = _runner_source()
        script = script.replace(
            "__ASSET_FORGE_REFERENCE_B64__",
            repr(base64.b64encode(source.read_bytes()).decode("ascii")),
        )
        script = script.replace(
            "__ASSET_FORGE_MC_RESOLUTION__",
            str(resolution),
        )
        script = script.replace(
            "__ASSET_FORGE_TRIPOSR_COMMIT__",
            TRIPOSR_COMMIT,
        )
        (root / "runner.py").write_text(script, encoding="utf-8")

        metadata = {
            "id": kernel_id,
            "title": job_tag,
            "code_file": "runner.py",
            "language": "python",
            "kernel_type": "script",
            "is_private": True,
            "enable_gpu": True,
            "enable_internet": True,
            "machine_shape": accelerator,
            "dataset_sources": [],
            "competition_sources": [],
            "kernel_sources": [],
            "model_sources": [],
        }
        (root / "kernel-metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            _run(
                [
                    executable,
                    "kernels",
                    "push",
                    "-p",
                    str(root),
                    "--accelerator",
                    accelerator,
                ],
                timeout=min(timeout, 300),
                runner=runner,
            )
        except Exception as exc:
            raise Kaggle3DGenerationError(str(exc)) from exc

        deadline = time.monotonic() + timeout
        terminal_error = None
        last_status = ""
        while time.monotonic() < deadline:
            try:
                status_result = _run(
                    [executable, "kernels", "status", kernel_id],
                    timeout=60,
                    runner=runner,
                )
            except Exception as exc:
                raise Kaggle3DGenerationError(str(exc)) from exc
            body = (
                str(status_result.stdout or "")
                + "\n"
                + str(status_result.stderr or "")
            ).lower()
            last_status = body.strip()
            if any(word in body for word in ("complete", "completed")):
                break
            if any(word in body for word in ("error", "failed", "cancelled")):
                terminal_error = f"Kaggle TripoSR kernel failed: {last_status[:1200]}"
                break
            time.sleep(15)
        else:
            raise Kaggle3DGenerationError("Kaggle TripoSR kernel timed out")

        download_dir = root / "download"
        download_dir.mkdir()
        try:
            _run(
                [
                    executable,
                    "kernels",
                    "output",
                    kernel_id,
                    "-p",
                    str(download_dir),
                    "-o",
                ],
                timeout=180,
                runner=runner,
            )
        except Exception as exc:
            if terminal_error:
                raise Kaggle3DGenerationError(
                    f"{terminal_error}; output retrieval failed: {exc}"
                ) from exc
            raise Kaggle3DGenerationError(str(exc)) from exc

        if terminal_error:
            error_file = download_dir / "error.json"
            if error_file.is_file():
                try:
                    payload = json.loads(error_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    payload = None
                if isinstance(payload, dict):
                    detail = (
                        f"{payload.get('exceptionType') or 'Exception'}: "
                        f"{payload.get('message') or ''}"
                    ).strip()
                    raise Kaggle3DGenerationError(
                        f"{terminal_error}; exact exception: {detail}"
                    )
            diagnostics = []
            for candidate in sorted(download_dir.rglob("*.log")):
                try:
                    detail = _extract_kaggle_diagnostic(candidate)
                except OSError:
                    continue
                if detail:
                    diagnostics.append(detail)
            suffix = diagnostics[-1][-6000:] if diagnostics else "no diagnostic output"
            raise Kaggle3DGenerationError(
                f"{terminal_error}; diagnostics: {suffix}"
            )

        generated = download_dir / "asset.glb"
        if not generated.is_file() or generated.stat().st_size <= 0:
            raise Kaggle3DGenerationError("Kaggle TripoSR produced no asset.glb")
        raw = generated.read_bytes()
        if len(raw) > MAX_GLB_BYTES:
            raise Kaggle3DGenerationError("Kaggle TripoSR GLB exceeds 100 MiB")
        if len(raw) < 12 or raw[:4] != b"glTF":
            raise Kaggle3DGenerationError("Kaggle TripoSR output is not a GLB")

        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generated, target)

        result_path = download_dir / "result.json"
        result = {}
        if result_path.is_file():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result = {}

        try:
            _run(
                [executable, "kernels", "delete", kernel_id, "-y"],
                timeout=60,
                runner=runner,
            )
        except Exception:
            pass

    return {
        "provider": "kaggle-notebooks",
        "kernel": kernel_id,
        "backend": "kaggle-triposr",
        "model": model,
        "accelerator": accelerator,
        "license": "MIT",
        "triposrCommit": TRIPOSR_COMMIT,
        "mcResolution": resolution,
        "sourcePath": str(target),
        "sourceBytes": target.stat().st_size,
        "result": result,
    }
