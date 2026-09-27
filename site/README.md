# AI QA Academy (learning site)

The learning site for this repository: how LLMs, RAG, agents, LangChain, LangGraph and MCP work, and
how to test them, using this framework as the running example. Built with [VitePress](https://vitepress.dev).

```bash
cd site
npm ci            # once
npm run dev       # live-reloading preview on http://localhost:5173
npm run build     # static site in .vitepress/dist
```

- Pages are Markdown, one folder per track; the sidebar lives in `.vitepress/config.mts`.
- Before writing a page, read [`WRITING.md`](WRITING.md): the page template, the voice, and the rule
  that every measured number must come from a test or doc in this repository.
- Deployed on Vercel from this folder (framework preset: VitePress, root directory: `site`).
