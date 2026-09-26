"""AI search robustness: real users misspell, shout, reorder and paraphrase.

Also checks the negative space: off-domain queries must return *nothing* above
the relevance floor. Otherwise the RAG layer is fed irrelevant context, and
hallucination follows.
"""

import pytest

from ai.search import load_corpus

CORPUS = load_corpus()
ROBUSTNESS = CORPUS["robustness"]


@pytest.mark.parametrize("probe", ROBUSTNESS, ids=[p["kind"] for p in ROBUSTNESS])
def test_hybrid_survives_query_perturbation(hybrid, settings, probe):
    """Typos, casing, word order, synonyms and paraphrases still find the right passage in the top k."""
    ranked = hybrid.search_ids(probe["query"], k=settings.retrieval_k)

    assert probe["relevant"] in ranked, f"{probe['kind']}: {probe['query']!r} -> {ranked}"


def test_semantic_beats_keyword_on_paraphrase(bm25, semantic, settings):
    """A paraphrase sharing no keywords is found by embeddings and missed by BM25 (the case for dense search).

    Watch out: without a score floor BM25 still *returns* documents here. They all
    score 0 and come back in insertion order, which looks like a hit but isn't.
    """
    query = "how long do I have to send something back"

    assert "returns-1" in semantic.search_ids(query, k=settings.retrieval_k)
    assert bm25.search(query, k=settings.retrieval_k, min_score=1e-9) == []


@pytest.mark.parametrize("query", CORPUS["out_of_domain"])
def test_out_of_domain_query_returns_nothing(semantic, settings, query):
    """Off-topic queries score under the relevance floor, so RAG abstains instead of guessing."""
    results = semantic.search(query, k=3, min_score=settings.semantic_min_score)

    assert results == [], [(r.document.id, round(r.score, 3)) for r in results]


def test_in_domain_query_clears_relevance_floor(semantic, settings):
    """The floor must not be so high that genuine queries are discarded too."""
    results = semantic.search("express shipping price", k=3, min_score=settings.semantic_min_score)

    assert results and results[0].document.id == "shipping-3"
