# 01 · Setup and your first test

## Why
A framework is only useful if a new team member can run it in five minutes. Everything here
installs with one command and runs with one word.

## Read
- [`Makefile`](../../Makefile): every suite as a named target. `make help` lists them.
- [`pytest.ini`](../../pytest.ini): markers, default options, where reports go.
- [`conftest.py`](../../conftest.py): session fixtures shared by every layer, plus the
  hook that tags tests with markers based on their folder (`tests/api/...` gets `api`).
- [`config/settings.py`](../../config/settings.py) and [`.env.example`](../../.env.example).

## Run
```bash
python -m venv .venv && source .venv/bin/activate
make setup          # deps, Chromium, pre-commit hook
make smoke          # the critical path across UI, API and SQL
pytest tests/ui/test_login.py --headed --slowmo 500   # watch it
```

## How a test finds its markers
You never write `@pytest.mark.api` by hand. The `pytest_collection_modifyitems` hook in the root
`conftest.py` adds a marker per folder, and adds `live` / `judge` when a test asks for an
Ollama-backed fixture. So `pytest -m "not live"` always means "runs without a model server".

## Try it
1. Run `pytest --collect-only -q -m api` and count the tests.
2. Set `UI_BASE_URL=https://example.com` and run `make smoke`. Which tests fail, and which don't?

## Test your knowledge
1. Where would you change the Sauce Demo password for every test at once?
2. What does `--tracing retain-on-failure` in `pytest.ini` give you, and where does it go?
3. Why is the folder → marker mapping better than hand-written markers?

<details><summary>Answers</summary>

1. The `UI_PASSWORD` environment variable (or `.env`); the default is in `config/settings.py`.
2. A Playwright trace zip per failed test in `test-results/`. Open it with `playwright show-trace <zip>`.
3. It can't be forgotten: moving a file to `tests/api/` is enough to select it with `-m api`.
</details>
