"""Visual regression testing: screenshot-versus-baseline comparison.

Playwright's TypeScript runner has ``toHaveScreenshot``; the Python binding
does not. This module provides the same workflow:

* **Baselines** are stored per name, browser and OS (``card-chromium-linux.png``),
  because font rendering differs across platforms. A baseline from a Mac never
  gates a Linux CI run.
* **First run** writes the baseline and reports ``created``; review it and commit it.
* **Update** intentionally changed baselines with ``UPDATE_SNAPSHOTS=1``.
* **Dynamic regions** (timestamps, ads) are hidden with Playwright's own
  ``screenshot(mask=[locator])``, so they never cause diffs.
* **Tolerance**: a per-pixel channel tolerance absorbs anti-aliasing noise; a
  ratio threshold says how much of the image may change.
* **Evidence**: on failure a diff image (changed pixels in red) is written next
  to the actual screenshot.
"""

from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops


@dataclass(frozen=True)
class VisualResult:
    """Outcome of one comparison.

    Attributes:
        name: Snapshot name.
        status: ``"match"``, ``"mismatch"``, ``"created"`` or ``"updated"``.
        diff_ratio: Share of pixels that differ beyond the tolerance (0.0 to 1.0).
        baseline: Path of the baseline image.
        actual: Path of the actual screenshot (written on mismatch).
        diff: Path of the diff image (written on mismatch).
    """

    name: str
    status: str
    diff_ratio: float
    baseline: Path
    actual: Path | None = None
    diff: Path | None = None

    @property
    def passed(self) -> bool:
        """True unless the images differ beyond the threshold."""
        return self.status != "mismatch"


class VisualComparator:
    """Compares PNG screenshots with stored baselines.

    Args:
        baseline_dir: Where baselines live (commit this folder).
        output_dir: Where actual and diff images go on failure (a CI artifact).
        browser: Browser name used in baseline file names.
        max_diff_ratio: Largest share of changed pixels still counted as a match.
        pixel_tolerance: Per-channel difference (0-255) treated as identical.
        update: Overwrite baselines instead of comparing (defaults to the ``UPDATE_SNAPSHOTS`` env var).
    """

    def __init__(
        self,
        baseline_dir: Path,
        output_dir: Path,
        browser: str = "chromium",
        max_diff_ratio: float = 0.001,
        pixel_tolerance: int = 16,
        update: bool | None = None,
    ) -> None:
        """Store settings; directories are created lazily."""
        self.baseline_dir = Path(baseline_dir)
        self.output_dir = Path(output_dir)
        self.browser = browser
        self.max_diff_ratio = max_diff_ratio
        self.pixel_tolerance = pixel_tolerance
        self.update = bool(os.getenv("UPDATE_SNAPSHOTS")) if update is None else update

    def baseline_path(self, name: str) -> Path:
        """``<baseline_dir>/<name>-<browser>-<platform>.png``."""
        return self.baseline_dir / f"{name}-{self.browser}-{sys.platform}.png"

    def diff_ratio(self, expected: Image.Image, actual: Image.Image) -> tuple[float, Image.Image]:
        """Share of pixels differing beyond ``pixel_tolerance``, plus a red-on-grey diff image.

        Images of different sizes count as a full mismatch (ratio 1.0).
        """
        if expected.size != actual.size:
            return 1.0, actual.convert("RGB")
        delta = ImageChops.difference(expected.convert("RGB"), actual.convert("RGB")).convert("L")
        changed = delta.point(lambda v: 255 if v > self.pixel_tolerance else 0)
        histogram = changed.histogram()
        ratio = histogram[255] / (expected.width * expected.height)
        overlay = Image.blend(expected.convert("RGB").convert("L").convert("RGB"), Image.new("RGB", expected.size, "white"), 0.6)
        overlay.paste(Image.new("RGB", expected.size, (255, 0, 0)), mask=changed)
        return ratio, overlay

    def compare(self, name: str, png: bytes) -> VisualResult:
        """Compare screenshot bytes with the baseline for ``name`` (creating or updating it when due)."""
        baseline = self.baseline_path(name)
        if self.update or not baseline.exists():
            baseline.parent.mkdir(parents=True, exist_ok=True)
            status = "updated" if baseline.exists() else "created"
            baseline.write_bytes(png)
            return VisualResult(name, status, 0.0, baseline)

        ratio, diff_image = self.diff_ratio(Image.open(baseline), Image.open(io.BytesIO(png)))
        if ratio <= self.max_diff_ratio:
            return VisualResult(name, "match", ratio, baseline)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        actual = self.output_dir / f"{name}-actual.png"
        diff = self.output_dir / f"{name}-diff.png"
        actual.write_bytes(png)
        diff_image.save(diff)
        return VisualResult(name, "mismatch", ratio, baseline, actual, diff)
