"""Embedding-based semantic similarity as a DeepEval metric.

Why embeddings rather than an LLM judge here: cosine similarity over a
sentence-transformer is deterministic, free and fast, so it is a stable
regression signal. It answers "does the answer *mean* the same as the
reference?" — it does NOT check truthfulness (that is faithfulness's job).

Known limitation: embeddings are weak at negation ("X is refundable" vs
"X is not refundable" can score > 0.8). Pair this metric with faithfulness,
never use it alone to gate factual correctness.
"""
from __future__ import annotations

from functools import lru_cache

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from sentence_transformers import SentenceTransformer, util


@lru_cache(maxsize=2)
def _load_encoder(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name, device="cpu")


def cosine_similarity(a: str, b: str, model_name: str) -> float:
    encoder = _load_encoder(model_name)
    emb = encoder.encode([a, b], convert_to_tensor=True, normalize_embeddings=True)
    return float(util.cos_sim(emb[0], emb[1]).item())


class SemanticSimilarityMetric(BaseMetric):
    def __init__(self, model_name: str, threshold: float = 0.7) -> None:
        self.model_name = model_name
        self.threshold = threshold
        self.include_reason = True
        self.async_mode = False
        self.strict_mode = False
        self.evaluation_model = model_name
        self.score = None
        self.reason = None
        self.success = None
        self.error = None

    def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        if not test_case.expected_output:
            raise ValueError("SemanticSimilarityMetric requires expected_output on the test case")
        self.score = round(cosine_similarity(test_case.actual_output, test_case.expected_output, self.model_name), 4)
        self.success = self.score >= self.threshold
        self.reason = (
            f"cosine({self.model_name}) = {self.score} "
            f"{'>=' if self.success else '<'} threshold {self.threshold}"
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return bool(self.success)

    @property
    def __name__(self):
        return "Semantic Similarity"
