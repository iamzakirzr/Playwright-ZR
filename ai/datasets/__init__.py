"""Golden dataset loader."""
from __future__ import annotations

import json
from pathlib import Path

_GOLDEN = Path(__file__).with_name("golden_qa.json")


def load_golden(section: str = "cases") -> list[dict]:
    return json.loads(_GOLDEN.read_text())[section]
