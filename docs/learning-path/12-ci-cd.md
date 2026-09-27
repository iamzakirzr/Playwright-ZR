# 12 · CI/CD pipelines

## Why
Tests that only run on your laptop protect nobody, but a pipeline that runs everything on every
change is slow and, for live LLM tests, noisy. This repository splits suites by **determinism**
and **cost**: pull requests get a hermetic gate; public demo sites and live models stay off that path.

## Automatic: [`.github/workflows/tests.yml`](../../.github/workflows/tests.yml)
Triggers: `pull_request` and `push` to `main`.

| Job | When | What | Matrix |
|---|---|---|---|
| `lint` | PR + main | `ruff check` + `ruff format --check` | |
| `hermetic` | PR + main | unit, SQL, local Playwright essentials, healing, then AI offline | chromium |
| `api-sql` | main only | API, SQL and hybrid (hits Restful Booker) | |
| `ui` | main only | Sauce Demo UI + BDD (essentials/healing already covered by hermetic) | chromium, firefox, webkit |

Hermetic deliberately **excludes** `api` and `hybrid` so a required PR job never depends on
Restful Booker or Sauce Demo. Local equivalent: `make lint` and `make test-hermetic`.

## Manual only: [`.github/workflows/optional-suites.yml`](../../.github/workflows/optional-suites.yml)
Trigger: `workflow_dispatch` only. Start it from the Actions tab and pick a `suite`
(`all`, `lint`, `mobile`, `ai-offline`, `ai-live`, `docker`).

| Job | What | Matrix |
|---|---|---|
| `lint` | `ruff check` + `ruff format --check` | |
| `mobile-web` | phones emulated by Playwright | chromium, webkit |
| `mobile-native` | Android emulator (API 33) + Appium 2 + Chrome | |
| `ai-offline` | embeddings, classifiers, prompts, chains, guards, MCP, LangGraph agent | |
| `ai-live` | real model + 3B judge on Ollama **0.34.4** | behaviour, judged |
| `docker` | builds the test image, validates `docker-compose.yml` (Ollama pinned 0.34.4) | |
| `report` | merges every job's Allure results into one HTML report | |
| `publish-report` | deploys that report to GitHub Pages (`main` only, opt-in) | |

The shared install steps live in one **composite action**,
[`.github/actions/setup/action.yml`](../../.github/actions/setup/action.yml) (`extras=` selects
`pyproject.toml` optional dependencies). Every job uploads traces, screenshots and JUnit XML as artifacts.

### The trade-off, stated plainly
- **PRs are hermetic.** Lint + local/SQL/offline AI catch most breakages before merge. Sauce Demo
  and Restful Booker still run on `main` because they are useful integration smoke, not a PR gate.
- **Live AI suites are manual** because they need an Ollama server, take 10 to 20 minutes on CPU, and
  small models behave differently across machines (see chapter 14). Run them before merging a
  change to `ai/` or `apps/`.

## Other CI servers
[`ci-templates/Jenkinsfile`](../../ci-templates/Jenkinsfile) and
[`ci-templates/azure-pipelines.yml`](../../ci-templates/azure-pipelines.yml) are **templates**
(not executed here). Prefer the GitHub Actions policy above when updating them.

## Locally, before you push
```bash
make lint            # or let the pre-commit hook do it on every commit
make test-hermetic   # same suites as the PR gate (no Sauce Demo / Booker / Ollama)
docker compose up --abort-on-container-exit --exit-code-from tests   # the whole stack
```

## Test your knowledge
1. Why are the AI-live tiers separate jobs instead of one long job?
2. Why do the UI tests run on three browsers but the API tests only once?
3. What is the first thing you download when a CI UI test fails?
4. What does the PR hermetic job deliberately *not* call, and why?

<details><summary>Answers</summary>

1. They run in parallel (faster), fail independently, and a slow judge tier can't block the
   model-behaviour signal.
2. Rendering differs per engine; an HTTP call doesn't. Repeating API tests per browser costs
   minutes and finds nothing.
3. The Playwright trace from the job's artifact: `playwright show-trace trace.zip` replays the run
   with DOM snapshots, network and console.
4. Restful Booker and Sauce Demo (and live Ollama). Availability or UI drift on those hosts must
   not flake a required PR check; they stay on the main-only jobs / manual live suites.
</details>
