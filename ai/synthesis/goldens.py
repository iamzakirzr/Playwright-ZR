"""Synthetic goldens: generate question/answer pairs from documents, then *gate* them.

Writing golden datasets by hand is slow, so DeepEval's ``Synthesizer`` (like Ragas' testset
generator) asks an LLM to write them from your documents. The catch: a generator LLM
hallucinates too. Measured with llama3.2:3b on this repo's policy corpus, one of two goldens had
an expected answer claiming items are "eligible for a refund or exchange", which the source
never says. A bot that answers faithfully would then *fail* against that golden.

So every synthetic golden passes a quality gate before it's used:

* **complete**: it has a question, an expected answer and its source context;
* **not copied**: the question isn't lifted verbatim from the context (tests nothing);
* **unique**: no near-duplicate question already accepted (embedding similarity);
* **grounded**: the expected answer is faithful to the context (DeepEval ``FaithfulnessMetric``,
  a judged check this repo has calibrated for the 3B judge). Optional, since it needs a model.

Rejected goldens are kept with their reasons, so a human can review what the generator got wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deepeval.dataset import Golden
from deepeval.metrics import FaithfulnessMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase

from ai.evaluators import cosine_similarity, rouge_scores


def synthesize_goldens(contexts: list[list[str]], model: DeepEvalBaseLLM, per_context: int = 1) -> list[Golden]:
    """Generate goldens from ``contexts`` with DeepEval's ``Synthesizer`` and a local model.

    Evolutions (which rewrite questions to be harder) are off and quality retries limited to one,
    because each extra step is another slow CPU call; the quality gate below does the filtering.

    Args:
        contexts: One list of passages per golden group (usually one passage each).
        model: DeepEval model used both to write and to critique the goldens.
        per_context: Goldens to request per context.
    """
    from deepeval.synthesizer import Synthesizer
    from deepeval.synthesizer.config import EvolutionConfig, FiltrationConfig

    synthesizer = Synthesizer(
        model=model,
        async_mode=False,
        filtration_config=FiltrationConfig(critic_model=model, max_quality_retries=1),
        evolution_config=EvolutionConfig(num_evolutions=0),
    )
    return synthesizer.generate_goldens_from_contexts(
        contexts=contexts, max_goldens_per_context=per_context, include_expected_output=True, _send_data=False
    )


@dataclass
class GoldenReview:
    """The gate's verdict on one golden.

    Attributes:
        golden: The golden reviewed.
        problems: Why it was rejected; empty means accepted.
    """

    golden: Golden
    problems: list[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        """True when no check found a problem."""
        return not self.problems


class GoldenQualityGate:
    """Filters synthetic goldens before they become test data.

    Args:
        embedding_model: Sentence-transformers model for duplicate detection.
        judge: Optional DeepEval model; when given, expected answers must be faithful to the context.
        duplicate_similarity: Questions at least this similar count as duplicates.
        copy_rouge: Questions whose ROUGE-L precision against the context reaches this are "copied".
        faithfulness_threshold: Minimum faithfulness of the expected answer.
    """

    def __init__(
        self,
        embedding_model: str,
        judge: DeepEvalBaseLLM | None = None,
        duplicate_similarity: float = 0.9,
        copy_rouge: float = 0.9,
        faithfulness_threshold: float = 0.7,
    ) -> None:
        """Create the GoldenQualityGate; arguments are described in the class docstring."""
        self.embedding_model = embedding_model
        self.judge = judge
        self.duplicate_similarity = duplicate_similarity
        self.copy_rouge = copy_rouge
        self.faithfulness_threshold = faithfulness_threshold

    def review(self, goldens: list[Golden]) -> list[GoldenReview]:
        """Review goldens in order; a golden is a duplicate only of an earlier *accepted* one."""
        reviews: list[GoldenReview] = []
        accepted_questions: list[str] = []
        for golden in goldens:
            problems = self._structural_problems(golden)
            if not problems:
                problems += self._duplicate_problems(golden.input, accepted_questions)
            if not problems and self.judge is not None:
                problems += self._grounding_problems(golden)
            reviews.append(GoldenReview(golden, problems))
            if not problems:
                accepted_questions.append(golden.input)
        return reviews

    def accepted(self, goldens: list[Golden]) -> list[Golden]:
        """Only the goldens that passed every check."""
        return [r.golden for r in self.review(goldens) if r.accepted]

    # -- checks ---------------------------------------------------------------
    def _structural_problems(self, golden: Golden) -> list[str]:
        """Missing fields, or a question copied from the context."""
        problems = []
        if not (golden.input or "").strip():
            problems.append("empty question")
        if not (golden.expected_output or "").strip():
            problems.append("no expected answer")
        if not golden.context:
            problems.append("no source context")
        if not problems:
            context = " ".join(golden.context)
            # Precision, not F-measure: a question lifted from one sentence of a long context has
            # low recall against the whole context, so F would hide the copy.
            if rouge_scores(golden.input, context, measure="precision")["rougeL"] >= self.copy_rouge:
                problems.append("question copied from the context")
        return problems

    def _duplicate_problems(self, question: str, accepted: list[str]) -> list[str]:
        """Near-duplicate of an already accepted question."""
        for earlier in accepted:
            if cosine_similarity(question, earlier, self.embedding_model) >= self.duplicate_similarity:
                return [f"duplicate of: {earlier!r}"]
        return []

    def _grounding_problems(self, golden: Golden) -> list[str]:
        """Expected answer contains claims the context doesn't support."""
        metric = FaithfulnessMetric(threshold=self.faithfulness_threshold, model=self.judge, async_mode=False)
        metric.measure(LLMTestCase(input=golden.input, actual_output=golden.expected_output, retrieval_context=golden.context))
        if metric.score < self.faithfulness_threshold:
            return [f"expected answer not grounded (faithfulness {metric.score:.2f}): {metric.reason}"]
        return []
