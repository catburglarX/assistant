#!/usr/bin/env python3
"""Render the importable Open WebUI Mira model preset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project import ROOT, read_env, setting


def render(env_path: Path | None = None, output: Path | None = None) -> Path:
    values = read_env(env_path)
    name = setting(values, "ASSISTANT_NAME", "Mira")
    model = setting(values, "OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    prompt = (ROOT / "config" / "mira-system-prompt.md").read_text(encoding="utf-8").strip()
    template = json.loads((ROOT / "config" / "mira-model.template.json").read_text(encoding="utf-8"))
    entry = template[0]
    entry["name"] = name
    entry["base_model_id"] = model
    entry["params"]["system"] = prompt
    destination = output or ROOT / "config" / "mira-model.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    print(render(args.env, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
