"""Offline unit tests for the shop assistant: catalogue, tool execution and the agent loop.

The LLM is replaced with a scripted one (overriding ``_chat``), so the tool
loop, argument repair and fallbacks are tested deterministically in milliseconds.
"""

import pytest
from fastapi.testclient import TestClient

from ai.search import BM25Retriever, load_documents
from apps.shop_assistant import main
from apps.shop_assistant.agent import (
    MAX_TOOL_ROUNDS,
    NO_TOOL_NUDGE,
    OFF_TOPIC_REPLY,
    ShopAgent,
    asks_about_cart,
    claims_cart_action,
    mentions_store_vocabulary,
    normalise_arguments,
)
from apps.shop_assistant.catalog import Cart, UnknownProductError, resolve_product


class ScriptedShopAgent(ShopAgent):
    """ShopAgent whose LLM replies come from a list (a test double)."""

    def __init__(self, replies: list[dict]) -> None:
        """Use a keyword retriever (no model download) and queue ``replies``."""
        super().__init__(BM25Retriever(load_documents()), "http://unused", "scripted")
        self.replies = list(replies)
        self.sent: list[list[dict]] = []

    def _chat(self, messages: list[dict], tools: bool = True) -> dict:
        """Record what would have been sent and return the next scripted reply."""
        self.sent.append(messages)
        return self.replies.pop(0)


#: Scripted classifier verdict for messages without store nouns ("add it"), which consult the scope guard first.
IN_SCOPE = {"content": "IN_SCOPE"}


def tool_reply(name: str, arguments) -> dict:
    """An Ollama-shaped assistant message that requests one tool call."""
    return {"content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


class TestArgumentRepair:
    """Small models often send malformed tool arguments; the agent must repair them."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ({"product": "Backpack", "quantity": 2}, {"product": "Backpack", "quantity": 2}),
            ({"quantity": {"type": "integer", "value": 2}}, {"quantity": 2}),
            ({"product": {"description": "Sauce Labs Backpack", "type": "string"}}, {"product": "Sauce Labs Backpack"}),
            ('{"product": "Onesie"}', {"product": "Onesie"}),
            ("not json", {}),
            (None, {}),
        ],
        ids=["clean", "schema-value", "schema-description", "json-string", "garbage", "none"],
    )
    def test_normalise_arguments(self, raw, expected):
        """Each malformed shape seen from qwen2.5:1.5b is mapped to plain values."""
        assert normalise_arguments(raw) == expected


class TestCatalog:
    """Product matching and cart arithmetic."""

    @pytest.mark.parametrize(
        ("loose", "exact"),
        [
            ("backpack", "Sauce Labs Backpack"),
            ("Bike Lights", "Sauce Labs Bike Light"),
            ("fleece jacket", "Sauce Labs Fleece Jacket"),
            # Seen from qwen2.5:1.5b: the product description passed as the name.
            ("Soft and comfortable onesie for all your little ones.", "Sauce Labs Onesie"),
        ],
        ids=["short", "plural", "partial", "description"],
    )
    def test_resolve_product(self, loose, exact):
        """Loose names map to catalogue names."""
        assert resolve_product(loose) == exact

    @pytest.mark.parametrize("name", ["", "  ", "s", "labs", "sauce", "Sauce Labs", "item"])
    def test_empty_or_generic_names_match_nothing(self, name):
        """Regression: "" was a substring of every name, so a missing product added a backpack."""
        with pytest.raises(UnknownProductError):
            resolve_product(name)

    def test_unknown_product_is_rejected(self):
        """Nothing is guessed for an unrelated name."""
        with pytest.raises(UnknownProductError):
            resolve_product("laptop")

    def test_cart_total_and_quantities(self):
        """Adding twice accumulates quantity; the total is rounded to cents."""
        cart = Cart()
        cart.add("Sauce Labs Backpack", 2)
        cart.add("Sauce Labs Backpack")
        cart.add("Sauce Labs Onesie")
        assert cart.items == {"Sauce Labs Backpack": 3, "Sauce Labs Onesie": 1}
        assert cart.total == round(3 * 29.99 + 7.99, 2)

    def test_partial_removal(self):
        """Regression: "remove one backpack" emptied the cart because remove() had no quantity."""
        cart = Cart()
        cart.add("Sauce Labs Backpack", 2)

        assert cart.remove("Sauce Labs Backpack", 1)
        assert cart.items == {"Sauce Labs Backpack": 1}
        assert cart.remove("Sauce Labs Backpack", 5)  # more than present removes the line
        assert cart.items == {}
        assert not cart.remove("Sauce Labs Backpack")

    def test_quantity_must_be_positive(self):
        """Zero or negative quantities are refused."""
        with pytest.raises(ValueError):
            Cart().add("Sauce Labs Onesie", 0)


class TestAgentLoop:
    """The tool-calling loop, with a scripted model."""

    def test_tool_call_updates_cart_and_is_reported(self):
        """A requested tool runs against the session cart and appears in ``tools_called``."""
        agent = ScriptedShopAgent([tool_reply("add_to_cart", {"product": "backpack", "quantity": 2}), {"content": "Added."}])

        result = agent.handle("s1", "add 2 backpacks")

        assert agent.cart("s1").items == {"Sauce Labs Backpack": 2}
        assert [(c.name, c.arguments) for c in result.tools_called] == [
            ("add_to_cart", {"product": "Sauce Labs Backpack", "quantity": 2})
        ]
        assert result.reply == "Added."

    def test_tool_result_is_fed_back_to_the_model(self):
        """The second model call sees the tool output as a ``tool`` message."""
        agent = ScriptedShopAgent([tool_reply("view_cart", {}), {"content": "Empty."}])
        agent.handle("s1", "what's in my cart")

        assert agent.sent[1][-1]["role"] == "tool"
        assert '"total": 0' in agent.sent[1][-1]["content"]

    def test_unknown_product_becomes_a_polite_error_not_a_crash(self):
        """A bad tool argument is reported back; the fallback reply explains it."""
        agent = ScriptedShopAgent([IN_SCOPE, tool_reply("add_to_cart", {"product": "laptop", "quantity": 1}), {"content": ""}])

        result = agent.handle("s1", "add a laptop")

        assert result.tools_called[0].output["ok"] is False
        assert "couldn't" in result.reply
        assert agent.cart("s1").items == {}

    def test_zero_quantity_is_an_error_not_one_item(self):
        """Regression: ``quantity or 1`` turned 0 into 1 and skipped Cart.add's validation."""
        agent = ScriptedShopAgent([tool_reply("add_to_cart", {"product": "backpack", "quantity": 0}), {"content": "ok"}])

        call = agent.handle("s1", "set backpacks to 0").tools_called[0]

        assert call.output == {"ok": False, "error": "quantity must be at least 1"}
        assert agent.cart("s1").items == {}

    def test_remove_tool_honours_quantity(self):
        """The model can remove some of a product; omitting quantity still removes all."""
        agent = ScriptedShopAgent(
            [
                tool_reply("add_to_cart", {"product": "backpack", "quantity": 3}),
                tool_reply("remove_from_cart", {"product": "backpack", "quantity": 1}),
                {"content": "ok"},
            ]
        )

        agent.handle("s1", "add 3 backpacks then remove one")

        assert agent.cart("s1").items == {"Sauce Labs Backpack": 2}

    @pytest.mark.parametrize(
        ("message", "left"),
        [("remove one backpack", 2), ("please take out 2 backpacks", 1), ("remove the backpack", 0), ("remove a backpack", 2)],
    )
    def test_removal_count_falls_back_to_the_users_words(self, message, left):
        """Regression: the 1.5B model omits quantity, so "remove one" removed all three."""
        agent = ScriptedShopAgent([tool_reply("remove_from_cart", {"product": "backpack"}), {"content": "ok"}])
        agent.cart("s1").add("Sauce Labs Backpack", 3)

        agent.handle("s1", message)

        assert agent.cart("s1").items.get("Sauce Labs Backpack", 0) == left

    def test_count_applies_only_to_the_product_it_names(self):
        """In "remove one backpack and the jacket", only the backpack has a count."""
        agent = ScriptedShopAgent(
            [
                {
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "remove_from_cart", "arguments": {"product": "backpack"}}},
                        {"function": {"name": "remove_from_cart", "arguments": {"product": "fleece jacket"}}},
                    ],
                },
                {"content": "ok"},
            ]
        )
        agent.cart("s1").add("Sauce Labs Backpack", 3)
        agent.cart("s1").add("Sauce Labs Fleece Jacket", 2)

        agent.handle("s1", "remove one backpack and the jacket")

        assert agent.cart("s1").items == {"Sauce Labs Backpack": 2}

    def test_cart_question_is_answered_from_the_real_cart(self):
        """Regression: asked "what's in my cart now?", the model invented three items without a tool."""
        agent = ScriptedShopAgent([{"content": "You have 1 backpack, 1 bike light and 1 t-shirt ($49.98)."}])
        agent.cart("s1").add("Sauce Labs Backpack", 1)

        result = agent.handle("s1", "What's in my cart now?")

        assert [c.name for c in result.tools_called] == ["view_cart"]
        assert result.reply == "Your cart: 1 x Sauce Labs Backpack. Total $29.99."

    @pytest.mark.parametrize(
        ("message", "is_cart_question"),
        [
            ("What's in my cart now?", True),
            ("show me my basket", True),
            ("how many items are in my cart", True),
            ("add 2 backpacks to my cart", False),
            ("What is your return policy?", False),
        ],
    )
    def test_cart_question_detection(self, message, is_cart_question):
        """Only questions about cart contents trigger the grounded answer."""
        assert asks_about_cart(message) is is_cart_question

    def test_missing_product_adds_nothing(self):
        """Regression: a tool call without a product used to add a Sauce Labs Backpack."""
        agent = ScriptedShopAgent([IN_SCOPE, tool_reply("add_to_cart", {"quantity": 2}), {"content": "ok"}])

        call = agent.handle("s1", "add two").tools_called[0]

        assert call.output["ok"] is False
        assert agent.cart("s1").items == {}

    def test_failed_turn_rolls_back_history_and_cart(self):
        """Regression: a mid-turn LLM failure left the message (and any tool effects) behind,
        so a client retry double-applied them."""

        class FlakyAgent(ScriptedShopAgent):
            def _chat(self, messages, tools=True):
                if not self.replies:
                    raise TimeoutError("ollama timed out")
                return super()._chat(messages, tools)

        agent = FlakyAgent([tool_reply("add_to_cart", {"product": "backpack", "quantity": 2})])
        with pytest.raises(TimeoutError):
            agent.handle("s1", "add 2 backpacks")

        assert agent.histories["s1"] == []
        assert agent.cart("s1").items == {}

    def test_tool_rounds_are_bounded(self):
        """A model stuck in a tool loop is cut off after MAX_TOOL_ROUNDS model calls."""
        agent = ScriptedShopAgent([tool_reply("view_cart", {})] * (MAX_TOOL_ROUNDS + 5))

        agent.handle("s1", "show my cart again and again")

        assert len(agent.sent) == MAX_TOOL_ROUNDS

    def test_sessions_are_isolated(self):
        """Two sessions never share a cart or a history."""
        agent = ScriptedShopAgent([tool_reply("add_to_cart", {"product": "onesie", "quantity": 1}), {"content": "ok"}])
        agent.handle("a", "add a onesie")

        assert agent.cart("b").items == {}
        assert "b" not in agent.histories

    def test_policy_context_is_retrieved_into_system_prompt(self):
        """RAG: the passage about the return window is in the system prompt for a returns question."""
        agent = ScriptedShopAgent([{"content": "45 days."}])
        result = agent.handle("s1", "what is the return window for items")

        assert "returns-1" in result.sources
        assert "45 days" in agent.sent[0][0]["content"]


class TestActionClaimGuard:
    """The agent must not claim a cart change it never made."""

    @pytest.mark.parametrize(
        ("text", "claims"),
        [
            ("I've added 2 backpacks to your cart.", True),
            ("The onesie has been removed from your cart.", True),
            ("Your cart contains 1 bike light.", False),
            ("You have 45 days to return an item.", False),
            # Regressions: negations and offers are not claims, and must not trigger the nudge.
            ("Your cart is empty; nothing has been added to your cart yet.", False),
            ("Would you like me to put it in your basket?", False),
            ("I haven't added anything to your cart.", False),
            ("Sure. I've added the jacket to your cart. Anything else?", True),
        ],
    )
    def test_claims_cart_action(self, text, claims):
        """Narrated cart changes are detected; descriptions and policy answers are not."""
        assert claims_cart_action(text) is claims

    def test_false_claim_triggers_one_nudge_then_tool_call(self):
        """A narrated-but-not-done action is retried once; the real tool then runs."""
        agent = ScriptedShopAgent(
            [
                IN_SCOPE,
                {"content": "I've added one more bike light to your cart."},
                tool_reply("add_to_cart", {"product": "bike light", "quantity": 1}),
                {"content": "Done."},
            ]
        )

        result = agent.handle("s1", "add one more of the same")

        assert agent.cart("s1").items == {"Sauce Labs Bike Light": 1}
        assert [c.name for c in result.tools_called] == ["add_to_cart"]
        assert agent.sent[2][-1]["content"] == NO_TOOL_NUDGE  # sent[0] is the scope check

    def test_false_claim_and_nudge_are_removed_from_history(self):
        """Later turns never see the false claim or the internal nudge."""
        agent = ScriptedShopAgent(
            [
                {"content": "I've added a onesie to your cart."},
                tool_reply("add_to_cart", {"product": "onesie", "quantity": 1}),
                {"content": "Done."},
            ]
        )
        agent.handle("s1", "add a onesie")

        contents = [m.get("content") for m in agent.histories["s1"]]
        assert NO_TOOL_NUDGE not in contents
        assert "I've added a onesie to your cart." not in contents

    def test_only_one_nudge_per_turn(self):
        """A model that keeps narrating is not nudged forever; the second claim is returned as is."""
        claim = {"content": "I've added it to your cart."}
        agent = ScriptedShopAgent([IN_SCOPE, claim, claim])

        result = agent.handle("s1", "add it")

        assert len(agent.sent) == 3  # scope check + claim + one nudged retry
        assert result.tools_called == []


class TestScopeGuard:
    """Hybrid scope guard: regex allow-list first, LLM classifier only for the rest."""

    @pytest.mark.parametrize(
        "message",
        ["Please put a bike light in my basket", "Add 2 backpacks", "Is shipping free?", "thanks!", "remove the onesie"],
    )
    def test_store_messages_skip_the_llm(self, message):
        """Store vocabulary is recognised without spending a model call (and can't be misclassified)."""
        assert mentions_store_vocabulary(message)

    @pytest.mark.parametrize(
        "message",
        [
            "write a poem about history",
            "tell me about high school",
            "write python code to add two numbers",
            "which card game should I learn",
            "hi, can you summarise the French revolution for me",
        ],
    )
    def test_unrelated_messages_go_to_the_classifier(self, message):
        r"""Regression: open prefixes (``hi\w*``, ``add``) let these bypass the scope classifier."""
        assert not mentions_store_vocabulary(message)

    def test_off_topic_message_is_refused_without_tools(self):
        """A clear OUT_OF_SCOPE verdict returns the fixed reply; no tools, no RAG."""
        agent = ScriptedShopAgent([{"content": "OUT_OF_SCOPE"}])

        result = agent.handle("s1", "Write me a haiku about the ocean")

        assert result.reply == OFF_TOPIC_REPLY
        assert result.tools_called == [] and result.sources == []
        assert len(agent.sent) == 1

    @pytest.mark.parametrize("verdict", ["IN_SCOPE", "", "hmm, not sure"])
    def test_unclear_verdict_fails_open(self, verdict):
        """Anything but a clear OUT_OF_SCOPE lets the message through to the assistant."""
        agent = ScriptedShopAgent([{"content": verdict}, {"content": "Hello!"}])

        assert agent.handle("s1", "what can you do for me").reply == "Hello!"


class TestHttpContract:
    """API contract via FastAPI's in-process TestClient (the model is scripted)."""

    @pytest.fixture
    def client(self, monkeypatch):
        """TestClient whose agent is scripted to add one onesie."""
        agent = ScriptedShopAgent(
            [tool_reply("add_to_cart", {"product": "onesie", "quantity": 1}), {"content": "Added a onesie."}]
        )
        monkeypatch.setattr(main, "get_agent", lambda: agent)
        return TestClient(main.app)

    def test_chat_then_cart_then_reset(self, client):
        """POST /chat changes the cart; GET /cart shows it; DELETE /session clears it."""
        body = client.post("/chat", json={"session_id": "s1", "message": "add a onesie"}).json()
        assert body["tools_called"][0]["name"] == "add_to_cart"

        assert client.get("/cart/s1").json() == {
            "items": [{"product": "Sauce Labs Onesie", "quantity": 1, "unit_price": 7.99}],
            "total": 7.99,
        }
        assert client.delete("/session/s1").status_code == 204
        assert client.get("/cart/s1").json()["items"] == []

    @pytest.mark.parametrize(
        "payload", [{"session_id": "", "message": "hi"}, {"session_id": "s", "message": ""}, {"message": "hi"}]
    )
    def test_invalid_requests_are_rejected(self, client, payload):
        """Empty or missing fields are 422s, validated before reaching the model."""
        assert client.post("/chat", json=payload).status_code == 422
