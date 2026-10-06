#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env 2>/dev/null || true
  echo "Created .env. Add your OpenRouter key locally, then run this command again."
  exit 1
fi

chmod 600 .env 2>/dev/null || true
python3 scripts/validate.py
python3 scripts/render_config.py
docker compose --env-file .env up -d

app_url="$(python3 - <<'PY'
from scripts.project import read_env, setting
values = read_env()
print(f"http://{setting(values, 'APP_HOST', '127.0.0.1')}:{setting(values, 'APP_PORT', '3000')}")
PY
)"
echo "Waiting for Open WebUI..."
i=0
until curl --fail --silent "${app_url}/health" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "Open WebUI did not become healthy. Run ./scripts/logs.sh."
    exit 1
  fi
  sleep 2
done
echo "Coco's Open WebUI is reachable at ${app_url}"
echo "After creating the first admin account, import config/coco-model.json in Workspace > Models."
