# 02 · Page Object Model

## Why
When a selector changes, you want to edit one line, not forty tests. A page object owns a page's
locators and actions; tests only call methods that read like the user's intent.

## Read
1. [`pages/base_page.py`](../../pages/base_page.py): what every page shares (`open`, `by_test_id`,
   `expect_loaded`, and `healable` for chapter 11).
2. [`pages/login_page.py`](../../pages/login_page.py): locators in `__init__`, one method per action.
3. [`pages/components/header.py`](../../pages/components/header.py): a **component** object,
   because the header appears on many pages. Composition, not inheritance.
4. [`tests/ui/test_login.py`](../../tests/ui/test_login.py) and
   [`tests/ui/test_checkout_e2e.py`](../../tests/ui/test_checkout_e2e.py).

## The OOP ideas in play
| Idea | Where |
|---|---|
| Inheritance: shared behaviour | every page extends `BasePage` |
| Composition: reusable parts | `InventoryPage.header` is a `Header` |
| Encapsulation: hide locators | tests use `login_as()`, never `#user-name` |
| Fluent interface: chainable calls | `login_page.open().expect_loaded()` returns `self` |

## Run
```bash
make test-ui                       # Chromium
BROWSER=firefox make test-ui       # same tests, another engine
```

## Try it
Add a `remove(product_name)` method to `CartPage` (copy the filter-by-text-then-role idea from
`InventoryPage.add_to_cart`, with the button named "Remove") and a test that adds two
products, removes one, and checks both the cart list and `header.cart_count()`.

## Test your knowledge
1. Why do page methods like `open()` return `self`?
2. Should a page object contain `assert` statements?
3. Why prefer `get_by_test_id` over CSS classes?

<details><summary>Answers</summary>

1. So calls chain (`open().expect_loaded()`), keeping tests short and readable.
2. Waits and "page is ready" checks (`expect_loaded`) are fine; business assertions belong in the
   test, so a page object can be reused for positive and negative cases.
3. `data-test` attributes exist for testing and survive restyling; CSS classes change with design.
</details>
