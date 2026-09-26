"""Embedding-based semantic similarity.

Why embeddings instead of an LLM judge: cosine similarity over a
sentence-transformer is deterministic, free and fast, so it makes a stable
regression signal. It answers "does the answer *mean* the same as the
reference?". It does NOT check truthfulness or completeness.

Known limitation: embeddings are weak on negation ("X is refundable" vs
"X is not refundable" can score above 0.8) and on missing facts. Always pair
this with faithfulness and completeness.
"""

from __future__ import annotations

from functools import lru_cache

from deepeval.test_case import LLMTestCase
from sentence_transformers import SentenceTransformer, util

from ai.evaluators.base import DeterministicMetric


@lru_cache(maxsize=2)
def load_encoder(model_name: str) -> SentenceTransformer:
    """Load (once per process) a sentence-transformers model on CPU."""
    return SentenceTransformer(model_name, device="cpu")


def cosine_similarity(a: str, b: str, model_name: str) -> float:
    """Cosine similarity of two texts' embeddings, in [-1, 1] (in practice [0, 1])."""
    encoder = load_encoder(model_name)
    emb = encoder.encode([a, b], convert_to_tensor=True, normalize_embeddings=True)
    return float(util.cos_sim(emb[0], emb[1]).item())


class SemanticSimilarityMetric(DeterministicMetric):
    """Cosine similarity between ``actual_output`` and ``expected_output``.

    Args:
        model_name: sentence-transformers model id.
        threshold: Minimum similarity that counts as a pass.
    """

    metric_name = "Semantic Similarity"

    def __init__(self, model_name: str, threshold: float = 0.7) -> None:
        """Create the SemanticSimilarityMetric; arguments are described in the class docstring."""
        super().__init__(pass_threshold=threshold)
        self.model_name = model_name
        self.evaluation_model = model_name

    def evaluate(self, test_case: LLMTestCase) -> tuple[float, str]:
        """Embed both texts and return their cosine similarity.

        Raises:
            ValueError: If the test case has no ``expected_output``.
        """
        if not test_case.expected_output:
            raise ValueError("SemanticSimilarityMetric requires expected_output on the test case")
        score = cosine_similarity(test_case.actual_output, test_case.expected_output, self.model_name)
        return score, f"cosine({self.model_name})"
