"""Live chatbot adapter for an open-source model served by Ollama.

Traffic goes through Playwright's ``APIRequestContext``, so chatbot calls are
traced exactly like the API suite's HTTP calls.
"""

from __future__ import annotations

import time

from playwright.sync_api import APIRequestContext
from playwright.sync_api import Error as PlaywrightError

from ai.chatbot.base import ChatbotClient, ChatResponse


class OllamaChatbot(ChatbotClient):
    """Concrete :class:`ChatbotClient` that talks to Ollama's ``/api/chat`` endpoint.

    Args:
        request: A Playwright request context whose ``base_url`` is the Ollama host.
        model: Name of a pulled Ollama model, e.g. ``qwen2.5:1.5b``.
        temperature: Sampling temperature; 0 makes runs as repeatable as an LLM allows.
        seed: Fixed sampling seed, which also reduces run-to-run variance.
        timeout_s: Per-request timeout in seconds (CPU inference is slow).
        **kwargs: Forwarded to :class:`ChatbotClient` (prompt templates, canary).
    """

    def __init__(
        self,
        request: APIRequestContext,
        model: str,
        temperature: float = 0.0,
        seed: int = 42,
        timeout_s: int = 180,
        **kwargs,
    ) -> None:
        """Create the OllamaChatbot; arguments are described in the class docstring."""
        super().__init__(**kwargs)
        self.request = request
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.timeout_ms = timeout_s * 1000

    def is_available(self) -> bool:
        """Return True if Ollama answers and ``self.model`` has been pulled."""
        try:
            response = self.request.get("/api/tags", timeout=5_000)
        except PlaywrightError:
            return False
        if not response.ok:
            return False
        return self.model in {m["name"] for m in response.json().get("models", [])}

    def with_options(self, *, temperature: float | None = None, seed: int | None = None) -> OllamaChatbot:
        """Return a copy with different sampling options (used by consistency tests).

        Args:
            temperature: New temperature, or None to keep the current one.
            seed: New seed, or None to keep the current one.
        """
        return OllamaChatbot(
            self.request,
            self.model,
            temperature=self.temperature if temperature is None else temperature,
            seed=self.seed if seed is None else seed,
            timeout_s=self.timeout_ms // 1000,
            grounded_prompt=self.grounded_prompt,
            open_prompt=self.open_prompt,
            canary=self.canary,
        )

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> ChatResponse:
        """POST one chat turn to Ollama and wrap the reply in a :class:`ChatResponse`.

        Raises:
            RuntimeError: If Ollama returns a non-2xx status.
        """
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature, "seed": self.seed},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["format"] = "json"
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
            prompt_tokens=body.get("prompt_eval_count", 0),
            completion_tokens=body.get("eval_count", 0),
            raw=body,
        )
