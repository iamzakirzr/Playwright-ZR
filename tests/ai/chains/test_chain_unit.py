"""Prompt-chain unit tests with a scripted (fake) model: fast, deterministic, offline.

Chains fail between links, so each link's contract is tested separately:
routing, short-circuiting, what each step passes to the next, error
attribution, and output normalisation. The ``ScriptedChatbot`` spy records
every prompt the chain sent, so tests can assert on *what the model was
asked*, not just on what came back.
"""

import pytest

from ai.chains import HANDOFF_MESSAGE, Chain, ChainError, ChainState, ChainStep, IntentStep, build_support_chain
from ai.chatbot import ScriptedChatbot


def scripted(intent: str, query: str = "return window days", answer: str = "You have 45 days.") -> ScriptedChatbot:
    """A fake model that answers the classify, rewrite and answer prompts in turn."""
    return ScriptedChatbot([intent, query, answer], canary="TEST-CANARY")


class TestHappyPath:
    """A normal, in-scope question runs every step."""

    def test_all_steps_run_in_order(self, hybrid):
        """intent → handoff → rewrite → retrieve → answer, one trace entry per step."""
        state = build_support_chain(scripted("returns"), hybrid).run("How long can I return stuff?")

        assert state.executed_steps == ["intent", "handoff", "rewrite", "retrieve", "answer"]
        assert state.answer == "You have 45 days."

    def test_rewritten_query_drives_retrieval(self, hybrid):
        """Retrieval uses the rewritten query and finds the matching passage."""
        state = build_support_chain(scripted("shipping", query="express shipping cost"), hybrid).run(
            "hey how much for fast delivery??"
        )

        assert state.query == "express shipping cost"
        assert "shipping-3" in state.document_ids

    def test_answer_step_gets_original_question_and_retrieved_passages(self, hybrid):
        """The final prompt holds the user's *original* wording plus the retrieved passages."""
        bot = scripted("returns")
        question = "How long can I return stuff?"
        state = build_support_chain(bot, hybrid).run(question)

        answer_call = bot.calls[-1]
        assert answer_call.user == question
        assert all(doc in answer_call.system for doc in state.documents)

    def test_model_calls_are_bounded(self, hybrid):
        """An in-scope question costs exactly three model calls (classify, rewrite, answer)."""
        bot = scripted("returns")
        build_support_chain(bot, hybrid).run("return policy?")

        assert len(bot.calls) == 3


class TestRouting:
    """Out-of-scope questions are short-circuited."""

    def test_out_of_scope_is_handed_off_after_one_call(self, hybrid):
        """Off-topic input stops at the hand-off: one model call, no retrieval, no answer generation."""
        bot = ScriptedChatbot(["out_of_scope"])
        state = build_support_chain(bot, hybrid).run("Write me a poem")

        assert state.halted
        assert state.answer == HANDOFF_MESSAGE
        assert state.executed_steps == ["intent", "handoff"]
        assert len(bot.calls) == 1

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("returns", "returns"),
            ("Returns.", "returns"),
            ("  SHIPPING\n", "shipping"),
            ("support hours", "support_hours"),
            ("The label is: warranty", "warranty"),
            ("banana", "out_of_scope"),
            ("", "out_of_scope"),
        ],
    )
    def test_intent_normalisation(self, raw, expected):
        """Free-form model output is mapped onto the closed label set; unknown input fails safe to out_of_scope."""
        assert IntentStep.normalise(raw) == expected


class TestFailureHandling:
    """Errors are attributed to the failing link."""

    def test_step_failure_names_the_step(self):
        """A crash inside a step surfaces as ChainError carrying that step's name."""

        class Boom(ChainStep):
            """A step that always fails."""

            name = "boom"

            def run(self, state: ChainState):
                """Raise to simulate a broken dependency."""
                raise TimeoutError("vector DB timed out")

        with pytest.raises(ChainError) as err:
            Chain([Boom()]).run("anything")

        assert err.value.step == "boom"
        assert isinstance(err.value.cause, TimeoutError)

    def test_empty_rewrite_falls_back_to_original_question(self, hybrid):
        """If the rewriter returns nothing, retrieval still runs on the user's question."""
        state = build_support_chain(scripted("returns", query=""), hybrid).run("return window")

        assert state.query == "return window"
        assert state.document_ids

    def test_chain_requires_steps(self):
        """An empty chain is a construction error, not a silent no-op."""
        with pytest.raises(ValueError):
            Chain([])
