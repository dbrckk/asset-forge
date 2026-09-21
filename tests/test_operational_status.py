import unittest
from pathlib import Path
from unittest.mock import patch

from operational_status import build_operational_status


class OperationalStatusTests(unittest.TestCase):
    def test_ready_matrix_is_machine_readable(self):
        def which(name):
            mapping = {
                "polli": "/usr/bin/polli",
                "godot4": "/usr/bin/godot4",
            }
            return mapping.get(name)

        with patch("generator_backends.shutil.which", side_effect=which), \
             patch("operational_status.raster_backend_status") as raster, \
             patch("operational_status.detect_3d_tools", return_value={"blender": {"available": False}}):
            raster.return_value = {
                "png": {"decode": True, "encode": True, "dependency": "builtin"},
                "webp": {
                    "inspect": True,
                    "decode": {"available": True},
                    "encode": {"available": True},
                },
            }
            status = build_operational_status(
                environ={"POLLINATIONS_API_KEY": "secret"},
                home=Path("/not-real"),
                which=which,
            )

        self.assertEqual(status["schema"], "asset-forge/operational-status/v1")
        self.assertTrue(status["ready"]["full"])
        self.assertTrue(status["capabilities"]["rasterPng"])
        self.assertTrue(status["capabilities"]["rasterWebp"])
        self.assertTrue(status["capabilities"]["vectorSvg"])
        self.assertTrue(status["capabilities"]["threeDGlb"])
        self.assertTrue(status["capabilities"]["godotImport"])
        self.assertNotIn("secret", repr(status))

    def test_missing_optional_tools_are_reported_without_crashing(self):
        with patch("generator_backends.shutil.which", return_value=None), \
             patch("operational_status.raster_backend_status") as raster, \
             patch("operational_status.detect_3d_tools", return_value={}):
            raster.return_value = {
                "png": {"decode": True, "encode": True, "dependency": "builtin"},
                "webp": {
                    "inspect": True,
                    "decode": {"available": False},
                    "encode": {"available": False},
                },
            }
            status = build_operational_status(
                environ={},
                home=Path("/not-real"),
                which=lambda name: None,
            )

        self.assertFalse(status["ready"]["anyGeneratedAsset"])
        self.assertFalse(status["ready"]["full"])
        self.assertTrue(status["blockers"])


    def test_imagen_codex_reports_required_token_names(self):
        def which(name):
            return "/usr/bin/imagen" if name == "imagen" else None

        with patch("generator_backends.shutil.which", side_effect=which), \
             patch("operational_status.raster_backend_status") as raster, \
             patch("operational_status.detect_3d_tools", return_value={}):
            raster.return_value = {
                "png": {"decode": True, "encode": True, "dependency": "builtin"},
                "webp": {
                    "inspect": True,
                    "decode": {"available": True},
                    "encode": {"available": True},
                },
            }
            status = build_operational_status(
                environ={"IMAGEN_API_KEY": "unused"},
                home=Path("/not-real"),
                which=which,
            )

        self.assertFalse(status["capabilities"]["imagenCodexRaster"])
        self.assertTrue(any(
            "CODEX_ACCESS_TOKEN or CHATGPT_ACCESS_TOKEN" in value
            for value in status["blockers"]
        ))


    def test_cloudflare_free_raster_is_reported_as_ready_without_cli(self):
        with patch(
            "operational_status.generator_backend_status",
            return_value={
                "cloudflare": {
                    "authenticated": True,
                    "rasterReady": True,
                    "model": "@cf/test",
                },
                "kaggleQwen": {"rasterReady": False},
                "pollinations": {
                    "installed": False,
                    "authenticated": False,
                    "rasterVectorReady": False,
                    "threeDReady": False,
                },
                "imagenCodex": {
                    "installed": False,
                    "authenticated": False,
                    "rasterReady": False,
                },
                "qwenColab": {"queueReady": False},
            },
        ), patch("operational_status.raster_backend_status") as raster, patch(
            "operational_status.detect_3d_tools", return_value={}
        ):
            raster.return_value = {
                "png": {"decode": True, "encode": True, "dependency": "builtin"},
                "webp": {
                    "inspect": True,
                    "decode": {"available": True},
                    "encode": {"available": True},
                },
            }
            status = build_operational_status(
                environ={},
                home=Path("/not-real"),
                which=lambda name: None,
            )

        self.assertTrue(status["ready"]["anyGeneratedAsset"])
        self.assertTrue(status["ready"]["raster"])
        self.assertTrue(status["capabilities"]["freeRaster"])
        self.assertTrue(status["capabilities"]["cloudflareRaster"])
        self.assertTrue(status["capabilities"]["autoRaster"])
        self.assertTrue(status["ready"]["autoRaster"])
        self.assertEqual(
            status["routing"]["preferredRasterBackend"],
            "cloudflare",
        )
        self.assertFalse(
            any("no authenticated raster generation backend" in value for value in status["blockers"])
        )

    def test_manual_raster_backend_is_not_reported_as_auto_route(self):
        with patch(
            "operational_status.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": False},
                "kaggleQwen": {"rasterReady": False},
                "pollinations": {
                    "installed": True,
                    "authenticated": True,
                    "rasterVectorReady": True,
                    "threeDReady": False,
                },
                "imagenCodex": {
                    "installed": False,
                    "authenticated": False,
                    "rasterReady": False,
                },
                "qwenColab": {"queueReady": False},
            },
        ), patch("operational_status.raster_backend_status") as raster, patch(
            "operational_status.detect_3d_tools", return_value={}
        ):
            raster.return_value = {
                "png": {"decode": True, "encode": True, "dependency": "builtin"},
                "webp": {
                    "inspect": True,
                    "decode": {"available": True},
                    "encode": {"available": True},
                },
            }
            status = build_operational_status(
                environ={},
                home=Path("/not-real"),
                which=lambda name: None,
            )

        self.assertTrue(status["ready"]["raster"])
        self.assertFalse(status["ready"]["autoRaster"])
        self.assertFalse(status["capabilities"]["autoRaster"])
        self.assertIsNone(status["routing"]["preferredRasterBackend"])
        self.assertFalse(status["routing"]["autoRasterReady"])
        self.assertTrue(any(
            "automatic free raster routing is unavailable" in value
            for value in status["blockers"]
        ))

    def test_qwen_colab_queue_counts_as_queued_generation_capability(self):
        with patch(
            "operational_status.generator_backend_status",
            return_value={
                "cloudflare": {"rasterReady": False},
                "kaggleQwen": {"rasterReady": False},
                "pollinations": {
                    "rasterVectorReady": False,
                    "threeDReady": False,
                },
                "imagenCodex": {
                    "installed": False,
                    "authenticated": False,
                    "rasterReady": False,
                },
                "qwenColab": {"queueReady": True},
            },
        ), patch("operational_status.raster_backend_status") as raster, patch(
            "operational_status.detect_3d_tools", return_value={}
        ):
            raster.return_value = {
                "png": {"decode": True, "encode": True, "dependency": "builtin"},
                "webp": {
                    "inspect": True,
                    "decode": {"available": True},
                    "encode": {"available": True},
                },
            }
            status = build_operational_status(
                environ={},
                home=Path("/not-real"),
                which=lambda name: None,
            )

        self.assertTrue(status["ready"]["anyGeneratedAsset"])
        self.assertFalse(status["ready"]["raster"])
        self.assertTrue(status["ready"]["queuedRaster"])
        self.assertTrue(status["capabilities"]["qwenColabQueue"])
        self.assertEqual(status["routing"]["queuedRasterBackend"], "qwen-colab")
        self.assertTrue(
            any("Qwen Colab batch queue is available" in value for value in status["blockers"])
        )


if __name__ == "__main__":
    unittest.main()
