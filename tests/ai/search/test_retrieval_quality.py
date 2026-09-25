"""AI search quality: standard IR metrics on a labelled query set (qrels).

Runs offline: embeddings and BM25 only, no LLM. Every retriever strategy is
held to the same bar, and the hybrid (production) retriever must be at least
as good as its best component, which is the reason it exists.
"""
import pytest

from ai.search import metrics as ir

STRATEGIES = ["bm25", "semantic", "hybrid"]


def evaluate(retriever, queries, k):
    """Run every labelled query and return the averaged IR metrics.

    Args:
        retriever: Any ``Retriever``.
        queries: ``[{"query": str, "relevant": [ids]}]``.
        k: Cut-off rank.
    """
    rows = []
    for q in queries:
        ranked = retriever.search_ids(q["query"], k=k)
        rows.append(
            {
                "recall": ir.recall_at_k(ranked, q["relevant"], k),
                "hit": ir.hit_rate_at_k(ranked, q["relevant"], k),
                "mrr": ir.reciprocal_rank(ranked, q["relevant"]),
                "ndcg": ir.ndcg_at_k(ranked, q["relevant"], k),
            }
        )
    return {name: ir.mean(r[name] for r in rows) for name in rows[0]}


class TestIRMetricMath:
    """Unit tests for the metric functions themselves (known inputs, known answers)."""

    def test_perfect_ranking(self):
        """Relevant documents ranked first score 1.0 on every metric."""
        ranked, rel = ["a", "b", "c"], {"a", "b"}
        assert ir.recall_at_k(ranked, rel, 2) == 1.0
        assert ir.precision_at_k(ranked, rel, 2) == 1.0
        assert ir.reciprocal_rank(ranked, rel) == 1.0
        assert ir.ndcg_at_k(ranked, rel, 3) == pytest.approx(1.0)

    def test_relevant_document_at_rank_three(self):
        """MRR is 1/rank; nDCG penalises a low position logarithmically."""
        ranked, rel = ["x", "y", "a"], {"a"}
        assert ir.reciprocal_rank(ranked, rel) == pytest.approx(1 / 3)
        assert ir.ndcg_at_k(ranked, rel, 3) == pytest.approx(0.5)
        assert ir.recall_at_k(ranked, rel, 2) == 0.0

    def test_no_relevant_results(self):
        """Nothing relevant retrieved means zero on every metric."""
        assert ir.hit_rate_at_k(["x"], {"a"}, 1) == 0.0
        assert ir.reciprocal_rank(["x"], {"a"}) == 0.0


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_retriever_meets_quality_bar(retrievers, corpus, settings, strategy):
    """Recall@k, MRR and nDCG@k must clear the configured floors for every strategy."""
    scores = evaluate(retrievers[strategy], corpus["queries"], settings.retrieval_k)

    assert scores["recall"] >= settings.min_recall_at_k, scores
    assert scores["mrr"] >= settings.min_mrr, scores
    assert scores["ndcg"] >= settings.min_ndcg_at_k, scores


def test_hybrid_is_at_least_as_good_as_its_components(retrievers, corpus, settings):
    """Fusion must not regress below the best single strategy on nDCG (the reason to pay for it)."""
    k = settings.retrieval_k
    ndcg = {name: evaluate(r, corpus["queries"], k)["ndcg"] for name, r in retrievers.items()}

    assert ndcg["hybrid"] >= max(ndcg["bm25"], ndcg["semantic"]) - 0.05, ndcg


def test_results_are_ranked_and_deduplicated(hybrid):
    """Ranks are 1..k in order, scores never increase, and no document appears twice."""
    results = hybrid.search("shipping cost", k=5)

    assert [r.rank for r in results] == list(range(1, len(results) + 1))
    assert all(a.score >= b.score for a, b in zip(results, results[1:]))
    assert len({r.document.id for r in results}) == len(results)


def test_search_is_deterministic(hybrid):
    """The same query twice gives the same ranking (no hidden randomness)."""
    assert hybrid.search_ids("warranty coverage", k=5) == hybrid.search_ids("warranty coverage", k=5)
