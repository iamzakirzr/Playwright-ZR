# 11 · Self-healing locators and visual testing

## Why
Two classic sources of UI-test pain: a front-end refactor renames every `data-test` attribute
(tests break but the product works), and a CSS change breaks the look (tests pass but the product
is broken). Healing addresses the first; visual testing addresses the second.

## Self-healing: [`pages/healing/self_healing.py`](../../pages/healing/self_healing.py)
Resolution order for a `healable` element:
1. the selector in the page object;
2. a previously healed selector from the JSON **cache**;
3. ask the **LLM** for candidate selectors, given the element's description and a trimmed copy of
   the page HTML, then **validate** each candidate (must match exactly one visible element).

A healed selector is logged so the page-object owner fixes the source. Healing is a safety net,
not a replacement for good locators.
Tests: [`tests/ai/healing/test_self_healing.py`](../../tests/ai/healing/test_self_healing.py)
(fake healer offline, local LLM live) with v1/v2 demo pages in `tests/ai/healing/html/`.

## Visual regression: [`visual/comparator.py`](../../visual/comparator.py)
- Baselines are per name, browser **and** OS (fonts render differently).
- The first run creates the baseline; `UPDATE_SNAPSHOTS=1` accepts intended changes.
- Dynamic regions (timestamps) are hidden with `screenshot(mask=[...])`.
- On a mismatch you get the actual image and a red-on-grey diff image.
- [`visual/vision_judge.py`](../../visual/vision_judge.py): an opt-in vision model looks at a
  side-by-side composite and says what changed. **Advisory only**: pixels decide pass/fail.

## Run
```bash
pytest -m "healing and not live"
make test-visual
```

## Try it
Change the card's font size in `tests/ui/visual/html/product_card.html`, run the visual tests, and
open the diff image from the failure message.

## Test your knowledge
1. Why must a healed selector match exactly one element?
2. Why is the vision LLM advisory rather than the pass/fail gate?

<details><summary>Answers</summary>

1. A selector matching several elements (e.g. `button`) would "heal" to the wrong one and click it.
2. Small vision models hallucinate descriptions; a pixel diff is deterministic. The LLM helps a
   human understand the diff faster.
</details>
