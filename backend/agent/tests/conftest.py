from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.core.cache import cache

from agent import claude

ANSWER = "I've spent twelve years in healthcare IT, the last eight in cardiovascular informatics."


@pytest.fixture(autouse=True)
def reset_state(db):
    """Throttle counts live in the cache; no test should inherit another's."""
    cache.clear()
    claude.reset_client()
    yield
    cache.clear()
    claude.reset_client()


@pytest.fixture
def fake_claude(monkeypatch):
    """Stand in for the Anthropic client. No test makes a real API call."""
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=ANSWER)],
        stop_reason="end_turn",
        stop_details=None,
    )
    monkeypatch.setattr(claude, "get_client", lambda: client)
    return client
