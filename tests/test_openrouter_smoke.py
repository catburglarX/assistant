from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("smoke", ROOT / "scripts" / "openrouter_smoke.py")
smoke = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(smoke)


class SmokeUnitTests(unittest.TestCase):
    def test_payload_uses_supported_minimal_fields(self):
        body = smoke.payload("nvidia/nemotron-3-ultra-550b-a55b", True)
        self.assertEqual(
            set(body),
            {"model", "messages", "max_tokens", "stream"},
        )
        self.assertNotIn("reasoning", body)
        self.assertNotIn("temperature", body)
        self.assertLessEqual(body["max_tokens"], 32)

    def test_error_labels_never_claim_success(self):
        class Error:
            code = 402

        self.assertEqual(smoke.friendly_http_error(Error()), "insufficient OpenRouter credits")

    def test_stream_parser(self):
        lines = [
            b'data: {"choices":[{"delta":{"content":"Coco "}}]}\n',
            b'data: {"choices":[{"delta":{"content":"OK"}}]}\n',
            b"data: [DONE]\n",
        ]
        self.assertEqual(smoke.parse_sse(lines), "Coco OK")

    def test_malformed_stream_fails(self):
        with self.assertRaises(ValueError):
            smoke.parse_sse([b'data: {"unexpected":true}\n'])


if __name__ == "__main__":
    unittest.main()
