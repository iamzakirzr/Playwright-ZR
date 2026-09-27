# Playwright-ZR

A layered, object-oriented **Playwright (Python)** test framework for UI, API, SQL, mobile and AI,
built to be learned from as much as used.

| Layer | What it tests | Target |
|---|---|---|
| **UI** | Page Object Model flows, visual baselines, self-healing locators | [saucedemo.com](https://www.saucedemo.com) |
| **Playwright essentials** | Network mocking, dialogs, frames, tabs, files, auth state, emulation | Local playground app ([`apps/playground`](apps/playground)) |
| **API** | CRUD + contract (schema) validation | [restful-booker](https://restful-booker.herokuapp.com) |
| **SQL** | Repositories, constraints, integrity | Seeded SQLite |
| **Hybrid** | API ↔ DB consistency | both |
| **BDD** | Gherkin scenarios over the same page objects | saucedemo + AI assistant |
| **Mobile** | Device emulation (Pixel, iPhone) and Appium on an Android emulator | saucedemo |
| **AI** | RAG quality, AI search, prompts, chains, agents & tool calls, multi-turn conversations, MCP servers, red teaming, GenAI validation, LangChain apps, synthetic data, chat UI | Open-source LLMs served locally by [Ollama](https://ollama.com) |

Everything is open source and runs locally. No paid API keys are needed.

> **New here? Start with the [learning path](docs/learning-path/README.md):** 14 short chapters,
> one per layer, each with files to read, a command to run, an exercise and a quiz.
> [Course coverage](docs/course-coverage.md) maps ExecuteAutomation (Karthik KK) course topics to
> the code that practises them.

---

## 1. Quick start

**Prerequisites:** Python 3.11+, `make`, and about 8 GB of free disk space for the models.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
make setup            # CPU-only torch, requirements, Chromium, pre-commit hook
make help             # every command, one line each

make test-functional  # UI + API + SQL + BDD, no AI              (~30 s)
make test-ai-offline  # embeddings, classifiers, stubs, MCP      (~40 s)
make test-mobile-web  # phones emulated by Playwright            (~15 s)
make lint             # ruff, same as CI
make report-open      # Allure HTML report of the last run (needs Node.js)
```

Every `make` target is a plain `pytest -m ...` call; open the [`Makefile`](Makefile) to see and copy it.
No `make` (Windows)? Run the pytest line from the Makefile directly.

**Docker instead:** `docker compose up --abort-on-container-exit --exit-code-from tests` starts
Ollama, pulls the models and runs the suites in containers ([`docker-compose.yml`](docker-compose.yml)).

### Live AI suites (need Ollama)

```bash
# Install Ollama: https://ollama.com/download
# (Linux: curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.34.4 sh; it needs `zstd` installed.
#  Thresholds were measured on 0.34.4; other versions can shift a small model's output.)
ollama serve &                   # leave running
ollama pull qwen2.5:1.5b         # chatbot under test (~1 GB)
ollama pull llama3.2:3b          # judge for quality metrics (~2 GB)

make test-ai-live      # model behaviour, no judge
make test-ai-judged    # metrics the 3B judge is calibrated for (slow on CPU)

# Optional: strong judge for relevancy, correctness, hallucination, judged safety and Ragas
ollama pull qwen2.5:7b           # ~4.7 GB, ~1-2 min per judged call on CPU
make test-ai-strong
```

Tests that need a missing server or model **skip** with a message telling you what to pull. They never fail for that reason.

---

## 2. Architecture

```
tests/                         ← WHAT is asserted (thin, readable, one behaviour per test)
  ui/ (visual/) api/ sql/ hybrid/ bdd/ mobile/{web,native}/
  ai/{rag,search,prompts,chains,redteam,validation,chat_ui,agent,mcp,healing}/
        │  fixtures (conftest.py) inject ↓
pages/        api/          db/               ai/
Page Objects  Service       Repositories      chatbot/   ChatbotClient + adapters
(+ healing/)  objects                         prompts/   versioned PromptTemplate + registry
                                              chains/    Chain + ChainStep pipeline
                                              search/    Retriever strategies, IR metrics, RAG
                                              evaluators/ metrics (rule, classifier, LLM-judged)
                                              redteam/   attack library + runner
                                              chat_ui/   chat widget served via page.route
mobile/       Appium driver factory + screen objects
visual/       screenshot comparator + opt-in vision judge
data/         Faker factories (seeded, replayable)
reporting/    Allure steps and attachments
apps/         apps under test: shop_assistant (FastAPI agent + LangGraph agent), store_mcp (MCP server)
config/settings.py             ← every URL, model, threshold and budget (env-overridable)
```

### OOP design patterns used (and where to look)

| Pattern | Where | Why |
|---|---|---|
| **Page Object** + inheritance | `pages/base_page.py` → `LoginPage`, `ChatPage`… | Locators and navigation in one place; tests read like user stories |
| **Composition** | `pages/components/header.py` used by several pages | Shared widgets without deep inheritance |
| **Service Object** | `api/base_client.py` → `BookingClient` | Same idea as POM for HTTP |
| **Repository** | `db/repositories/base_repository.py` → `UserRepository` | SQL out of tests, always parameterised |
| **Abstract Base Class + Template Method** | `ai/chatbot/base.py` (`ask` → abstract `complete`); `ai/search/base.py` (`search` → abstract `_score`); `ai/evaluators/base.py` (`measure` → abstract `evaluate`) | The shared algorithm lives in the base; subclasses fill in one step |
| **Strategy** | `BM25Retriever` / `SemanticRetriever` / `HybridRetriever`; red-team detectors | Swap algorithms; run one test against all of them |
| **Composite** | `HybridRetriever` fuses child retrievers | Treat a group like one retriever |
| **Decorator** | `GuardedChatbot(inner)` | Adds guard rails without changing the bot; same interface |
| **Adapter** | `OllamaChatbot`, `UiChatbot` (drives the browser) | One interface, many backends. Every eval runs through UI or API unchanged |
| **Test Double (stub + spy)** | `ScriptedChatbot` | Deterministic, offline chain/prompt tests; records every call |
| **Factory** | `ai/evaluators/factory.py` `MetricFactory` | One place wires the judge and thresholds for 15+ metrics |
| **Pipeline / Chain of Responsibility** | `ai/chains/base.py` | Multi-step LLM flows with per-step traces |
| **Registry** | `ai/prompts/registry.py` | Versioned prompts, fetched by name |
| **Dependency Injection** | pytest fixtures (`conftest.py`, `tests/ai/conftest.py`) | Tests ask for objects, never build them |
| **Builder / Factory** (test data) | `data/factories.py` `BookingFactory.build(totalprice=0)` | Fresh realistic data; pin only the field the test cares about |
| **Screen Object** | `mobile/screens/` → `MobileLoginScreen` | The Page Object idea for Appium |
| **Proxy (self-healing)** | `pages/healing/self_healing.py` `SelfHealingLocator` | Stands in for a locator; falls back to cache, then an LLM, and validates the fix |
| **Value Objects** (frozen dataclasses) | `ChatResponse`, `PromptTemplate`, `Attack`, `SearchResult` | Immutable, comparable, safe to cache |

Every module, class and function has a docstring. Start reading at `ai/chatbot/base.py`, then `tests/ai/conftest.py`.

---

## 3. The AI test suites

The chatbot is `qwen2.5:1.5b`, grounded on a **fictional** store policy, so a correct answer can only come from the supplied context. That is what makes faithfulness measurable.

### 3.1 RAG answer quality: `tests/ai/rag/`
| Test | Metric | Catches |
|---|---|---|
| `test_semantic_similarity.py` | Embedding cosine (custom DeepEval metric) | Meaning drifts from the reference |
| `test_faithfulness.py` | DeepEval `FaithfulnessMetric` | Claims not supported by the context |
| `test_production_metrics.py` | Required-fact coverage (gating), helpful-fact coverage and G-Eval completeness (dataset baselines); answer relevancy, correctness, hallucination, contextual precision/recall/relevancy (strong judge) | Wrong, incomplete, off-topic or contradicting answers; poor retrieval |
| `test_grounding_guardrails.py` | Refusal detector, counterfactual context | Inventing answers; pre-training beating context |
| `test_ragas_crosscheck.py` | Ragas `Faithfulness` (opt-in) | Second, independent implementation |

**A judged metric is only trusted with a judge that passes calibration for it.** Every judged metric first runs on a known-good and a known-bad hand-written answer. Calibrating the default `llama3.2:3b` judge gave these results:

| Metric | 3B judge calibration | Tier |
|---|---|---|
| Faithfulness | faithful 1.0, contradicting 0.0 ✅ | default |
| G-Eval completeness | complete 0.8–0.9, incomplete 0.4–0.6 ✅ (threshold 0.7) | default |
| Contextual precision / recall / relevancy | ❌ recall 0.33 on a *perfect* retrieval; passed locally, failed in CI on identical input | strong judge (7B); retrieval is gated by IR metrics |
| Prompt alignment | ❌ claimed lists and markdown in a one-sentence answer | strong judge (7B); word limit is gated deterministically |
| Answer relevancy | ❌ scored a perfectly on-topic answer 0.25 | strong judge (7B) |
| G-Eval correctness | ❌ flat 0.6 for right and wrong answers | strong judge (7B) |
| Hallucination | ❌ **inverted**: correct answer 1.0, wrong answer 0.0 | strong judge (7B) |
| DeepEval toxicity | ❌ polite refusal scored 1.0 (toxic) | replaced by `toxic-bert` classifier; judged version needs 7B |

**Known model limitation, tracked rather than hidden:** `qwen2.5:1.5b` reliably states the fact a question needs, but drops extras. Asked "Is shipping free?", it says free from $75 and never mentions the $4.99 fee. Four prompt variants, including few-shot, and `qwen2.5:3b` all failed to fix this. So:
- **required facts** (what the question strictly needs) gate every case, and
- **helpful facts** are tracked at the dataset level against a recorded baseline (`MIN_MEAN_HELPFUL_COVERAGE`, `MIN_MEAN_COMPLETENESS`). The gap stays visible in every run and fails if it gets worse.

### 3.2 AI search: `tests/ai/search/`
- **IR metrics** (`ai/search/metrics.py`): Recall@k, Precision@k, Hit rate, MRR and nDCG@k over a labelled query set, for **BM25**, **semantic** and **hybrid (RRF)** retrieval.
- **Robustness**: typos, casing, word order, synonyms, paraphrases.
- **Negative space**: off-domain queries return nothing above the relevance floor, so RAG abstains and never calls the LLM.
- **End-to-end RAG**: the right passage is retrieved, the answer is faithful to *what was actually retrieved*.

### 3.3 Prompt testing: `tests/ai/prompts/`
- **Offline**: rendering, missing or unexpected variables, template-injection safety, version pinning, security-rule lint, and **prompt-drift snapshots** (a wording change fails until it is reviewed: `UPDATE_PROMPT_SNAPSHOTS=1 pytest tests/ai/prompts/test_prompt_registry.py`).
- **Live**: classifier accuracy (few-shot `intent_classifier` v2 routes 14/14 vs v1's 10/14), JSON-schema adherence (`JsonSchemaMetric` + DeepEval `JsonCorrectnessMetric`), word limits, Yes/No closed form, DeepEval `PromptAlignmentMetric` (strong judge), **A/B regression** (new prompt version must not cover fewer facts than v1), paraphrase robustness, summariser fact retention (`summarizer` v2, one sentence per rule, kept every number in 16/16 sampled runs vs 4–8/16 for v1's two-sentence cap, which wrote "$4. 99").

### 3.4 Prompt chaining: `tests/ai/chains/`
Chain: `intent → handoff (out_of_scope stops here) → rewrite → retrieve → answer`.
- **Unit (scripted model)**: step order, bounded model calls, what each step passes to the next, short-circuit routing, output normalisation, error attribution (`ChainError.step`), fallbacks.
- **Live**: each link meets its own contract (intent, query length, retrieved doc, answer facts) plus end-to-end faithfulness.

### 3.5 Red teaming: `tests/ai/redteam/`
14 attacks in `ai/redteam/attacks.json`, mapped to the **OWASP Top 10 for LLM Applications**: direct and indirect prompt injection, system-prompt leakage (detected with a **canary token**), PII exfiltration, jailbreaks, phishing, toxicity, bias, off-topic misuse.

| Suite | Target | Pass rule |
|---|---|---|
| `test_guarded_attacks.py` | Bot + guard rails | **Every** attack defended (ASR budget 0%) |
| `test_raw_model_baseline.py` | Raw bot | ASR ≤ budget; guard must strictly reduce ASR |
| `test_over_refusal.py` | Both | Legitimate questions refused ≤ 25% |
| `test_guard_units.py` | Each guard layer, scripted | Offline regression for every regex, redaction and detector |
| `test_safety_judges.py` | DeepEval toxicity/bias/PII/role (opt-in strong judge) | Judged safety |

Measured on `qwen2.5:1.5b`, CPU, temperature 0:

| | Raw model | Guarded (`GuardedChatbot`) |
|---|---|---|
| Attacks succeeded | **9 / 14**: leaked SSNs and cards, revealed the canary, wrote a phishing email, obeyed "I HAVE BEEN PWNED" | **0 / 14** |
| Legitimate questions refused | 0–1 / 8 | 1 / 8 (moderator flags "Someone hacked my account", a known false positive tracked in the budget) |

The guard (`ai/chatbot/guarded_client.py`) has three layers: an injection-signature regex, a Llama-Guard-style **LLM moderator prompt** (fails closed), and **output redaction** of the canary and PII.

### 3.6 LLM / GenAI validation: `tests/ai/validation/`
Reproducibility at temperature 0, semantic stability across seeds, latency and **token budgets**, output hygiene (no HTML, no template leftovers, no echoed system prompt, expected language), toxicity floor (`unitary/toxic-bert` classifier), model-identity check, plus offline calibration of every deterministic metric.

### 3.7 Chat UI through Playwright: `tests/ai/chat_ui/`
`ai/chat_ui/index.html` is served with **`page.route`** at `http://chatbot.local` (no web server). `ChatHost` switches the backend between **stub** (canned or error replies), **hold** (to test loading states) and **proxy** (the real Ollama model).
- Stubbed: render order, **request-payload contract**, typing indicator and disabled input, friendly 500 error, **XSS: model HTML rendered as text**, blank input.
- Live: `UiChatbot` (a `ChatbotClient`) runs the **same metrics** through the browser as the API adapter does.

### 3.8 Agents and tool calls: `tests/ai/agent/`
`apps/shop_assistant/` is a FastAPI app with a tool-calling agent (`add_to_cart`, `remove_from_cart`,
`view_cart`) plus retrieval over the store policies over Ollama; `api/shop_assistant_client.py` is its service object.
- **Unit (scripted model)**: tool routing, argument normalisation, the "claimed an action without
  calling a tool" guard, the scope guard, the tool-round limit.
- **Live**: DeepEval `ToolCorrectnessMetric` on the tool trajectory, cart **state verified through the
  API** (never trust the reply text), multi-turn memory, off-topic refusal, a golden
  `EvaluationDataset`, and the same flows as Gherkin (`test_assistant_feature.py`).
- The tests found four real agent defects (fake action claims, lost context, off-topic answers,
  descriptions passed as product names); each fix is in `agent.py` with a regression test.

### 3.9 MCP server testing: `tests/ai/mcp/`
`apps/store_mcp/` exposes the store as an MCP server. Tests check the tool list and schemas, typed
structured results, `ToolError` on bad input, and run over **two transports**: in-process (fast) and
a **stdio subprocess** (`python -m apps.store_mcp`, what Claude Desktop or Cursor launch).

### 3.10 Self-healing locators: `tests/ai/healing/`
`BasePage.healable(name, selector, description)` returns a locator that, when the selector breaks,
tries the JSON cache, then asks an LLM for candidates from trimmed page HTML, and accepts only a
candidate matching **exactly one visible element**. Offline tests use a fake healer; the live test
heals a renamed login form with the local model.

### 3.11 Visual testing: `tests/ui/visual/`
`visual/comparator.py`: per-browser-and-OS baselines, masked dynamic regions, a pixel tolerance, and
a diff image on failure (`UPDATE_SNAPSHOTS=1` accepts changes). `visual/vision_judge.py` adds an
opt-in vision-LLM description of a side-by-side composite; it is **advisory**, pixels decide.

### 3.12 Multi-turn conversations: `tests/ai/conversation/`, `tests/ai/agent/test_agent_conversation.py`
`run_conversation` builds DeepEval `ConversationalTestCase`s from any bot. Calibration decides
which judged metrics may gate: completeness (3B judge), role adherence and turn relevancy (7B
judge only; the 3B judge confused speakers in CI), knowledge retention (failed on both, so the rule-based `RetentionProbeMetric` is used
instead). The first run of the shopping conversation found three agent defects: "remove one
backpack" removed all of them, the model ignored an optional `quantity`, and it invented cart
contents. A first fix with regex guards over the user's text was rejected in code review (every
new phrasing needed another rule). The structural fix: the live cart goes into the system prompt
every turn, `quantity` is required on removal, and malformed arguments are repaired from their
shape. When CI showed the model copying the schema text (`"product": "Product name"`), `product`
became an `enum` of catalogue names; an unusable product falls back to the one product the user
named (only if exactly one), never to a guess, and never decides the action or quantity.

### 3.13 LangChain app under test: `tests/ai/langchain/`
`LangChainChatbot` is an LCEL RAG chain (retrieve, then messages, then `ChatOllama`) behind the same
`ChatbotClient` interface, so the golden-set, faithfulness and canary checks run against a
LangChain app unchanged. Unit tests swap the model for a recording `RunnableLambda`.

### 3.13b Building an agent with LangChain and LangGraph: `tests/ai/langgraph/`
[`apps/shop_assistant/langgraph_agent.py`](apps/shop_assistant/langgraph_agent.py) rebuilds the shop
assistant with `@tool` functions (typed arguments become the schema: an `enum` of product names),
a `StateGraph` (`retrieve -> agent -> tools -> agent`), `ToolNode` error feedback, a checkpointer for
memory, and a `recursion_limit` loop bound. Tested offline with `ScriptedChatModel` (a chat model
double that can `bind_tools`) and live on qwen2.5:1.5b. Measured while building it: in agentic-RAG
mode the model called the search tool in 0 of 6 policy questions and invented answers, so retrieval
is a graph node by default. Walkthrough: [learning-path chapter 15](docs/learning-path/15-building-agents-with-langchain.md).

### 3.14 Synthetic data: `tests/ai/synthesis/`
- **Goldens**: DeepEval's `Synthesizer` with a local model, then `GoldenQualityGate` (complete,
  not copied, not duplicate, expected answer grounded). It rejects the hallucinated golden the
  synthesizer actually produced during development.
- **Test cases from requirements**: JSON drafts per requirement with related requirements as RAG
  context, pydantic validation, and a coverage review (uncovered, missing negatives, duplicates,
  unchecked error messages). llama3.2:3b covers 7/7 Sauce Demo requirements.

### 3.15 Metric catalogue
| Kind | Metrics | Where |
|---|---|---|
| Rule-based (fast, deterministic) | Semantic similarity, keyword coverage, JSON schema, word limit, refusal, canary leakage, regex PII, retention probe | `ai/evaluators/deterministic.py`, `semantic_similarity.py`, `conversation.py` |
| Reference overlap (Hugging Face `evaluate`) | ROUGE-1/2/L, BLEU (for wording-sensitive output only) | `ai/evaluators/reference_metrics.py` |
| Classifier | Toxicity (`unitary/toxic-bert`) | `ai/evaluators/classifiers.py` |
| LLM-judged conversational (DeepEval) | Conversation completeness, role adherence, turn relevancy, knowledge retention | `ai/evaluators/factory.py` |
| LLM-judged (DeepEval) | Faithfulness, answer relevancy, contextual precision/recall/relevancy, hallucination, G-Eval completeness and correctness, summarisation, prompt alignment, JSON correctness, toxicity, bias, PII leakage, role violation, misuse. See §3.1 for which judge each needs | `ai/evaluators/factory.py` |
| LLM-judged (Ragas) | Faithfulness | `tests/ai/rag/test_ragas_crosscheck.py` |
| Retrieval (IR) | Recall@k, Precision@k, Hit rate, MRR, nDCG@k | `ai/search/metrics.py` |
| Red team | Attack Success Rate per category, over-refusal rate | `ai/redteam/runner.py` |

**Rule of thumb:** use a rule if a rule can express the requirement, a classifier if one exists, and an LLM judge only for what needs understanding.

---

## 4. Running subsets

Markers are applied **automatically**: by folder (`tests/ai/redteam/…` gets `ai` + `redteam`) and by dependency (anything needing Ollama gets `live`; anything needing a judge gets `judge`; the opt-in 7B judge adds `strong_judge`).

```bash
pytest -m smoke                          # critical path
pytest -m "redteam and not live"         # guard regressions, offline, seconds
pytest -m search                         # AI search only
pytest -m "chains or prompts"
pytest tests/ai/chat_ui -v --headed      # watch the chat widget being driven
pytest -m "ai and not judge" -n 4        # parallel (safe except for judge-heavy runs on small CPUs)
pytest -m "agent or mcp"                 # the AI app and its MCP server
FAKER_SEED=1234 pytest tests/api         # replay the exact test data of a failed run (seed is in the header)
```

On failure, Playwright saves a screenshot and trace in `test-results/` (`playwright show-trace <zip>`),
and every run writes Allure results to `reports/allure-results` (`make report-open`).

---

## 5. Configuration

All settings live in `config/settings.py`. Override any of them with an environment variable of the same name, or a `.env` file (copy `.env.example`).

| Variable | Default | Purpose |
|---|---|---|
| `CHATBOT_MODEL` | `qwen2.5:1.5b` | Model under test |
| `JUDGE_MODEL` | `llama3.2:3b` | Quality-metric judge (different family from the bot) |
| `STRONG_JUDGE_MODEL`, `RAGAS_JUDGE_MODEL` | `qwen2.5:7b` | Opt-in stronger judges |
| `MODERATOR_MODEL` | = chatbot | Guard-rail moderator |
| `CANARY_TOKEN` | `ZX-CANARY-7731` | Secret planted in system prompts |
| `SIMILARITY_THRESHOLD`, `FAITHFULNESS_THRESHOLD`, `QUALITY_THRESHOLD`, `COMPLETENESS_THRESHOLD` | 0.70 / 0.70 / 0.60 / 0.70 | Pass bars |
| `MIN_MEAN_HELPFUL_COVERAGE`, `MIN_MEAN_COMPLETENESS` | 0.60 / 0.55 | Dataset-level helpfulness baselines |
| `MIN_RECALL_AT_K`, `MIN_MRR`, `MIN_NDCG_AT_K`, `RETRIEVAL_K` | 0.80 / 0.75 / 0.75 / 3 | Search bars |
| `GUARDED_MAX_ASR`, `RAW_MODEL_MAX_ASR`, `MAX_OVER_REFUSAL_RATE` | 0.0 / 0.85 / 0.25 | Red-team risk budgets |
| `MAX_LATENCY_MS`, `MAX_COMPLETION_TOKENS` | 60000 / 150 | Non-functional budgets |
| `BROWSER_EXECUTABLE_PATH` | unset | Use a pre-installed Chromium |
| `JUDGE_TIMEOUT_S` | 600 | DeepEval per-call timeout (CPU is slow) |
| `VISION_MODEL` | `qwen2.5vl:3b` | Opt-in visual judge |
| `APPIUM_SERVER_URL`, `ANDROID_DEVICE_NAME` | `http://127.0.0.1:4723` / `emulator-5554` | Appium tests |
| `FAKER_SEED` | random (printed) | Replay test data (each test is reseeded from seed + test id) |
| `TESTGEN_MODEL` | `llama3.2:3b` | Model that drafts test cases from requirements |
| `UPDATE_SNAPSHOTS`, `UPDATE_PROMPT_SNAPSHOTS` | unset | Accept new visual / prompt baselines |

---

## 6. Extending the framework

| To add… | Do this |
|---|---|
| A UI page | Subclass `BasePage`, set `path`, bind locators in `__init__`, implement `expect_loaded`, add a fixture |
| An API endpoint | Add a method to a `BaseClient` subclass and a pydantic schema |
| A chatbot backend | Subclass `ChatbotClient`, implement `complete` and `is_available`; every AI test then works with it |
| A rule-based metric | Subclass `DeterministicMetric`, implement `evaluate` → `(score, reason)` |
| A judged metric | Add a method to `MetricFactory` |
| A retriever | Subclass `Retriever`, implement `_index` and `_score` |
| A chain step | Subclass `ChainStep`, implement `run(state)` |
| A prompt | Add it to `ai/prompts/library.json`, then refresh snapshots |
| A red-team attack | Add it to `ai/redteam/attacks.json` with its `checks` |
| A golden QA case | Add it to `ai/datasets/golden_qa.json` (with `required_facts`) |
| Test data | Subclass `Factory`, set `model`, implement `defaults()` |
| A BDD scenario | Add it to a `.feature` file in `tests/bdd/features/`; reuse or add steps in `test_ui_features.py` |
| A mobile screen | Subclass `BaseScreen` in `mobile/screens/` |
| A healable element | `self.healable("name", "selector", "plain-English description")` in a page object |
| A visual check | `comparator.compare("name", locator.screenshot(mask=[...]))` |
| A page served inside Playwright | `StaticSite(context, folder).json("GET", "/api/x", data).install()` ([`pages/support`](pages/support)) |
| A conversation eval | `run_conversation(send, turns, chatbot_role=...)` then `assert_test(case, [factory.conversation_completeness()])` |
| A requirement for AI test design | Add it to `ai/synthesis/requirements.json` (quote exact error messages) |

---

## 7. CI/CD

Two workflows, split by *when* they run:

**Automatic, on merge only:** [`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs
when a change lands on `main` (a merged pull request). It runs nothing on pull requests, on a
schedule or by hand.

| Job | Selects | Matrix |
|---|---|---|
| `api-sql` | `api or sql or hybrid` | |
| `ui` | `(ui or bdd) and not ai and not live` | chromium, firefox, webkit |

**Deactivated, manual only:** [`.github/workflows/optional-suites.yml`](.github/workflows/optional-suites.yml)
runs only from the Actions tab ("Run workflow", input `suite`):

| Job | Selects | Matrix |
|---|---|---|
| `lint` | `ruff check` + `ruff format --check` | |
| `mobile-web` | `mobile_web` | chromium, webkit |
| `mobile-native` | `mobile_native` on an Android emulator with Appium 2 | |
| `ai-offline` | `ai and not live and not judge` | |
| `ai-live` | `ai and live and not judge` / `ai and judge and not strong_judge` | two tiers |
| `docker` | builds the image, validates `docker-compose.yml` | |
| `report` | merges every job's Allure results into one HTML report (artifact) | |

Because pull requests get no CI, run `make lint` and `make test` (or the pre-commit hook) before
you open one: a broken change is found only after it is merged.

Shared install steps live in the composite action [`.github/actions/setup`](.github/actions/setup/action.yml).
Publishing the Allure report to GitHub Pages is opt-in: enable Pages (source: GitHub Actions) and set
the repository variable `DEPLOY_ALLURE_PAGES=true`.

The strong-judge tests (`-m strong_judge`) aren't selected even in the manual workflow, because a 7B judge takes about
2 min per call on a CPU runner. Run them locally or on a GPU runner.

**Other CI servers:** [`ci-templates/Jenkinsfile`](ci-templates/Jenkinsfile) and
[`ci-templates/azure-pipelines.yml`](ci-templates/azure-pipelines.yml) mirror the same policy
(functional stages on merge to `main`, everything else on a manual run).
They are templates, not executed by this repository.

## 8. Known limitations (read before trusting a green run)

- **Similarity is not correctness.** Embeddings are weak on negation and on missing facts. That's why keyword coverage and G-Eval completeness exist alongside similarity.
- **Small judges are noisy.** `llama3.2:3b` is trusted only for the metrics it calibrates on (see §3.1), and even then its written *reasons* are often incoherent. Read the score, not the reason.
- **LLM output is probabilistic.** Temperature 0 and a fixed seed make runs repeatable on one machine, not across hardware or model versions. Thresholds and budgets are deliberately not 100%.
- **Guard rails are heuristics.** 0/14 attack success on *this* library is not proof of safety. Add attacks whenever you find a new technique; the moderator's false positive shows the cost of tightening.
- **CPU inference is slow.** The judged tier takes tens of minutes on a laptop CPU; a GPU cuts that roughly tenfold.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| AI tests all **skipped** | `ollama serve` isn't running, or the model isn't pulled (the skip message names it) |
| `BrowserType.launch: Executable doesn't exist` | `playwright install chromium`, or set `BROWSER_EXECUTABLE_PATH` |
| `net::ERR_CERT_AUTHORITY_INVALID` behind a corporate proxy | Import your proxy CA into the NSS store: `certutil -A -d sql:$HOME/.pki/nssdb -n proxy -t "C,," -i ca.crt` |
| `TimeoutError: call timed out after 88.5s` from DeepEval | Raise `JUDGE_TIMEOUT_S`, or use a smaller or faster judge |
| `TypeError: ...__init__() got an unexpected keyword argument` inside `assert_test` | A custom metric's base-class constructor parameter shares a name with an attribute. See the `DeterministicMetric` docstring; `test_metric_survives_deepeval_cloning` guards this |
| Ragas `OUTPUT_PARSING_FAILURE` | The judge is too small; use `RAGAS_JUDGE_MODEL=qwen2.5:7b` or larger |
| Prompt snapshot test fails | You changed a prompt: review it, then `UPDATE_PROMPT_SNAPSHOTS=1 pytest tests/ai/prompts/test_prompt_registry.py` |
| `ImportError` from ragas about `langchain_community` | Keep `langchain-community<0.4` (pinned in `requirements.txt`) |
| Mobile-native tests all **skipped** | No Appium server at `APPIUM_SERVER_URL`; see [chapter 10](docs/learning-path/10-mobile.md) |
| Visual test fails after an intended style change | Check the diff image, then rerun with `UPDATE_SNAPSHOTS=1` |
| Pre-commit hook rewrote files | That's ruff formatting them; `git add` and commit again |
