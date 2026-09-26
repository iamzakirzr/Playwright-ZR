"""The shop assistant agent: RAG for policy questions, tools for cart actions.

Flow for one user message::

    retrieve policy passages ─▶ LLM (with tools) ─┬─ tool calls? ─▶ run tools ─▶ LLM again (max N rounds)
                                                   └─ text ─────────▶ reply

Two guards against the classic agent failure (claiming an action it never took):

* the session history keeps the *full trajectory* (tool calls and tool results),
  so the model sees that cart changes happen through tools, not through prose;
* :func:`claims_cart_action` detects replies like "I've added..." made without a
  tool call, and the agent re-prompts once, telling the model to call the tool.

A **hybrid scope guard** keeps the agent on topic. Store vocabulary (cart,
basket, product names, policy words) is allowed by a regex without any LLM
call; only messages with none of it go to a small classifier prompt, and
anything but a clear OUT_OF_SCOPE is allowed (fail open). Measured on
qwen2.5:1.5b, the classifier alone refused "put a bike light in my basket",
which is why the allow-list comes first.

Small models sometimes echo the JSON schema instead of plain values, e.g.
``{"quantity": {"type": "integer", "value": 2}}``. :func:`normalise_arguments`
repairs that before a tool runs. Defensive parsing like this is part of any
real agent, and the test suite pins it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from ai.prompts import default_registry
from ai.search import Retriever
from apps.shop_assistant.catalog import PRODUCTS, Cart, UnknownProductError, resolve_product

MAX_TOOL_ROUNDS = 3

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to the shopping cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product name"},
                    "quantity": {"type": "integer", "minimum": 1},
                },
                "required": ["product", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove some or all of a product from the shopping cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string"},
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "How many to remove; to remove all, use the quantity shown in CURRENT CART",
                    },
                },
                "required": ["product", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Show what is in the shopping cart and its total",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = (
    "You are the Sauce Demo Store shopping assistant.\n"
    "Products: {products}.\n"
    "Use the tools to add, remove or show cart items. Every cart change needs a tool call in THIS turn, "
    "even if a similar change happened earlier in the conversation.\n"
    "CURRENT CART below is the live cart: answer questions about the cart from it, and use its quantities "
    "when the user asks to remove everything of a product.\n"
    "Politely refuse anything unrelated to shopping at the Sauce Demo Store (poems, code, general knowledge).\n"
    "For policy questions answer ONLY from the POLICY CONTEXT. If it doesn't contain the answer, reply exactly: "
    '"I don\'t know based on the provided information."\n'
    "Be concise: at most three sentences.\n\nCURRENT CART:\n{cart}\n\nPOLICY CONTEXT:\n{context}"
)


OFF_TOPIC_REPLY = "I can only help with shopping at the Sauce Demo Store: products, your cart, orders and store policies."
#: Store-specific nouns with their inflections spelled out. Verbs ("add"), greetings ("hi") and
#: open prefixes (``\w*``) are deliberately absent: "add two numbers" or "history" must not bypass
#: the classifier. Anything not matched here goes to the LLM scope check.
_STORE_VOCABULARY = re.compile(
    r"\b(carts?|baskets?|orders?|checkout|prices?|shipping|delivery|deliveries|returns?|refunds?|warrant(?:y|ies)|"
    r"payments?|paypal|store|shop|products?|backpacks?|bike lights?|t-?shirts?|jackets?|fleece|onesies?)\b",
    re.I,
)


#: A message that is *only* a greeting or thanks. Anchored, so "hi" inside "history" doesn't count.
_SMALL_TALK = re.compile(r"^\W*(hi|hello|hey|thanks|thank you|thx|cheers)\b[\s\w]{0,10}\W*$", re.I)


def mentions_store_vocabulary(text: str) -> bool:
    """True if ``text`` names a store concept or is plain small talk; such messages skip the LLM scope check."""
    return bool(_STORE_VOCABULARY.search(text) or _SMALL_TALK.match(text))


NO_TOOL_NUDGE = (
    "You described a cart change but did not call a tool, so nothing changed. "
    "Call the correct tool now (add_to_cart, remove_from_cart or view_cart)."
)
_ACTION_CLAIM = re.compile(r"\b(added|removed|put|placed|increased|updated|deleted)\b.*\b(cart|basket)\b", re.I)
_NEGATION = re.compile(r"\b(not|no|nothing|never|yet|n't|cannot)\b|n't\b", re.I)


def describe_cart(cart: Cart) -> str:
    """One line per item plus the total, as the model sees it in CURRENT CART.

    Giving the model the live cart every turn means it never has to remember or guess it:
    before this, asked "what's in my cart now?", it invented three items and a total.
    """
    if not cart.items:
        return "(empty)"
    lines = [f"- {quantity} x {product}" for product, quantity in sorted(cart.items.items())]
    return "\n".join([*lines, f"Total: ${cart.total:.2f}"])


def claims_cart_action(text: str) -> bool:
    """True if a sentence of ``text`` states a cart change ("I've added 2 backpacks to your cart").

    Questions ("Would you like me to put it in your basket?") and negations ("nothing has been
    added to your cart yet") are not claims, so they don't trigger the no-tool nudge.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        if _ACTION_CLAIM.search(sentence) and not sentence.rstrip().endswith("?") and not _NEGATION.search(sentence):
            return True
    return False


@dataclass
class ToolCall:
    """One executed tool call, as reported to the client (and to DeepEval's ToolCorrectnessMetric)."""

    name: str
    arguments: dict[str, Any]
    output: dict[str, Any]


@dataclass
class AgentReply:
    """What the agent returns for one user message."""

    reply: str
    tools_called: list[ToolCall] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def normalise_arguments(arguments: Any) -> dict[str, Any]:
    """Repair common small-model tool-argument mistakes.

    Handles a JSON string instead of an object, and object-shaped values seen from
    qwen2.5:1.5b: schema echoes (``{"type": "integer", "value": 2}``,
    ``{"description": "Backpack"}``) and cart-line copies (``{"quantity": 3, "type":
    "Sauce Labs Backpack"}``). The first plain value wins, skipping JSON-schema type names.
    """
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return {}
    if not isinstance(arguments, dict):
        return {}
    return {key: _plain_value(value) for key, value in arguments.items()}


_SCHEMA_TYPES = {"string", "integer", "number", "boolean", "object", "array", "null"}
_VALUE_KEYS = ("value", "description", "default", "name", "product", "type")


def _plain_value(value: Any) -> Any:
    """The usable value inside an object-shaped argument, or the value itself."""
    if not isinstance(value, dict):
        return value
    for key in _VALUE_KEYS:
        candidate = value.get(key)
        if candidate is not None and not (isinstance(candidate, str) and candidate.lower() in _SCHEMA_TYPES):
            return candidate
    return None


class ShopAgent:
    """Stateful agent: one conversation history and one cart per session id.

    Args:
        retriever: Search over the policy knowledge base.
        ollama_host: Ollama base URL.
        model: Tool-capable Ollama model.
        k: Policy passages to retrieve per message.
    """

    def __init__(self, retriever: Retriever, ollama_host: str, model: str, k: int = 3) -> None:
        """Create the ShopAgent; arguments are described in the class docstring."""
        self.retriever = retriever
        self.ollama_host = ollama_host.rstrip("/")
        self.model = model
        self.k = k
        self.histories: dict[str, list[dict]] = {}
        self.carts: dict[str, Cart] = {}

    # -- session state ------------------------------------------------------
    def cart(self, session_id: str) -> Cart:
        """The cart for ``session_id``, created on first use."""
        return self.carts.setdefault(session_id, Cart())

    def reset(self, session_id: str) -> None:
        """Forget a session's history and cart."""
        self.histories.pop(session_id, None)
        self.carts.pop(session_id, None)

    # -- tools --------------------------------------------------------------
    def run_tool(self, session_id: str, name: str, raw_arguments: Any) -> ToolCall:
        """Execute one tool call against the session's cart; errors become tool output, not crashes."""
        args = normalise_arguments(raw_arguments)
        cart = self.cart(session_id)
        try:
            if name == "remove_from_cart" and not args.get("product") and len(cart.items) == 1:
                # Unambiguous from state, not from parsing words: the cart holds one kind of item.
                args["product"] = next(iter(cart.items))
            if name in {"add_to_cart", "remove_from_cart"} and not args.get("product"):
                raise ValueError(f"product is required: call {name} again with the product name from the catalogue")
            if name == "add_to_cart":
                product = resolve_product(str(args.get("product", "")))
                raw_quantity = args.get("quantity")
                quantity = 1 if raw_quantity in (None, "") else int(raw_quantity)  # 0 must reach Cart.add's check
                cart.add(product, quantity)
                args = {"product": product, "quantity": quantity}
                output = {"ok": True, "cart": cart.as_dict()}
            elif name == "remove_from_cart":
                product = resolve_product(str(args.get("product", "")))
                if args.get("quantity") in (None, ""):
                    # Required by the schema; an explicit error lets the model correct itself next round
                    # instead of the agent guessing "all" or "one".
                    raise ValueError("quantity is required: how many to remove (see CURRENT CART)")
                quantity = int(args["quantity"])
                args = {"product": product, "quantity": quantity}
                output = {"ok": cart.remove(product, quantity), "cart": cart.as_dict()}
            elif name == "view_cart":
                output = {"ok": True, "cart": cart.as_dict()}
            else:
                output = {"ok": False, "error": f"unknown tool {name}"}
        except (UnknownProductError, ValueError) as exc:
            output = {"ok": False, "error": str(exc)}
        return ToolCall(name=name, arguments=args, output=output)

    # -- scope guard ----------------------------------------------------------
    def is_out_of_scope(self, message: str) -> bool:
        """Hybrid guard: store vocabulary means in scope; otherwise ask the classifier (fail open)."""
        if mentions_store_vocabulary(message):
            return False
        prompt = default_registry().get("scope_guard").render(message=message)
        verdict = self._chat(
            [{"role": "system", "content": prompt.system}, {"role": "user", "content": prompt.user}], tools=False
        )
        return "OUT_OF_SCOPE" in (verdict.get("content") or "").upper()

    # -- LLM ----------------------------------------------------------------
    def _chat(self, messages: list[dict], tools: bool = True) -> dict:
        """One non-streaming call to Ollama, offering the cart tools unless ``tools`` is False."""
        payload = {"model": self.model, "stream": False, "options": {"temperature": 0, "seed": 42}, "messages": messages}
        if tools:
            payload["tools"] = TOOLS
        response = httpx.post(f"{self.ollama_host}/api/chat", json=payload, timeout=300)
        response.raise_for_status()
        return response.json()["message"]

    def handle(self, session_id: str, message: str) -> AgentReply:
        """Answer one user message as an atomic turn.

        If anything fails mid-turn (Ollama timeout, 5xx), the session's history and cart are
        restored, so a client retry doesn't see a duplicated message or double-applied tool calls.
        """
        history = self.histories.setdefault(session_id, [])
        cart = self.cart(session_id)
        history_checkpoint, cart_checkpoint = len(history), dict(cart.items)
        try:
            return self._handle(session_id, message)
        except Exception:
            del history[history_checkpoint:]
            cart.items = cart_checkpoint
            raise

    def _handle(self, session_id: str, message: str) -> AgentReply:
        """Answer one user message, running tools as the model requests (bounded by MAX_TOOL_ROUNDS)."""
        if self.is_out_of_scope(message):
            return AgentReply(reply=OFF_TOPIC_REPLY)
        results = self.retriever.search(message, k=self.k)
        system = SYSTEM_PROMPT.format(
            products=", ".join(f"{p} (${price})" for p, price in PRODUCTS.items()),
            cart=describe_cart(self.cart(session_id)),
            context="\n".join(f"- {r.document.text}" for r in results),
        )
        history = self.histories.setdefault(session_id, [])
        history.append({"role": "user", "content": message})
        calls: list[ToolCall] = []
        nudged = False
        false_claim = None

        for _ in range(MAX_TOOL_ROUNDS):
            reply = self._chat([{"role": "system", "content": system}, *history])
            tool_requests = reply.get("tool_calls") or []
            if not tool_requests:
                if not calls and not nudged and claims_cart_action(reply.get("content", "")):
                    # Guard: the model narrated an action without doing it. Ask once more.
                    nudged = True
                    false_claim = reply.get("content", "")
                    history.append({"role": "assistant", "content": reply.get("content", "")})
                    history.append({"role": "user", "content": NO_TOOL_NUDGE})
                    continue
                break
            history.append({"role": "assistant", "content": reply.get("content", ""), "tool_calls": tool_requests})
            for request in tool_requests:
                fn = request["function"]
                call = self.run_tool(session_id, fn["name"], fn.get("arguments", {}))
                calls.append(call)
                history.append({"role": "tool", "content": json.dumps(call.output)})
        text = (reply.get("content") or "").strip() or self._summarise(calls)
        if nudged:
            # Drop the false claim and the nudge from future turns; keep the real trajectory.
            history[:] = [
                m
                for m in history
                if m.get("content") != NO_TOOL_NUDGE
                and not (m["role"] == "assistant" and m.get("content") == false_claim and "tool_calls" not in m)
            ]
        history.append({"role": "assistant", "content": text})
        return AgentReply(reply=text, tools_called=calls, sources=[r.document.id for r in results])

    @staticmethod
    def _summarise(calls: list[ToolCall]) -> str:
        """Fallback text when the model returns tool calls but no words."""
        if not calls:
            return "Sorry, I couldn't process that."
        last = calls[-1]
        if not last.output.get("ok"):
            return f"Sorry, I couldn't do that: {last.output.get('error', 'unknown error')}."
        cart = last.output["cart"]
        lines = ", ".join(f"{i['quantity']} x {i['product']}" for i in cart["items"]) or "empty"
        return f"Your cart: {lines}. Total ${cart['total']:.2f}."
