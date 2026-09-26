# 13 · Playwright essentials

## Why
Real apps have pop-ups, iframes, uploads, flaky backends and logins you don't want to repeat in
every test. Playwright has one clean API for each, and this chapter practises all of them on a
deterministic local app, so every test is fast and never flaky.

## The playground
[`apps/playground`](../../apps/playground) is a small site served **inside Playwright** by
[`pages/support/static_site.py`](../../pages/support/static_site.py) (`StaticSite`):
`context.route` answers every request for `https://playground.local` from local files and
Python functions. No server, no network, and every request is recorded for assertions.

Why `https://`? Geolocation and downloads require a *secure context*. A test failed with
`denied` until the origin changed from `http://`, which is a good lesson in itself.

## Read, technique by technique
| Technique | Page object method | Test |
|---|---|---|
| Mock an API (data / empty / 500) | `ProductsPage` | [`test_network.py`](../../tests/ui/essentials/test_network.py) |
| Modify a real response | `route.fetch()` then `route.fulfill(json=...)` | same |
| Block requests (images) | `page.route("**/*.png", lambda r: r.abort())` | same |
| Wait for a response | `page.expect_response(...)` | same |
| alert / confirm / prompt | `DialogsPage.click_and_answer` | [`test_dialogs_frames_tabs.py`](../../tests/ui/essentials/test_dialogs_frames_tabs.py) |
| iframe | `FramesPage.pay` (`frame_locator`) | same |
| New tab | `TabsPage.open_terms` (`context.expect_page`) | same |
| Upload (disk and in-memory) | `FilesPage.upload` | [`test_files_and_auth.py`](../../tests/ui/essentials/test_files_and_auth.py) |
| Download | `FilesPage.download_orders` (`expect_download`) | same |
| Log in once (`storage_state`) | `PlaygroundLoginPage.sign_in` | same, and for real in [`test_checkout_e2e.py`](../../tests/ui/test_checkout_e2e.py) |
| Locale, timezone, dark mode, geolocation, offline | `browser.new_context(...)` options | [`test_emulation_and_input.py`](../../tests/ui/essentials/test_emulation_and_input.py) |
| Hover, drag and drop, keyboard | `InteractionsPage` | same |

## Engine differences found while building this
- An intercepted download started by `<a download>` is **cancelled in Chromium**, and in WebKit a
  downloaded intercepted response **never starts**. The playground's export builds a Blob
  client-side (as many real "Export CSV" buttons do), which works in every engine.
- `route.fetch()` goes to the **real network** and skips other routes, so the "modify a real
  response" test targets a real local server (`real_products_api` fixture).
- `request.all_headers()` **hangs inside a route handler** (it waits for data that only comes
  after the route is released), so `StaticSite` rebuilds the cookie header from `context.cookies()`.

## Recording a test (codegen)
```bash
playwright codegen --target python-pytest https://www.saucedemo.com
```
Click through the flow; Playwright writes pytest code with locators. Treat it as a draft:
move the locators into a page object, and replace the recorded values with factory data.

## Debugging a failure
Every failing test keeps a screenshot, a video and a trace in `test-results/`:
```bash
playwright show-trace test-results/<test-folder>/trace.zip
PWDEBUG=1 pytest tests/ui/essentials/test_network.py -k modify   # step through with the inspector
```

## Run
```bash
pytest tests/ui/essentials                     # Chromium
pytest tests/ui/essentials --browser webkit    # the same tests, Safari's engine
```

## Try it
Add a "session expired" case: make `/api/me` return 401 after sign-in (`site.json("GET", "/api/me", {...}, status=401)`)
and assert the account page asks the user to sign in again.

## Test your knowledge
1. Why install routes on the **context** rather than the page?
2. What does `storage_state` save, and why does it make a suite faster *and* more focused?
3. You mock `/api/products` with `context.route` in a fixture. How can one test override it?

<details><summary>Answers</summary>

1. Pop-ups and new tabs are new pages; context routes serve them too.
2. Cookies and localStorage per origin. Tests skip the login form (seconds each), and a
   broken login page fails only the login tests, not everything behind it.
3. Add a `page.route` for the same URL: page-level handlers run before context-level ones.
</details>
