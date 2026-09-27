# AI QA Academy (Next.js)

Premium e-learning shell for [Playwright-ZR](https://github.com/iamzakirzr/Playwright-ZR), built to the Gemini UI overhaul plan:

- **Next.js 15** + **React 19** + **Tailwind CSS v4**
- **Shadcn-style** primitives (`components/ui`)
- **Framer Motion** marketing hero + bento
- **Shiki** IDE-like code blocks
- **RAG visualizer** on the RAG lesson

Content is mapped from `site/` and the Python repository. It does **not** invent TypeScript API frameworks or LangTools demos that are not in this repo.

## Develop

```bash
cd academy
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Learn shell: `/learn`.

## Deploy

The legacy VitePress docs remain in `/site` (current Vercel `rootDirectory`). To ship this Next app, point a Vercel project `rootDirectory` at `academy` (see `vercel.json` here).

## Phases

| Phase | Status |
| --- | --- |
| 1 Foundation & theming | Done (`globals.css` OKLCH `@theme`, `lib/utils.ts`) |
| 2 Design system | Done (Button, Card, Badge, Accordion, Tabs) |
| 3 Landing / marketing | Done (Hero, CurriculumBentoGrid) |
| 4 Learn UI | Done (sidebar layout, CodeBlock, RAGVisualizer) |
| 5 Content map | Done (lessons from Playwright-ZR / `site/`) |
