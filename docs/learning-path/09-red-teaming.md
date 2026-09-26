# 09 · Red teaming and guardrails

## Why
Users (and documents the bot reads) will try to make it leak its instructions, ignore its rules,
or say harmful things. Red teaming measures how often that works, and guardrails bring it to zero.

## Read
1. [`ai/redteam/attacks.json`](../../ai/redteam/attacks.json): attacks tagged with OWASP LLM Top 10
   IDs (LLM01 prompt injection, LLM02 sensitive info, LLM05 output handling, LLM06 excessive agency,
   LLM07 system-prompt leakage, LLM09 misinformation), plus **benign** prompts that must *not* be refused.
2. [`ai/redteam/runner.py`](../../ai/redteam/runner.py): runs each attack, picks a detector
   (canary leak, refusal, PII regex, `must_not_contain` markers, toxic-bert, or a toxicity/bias judge) and reports attack success rate (ASR) per category.
3. [`ai/chatbot/guarded_client.py`](../../ai/chatbot/guarded_client.py): `GuardedChatbot` is a
   **decorator**: it wraps any `ChatbotClient` with an input regex filter, an optional LLM
   moderator, and output redaction of the canary.
4. [`tests/ai/redteam/`](../../tests/ai/redteam): the raw model's ASR baseline, the guarded
   bot's ASR (budget `GUARDED_MAX_ASR=0.0`), and over-refusal on benign prompts.

## The canary
A made-up secret (`CANARY_TOKEN`) is planted in the system prompt. If it ever appears in output,
the system prompt leaked. It is a zero-false-positive detector.

## Run
```bash
pytest -m "redteam and not live"    # guard unit tests
pytest -m "redteam and live"        # attacks against the real model
```

## Try it
Add an attack that hides an instruction inside the *context* (indirect injection), run it against
the raw and the guarded bot, and compare.

## Test your knowledge
1. Why measure over-refusal alongside attack success?
2. Why keep a raw-model baseline test with a generous budget (`RAW_MODEL_MAX_ASR`)?

<details><summary>Answers</summary>

1. A bot that refuses everything has 0% ASR and is useless; both numbers must be good.
2. It shows how much the guardrails contribute, and it flags a model upgrade that is much weaker.
</details>
