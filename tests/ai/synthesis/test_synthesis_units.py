"""Offline tests for synthetic data: parsing, validation, coverage review and the golden gate.

A scripted model stands in for the LLM, so every rule is checked in milliseconds.
"""

import json

import pytest
from deepeval.dataset import Golden

from ai.chatbot import ScriptedChatbot
from ai.synthesis import (
    GeneratedTestCase,
    GoldenQualityGate,
    Requirement,
    TestCaseGenerationError,
    generate_test_cases,
    load_requirements,
    related_requirements,
    review_suite,
)
from ai.synthesis.test_cases import parse_test_cases, quoted_messages

LOGIN = Requirement(id="REQ-L", text="No username shows 'Username is required'.", needs_negative=True)


def case(requirement_id="REQ-L", title="Missing username", type_="negative", expected="'Username is required' shown"):
    """A valid generated test case with overridable fields."""
    return GeneratedTestCase(requirement_id=requirement_id, title=title, type=type_, steps=["Click Login"], expected=expected)


class TestParsing:
    """``parse_test_cases``: tolerant of shape, strict on content."""

    def test_valid_cases_parse_and_get_the_callers_requirement_id(self):
        """The id comes from the code, never from the model's text."""
        text = json.dumps(
            {
                "test_cases": [
                    {
                        "title": "Missing username",
                        "type": "Negative",
                        "steps": ["a"],
                        "expected": "error",
                        "requirement_id": "WRONG",
                    }
                ]
            }
        )

        cases, dropped = parse_test_cases(text, "REQ-L")

        assert cases[0].requirement_id == "REQ-L" and cases[0].type == "negative"
        assert dropped == []

    def test_bare_list_is_accepted(self):
        """Some models return the list without the wrapper object."""
        cases, _ = parse_test_cases(
            json.dumps([{"title": "Valid login", "type": "positive", "steps": ["a"], "expected": "ok!"}]), "R"
        )

        assert len(cases) == 1

    @pytest.mark.parametrize(
        "bad",
        [
            {"title": "Hi", "type": "positive", "steps": ["a"], "expected": "ok!"},
            {"title": "Valid login", "type": "smoke", "steps": ["a"], "expected": "ok!"},
            {"title": "Valid login", "type": "positive", "steps": [], "expected": "ok!"},
            {"title": "Valid login", "type": "positive", "steps": ["a"]},
            "not an object",
        ],
        ids=["short-title", "unknown-type", "no-steps", "no-expected", "not-object"],
    )
    def test_invalid_cases_are_dropped_with_a_note(self, bad):
        """One bad case doesn't sink the batch; the reason is kept."""
        good = {"title": "Valid login", "type": "positive", "steps": ["a"], "expected": "ok!"}

        cases, dropped = parse_test_cases(json.dumps({"test_cases": [good, bad]}), "R")

        assert len(cases) == 1 and len(dropped) == 1 and dropped[0].startswith("case 1 dropped")

    @pytest.mark.parametrize("text", ["not json", '{"cases": []}', '"just a string"'])
    def test_unusable_reply_raises(self, text):
        """No JSON, or no case list, is an error, not an empty suite."""
        with pytest.raises(TestCaseGenerationError):
            parse_test_cases(text, "R")


class TestGeneration:
    """``generate_test_cases`` with a scripted model."""

    def test_prompt_is_grounded_and_json_mode_is_requested(self):
        """The requirement and its retrieved neighbours reach the model; JSON mode is on."""
        reply = json.dumps(
            {"test_cases": [{"title": "Missing username", "type": "negative", "steps": ["a"], "expected": "error"}]}
        )
        bot = ScriptedChatbot([reply])
        related = [Requirement(id="REQ-P", text="No password shows 'Password is required'.")]

        cases = generate_test_cases(bot, LOGIN, related)

        call = bot.calls[0]
        assert call.json_mode is True
        assert "REQ-L" in call.user and "Username is required" in call.user and "REQ-P" in call.user
        assert cases[0].requirement_id == "REQ-L"

    def test_all_invalid_raises(self):
        """A reply with nothing usable is an error the caller must handle."""
        bot = ScriptedChatbot([json.dumps({"test_cases": [{"title": "x"}]})])

        with pytest.raises(TestCaseGenerationError, match="REQ-L"):
            generate_test_cases(bot, LOGIN)

    def test_related_requirements_are_retrieved_by_topic(self):
        """RAG context for a login rule is other login rules, not checkout ones."""
        requirements = load_requirements()
        target = next(r for r in requirements if r.id == "REQ-LOGIN-03")

        related = related_requirements(target, requirements, k=2)

        assert target not in related
        assert all(r.id.startswith("REQ-LOGIN") for r in related)


class TestReview:
    """``review_suite`` coverage rules."""

    def test_complete_suite_is_ok(self):
        """Covered, negative present, message checked: nothing to report."""
        assert review_suite([LOGIN], [case()]).ok

    def test_uncovered_requirement(self):
        """A requirement with no case is listed."""
        other = Requirement(id="REQ-X", text="Something else.")

        assert review_suite([LOGIN, other], [case()]).uncovered == ["REQ-X"]

    def test_missing_negative(self):
        """An error requirement covered only by positive cases is flagged."""
        review = review_suite([LOGIN], [case(type_="positive")])

        assert review.missing_negative == ["REQ-L"]

    def test_duplicate_titles_within_a_requirement(self):
        """Same title twice under one requirement is a defect; case and spacing don't hide it."""
        review = review_suite([LOGIN], [case(), case(title=" missing USERNAME ")])

        assert review.duplicate_titles == ["REQ-L: missing username"]

    def test_quoted_message_must_be_checked(self):
        """If the requirement quotes an error, some expected result must contain it."""
        review = review_suite([LOGIN], [case(expected="an error appears")])

        assert review.unchecked_messages and not review.ok

    def test_placeholder_in_quoted_message_matches_any_field(self):
        """``'Error: <Field> is required'`` is satisfied by "Error: First Name is required"."""
        requirement = Requirement(id="R", text="Missing field shows 'Error: <Field> is required'.")

        (pattern,) = quoted_messages(requirement)

        assert pattern.search("Shows Error: First Name is required")
        assert not pattern.search("Shows Error: required")

    def test_shared_titles_are_informational(self):
        """The same title under two requirements is reported but doesn't fail the review."""
        other = Requirement(id="REQ-Y", text="Another rule.")

        review = review_suite([LOGIN, other], [case(), case(requirement_id="REQ-Y", type_="positive")])

        assert review.shared_titles == ["missing username"]
        assert review.ok


class TestGoldenGate:
    """Deterministic checks of :class:`GoldenQualityGate` (no judge)."""

    @pytest.fixture
    def gate(self, settings) -> GoldenQualityGate:
        """Gate without the judged grounding check."""
        return GoldenQualityGate(settings.embedding_model)

    CONTEXT = ["Sauce Demo Store accepts returns within 45 days of delivery."]

    def test_good_golden_is_accepted(self, gate):
        """A real question, an answer and its context pass."""
        golden = Golden(
            input="Can I return a product after 45 days?", expected_output="No, only within 45 days.", context=self.CONTEXT
        )

        assert gate.review([golden])[0].accepted

    @pytest.mark.parametrize(
        ("fields", "problem"),
        [
            ({"input": " ", "expected_output": "x", "context": CONTEXT}, "empty question"),
            ({"input": "q?", "expected_output": "", "context": CONTEXT}, "no expected answer"),
            ({"input": "q?", "expected_output": "x", "context": None}, "no source context"),
        ],
        ids=["no-question", "no-answer", "no-context"],
    )
    def test_incomplete_goldens_are_rejected(self, gate, fields, problem):
        """Missing parts are rejected with a readable reason."""
        assert problem in gate.review([Golden(**fields)])[0].problems

    def test_question_copied_from_context_is_rejected(self, gate):
        """A question that restates the context verbatim tests nothing."""
        golden = Golden(
            input="Sauce Demo Store accepts returns within 45 days of delivery?", expected_output="Yes.", context=self.CONTEXT
        )

        assert gate.review([golden])[0].problems == ["question copied from the context"]

    def test_near_duplicate_of_an_accepted_question_is_rejected(self, gate):
        """Only the first of two paraphrased questions is kept."""
        first = Golden(input="Can I return an item after 45 days?", expected_output="No.", context=self.CONTEXT)
        second = Golden(input="Can I return an item after 45 days have passed?", expected_output="No.", context=self.CONTEXT)

        reviews = gate.review([first, second])

        assert reviews[0].accepted
        assert reviews[1].problems[0].startswith("duplicate of")
