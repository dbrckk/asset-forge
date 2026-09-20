from __future__ import annotations

import base64
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPOSITORY = os.environ.get("ASSET_FORGE_GITHUB_REPOSITORY", "dbrckk/asset-forge")
BRANCH = os.environ.get("ASSET_FORGE_GITHUB_BRANCH", "main")
QUEUE_DIR = os.environ.get("ASSET_FORGE_COLAB_QUEUE_DIR", "colab-queue/jobs")
RESULT_DIR = os.environ.get("ASSET_FORGE_COLAB_RESULT_DIR", "colab-queue/results")
MODEL_ID = os.environ.get("QWEN_IMAGE_MODEL", "Qwen/Qwen-Image-2.1")
POLL_SECONDS = max(5, int(os.environ.get("ASSET_FORGE_COLAB_POLL_SECONDS", "15")))


def _token() -> str:
    token = str(os.environ.get("ASSET_FORGE_GITHUB_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("ASSET_FORGE_GITHUB_TOKEN is required")
    return token


def _request(method: str, path: str, payload: dict | None = None):
    url = f"https://api.github.com/repos/{REPOSITORY}/{path}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {_token()}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "asset-forge-colab-worker",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")) if raw else None


def list_jobs() -> list[dict]:
    try:
        rows = _request("GET", f"contents/{urllib.parse.quote(QUEUE_DIR)}?ref={urllib.parse.quote(BRANCH)}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        raise
    if not isinstance(rows, list):
        return []
    return sorted(
        [row for row in rows if isinstance(row, dict) and str(row.get("name", "")).endswith(".json")],
        key=lambda row: str(row.get("name") or ""),
    )


def _get_json(path: str) -> tuple[dict, str]:
    value = _request("GET", f"contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(BRANCH)}")
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid GitHub file payload: {path}")
    content = base64.b64decode(str(value.get("content") or "")).decode("utf-8")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise RuntimeError(f"job must be an object: {path}")
    return payload, str(value.get("sha") or "")


def _put(path: str, data: bytes, message: str, sha: str | None = None) -> dict:
    payload = {
        "message": message,
        "content": base64.b64encode(data).decode("ascii"),
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha
    return _request("PUT", f"contents/{urllib.parse.quote(path)}", payload)


def _put_overwrite(path: str, data: bytes, message: str) -> dict:
    sha = None
    try:
        current = _request(
            "GET",
            f"contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(BRANCH)}",
        )
        if isinstance(current, dict):
            sha = str(current.get("sha") or "") or None
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    return _put(path, data, message, sha=sha)


def heartbeat() -> None:
    payload = {
        "schema": "asset-forge/qwen-colab-worker-status/v1",
        "repository": REPOSITORY,
        "branch": BRANCH,
        "model": MODEL_ID,
        "timestamp": int(time.time()),
        "online": True,
    }
    _put_overwrite(
        "colab-queue/worker-status.json",
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "colab: worker heartbeat",
    )


def _delete(path: str, sha: str, message: str) -> None:
    _request(
        "DELETE",
        f"contents/{urllib.parse.quote(path)}",
        {"message": message, "sha": sha, "branch": BRANCH},
    )


def _download_reference(value):
    from PIL import Image

    if isinstance(value, dict) and str(value.get("github_path") or "").strip():
        remote_path = str(value["github_path"])
        payload = _request(
            "GET",
            f"contents/{urllib.parse.quote(remote_path)}?ref={urllib.parse.quote(BRANCH)}",
        )
        raw = base64.b64decode(str(payload.get("content") or ""))
        return Image.open(io.BytesIO(raw)).convert("RGBA")

    url = str(value or "")
    request = urllib.request.Request(url, headers={"User-Agent": "asset-forge-colab-worker"})
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = response.read()
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def load_pipeline():
    import torch
    from diffusers import QwenImage21Pipeline

    pipe = QwenImage21Pipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
    )
    if torch.cuda.is_available():
        pipe = pipe.to("cuda")
    else:
        pipe.enable_model_cpu_offload()
    return pipe


def run_job(pipe, job: dict):
    import torch

    prompt = str(job.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("prompt missing")
    width = int(job.get("width") or 1024)
    height = int(job.get("height") or 1024)
    steps = int(job.get("steps") or 28)
    seed = int(job.get("seed") or 0)
    refs = job.get("references") if isinstance(job.get("references"), list) else []
    images = [
        _download_reference(value)
        for value in refs[:10]
        if (
            isinstance(value, dict)
            and str(value.get("github_path") or "").strip()
        )
        or str(value).startswith("https://")
    ]

    kwargs = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": steps,
        "generator": torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed),
    }
    if images:
        kwargs["image"] = images if len(images) > 1 else images[0]

    image = pipe(**kwargs).images[0]
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue(), {
        "model": MODEL_ID,
        "width": image.width,
        "height": image.height,
        "seed": seed,
        "steps": steps,
        "references": len(images),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }


def process_once(pipe) -> bool:
    jobs = list_jobs()
    if not jobs:
        return False

    row = jobs[0]
    job_path = str(row.get("path") or "")
    job, sha = _get_json(job_path)
    job_id = str(job.get("id") or Path(job_path).stem)
    result_prefix = f"{RESULT_DIR}/{job_id}"

    try:
        png, metadata = run_job(pipe, job)
        _put(f"{result_prefix}/asset.png", png, f"colab: render {job_id}")
        result = {
            "schema": "asset-forge/qwen-colab-result/v1",
            "id": job_id,
            "success": True,
            "artifact": f"{result_prefix}/asset.png",
            "metadata": metadata,
        }
        _put(
            f"{result_prefix}/result.json",
            (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            f"colab: complete {job_id}",
        )
        _delete(job_path, sha, f"colab: dequeue {job_id}")
    except Exception as exc:
        result = {
            "schema": "asset-forge/qwen-colab-result/v1",
            "id": job_id,
            "success": False,
            "error": f"{type(exc).__name__}: {exc}"[:1000],
        }
        _put(
            f"{result_prefix}/result.json",
            (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            f"colab: fail {job_id}",
        )
        _delete(job_path, sha, f"colab: dequeue failed {job_id}")
    return True


def main() -> None:
    print(f"Loading {MODEL_ID}...")
    pipe = load_pipeline()
    print(f"Worker online for {REPOSITORY}@{BRANCH}.")
    while True:
        heartbeat()
        worked = process_once(pipe)
        if not worked:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
