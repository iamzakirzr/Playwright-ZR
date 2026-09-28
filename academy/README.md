# AI QA Academy (Next.js)

Tool-category dashboard for learning Playwright-ZR surfaces.

## Structure

- `/` — dashboard of categories (UI, API, DB, AI Evals, RAG, Agents/MCP, Mobile)
- `/tools/[category]` — tools in a category
- `/tools/[category]/[tool]` — curated learning function calls
- `/learn` — deeper lesson pages (linked from calls)

Design source: `DESIGN.md`. Catalog: `lib/tools-catalog.ts`.

## Develop

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
