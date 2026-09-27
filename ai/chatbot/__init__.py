"""Chatbot adapters. Every class here is a :class:`ChatbotClient`."""

from ai.chatbot.base import ChatbotClient, ChatResponse
from ai.chatbot.guarded_client import REFUSAL_MESSAGE, GuardedChatbot
from ai.chatbot.ollama_client import OllamaChatbot
from ai.chatbot.scripted_chat_model import ScriptedChatModel, tool_call_message
from ai.chatbot.scripted_client import RecordedCall, ScriptedChatbot
from ai.chatbot.ui_client import UiChatbot

__all__ = [
    "ChatbotClient",
    "ChatResponse",
    "GuardedChatbot",
    "OllamaChatbot",
    "REFUSAL_MESSAGE",
    "RecordedCall",
    "ScriptedChatModel",
    "ScriptedChatbot",
    "UiChatbot",
    "tool_call_message",
]
