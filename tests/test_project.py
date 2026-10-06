from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


os.sys.path.insert(0, str(SCRIPTS))
validate_module = load("validate")
render_module = load("render_config")


class ProjectTests(unittest.TestCase):
    def test_safe_configuration(self):
        values = {
            "OPENROUTER_API_KEY": "test-only-not-a-real-key",
            "OPENROUTER_MODEL": "nvidia/nemotron-3-ultra-550b-a55b",
            "ASSISTANT_NAME": "Coco",
            "APP_HOST": "127.0.0.1",
            "APP_PORT": "3000",
        }
        self.assertEqual(validate_module.validate(values), [])
        values["APP_HOST"] = "0.0.0.0"
        self.assertIn("127.0.0.1", validate_module.validate(values)[0])

    def test_missing_key_is_useful(self):
        errors = validate_module.validate(
            {
                "OPENROUTER_MODEL": "nvidia/nemotron-3-ultra-550b-a55b",
                "APP_HOST": "127.0.0.1",
                "APP_PORT": "3000",
            }
        )
        self.assertTrue(any("OPENROUTER_API_KEY is missing" in item for item in errors))

    def test_rendered_preset_is_manual_memory_only(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            env.write_text(
                "ASSISTANT_NAME=Coco\nOPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b\n",
                encoding="utf-8",
            )
            output = Path(directory) / "model.json"
            render_module.render(env, output)
            model = json.loads(output.read_text(encoding="utf-8"))[0]
            self.assertEqual(model["name"], "Coco")
            self.assertEqual(model["base_model_id"], "nvidia/nemotron-3-ultra-550b-a55b")
            self.assertTrue(model["meta"]["capabilities"]["memory"])
            self.assertFalse(model["meta"]["builtinTools"]["memory"])
            self.assertFalse(model["meta"]["builtinTools"]["web_search"])
            self.assertIn("You are AI, not human", model["params"]["system"])

    def test_compose_is_loopback_authenticated_and_persistent(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("${APP_HOST:-127.0.0.1}:${APP_PORT:-3000}:8080", compose)
        self.assertIn('WEBUI_AUTH: "true"', compose)
        self.assertIn("coco-data:/app/backend/data", compose)
        self.assertIn('ENABLE_OLLAMA_API: "false"', compose)
        self.assertIn('ENABLE_WEB_SEARCH: "false"', compose)
        self.assertIn('ENABLE_CODE_INTERPRETER: "false"', compose)
        self.assertIn('ENABLE_MEMORY_BACKGROUND_REVIEW: "false"', compose)

    def test_no_committed_openrouter_secret(self):
        key_pattern = re.compile(r"sk-or-v1-[A-Za-z0-9_-]{16,}")
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertIsNone(key_pattern.search(text), f"possible secret in {path}")


if __name__ == "__main__":
    unittest.main()
