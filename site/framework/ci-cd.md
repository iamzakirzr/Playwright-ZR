---
title: CI/CD
description: Playwright-ZR's CI policy - hermetic lint/unit/SQL/essentials/AI-offline on every PR, Sauce Demo and Restful Booker only on merge to main, live AI and mobile by manual dispatch.
---

# CI/CD

::: tip In one minute
- **PR + main**: `.github/workflows/tests.yml` runs **lint** and a **hermetic** job (unit, SQL/hybrid, local Playwright essentials, healing, AI offline). No Sauce Demo, Restful Booker, or Ollama on the PR gate.
- **Main only**: the same workflow also runs **API** (Restful Booker) and **UI/BDD** (Sauce Demo) after merge.
- **Manual**: `.github/workflows/optional-suites.yml` holds **mobile, live AI, Docker and Allure**, started from the Actions tab.
- **Local PR gate**: `make lint` and `make test-hermetic`.
- Ollama in Docker Compose is pinned to **0.34.4** (same as the live AI CI job).
:::

## The idea

A pipeline is a promise: "if this is green, the change is safe enough". Running everything on every change
sounds safest, but it is slow, and for LLM tests it is **noisy**: a small model on a different machine can
give a different answer at temperature 0. A red build that is red for no reason trains people to ignore red
builds.

So this repository splits its suites by how **deterministic** and how **expensive** they are. Pull requests
get a hermetic signal; public demo sites and live models stay off the critical path.

```mermaid
flowchart TD
  PR["Pull request"] --> TY["tests.yml"]
  TY --> L["lint"]
  TY --> H["hermetic: unit / SQL / essentials / healing / AI offline"]
  M["Merge to main"] --> TY
  TY --> J1["api-sql: Restful Booker + SQL"]
  TY --> J2["ui: Sauce Demo, chromium/firefox/webkit"]
  Human["Actions tab, Run workflow"] --> OS["optional-suites.yml"]
  OS --> O["mobile, ai-live, docker, Allure"]
```

## How it works

### Automatic: tests.yml

[`.github/workflows/tests.yml`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/.github/workflows/tests.yml)
triggers on `pull_request` and on `push` to `main`.

| Job | When | Selects | Matrix |
|---|---|---|---|
| `lint` | PR + main | ruff check + format | none |
| `hermetic` | PR + main | `(unit or sql or hybrid or essentials or healing) and not live`, then AI offline | chromium |
| `api-sql` | main only | `api or sql or hybrid` | none |
| `ui` | main only | Sauce Demo UI + BDD (excludes essentials/healing) | chromium, firefox, webkit |

The UI job runs on three engines because rendering differs per engine. The API job runs once because an HTTP
call does not care which browser is installed. `fail-fast: false` lets every browser finish, so one engine's
failure does not hide the others. Every job uploads `reports/` (JUnit XML and Allure results) and, for UI,
`test-results/` (traces, screenshots, videos) as artifacts, even when tests fail.

### Manual: optional-suites.yml

[`.github/workflows/optional-suites.yml`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/.github/workflows/optional-suites.yml)
triggers only on `workflow_dispatch`, with a `suite` input: `all`, `lint`, `mobile`, `ai-offline`, `ai-live`
or `docker`.

| Job | What it runs |
|---|---|
| `lint` | `ruff check` and `ruff format --check` |
| `mobile-web` | `mobile_web` on Chromium and WebKit (Firefox cannot emulate `isMobile`) |
| `mobile-native` | an Android emulator (API 33) with Appium 2 and Chrome |
| `ai-offline` | `ai and not live and not judge and not strong_judge` |
| `ai-live` | two tiers: `live and not judge`, and `judge and not strong_judge`, with Ollama pinned |
| `docker` | builds the image and validates `docker-compose.yml` |
| `report` | merges every job's Allure results into one HTML report (an artifact) |
| `publish-report` | deploys it to GitHub Pages, opt-in with the variable `DEPLOY_ALLURE_PAGES=true` |

The strong-judge tests (`-m strong_judge`) are not selected even here: a 7B judge takes about two minutes
per call on a CPU runner. Run them locally or on a GPU runner.

Shared install steps (Python, CPU-only torch, requirements, the requested Playwright browsers) live in one
composite action, [`.github/actions/setup/action.yml`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/.github/actions/setup/action.yml),
so each job reads as checkout, setup, pytest, upload.

### Locally: pre-commit, make, Docker

- [`.pre-commit-config.yaml`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/.pre-commit-config.yaml)
  runs ruff (lint with `--fix`, and format) plus whitespace, YAML, JSON and large-file checks on every commit.
  `make setup` installs the hook. It uses the same ruff version as the lint job, so a clean commit means a green lint job.
- `make lint` and `make test-hermetic` are the pre-merge gate (same suites as the PR jobs).
- Dependencies install from `pyproject.toml` extras via `pip install -e ".[…]"`.
- The [`Dockerfile`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/Dockerfile) builds a test runner
  (Python 3.11, CPU-only torch, Chromium) whose default command runs everything that needs no model server.
  [`docker-compose.yml`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/docker-compose.yml) adds an
  Ollama **0.34.4** service and a one-shot model pull; `SUITE="live and not judge" docker compose up ...` picks another tier.

### Other CI servers

[`ci-templates/Jenkinsfile`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/ci-templates/Jenkinsfile) and
[`ci-templates/azure-pipelines.yml`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/ci-templates/azure-pipelines.yml)
follow the same policy: functional stages on merge to `main`, everything else on a manual run. In Jenkins, the
first `SUITE` choice, `functional`, is the default for automatic builds. In Azure, `pr: none` disables pull-request
builds and the AI and lint stages have `condition: eq(variables['Build.Reason'], 'Manual')`. They are
**templates**, not executed by this repository: adapt agents, pools and the Ollama connection before using them.

## How to test it

How do you judge a CI policy? Ask what it catches, when, and at what cost.

**The trade-off, stated plainly.** Pull requests get a **hermetic** CI signal (lint + unit/SQL/local
essentials/healing + AI offline). Sauce Demo and Restful Booker stay on **main-only** jobs so third-party
availability cannot flake a required PR check. Live AI remains manual. See
[chapter 12](https://github.com/iamzakirzr/Playwright-ZR/blob/main/docs/learning-path/12-ci-cd.md).

**Why the AI suites are manual.**

- They need an **Ollama server** and several gigabytes of models on the runner.
- They are **slow on CPU**: 10 to 20 minutes for the live tiers, and judged metrics take much longer.
- **Small models differ across machines.** Temperature 0 and a fixed seed make runs repeatable on one
  machine, not across hardware or Ollama versions. An automatic job that fails for that reason is noise.

That does not mean "never run them". Run them before merging a change to `ai/` or `apps/`, and read them as
evaluations with thresholds, not as pass/fail unit tests. See [Evaluating LLMs](/evals/evaluating-llms) and
[Performance evals](/evals/performance-evals).

**Evidence on failure.** When a UI job fails, download its artifact and run `playwright show-trace` on the
trace zip: it replays the run with DOM snapshots, network and console. The `ai-live` job also uploads
`ollama.log`, and `attach_llm_exchange` in
[`reporting/allure_helpers.py`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/reporting/allure_helpers.py)
records every prompt and answer, so a failed evaluation shows what the model said, not only a score.

## In this repository

The hermetic PR job, from `tests.yml`:

```yaml
  hermetic:
    name: Hermetic (unit / SQL / essentials / healing / AI offline)
    steps:
      - uses: ./.github/actions/setup
        with:
          browsers: chromium
          extras: ui,apps,ai,visual
      - run: >
          pytest -m "(unit or sql or essentials or healing) and not live and not api and not hybrid"
          --browser chromium -n auto
      - run: pytest -m "ai and not live and not judge and not strong_judge" -n auto
```

Sauce Demo UI/BDD still run on main (three browsers). Markers come from folders (see
[the framework tour](/framework/overview)).

The Ollama pin in the `ai-live` job, with the reason recorded next to it:

```yaml
      # Pinned: a new Ollama build can change a small model's temperature-0 output, and every
      # threshold here was measured on this version (an unpinned install dropped prices from
      # the summarizer test in CI while 0.34.4 kept them on 10/10 seeds).
      OLLAMA_VERSION: 0.34.4
```

## Measured here

Facts recorded in the repository that shaped this policy:

- An unpinned Ollama install dropped prices from the summarizer test in CI, while Ollama 0.34.4 kept them
  on 10 of 10 seeds (comment in `optional-suites.yml`).
- The 3B judge's contextual metrics passed locally and failed in CI on identical input (README, section 3.1);
  they moved to the 7B judge tier.
- The 3B judge confused speakers in CI for role adherence and turn relevancy (README, section 3.12).
- A 7B judge takes about two minutes per call on a CPU runner, so `strong_judge` is not run in CI.
- The live AI suites take 10 to 20 minutes on CPU (learning path chapter 12).

## Try it

```bash
make lint                              # what the lint job runs
make test-hermetic                     # same suites as the PR gate
pre-commit run --all-files             # the hook, on every file
docker compose up --abort-on-container-exit --exit-code-from tests
```

Exercise: open a pull request that breaks one hermetic unit test and watch the PR `lint` / `hermetic`
jobs fail. Then write down, for your team, which suites you would put on pull requests, which on merge,
and which on a nightly or manual run, and why.

## Check yourself

1. With this policy, what catches a broken change before it reaches `main`?

::: details Answer
The PR `lint` and `hermetic` jobs (plus pre-commit locally). Sauce Demo / Restful Booker / live Ollama
are intentionally *not* on that critical path.
:::

2. Why do the UI tests run on three browsers but the API tests only once?

::: details Answer
Rendering and browser behaviour differ per engine; an HTTP call does not. Repeating API tests per browser
costs minutes and finds nothing.
:::

3. Give two reasons the AI suites are not automatic.

::: details Answer
They need an Ollama server and models on the runner, they are slow on CPU (10 to 20 minutes, much more for
judged tiers), and small models can answer differently on different machines or Ollama versions, which makes
automatic runs noisy.
:::

4. Why is the Ollama version pinned in the `ai-live` job?

::: details Answer
Every threshold was measured on 0.34.4. A newer build changed a small model's temperature-0 output in CI
(prices dropped from the summarizer), so an unpinned version turns an infrastructure change into a test failure.
:::
