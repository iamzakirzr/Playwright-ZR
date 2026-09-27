---
title: How to use this site
description: Who AI QA Academy is for, how every page is laid out, what to install, and where each of the six tracks starts.
---

# How to use this site

::: tip In one minute
- This site teaches a tester who is new to AI how LLMs, RAG, agents and MCP work, and how to test them.
- Every idea is shown in one real, open-source repository: [Playwright-ZR](https://github.com/iamzakirzr/Playwright-ZR).
- Every page has the same sections, so you always know where to find the theory, the tests and the commands.
- You need Python 3.11 and git. The AI tests that call a model also need Ollama and two free models.
- Start with the [roadmap](/start/roadmap) if you want a week-by-week plan, or pick a track below.
:::

## Who this is for

You already test software. You can write a pytest test, read a stack trace and argue about what a
good assertion is. What you may not know yet is how a large language model produces an answer,
why the same question can get two different replies, or how you would even write an assertion for
"the chatbot answered correctly".

That is the gap this site closes. It assumes no machine-learning background. It does assume you
are willing to run code, because every page ends with something to run.

The running example is the [Sauce Demo](https://www.saucedemo.com) store and a small shop
assistant built on top of it: a chatbot that answers questions about a fictional store policy and
can add items to your cart. The repository tests that assistant the way you would test any
feature, from the browser, the API and the database, and then adds the AI-specific checks.

## What you will be able to do

After working through the site you should be able to:

- explain in plain words what a [token](/start/glossary#token), an [embedding](/start/glossary#embedding)
  and the [temperature](/start/glossary#temperature) are, and why they matter for a tester;
- write deterministic checks for AI output first, and add an [LLM judge](/start/glossary#judge-llm-as-a-judge)
  only after proving it can tell a good answer from a bad one;
- test retrieval with IR metrics such as [recall@k](/start/glossary#recall-k) and [nDCG](/start/glossary#ndcg);
- test an [agent](/start/glossary#agent) by checking the real state it changed and the tools it called,
  not just the text it wrote;
- test an [MCP](/start/glossary#mcp) server like any other API contract;
- attack a chatbot with a [red-team](/start/glossary#red-teaming) library and measure its guardrails;
- decide which AI checks should block a merge and which should only report.

## How every page is laid out

Every topic page uses the same headings, in the same order. Skim the ones you know, stop at the
ones you don't.

| Section | What it gives you |
|---|---|
| **In one minute** | The whole page in three to five bullets. Read this first. |
| **The idea** | The concept in plain words, often with one small diagram. |
| **How it works** | The mechanism, step by step, sometimes with short code. |
| **How to test it** | What goes wrong, what to assert, which metric or oracle to use and why. |
| **In this repository** | The files that implement it, with a short excerpt copied from the code. |
| **Measured here** | Numbers the repository's own tests produced. Nothing is invented. |
| **Try it** | Commands to run and one small exercise. |
| **Check yourself** | Two to four questions with folded answers. |

A note on **Measured here**: the numbers come from a small model (`qwen2.5:1.5b`) running on a
CPU. They are there to show you what real failures look like, not to rank models. When the page
says "the model called the search tool in 0 of 6 policy questions", that is a measurement from
a test in the repository, and the page links to where it came from.

Pages that describe the industry (the last track) are the exception: they separate general
practice from what this repository demonstrates, and they contain no statistics.

## Prerequisites

You need:

- **Python 3.11 or newer**, and `make` (on Windows without `make`, copy the `pytest` line from
  the [`Makefile`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/Makefile) and run it directly);
- **git**;
- about 8 GB of free disk space if you want the models;
- optionally, [Ollama](https://ollama.com/download) to run open-source models locally. No paid
  API key is needed anywhere.

Clone the repository and install everything with the commands from the
[README quick start](https://github.com/iamzakirzr/Playwright-ZR/blob/main/README.md):

```bash
git clone https://github.com/iamzakirzr/Playwright-ZR.git
cd Playwright-ZR
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
make setup            # CPU-only torch, requirements, Chromium, pre-commit hook
make help             # every command, one line each
```

`make setup` installs a CPU-only build of PyTorch (used for embeddings and classifiers), the
Python requirements, the Chromium browser for Playwright and a git pre-commit hook.

For the live AI tests, install Ollama and pull the two models:

```bash
ollama serve &                   # leave running
ollama pull qwen2.5:1.5b         # chatbot under test (~1 GB)
ollama pull llama3.2:3b          # judge for quality metrics (~2 GB)
```

`make models` runs the same two `ollama pull` commands. The README notes that the thresholds were
measured on Ollama 0.34.4 and that other versions can shift a small model's output.

::: info Settings live in one place
Every URL, model name, threshold and budget is a field in
[`config/settings.py`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/config/settings.py),
overridable by an environment variable or a `.env` file (copy
[`.env.example`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/.env.example)).
:::

## Offline and live tiers

The repository sorts its tests by what they need to run. Markers are added automatically: a test
that needs Ollama gets `live`, a test that needs a judge model gets `judge`, and a test that needs
the optional 7B judge gets `strong_judge`. That gives you tiers you can run in order.

| Tier | Command | Needs | What it runs |
|---|---|---|---|
| Functional | `make test-functional` | nothing extra | UI, API, SQL, hybrid and BDD tests, no AI |
| AI offline | `make test-ai-offline` | nothing extra | embeddings, classifiers, scripted (stub) models, MCP |
| Everything offline | `make test` | nothing extra | the two rows above together |
| AI live | `make test-ai-live` | Ollama + `qwen2.5:1.5b` | real model behaviour, no judge |
| AI judged | `make test-ai-judged` | + `llama3.2:3b` | metrics the 3B judge passed calibration for (slow on CPU) |
| AI strong judge | `make test-ai-strong` | + `ollama pull qwen2.5:7b` | relevancy, correctness, hallucination, judged safety, Ragas |

Each target is a plain `pytest -m ...` call. For example, `make test-ai-offline` runs
`pytest -m "ai and not live and not judge and not strong_judge"`.

If Ollama is not running, or a model is missing, the live tests **skip** with a message naming
what to pull. They never fail for that reason. So `make test-ai-live` on a laptop without Ollama is
safe: you will just see skips.

```bash
make test-functional  # ~30 s
make test-ai-offline  # ~40 s
make test-ai-live     # needs `ollama serve`
make report-open      # Allure HTML report of the last run (needs Node.js)
```

::: warning CPU is slow
The judged tier takes tens of minutes on a laptop CPU. A 7B judge call takes one to two minutes
each. Start with the offline tiers and one live test file, not the whole live suite.
:::

## The six tracks

The site is split into six tracks. The first four teach AI concepts and how to test them; the
fifth is the non-AI QA framework they all build on; the sixth is about using all of this at work.

**1 · How LLMs work** — [Start: LLMs from the inside](/foundations/how-llms-work)
Tokens, embeddings, temperature and tool calling, then prompting, prompt chaining, AI search
and RAG.

**2 · Evaluating AI** — [Start: Evaluating LLM output](/evals/evaluating-llms)
Semantic similarity, faithfulness, calibrated LLM judges, performance evals, production metrics,
observability and red teaming.

**3 · Agents** — [Start: What an agent is](/agents/what-is-an-agent)
How to test an agent by its state and trajectory, how to build one by hand, with LangChain and
with LangGraph, and what changes for voice agents.

**4 · MCP** — [Start: How MCP works](/mcp/how-mcp-works)
The Model Context Protocol, contract tests for an MCP server, and driving a browser with
Playwright MCP.

**5 · The QA framework** — [Start: Tour of the repository](/framework/overview)
Page objects, API service clients, SQL repositories, cross-layer tests and CI/CD.

**6 · AI for QA at work** — [Start: How companies use AI in QA](/industry/ai-in-qa-at-companies)
How teams use AI to help testing and how they test AI features, then a
[step-by-step adoption playbook](/industry/adoption-playbook).

::: tip Which track first?
If you have never tested an AI feature, do track 5 quickly (you probably know most of it), then
tracks 1, 2, 3, 4 in order. If you already know how LLMs work, jump to track 2. The
[roadmap](/start/roadmap) turns this into a six-week plan. Unknown word? The
[glossary](/start/glossary) has short definitions with links back to the pages.
:::

## The repository's own course

The repository also ships a text course in
[`docs/learning-path`](https://github.com/iamzakirzr/Playwright-ZR/tree/main/docs/learning-path):
15 short chapters, each with files to read, a command to run, an exercise and a quiz. This site
explains the ideas in more depth; the chapters are the hands-on companion. The
[roadmap](/start/roadmap) maps each week to both.

## Check yourself

1. You run `make test-ai-live` on a machine without Ollama. What happens?

::: details Answer
The live tests skip, each with a message saying which server or model is missing. They do not
fail, so a machine without Ollama still gives you a clean offline run.
:::

2. Which section of a page would you read to find out how the repository actually implements a
concept, and which to find real numbers?

::: details Answer
**In this repository** shows the files and a short excerpt from the code. **Measured here** lists
numbers produced by the repository's own tests, copied from its docs, tests or commit messages.
:::

3. Why does the repository need two different models, `qwen2.5:1.5b` and `llama3.2:3b`?

::: details Answer
`qwen2.5:1.5b` is the chatbot under test. `llama3.2:3b` is the judge that scores some of its
answers. Using a different model family for the judge avoids a model grading its own habits. The
judge is only trusted for the metrics where it passed calibration.
:::
