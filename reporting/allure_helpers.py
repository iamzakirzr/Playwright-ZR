"""Thin helpers over allure-pytest so reports read like documentation.

* ``@step("Log in as {username}")`` on page-object methods gives each report a
  human-readable, nested timeline, with arguments filled in.
* ``attach_llm_exchange`` records every prompt/answer an AI test used, so a
  failed evaluation shows *what the model said*, not only a score.
* When allure-pytest isn't installed, every helper is a no-op, so the framework
  still runs without it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

try:  # pragma: no cover - exercised implicitly by every run
    import allure

    _ENABLED = True
except ImportError:  # pragma: no cover
    allure = None
    _ENABLED = False


def step(title: str) -> Callable[[F], F]:
    """Decorator marking a function as a report step; ``{arg}`` placeholders are filled from its arguments."""
    if _ENABLED:
        return allure.step(title)
    return lambda fn: fn


def attach_text(name: str, text: str) -> None:
    """Attach plain text to the current test."""
    if _ENABLED:
        allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_json(name: str, data: Any) -> None:
    """Attach pretty-printed JSON to the current test."""
    if _ENABLED:
        allure.attach(json.dumps(data, indent=2, default=str), name=name, attachment_type=allure.attachment_type.JSON)


def attach_png(name: str, png: bytes) -> None:
    """Attach a PNG (a screenshot or a visual diff) to the current test."""
    if _ENABLED:
        allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)


def attach_llm_exchange(
    question: str, answer: str, *, model: str = "", context: list[str] | None = None, **telemetry: Any
) -> None:
    """Attach one LLM call (question, context, answer, model, latency, tokens) as a JSON record."""
    attach_json(
        f"LLM: {question[:60]}",
        {"model": model, "question": question, "context": context or [], "answer": answer, **telemetry},
    )
