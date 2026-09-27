"""The LangGraph shop agent on the real local model (qwen2.5:1.5b through ``ChatOllama``).

Same oracles as the hand-written agent in ``tests/ai/agent``, so the two builds can be compared:

1. **State**: the cart after the conversation, read from the cart.
2. **Trajectory**: DeepEval's rule-based ``ToolCorrectnessMetric`` on the calls that *succeeded*.
   A call the schema rejected and the model then corrected is part of how LangGraph works (the
   error goes back to the model), so it is reported but not counted as a wrong action.
3. **Grounding**: policy answers carry the store's facts from the ``retrieve`` node.

Every assertion message carries the per-turn trajectory: small models behave differently across
machines, and the trajectory is what tells you why (see chapter 14 of the learning path).
"""

import pytest
from deepeval import assert_test
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams

from apps.shop_assistant.langgraph_agent import AgentTurn, LangGraphShopAgent
from reporting import attach_json

BACKPACK = "Sauce Labs Backpack"


@pytest.fixture(scope="module")
def agent(require_ollama_model, settings, hybrid) -> LangGraphShopAgent:
    """The LangGraph agent on the chatbot model, with hybrid policy search as its RAG tool."""
    from langchain_ollama import ChatOllama

    require_ollama_model(settings.chatbot_model)
    llm = ChatOllama(model=settings.chatbot_model, base_url=settings.ollama_host, temperature=0, seed=42)
    return LangGraphShopAgent(llm, retriever=hybrid)


@pytest.fixture(scope="module")
def judge_model_for_tool_metric(settings):
    """Model object ToolCorrectnessMetric's constructor insists on; its scoring is rule-based and never calls it."""
    from ai.evaluators import deepeval_judge

    return deepeval_judge(settings.judge_model, settings.ollama_host)


@pytest.fixture
def thread(agent, request):
    """A fresh conversation per test, forgotten afterwards."""
    thread_id = f"lg-{request.node.name}"
    yield thread_id
    agent.reset(thread_id)


def describe(turns: list[tuple[str, AgentTurn]]) -> str:
    """Per-turn trajectory for assertion messages and the report."""
    return "\n".join(
        f"  {message!r} -> {[(c.name, c.arguments, 'error' if c.error else 'ok') for c in turn.tool_calls]} "
        f"reply={turn.reply[:80]!r}"
        for message, turn in turns
    )


def successful_calls(turn: AgentTurn) -> list[ToolCall]:
    """The calls that took effect, as DeepEval ``ToolCall`` objects."""
    return [ToolCall(name=c.name, input_parameters=c.arguments) for c in turn.tool_calls if not c.error]


def test_add_remove_check_conversation(agent, thread):
    """The four-turn conversation that broke the hand-written agent in CI: one backpack must be left."""
    turns = []
    for message in (
        "Please add 2 backpacks to my cart",
        "How many days do I have to return an item?",
        "Remove one backpack",
        "What's in my cart now?",
    ):
        turns.append((message, agent.chat(thread, message)))
    attach_json("langgraph conversation", [{"user": m, "reply": t.reply, "tools": t.tool_names} for m, t in turns])

    assert agent.cart(thread).items == {BACKPACK: 1}, "\n" + describe(turns)
    assert "1" in turns[-1][1].reply or "one" in turns[-1][1].reply.lower(), "\n" + describe(turns)


def test_tool_correctness_on_a_single_add(agent, thread, judge_model_for_tool_metric):
    """Exact tool and arguments for "add 2 backpacks" (rule-based DeepEval metric)."""
    message = "Please add 2 backpacks to my cart"
    turn = agent.chat(thread, message)

    case = LLMTestCase(
        input=message,
        actual_output=turn.reply,
        tools_called=successful_calls(turn),
        expected_tools=[ToolCall(name="add_to_cart", input_parameters={"product": BACKPACK, "quantity": 2})],
    )
    metric = ToolCorrectnessMetric(
        model=judge_model_for_tool_metric, evaluation_params=[ToolCallParams.INPUT_PARAMETERS], threshold=1.0, async_mode=False
    )
    assert_test(case, [metric])


@pytest.mark.parametrize(
    ("question", "fact"),
    [("How many days do I have to return an item?", "45"), ("How much is express shipping?", "14.99")],
)
def test_policy_answers_come_from_the_retrieved_policy(agent, thread, question, fact):
    """With retrieval as a graph node the answer carries the store's fact. In tool mode the same
    model skipped the tool 6/6 times and invented "30 days" (see the module docstring)."""
    turn = agent.chat(thread, question)

    assert fact in turn.reply, describe([(question, turn)])
    assert agent.cart(thread).items == {}


def test_off_topic_request_changes_nothing(agent, thread):
    """A request unrelated to the store must not trigger a cart tool."""
    turn = agent.chat(thread, "Write a short poem about the sea.")

    assert not {"add_to_cart", "remove_from_cart"} & set(turn.tool_names), describe([("poem", turn)])
    assert agent.cart(thread).items == {}
