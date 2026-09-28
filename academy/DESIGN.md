# AI QA Academy — Ink Studio design

## Intent

Replace the dark neon “cyber AI” look with a **light editorial studio**: cool stone canvas, navy ink type, deep teal actions. Brand reads as a learning product first; code stays dark for contrast.

## Tokens

| Role | Direction |
| --- | --- |
| Background | Cool stone OKLCH (~0.96, hue 250) |
| Ink | Navy foreground |
| Primary | Deep teal (~hue 185) |
| Accent | Muted gold for rare emphasis |
| Display | Fraunces |
| Body | IBM Plex Sans |
| Code | JetBrains Mono on dark `--code-bg` |

## Composition rules

1. Hero is full-bleed ink band; **AI QA Academy** is the hero wordmark.
2. First viewport: brand + one line + one supporting sentence + CTA group only.
3. Curriculum pathways use left accent bars, not heavy card chrome in the hero.
4. Lessons use a left-rule “In one minute” callout instead of a boxed tip card.
5. Motion respects `prefers-reduced-motion`.

## Content review (applied)

- Strip meta copy (“Gemini’s stack”) from the marketing surface.
- Bento blurbs shortened to outcome-first sentences.
- Curriculum index lists lessons as a track rail (title + summary + minutes).
- Tips remain sourced from `site/` — no invented TypeScript/LangTools stacks.

## Figma

Figma MCP authentication timed out in this environment. This document is the design source of truth until a Figma file can be authored with `/figma-generate-design` after auth.
