"""Synthetic test data for AI and UI testing: goldens from documents, test cases from requirements."""

from ai.synthesis.goldens import GoldenQualityGate, GoldenReview, synthesize_goldens
from ai.synthesis.test_cases import (
    GeneratedTestCase,
    Requirement,
    TestCaseGenerationError,
    TestSuiteReview,
    generate_test_cases,
    load_requirements,
    related_requirements,
    review_suite,
)

__all__ = [
    "GeneratedTestCase",
    "GoldenQualityGate",
    "GoldenReview",
    "Requirement",
    "TestCaseGenerationError",
    "TestSuiteReview",
    "generate_test_cases",
    "load_requirements",
    "related_requirements",
    "review_suite",
    "synthesize_goldens",
]
