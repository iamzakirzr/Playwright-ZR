"""Self-healing locators: when a page-object selector breaks, ask an LLM for a replacement.

Resolution order (Chain of Responsibility)::

    1. current selector  ── matches exactly one element? ──▶ use it
    2. healing cache     ── a healed selector for this key still matches? ──▶ use it
    3. LLM healer        ── candidates from page context, each validated ──▶ first unique match
                            └─ saved to the JSON cache (observability + no second LLM call)
    4. nothing works     ──▶ LocatorHealingError (the test fails loudly, never guesses)

Two rules keep this safe:

* **Validate, never trust.** A candidate is used only if it matches exactly one
  element on the live page. An LLM that invents a selector changes nothing.
* **Context engineering.** The LLM gets only the interactive elements (inputs,
  buttons, links...), not the whole DOM, which keeps prompts small and answers focused.

Every heal is recorded in the cache file. Treat it as a to-do list: a healed
locator means the page object needs updating, not that the problem is gone.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from playwright.sync_api import Locator, Page

log = logging.getLogger(__name__)

#: JavaScript that returns the outerHTML of interactive elements only (context engineering).
_INTERACTIVE_HTML_JS = """
(maxChars) => {
  const els = document.querySelectorAll('input, button, a, select, textarea, [role], label, [data-test], [data-testid]');
  const parts = [];
  let size = 0;
  for (const el of els) {
    const clone = el.cloneNode(false);
    let html = clone.outerHTML;
    const text = (el.innerText || '').trim().slice(0, 40);
    if (text && !html.includes(text)) html = html.replace(/<\\/[a-z]+>$/, '') + text;
    if (size + html.length > maxChars) break;
    parts.push(html);
    size += html.length;
  }
  return parts.join('\\n');
}
"""


class LocatorHealingError(AssertionError):
    """No working selector could be found, even after healing."""


class LocatorHealer(Protocol):
    """Anything that proposes replacement selectors (an LLM, a heuristic, a test double)."""

    def suggest(self, description: str, broken_selector: str, html: str) -> list[str]:
        """Return candidate CSS selectors, best first."""


@dataclass
class HealedLocator:
    """One cache entry: which selector replaced which, where and when."""

    key: str
    original: str
    healed: str
    url: str
    healed_at: str


class HealingCache:
    """Persistent JSON cache of healed selectors, keyed by page-object element name.

    Args:
        path: JSON file to read and write. Created on first save.
    """

    def __init__(self, path: Path) -> None:
        """Load existing entries from ``path`` if it exists."""
        self.path = Path(path)
        self._entries: dict[str, HealedLocator] = {}
        if self.path.exists():
            for key, value in json.loads(self.path.read_text()).items():
                self._entries[key] = HealedLocator(**value)

    def get(self, key: str) -> HealedLocator | None:
        """The healed entry for ``key``, if any."""
        return self._entries.get(key)

    def put(self, entry: HealedLocator) -> None:
        """Store an entry and write the whole cache to disk."""
        self._entries[entry.key] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: asdict(v) for k, v in self._entries.items()}, indent=2))

    def __len__(self) -> int:
        """Number of healed locators recorded."""
        return len(self._entries)


class LlmLocatorHealer:
    """Healer backed by any :class:`~ai.chatbot.ChatbotClient` using the ``locator_healer`` prompt.

    Args:
        chatbot: The model to ask (a local Ollama model in this framework).
    """

    def __init__(self, chatbot) -> None:
        """Keep the chatbot and load the prompt from the registry."""
        from ai.prompts import default_registry

        self.chatbot = chatbot
        self.prompt = default_registry().get("locator_healer")

    def suggest(self, description: str, broken_selector: str, html: str) -> list[str]:
        """Ask for JSON ``{"candidates": [...]}`` and return the selectors (an empty list on bad output)."""
        reply = self.chatbot.run_prompt(
            self.prompt, json_mode=True, description=description, selector=broken_selector, html=html
        ).text
        try:
            candidates = json.loads(reply).get("candidates", [])
        except (json.JSONDecodeError, AttributeError):
            return []
        return [c for c in candidates if isinstance(c, str) and c.strip()]


class SelfHealingLocator:
    """A page-object element that heals itself when its selector breaks.

    Args:
        page: The Playwright page.
        key: Stable element name used as the cache key, e.g. ``"LoginPage.login_button"``.
        selector: The page object's current CSS selector.
        description: Human description the healer uses, e.g. ``"the Login submit button"``.
        healer: Proposes replacement selectors.
        cache: Where healed selectors are stored.
        max_html_chars: Size budget for the page context sent to the healer.
    """

    def __init__(
        self,
        page: Page,
        key: str,
        selector: str,
        description: str,
        healer: LocatorHealer,
        cache: HealingCache,
        max_html_chars: int = 6000,
    ) -> None:
        """Store configuration; nothing touches the page until :meth:`resolve`."""
        self.page = page
        self.key = key
        self.selector = selector
        self.description = description
        self.healer = healer
        self.cache = cache
        self.max_html_chars = max_html_chars
        #: How the last resolve succeeded: "current", "cache" or "healed".
        self.resolved_by: str | None = None

    def _unique(self, selector: str) -> Locator | None:
        """The locator if ``selector`` is valid CSS matching exactly one element, else None."""
        try:
            locator = self.page.locator(selector)
            return locator if locator.count() == 1 else None
        except Exception:  # noqa: BLE001 - invalid selector syntax from the LLM
            return None

    def page_context(self) -> str:
        """Interactive-element HTML sent to the healer (bounded by ``max_html_chars``)."""
        html = self.page.evaluate(_INTERACTIVE_HTML_JS, self.max_html_chars)
        return re.sub(r"\s+", " ", html) if len(html) > self.max_html_chars else html

    def resolve(self) -> Locator:
        """Return a working locator, healing if needed (see the module docstring for the order).

        Raises:
            LocatorHealingError: If the current, cached and suggested selectors all fail.
        """
        if (locator := self._unique(self.selector)) is not None:
            self.resolved_by = "current"
            return locator

        cached = self.cache.get(self.key)
        if cached and (locator := self._unique(cached.healed)) is not None:
            self.resolved_by = "cache"
            return locator

        candidates = self.healer.suggest(self.description, self.selector, self.page_context())
        for candidate in candidates:
            if (locator := self._unique(candidate)) is not None:
                self.cache.put(
                    HealedLocator(
                        key=self.key,
                        original=self.selector,
                        healed=candidate,
                        url=self.page.url,
                        healed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    )
                )
                log.warning("Self-healed %s: %r -> %r (update the page object)", self.key, self.selector, candidate)
                self.resolved_by = "healed"
                return locator

        raise LocatorHealingError(
            f"{self.key}: selector {self.selector!r} is broken and no candidate matched uniquely: {candidates}"
        )
