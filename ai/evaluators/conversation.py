"""Multi-turn evaluation helpers: build conversations from any bot, and check memory without a judge.

* :func:`run_conversation` drives a chat function turn by turn and returns DeepEval's
  ``ConversationalTestCase`` (the input the conversational metrics in ``MetricFactory`` need).
* :class:`RetentionProbeMetric` is a rule-based stand-in for ``KnowledgeRetentionMetric``,
  which didn't separate a remembering bot from a forgetful one on either local judge: it checks
  that a later assistant turn states facts the user gave earlier.
"""

from __future__ import annotations

from collections.abc import Callable

from deepeval.metrics import BaseConversationalMetric
from deepeval.test_case import ConversationalTestCase, Turn


def run_conversation(
    send: Callable[[str], str], user_turns: list[str], chatbot_role: str | None = None
) -> ConversationalTestCase:
    """Send each user message in order and record both sides of the conversation.

    Args:
        send: Sends one message in the *same* session and returns the assistant's reply text.
        user_turns: The user's messages.
        chatbot_role: Role description used by ``RoleAdherenceMetric``.
    """
    turns: list[Turn] = []
    for message in user_turns:
        turns.append(Turn(role="user", content=message))
        turns.append(Turn(role="assistant", content=send(message)))
    return ConversationalTestCase(turns=turns, chatbot_role=chatbot_role)


class RetentionProbeMetric(BaseConversationalMetric):
    """Scores the share of ``facts`` that a chosen assistant turn repeats (case-insensitive).

    Args:
        facts: Strings the user gave earlier, e.g. ``["4471"]`` for an order number.
        turn: Index into the assistant turns to check; ``-1`` is the last reply.
        threshold: Share of facts required to pass (default: all of them).
    """

    def __init__(self, facts: list[str], turn: int = -1, threshold: float = 1.0) -> None:
        """Create the RetentionProbeMetric; arguments are described in the class docstring."""
        self.facts = facts
        self.turn = turn
        self.threshold = threshold
        self.evaluation_model = "rule-based"
        self.include_reason = True
        self.async_mode = False
        self.strict_mode = False

    def measure(self, test_case: ConversationalTestCase, *args, **kwargs) -> float:
        """Score the chosen assistant turn; sets ``score``, ``reason`` and ``success``."""
        replies = [t.content for t in test_case.turns if t.role == "assistant"]
        text = replies[self.turn].lower() if replies else ""
        missing = [fact for fact in self.facts if fact.lower() not in text]
        self.score = (len(self.facts) - len(missing)) / len(self.facts) if self.facts else 1.0
        self.reason = f"missing {missing}" if missing else "all facts retained"
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case: ConversationalTestCase, *args, **kwargs) -> float:
        """Async entry point required by DeepEval; the check is CPU-only."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """True when the last :meth:`measure` passed."""
        return bool(self.success)

    @property
    def __name__(self) -> str:
        """Name shown in DeepEval's results table."""
        return "Retention probe"
