"""Offline prompt/config contracts; these are not live model behavior tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render_config import render


class PromptContractTests(unittest.TestCase):
    def setUp(self):
        self.prompt = (ROOT / "config/coco-system-prompt.md").read_text(encoding="utf-8")

    def test_language_and_shortcut_contracts(self):
        for fragment in (
            "English -> reply in English.",
            "Hinglish -> reply in natural Hinglish.",
            "Switch when the user switches.",
            "ik = I know; idk = I don't know; u = you.",
            "English abbreviations, informal spelling, and typos do not make a message Hinglish.",
        ):
            self.assertIn(fragment, self.prompt)

    def test_listening_and_banter_preserve_boundaries(self):
        for fragment in (
            "Ask at most one relevant question, then wait.",
            "Don't append speculative advice after asking for context.",
            "Don't demand polite language before answering a legitimate question.",
            "Don't say you're leaving, ending the session",
            "Don't claim love, jealousy, loneliness, or a need for the user.",
            "You are AI, not human.",
        ):
            self.assertIn(fragment, self.prompt)

    def test_manual_memory_is_not_authorized_by_prompt(self):
        self.assertIn("You cannot write memories yourself.", self.prompt)
        self.assertIn("Confirm a save, edit, or deletion only after an actual successful operation.", self.prompt)
        self.assertIn("Don't store passwords, API keys", self.prompt)

    def test_render_embeds_exact_prompt_and_bounded_output(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / "test.env"
            env.write_text("ASSISTANT_NAME=Coco\n", encoding="utf-8")
            output = Path(directory) / "coco.json"
            render(env, output)
            model = json.loads(output.read_text(encoding="utf-8"))[0]
            self.assertEqual(model["params"]["system"], self.prompt.strip())
            self.assertEqual(model["params"]["max_tokens"], 1024)
            self.assertTrue(model["meta"]["capabilities"]["memory"])
            self.assertFalse(model["meta"]["capabilities"]["builtin_tools"])
            self.assertTrue(all(value is False for value in model["meta"]["builtinTools"].values()))


if __name__ == "__main__":
    unittest.main()
