# 12 · CI/CD pipelines

## Why
Tests that only run on your laptop protect nobody. The pipeline runs every tier at the right
moment: fast checks on every push, slow AI evals in parallel jobs, device tests on an emulator,
and everything nightly.

## GitHub Actions: [`.github/workflows/tests.yml`](../../.github/workflows/tests.yml)
| Job | What | Matrix |
|---|---|---|
| `lint` | `ruff check` + `ruff format --check` | |
| `api-sql` | API, SQL and hybrid tests, parallel with `-n auto` | |
| `ui` | UI pages, visual baselines, BDD scenarios | chromium, firefox, webkit |
| `mobile-web` | phones emulated by Playwright | chromium, webkit |
| `mobile-native` | Android emulator (API 33) + Appium 2 + Chrome | |
| `ai-offline` | embeddings, classifiers, prompts, chains, guards, MCP | |
| `ai-live` | real model + 3B judge on Ollama | behaviour, judged |
| `docker` | builds the test image, validates `docker-compose.yml` | |
| `report` | merges every job's Allure results into one HTML report | |
| `publish-report` | deploys that report to GitHub Pages (`main` only, opt-in) | |

The shared install steps live in one **composite action**,
[`.github/actions/setup/action.yml`](../../.github/actions/setup/action.yml), so each job reads as
checkout → setup → pytest → upload.

- **Nightly** (`schedule`) catches drift in the public demo sites and model behaviour.
- **Manual runs** (`workflow_dispatch`) take `suite` and `browser` inputs: run one tier on demand.
- Every job uploads traces, screenshots and JUnit XML as artifacts.

## Other CI servers
[`ci-templates/Jenkinsfile`](../../ci-templates/Jenkinsfile) and
[`ci-templates/azure-pipelines.yml`](../../ci-templates/azure-pipelines.yml) show the same stages.
They are **templates**: not executed by this repo, so adapt agent labels and pools before using them.

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

<details><summary>Answers</summary>

1. They run in parallel (faster), fail independently, and a slow judge tier can't block the
   model-behaviour signal.
2. Rendering differs per engine; an HTTP call doesn't. Repeating API tests per browser costs
   minutes and finds nothing.
3. The Playwright trace from the job's artifact: `playwright show-trace trace.zip` replays the run
   with DOM snapshots, network and console.
</details>
