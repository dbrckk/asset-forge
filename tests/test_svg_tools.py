import tempfile
import unittest
from pathlib import Path

from svg_tools import inspect_svg, sanitize_svg


class SvgToolsTests(unittest.TestCase):
    def test_valid_svg_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
                '<path d="M0 0h16v16H0z"/></svg>',
                encoding="utf-8",
            )
            info, errors, warnings = inspect_svg(path)

        self.assertEqual(errors, [])
        self.assertEqual(info["viewBox"], "0 0 16 16")
        self.assertEqual(warnings, [])

    def test_missing_viewbox_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"></svg>',
                encoding="utf-8",
            )
            _, errors, warnings = inspect_svg(path)

        self.assertEqual(errors, [])
        self.assertIn("viewBox is recommended for scalable project assets", warnings)

    def test_script_and_events_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" onload="x()">'
                '<script>alert(1)</script></svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertTrue(any("disallowed" in error for error in errors))
        self.assertTrue(any("event-handler" in error for error in errors))

    def test_external_href_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<image href="https://example.com/a.png"/></svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertTrue(any("external references" in error for error in errors))

    def test_sanitize_removes_dangerous_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.svg"
            output = Path(tmp) / "clean.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" onclick="x()">'
                '<script>alert(1)</script>'
                '<image href="https://example.com/a.png"/>'
                '<rect x="1" y="1" width="8" height="8"/>'
                '</svg>',
                encoding="utf-8",
            )

            report = sanitize_svg(source, output)
            _, errors, _ = inspect_svg(output)
            rendered = output.read_text(encoding="utf-8")

        self.assertEqual(errors, [])
        self.assertEqual(report["removedElements"], 1)
        self.assertGreaterEqual(report["removedAttributes"], 2)
        self.assertNotIn("<script", rendered)
        self.assertNotIn("https://example.com", rendered)


if __name__ == "__main__":
    unittest.main()
