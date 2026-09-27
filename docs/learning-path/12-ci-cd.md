# 12 · CI/CD pipelines

## Why
Tests that only run on your laptop protect nobody, but a pipeline that runs everything on every
change is slow and, for LLM tests, noisy. This repository makes a deliberate trade: **only the
deterministic functional suites (UI, API, SQL) run automatically, and only when a pull request is
merged into `main`.** Everything else is kept, deactivated, behind a manual button.

## Automatic: [`.github/workflows/tests.yml`](../../.github/workflows/tests.yml)
Trigger: `push` to `main`, which is what a merge produces. No `pull_request`, `schedule` or
`workflow_dispatch` trigger.

| Job | What | Matrix |
|---|---|---|
| `api-sql` | API, SQL and hybrid (API ↔ DB) tests, parallel with `-n auto` | |
| `ui` | UI pages, Playwright essentials, visual baselines, BDD scenarios | chromium, firefox, webkit |

## Deactivated, manual only: [`.github/workflows/optional-suites.yml`](../../.github/workflows/optional-suites.yml)
Trigger: `workflow_dispatch` only. Start it from the Actions tab and pick a `suite`
(`all`, `lint`, `mobile`, `ai-offline`, `ai-live`, `docker`).

| Job | What | Matrix |
|---|---|---|
| `lint` | `ruff check` + `ruff format --check` | |
| `mobile-web` | phones emulated by Playwright | chromium, webkit |
| `mobile-native` | Android emulator (API 33) + Appium 2 + Chrome | |
| `ai-offline` | embeddings, classifiers, prompts, chains, guards, MCP, LangGraph agent | |
| `ai-live` | real model + 3B judge on Ollama | behaviour, judged |
| `docker` | builds the test image, validates `docker-compose.yml` | |
| `report` | merges every job's Allure results into one HTML report | |
| `publish-report` | deploys that report to GitHub Pages (`main` only, opt-in) | |

The shared install steps live in one **composite action**,
[`.github/actions/setup/action.yml`](../../.github/actions/setup/action.yml), so each job reads as
checkout → setup → pytest → upload. Every job uploads traces, screenshots and JUnit XML as artifacts.

### The trade-off, stated plainly
- **Merge-only means post-merge detection.** A pull request gets no CI signal, so a broken change
  is found after it is on `main`. The pre-commit hook and `make test` locally are the gate now.
- **AI suites are manual** because they need an Ollama server, take 10 to 20 minutes on CPU, and
  small models behave differently across machines (see chapter 14). Run them before merging a
  change to `ai/` or `apps/`.
- To go back to gating pull requests, add `pull_request:` under `on:` in `tests.yml`.

## Other CI servers
[`ci-templates/Jenkinsfile`](../../ci-templates/Jenkinsfile) and
[`ci-templates/azure-pipelines.yml`](../../ci-templates/azure-pipelines.yml) follow the same policy:
functional stages on merge to `main`, everything else on a manual run. They are **templates**:
not executed by this repo, so adapt agent labels and pools before using them.

## Locally, before you push
```bash
make lint            # or let the pre-commit hook do it on every commit
make test            # everything that needs no model server
docker compose up --abort-on-container-exit --exit-code-from tests   # the whole stack
```

## Test your knowledge
1. Why are the AI-live tiers separate jobs instead of one long job?
2. Why do the UI tests run on three browsers but the API tests only once?
3. What is the first thing you download when a CI UI test fails?
4. With CI only on merge, what catches a broken change before it reaches `main`?

<details><summary>Answers</summary>

1. They run in parallel (faster), fail independently, and a slow judge tier can't block the
   model-behaviour signal.
2. Rendering differs per engine; an HTTP call doesn't. Repeating API tests per browser costs
   minutes and finds nothing.
3. The Playwright trace from the job's artifact: `playwright show-trace trace.zip` replays the run
   with DOM snapshots, network and console.
4. Nothing in CI. The pre-commit hook (ruff) and running `make test` locally before opening the
   pull request; that is the cost of the merge-only policy.
</details>
