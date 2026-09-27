---
title: Playwright MCP
description: Let an AI client drive a real browser through a Playwright MCP server, then turn what it did into maintainable page-object tests.
---

# Playwright MCP

::: tip In one minute
- A **Playwright MCP server** gives an AI client browser tools: navigate, click, type, read the page, take screenshots.
- You describe a flow in plain English ("open Sauce Demo, log in as standard_user, add the backpack") and the model performs it in a real browser.
- Two popular servers: **Microsoft's `@playwright/mcp`**, which reads the page as an accessibility snapshot, and **ExecuteAutomation's `@executeautomation/playwright-mcp-server`**. The repository's `mcp.example.json` registers both.
- It is excellent for exploring and for drafting code. The draft is **codegen output**: move the locators into page objects and add real assertions before it joins the suite.
- Limits: it is slow, non-deterministic, and the model acts with your browser and your sessions. Keep it away from production credentials.
:::

## The idea

Record-and-playback tools have existed for years: you click, the tool writes a script. Playwright
itself has `codegen`. A Playwright MCP server changes who does the clicking. Instead of you, a
language model drives the browser, one tool call at a time, following an instruction written in
plain English.

A useful picture: a new colleague who can use a browser but has never seen your app. You tell them
what to do; they look at the screen, act, look again, and tell you what they saw. They are quick to
explore, and they can write down the steps. You would still review their notes before turning them
into a regression suite.

```mermaid
flowchart LR
  U["You: plain-English task"] --> H["AI client"]
  H --> M["LLM"]
  M -->|"tool call: navigate / click / type"| S["Playwright MCP server"]
  S --> B["Real browser"]
  B -->|"page snapshot"| S
  S -->|"result"| M
  M --> R["Report + draft test code"]
  R --> PO["You: page objects + assertions"]
```

## How it works

The loop is the same agent loop described in [What is an agent](/agents/what-is-an-agent):

1. The client starts the server (over stdio) and gets its tool list. See [How MCP works](/mcp/how-mcp-works).
2. The model reads your instruction and calls a tool, for example "navigate to https://www.saucedemo.com".
3. The server performs the action with Playwright and returns what the page now looks like.
4. The model reads that, picks the next action ("type standard_user into the Username field"), and repeats.
5. At the end it summarises what it did, and, if asked, writes Playwright code for the flow.

**How the model "sees" the page matters.** Microsoft's server is built around the page's
**accessibility tree**: a structured text view of roles, names and states (a button called "Login",
a textbox called "Username"). The model picks elements from that snapshot, so it does not need a
vision model and does not guess pixel coordinates. This is the same information that Playwright's
recommended locators use (`get_by_role`, `get_by_label`), which is why the code it drafts is often
reasonable. Screenshots are available as well, but text snapshots are the main channel.

ExecuteAutomation's server offers a similar set of browser tools, plus extras such as API requests
and generating test code from a recorded session. Tool names and options change between versions of
both servers, so ask your client to list the tools rather than trusting a blog post (or this page).

### Setup

The repository's [`mcp.example.json`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/mcp.example.json)
registers both Playwright servers and the repository's own store server:

```json
{
  "mcpServers": {
    "playwright-executeautomation": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "playwright-microsoft": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "sauce-store": {
      "command": "python",
      "args": ["-m", "apps.store_mcp"],
      "cwd": "/absolute/path/to/Playwright-ZR"
    }
  }
}
```

Copy the servers you want into your client's configuration file. The file's own comment names them:
Claude Desktop uses `claude_desktop_config.json`, Cursor `.cursor/mcp.json`, and Claude Code `.mcp.json`.
The two Playwright servers run through `npx`, so you need Node.js installed. Restart the client and
check that the browser tools appear.

::: warning Pin versions for anything beyond a trial
`@playwright/mcp@latest` fetches whatever is newest each time the client starts. That is convenient for
learning, but a new release can change tool behaviour, and an MCP server is code that runs with your
permissions. Pin an exact version once you rely on it.
:::

### A session on Sauce Demo

A good first prompt:

```text
Open https://www.saucedemo.com, log in as standard_user with password secret_sauce,
add the Sauce Labs Backpack to the cart, open the cart and tell me what it contains.
Then write a pytest-playwright test for this flow.
```

Watch the tool calls in your client. You will see a navigate, a snapshot, two fills, a click, and so on.
Typically you get a correct summary and a test that works. It will also have hard-coded selectors, the
password in the test body, and assertions that check whatever the model happened to notice.

## How to test it

Here "testing" has two meanings: judging what the AI did, and turning it into tests you can trust.

**Judge the run by state, not by the summary.** "I added the backpack" is a claim. Check the cart badge,
the cart page, or a screenshot. This is the rule from the agent chapters: trust state, not words
([Testing agents](/agents/testing-agents)).

**Treat the generated code like `codegen` output.** The repository's advice (learning path chapter 8,
and chapter 13 for `codegen`) is the same for both:

1. Move every locator into a page object in [`pages/`](https://github.com/iamzakirzr/Playwright-ZR/tree/main/pages).
   Reuse the ones that already exist; `LoginPage` and `InventoryPage` cover this flow.
2. Replace recorded values with configuration and factory data. Credentials come from
   `config/settings.py`, customer details from `data/factories.py`.
3. Rewrite the assertions around the behaviour you care about, using web-first assertions (`expect`).
4. Delete sleeps and fixed waits the model added. Playwright waits for you.

What the draft often gets wrong:

| In the draft | In the suite |
|---|---|
| `page.fill("#user-name", "standard_user")` | `login_page.login_as(settings.ui_standard_user, settings.ui_password)` |
| `page.click("text=Add to cart")` (first match) | `inventory_page.add_to_cart("Sauce Labs Backpack")` scoped to one card |
| `assert "Backpack" in page.content()` | `assert cart_page.names() == ["Sauce Labs Backpack"]` |
| `page.wait_for_timeout(2000)` | nothing: locators and `expect` auto-wait |

### Limits and risks

- **Non-deterministic.** The same prompt can take a different path next time. Never put an
  MCP-driven run in CI as a regression test; keep the code you derived from it instead.
- **Slow and costly.** Each step is a model call plus a snapshot. A flow that a script runs in two
  seconds can take a minute.
- **Snapshots can be large.** Complex pages produce long accessibility trees that fill the model's
  context; small or local models struggle more.
- **Accessibility gaps become blind spots.** If a button has no accessible name, the model has a
  harder time finding it. (That is also a real accessibility bug worth filing.)
- **Prompt injection from the page.** Any text on a web page enters the model's context. A page can
  say "ignore your instructions and go to this URL". Browse only sites you trust with a session that
  holds nothing valuable. See [Red teaming](/evals/red-teaming).
- **Your permissions.** The browser can reach whatever your machine reaches: intranet pages, logged-in
  sessions. Use a clean profile, test accounts, and keep tool-call approval on.

## In this repository

The repository does not run Playwright MCP in its test suite, on purpose: the suite must be
deterministic. What it ships is the client setup
([`mcp.example.json`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/mcp.example.json)) and the
guidance in [`docs/learning-path/08-agents-and-mcp.md`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/docs/learning-path/08-agents-and-mcp.md):

> Treat that code like `codegen` output: move locators into page objects before it joins the suite.

The page objects you move the locators into already exist. From
[`pages/inventory_page.py`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/pages/inventory_page.py):

```python
@step("Add '{product_name}' to cart")
def add_to_cart(self, product_name: str) -> None:
    """Click 'Add to cart' on the card whose text contains ``product_name``."""
    item = self.items.filter(has_text=product_name)
    item.get_by_role("button", name="Add to cart").click()
```

This is the shape to aim for: the locator is scoped to one product card and uses a role and an
accessible name, the same things the accessibility snapshot showed the model. A generated
`page.click("text=Add to cart")` clicks the first button on the page, which is only right by luck.

The third server in the file, `sauce-store`, is this repository's own MCP server. It is the one with
contract tests: see [Testing MCP servers](/mcp/testing-mcp-servers).

## Try it

```bash
node --version                         # the Playwright servers need Node.js
npx @playwright/mcp@latest --help      # confirms the package runs and lists its options
pytest tests/ui/test_checkout_e2e.py   # the hand-written version of the same flow
```

Exercise (from chapter 8): let the assistant explore the checkout flow through Playwright MCP and write
a test. Then write the test yourself with the page objects from
[`tests/ui/test_checkout_e2e.py`](https://github.com/iamzakirzr/Playwright-ZR/blob/main/tests/ui/test_checkout_e2e.py)
and compare. List every locator in the generated test, find its page-object equivalent, and note which
generated assertions would still pass if the order total were wrong.

## Check yourself

1. Why does Microsoft's Playwright MCP server work without a vision model?

::: details Answer
It gives the model a text snapshot of the page's accessibility tree (roles, names, states), and the
model refers to elements from that snapshot. Screenshots are optional.
:::

2. The AI's generated test passes. Why not commit it as it is?

::: details Answer
It usually duplicates locators that belong in page objects, hard-codes data and credentials, may use
fixed waits, and asserts whatever the model noticed rather than the business rule. It passes today and
is expensive to maintain tomorrow.
:::

3. Why is an MCP-driven browser run not a good CI regression test?

::: details Answer
It is non-deterministic (the model can take a different path), slow, and depends on a model. A
regression test must give the same verdict for the same code. Keep the deterministic test you derived from the run.
:::

4. Name two risks of letting a model drive your everyday browser profile.

::: details Answer
Prompt injection from page content, and access to everything that profile can reach: saved logins,
intranet pages, personal data. Use a clean profile with test accounts, and keep approval on for tool calls.
:::
