# One-word commands for every suite. `make help` lists them.
# Each target is a plain pytest call, so you can copy it and add your own flags.

PY      ?= python
PYTEST  ?= $(PY) -m pytest
BROWSER ?= chromium
MARK_OFFLINE = not live and not judge and not strong_judge

.DEFAULT_GOAL := help
.PHONY: help setup models lint format test test-functional test-unit test-ui test-api test-sql bdd \
        test-visual test-mobile-web test-mobile-native test-ai-offline test-ai-live test-ai-judged \
        test-ai-strong smoke report report-open docker-build docker-up docker-down site site-build clean

help: ## Show this list
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- setup ----------
setup: ## Install Python deps, Chromium, and the git pre-commit hook
	$(PY) -m pip install torch --index-url https://download.pytorch.org/whl/cpu
	$(PY) -m pip install -r requirements-dev.txt
	$(PY) -m playwright install --with-deps chromium
	pre-commit install

models: ## Pull the Ollama models used by the live AI tests
	ollama pull qwen2.5:1.5b
	ollama pull llama3.2:3b

# ---------- code quality ----------
lint: ## Lint and check formatting (what CI runs)
	ruff check .
	ruff format --check .

format: ## Auto-fix lint issues and reformat
	ruff check . --fix
	ruff format .

# ---------- functional ----------
test: test-functional test-ai-offline ## Everything that needs no LLM server

test-functional: ## UI + API + SQL + hybrid + BDD (no AI)
	$(PYTEST) -m "(unit or ui or api or sql or hybrid or bdd) and not ai and not live" --browser $(BROWSER) -n auto

test-ui: ## Browser tests only (BROWSER=firefox make test-ui)
	$(PYTEST) -m "ui" --browser $(BROWSER)

test-api: ## Restful Booker API tests
	$(PYTEST) -m "api"

test-unit: ## Framework self-tests (seconds, no browser/network/model)
	$(PYTEST) -m "unit"

test-sql: ## SQLite repository tests
	$(PYTEST) -m "sql or hybrid"

bdd: ## Gherkin scenarios (tests/bdd/features)
	$(PYTEST) -m "bdd and not live" --browser $(BROWSER)

test-visual: ## Screenshot baselines (UPDATE_SNAPSHOTS=1 to accept changes)
	$(PYTEST) -m "visual and not live" --browser $(BROWSER)

smoke: ## Fast critical path
	$(PYTEST) -m "smoke"

# ---------- mobile ----------
test-mobile-web: ## Phones emulated by Playwright (BROWSER=webkit for Safari's engine)
	$(PYTEST) -m "mobile_web" --browser $(BROWSER)

test-mobile-native: ## Chrome on Android via Appium (needs `appium` + an emulator)
	$(PYTEST) -m "mobile_native"

# ---------- AI ----------
test-ai-offline: ## Deterministic AI tests: embeddings, classifiers, stubs (no Ollama)
	$(PYTEST) -m "ai and $(MARK_OFFLINE)"

test-ai-live: ## Real model behaviour, no judge (needs `ollama serve` + `make models`)
	$(PYTEST) -m "live and not judge"

test-ai-judged: ## LLM-as-judge metrics with the 3B judge (slow on CPU)
	$(PYTEST) -m "judge and not strong_judge"

test-ai-strong: ## Metrics that need the 7B judge (ollama pull qwen2.5:7b)
	$(PYTEST) -m "strong_judge"

# ---------- reporting ----------
report: ## Build the Allure HTML report from reports/allure-results
	npx -y allure-commandline generate reports/allure-results -o reports/allure-report --clean

report-open: report ## Build and open the Allure report
	npx -y allure-commandline open reports/allure-report

# ---------- learning site ----------
site: ## Live preview of the learning site (site/) on http://localhost:5173
	cd site && npm ci && npm run dev

site-build: ## Build the learning site into site/.vitepress/dist
	cd site && npm ci && npm run build

# ---------- docker ----------
docker-build: ## Build the test image
	docker compose build tests

docker-up: ## Start Ollama, pull models, run the offline + live suites in containers
	docker compose up --abort-on-container-exit --exit-code-from tests

docker-down: ## Stop containers and drop the model volume
	docker compose down -v

clean: ## Remove test output
	rm -rf reports test-results .pytest_cache
