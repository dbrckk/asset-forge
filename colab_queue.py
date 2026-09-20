from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class ColabQueueError(RuntimeError):
    pass


def job_id(job: dict) -> str:
    canonical = json.dumps(job, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:24]


def build_colab_job(
    job: dict,
    *,
    reference_urls: list[str] | None = None,
    references: list[dict] | None = None,
) -> dict:
    prompt = str(job.get("instruction") or "").strip()
    if not prompt:
        raise ColabQueueError("production job instruction missing")
    manifest = job.get("manifest") if isinstance(job.get("manifest"), dict) else {}
    constraints = manifest.get("constraints") if isinstance(manifest.get("constraints"), dict) else {}
    payload = {
        "schema": "asset-forge/qwen-colab-job/v1",
        "prompt": prompt,
        "width": int(constraints.get("generationWidth") or 1024),
        "height": int(constraints.get("generationHeight") or 1024),
        "steps": int(constraints.get("generationSteps") or 28),
        "seed": int(constraints.get("seed") or 0),
        "references": (
            list(references or [])
            if references is not None
            else list(reference_urls or [])
        )[:10],
    }
    payload["id"] = job_id(payload)
    return payload


def _github_request(repository: str, token: str, method: str, path: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/{path}",
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "asset-forge-colab-queue",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")) if raw else None


def submit(
    job: dict,
    *,
    repository: str | None = None,
    branch: str = "main",
    token: str | None = None,
    queue_dir: str = "colab-queue/jobs",
    input_dir: str = "colab-queue/inputs",
    reference_paths: list[Path] | None = None,
) -> dict:
    import base64

    repository = repository or os.environ.get("ASSET_FORGE_GITHUB_REPOSITORY", "dbrckk/asset-forge")
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("ASSET_FORGE_GITHUB_TOKEN")
    if not str(token or "").strip():
        raise ColabQueueError("GitHub token required to submit a Colab job")
    payload = build_colab_job(job)
    refs = []
    for index, raw_path in enumerate(reference_paths or []):
        source = Path(raw_path)
        if not source.is_file():
            raise ColabQueueError(f"reference file missing: {source}")
        suffix = source.suffix.lower() or ".png"
        remote_path = f"{input_dir}/{payload['id']}/{index}{suffix}"
        encoded_ref = base64.b64encode(source.read_bytes()).decode("ascii")
        _github_request(
            repository,
            str(token),
            "PUT",
            f"contents/{urllib.parse.quote(remote_path)}",
            {
                "message": f"colab: upload reference {payload['id']} #{index}",
                "content": encoded_ref,
                "branch": branch,
            },
        )
        refs.append({"github_path": remote_path})
    if refs:
        payload["references"] = refs[:10]
        payload["id"] = job_id({key: value for key, value in payload.items() if key != "id"})
    path = f"{queue_dir}/{payload['id']}.json"
    encoded = base64.b64encode((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")).decode("ascii")
    _github_request(
        repository,
        str(token),
        "PUT",
        f"contents/{urllib.parse.quote(path)}",
        {"message": f"colab: queue {payload['id']}", "content": encoded, "branch": branch},
    )
    return {"id": payload["id"], "path": path, "repository": repository, "branch": branch}


def wait_result(
    job_id_value: str,
    *,
    repository: str | None = None,
    branch: str = "main",
    token: str | None = None,
    timeout_seconds: float = 900,
    poll_seconds: float = 10,
    result_dir: str = "colab-queue/results",
) -> dict:
    import base64

    repository = repository or os.environ.get("ASSET_FORGE_GITHUB_REPOSITORY", "dbrckk/asset-forge")
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("ASSET_FORGE_GITHUB_TOKEN")
    if not str(token or "").strip():
        raise ColabQueueError("GitHub token required to read Colab results")
    deadline = time.monotonic() + timeout_seconds
    path = f"{result_dir}/{job_id_value}/result.json"
    while time.monotonic() < deadline:
        try:
            value = _github_request(
                repository,
                str(token),
                "GET",
                f"contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(branch)}",
            )
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                time.sleep(poll_seconds)
                continue
            raise
        content = base64.b64decode(str(value.get("content") or "")).decode("utf-8")
        result = json.loads(content)
        if isinstance(result, dict):
            return result
        raise ColabQueueError("invalid Colab result payload")
    raise TimeoutError(f"Colab job {job_id_value} did not complete before timeout")


def download_result_asset(
    result: dict,
    destination: Path,
    *,
    repository: str | None = None,
    branch: str = "main",
    token: str | None = None,
) -> Path:
    import base64

    repository = repository or os.environ.get("ASSET_FORGE_GITHUB_REPOSITORY", "dbrckk/asset-forge")
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("ASSET_FORGE_GITHUB_TOKEN")
    if not str(token or "").strip():
        raise ColabQueueError("GitHub token required to download Colab artifact")
    artifact = str(result.get("artifact") or "").strip()
    if result.get("success") is not True or not artifact:
        raise ColabQueueError(str(result.get("error") or "Colab generation failed"))
    value = _github_request(
        repository,
        str(token),
        "GET",
        f"contents/{urllib.parse.quote(artifact)}?ref={urllib.parse.quote(branch)}",
    )
    raw = base64.b64decode(str(value.get("content") or ""))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return destination
