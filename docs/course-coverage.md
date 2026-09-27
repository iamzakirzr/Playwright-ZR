# Course coverage: ExecuteAutomation (Karthik KK) topics → this repo

This maps the topics of Karthik KK's ExecuteAutomation courses to where each is practised
here. **How the list was built:** Udemy and Class Central block automated reading, so the
topics come from the courses' public descriptions and search listings, and from his
`mcp-playwright` documentation (sources at the end). It is not a lecture-by-lecture copy.

Status: **Covered** = implemented and tested here · **Partly** = the idea is covered with a
different tool or scope · **Not covered** = out of scope, with the reason.

## E2E Test Automation with Playwright

| Topic | Status | Where |
|---|---|---|
| Page Object Model, fixtures/hooks, parallel runs | Covered | [`pages/`](../pages), [`conftest.py`](../conftest.py), `-n auto` in the [`Makefile`](../Makefile) |
| Chromium, Firefox, WebKit | Covered | CI `ui` matrix; [`tests/ui/essentials`](../tests/ui/essentials) passes on all three |
| Auto-wait and web-first assertions | Covered | `expect(...)` throughout; [`pages/playground.py`](../pages/playground.py) |
| Network interception: mock, modify, block, wait | Covered | [`tests/ui/essentials/test_network.py`](../tests/ui/essentials/test_network.py) |
| Dialogs, iframes, new tabs | Covered | [`test_dialogs_frames_tabs.py`](../tests/ui/essentials/test_dialogs_frames_tabs.py) |
| File upload and download | Covered | [`test_files_and_auth.py`](../tests/ui/essentials/test_files_and_auth.py) |
| Login once, reuse the session (`storage_state`) | Covered | same file; used for real by [`tests/ui/test_checkout_e2e.py`](../tests/ui/test_checkout_e2e.py) |
| Emulation: locale, timezone, theme, geolocation, offline | Covered | [`test_emulation_and_input.py`](../tests/ui/essentials/test_emulation_and_input.py) |
| Mobile device emulation | Covered | [`tests/mobile/web`](../tests/mobile/web) |
| Screenshots, video, tracing | Covered | [`pytest.ini`](../pytest.ini): `--screenshot`, `--video`, `--tracing` on failure |
| Visual testing | Covered | [`visual/`](../visual), [`tests/ui/visual`](../tests/ui/visual) |
| API testing with Playwright | Covered | [`api/`](../api), [`tests/api`](../tests/api) |
| Recording tests (codegen) | Covered (docs) | [chapter 13](learning-path/13-playwright-essentials.md) |
| Allure and HTML reports | Covered | [`reporting/`](../reporting), `make report` |
| Docker and GitHub Actions | Covered | [`Dockerfile`](../Dockerfile), [`.github/workflows/tests.yml`](../.github/workflows/tests.yml) (hermetic lint/unit/SQL/essentials/AI-offline on every PR; Sauce Demo + Restful Booker on merge) and [`optional-suites.yml`](../.github/workflows/optional-suites.yml) (manual mobile/live AI) |
| TypeScript, C# and Java bindings | Not covered | This repo is Python; the concepts carry over one to one |

## Generative AI in software testing / AI-driven test automation

| Topic | Status | Where |
|---|---|---|
| Running LLMs locally (Ollama) | Covered | [`ai/chatbot/ollama_client.py`](../ai/chatbot/ollama_client.py) |
| Generating test cases with GenAI, grounded by RAG | Covered | [`ai/synthesis/test_cases.py`](../ai/synthesis/test_cases.py) + coverage review |
| Generating test data | Covered | Faker factories ([`data/`](../data)); synthetic goldens ([`ai/synthesis/goldens.py`](../ai/synthesis/goldens.py)) |
| AI-assisted UI automation (self-healing) | Covered | [`pages/healing/`](../pages/healing) |
| MCP: driving browsers and tools from an AI client | Covered | our MCP server [`apps/store_mcp`](../apps/store_mcp) + tests; client setup for Playwright MCP in [chapter 8](learning-path/08-agents-and-mcp.md) |
| OpenAI APIs in test code | Partly | Same pattern with a local model (no paid key); swap the client class to use a hosted API |
| TestRigor (no-code), Postman PostBot | Not covered | Commercial tools; nothing to practise in an open-source repo |

## Testing AI apps: DeepEval, RAGAs, HF Evaluate, LangChain, Ollama

| Topic | Status | Where |
|---|---|---|
| LLM-as-a-judge with local models, and judge calibration | Covered | [`ai/evaluators/judge.py`](../ai/evaluators/judge.py), [`tests/ai/validation/test_metric_calibration.py`](../tests/ai/validation/test_metric_calibration.py) |
| Test cases, datasets and goldens | Covered | [`ai/datasets`](../ai/datasets), `EvaluationDataset` in [`tests/ai/rag/test_dataset_evaluation.py`](../tests/ai/rag/test_dataset_evaluation.py) |
| RAG metrics (faithfulness, relevancy, contextual precision/recall) | Covered | [`ai/evaluators/factory.py`](../ai/evaluators/factory.py), [`tests/ai/rag`](../tests/ai/rag) |
| G-Eval and custom metrics | Covered | `completeness`/`correctness` GEval; `DeterministicMetric` subclasses |
| RAGAs | Covered | [`tests/ai/rag/test_ragas_crosscheck.py`](../tests/ai/rag/test_ragas_crosscheck.py) (7B judge) |
| Hugging Face `evaluate` (BLEU, ROUGE) | Covered | [`ai/evaluators/reference_metrics.py`](../ai/evaluators/reference_metrics.py), [`tests/ai/validation/test_reference_metrics.py`](../tests/ai/validation/test_reference_metrics.py) |
| Testing a LangChain application | Covered | [`ai/chatbot/langchain_client.py`](../ai/chatbot/langchain_client.py), [`tests/ai/langchain`](../tests/ai/langchain) |
| Chatbot testing, multi-turn | Covered | [`tests/ai/agent/test_agent_conversation.py`](../tests/ai/agent/test_agent_conversation.py), [`tests/ai/conversation`](../tests/ai/conversation) |
| AI agents and tool calling | Covered | [`apps/shop_assistant`](../apps/shop_assistant), [`tests/ai/agent`](../tests/ai/agent) |
| Building an agent with LangChain tools (`@tool`, `bind_tools`) | Covered | [`langgraph_agent.py`](../apps/shop_assistant/langgraph_agent.py), [chapter 15](learning-path/15-building-agents-with-langchain.md) |
| LangGraph: state graph, `ToolNode`, conditional routing | Covered | same; graph shape pinned by [`test_langgraph_agent_units.py`](../tests/ai/langgraph/test_langgraph_agent_units.py) |
| Agent memory (checkpointer, threads) and loop bounds | Covered | `InMemorySaver` + `recursion_limit`; memory, isolation and bound tests in the same file |
| Agentic RAG (retrieval as a tool) vs. retrieval node | Covered | `retrieval="tool"` / `"node"`; measured: the 1.5B model used the tool 0/6 times |
| Unit-testing LangChain code without a model | Covered | [`ScriptedChatModel`](../ai/chatbot/scripted_chat_model.py) (can `bind_tools`), recording `RunnableLambda` in [`tests/ai/langchain`](../tests/ai/langchain) |
| LangSmith tracing | Partly | Documented in chapter 15 (env vars only); needs a hosted account, so tests assert on the graph's own trajectory instead |
| MCP server testing | Covered | [`tests/ai/mcp`](../tests/ai/mcp) |
| Synthetic golden generation | Covered | DeepEval `Synthesizer` + quality gate, [`tests/ai/synthesis`](../tests/ai/synthesis) |
| AI safety testing | Covered | [`ai/redteam`](../ai/redteam), [`tests/ai/redteam`](../tests/ai/redteam) |
| Fine-tuning LLMs | Not covered | A model-building topic, not a testing one |

## Other courses

| Topic | Status | Why |
|---|---|---|
| Selenium C# / .NET framework development | Not covered | Different stack; the framework patterns (POM, factories, DI, reporting) are the same ones used here |
| Appium native apps | Partly | Appium drives Chrome on an Android emulator in CI; native APK screens are documented as the next step (the demo APK download is blocked in this environment) |
| Microservice contract testing (Pact) | Partly | Consumer-side contracts via pydantic schemas ([`api/schemas`](../api/schemas)); no Pact broker. [Guessing] whether the Pact course is his: the listing didn't name the instructor |

## Sources

- [Karthik KK on Udemy](https://www.udemy.com/user/karthik-kk/)
- [2026-End to End Test Automation with Playwright (TS/C#/Java)](https://www.udemy.com/course/e2e-playwright/)
- [AI Agents, RAG & LLM Evals for Beginners: DeepEval & RAGAS](https://www.udemy.com/course/ai-testing-deepeval-ragas-ollama/)
- [E2E Testing ChatBot, AI Agent, RAG, MCP Server with DeepEval](https://www.udemy.com/course/ai-testing-deepeval-chatbot-rag-agent-mcp/)
- [Generative AI in Software Automation Testing (mcp-playwright docs)](https://executeautomation.github.io/mcp-playwright/docs/ai-courses/GenAICourse)
- [executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright)
