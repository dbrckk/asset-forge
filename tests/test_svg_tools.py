import tempfile
import unittest
from pathlib import Path

from svg_tools import inspect_svg, normalize_viewbox, sanitize_svg, validate_svg_profile


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

        self.assertTrue(any("non-fragment references" in error for error in errors))

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

    def test_icon_profile_requires_square_viewbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 16"></svg>',
                encoding="utf-8",
            )
            _, errors, _ = validate_svg_profile(path, "icon")

        self.assertIn("profile icon: square viewBox required", errors)

    def test_ui_profile_accepts_non_square_viewbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180"></svg>',
                encoding="utf-8",
            )
            _, errors, _ = validate_svg_profile(path, "ui")

        self.assertEqual(errors, [])

    def test_aspect_ratio_mismatch_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mismatch.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
                'viewBox="0 0 200 100"></svg>',
                encoding="utf-8",
            )
            _, errors, warnings = inspect_svg(path)

        self.assertEqual(errors, [])
        self.assertIn(
            "width/height aspect ratio differs from viewBox aspect ratio",
            warnings,
        )

    def test_normalize_viewbox_from_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.svg"
            output = Path(tmp) / "normalized.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32">'
                '<rect width="64" height="32"/></svg>',
                encoding="utf-8",
            )

            report = normalize_viewbox(source, output)
            info, errors, _ = inspect_svg(output)

        self.assertTrue(report["changed"])
        self.assertEqual(info["viewBox"], "0 0 64 32")
        self.assertEqual(errors, [])

    def test_sanitize_removes_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.svg"
            output = Path(tmp) / "clean.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<metadata>editor data</metadata>'
                '<rect width="10" height="10"/>'
                '</svg>',
                encoding="utf-8",
            )

            report = sanitize_svg(source, output)
            rendered = output.read_text(encoding="utf-8")

        self.assertEqual(report["removedElements"], 1)
        self.assertNotIn("metadata", rendered)

    def test_data_uri_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<image href="data:image/png;base64,AAAA"/></svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertTrue(any("non-fragment references" in error for error in errors))

    def test_relative_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<image href="texture.png"/></svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertTrue(any("texture.png" in error for error in errors))

    def test_internal_fragment_reference_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<defs><linearGradient id="g"/></defs>'
                '<rect width="10" height="10" fill="url(#g)"/></svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertEqual(errors, [])

    def test_css_external_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<rect style="fill:url(https://example.com/a.svg#x)" width="10" height="10"/>'
                '</svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertTrue(any("unsafe CSS references" in error for error in errors))

    def test_css_import_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<style>@import url("https://example.com/x.css");</style></svg>',
                encoding="utf-8",
            )
            _, errors, _ = inspect_svg(path)

        self.assertTrue(any("@import" in error for error in errors))

    def test_sanitize_removes_unsafe_css(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.svg"
            output = Path(tmp) / "clean.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<style>@import url("https://example.com/x.css");</style>'
                '<rect style="fill:url(texture.svg#x)" width="10" height="10"/>'
                '</svg>',
                encoding="utf-8",
            )
            report = sanitize_svg(source, output)
            _, errors, _ = inspect_svg(output)

        self.assertEqual(errors, [])
        self.assertGreaterEqual(report["removedElements"], 1)
        self.assertGreaterEqual(report["removedAttributes"], 1)

    def test_profile_depth_limit_is_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep.svg"
            inner = '<rect width="1" height="1"/>'
            for _ in range(40):
                inner = f"<g>{inner}</g>"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
                + inner
                + '</svg>',
                encoding="utf-8",
            )
            info, errors, _ = validate_svg_profile(path, "icon")

        self.assertGreater(info["maxDepth"], 32)
        self.assertTrue(any("XML depth" in error for error in errors))

    def test_profile_file_size_limit_is_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.svg"
            payload = "x" * 270000
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
                f"<desc>{payload}</desc></svg>",
                encoding="utf-8",
            )
            info, errors, _ = validate_svg_profile(path, "icon")

        self.assertGreater(info["bytes"], 262144)
        self.assertTrue(any("file size" in error for error in errors))

    def test_existing_malformed_viewbox_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.svg"
            output = Path(tmp) / "normalized.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32" '
                'viewBox="broken"></svg>',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "existing viewBox is malformed"):
                normalize_viewbox(source, output)


if __name__ == "__main__":
    unittest.main()
