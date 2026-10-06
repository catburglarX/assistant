#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p backups
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="backups/coco-data-${stamp}.tar.gz"
docker compose exec -T open-webui tar -C /app/backend/data -czf - . > "$output"
chmod 600 "$output" 2>/dev/null || true
echo "Created $output"
