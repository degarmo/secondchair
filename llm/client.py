"""Thin wrapper over the Anthropic SDK.

Everything that talks to Claude goes through ``complete_json`` so that the
model id, effort, and JSON-schema enforcement are set in exactly one place.
"""

import json

import anthropic
from django.conf import settings


class LLMUnavailable(RuntimeError):
    """No API key configured, or the API could not be reached."""


_client = None


def get_client():
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise LLMUnavailable(
                "ANTHROPIC_API_KEY is not set. Add it to .env."
            )
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def complete_json(*, system, user, schema, effort="high", max_tokens=16000):
    """One request, one JSON object back, validated against ``schema``.

    ``output_config.format`` guarantees the response is a single text block
    of schema-conforming JSON, so callers can json.loads without guarding.
    """
    client = get_client()
    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            thinking={"type": "adaptive"},
            output_config={
                "effort": effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        )
    except anthropic.APIStatusError as exc:
        raise LLMUnavailable(f"Claude API error {exc.status_code}") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMUnavailable("Could not reach the Claude API.") from exc

    if response.stop_reason == "refusal":
        raise LLMUnavailable("Claude declined to respond to this request.")

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
