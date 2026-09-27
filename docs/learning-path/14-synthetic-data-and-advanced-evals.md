# 14 · Synthetic data and advanced AI evals

## Why
Hand-written goldens and test cases don't scale, so teams generate them with an LLM. But a
generator LLM hallucinates too. This chapter generates data **and** gates it, then adds the
evaluation types the earlier chapters didn't: multi-turn conversations, traditional
reference metrics, and a LangChain app.

## Synthetic goldens: [`ai/synthesis/goldens.py`](../../ai/synthesis/goldens.py)
DeepEval's `Synthesizer` writes question/answer pairs from your documents with a local model.
Measured here: of the first two goldens, one had an expected answer claiming items are
"eligible for a refund or exchange", which the source never says. A faithful bot would *fail*
against it. `GoldenQualityGate` rejects:
- incomplete goldens (no question, answer or context),
- questions copied from the context (they test nothing),
- near-duplicates (embedding similarity),
- expected answers not grounded in the context (calibrated faithfulness judge).

## AI-generated test cases: [`ai/synthesis/test_cases.py`](../../ai/synthesis/test_cases.py)
Requirements in [`requirements.json`](../../ai/synthesis/requirements.json) go to the model one at
a time, with related requirements retrieved as context (RAG), in JSON mode. Every case is
validated with pydantic, and `review_suite` reports:
uncovered requirements, missing negative cases, duplicates, and quoted error messages that no
expected result checks.
Measured: llama3.2:3b covered 7/7 requirements; qwen2.5:1.5b covered 6/7 and labelled error
scenarios as "positive". It also invented a "maximum login attempts" rule, which no automated check
catches: **generated cases are drafts for a human reviewer**.

## Multi-turn conversations
- [`ai/evaluators/conversation.py`](../../ai/evaluators/conversation.py): `run_conversation` turns
  any chat function into DeepEval's `ConversationalTestCase`; `RetentionProbeMetric` checks
  memory without a judge.
- Calibration ([`tests/ai/conversation`](../../tests/ai/conversation)): completeness works on the 3B
  judge; role adherence and turn relevancy need the 7B judge; **knowledge retention failed
  on both**, so the rule-based probe replaces it.
- [`tests/ai/agent/test_agent_conversation.py`](../../tests/ai/agent/test_agent_conversation.py)
  found three real agent defects on its first run: "remove one backpack" removed all of them,
  the 1.5B model ignored an optional `quantity` argument, and it invented cart contents instead of
  calling `view_cart`.
- **The lesson in the fix**: the first attempt parsed the user's words with regexes ("remove
  *one*", "what's in my *cart*"). Code review showed each new phrasing broke it ("is shipping free
  if my cart total is over $50?" got a cart summary). The fix that held changed the *system*:
  the live cart is in the prompt every turn, and `quantity` is required. Prefer fixing what the
  model sees over post-processing what the user said.
- **Same lesson, second round (CI only)**: on GitHub runners the 1.5B model sent
  `{"product": "Product name"}` on every cart call, copying the schema's *description* as the
  value. It passed locally. The failing test's per-turn tool trajectory made the cause obvious
  in one run. The fix again changes what the model sees: `product` is now an `enum` of catalogue
  names, so there is no placeholder to copy. As a backstop, an unusable product is replaced by the
  one product the user's message names, only when exactly one is named. The user's words never
  decide the action or the quantity; those come from the tool call.
- **Calibrate on the machine that gates**: role adherence on the 3B judge scored good 0.67 /
  bad 0 locally but 0.0 / 0.0 in CI, and its reasons quoted a *user* turn as the bot's. It now
  gates only on the 7B judge (good 1.0 / bad 0.67, threshold 0.8).

## Reference metrics: [`ai/evaluators/reference_metrics.py`](../../ai/evaluators/reference_metrics.py)
BLEU and ROUGE via Hugging Face `evaluate`. The calibration test is the lesson: a correct
paraphrase scores ROUGE-L 0.32 and BLEU 0.08. Use them for wording-sensitive output
(templates, extractive summaries), not for free-form answers. On the golden set the live bot
averages ROUGE-L 0.535 against similarity 0.850.

## A LangChain app under test: [`ai/chatbot/langchain_client.py`](../../ai/chatbot/langchain_client.py)
An LCEL chain (retrieve, then messages, then `ChatOllama`) behind the `ChatbotClient` interface, so
every existing metric runs against it. Unit tests swap the model for a recording
`RunnableLambda`; live tests check golden meaning, faithfulness to `last_context`, and the
canary.

## Run
```bash
pytest tests/ai/synthesis tests/ai/conversation tests/ai/langchain -m "not live"   # offline
pytest tests/ai/synthesis tests/ai/conversation tests/ai/langchain                 # with Ollama
```

## Test your knowledge
1. Why does the golden gate check the *expected answer's* faithfulness, not the question's?
2. When is ROUGE the right metric?
3. Why does `MetricFactory.knowledge_retention` raise instead of returning DeepEval's metric?

<details><summary>Answers</summary>

1. The expected answer is the oracle. If it is wrong, correct bots fail and wrong bots pass.
2. When the exact wording is the requirement: templated messages, extractive summaries, or
   regression against a known-good output.
3. It failed calibration on both local judges (good and bad scored identically). The factory
   refuses to build a false gate; use `RetentionProbeMetric` instead.
</details>
