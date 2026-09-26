"""Visual regression tests on a local product card (deterministic, no network).

Each test gets its own baseline folder, so the whole workflow is exercised:
create the baseline, match it, catch a regression, mask dynamic content, update.
The page contains a live timestamp on purpose: without masking, every run would diff.
"""
from pathlib import Path

import pytest

from visual import VisionJudge, VisualComparator

CARD = (Path(__file__).with_name("html") / "product_card.html").as_uri()


@pytest.fixture
def comparator(tmp_path, browser_name) -> VisualComparator:
    """Comparator with a throwaway baseline folder (real suites point it at a committed folder)."""
    return VisualComparator(tmp_path / "baselines", tmp_path / "diffs", browser=browser_name, update=False)


def snap(page, **css) -> bytes:
    """Open the card, apply optional CSS overrides, and screenshot it with the timestamp masked."""
    page.goto(CARD)
    for selector, style in css.items():
        page.add_style_tag(content=f"{selector.replace('_', '.')} {{ {style} }}")
    card = page.get_by_test_id("card")
    return card.screenshot(mask=[page.get_by_test_id("stamp")], animations="disabled")


def test_first_run_creates_the_baseline(page, comparator):
    """No baseline yet: it's written and reported as ``created`` (review it, then commit it)."""
    result = comparator.compare("card", snap(page))

    assert result.status == "created"
    assert result.baseline.exists() and result.baseline.name.startswith("card-")


def test_unchanged_page_matches(page, comparator):
    """Two renders of the same page match, even though the (masked) timestamp changed."""
    comparator.compare("card", snap(page))

    result = comparator.compare("card", snap(page))

    assert result.status == "match", result


@pytest.mark.parametrize(
    "css, what",
    [
        ({"_price": "color: #e2231a;"}, "price colour"),
        ({"button": "margin-top: 40px;"}, "button moved"),
        ({"_title": "font-size: 26px;"}, "title size"),
    ],
    ids=["colour", "layout", "typography"],
)
def test_css_regression_is_detected_with_diff_image(page, comparator, css, what):
    """A real visual change fails, and the actual screenshot and a red diff image are saved as evidence."""
    comparator.compare("card", snap(page))

    result = comparator.compare("card", snap(page, **css))

    assert result.status == "mismatch", f"{what} not detected"
    assert result.diff_ratio > comparator.max_diff_ratio
    assert result.diff.exists() and result.actual.exists()


def test_unmasked_dynamic_content_would_flake(page, comparator):
    """Why masking matters: without it, the ever-changing timestamp makes the same page 'differ'."""
    page.goto(CARD)
    comparator.compare("card-unmasked", page.get_by_test_id("card").screenshot())
    page.wait_for_timeout(5)
    page.reload()

    result = comparator.compare("card-unmasked", page.get_by_test_id("card").screenshot())

    assert result.status == "mismatch"


def test_update_mode_rewrites_the_baseline(page, tmp_path, browser_name):
    """``UPDATE_SNAPSHOTS=1`` (here ``update=True``) accepts an intentional change as the new baseline."""
    comparator = VisualComparator(tmp_path / "b", tmp_path / "d", browser=browser_name)
    comparator.compare("card", snap(page))
    changed = snap(page, _price="color: #e2231a;")

    updater = VisualComparator(tmp_path / "b", tmp_path / "d", browser=browser_name, update=True)
    assert updater.compare("card", changed).status == "updated"
    assert comparator.compare("card", changed).status == "match"


def test_side_by_side_composite_layout(page):
    """The composite used by the vision judge is baseline-left, new-right, split by a separator."""
    from PIL import Image
    import io

    from visual.vision_judge import SEPARATOR_PX, side_by_side

    left = snap(page)
    width = Image.open(io.BytesIO(left)).width
    composite = Image.open(io.BytesIO(side_by_side(left, left)))

    assert composite.width == 2 * width + SEPARATOR_PX


def test_vision_llm_verdict_is_advisory_but_right(page, require_ollama_model, settings):
    """Opt-in: the vision model flags a real change and passes an identical page (verdict only; prose is unreliable)."""
    require_ollama_model(settings.vision_model)
    judge = VisionJudge(settings.ollama_host, settings.vision_model)
    baseline = snap(page)

    changed = judge.compare(baseline, snap(page, button="margin-top: 60px; background: #e2231a;"))
    identical = judge.compare(baseline, snap(page))

    assert not changed.same, changed
    assert identical.same, identical
