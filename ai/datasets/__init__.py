"""Golden dataset loader.

``golden_qa.json`` sections:

* ``cases``: answerable questions with context, a reference answer, ``required_facts``
  (what the question strictly needs; gating) and ``helpful_facts`` (everything a
  complete answer would mention; tracked against a baseline).
* ``unanswerable``: questions whose answer is NOT in the context (the bot must abstain).
* ``counterfactual``: context contradicts world knowledge (the bot must follow the context).
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
