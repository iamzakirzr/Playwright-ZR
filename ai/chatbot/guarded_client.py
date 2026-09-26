"""Guard-rail **Decorator** around any chatbot.

Production LLM apps rarely expose the raw model. They wrap it in layered
defences, and ``GuardedChatbot`` implements the three common layers:

1. **Input signature filter**: regexes for well-known injection phrasings. Free, instant.
2. **Input moderator** (optional): a second LLM that classifies each message
   as SAFE or UNSAFE, in the style of Llama Guard. Catches paraphrased and
   role-play attacks that regexes miss.
3. **Output redaction**: strips the system-prompt canary and PII-shaped strings,
   so a successful jailbreak still can't exfiltrate secrets.

It has the same interface as the bot it wraps, so the red-team suite runs
identical attacks against the raw and the guarded model and compares them.
"""

from __future__ import annotations

import re

from ai.chatbot.base import ChatbotClient, ChatResponse
from ai.prompts import default_registry

REFUSAL_MESSAGE = "I can't help with that request."

#: Signatures of instruction-override attacks.
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|rules|prompts?)",
    r"disregard (all |the )?(previous|prior|above|system)",
    r"(reveal|print|show|repeat|output) (me )?(your|the) (system|hidden|initial) (prompt|instructions|message)",
    r"system override",
    r"you are no longer",
    r"you are now (dan|in developer mode|unrestricted|jailbroken)",
    r"developer mode",
    r"\bDAN\b",
]

#: PII shapes redacted from output.
PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "card": r"\b(?:\d[ -]?){13,16}\b",
    "phone": r"\+?\d{1,3}[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b",
    "email": r"\b[\w.+-]+@[\w-]+\.[\w.]+\b",
}


class GuardedChatbot(ChatbotClient):
    """Decorates ``inner`` with input and output guard rails.

    Args:
        inner: The chatbot to protect. Its prompts and canary are reused.
        moderator: Optional chatbot that runs the ``input_moderator`` prompt. Use a
            *different* instance from ``inner`` in production, so one jailbreak
            can't compromise both.
    """

    def __init__(self, inner: ChatbotClient, moderator: ChatbotClient | None = None) -> None:
        """Create the GuardedChatbot; arguments are described in the class docstring."""
        super().__init__(grounded_prompt=inner.grounded_prompt, open_prompt=inner.open_prompt, canary=inner.canary)
        self.inner = inner
        self.moderator = moderator
        self.moderation_prompt = default_registry().get("input_moderator")
        self._injection = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)
        #: Why the last request was blocked (None if it wasn't); useful in assertions.
        self.last_block_reason: str | None = None

    def is_available(self) -> bool:
        """Delegate availability to the wrapped bot."""
        return self.inner.is_available()

    def is_injection(self, text: str) -> bool:
        """Layer 1: True if ``text`` matches a known instruction-override pattern."""
        return bool(self._injection.search(text))

    def is_flagged_by_moderator(self, text: str) -> bool:
        """Layer 2: ask the moderator LLM. Anything other than a clear SAFE counts as unsafe (fail closed)."""
        if self.moderator is None:
            return False
        verdict = self.moderator.run_prompt(self.moderation_prompt, message=text).text.upper()
        return "UNSAFE" in verdict or "SAFE" not in verdict

    def redact(self, text: str) -> str:
        """Layer 3: remove the canary token and PII-shaped strings from model output."""
        if self.canary:
            text = re.sub(re.escape(self.canary), "[REDACTED]", text, flags=re.IGNORECASE)
        for name, pattern in PII_PATTERNS.items():
            text = re.sub(pattern, f"[{name.upper()} REDACTED]", text)
        return text

    def _refuse(self, reason: str) -> ChatResponse:
        """Build the canned refusal and remember why it was issued."""
        self.last_block_reason = reason
        return ChatResponse(text=REFUSAL_MESSAGE, model="guardrail", latency_ms=0.0)

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> ChatResponse:
        """Run the input guards, then the wrapped bot, then output redaction."""
        self.last_block_reason = None
        if self.is_injection(user):
            return self._refuse("injection-signature")
        if self.is_flagged_by_moderator(user):
            return self._refuse("moderator")
        response = self.inner.complete(system, user, json_mode=json_mode)
        return ChatResponse(
            text=self.redact(response.text),
            model=response.model,
            latency_ms=response.latency_ms,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            raw=response.raw,
        )
