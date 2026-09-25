"""Live chatbot adapter for an open-source model served by Ollama.

Uses Playwright's APIRequestContext so the chatbot traffic is traced the same
way as the API suite. When `context` is provided the bot behaves like a RAG
assistant: it is instructed to answer only from the supplied passages, which
is what makes faithfulness measurable.
"""
from __future__ import annotations

import time

from playwright.sync_api import APIRequestContext, Error as PlaywrightError

from ai.chatbot.base import ChatResponse

GROUNDED_SYSTEM_PROMPT = (
    "You are a customer-support assistant. Answer the user's question using ONLY "
    "the information in the CONTEXT below. If the context does not contain the "
    "answer, reply exactly: \"I don't know based on the provided information.\" "
    "Be concise: at most three sentences.\n\nCONTEXT:\n{context}"
)
OPEN_SYSTEM_PROMPT = "You are a helpful assistant. Be concise: at most three sentences."


class OllamaChatbot:
    def __init__(
        self,
        request: APIRequestContext,
        model: str,
        temperature: float = 0.0,
        seed: int = 42,
        timeout_s: int = 180,
    ) -> None:
        self.request = request
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.timeout_ms = timeout_s * 1000

    def is_available(self) -> bool:
        try:
            response = self.request.get("/api/tags", timeout=5_000)
        except PlaywrightError:
            return False
        if not response.ok:
            return False
        names = {m["name"] for m in response.json().get("models", [])}
        return self.model in names

    @staticmethod
    def build_system_prompt(context: list[str] | None) -> str:
        if not context:
            return OPEN_SYSTEM_PROMPT
        return GROUNDED_SYSTEM_PROMPT.format(context="\n".join(f"- {c}" for c in context))

    def ask(self, question: str, context: list[str] | None = None) -> ChatResponse:
        payload = {
            "model": self.model,
            "stream": False,
            # temperature 0 + fixed seed: as deterministic as an LLM gets, which
            # keeps flakiness down without pretending outputs are fixed strings.
            "options": {"temperature": self.temperature, "seed": self.seed},
            "messages": [
                {"role": "system", "content": self.build_system_prompt(context)},
                {"role": "user", "content": question},
            ],
        }
        started = time.perf_counter()
        response = self.request.post("/api/chat", data=payload, timeout=self.timeout_ms)
        latency_ms = (time.perf_counter() - started) * 1000
        if not response.ok:
            raise RuntimeError(f"Chatbot HTTP {response.status}: {response.text()}")
        body = response.json()
        return ChatResponse(
            text=body["message"]["content"].strip(),
            model=body.get("model", self.model),
            latency_ms=latency_ms,
            raw=body,
        )
