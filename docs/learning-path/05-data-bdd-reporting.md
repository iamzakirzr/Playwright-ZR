# 05 · Test data, BDD and reporting

## Why
Hard-coded data hides bugs and collides in parallel runs; business readers can't review Python;
and a failing run in CI is useless without evidence. Three tools fix those three problems.

## Read
- **Factories**: [`data/factories.py`](../../data/factories.py). `BookingFactory.build(totalprice=0)`
  gives realistic random data with one field pinned. The seed is printed in the pytest header;
  `FAKER_SEED=<n> pytest ...` replays the exact data of a failed run.
- **BDD**: [`tests/bdd/features/`](../../tests/bdd/features) (Gherkin) and
  [`tests/bdd/test_ui_features.py`](../../tests/bdd/test_ui_features.py) (steps). Steps call the
  same page objects as the plain tests; BDD is a layer on top, not a second framework.
- **Allure**: [`reporting/allure_helpers.py`](../../reporting/allure_helpers.py). `@step` on
  page-object methods turns them into report steps; `attach_llm_exchange` saves prompts and answers.
  All helpers become no-ops if Allure isn't installed.

## Run
```bash
make bdd
make report-open        # needs Node.js for npx
```

## Try it
1. Add a scenario outline to `login.feature` for `problem_user`, reusing existing steps.
2. Run a test twice with the same `FAKER_SEED` and confirm the generated names match.

## Test your knowledge
1. Why is the step regex `I log in as "(?P<username>[^"]*)"$` anchored with `$`?
2. When is BDD *not* worth it?

<details><summary>Answers</summary>

1. Without the anchor, a shorter step can swallow a longer one ("I log in as X" matching
   "I log in as X with password Y").
2. When no non-developer reads or writes the scenarios; then it's only indirection.
</details>
