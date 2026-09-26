"""Golden dataset loader.

``golden_qa.json`` sections:

* ``cases``: answerable questions with context, a reference answer, ``required_facts``
  (what the question strictly needs; gating) and ``helpful_facts`` (everything a
  complete answer would mention; tracked against a baseline).
* ``unanswerable``: questions whose answer is NOT in the context (the bot must abstain).
* ``counterfactual``: context contradicts world knowledge (the bot must follow the context).

:func:`golden_dataset` and :func:`adversarial_dataset` wrap the same data as
DeepEval ``EvaluationDataset`` objects (``Golden`` = an input plus its
expectations, with no output yet). That is the shape DeepEval, Confident AI
and most eval tooling exchange, so datasets can be pushed, pulled and versioned.
"""
from __future__ import annotations

import json
from pathlib import Path

_GOLDEN = Path(__file__).with_name("golden_qa.json")


def load_golden(section: str = "cases") -> list[dict]:
    """Return one section of the golden dataset as a list of dicts.

    Args:
        section: ``cases``, ``unanswerable`` or ``counterfactual``.
    """
    return json.loads(_GOLDEN.read_text())[section]


def golden_case(case_id: str) -> dict:
    """Look up a single answerable case by id.

    Raises:
        KeyError: If no case has that id.
    """
    for case in load_golden("cases"):
        if case["id"] == case_id:
            return case
    raise KeyError(case_id)


def golden_dataset():
    """The answerable golden cases as a DeepEval ``EvaluationDataset``.

    Each ``Golden`` carries ``input``, ``expected_output`` and ``context``;
    ``additional_metadata`` keeps the id and fact lists for keyword checks.
    """
    from deepeval.dataset import EvaluationDataset, Golden

    return EvaluationDataset(
        goldens=[
            Golden(
                input=c["question"],
                expected_output=c["expected_answer"],
                context=c["context"],
                additional_metadata={"id": c["id"], "required_facts": c["required_facts"], "helpful_facts": c["helpful_facts"]},
            )
            for c in load_golden("cases")
        ]
    )


def adversarial_dataset():
    """The red-team attack library as a DeepEval ``EvaluationDataset`` of adversarial goldens."""
    from deepeval.dataset import EvaluationDataset, Golden

    from ai.redteam import load_attacks

    return EvaluationDataset(
        goldens=[
            Golden(
                input=a.prompt,
                context=list(a.context) or None,
                additional_metadata={"id": a.id, "category": a.category, "owasp": a.owasp, "checks": list(a.checks)},
            )
            for a in load_attacks()
        ]
    )
