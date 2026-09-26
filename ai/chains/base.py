"""Prompt-chaining primitives.

A chain is an ordered list of :class:`ChainStep` objects that read from and
write to a shared :class:`ChainState` (**Pipeline / Chain of
Responsibility**). Each step records a :class:`StepTrace`, so tests can check
every link on its own, not only the final answer. In multi-step LLM systems
most bugs sit between steps: a misrouted intent, a lossy query rewrite, an
empty retrieval.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ChainError(RuntimeError):
    """A step failed. ``step`` names it, so failures point at the broken link.

    Args:
        step: Name of the step that failed.
        cause: The original exception.
    """

    def __init__(self, step: str, cause: Exception) -> None:
        """Create the ChainError; arguments are described in the class docstring."""
        super().__init__(f"Chain step '{step}' failed: {cause}")
        self.step = step
        self.cause = cause


@dataclass
class StepTrace:
    """What one step saw and produced, for debugging and assertions."""

    step: str
    output: Any
    latency_ms: float


@dataclass
class ChainState:
    """Mutable blackboard passed from step to step.

    Attributes:
        question: Original user input (never modified).
        intent: Label set by the routing step.
        query: Search query produced by the rewrite step.
        documents: Passages retrieved for the query.
        document_ids: Ids of those passages, in rank order.
        answer: Final answer text.
        halted: Set by a step to stop the chain early (for example, off-topic input).
        trace: One :class:`StepTrace` per executed step.
    """

    question: str
    intent: str | None = None
    query: str | None = None
    documents: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    answer: str | None = None
    halted: bool = False
    trace: list[StepTrace] = field(default_factory=list)

    @property
    def executed_steps(self) -> list[str]:
        """Names of the steps that actually ran, in order."""
        return [t.step for t in self.trace]


class ChainStep(ABC):
    """One link in a chain. Subclasses implement :meth:`run` and set :attr:`name`."""

    name: str = "step"

    @abstractmethod
    def run(self, state: ChainState) -> Any:
        """Read from and update ``state``; return the step's main output (recorded in the trace)."""


class Chain:
    """Runs steps in order, records a trace, and stops when a step sets ``halted``.

    Args:
        steps: The steps, executed in list order.
    """

    def __init__(self, steps: list[ChainStep]) -> None:
        """Create the Chain; arguments are described in the class docstring."""
        if not steps:
            raise ValueError("A chain needs at least one step")
        self.steps = steps

    def run(self, question: str) -> ChainState:
        """Execute the chain for ``question``.

        Raises:
            ChainError: Wrapping any exception, tagged with the failing step's name.
        """
        state = ChainState(question=question)
        for step in self.steps:
            started = time.perf_counter()
            try:
                output = step.run(state)
            except Exception as exc:  # noqa: BLE001 - re-raised with context
                raise ChainError(step.name, exc) from exc
            state.trace.append(StepTrace(step.name, output, (time.perf_counter() - started) * 1000))
            if state.halted:
                break
        return state
