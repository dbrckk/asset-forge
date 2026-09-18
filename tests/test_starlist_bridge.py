import json
import tempfile
import unittest
from pathlib import Path

from starlist_bridge import build_visual_discovery_report, run_starlist_recommender


FAKE_RECOMMENDER = r'''#!/usr/bin/env python3
import argparse
import json

ap = argparse.ArgumentParser()
ap.add_argument("query")
ap.add_argument("--top")
ap.add_argument("--domain")
ap.add_argument("--max-complexity")
ap.add_argument("--json", action="store_true")
args = ap.parse_args()

print(json.dumps({
    "query": args.query,
    "inferredDomains": [args.domain],
    "recommendations": [{
        "repo": "example/tool",
        "selectionScore": 90,
        "domain": args.domain
    }]
}))
'''


class StarListBridgeTests(unittest.TestCase):
    def make_fake_star_list(self, root: Path) -> None:
        scripts = root / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "recommend.py").write_text(FAKE_RECOMMENDER, encoding="utf-8")

    def test_run_recommender_parses_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fake_star_list(root)
            result = run_starlist_recommender(root, "pixel art sprites", top=3)

        self.assertEqual(result["recommendations"][0]["repo"], "example/tool")
        self.assertEqual(result["inferredDomains"], ["graphics"])

    def test_full_report_runs_visual_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fake_star_list(root)
            report = build_visual_discovery_report(root)

        self.assertEqual(report["source"], "dbrckk/star-list")
        self.assertIn("pixel-art", report["queries"])
        self.assertIn("vector-ui", report["queries"])
        self.assertIn("3d", report["queries"])
        self.assertIn("materials", report["queries"])
        self.assertIn("optimization", report["queries"])

    def test_missing_recommender_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "recommender not found"):
                run_starlist_recommender(Path(tmp), "sprite")


if __name__ == "__main__":
    unittest.main()
