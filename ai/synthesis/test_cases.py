"""AI-assisted test design: turn written requirements into structured test cases.

An LLM drafts test cases for one requirement at a time, grounded in that requirement plus the
related ones retrieved from the same document (RAG), and must answer in JSON. The draft is then
*validated*, never trusted:

* **schema**: every case parses into :class:`GeneratedTestCase` (pydantic), or it's dropped;
* **traceability**: the requirement id is set by the code, not copied from the model's text;
* **coverage**: :func:`review_suite` reports requirements with no cases, requirements that need
  a negative case but got none, duplicate titles within a requirement, and error messages the
  requirement quotes that no expected result checks.

What no check can catch is an *invented* rule (measured: llama3.2:3b proposed a "maximum login
attempts" case for a requirement that has no such limit). Generated cases are drafts for a
human reviewer, not tests to run unread.

This is the "generate test cases and test data with GenAI" workflow, with the guard-rails a QA
team needs before generated cases reach a test-management tool.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from ai.chatbot.base import ChatbotClient
from ai.prompts import default_registry

REQUIREMENTS_FILE = Path(__file__).with_name("requirements.json")


class TestCaseGenerationError(RuntimeError):
    """The model's reply held no usable test case (not JSON, or nothing valid in it)."""


class Requirement(BaseModel):
    """One requirement from ``requirements.json``."""

    id: str
    text: str
    needs_negative: bool = False


class GeneratedTestCase(BaseModel):
    """One test case as drafted by the model and validated here.

    ``type`` accepts any case ("Negative") and is normalised to lower case.
    """

    __test__ = False  # not a pytest test class, despite the name

    requirement_id: str
    title: str = Field(min_length=5)
    type: Literal["positive", "negative", "boundary"]
    steps: list[str] = Field(min_length=1)
    expected: str = Field(min_length=3)

    @field_validator("type", mode="before")
    @classmethod
    def _lower(cls, value: str) -> str:
        """Normalise ``"Negative"`` to ``"negative"``."""
        return value.strip().lower() if isinstance(value, str) else value


def load_requirements(path: Path = REQUIREMENTS_FILE) -> list[Requirement]:
    """All requirements from the JSON file."""
    return [Requirement(**r) for r in json.loads(path.read_text())["requirements"]]


def related_requirements(requirement: Requirement, requirements: list[Requirement], k: int = 2) -> list[Requirement]:
    """The ``k`` requirements most similar to ``requirement`` (BM25 keyword search), excluding itself.

    This is the retrieval half of RAG: the generator sees neighbouring rules (for example the
    other login errors) so its cases stay consistent with them.
    """
    from ai.search import BM25Retriever
    from ai.search.base import Document

    others = [r for r in requirements if r.id != requirement.id]
    retriever = BM25Retriever([Document(id=r.id, title=r.id, text=r.text) for r in others])
    ids = [hit.document.id for hit in retriever.search(requirement.text, k=k)]
    return [r for r in others if r.id in ids]


def parse_test_cases(text: str, requirement_id: str) -> tuple[list[GeneratedTestCase], list[str]]:
    """Parse the model's JSON into valid cases, plus a note for every case that was dropped.

    Accepts ``{"test_cases": [...]}`` or a bare list. The requirement id always comes from the
    caller, so a model typo can't break traceability.

    Raises:
        TestCaseGenerationError: If the reply isn't JSON or has no case list.
    """
    try:
        data = json.loads(text)
    except ValueError as error:
        raise TestCaseGenerationError(f"reply is not JSON: {error}") from error
    raw_cases = data.get("test_cases") if isinstance(data, dict) else data
    if not isinstance(raw_cases, list):
        raise TestCaseGenerationError("reply has no 'test_cases' list")

    cases, dropped = [], []
    for index, raw in enumerate(raw_cases):
        try:
            cases.append(GeneratedTestCase(**{**raw, "requirement_id": requirement_id}))
        except (TypeError, ValidationError) as error:
            dropped.append(f"case {index} dropped: {str(error).splitlines()[0]}")
    return cases, dropped


def generate_test_cases(
    chatbot: ChatbotClient, requirement: Requirement, related: list[Requirement] | None = None
) -> list[GeneratedTestCase]:
    """Ask ``chatbot`` for test cases covering ``requirement`` (JSON mode) and return the valid ones.

    Args:
        chatbot: Any :class:`ChatbotClient` (a live model, or a scripted one in unit tests).
        requirement: The requirement to cover.
        related: Other requirements given as context (for example retrieved by search).

    Raises:
        TestCaseGenerationError: If no valid case comes back.
    """
    template = default_registry().get("test_case_generator")
    context = "\n".join(f"- {r.id}: {r.text}" for r in related or []) or "(none)"
    reply = chatbot.run_prompt(
        template, json_mode=True, requirement_id=requirement.id, requirement=requirement.text, related=context
    )
    cases, _dropped = parse_test_cases(reply.text, requirement.id)
    if not cases:
        raise TestCaseGenerationError(f"no valid test case for {requirement.id}")
    return cases


@dataclass
class TestSuiteReview:
    """Coverage report for a generated suite.

    Attributes:
        uncovered: Requirement ids with no test case.
        missing_negative: Requirements flagged ``needs_negative`` without a negative case.
        duplicate_titles: ``"REQ-ID: title"`` for titles repeated within one requirement.
        unchecked_messages: ``"REQ-ID: message"`` for quoted messages no expected result contains.
        shared_titles: Titles used under more than one requirement (informational: overlap to review).
        types: Count of cases per type.
    """

    __test__ = False

    uncovered: list[str] = field(default_factory=list)
    missing_negative: list[str] = field(default_factory=list)
    duplicate_titles: list[str] = field(default_factory=list)
    unchecked_messages: list[str] = field(default_factory=list)
    shared_titles: list[str] = field(default_factory=list)
    types: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """True when every requirement is covered with the kinds of cases and checks it needs."""
        return not (self.uncovered or self.missing_negative or self.duplicate_titles or self.unchecked_messages)


def quoted_messages(requirement: Requirement) -> list[re.Pattern]:
    """Messages the requirement quotes in single quotes, as patterns; ``<Field>`` matches any text."""
    patterns = []
    for message in re.findall(r"'([^']+)'", requirement.text):
        parts = re.split(r"<[^>]+>", message)
        patterns.append(re.compile(".+".join(re.escape(part) for part in parts), re.IGNORECASE))
    return patterns


def review_suite(requirements: list[Requirement], cases: list[GeneratedTestCase]) -> TestSuiteReview:
    """Check a generated suite for coverage gaps, duplicates and unchecked error messages."""
    by_requirement: dict[str, list[GeneratedTestCase]] = {r.id: [] for r in requirements}
    for case in cases:
        by_requirement.setdefault(case.requirement_id, []).append(case)

    review = TestSuiteReview(types=dict(Counter(case.type for case in cases)))
    owners: dict[str, set[str]] = {}
    for requirement in requirements:
        mine = by_requirement[requirement.id]
        if not mine:
            review.uncovered.append(requirement.id)
            continue
        if requirement.needs_negative and not any(c.type == "negative" for c in mine):
            review.missing_negative.append(requirement.id)
        titles = Counter(c.title.strip().lower() for c in mine)
        review.duplicate_titles += [f"{requirement.id}: {t}" for t, n in titles.items() if n > 1]
        for pattern in quoted_messages(requirement):
            if not any(pattern.search(c.expected) for c in mine):
                review.unchecked_messages.append(f"{requirement.id}: {pattern.pattern}")
        for title in titles:
            owners.setdefault(title, set()).add(requirement.id)
    review.shared_titles = sorted(t for t, ids in owners.items() if len(ids) > 1)
    return review
