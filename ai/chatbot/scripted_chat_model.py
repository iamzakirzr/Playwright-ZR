"""A LangChain chat model that replays scripted replies: the test double for LangChain agents.

LangChain's own fakes (``GenericFakeChatModel``) cannot ``bind_tools``, so they can't stand in for
a tool-calling model. ``ScriptedChatModel`` can: it records the tool schemas it was bound to and
every message list it received, then answers with the next scripted ``AIMessage``. That makes an
agent's control flow (which node runs, which tool is called, what the model was shown) testable
without a model server, in milliseconds.

Example::

    model = ScriptedChatModel(replies=[tool_call_message("view_cart"), AIMessage("It's empty.")])
    agent = LangGraphShopAgent(model)
    agent.chat("t1", "what's in my cart?")
    model.received[1][-1]   # the ToolMessage the model saw on its second call
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field

_ids = itertools.count(1)


def tool_call_message(name: str, content: str = "", **arguments: Any) -> AIMessage:
    """An ``AIMessage`` asking for one tool call, with a unique call id (as a real model sends)."""
    return AIMessage(content, tool_calls=[{"name": name, "args": arguments, "id": f"call_{next(_ids)}"}])


class ScriptedChatModel(BaseChatModel):
    """Chat model whose replies come from a list.

    Attributes:
        replies: Replies to return, in order. Running out fails the test loudly.
        received: Every message list the model was called with.
        bound_tools: The tool schemas (OpenAI format) from the last ``bind_tools`` call.
    """

    replies: list[AIMessage] = Field(default_factory=list)
    received: list[list[BaseMessage]] = Field(default_factory=list)
    bound_tools: list[dict] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        """Identifier LangChain uses in traces."""
        return "scripted"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> ScriptedChatModel:
        """Record the tool schemas (exactly what a real model would be sent) and return self."""
        self.bound_tools = [convert_to_openai_tool(t) for t in tools]
        return self

    def _generate(
        self, messages: list[BaseMessage], stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any
    ) -> ChatResult:
        """Record the input and return the next scripted reply."""
        self.received.append(list(messages))
        if not self.replies:
            raise AssertionError(f"ScriptedChatModel ran out of replies after {len(self.received) - 1} calls")
        return ChatResult(generations=[ChatGeneration(message=self.replies.pop(0))])
