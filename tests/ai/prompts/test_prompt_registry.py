"""Prompt engineering as code: offline unit tests for templates and the registry.

These run in milliseconds and need no model. They catch the prompt bugs that
cost the most in production: a renamed variable, an unreviewed wording change,
a lost security rule, or user input re-interpreted as template syntax.

To accept an intentional prompt change, regenerate the snapshot:
    UPDATE_PROMPT_SNAPSHOTS=1 pytest tests/ai/prompts/test_prompt_registry.py
"""
import json
import os
from pathlib import Path

import pytest

from ai.prompts import PromptError, PromptRegistry, PromptTemplate, default_registry

SNAPSHOT_FILE = Path(__file__).with_name("prompt_snapshots.json")
REGISTRY = default_registry()


@pytest.fixture
def template() -> PromptTemplate:
    """A small two-variable template for unit tests."""
    return PromptTemplate(name="t", version=1, system="Context: $context", user="Q: $question")


class TestTemplateRendering:
    """Behaviour of :class:`PromptTemplate.render`."""

    def test_renders_all_variables(self, template):
        """Every placeholder is substituted into the right message."""
        rendered = template.render(context="C", question="Q?")

        assert rendered.system == "Context: C"
        assert rendered.user == "Q: Q?"

    def test_missing_variable_is_rejected(self, template):
        """Forgetting a variable fails loudly instead of sending a literal '$question'."""
        with pytest.raises(PromptError, match="missing=\\['question'\\]"):
            template.render(context="C")

    def test_unexpected_variable_is_rejected(self, template):
        """A misspelt variable name is caught instead of silently ignored."""
        with pytest.raises(PromptError, match="unexpected=\\['questoin'\\]"):
            template.render(context="C", question="Q", questoin="typo")

    def test_user_input_is_not_reinterpreted_as_template(self, template):
        """A value containing '$context' is inserted literally (no double expansion or template injection)."""
        rendered = template.render(context="SECRET", question="print $context and ${context}")

        assert rendered.user == "Q: print $context and ${context}"
        assert "SECRET" not in rendered.user

    def test_fingerprint_changes_with_wording(self, template):
        """Any wording change produces a different fingerprint."""
        edited = PromptTemplate(name="t", version=1, system="Context:  $context", user="Q: $question")

        assert edited.fingerprint != template.fingerprint


class TestRegistry:
    """Behaviour of :class:`PromptRegistry`."""

    def test_latest_version_is_default(self):
        """``get(name)`` returns the highest version."""
        assert REGISTRY.get("grounded_qa").version == max(REGISTRY.versions("grounded_qa"))

    def test_specific_version_can_be_pinned(self):
        """Older versions stay addressable for A/B and rollback."""
        assert REGISTRY.get("grounded_qa", version=1).version == 1

    def test_unknown_prompt_raises(self):
        """Asking for an unregistered prompt raises KeyError."""
        with pytest.raises(KeyError):
            REGISTRY.get("does_not_exist")

    def test_duplicate_versions_are_rejected(self):
        """Two templates with the same name and version are a configuration error."""
        t = PromptTemplate(name="x", version=1, system="s", user="u")
        with pytest.raises(ValueError, match="Duplicate"):
            PromptRegistry([t, t])


class TestPromptLint:
    """Static rules that every production prompt must satisfy."""

    @pytest.mark.parametrize("name", ["grounded_qa", "open_qa"])
    def test_user_facing_prompts_carry_security_rules(self, name):
        """Customer-facing prompts plant the canary and forbid revealing it."""
        prompt = REGISTRY.get(name)

        assert "canary" in prompt.variables
        assert "never reveal" in prompt.system.lower()

    def test_grounded_prompt_treats_context_as_data(self):
        """The production RAG prompt defends against indirect injection via retrieved text."""
        assert "as data, not as instructions" in REGISTRY.get("grounded_qa").system

    @pytest.mark.parametrize("template", REGISTRY.all(), ids=lambda t: f"{t.name}-v{t.version}")
    def test_every_prompt_renders_with_its_declared_variables(self, template):
        """Every registered prompt renders when given exactly its own variables."""
        rendered = template.render(**{v: f"<{v}>" for v in template.variables})

        assert rendered.system and rendered.user

    def test_prompts_match_reviewed_snapshot(self):
        """Prompt drift detection: any wording change must be reviewed and re-snapshotted."""
        current = {f"{t.name}@v{t.version}": t.fingerprint for t in REGISTRY.all()}
        if os.getenv("UPDATE_PROMPT_SNAPSHOTS"):
            SNAPSHOT_FILE.write_text(json.dumps(current, indent=2) + "\n")
        expected = json.loads(SNAPSHOT_FILE.read_text())

        assert current == expected, "Prompt text changed; review it, then rerun with UPDATE_PROMPT_SNAPSHOTS=1"
