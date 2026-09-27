"""Offline tests of the LangGraph shop agent: a scripted chat model drives every path.

What an agent test pins down, in order of how often it catches real bugs:
1. **Trajectory**: which tools were called, with which arguments, in which order.
2. **State**: the cart after the turn, read from the cart itself, never from the reply text.
3. **What the model was shown**: tool schemas, tool results, the live cart in the prompt.
4. **Control flow**: error feedback, memory across turns, the loop bound.
"""

import pytest
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from ai.chatbot import ScriptedChatModel, tool_call_message
from ai.search import BM25Retriever, load_documents
from apps.shop_assistant.catalog import PRODUCTS
from apps.shop_assistant.langgraph_agent import GAVE_UP_REPLY, LangGraphShopAgent

BACKPACK = "Sauce Labs Backpack"
ONESIE = "Sauce Labs Onesie"


def _retriever(enabled: bool) -> dict:
    """Keyword arguments giving the agent a retriever (and so a retrieve node), or none."""
    return {"retriever": BM25Retriever(load_documents())} if enabled else {}


def agent_with(*replies: AIMessage, **kwargs) -> tuple[LangGraphShopAgent, ScriptedChatModel]:
    """An agent whose model answers with ``replies``, plus the model (to inspect what it saw)."""
    model = ScriptedChatModel(replies=list(replies))
    return LangGraphShopAgent(model, **kwargs), model


class TestGraphAndTools:
    """The agent's structure and the schemas the model is given."""

    def test_graph_is_agent_then_tools_loop(self):
        """START -> agent, agent -> tools or END, tools -> agent: the ReAct loop and nothing else."""
        agent, _ = agent_with()
        graph = agent.graph.get_graph()

        edges = {(e.source, e.target) for e in graph.edges}

        assert set(graph.nodes) == {"__start__", "agent", "tools", "__end__"}
        assert edges == {("__start__", "agent"), ("agent", "tools"), ("agent", "__end__"), ("tools", "agent")}

    def test_tool_schemas_come_from_type_hints(self):
        """``Literal`` of catalogue names becomes an enum, ``Field(ge=1)`` a minimum, and the
        injected run config is invisible to the model."""
        _, model = agent_with()
        schemas = {t["function"]["name"]: t["function"]["parameters"] for t in model.bound_tools}

        assert set(schemas) == {"add_to_cart", "remove_from_cart", "view_cart"}
        add = schemas["add_to_cart"]
        assert add["properties"]["product"]["enum"] == list(PRODUCTS)
        assert add["properties"]["quantity"]["minimum"] == 1
        assert add["required"] == ["product", "quantity"]
        assert "config" not in add["properties"] and schemas["view_cart"]["properties"] == {}

    def test_node_mode_retrieves_before_the_model_and_offers_no_search_tool(self):
        """Default: START -> retrieve -> agent. The model can't skip retrieval because it isn't asked."""
        agent, model = agent_with(retriever=BM25Retriever(load_documents()))
        edges = {(e.source, e.target) for e in agent.graph.get_graph().edges}

        assert {("__start__", "retrieve"), ("retrieve", "agent")} <= edges
        assert "search_policies" not in [t["function"]["name"] for t in model.bound_tools]

    def test_tool_mode_offers_search_as_a_tool(self):
        """Agentic RAG: no retrieve node; the model gets a search_policies tool and decides."""
        agent, model = agent_with(retriever=BM25Retriever(load_documents()), retrieval="tool")

        assert "retrieve" not in agent.graph.get_graph().nodes
        assert "search_policies" in [t["function"]["name"] for t in model.bound_tools]


class TestTurn:
    """One user turn: tool calls, state and what flows back to the model."""

    def test_tool_call_changes_the_cart_and_is_in_the_trajectory(self):
        """The requested tool runs against this thread's cart and is reported with its result."""
        agent, _ = agent_with(tool_call_message("add_to_cart", product=BACKPACK, quantity=2), AIMessage("Added."))

        turn = agent.chat("t1", "add 2 backpacks")

        assert agent.cart("t1").items == {BACKPACK: 2}
        assert turn.tool_names == ["add_to_cart"]
        assert turn.tool_calls[0].arguments == {"product": BACKPACK, "quantity": 2}
        assert not turn.tool_calls[0].error
        assert (turn.reply, turn.model_calls) == ("Added.", 2)

    def test_tool_result_and_live_cart_are_shown_to_the_model(self):
        """Second model call: the tool's JSON result is the last message, and the system prompt's
        CURRENT CART was rebuilt after the tool ran (the stale-cart bug from agent.py)."""
        agent, model = agent_with(tool_call_message("add_to_cart", product=BACKPACK, quantity=2), AIMessage("Added."))

        agent.chat("t1", "add 2 backpacks")

        first, second = model.received
        assert isinstance(first[0], SystemMessage) and "(empty)" in first[0].content
        assert "- 2 x Sauce Labs Backpack" in second[0].content
        assert isinstance(second[-1], ToolMessage) and '"quantity": 2' in second[-1].content

    def test_invalid_arguments_are_fed_back_and_the_model_recovers(self):
        """Regression from CI: the model copied placeholder text as the product. The schema rejects
        it, the model sees the error listing the valid names, and its retry succeeds."""
        agent, model = agent_with(
            tool_call_message("add_to_cart", product="Product name", quantity=2),
            tool_call_message("add_to_cart", product=BACKPACK, quantity=2),
            AIMessage("Added 2 backpacks."),
        )

        turn = agent.chat("t1", "Please add 2 backpacks to my cart")

        assert [c.error for c in turn.tool_calls] == [True, False]
        feedback = model.received[1][-1]
        assert feedback.status == "error" and "Product name" in feedback.content and BACKPACK in feedback.content
        assert agent.cart("t1").items == {BACKPACK: 2}

    def test_domain_errors_are_fed_back_without_changing_the_cart(self):
        """Removing something that isn't in the cart is an error the model can explain."""
        agent, _ = agent_with(tool_call_message("remove_from_cart", product=ONESIE, quantity=1), AIMessage("You have no onesie."))
        agent.cart("t1").add(BACKPACK, 1)

        turn = agent.chat("t1", "remove the onesie")

        assert turn.tool_calls[0].error and "not in the cart" in turn.tool_calls[0].output
        assert agent.cart("t1").items == {BACKPACK: 1}

    def test_quantity_below_one_never_reaches_the_cart(self):
        """``minimum: 1`` is enforced before the tool body runs."""
        agent, _ = agent_with(tool_call_message("add_to_cart", product=BACKPACK, quantity=0), AIMessage("How many?"))

        turn = agent.chat("t1", "add zero backpacks")

        assert turn.tool_calls[0].error
        assert agent.cart("t1").items == {}

    def test_node_mode_puts_this_turns_passages_in_the_prompt(self):
        """Each turn's system prompt carries the passages retrieved for *that* message."""
        agent, model = agent_with(AIMessage("45 days."), AIMessage("$4.99."), retriever=BM25Retriever(load_documents()))

        agent.chat("t1", "How long do I have to return an item?")
        agent.chat("t1", "How much does standard shipping cost?")

        first, second = (call[0].content for call in model.received)
        assert "POLICY CONTEXT:" in first and "45 days" in first
        assert "$4.99" in second and "45 days" not in second

    def test_policy_questions_retrieve_through_the_tool(self):
        """Tool mode: the model calls search_policies and answers from the passages it got back."""
        agent, model = agent_with(
            tool_call_message("search_policies", query="return window"),
            AIMessage("You have 45 days to return an item."),
            retriever=BM25Retriever(load_documents()),
            retrieval="tool",
        )

        turn = agent.chat("t1", "How long do I have to return something?")

        assert turn.tool_names == ["search_policies"]
        assert "45 days" in model.received[1][-1].content
        assert agent.cart("t1").items == {}

    @pytest.mark.parametrize("retrieval", ["node", "tool"])
    def test_unexpected_errors_are_bugs_and_propagate(self, retrieval):
        """Only errors the model can fix are fed back; a broken dependency must fail loudly."""

        class BrokenRetriever(BM25Retriever):
            def search(self, query, k=3, min_score=None):
                raise RuntimeError("index unavailable")

        agent, _ = agent_with(
            tool_call_message("search_policies", query="returns"),
            retriever=BrokenRetriever(load_documents()),
            retrieval=retrieval,
        )

        with pytest.raises(RuntimeError, match="index unavailable"):
            agent.chat("t1", "what is the return policy?")


class TestMemoryAndBounds:
    """Checkpointer memory, thread isolation and the loop bound."""

    def test_checkpointer_remembers_earlier_turns(self):
        """The second turn's model call sees the first turn (memory is the thread's checkpoint)."""
        agent, model = agent_with(AIMessage("Hi Priya!"), AIMessage("Your name is Priya."))

        agent.chat("t1", "Hi, I'm Priya")
        agent.chat("t1", "What's my name?")

        seen = [m.content for m in model.received[1][1:]]
        assert seen == ["Hi, I'm Priya", "Hi Priya!", "What's my name?"]

    def test_threads_are_isolated(self):
        """Another thread_id has its own history and its own cart."""
        agent, model = agent_with(
            tool_call_message("add_to_cart", product=BACKPACK, quantity=1), AIMessage("Added."), AIMessage("Hello.")
        )

        agent.chat("a", "add a backpack")
        agent.chat("b", "hello")

        assert agent.cart("b").items == {}
        assert [m.content for m in model.received[-1][1:]] == ["hello"]

    def test_reset_forgets_history_and_cart(self):
        """After reset the thread starts from nothing."""
        agent, _ = agent_with(tool_call_message("add_to_cart", product=BACKPACK, quantity=1), AIMessage("Added."))
        agent.chat("t1", "add a backpack")

        agent.reset("t1")

        assert agent.history("t1") == [] and agent.cart("t1").items == {}

    #: The bound must hold with and without the retrieve node, which is one extra graph step.
    #: Regression: the limit ignored it, so a retriever cost one model call and let a tool run unreported.
    WITH_AND_WITHOUT_RETRIEVAL = pytest.mark.parametrize("retrieval", [False, True], ids=["no-retriever", "retrieve-node"])

    @WITH_AND_WITHOUT_RETRIEVAL
    def test_endless_tool_loop_is_bounded_and_the_thread_stays_usable(self, retrieval):
        """A model that never stops calling tools is cut off after max_model_calls; the history is
        closed (no unanswered tool calls), so the next turn still works."""
        loop = [tool_call_message("view_cart") for _ in range(3)]
        agent, _ = agent_with(*loop, AIMessage("Your cart is empty."), max_model_calls=3, **_retriever(retrieval))

        turn = agent.chat("t1", "what's in my cart?")

        assert (turn.reply, turn.model_calls) == (GAVE_UP_REPLY, 3)
        last_ai = [m for m in agent.history("t1") if isinstance(m, AIMessage)][-1]
        assert last_ai.content == GAVE_UP_REPLY and not last_ai.tool_calls
        assert agent.chat("t1", "and now?").reply == "Your cart is empty."

    @WITH_AND_WITHOUT_RETRIEVAL
    def test_bound_stops_before_a_tool_call_nobody_would_report(self, retrieval):
        """The last allowed model call's tool request is *not* executed: a cart change the model
        could never tell the user about is worse than no change."""
        agent, _ = agent_with(
            tool_call_message("add_to_cart", product=BACKPACK, quantity=1),
            tool_call_message("add_to_cart", product=BACKPACK, quantity=1),
            max_model_calls=2,
            **_retriever(retrieval),
        )

        turn = agent.chat("t1", "add a backpack")

        assert turn.model_calls == 2
        assert agent.cart("t1").items == {BACKPACK: 1}
        assert turn.tool_calls[-1].error and "Not executed" in turn.tool_calls[-1].output
