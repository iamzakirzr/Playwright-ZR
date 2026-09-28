# AI QA Academy — Pastel Discover (mobile-first)

## Intent

An intuitive learning platform that helps users stay **organized, motivated, and confident** while growing advanced QA skills at their own pace. Soft teal pastels, rounded interactive track cards, welcome → discover flow. **No calendar scheduling.**

## Visual language

| Role | Direction |
| --- | --- |
| Canvas | Soft mint-teal wash → off-white |
| Primary | Vibrant teal CTA / active pills |
| Cards | Pastel mint, sand, blush, sage — large radius (~28px) |
| Ink | Charcoal headings, muted grey body |
| Display | Outfit |
| Body | Figtree |
| Code | JetBrains Mono on dark `--code-bg` |

## Screens

1. **Welcome** — full-bleed soft wash; brand **AI QA Academy** as hero signal; one headline; one supporting sentence; circular teal arrow CTA; stylized book-stack visual (no floating badges).
2. **Discover** — header + “Grow with expert-led QA lessons”; search/filter pills (`All`, `Playwright`, `API`, `Judges`, `RAG`, …); **2×2 pastel course cards** labeled Playwright / Typed API / LLM Judges / RAG (not Data Science / ML); “Core tracks” list (mentor-row pattern) linking curriculum tracks.
3. **Learn browse** — same card/list language; lesson rows with icon + title + arrow. **Never** a month calendar or timetable.

## Composition rules

1. First viewport: brand, one headline, one sentence, one CTA, one dominant visual.
2. No cards in the hero. Cards only for interactive track selection.
3. One job per section.
4. Motion: welcome rise-in, card stagger, CTA pulse — all gated by `prefers-reduced-motion`.
5. Content stays faithful to Playwright-ZR / `site/` — no invented stacks.

## Subagent

Use `.cursor/agents/academy-mobile-design.md` for future pastel/mobile design passes.
