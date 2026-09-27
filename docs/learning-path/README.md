# Learning path

A course through this repository, one chapter per layer. Each chapter follows the same shape:

1. **Why**: the problem the layer solves, in two or three sentences.
2. **Read**: the files to open, in order.
3. **Run**: one command that proves it works.
4. **Try it**: a small exercise that changes the code.
5. **Test your knowledge**: a short quiz, answers folded underneath.

Work through them in order; each chapter uses what the previous one built.

| # | Chapter | Needs Ollama? | Command |
|---|---|---|---|
| 01 | [Setup and your first test](01-setup-and-first-test.md) | no | `make setup && make smoke` |
| 02 | [Page Object Model](02-page-object-model.md) | no | `make test-ui` |
| 03 | [API testing with service objects](03-api-testing.md) | no | `make test-api` |
| 04 | [Database and cross-layer tests](04-database-and-hybrid.md) | no | `make test-sql` |
| 05 | [Test data, BDD and reporting](05-data-bdd-reporting.md) | no | `make bdd && make report` |
| 06 | [AI evaluation fundamentals](06-ai-evals-fundamentals.md) | yes | `make test-ai-live` |
| 07 | [AI search, prompts and chains](07-ai-search-prompts-chains.md) | partly | `make test-ai-offline` |
| 08 | [Agents and MCP servers](08-agents-and-mcp.md) | partly | `pytest -m "agent or mcp"` |
| 09 | [Red teaming and guardrails](09-red-teaming.md) | partly | `pytest -m redteam` |
| 10 | [Mobile: emulation and Appium](10-mobile.md) | no | `make test-mobile-web` |
| 11 | [Self-healing locators and visual testing](11-healing-and-visual.md) | partly | `pytest -m "healing or visual"` |
| 12 | [CI/CD pipelines](12-ci-cd.md) | no | `make lint` |
| 13 | [Playwright essentials](13-playwright-essentials.md) | no | `pytest tests/ui/essentials` |
| 14 | [Synthetic data and advanced AI evals](14-synthetic-data-and-advanced-evals.md) | partly | `pytest tests/ai/synthesis tests/ai/conversation tests/ai/langchain` |
| 15 | [Building and testing agents with LangChain and LangGraph](15-building-agents-with-langchain.md) | partly | `pytest tests/ai/langgraph` |

Chapter 13 fits right after chapter 2 if you prefer to learn every browser technique first.

**AI / LLM track** (after chapters 01 to 05), in this order:

| Step | Chapter | You learn to |
|---|---|---|
| 1 | 06 AI evaluation fundamentals | score LLM answers: similarity, faithfulness, calibrated judges |
| 2 | 07 AI search, prompts and chains | test retrieval, versioned prompts and multi-step chains |
| 3 | 14 Synthetic data and advanced evals | generate and gate test data; multi-turn, BLEU/ROUGE, a LangChain RAG app |
| 4 | 08 Agents and MCP servers | test a tool-calling agent and an MCP server (state + trajectory oracles) |
| 5 | 15 Building agents with LangChain and LangGraph | build an agent with `@tool` and `StateGraph`, and test every layer |
| 6 | 09 Red teaming and guardrails | attack what you built and measure the guardrails |
[Course coverage](../course-coverage.md) maps ExecuteAutomation course topics to these chapters.

"Partly" means the chapter has an offline tier that runs anywhere and a live tier that skips
cleanly without Ollama.

## Three rules the whole framework follows

- **Tests say *what*, objects say *how*.** A test never contains a selector, a URL or SQL.
  Those live in page objects, service clients and repositories.
- **Configuration comes from one place.** Every URL, credential, model name and threshold is a
  field in [`config/settings.py`](../../config/settings.py), overridable by an environment variable.
- **Every AI threshold is calibrated.** Before a metric judges the bot, a test proves the metric
  itself can tell a good answer from a bad one ([`tests/ai/validation/test_metric_calibration.py`](../../tests/ai/validation/test_metric_calibration.py)).
