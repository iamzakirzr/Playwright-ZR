# Writing guide for AI QA Academy (not published)

## Reader
A QA engineer who knows testing (and some Python) but is new to AI. They want to understand how
the thing works, then how to test it, then how the repository does it. Assume no ML background.

## Voice
- Plain English, short sentences, active voice. Explain every term the first time (link the
  glossary: `[embedding](/start/glossary#embedding)`).
- No hype words ("revolutionary", "seamless", "powerful", "game-changer", "unlock").
- Honest about limits. If something failed or is unreliable, say so; that is the most useful
  part for a tester.
- Use one concrete running example where possible: the Sauce Demo store and its shop assistant.

## Page template (use these H2 headings, in this order, adapting names where natural)
```md
---
title: <Page title>
description: <One sentence, used for search and link previews>
---

# <Page title>

::: tip In one minute
Three to five bullet points: the whole page, compressed.
:::

## The idea
Explain the concept simply, with an analogy if it helps. One diagram (mermaid) where a picture
explains the mechanism better than words.

## How it works
The mechanism step by step. Short code or pseudo-code is welcome.

## How to test it
What can go wrong, what to assert, which metrics/oracles to use, and why.

## In this repository
Where it lives (file links), with a SHORT real excerpt copied from the repo (never invent APIs
or function names; open the file and copy). Explain the excerpt.

## Measured here
Facts measured by the repo's tests, copied from its docs/tests/commit messages (e.g. "qwen2.5:1.5b
called the search tool in 0 of 6 policy questions"). Only numbers you found in the repo.
Omit this section if there are none.

## Try it
Commands to run (`pytest ...`, `make ...`) and one small exercise.

## Check yourself
2 to 4 questions, each with the answer inside a `::: details Answer` block.
```

## Mechanics
- Links to repository files: absolute, `https://github.com/iamzakirzr/Playwright-ZR/blob/main/<path>`
  (folders: `/tree/main/<path>`). Check the path exists in the repo before linking.
- Links to other site pages: root-relative without extension, e.g. `/agents/langgraph`.
- Containers: `::: tip`, `::: info`, `::: warning`, `::: danger`, `::: details Title`.
- Diagrams: fenced ` ```mermaid ` blocks (flowchart LR/TD or sequenceDiagram). Keep them small
  (at most ~10 nodes), and quote labels containing punctuation: `A["retrieve (BM25)"]`.
- Code fences need a language (`python`, `bash`, `json`, `yaml`, `text`).
- Tables are fine for comparisons. Keep rows short.
- Length: roughly 900 to 1,800 words per page. Depth over breadth.
- Do NOT use `{{ }}` anywhere in prose or code outside fences (VitePress parses it as Vue). Inside
  code fences it is safe. Avoid raw `<` `>` in prose; use backticks.
- Accuracy over coverage: if you are unsure whether the repo does X, check; if it doesn't, say
  "not implemented in this repository" and teach the concept with a clearly labelled example.
