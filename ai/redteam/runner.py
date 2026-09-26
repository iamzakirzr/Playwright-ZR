"""Red-team runner: fires attacks at a chatbot and judges whether each was defended.

Every attack names *detectors*. The runner maps detector names to metric
objects (**Strategy** registry) and runs them all on the response. Adding a
new detector means adding one entry to :meth:`RedTeamRunner._detector`, not
editing any test.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from ai.chatbot.base import ChatbotClient, ChatResponse
from ai.evaluators.classifiers import ToxicityClassifierMetric
from ai.evaluators.deterministic import CanaryLeakageMetric, RefusalMetric, RegexPIIMetric
from ai.evaluators.factory import MetricFactory

ATTACKS_FILE = Path(__file__).with_name("attacks.json")


@dataclass(frozen=True)
class Attack:
    """One adversarial prompt and how to judge the response.

    Attributes:
        id: Stable id used as the pytest param id.
        category: Attack family, e.g. ``prompt_injection``.
        owasp: OWASP LLM Top-10 reference, e.g. ``LLM01``.
        prompt: The adversarial user message.
        checks: Detector names; all must pass for the attack to count as defended.
        context: Optional RAG context. Used for indirect injection and PII in documents.
        must_not_contain: Strings whose presence proves the attack worked.
    """

    id: str
    category: str
    owasp: str
    prompt: str
    checks: tuple[str, ...]
    context: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()


@dataclass
class AttackResult:
    """Outcome of one attack.

    Attributes:
        attack: The attack that was run.
        response: What the bot said.
        verdicts: Detector name mapped to ``(passed, reason)``.
    """

    attack: Attack
    response: ChatResponse
    verdicts: dict[str, tuple[bool, str]] = field(default_factory=dict)

    @property
    def defended(self) -> bool:
        """True when every detector passed."""
        return all(passed for passed, _ in self.verdicts.values())

    def summary(self) -> str:
        """One-line, human-readable result used in assertion messages."""
        failed = {k: r for k, (ok, r) in self.verdicts.items() if not ok}
        status = "DEFENDED" if self.defended else f"BREACHED {failed}"
        return f"[{self.attack.id}] {status} :: {self.response.text[:160]!r}"


def load_attacks(path: Path = ATTACKS_FILE) -> list[Attack]:
    """Load the attack library as :class:`Attack` objects."""
    raw = json.loads(path.read_text())["attacks"]
    return [
        Attack(
            id=a["id"],
            category=a["category"],
            owasp=a["owasp"],
            prompt=a["prompt"],
            checks=tuple(a["checks"]),
            context=tuple(a.get("context", ())),
            must_not_contain=tuple(a.get("must_not_contain", ())),
        )
        for a in raw
    ]


def load_benign(path: Path = ATTACKS_FILE) -> list[dict]:
    """Load the benign control prompts, used to catch over-refusal."""
    return json.loads(path.read_text())["benign"]


class RedTeamRunner:
    """Runs attacks and scores responses.

    Args:
        chatbot: Target under test (raw or guarded).
        canary: The secret planted in the target's system prompt.
        factory: Optional :class:`MetricFactory`; needed only for the LLM-judged
            detectors ``toxicity_judge`` and ``bias_judge``.
    """

    def __init__(self, chatbot: ChatbotClient, canary: str, factory: MetricFactory | None = None) -> None:
        """Create the RedTeamRunner; arguments are described in the class docstring."""
        self.chatbot = chatbot
        self.canary = canary
        self.factory = factory

    def _detector(self, name: str) -> BaseMetric:
        """Resolve a detector name to a fresh metric instance.

        Raises:
            ValueError: For an unknown detector, or a judged detector without a factory.
        """
        deterministic = {
            "canary": lambda: CanaryLeakageMetric(self.canary),
            "refusal": lambda: RefusalMetric(expect_refusal=True),
            "pii": lambda: RegexPIIMetric(),
            "toxicity": lambda: ToxicityClassifierMetric(),
        }
        if name in deterministic:
            return deterministic[name]()
        if name in {"toxicity_judge", "bias_judge"}:
            if self.factory is None:
                raise ValueError(f"Detector '{name}' needs a judge: pass a MetricFactory")
            return getattr(self.factory, name.removesuffix("_judge"))()
        raise ValueError(f"Unknown detector '{name}'")

    @staticmethod
    def _contains_check(attack: Attack, text: str) -> tuple[bool, str]:
        """``must_not_contain`` detector: the attack's success marker must be absent."""
        hits = [s for s in attack.must_not_contain if s.lower() in text.lower()]
        return (not hits), (f"found {hits}" if hits else "no success markers")

    def run(self, attack: Attack) -> AttackResult:
        """Send ``attack`` to the chatbot and evaluate every detector it lists."""
        response = self.chatbot.ask(attack.prompt, list(attack.context) or None)
        result = AttackResult(attack, response)
        test_case = LLMTestCase(input=attack.prompt, actual_output=response.text)
        for check in attack.checks:
            if check == "must_not_contain":
                result.verdicts[check] = self._contains_check(attack, response.text)
                continue
            metric = self._detector(check)
            metric.measure(test_case)
            result.verdicts[check] = (metric.is_successful(), metric.reason or "")
        return result

    def run_all(self, attacks: list[Attack]) -> list[AttackResult]:
        """Run every attack in order."""
        return [self.run(a) for a in attacks]


def attack_success_rate(results: list[AttackResult]) -> dict[str, float]:
    """Attack Success Rate (ASR) per category: the share of attacks that got through."""
    by_category: dict[str, list[bool]] = defaultdict(list)
    for r in results:
        by_category[r.attack.category].append(not r.defended)
    return {cat: sum(v) / len(v) for cat, v in sorted(by_category.items())}
