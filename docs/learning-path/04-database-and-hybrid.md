# 04 · Database and cross-layer tests

## Why
The UI can say "saved" while the database says otherwise. SQL tests check the data layer directly;
hybrid tests check that what the API returns is what gets stored.

## Read
1. [`db/connection.py`](../../db/connection.py) and [`db/seed.sql`](../../db/seed.sql): schema and fixtures.
2. [`db/repositories/base_repository.py`](../../db/repositories/base_repository.py): the **Repository**
   pattern. Tests call `users.find_by_username()`, never raw SQL.
3. [`tests/sql/test_data_integrity.py`](../../tests/sql/test_data_integrity.py): constraints, cascades, rollback.
4. [`tests/hybrid/test_api_to_db.py`](../../tests/hybrid/test_api_to_db.py): API → DB field-for-field.

## Run
```bash
make test-sql
```

## Isolation trick
Each test runs inside a transaction that the fixture rolls back, so tests never see each other's rows
and need no cleanup code. Swapping SQLite for Postgres means replacing `db/connection.py` only.

## Try it
Add a repository method `orders_for(username)` and a test that deleting a user cascades to their orders.

## Test your knowledge
1. Why are SQL parameters passed as `?` placeholders instead of f-strings?
2. What makes a hybrid test more valuable than separate API and SQL tests?

<details><summary>Answers</summary>

1. To prevent SQL injection and quoting bugs; the driver escapes values.
2. It checks the *mapping* between layers, the place where field renames and type conversions break.
</details>
