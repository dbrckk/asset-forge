from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


DEFAULT_MODEL = "Qwen/Qwen-Image-2.1"
DEFAULT_ACCELERATOR = "NvidiaTeslaT4"


class KaggleGenerationError(RuntimeError):
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
        "rasterReady": ready,
        "vectorSvgReady": False,
        "threeDReady": False,
        "credentialSource": "environment" if token and username else None,
        "model": DEFAULT_MODEL,
        "accelerator": DEFAULT_ACCELERATOR,
    }


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    return cleaned[:50] or "asset"


def _runner_source() -> str:
    template = r'''import base64
import json
import subprocess
import sys
from pathlib import Path

# Kaggle images can ship an older torchao that is incompatible with the
# current Diffusers import graph (missing FqnToConfig). Qwen-Image does not
# require torchao for this fp16/offload path, so remove the stale optional
# package before importing Diffusers.
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-q", "-y", "torchao"], check=False)
subprocess.run([
    sys.executable, "-m", "pip", "install", "-q", "-U",
    "transformers>=5.17", "accelerate", "pillow",
    "git+https://github.com/huggingface/diffusers",
], check=True)

import torch
from PIL import Image
from diffusers import QwenImage21Pipeline

def _input_file(name):
    candidates = [
        Path("/kaggle/working") / name,
        Path("/kaggle/src") / name,
        Path(__file__).resolve().parent / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{name} not found in Kaggle working/source directories")

job = __ASSET_FORGE_JOB__
model = job.get("model") or "Qwen/Qwen-Image-2.1"
pipe = QwenImage21Pipeline.from_pretrained(model, torch_dtype=torch.float16)
pipe.enable_model_cpu_offload()

kwargs = {
    "prompt": job["prompt"],
    "width": int(job.get("width") or 1024),
    "height": int(job.get("height") or 1024),
    "num_inference_steps": int(job.get("steps") or 20),
    "generator": torch.Generator(device="cuda").manual_seed(int(job.get("seed") or 0)),
}
reference_b64 = __ASSET_FORGE_REFERENCE_B64__
if reference_b64:
    import io
    kwargs["image"] = Image.open(io.BytesIO(base64.b64decode(reference_b64))).convert("RGBA")

image = pipe(**kwargs).images[0]
output = Path("/kaggle/working/asset.png")
image.save(output)
Path("/kaggle/working/result.json").write_text(json.dumps({
    "success": True,
    "model": model,
    "width": image.width,
    "height": image.height,
    "seed": int(job.get("seed") or 0),
}, indent=2) + "\n")
'''
    return template


def _extract_kaggle_diagnostic(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return ""

    stderr_parts: list[str] = []
    fallback_parts: list[str] = []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None

    records = parsed if isinstance(parsed, list) else None
    if records is None:
        records = []
        for line in raw.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                fallback_parts.append(line)
                continue
            records.append(record)

    for record in records:
        if not isinstance(record, dict):
            continue
        data = str(record.get("data") or "")
        if not data:
            continue
        stream = str(record.get("stream_name") or "").lower()
        if stream == "stderr":
            stderr_parts.append(data)
        else:
            fallback_parts.append(data)

    preferred = "".join(stderr_parts).strip() or "".join(fallback_parts).strip() or raw
    markers = (
        "Traceback (most recent call last):",
        "RuntimeError:",
        "ImportError:",
        "ModuleNotFoundError:",
        "ValueError:",
        "TypeError:",
        "FileNotFoundError:",
        "CUDA out of memory",
        "OutOfMemoryError",
        "Killed",
    )
    positions = [preferred.rfind(marker) for marker in markers if marker in preferred]
    positions = [pos for pos in positions if pos >= 0]
    if positions:
        preferred = preferred[min(positions):]
    return preferred[-16000:]


def _run(command: list[str], *, timeout: float, runner=subprocess.run) -> subprocess.CompletedProcess:
    completed = runner(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        stderr = str(completed.stderr or "").strip()
        stdout = str(completed.stdout or "").strip()
        detail = stderr or stdout
        raise KaggleGenerationError(
            f"Kaggle command failed: {' '.join(command[:3])}"
            + (f": {detail[:1200]}" if detail else "")
        )
    return completed


def generate(
    prompt: str,
    output: Path,
    *,
    width: int = 1024,
    height: int = 1024,
    seed: int = 0,
    steps: int = 20,
    reference_path: Path | None = None,
    model: str = DEFAULT_MODEL,
    accelerator: str = DEFAULT_ACCELERATOR,
    timeout_seconds: float = 3600.0,
    environ=None,
    runner=subprocess.run,
) -> dict:
    env = os.environ if environ is None else environ
    token = str(env.get("KAGGLE_API_TOKEN") or "").strip()
    username = str(env.get("KAGGLE_USERNAME") or "").strip()
    executable = shutil.which("kaggle")
    if not token or not username:
        raise KaggleGenerationError("KAGGLE_API_TOKEN and KAGGLE_USERNAME are required")
    if not executable:
        raise KaggleGenerationError("kaggle CLI is not installed")
    if not str(prompt or "").strip():
        raise KaggleGenerationError("prompt is required")

    width = max(256, min(2048, int(width)))
    height = max(256, min(2048, int(height)))
    steps = max(1, min(40, int(steps)))
    job_tag = _slug(f"asset-forge-qwen-{int(time.time())}-{os.getpid()}")
    kernel_id = f"{_slug(username)}/{job_tag}"

    with tempfile.TemporaryDirectory(prefix="asset-forge-kaggle-") as td:
        root = Path(td)
        job_payload = {
            "prompt": str(prompt),
            "width": width,
            "height": height,
            "seed": int(seed),
            "steps": steps,
            "model": model,
        }
        reference_b64 = ""
        if reference_path is not None:
            source = Path(reference_path)
            if not source.is_file() or source.stat().st_size <= 0:
                raise KaggleGenerationError(f"reference file missing or empty: {source}")
            import base64
            reference_b64 = base64.b64encode(source.read_bytes()).decode("ascii")
        runner_source = _runner_source()
        runner_source = runner_source.replace("__ASSET_FORGE_JOB__", repr(job_payload))
        runner_source = runner_source.replace("__ASSET_FORGE_REFERENCE_B64__", repr(reference_b64))
        (root / "runner.py").write_text(runner_source, encoding="utf-8")

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

        _run(
            [executable, "kernels", "push", "-p", str(root), "--accelerator", accelerator],
            timeout=min(timeout_seconds, 300),
            runner=runner,
        )

        deadline = time.monotonic() + timeout_seconds
        last_status = ""
        terminal_error = None
        while time.monotonic() < deadline:
            status_result = _run(
                [executable, "kernels", "status", kernel_id],
                timeout=60,
                runner=runner,
            )
            text = (str(status_result.stdout or "") + "\n" + str(status_result.stderr or "")).lower()
            last_status = text.strip()
            if any(word in text for word in ("complete", "completed")):
                break
            if any(word in text for word in ("error", "failed", "cancelled")):
                terminal_error = f"Kaggle kernel failed: {last_status[:1200]}"
                break
            time.sleep(15)
        else:
            raise KaggleGenerationError("Kaggle kernel timed out")

        download_dir = root / "download"
        download_dir.mkdir()
        try:
            _run(
                [executable, "kernels", "output", kernel_id, "-p", str(download_dir), "-o"],
                timeout=180,
                runner=runner,
            )
        except KaggleGenerationError as output_exc:
            if terminal_error:
                raise KaggleGenerationError(f"{terminal_error}; output retrieval failed: {output_exc}") from output_exc
            raise
        if terminal_error:
            diagnostics = []
            for candidate in sorted(download_dir.rglob("*")):
                if candidate.is_file() and candidate.suffix.lower() in {".log", ".txt", ".json"}:
                    try:
                        body = candidate.read_text(encoding="utf-8", errors="replace").strip()
                    except OSError:
                        continue
                    if body:
                        if candidate.suffix.lower() == ".log":
                            extracted = _extract_kaggle_diagnostic(candidate)
                            if extracted:
                                diagnostics.append(f"{candidate.name}: {extracted}")
                        else:
                            diagnostics.append(f"{candidate.name}: {body[-4000:]}")
            detail = "; ".join(diagnostics)[-8000:] if diagnostics else "no diagnostic output was returned"
            raise KaggleGenerationError(f"{terminal_error}; diagnostics: {detail}")
        generated = download_dir / "asset.png"
        result_path = download_dir / "result.json"
        if not generated.is_file() or generated.stat().st_size <= 0:
            raise KaggleGenerationError("Kaggle kernel produced no asset.png")

        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generated, output)
        metadata_out = {}
        if result_path.is_file():
            try:
                metadata_out = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                metadata_out = {}

        try:
            _run(
                [executable, "kernels", "delete", kernel_id, "-y"],
                timeout=60,
                runner=runner,
            )
        except KaggleGenerationError:
            pass

    return {
        "provider": "kaggle-notebooks",
        "kernel": kernel_id,
        "model": model,
        "accelerator": accelerator,
        "width": width,
        "height": height,
        "steps": steps,
        "seed": int(seed),
        "reference": reference_path is not None,
        "result": metadata_out,
    }
