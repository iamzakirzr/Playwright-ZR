"""Dataset report: n-gram overlap (ROUGE-L) versus meaning (embedding similarity) on live answers.

Both are computed for every golden case and attached to the report. Only the *means* are
asserted, as regression budgets, and the similarity mean must exceed the ROUGE mean: if it
doesn't, either the bot started copying the reference verbatim or the embedding model changed.
"""

import statistics

from ai.datasets import load_golden
from ai.evaluators import cosine_similarity, rouge_scores
from reporting import attach_json

GOLDEN = load_golden("cases")

#: Measured on qwen2.5:1.5b (temperature 0): ROUGE-L mean 0.535, similarity mean 0.850.
#: Budgets leave room for small cross-hardware drift.
MIN_MEAN_ROUGE_L = 0.45
MIN_MEAN_SIMILARITY = 0.78


def test_meaning_beats_wording_on_the_golden_set(ask, settings):
    """Correct answers are paraphrases: semantic similarity sits well above ROUGE-L."""
    rows = []
    for case in GOLDEN:
        answer = ask(case["question"], case["context"]).text
        rows.append(
            {
                "id": case["id"],
                "rougeL": round(rouge_scores(answer, case["expected_answer"])["rougeL"], 3),
                "similarity": round(cosine_similarity(answer, case["expected_answer"], settings.embedding_model), 3),
            }
        )
    mean_rouge = statistics.mean(r["rougeL"] for r in rows)
    mean_similarity = statistics.mean(r["similarity"] for r in rows)
    attach_json("overlap vs meaning", {"mean_rougeL": mean_rouge, "mean_similarity": mean_similarity, "cases": rows})
    print(f"mean ROUGE-L={mean_rouge:.3f} mean similarity={mean_similarity:.3f}")

    assert mean_similarity > mean_rouge
    assert mean_rouge >= MIN_MEAN_ROUGE_L
    assert mean_similarity >= MIN_MEAN_SIMILARITY
