#!/usr/bin/env python3
"""Opt-in, low-token OpenRouter non-streaming and streaming smoke test."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from project import read_env, setting

URL = "https://openrouter.ai/api/v1/chat/completions"


def payload(model: str, stream: bool) -> dict:
    # Deliberately omit reasoning and sampling options. The smoke test checks
    # only basic chat and streaming with a small response budget.
    return {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: Mira smoke test OK"}],
        "max_tokens": 32,
        "stream": stream,
    }


def parse_sse(lines) -> str:
    chunks: list[str] = []
    for raw in lines:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        event = json.loads(data)
        choices = event.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("stream event did not include choices")
        chunks.append(choices[0].get("delta", {}).get("content") or "")
    return "".join(chunks)


def request_completion(key: str, model: str, stream: bool) -> str:
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload(model, stream)).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        if not stream:
            body = json.load(response)
            return body["choices"][0]["message"]["content"]
        return parse_sse(response)


def friendly_http_error(error: urllib.error.HTTPError) -> str:
    labels = {
        401: "invalid or missing API key",
        402: "insufficient OpenRouter credits",
        404: "configured model or endpoint unavailable",
        429: "rate limited by OpenRouter/provider",
    }
    return labels.get(error.code, f"provider HTTP error {error.code}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="required confirmation: makes two small paid API requests",
    )
    args = parser.parse_args()
    if not args.live:
        print("No request made. Re-run with --live to spend a small amount of OpenRouter credit.")
        return 2
    values = read_env()
    key = setting(values, "OPENROUTER_API_KEY")
    model = setting(values, "OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    if not key:
        print("ERROR: OPENROUTER_API_KEY is missing from .env.", file=sys.stderr)
        return 1
    try:
        ordinary = request_completion(key, model, False)
        streamed = request_completion(key, model, True)
    except urllib.error.HTTPError as error:
        print(f"ERROR: {friendly_http_error(error)}. Request did not succeed.", file=sys.stderr)
        return 1
    except (TimeoutError, urllib.error.URLError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: malformed, timed out, or interrupted provider response: {error}", file=sys.stderr)
        return 1
    print(f"ordinary: {ordinary}")
    print(f"streaming: {streamed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
