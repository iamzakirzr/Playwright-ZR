# AI QA Academy — Tools Dashboard

## Purpose

Help QA engineers stay organized while learning the **real tools in Playwright-ZR**.  
Structure is flat and practical:

1. **Dashboard** — categories (UI, API, DB, AI Evals, …)
2. **Category** — tools in that category
3. **Tool** — curated **learning function calls** (+ related tests / lessons)

No calendar. No dense marketing chrome. Drive learning by practicing the calls each tool exposes.

## Categories (milestones)

| ID | Category | Milestone |
| --- | --- | --- |
| `ui` | UI Tools | Page objects, healing, visual compare |
| `api` | API Tools | Service clients + pydantic contracts |
| `db` | DB Tools | SQLite repositories + hybrid checks |
| `ai-evals` | AI Evals | Judges, factory metrics, deterministic gates |
| `rag` | RAG & Search | Retriever + `RagPipeline.answer` |
| `agents-mcp` | Agents & MCP | Shop assistant + store MCP tools |
| `mobile` | Mobile Tools | Appium screen objects |

## Phases

1. **Catalog** — typed `tools-catalog` grounded in repo paths and real method names  
2. **Dashboard** — home lists categories with counts  
3. **Category pages** — list tools for one category  
4. **Tool pages** — learning function calls, signatures, why they matter, related tests  
5. **Cross-links** — deep lessons under `/learn` remain available  
6. **Verify** — lint/build green; mobile-readable lists

## Community alignment

Taxonomy mirrors common QA + AI eval practice (Playwright POMs, API clients, SQL repos, DeepEval-style RAG/judge/MCP metrics) while staying faithful to **this** repository’s Python surfaces — no invented TypeScript stacks.

## Done when

Every category above has ≥1 tool; every tool has ≥3 curated learning calls; dashboard → category → tool navigates cleanly; `npm run build` passes.

## Catalog depth (loop)

Must include core surfaces learners hit first: `CheckoutPage`, `SelfHealingLocator`, `BookingRepository`, judge helpers (`deepeval_judge` / `ragas_judge`), plus the original POM/API/DB/eval/RAG/MCP/mobile set.
