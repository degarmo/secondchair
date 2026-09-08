"""Loading and caching of the knowledge base that grounds the agent."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_knowledge_base: str | None = None


def load_knowledge_base(*, refresh: bool = False) -> str:
    """Return the knowledge base text, reading it from disk at most once.

    Pass ``refresh=True`` to force a re-read; tests use it after pointing
    ``settings.KNOWLEDGE_BASE_PATH`` at a fixture.
    """
    global _knowledge_base

    if _knowledge_base is not None and not refresh:
        return _knowledge_base

    path = settings.KNOWLEDGE_BASE_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ImproperlyConfigured(
            f"Knowledge base not readable at {path}. The interview agent has "
            "nothing to ground answers in without it."
        ) from exc

    if not text.strip():
        raise ImproperlyConfigured(f"Knowledge base at {path} is empty.")

    _knowledge_base = text
    return _knowledge_base
