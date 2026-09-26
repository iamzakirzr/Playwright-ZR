# 03 · API testing with service objects

## Why
The Page Object idea applies to APIs too: a **service object** (client) per API hides URLs,
headers and auth; **schemas** turn JSON into typed objects so a changed contract fails loudly.

## Read
1. [`api/base_client.py`](../../api/base_client.py): one wrapper over Playwright's `APIRequestContext`.
2. [`api/auth_client.py`](../../api/auth_client.py) and [`api/booking_client.py`](../../api/booking_client.py).
3. [`api/schemas/booking.py`](../../api/schemas/booking.py): pydantic models = contract tests for free.
4. [`tests/api/test_booking_crud.py`](../../tests/api/test_booking_crud.py): create → read → update → delete,
   with cleanup in `finally`.

## Run
```bash
make test-api
```

## Patterns worth copying
- **Contract validation**: `Booking.model_validate(response.json())` fails on a missing or
  mistyped field, with a message naming it.
- **Auth as a fixture**: `authed_booking_client` logs in once; tests just use it.
- **Always clean up**: every created booking is deleted in `finally`, so reruns stay independent.

## Try it
Add a test that `PATCH`es only `firstname` and asserts every other field is unchanged.

## Test your knowledge
1. Why do API tests use Playwright's `request` fixture rather than `requests`?
2. What does a pydantic schema catch that `assert response.status == 200` does not?

<details><summary>Answers</summary>

1. One tool for UI and API: shared config, tracing, and the same fixtures; you can also reuse the
   browser's cookies for hybrid UI+API tests.
2. Contract drift: a renamed, missing or wrongly typed field while the status is still 200.
</details>
