# Playwright-ZR

A layered Playwright (Python) framework that covers **UI, API, SQL** and **live LLM-chatbot evaluation**
(semantic similarity + faithfulness), all open source, all runnable locally without paid APIs.

| Layer  | Target                                   | Pattern                      | Tooling                                   |
|--------|------------------------------------------|------------------------------|-------------------------------------------|
| UI     | saucedemo.com                            | Page Object Model            | pytest-playwright                         |
| API    | restful-booker.herokuapp.com             | Service objects + schemas    | Playwright `APIRequestContext`, pydantic  |
| SQL    | Seeded SQLite                            | Repositories                 | sqlite3, per-test transaction rollback    |
| Hybrid | API ↔ DB                                 | Composes the above           |                                           |
| AI     | Open-source LLM served by Ollama         | Chatbot adapter + metrics    | DeepEval, Ragas, sentence-transformers    |

## Why Python?
DeepEval and Ragas, the two most widely used open-source LLM-eval libraries, are Python-native.
Playwright's Python binding is first-class, so the whole framework uses one language and one test runner.

## Layout
```
config/settings.py          env-driven settings (.env overrides everything)
pages/                      UI page objects (+ components/header.py)
api/                        service clients + pydantic contract schemas
db/                         connection, seed.sql, repositories/
ai/chatbot/                 ChatbotClient protocol + OllamaChatbot adapter
ai/evaluators/              SemanticSimilarityMetric (DeepEval BaseMetric), judge factories
ai/datasets/golden_qa.json  golden Q/A + context, unanswerable and counterfactual cases
tests/{ui,api,sql,hybrid,ai}/
conftest.py                 fixtures: page objects, clients, repos (markers auto-applied by folder)
tests/ai/conftest.py        chatbot, judge, metrics, answer cache (AI tests skip if Ollama is absent)
```

**Layering rule:** page objects, clients and repositories encapsulate *how* to interact with the system.
Tests own *what* is asserted. The only assertion allowed in a page object is `expect_loaded()`.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu   # optional: smaller CPU-only torch
pip install -r requirements.txt
playwright install chromium

pytest -m "ui or api or sql or hybrid" -n auto      # functional suites (~15s)
```

### AI suite
```bash
curl -fsSL https://ollama.com/install.sh | sh && ollama serve &
ollama pull qwen2.5:1.5b     # chatbot under test
ollama pull llama3.2:3b      # DeepEval judge (different model family from the bot, to reduce self-preference bias)
pytest -m "ai and not ragas" -v                      # ~2 min on CPU

ollama pull qwen2.5:7b       # optional: Ragas judge
pytest -m ragas -v                                   # ~2-3 min per sample on CPU
```

## How the AI tests work
The bot receives a **fictional** policy document as context (RAG-style) and must answer only from it.
Because the facts are fictional, a correct answer can only come from the context. That is what makes faithfulness measurable.

| Test file                       | Metric                                     | What it catches                                   |
|---------------------------------|--------------------------------------------|---------------------------------------------------|
| `test_semantic_similarity.py`   | Cosine over `all-MiniLM-L6-v2` embeddings  | Answer drifts in meaning from the reference       |
| `test_faithfulness.py`          | DeepEval `FaithfulnessMetric` (LLM judge)  | Claims unsupported by, or contradicting, context  |
| `test_grounding_guardrails.py`  | Deterministic checks                       | Invents answers to unanswerable Qs; uses prior knowledge over context |
| `test_ragas_crosscheck.py`      | Ragas `Faithfulness`                       | Independent second opinion on faithfulness        |

**Calibration tests come first.** Each metric is first run on hand-written inputs: a paraphrase vs unrelated text,
and a faithful vs hallucinated answer. This proves the metric can discriminate before its verdict on live
output is trusted. A judge that passes everything is worse than no test.

### Known limitations
- **Similarity is not correctness.** Embeddings are weak on negation and on *incomplete* answers. For example, the bot
  answers the shipping question with only the free-shipping rule and scores ~0.74, which is still a pass. Always pair similarity with faithfulness,
  and consider a completeness metric (DeepEval `GEval`) for answers with several required facts.
- **Small judges are noisy.** `llama3.2:3b` gets the scores right on the calibration cases, but its written *reasons* are often
  incoherent. Use a 7B+ judge when you need explanations you can trust. Ragas fails outright on 3B judges (JSON parsing).
- **LLM output is probabilistic.** Temperature 0 and a fixed seed reduce variance but don't remove it. The AI suite runs as a
  separate CI job so it never blocks the deterministic suites.

## Configuration
All settings live in `config/settings.py` and can be overridden with env vars or `.env` (see `.env.example`).
Set `BROWSER_EXECUTABLE_PATH` to use a pre-installed Chromium when `playwright install` isn't possible.

## CI
`.github/workflows/tests.yml` runs two jobs: `functional` (UI/API/SQL/hybrid, parallel) and `ai-eval`
(installs Ollama, caches the models, runs the DeepEval suite).
