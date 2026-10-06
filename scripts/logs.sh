#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
# Best-effort redaction for common OpenRouter key and Authorization formats.
docker compose logs --tail="${1:-200}" 2>&1 |
  sed -E \
    -e 's/(sk-or-v1-)[A-Za-z0-9_-]+/\1[REDACTED]/g' \
    -e 's/(Authorization: Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/Ig'
