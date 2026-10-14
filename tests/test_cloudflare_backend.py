import base64
import io
import json
import tempfile
import unittest
from pathlib import Path

from cloudflare_backend import (
    CloudflareGenerationError,
    FLUX_KLEIN_MODEL,
    _extract_image_bytes,
    generate,
    status,
)


class Headers:
    def __init__(self, content_type):
        self.content_type = content_type
    def get(self, name):
        return self.content_type if name == "Content-Type" else None


class Response:
    def __init__(self, body, content_type="image/png"):
        self.body = body
        self.headers = Headers(content_type)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def read(self):
        return self.body


class CloudflareBackendTests(unittest.TestCase):
    def test_status_requires_both_credentials(self):
        self.assertFalse(status(environ={})["rasterReady"])
        self.assertTrue(status(environ={
            "CLOUDFLARE_API_TOKEN": "t",
            "CLOUDFLARE_ACCOUNT_ID": "a",
        })["rasterReady"])

    def test_extracts_base64_json_image(self):
        raw = json.dumps({"result": {"image": base64.b64encode(b"PNG").decode()}}).encode()
        self.assertEqual(_extract_image_bytes(raw, "application/json"), b"PNG")

    def test_generate_sends_img2img_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = root / "ref.png"
            ref.write_bytes(b"REFERENCE")
            out = root / "out.png"
            seen = {}

            def opener(request, timeout):
                seen["url"] = request.full_url
                seen["auth"] = request.get_header("Authorization")
                seen["payload"] = json.loads(request.data.decode())
                return Response(b"PNG")

            result = generate(
                "premium sprite",
                out,
                width=512,
                height=768,
                seed=7,
                reference_path=ref,
                environ={
                    "CLOUDFLARE_API_TOKEN": "secret",
                    "CLOUDFLARE_ACCOUNT_ID": "account",
                },
                opener=opener,
            )

            self.assertEqual(out.read_bytes(), b"PNG")
            self.assertIn("@cf/stabilityai/stable-diffusion-xl-base-1.0", seen["url"])
            self.assertEqual(seen["auth"], "Bearer secret")
            self.assertIn("image_b64", seen["payload"])
            self.assertEqual(seen["payload"]["width"], 512)
            self.assertTrue(result["reference"])

            # Official FLUX.2 Klein Workers AI protocol uses multipart binary
            # input_image_0..3, not SDXL JSON image_b64. Verify two references
            # and the Apache-2.0 4B endpoint without any network call.
            try:
                from PIL import Image
            except ImportError:
                # The base no-deps suite retains its historical dependencies.
                # CI separately reruns this test after installing Pillow.
                return
            ref2 = root / "ref2.png"
            Image.new("RGB", (64, 80)).save(ref)
            Image.new("RGB", (96, 96)).save(ref2)
            seen_flux = {}

            def flux_opener(request, timeout):
                seen_flux["url"] = request.full_url
                seen_flux["headers"] = {
                    key.lower(): value for key, value in request.header_items()
                }
                seen_flux["body"] = request.data
                return Response(
                    json.dumps({"result": {"image": base64.b64encode(b"PNG").decode()}}).encode(),
                    "application/json",
                )

            result = generate(
                "keep character identity",
                out,
                width=512,
                height=768,
                reference_path=ref,
                reference_paths=[ref, ref2],
                model=FLUX_KLEIN_MODEL,
                environ={
                    "CLOUDFLARE_API_TOKEN": "secret",
                    "CLOUDFLARE_ACCOUNT_ID": "account",
                },
                opener=flux_opener,
            )
            self.assertEqual(out.read_bytes(), b"PNG")
            self.assertIn(FLUX_KLEIN_MODEL, seen_flux["url"])
            self.assertTrue(
                seen_flux["headers"]["content-type"].startswith(
                    "multipart/form-data; boundary="
                )
            )
            self.assertIn(b'name="input_image_0"', seen_flux["body"])
            self.assertIn(b'name="input_image_1"', seen_flux["body"])
            self.assertIn(b'name="prompt"', seen_flux["body"])
            self.assertNotIn(b"image_b64", seen_flux["body"])
            self.assertNotIn(b"num_steps", seen_flux["body"])
            self.assertEqual(result["reference_count"], 2)
            self.assertEqual(result["steps"], 4)

            # Reject disallowed reference geometry before any chargeable call.
            Image.new("RGB", (512, 80)).save(ref2)
            with self.assertRaisesRegex(CloudflareGenerationError, "smaller than 512"):
                generate(
                    "keep character identity",
                    out,
                    reference_paths=[ref, ref2],
                    model=FLUX_KLEIN_MODEL,
                    environ={
                        "CLOUDFLARE_API_TOKEN": "secret",
                        "CLOUDFLARE_ACCOUNT_ID": "account",
                    },
                    opener=lambda *args, **kwargs: self.fail("unexpected paid request"),
                )

    def test_generate_rejects_missing_credentials(self):
        with self.assertRaisesRegex(CloudflareGenerationError, "required"):
            generate("x", Path("unused.png"), environ={})


if __name__ == "__main__":
    unittest.main()
