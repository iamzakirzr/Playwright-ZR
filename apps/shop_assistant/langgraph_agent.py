"""The shop assistant rebuilt as a LangGraph agent: how agents are *developed* with LangChain.

``agent.py`` in this package is a hand-written tool loop over Ollama's HTTP API. This module
builds the same assistant the way most teams do today, with LangChain tools and a LangGraph
state machine, so the two can be compared and tested side by side::

    START -> retrieve -> agent --(tool calls?)--> tools -> agent -> ... -> END
                               \\--(no tool calls)--> END

Building blocks (each one is something a test can pin down):

* **Tools** are plain Python functions decorated with ``@tool``. Their type hints *are* the
  schema the model sees: ``Literal[...]`` of catalogue names becomes an ``enum`` (the fix for the
  "Product name" placeholder bug in ``agent.py``), ``Field(ge=1)`` becomes ``minimum: 1``.
* **Invalid arguments are fed back, not repaired.** ``ToolNode`` validates each call against the
  schema; a violation comes back to the model as an error ``ToolMessage`` it can correct on the
  next step. Compare ``normalise_arguments`` in ``agent.py``, which repairs arguments by hand.
* **Memory is a checkpointer.** The graph is compiled with ``InMemorySaver``; each conversation is
  a ``thread_id`` in the run config, so multi-turn memory needs no hand-kept history.
* **Per-session state comes from the run config.** Tools receive the ``RunnableConfig``
  (injected by LangChain, invisible to the model) and use its ``thread_id`` to find the cart.
* **The live cart is in the system prompt on every model call**, rebuilt from the cart itself,
  the lesson ``agent.py`` learned the hard way.
* **Retrieval is a graph node, not a model decision** (``retrieval="node"``, the default). The
  ``retrieve`` node searches the policies for every user message and the passages go into the
  system prompt. The alternative, agentic RAG (``retrieval="tool"``: a ``search_policies`` tool the
  model may call), was measured first: qwen2.5:1.5b called the tool in **0 of 6** policy questions,
  even when told to ALWAYS call it, and invented policy instead ("30 days" for a 45-day window).
  When the model can't be trusted with a decision, make it an edge in the graph. Tool mode stays
  available for stronger models and is covered by the offline tests.
* **Loops are bounded** by LangGraph's ``recursion_limit``; hitting it ends the turn politely.

Example::

    from langchain_ollama import ChatOllama

    agent = LangGraphShopAgent(ChatOllama(model="qwen2.5:1.5b", temperature=0), retriever=retriever)
    turn = agent.chat("session-1", "add 2 backpacks")
    turn.reply, turn.tool_calls, agent.cart("session-1").items
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.prebuilt.tool_node import ToolInvocationError
from pydantic import Field

from ai.search.base import Retriever
from apps.shop_assistant.catalog import PRODUCTS, Cart, cart_lines

#: The product argument's type: exactly the catalogue names, so the tool schema is an ``enum``.
ProductName = Literal[tuple(PRODUCTS)]  # type: ignore[valid-type]

#: Model calls allowed per user turn. Each tool round costs two graph steps (agent, tools).
MAX_MODEL_CALLS = 4

GAVE_UP_REPLY = "Sorry, I couldn't finish that request. Please try rephrasing it."

#: How policy questions get their evidence: a graph node every turn, or a tool the model may call.
Retrieval = Literal["node", "tool"]

_POLICY_RULE = {
    "node": "Answer store policy questions ONLY from the POLICY CONTEXT below; if it doesn't contain the answer, "
    "say you don't know.",
    "tool": "For store policy questions (returns, shipping, warranty, support, payments) call search_policies and "
    "answer only from what it returns; if it has no answer, say you don't know.",
}

SYSTEM_PROMPT = (
    "You are the Sauce Demo Store shopping assistant.\n"
    "Use the tools to add, remove or show cart items. Every cart change needs a tool call in this turn.\n"
    "{policy_rule}\n"
    "Politely refuse anything unrelated to the store. Be concise: at most three sentences.\n\n"
    "CURRENT CART (live):\n{cart}"
)


class ShopState(MessagesState):
    """Graph state: the conversation plus the policy passages retrieved for the current turn."""

    policy_context: list[str]


@dataclass(frozen=True)
class ToolCallRecord:
    """One tool call the agent made during a turn, with what the tool returned.

    Attributes:
        name: Tool name.
        arguments: Arguments the model sent.
        output: The tool's result text (an error message if the call failed).
        error: True when the tool call failed (bad arguments, unknown product, ...).
    """

    name: str
    arguments: dict[str, Any]
    output: str
    error: bool = False


@dataclass
class AgentTurn:
    """The result of one user message.

    Attributes:
        reply: The assistant's final text.
        tool_calls: Every tool call made this turn, in order (the agent's *trajectory*).
        model_calls: How many times the model was called this turn.
    """

    reply: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    model_calls: int = 0

    @property
    def tool_names(self) -> list[str]:
        """Names of the tools called, in order: the shape trajectory assertions compare."""
        return [call.name for call in self.tool_calls]


def describe_cart(cart: Cart) -> str:
    """The cart as the model sees it in the system prompt."""
    view = cart.as_dict()
    if not view["items"]:
        return "(empty)"
    return "\n".join(f"- {line}" for line in cart_lines(view)) + f"\nTotal: ${view['total']:.2f}"


class LangGraphShopAgent:
    """Tool-calling shopping agent built with LangChain tools and a LangGraph graph.

    Args:
        llm: Any LangChain chat model that supports tool calling (``ChatOllama`` in live tests,
            a scripted fake in unit tests).
        retriever: Policy search; None means the agent has no policy knowledge.
        retrieval: ``"node"`` retrieves for every message before the model runs (reliable with
            small models); ``"tool"`` offers ``search_policies`` and lets the model decide.
        k: Passages retrieved per search.
        max_model_calls: Upper bound on model calls per turn (enforced via ``recursion_limit``).
    """

    def __init__(
        self,
        llm: BaseChatModel,
        retriever: Retriever | None = None,
        retrieval: Retrieval = "node",
        k: int = 2,
        max_model_calls: int = MAX_MODEL_CALLS,
    ) -> None:
        """Create the agent; arguments are described in the class docstring."""
        self.retriever = retriever
        self.retrieval = retrieval
        self.k = k
        self.max_model_calls = max_model_calls
        self.carts: dict[str, Cart] = {}
        self.tools: list[BaseTool] = self._make_tools()
        self.llm = llm.bind_tools(self.tools)
        self.graph: CompiledStateGraph = self._build_graph().compile(checkpointer=InMemorySaver())

    # -- session state ------------------------------------------------------
    def cart(self, thread_id: str) -> Cart:
        """The cart for ``thread_id``, created on first use."""
        return self.carts.setdefault(thread_id, Cart())

    def history(self, thread_id: str) -> list[BaseMessage]:
        """Every message the checkpointer holds for ``thread_id`` (the conversation memory)."""
        snapshot = self.graph.get_state(self._config(thread_id))
        return list(snapshot.values.get("messages", []))

    def reset(self, thread_id: str) -> None:
        """Forget a thread's cart and conversation."""
        self.carts.pop(thread_id, None)
        self.graph.checkpointer.delete_thread(thread_id)

    # -- tools ----------------------------------------------------------------
    def _make_tools(self) -> list[BaseTool]:
        """The agent's tools. Closures over ``self`` give them the per-thread carts."""

        def cart_for(config: RunnableConfig) -> Cart:
            return self.cart(config["configurable"]["thread_id"])

        @tool
        def add_to_cart(product: ProductName, quantity: Annotated[int, Field(ge=1)], config: RunnableConfig) -> dict:
            """Add a quantity of a catalogue product to the shopping cart."""
            cart = cart_for(config)
            cart.add(product, quantity)
            return cart.as_dict()

        @tool
        def remove_from_cart(
            product: ProductName,
            quantity: Annotated[int, Field(ge=1, description="How many to remove; to remove all, use the CURRENT CART quantity")],
            config: RunnableConfig,
        ) -> dict:
            """Remove some or all of a product from the shopping cart."""
            cart = cart_for(config)
            if not cart.remove(product, quantity):
                raise ValueError(f"{product} is not in the cart")
            return cart.as_dict()

        @tool
        def view_cart(config: RunnableConfig) -> dict:
            """Show what is in the shopping cart and its total."""
            return cart_for(config).as_dict()

        tools: list[BaseTool] = [add_to_cart, remove_from_cart, view_cart]
        if self.retriever is not None and self.retrieval == "tool":

            @tool
            def search_policies(query: str) -> list[str]:
                """Search the store's policies (returns, shipping, warranty, support, payments)."""
                return self._search(query)

            tools.append(search_policies)
        return tools

    # -- graph ----------------------------------------------------------------
    def _search(self, query: str) -> list[str]:
        """Policy passages for ``query``."""
        return [hit.document.text for hit in self.retriever.search(query, k=self.k)]

    def _build_graph(self) -> StateGraph:
        """[retrieve ->] agent -> (tools -> agent)* -> END, routed by whether the model asked for tools."""
        graph = StateGraph(ShopState)
        graph.add_node("agent", self._call_model)
        # Errors a model can fix go back to it as an error ToolMessage: schema violations
        # (ToolInvocationError, e.g. "Product name" is not in the enum) and domain errors
        # (ValueError, e.g. removing what isn't in the cart). Anything else is a bug and propagates.
        graph.add_node("tools", ToolNode(self.tools, handle_tool_errors=(ToolInvocationError, ValueError)))
        if self.retriever is not None and self.retrieval == "node":
            graph.add_node("retrieve", self._retrieve)
            graph.add_edge(START, "retrieve")
            graph.add_edge("retrieve", "agent")
        else:
            graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
        return graph

    def _retrieve(self, state: ShopState) -> dict:
        """The ``retrieve`` node: policy passages for this turn's user message."""
        question = next(m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
        return {"policy_context": self._search(str(question))}

    def _call_model(self, state: ShopState, config: RunnableConfig) -> dict:
        """The ``agent`` node: rules, live cart and (node mode) policy context, then the conversation."""
        cart = self.cart(config["configurable"]["thread_id"])
        mode = self.retrieval if self.retriever is not None else "node"
        prompt = SYSTEM_PROMPT.format(policy_rule=_POLICY_RULE[mode], cart=describe_cart(cart))
        if mode == "node":
            passages = state.get("policy_context") or []
            prompt += "\n\nPOLICY CONTEXT:\n" + ("\n".join(f"- {p}" for p in passages) or "(none)")
        return {"messages": [self.llm.invoke([SystemMessage(prompt), *state["messages"]], config)]}

    def _config(self, thread_id: str) -> RunnableConfig:
        """Run config: the thread (memory + cart) and the loop bound."""
        # Steps: agent, tools, agent, ..., agent. 2n - 1 allows n model calls and stops *before* a
        # tools step whose result no model call would ever see (a silent cart change).
        return {"configurable": {"thread_id": thread_id}, "recursion_limit": 2 * self.max_model_calls - 1}

    # -- public API -------------------------------------------------------------
    def chat(self, thread_id: str, message: str) -> AgentTurn:
        """Run one user turn and return the reply plus the tool trajectory of this turn only."""
        config = self._config(thread_id)
        before = len(self.history(thread_id))
        try:
            self.graph.invoke({"messages": [HumanMessage(message)]}, config)
        except GraphRecursionError:
            model_calls = _model_calls(self.history(thread_id)[before:])  # before the agent's own reply
            self._close_turn(thread_id)
            return AgentTurn(GAVE_UP_REPLY, _trajectory(self.history(thread_id)[before:]), model_calls)
        new = self.history(thread_id)[before:]
        reply = str(new[-1].content) if new and isinstance(new[-1], AIMessage) else ""
        return AgentTurn(reply, _trajectory(new), _model_calls(new))

    def _close_turn(self, thread_id: str) -> None:
        """After hitting the loop bound, answer the dangling tool calls and end with the give-up reply.

        Without this the saved conversation ends in tool calls nobody answered, and chat models
        reject such a history on the next turn.
        """
        last = self.history(thread_id)[-1]
        unanswered = last.tool_calls if isinstance(last, AIMessage) else []
        skipped = [
            ToolMessage("Not executed: step limit reached.", tool_call_id=call["id"], status="error") for call in unanswered
        ]
        self.graph.update_state(self._config(thread_id), {"messages": [*skipped, AIMessage(GAVE_UP_REPLY)]})


def _model_calls(messages: list[BaseMessage]) -> int:
    """Model calls in a turn = AI messages in it."""
    return sum(isinstance(m, AIMessage) for m in messages)


def _trajectory(messages: list[BaseMessage]) -> list[ToolCallRecord]:
    """Pair each tool call the model made with the ToolMessage that answered it."""
    results = {m.tool_call_id: m for m in messages if isinstance(m, ToolMessage)}
    records = []
    for message in messages:
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                result = results.get(call["id"])
                records.append(
                    ToolCallRecord(
                        name=call["name"],
                        arguments=dict(call["args"]),
                        output=str(result.content) if result else "",
                        error=bool(result and result.status == "error"),
                    )
                )
    return records
