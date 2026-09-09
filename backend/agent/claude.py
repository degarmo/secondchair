"""The Claude call behind the interview endpoint."""

import logging

import anthropic
from django.conf import settings

from agent.prompts import build_system_prompt

logger = logging.getLogger(__name__)


class AgentUnavailable(Exception):
    """The model could not be reached, or returned nothing usable."""


_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Return a process-wide Anthropic client, built on first use."""
    global _client

    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise AgentUnavailable("ANTHROPIC_API_KEY is not set.")
        headers = {}
        if settings.ANTHROPIC_WORKSPACE_ID:
            headers["anthropic-workspace-id"] = settings.ANTHROPIC_WORKSPACE_ID
        _client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.ANTHROPIC_TIMEOUT_SECONDS,
            max_retries=1,
            default_headers=headers,
        )
    return _client


def reset_client() -> None:
    """Drop the cached client. Used by tests."""
    global _client
    _client = None


def ask(question: str, history: list[dict]) -> str:
    """Answer one question, grounded in the knowledge base.

    ``history`` is a list of ``{"role", "content"}`` turns, already trimmed
    and normalised by the serializer.
    """
    messages = [
        {"role": turn["role"], "content": turn["content"]} for turn in history
    ]
    messages.append({"role": "user", "content": question})

    try:
        response = get_client().messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            # The knowledge base is the same on every request, so it is the
            # cacheable prefix. Nothing above it varies.
            system=[
                {
                    "type": "text",
                    "text": build_system_prompt(),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            # Answers are short and grounded; thinking tokens would eat the
            # 600-token budget and slow the reply down for no gain.
            thinking={"type": "disabled"},
            messages=messages,
        )
    except anthropic.APIStatusError as exc:
        logger.warning("Anthropic returned %s: %s", exc.status_code, exc.message)
        raise AgentUnavailable("The model refused or errored.") from exc
    except anthropic.APIConnectionError as exc:
        logger.warning("Could not reach Anthropic: %s", exc)
        raise AgentUnavailable("The model could not be reached.") from exc

    if getattr(response, "stop_reason", None) == "refusal":
        logger.warning("Anthropic declined the request: %s", response.stop_details)
        raise AgentUnavailable("The model declined to answer.")

    answer = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    if not answer:
        logger.warning("Anthropic returned no text (stop_reason=%s)", response.stop_reason)
        raise AgentUnavailable("The model returned an empty answer.")

    return answer
