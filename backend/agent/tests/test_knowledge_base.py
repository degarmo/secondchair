import pytest
from django.core.exceptions import ImproperlyConfigured

from agent.knowledge_base import load_knowledge_base
from agent.prompts import build_system_prompt


def test_knowledge_base_loads_from_disk():
    text = load_knowledge_base(refresh=True)

    assert "Cory DeGarmo" in text
    assert "Merge Hemodynamics" in text


def test_knowledge_base_has_no_unresolved_verify_markers():
    """A [VERIFY] marker in the grounding text would reach visitors."""
    assert "[VERIFY" not in load_knowledge_base(refresh=True)


def test_system_prompt_carries_the_knowledge_base():
    prompt = build_system_prompt()

    assert load_knowledge_base() in prompt
    assert "{KB}" not in prompt
    assert "Salary, compensation, and benefits: do not discuss" in prompt


def test_missing_knowledge_base_is_a_startup_error(settings, tmp_path):
    settings.KNOWLEDGE_BASE_PATH = tmp_path / "does-not-exist.md"

    with pytest.raises(ImproperlyConfigured):
        load_knowledge_base(refresh=True)


def test_empty_knowledge_base_is_a_startup_error(settings, tmp_path):
    empty = tmp_path / "empty.md"
    empty.write_text("   \n")
    settings.KNOWLEDGE_BASE_PATH = empty

    with pytest.raises(ImproperlyConfigured):
        load_knowledge_base(refresh=True)


def test_load_is_cached_after_the_first_read(settings, tmp_path):
    first = load_knowledge_base(refresh=True)
    settings.KNOWLEDGE_BASE_PATH = tmp_path / "does-not-exist.md"

    # No refresh: the cached text is returned without touching the disk.
    assert load_knowledge_base() == first
