"""Fixtures for self-healing locator tests."""

from __future__ import annotations

import pytest

from pages.healing import HealingCache


@pytest.fixture
def healing_cache(tmp_path) -> HealingCache:
    """A fresh healing cache file per test."""
    return HealingCache(tmp_path / "healed_locators.json")
