#!/usr/bin/env python3
"""Fail fast on unsafe or incomplete local configuration."""

from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
from pathlib import Path

from project import ROOT, read_env, setting


def validate(values: dict[str, str], require_key: bool = True) -> list[str]:
    errors: list[str] = []
    key = setting(values, "OPENROUTER_API_KEY")
    if require_key and (not key or key.lower() in {"replace_me", "changeme", "your_key_here"}):
        errors.append("OPENROUTER_API_KEY is missing. Add it locally to .env; do not commit it.")
    model = setting(values, "OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    if not model or re.search(r"\s", model):
        errors.append("OPENROUTER_MODEL must be a non-empty model ID without spaces.")
    host = setting(values, "APP_HOST", "127.0.0.1")
    if host != "127.0.0.1":
        errors.append("APP_HOST must remain 127.0.0.1 for loopback-only hosting.")
    try:
        port = int(setting(values, "APP_PORT", "3000"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        errors.append("APP_PORT must be an integer from 1 to 65535.")
    if not setting(values, "ASSISTANT_NAME", "Mira"):
        errors.append("ASSISTANT_NAME cannot be empty.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    parser.add_argument("--allow-missing-key", action="store_true")
    parser.add_argument("--skip-compose", action="store_true")
    args = parser.parse_args()
    values = read_env(args.env)
    errors = validate(values, require_key=not args.allow_missing_key)
    if args.env.exists() and args.env.name != ".env.example" and os.name == "posix":
        mode = stat.S_IMODE(args.env.stat().st_mode)
        if mode & 0o077:
            errors.append(f"{args.env} permissions are {mode:o}; run chmod 600 {args.env}.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if not args.skip_compose:
        try:
            result = subprocess.run(
                ["docker", "compose", "--env-file", str(args.env), "config", "--quiet"],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError:
            print("ERROR: Docker Compose was not found.")
            return 1
        if result.returncode:
            print(result.stderr.strip() or "ERROR: docker compose configuration is invalid.")
            return result.returncode
    print("Configuration is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
