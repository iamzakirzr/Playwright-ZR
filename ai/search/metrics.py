"""Standard information-retrieval metrics (pure functions, no dependencies).

All functions take ``retrieved``, a ranked list of ids with the best first,
and ``relevant``, the set of ids a human judged relevant.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def precision_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Fraction of the top-k results that are relevant."""
    relevant = set(relevant)
    top = retrieved[:k]
    return sum(1 for d in top if d in relevant) / k if k else 0.0


def recall_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Fraction of all relevant documents that appear in the top k."""
    relevant = set(relevant)
    return len(relevant & set(retrieved[:k])) / len(relevant) if relevant else 0.0


def hit_rate_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """1.0 if any relevant document is in the top k, else 0.0."""
    return 1.0 if set(relevant) & set(retrieved[:k]) else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: Iterable[str]) -> float:
    """1 / rank of the first relevant hit (0 if none). Averaged over queries it is MRR."""
    relevant = set(relevant)
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Normalised Discounted Cumulative Gain with binary relevance.

    Rewards putting relevant documents *higher*. 1.0 means ideal ordering.
    """
    relevant = set(relevant)
    dcg = sum(1.0 / math.log2(rank + 1) for rank, d in enumerate(retrieved[:k], start=1) if d in relevant)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0


def mean(values: Iterable[float]) -> float:
    """Arithmetic mean that returns 0.0 for an empty input."""
    values = list(values)
    return sum(values) / len(values) if values else 0.0
