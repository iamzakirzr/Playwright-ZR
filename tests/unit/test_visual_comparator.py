"""Unit tests for the pixel comparator: no browser, just images built in memory."""

import io

import pytest
from PIL import Image

from visual import VisualComparator


def png(color: str, size=(40, 20)) -> bytes:
    """A solid-colour PNG."""
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def comparator(tmp_path) -> VisualComparator:
    """Comparator with default tolerances and a throwaway baseline folder."""
    return VisualComparator(tmp_path / "baselines", tmp_path / "diffs", update=False)


def test_blue_only_change_is_detected(comparator):
    """Regression: luminance weights blue at 0.114, so #132322 -> #1323a0 (blue +126) scored 14 and passed."""
    comparator.compare("price", png("#132322"))

    result = comparator.compare("price", png("#1323a0"))

    assert result.status == "mismatch"
    assert result.diff_ratio == 1.0


def test_changes_within_tolerance_still_match(comparator):
    """Anti-aliasing-sized noise (every channel +10) stays under the 16-level tolerance."""
    comparator.compare("price", png("#808080"))

    assert comparator.compare("price", png("#8a8a8a")).status == "match"


def test_size_change_is_a_full_mismatch(comparator):
    """Different dimensions can't be compared pixel by pixel, so they fail outright."""
    comparator.compare("card", png("white"))

    assert comparator.compare("card", png("white", size=(41, 20))).diff_ratio == 1.0


@pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
def test_update_mode_needs_an_explicit_true(monkeypatch, tmp_path, value):
    """Regression: bool(os.getenv(...)) made UPDATE_SNAPSHOTS=0 overwrite every baseline."""
    monkeypatch.setenv("UPDATE_SNAPSHOTS", value)

    assert VisualComparator(tmp_path, tmp_path).update is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_update_mode_accepts_true_values(monkeypatch, tmp_path, value):
    """The usual spellings of "true" switch update mode on."""
    monkeypatch.setenv("UPDATE_SNAPSHOTS", value)

    assert VisualComparator(tmp_path, tmp_path).update is True
