from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_starlist_recommender(
    star_list_root: Path,
    query: str,
    *,
    top: int = 8,
    domain: str = "graphics",
    max_complexity: str = "medium",
) -> dict:
    """Run dbrckk/star-list's recommender without duplicating its ranking logic."""
    star_list_root = star_list_root.resolve()
    script = star_list_root / "scripts" / "recommend.py"
    if not script.is_file():
        raise ValueError(f"star-list recommender not found: {script}")
    if top < 1:
        raise ValueError("top must be >= 1")

    command = [
        sys.executable,
        str(script),
        query,
        "--top",
        str(top),
        "--domain",
        domain,
        "--max-complexity",
        max_complexity,
        "--json",
    ]

    completed = subprocess.run(
        command,
        cwd=star_list_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"star-list recommender failed: {detail}")

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("star-list recommender returned invalid JSON") from exc

    if not isinstance(result, dict):
        raise RuntimeError("star-list recommender returned a non-object result")

    recommendations = result.get("recommendations")
    if not isinstance(recommendations, list):
        raise RuntimeError("star-list result is missing recommendations")

    return result


def build_visual_discovery_report(star_list_root: Path) -> dict:
    tasks = {
        "pixel-art": "pixel art sprites tilesets animation atlas",
        "vector-ui": "vector svg game ui icons illustration",
        "3d": "3d modeling rigging animation textures game assets",
        "materials": "pbr materials texture generation game assets",
        "optimization": "image texture mesh optimization game assets",
    }

    report = {
        "source": "dbrckk/star-list",
        "domain": "graphics",
        "queries": {},
    }

    for key, query in tasks.items():
        result = run_starlist_recommender(
            star_list_root,
            query,
            top=8,
            domain="graphics",
            max_complexity="medium",
        )
        report["queries"][key] = {
            "query": query,
            "recommendations": result.get("recommendations", []),
        }

    return report
