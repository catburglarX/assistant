#!/usr/bin/env python3
"""Dependency-free helpers shared by project scripts."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path | None = None) -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = path or ROOT / ".env"
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return {**values, **{k: v for k, v in os.environ.items() if v is not None}}


def setting(values: dict[str, str], key: str, default: str = "") -> str:
    return values.get(key, default).strip()
