"""Prompt registry: the single source of truth for every prompt the app sends."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ai.prompts.template import PromptTemplate

LIBRARY_FILE = Path(__file__).with_name("library.json")


class PromptRegistry:
    """Holds every :class:`PromptTemplate`, keyed by name and version.

    Args:
        templates: The templates to register.

    Raises:
        ValueError: If two templates share a name and version.
    """

    def __init__(self, templates: list[PromptTemplate]) -> None:
        """Create the PromptRegistry; arguments are described in the class docstring."""
        self._templates: dict[tuple[str, int], PromptTemplate] = {}
        for template in templates:
            key = (template.name, template.version)
            if key in self._templates:
                raise ValueError(f"Duplicate prompt {key}")
            self._templates[key] = template

    @classmethod
    def from_file(cls, path: Path = LIBRARY_FILE) -> PromptRegistry:
        """Load templates from a JSON file shaped like ``library.json``."""
        data = json.loads(path.read_text())
        return cls([PromptTemplate(**entry) for entry in data["prompts"]])

    def names(self) -> list[str]:
        """Sorted, de-duplicated prompt names."""
        return sorted({name for name, _ in self._templates})

    def versions(self, name: str) -> list[int]:
        """All registered versions of ``name``, oldest first."""
        return sorted(v for n, v in self._templates if n == name)

    def get(self, name: str, version: int | None = None) -> PromptTemplate:
        """Return a template; the latest version when ``version`` is None.

        Raises:
            KeyError: If the name or version is not registered.
        """
        versions = self.versions(name)
        if not versions:
            raise KeyError(f"Unknown prompt '{name}'")
        chosen = versions[-1] if version is None else version
        return self._templates[(name, chosen)]

    def all(self) -> list[PromptTemplate]:
        """Every registered template, ordered by (name, version)."""
        return [self._templates[k] for k in sorted(self._templates)]


@lru_cache(maxsize=1)
def default_registry() -> PromptRegistry:
    """The registry built from the bundled ``library.json`` (cached)."""
    return PromptRegistry.from_file()
