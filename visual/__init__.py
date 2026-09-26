"""Visual regression testing: pixel comparator with baselines, plus an opt-in vision-LLM judge."""

from visual.comparator import VisualComparator, VisualResult
from visual.vision_judge import VisionJudge, VisionVerdict

__all__ = ["VisionJudge", "VisionVerdict", "VisualComparator", "VisualResult"]
