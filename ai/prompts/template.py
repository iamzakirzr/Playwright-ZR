"""Versioned prompt templates.

Prompts are code: they are versioned, validated and fingerprinted so a test
can detect an unreviewed prompt change the same way a snapshot test detects
an unreviewed UI change.
"""
from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass


class PromptError(ValueError):
    """Raised when a prompt is rendered with missing or unexpected variables."""


@dataclass(frozen=True)
class RenderedPrompt:
    """The concrete system and user messages produced by :meth:`PromptTemplate.render`."""

    system: str
    user: str


@dataclass(frozen=True)
class PromptTemplate:
    """An immutable, versioned prompt with ``$placeholder`` variables.

    ``string.Template`` substitution is single-pass: a user value that itself
    contains ``$system`` is inserted literally and never re-expanded. That
    closes off a whole class of template-injection bugs.

    Attributes:
        name: Stable identifier, e.g. ``grounded_qa``.
        version: Integer version, bumped on every behavioural change.
        system: System-message template.
        user: User-message template.
        description: What the prompt is for (shown in reports).
    """

    name: str
    version: int
    system: str
    user: str
    description: str = ""

    @property
    def variables(self) -> frozenset[str]:
        """All placeholder names used in the system and user templates."""
        names: set[str] = set()
        for text in (self.system, self.user):
            for _, named, braced, _ in string.Template.pattern.findall(text):
                if named or braced:
                    names.add(named or braced)
        return frozenset(names)

    @property
    def fingerprint(self) -> str:
        """Short SHA-256 of the template text, used for prompt-drift snapshots."""
        digest = hashlib.sha256(f"{self.system}\x00{self.user}".encode()).hexdigest()
        return digest[:16]

    def render(self, **values: object) -> RenderedPrompt:
        """Substitute ``values`` into the template.

        Args:
            **values: One value per placeholder in :attr:`variables`.

        Returns:
            A :class:`RenderedPrompt`.

        Raises:
            PromptError: If a placeholder has no value, or a value has no placeholder
                (usually a typo in the caller).
        """
        provided = set(values)
        missing = self.variables - provided
        unexpected = provided - self.variables
        if missing or unexpected:
            raise PromptError(
                f"{self.name} v{self.version}: missing={sorted(missing)} unexpected={sorted(unexpected)}"
            )
        as_text = {k: str(v) for k, v in values.items()}
        return RenderedPrompt(
            system=string.Template(self.system).substitute(as_text),
            user=string.Template(self.user).substitute(as_text),
        )
