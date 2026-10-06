# Coco on Open WebUI

A small, configuration-first personal assistant deployment based on the official Open WebUI image. This project is an independent deployment configuration, **not an official Open WebUI release**.

Coco supports normal conversation, practical help, beginner-friendly coding explanations, and progressively hinted practice problems. Open WebUI supplies streaming, clearly separated messages, new chats, a persistent chat list, rename/delete controls, stop generation, response copying, responsive layouts, settings, and memory management.

## What is pinned

- Open WebUI release: `v0.11.4`
- Upstream commit: `8bd8b4fac5e059578ac0c74b3c18d11139f88b7d`
- Image: `ghcr.io/open-webui/open-webui:v0.11.4-slim`
- OpenRouter base URL: `https://openrouter.ai/api/v1`
- Default model: `nvidia/nemotron-3-ultra-550b-a55b`

The slim release is used because hosted text chat, SQLite, and local file storage work without bundled local models. No Ollama, CUDA, GPU, local LLM, local speech model, PostgreSQL, Redis, or vector database is installed.

## Privacy model

> Your chats and saved memories are stored by this local application. To generate replies, selected conversation context and enabled memories are sent to OpenRouter and the provider serving your model. This is not offline AI. Provider retention depends on the selected provider and your account/routing settings.

Stored conversation history, request context, and long-term memory are different:

1. **History** is the local chat database in the Docker volume.
2. **Request context** is the bounded selection Open WebUI sends for a reply—not the whole database.
3. **Memory** is a separate user-controlled store. Approved memories are injected with separate 2,000-character budgets.

Deleting a memory does not delete a chat. Deleting a chat does not delete exports or backups. Deleting local data cannot promise deletion from OpenRouter or the routed provider.

The API key is sent to the container as a server-side environment variable. It is not built into an image or preset and is not intentionally exposed to browser storage. A local OS or Docker administrator can still inspect container environment values.

## First start

Requirements: Docker with Docker Compose and Python 3.

```bash
git clone https://github.com/catburglarX/assistant.git
cd assistant
cp .env.example .env
chmod 600 .env
chmod +x scripts/*.sh scripts/*.py
```

Open `.env` in a text editor and enter your key after `OPENROUTER_API_KEY=`. **Do this locally; never paste the key into chat or commit it.**

Validate and start:

```bash
python3 scripts/validate.py
./scripts/start.sh
```

Open [http://localhost:3000](http://localhost:3000), create the first admin account, and use a strong unique password. Open WebUI v0.11.4 automatically persists signup as disabled once the first admin exists. Confirm this at **Admin settings → Authentication → New signups**.

In your OpenRouter account, review provider routing and data/privacy controls before chatting. Provider availability and retention can change independently of this project; do not assume zero retention.

### Import and select Coco

`start.sh` renders `config/coco-model.json` from `.env` and `config/coco-system-prompt.md`.

1. Go to **Workspace → Models**.
2. Use **Import** and choose `config/coco-model.json`.
3. Start a new chat and select **Coco**.
4. Send: `Hi Coco. Briefly introduce yourself.`

If you change `ASSISTANT_NAME`, `OPENROUTER_MODEL`, or the prompt, run:

```bash
python3 scripts/render_config.py
```

Then import the regenerated preset again. No image rebuild is needed.

## Memory

This deployment deliberately uses manual, user-controlled memory:

- Go to **Settings → Personalization → Memory**.
- Add concise confirmed facts or preferences.
- Use the item controls to edit or delete one.
- Use **Clear** to remove all personal memories.
- Disable the personal Memory toggle when you do not want memories used in a chat.
- An administrator can globally disable memory at **Admin settings → General → Features → Memories**.

Background extraction is off, and Coco's model preset explicitly withholds native memory tools. This prevents an unsolicited model tool call from writing memory. Approved memories remain available in fresh chats through Open WebUI's server-side memory context. If memory is disabled globally, v0.11.4 blocks its APIs, tools, and context injection.

For example, you can manually save “I prefer explanations before code,” “Keep replies short,” “I’m learning Python,” or a registration number you explicitly want remembered. A registration number is a personal identifier: store it only if needed, and remember that enabled memories can be sent to OpenRouter and the routed provider when relevant.

Do not save passwords, API keys, inferred sensitive traits, temporary moods, or unconfirmed assumptions as memories.

## Everyday commands

```bash
# Start
./scripts/start.sh

# Stop containers; keeps containers and data
./scripts/stop.sh

# Restart
./scripts/restart.sh

# View the last 200 log lines with best-effort key redaction
./scripts/logs.sh

# Back up the running application's data
./scripts/backup.sh
```

The application data lives in the named volume `coco-assistant_coco-data`, so chats and memories survive restarts and container recreation.

### Stop vs remove vs erase

```bash
# Stop only; data and containers remain
docker compose stop

# Remove containers/network; named volume remains
docker compose down

# DANGER: permanently delete persistent local application data.
# This is intentionally never run by a script.
docker volume rm coco-assistant_coco-data
```

Backups under `backups/` are separate files and must be deleted separately.

## Diagnostics and failures

```bash
python3 scripts/validate.py
./scripts/logs.sh 300
docker compose ps
docker stats --no-stream coco-open-webui
```

Open WebUI surfaces provider failures rather than converting them into assistant messages. Common causes:

- `401`: invalid/missing key
- `402`: insufficient OpenRouter credits
- `404`: configured model/provider unavailable
- `429`: rate limit
- timeout/interrupted stream: retry once only after checking provider status; verify no reply was already saved before retrying

Change `OPENROUTER_MODEL` in `.env`, regenerate/import the preset, and restart only when you intentionally choose another model. This project never silently substitutes a model.

## Tests

Routine tests use no API credits:

```bash
python3 -m unittest discover -s tests -v
docker compose --env-file .env config --quiet
```

The live test is opt-in and makes two small paid requests: one ordinary completion and one streaming completion.

```bash
python3 scripts/openrouter_smoke.py --live
```

It intentionally sends only `model`, `messages`, `max_tokens`, and `stream`. Tool calling is not used for memory and is therefore not enabled or probed.

Manual behavior checks:

1. Casual greeting.
2. Beginner coding question.
3. Correct Coco and verify it accepts the correction.
4. Add a preference manually; open a fresh chat and verify it is used.
5. Emotional but non-crisis message.
6. Ask “Are you human?” and “Do you have feelings?”
7. Press Stop during a long response; copy a response; rename and delete a test chat.
8. Restart and confirm a chat plus a memory remain.
9. Recreate the container with `docker compose down && docker compose up -d`; confirm the volume persists.
10. Disable memory and confirm the preference is not injected and no memory is written.

These checks demonstrate the tested conversations only; they do not prove universal safety or friendliness.

## Updating safely

1. Run `./scripts/backup.sh`.
2. Read upstream release and security notes.
3. Change the exact image tag in `docker-compose.yml`; never switch this project to `main`.
4. Re-check renamed/removed environment variables and memory behavior.
5. Run unit tests and `docker compose config --quiet`.
6. Pull and recreate:

   ```bash
   docker compose pull
   docker compose up -d
   ```

7. Repeat persistence, memory-off, chat, streaming, stop-generation, and security checks.

Rollback by restoring the old tag and running `docker compose up -d`. Database migrations may make restoring a pre-update backup necessary.

## Security notes

- The published port defaults to loopback-only `127.0.0.1:3000`.
- Authentication remains enabled; no password is hardcoded.
- Public sharing, community sharing, web search, browser URL upload, plugins, direct integrations/MCP, code execution, terminal access, automations, channels, calendars, user webhooks, audio, and image generation are disabled.
- The container is not given the Docker socket, host filesystem, privileged mode, or a public tunnel.
- Logs default to INFO with audit logging off. `logs.sh` adds best-effort redaction, but review output before sharing it.
- The upstream license is preserved in `OPEN_WEBUI_LICENSE.txt`; the UI name retains “Open WebUI”.

## Voice

Voice is intentionally disabled in this core release. The slim image contains no local Whisper or local voices. Enabling speech later requires a separately configured provider and a separate privacy review because audio may leave the computer. Text chat remains the fallback.

## Known limitations

- The Coco preset import is one manual post-signup step.
- This configuration has no custom approval UI for conversational “remember this”; use the native memory editor.
- Provider-side retention and routing are controlled outside this repository.
- Resource usage depends on your OS, Docker, browser, and Open WebUI release. Measure it locally with `docker stats`; this repository does not invent a benchmark or impose an unmeasured memory cap.
- The slim image intentionally omits local speech, local embeddings, advanced document extraction, and other heavyweight features.

## Upstream references

- Open WebUI repository and license: https://github.com/open-webui/open-webui
- Pinned release: https://github.com/open-webui/open-webui/releases/tag/v0.11.4
- Security advisories: https://github.com/open-webui/open-webui/security
- Environment variables: https://docs.openwebui.com/reference/env-configuration
- Memory: https://docs.openwebui.com/features/chat-conversations/memory
- OpenRouter model: https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b
