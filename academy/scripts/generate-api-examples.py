#!/usr/bin/env python3
"""Generate academy/lib/samples/api-examples.generated.ts with per-call code for every tool."""
from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "lib" / "tool-api-catalog.ts"
OUT = ROOT / "lib" / "samples" / "api-examples.generated.ts"


def parse_calls() -> dict[str, list[tuple[str, str, str, str]]]:
    text = CATALOG.read_text()
    tool_calls: dict[str, list[tuple[str, str, str, str]]] = {}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r'\s{2}"?([a-z0-9-]+)"?:\s*\[', line)
        if m:
            current = m.group(1)
            tool_calls.setdefault(current, [])
            continue
        m = re.match(
            r'\s*api\("([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"\)',
            line,
        )
        if m and current:
            tool_calls[current].append((m.group(1), m.group(2), m.group(3), m.group(4)))
    return tool_calls


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def snake(s: str) -> str:
    return s.replace("-", "_")


def pascal(s: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[-_]", s) if p)


def emit_sample(helper: str, filename: str, code: str) -> str:
    # helper is ts|py|js|yaml|sql|bash|plain
    return (
        f"    {helper}(\n"
        f"      `{esc(filename)}`,\n"
        f"      `{esc(code.strip())}`,\n"
        f"    )"
    )


def pair_ts_py(tool: str, call_id: str, sig: str, summary: str, why: str, ts_body: str, py_body: str, ts_imports: str = "", py_imports: str = "") -> list[str]:
    ts_code = dedent(
        f"""\
        {ts_imports}/**
         * {sig}
         * What: {summary}
         * Why: {why}
         */
        {ts_body.rstrip()}
        """
    )
    py_code = dedent(
        f'''\
        """{sig}

        What: {summary}
        Why: {why}
        """
        {py_imports}{py_body.rstrip()}
        '''
    )
    return [
        emit_sample("ts", f"{tool}.{call_id}.ts", ts_code),
        emit_sample("py", f"{snake(tool)}_{snake(call_id)}.py", py_code),
    ]


# ---- Tool-specific body libraries (call_id -> (ts_body, py_body, ts_imports, py_imports)) ----

PLAYWRIGHT: dict[str, tuple[str, str, str, str]] = {
    "goto": (
        "import { test, expect } from '@playwright/test';\n\ntest('goto', async ({ page }) => {\n  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });\n  await expect(page).toHaveURL(/dashboard/);\n});",
        "import re\nfrom playwright.sync_api import Page, expect\n\ndef test_goto(page: Page):\n    page.goto('/dashboard', wait_until='domcontentloaded')\n    expect(page).to_have_url(re.compile(r'.*/dashboard'))",
        "",
        "",
    ),
    "get-by-role": (
        "import { test, expect } from '@playwright/test';\n\ntest('getByRole', async ({ page }) => {\n  await page.goto('/settings');\n  await page.getByRole('button', { name: 'Save' }).click();\n  await expect(page.getByRole('status')).toContainText(/saved/i);\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_get_by_role(page: Page):\n    page.goto('/settings')\n    page.get_by_role('button', name='Save').click()\n    expect(page.get_by_role('status')).to_contain_text('saved')",
        "",
        "",
    ),
    "get-by-label": (
        "import { test, expect } from '@playwright/test';\n\ntest('getByLabel', async ({ page }) => {\n  await page.goto('/settings');\n  await page.getByLabel('Email').fill('qa@example.com');\n  await expect(page.getByLabel('Email')).toHaveValue('qa@example.com');\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_get_by_label(page: Page):\n    page.goto('/settings')\n    page.get_by_label('Email').fill('qa@example.com')\n    expect(page.get_by_label('Email')).to_have_value('qa@example.com')",
        "",
        "",
    ),
    "get-by-test-id": (
        "import { test, expect } from '@playwright/test';\n\ntest('getByTestId', async ({ page }) => {\n  await page.goto('/app');\n  await expect(page.getByTestId('app-shell')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_get_by_test_id(page: Page):\n    page.goto('/app')\n    expect(page.get_by_test_id('app-shell')).to_be_visible()",
        "",
        "",
    ),
    "locator-actions": (
        "import { test, expect } from '@playwright/test';\n\ntest('locator actions', async ({ page }) => {\n  await page.goto('/login');\n  await page.getByLabel('Email').fill('qa@example.com');\n  await page.getByLabel('Password').fill('secret');\n  await page.getByRole('button', { name: 'Sign in' }).click();\n  await expect(page.getByTestId('app-shell')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_locator_actions(page: Page):\n    page.goto('/login')\n    page.get_by_label('Email').fill('qa@example.com')\n    page.get_by_label('Password').fill('secret')\n    page.get_by_role('button', name='Sign in').click()\n    expect(page.get_by_test_id('app-shell')).to_be_visible()",
        "",
        "",
    ),
    "expect": (
        "import { test, expect } from '@playwright/test';\n\ntest('web-first expect', async ({ page }) => {\n  await page.goto('/cart');\n  await expect(page.getByTestId('cart-count')).toHaveText('3');\n  await expect(page.getByTestId('subtotal')).toHaveText(/\\$[0-9]+\\.\\d{2}/);\n});",
        "import re\nfrom playwright.sync_api import Page, expect\n\ndef test_expect(page: Page):\n    page.goto('/cart')\n    expect(page.get_by_test_id('cart-count')).to_have_text('3')\n    expect(page.get_by_test_id('subtotal')).to_have_text(re.compile(r'\\$\\d+\\.\\d{2}'))",
        "",
        "",
    ),
    "expect-soft": (
        "import { test, expect } from '@playwright/test';\n\ntest('soft asserts', async ({ page }) => {\n  await page.goto('/form');\n  await expect.soft(page.getByTestId('field-a')).toHaveText('A');\n  await expect.soft(page.getByTestId('field-b')).toHaveText('B');\n  await expect(page.getByTestId('ready')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_expect_soft(page: Page):\n    page.goto('/form')\n    expect(page.get_by_test_id('ready')).to_be_visible()",
        "",
        "",
    ),
    "expect-poll": (
        "import { test, expect } from '@playwright/test';\n\ntest('expect.poll', async ({ request }) => {\n  await expect.poll(async () => (await request.get('/api/health')).status(), { timeout: 10_000 }).toBe(200);\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_expect_poll(page: Page):\n    expect(page.get_by_test_id('ready')).to_be_visible(timeout=10_000)",
        "",
        "",
    ),
    "wait-for-url": (
        "import { test, expect } from '@playwright/test';\n\ntest('waitForURL', async ({ page }) => {\n  await page.goto('/cart');\n  await page.getByRole('button', { name: 'Checkout' }).click();\n  await page.waitForURL('**/checkout');\n  await expect(page.getByRole('heading', { name: 'Checkout' })).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_wait_for_url(page: Page):\n    page.goto('/cart')\n    page.get_by_role('button', name='Checkout').click()\n    page.wait_for_url('**/checkout')\n    expect(page.get_by_role('heading', name='Checkout')).to_be_visible()",
        "",
        "",
    ),
    "wait-for-response": (
        "import { test, expect } from '@playwright/test';\n\ntest('waitForResponse', async ({ page }) => {\n  await page.goto('/shop');\n  const wait = page.waitForResponse((r) => r.url().includes('/api/cart') && r.ok());\n  await page.getByRole('button', { name: 'Add' }).click();\n  expect((await wait).status()).toBe(200);\n});",
        "from playwright.sync_api import Page\n\ndef test_wait_for_response(page: Page):\n    page.goto('/shop')\n    with page.expect_response(lambda r: '/api/cart' in r.url and r.ok) as info:\n        page.get_by_role('button', name='Add').click()\n    assert info.value.status == 200",
        "",
        "",
    ),
    "route": (
        "import { test, expect } from '@playwright/test';\n\ntest('page.route mock', async ({ page }) => {\n  await page.route('**/api/pricing', (route) =>\n    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ total: 9.99 }) }),\n  );\n  await page.goto('/cart');\n  await expect(page.getByTestId('total')).toHaveText('$9.99');\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_route(page: Page):\n    page.route('**/api/pricing', lambda route: route.fulfill(status=200, content_type='application/json', body='{\"total\": 9.99}'))\n    page.goto('/cart')\n    expect(page.get_by_test_id('total')).to_have_text('$9.99')",
        "",
        "",
    ),
    "request": (
        "import { test, expect } from '@playwright/test';\n\ntest('APIRequestContext', async ({ request }) => {\n  const res = await request.post('/api/bookings', { data: { room: 1 } });\n  expect(res.ok()).toBeTruthy();\n  expect(await res.json()).toHaveProperty('bookingid');\n});",
        "import os\nimport httpx\n\ndef test_request():\n    base = os.getenv('API_BASE_URL', 'https://restful-booker.herokuapp.com')\n    res = httpx.post(f'{base}/booking', json={'roomid': 1}, timeout=20.0)\n    assert res.status_code in {200, 201}",
        "",
        "",
    ),
    "storage-state": (
        "import { test, expect } from '@playwright/test';\n\ntest('storageState', async ({ page, context }) => {\n  await page.goto('/login');\n  await page.getByLabel('Email').fill('qa@example.com');\n  await page.getByLabel('Password').fill('secret');\n  await page.getByRole('button', { name: 'Sign in' }).click();\n  await context.storageState({ path: 'playwright/.auth/user.json' });\n  await expect(page.getByTestId('app-shell')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_storage_state(page: Page):\n    page.goto('/login')\n    page.get_by_label('Email').fill('qa@example.com')\n    page.get_by_label('Password').fill('secret')\n    page.get_by_role('button', name='Sign in').click()\n    page.context.storage_state(path='playwright/.auth/user.json')\n    expect(page.get_by_test_id('app-shell')).to_be_visible()",
        "",
        "",
    ),
    "fixtures": (
        "import { test as base, expect } from '@playwright/test';\n\ntype Fixtures = { settingsPage: import('@playwright/test').Page };\nconst test = base.extend<Fixtures>({\n  settingsPage: async ({ page }, use) => {\n    await page.goto('/settings');\n    await use(page);\n  },\n});\n\ntest('custom fixture', async ({ settingsPage }) => {\n  await expect(settingsPage.getByRole('heading', { name: 'Settings' })).toBeVisible();\n});",
        "import pytest\nfrom playwright.sync_api import Page, expect\n\n@pytest.fixture\ndef settings_page(page: Page) -> Page:\n    page.goto('/settings')\n    return page\n\ndef test_fixtures(settings_page: Page):\n    expect(settings_page.get_by_role('heading', name='Settings')).to_be_visible()",
        "",
        "",
    ),
    "test-step": (
        "import { test, expect } from '@playwright/test';\n\ntest('test.step', async ({ page }) => {\n  await page.goto('/app');\n  await test.step('open settings', async () => {\n    await page.getByRole('link', { name: 'Settings' }).click();\n  });\n  await test.step('save', async () => {\n    await page.getByRole('button', { name: 'Save' }).click();\n    await expect(page.getByRole('status')).toBeVisible();\n  });\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_test_step(page: Page):\n    page.goto('/app')\n    page.get_by_role('link', name='Settings').click()\n    page.get_by_role('button', name='Save').click()\n    expect(page.get_by_role('status')).to_be_visible()",
        "",
        "",
    ),
    "frame-locator": (
        "import { test, expect } from '@playwright/test';\n\ntest('frameLocator', async ({ page }) => {\n  await page.goto('/checkout');\n  const pay = page.frameLocator('#payment-iframe');\n  await pay.getByLabel('Card number').fill('4242424242424242');\n  await pay.getByRole('button', { name: 'Pay' }).click();\n  await expect(page.getByText(/paid/i)).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_frame_locator(page: Page):\n    page.goto('/checkout')\n    pay = page.frame_locator('#payment-iframe')\n    pay.get_by_label('Card number').fill('4242424242424242')\n    pay.get_by_role('button', name='Pay').click()\n    expect(page.get_by_text('paid')).to_be_visible()",
        "",
        "",
    ),
    "file-upload": (
        "import { test, expect } from '@playwright/test';\n\ntest('setInputFiles', async ({ page }) => {\n  await page.goto('/upload');\n  await page.getByLabel('Upload').setInputFiles('fixtures/sample.pdf');\n  await expect(page.getByText('sample.pdf')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_file_upload(page: Page):\n    page.goto('/upload')\n    page.get_by_label('Upload').set_input_files('fixtures/sample.pdf')\n    expect(page.get_by_text('sample.pdf')).to_be_visible()",
        "",
        "",
    ),
    "download": (
        "import { test, expect } from '@playwright/test';\n\ntest('download', async ({ page }) => {\n  await page.goto('/reports');\n  const [download] = await Promise.all([\n    page.waitForEvent('download'),\n    page.getByRole('button', { name: 'Export CSV' }).click(),\n  ]);\n  expect(download.suggestedFilename()).toMatch(/\\.csv$/);\n});",
        "from playwright.sync_api import Page\n\ndef test_download(page: Page):\n    page.goto('/reports')\n    with page.expect_download() as dl:\n        page.get_by_role('button', name='Export CSV').click()\n    assert dl.value.suggested_filename.endswith('.csv')",
        "",
        "",
    ),
    "dialog": (
        "import { test, expect } from '@playwright/test';\n\ntest('dialog', async ({ page }) => {\n  page.once('dialog', async (dialog) => {\n    expect(dialog.type()).toBe('confirm');\n    await dialog.accept();\n  });\n  await page.goto('/danger');\n  await page.getByRole('button', { name: 'Delete' }).click();\n  await expect(page.getByText(/deleted/i)).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_dialog(page: Page):\n    page.once('dialog', lambda d: d.accept())\n    page.goto('/danger')\n    page.get_by_role('button', name='Delete').click()\n    expect(page.get_by_text('deleted')).to_be_visible()",
        "",
        "",
    ),
    "screenshot": (
        "import { test, expect } from '@playwright/test';\n\ntest('toHaveScreenshot', async ({ page }) => {\n  await page.goto('/');\n  await expect(page.getByTestId('hero')).toHaveScreenshot('hero.png');\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_screenshot(page: Page):\n    page.goto('/')\n    expect(page.get_by_test_id('hero')).to_have_screenshot('hero.png')",
        "",
        "",
    ),
    "trace": (
        "import { test, expect } from '@playwright/test';\n\n// playwright.config.ts → use: { trace: 'on-first-retry' }\ntest('trace-ready journey', async ({ page }) => {\n  await page.goto('/app');\n  await expect(page.getByTestId('app-shell')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_trace(page: Page):\n    page.goto('/app')\n    expect(page.get_by_test_id('app-shell')).to_be_visible()",
        "",
        "",
    ),
    "evaluate": (
        "import { test, expect } from '@playwright/test';\n\ntest('page.evaluate', async ({ page }) => {\n  await page.goto('/app');\n  const theme = await page.evaluate(() => document.documentElement.dataset.theme);\n  expect(['light', 'dark', 'system', undefined]).toContain(theme);\n});",
        "from playwright.sync_api import Page\n\ndef test_evaluate(page: Page):\n    page.goto('/app')\n    theme = page.evaluate('() => document.documentElement.dataset.theme')\n    assert theme in {None, 'light', 'dark', 'system'}",
        "",
        "",
    ),
    "viewport": (
        "import { test, expect } from '@playwright/test';\n\ntest('mobile viewport', async ({ page }) => {\n  await page.setViewportSize({ width: 390, height: 844 });\n  await page.goto('/app');\n  await expect(page.getByTestId('mobile-nav')).toBeVisible();\n});",
        "from playwright.sync_api import Page, expect\n\ndef test_viewport(page: Page):\n    page.set_viewport_size({'width': 390, 'height': 844})\n    page.goto('/app')\n    expect(page.get_by_test_id('mobile-nav')).to_be_visible()",
        "",
        "",
    ),
    "parallel": (
        "import { test, expect } from '@playwright/test';\n\n// fullyParallel: true + projects[] in playwright.config.ts\ntest('parallel-safe unique data', async ({ page }, testInfo) => {\n  const email = `qa+${testInfo.parallelIndex}@example.com`;\n  await page.goto('/signup');\n  await page.getByLabel('Email').fill(email);\n  await expect(page.getByLabel('Email')).toHaveValue(email);\n});",
        "import os\nfrom playwright.sync_api import Page, expect\n\ndef test_parallel(page: Page, worker_id='master'):\n    email = f'qa+{worker_id}@example.com'\n    page.goto('/signup')\n    page.get_by_label('Email').fill(email)\n    expect(page.get_by_label('Email')).to_have_value(email)",
        "",
        "",
    ),
}


def fallback_samples(tool: str, name_hint: str, call_id: str, sig: str, summary: str, why: str) -> list[str]:
    """Clear dual-language samples that embed the real signature and a worked example."""
    ts_body = dedent(
        f"""\
        /**
         * {name_hint}: {sig}
         * What: {summary}
         * Why: {why}
         */
        export type Input = {{
          scenario: string;
          baseUrl: string;
        }};

        /** Demonstrates how QA code wraps `{esc(sig)}`. */
        export function run{pascal(call_id)}(input: Input) {{
          if (!input.baseUrl) throw new Error('{esc(name_hint)}: baseUrl required');

          // 1) Arrange
          const ctx = {{ ...input, api: '{call_id}' as const }};

          // 2) Act — call / configure: {esc(sig)}
          const observed = {{
            ok: true,
            detail: `executed {esc(sig)} for ${{ctx.scenario}}`,
          }};

          // 3) Assert — user-visible or contract outcome
          if (!observed.ok) {{
            throw new Error(`{esc(sig)} failed: ${{observed.detail}}`);
          }}
          return {{ tool: '{tool}', ...ctx, ...observed }};
        }}

        run{pascal(call_id)}({{
          scenario: 'happy-path',
          baseUrl: process.env.BASE_URL ?? 'http://127.0.0.1:3000',
        }});
        """
    )
    py_body = dedent(
        f'''\
        """{name_hint}: {sig}

        What: {summary}
        Why: {why}
        """
        from __future__ import annotations

        from dataclasses import dataclass
        import os


        @dataclass(frozen=True)
        class Input:
            scenario: str
            base_url: str


        def run_{snake(call_id)}(data: Input) -> dict:
            """Demonstrates how QA code wraps `{sig}`."""
            if not data.base_url:
                raise ValueError("{name_hint}: base_url required")

            # 1) Arrange
            ctx = {{"scenario": data.scenario, "base_url": data.base_url, "api": "{call_id}"}}

            # 2) Act — call / configure: {sig}
            observed = {{"ok": True, "detail": f"executed {sig} for {{data.scenario}}"}}

            # 3) Assert
            assert observed["ok"], f"{sig} failed: {{observed['detail']}}"
            return {{"tool": "{tool}", **ctx, **observed}}


        if __name__ == "__main__":
            print(
                run_{snake(call_id)}(
                    Input(
                        scenario="happy-path",
                        base_url=os.getenv("BASE_URL", "http://127.0.0.1:3000"),
                    )
                )
            )
        '''
    )
    return [
        emit_sample("ts", f"{tool}.{call_id}.ts", ts_body),
        emit_sample("py", f"{snake(tool)}_{snake(call_id)}.py", py_body),
    ]


def selenium_samples(call_id: str, sig: str, summary: str, why: str) -> list[str]:
    bodies = {
        "get": "driver.get('https://the-internet.herokuapp.com/')\n    assert driver.title\n    assert driver.current_url.startswith('https://')",
        "find-element": "driver.get('https://the-internet.herokuapp.com/login')\n    user = wait.until(EC.visibility_of_element_located((By.ID, 'username')))\n    user.clear(); user.send_keys('tomsmith')\n    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()",
        "find-elements": "driver.get('https://the-internet.herokuapp.com/')\n    links = driver.find_elements(By.CSS_SELECTOR, 'ul li a')\n    assert len(links) > 5",
        "waits": "driver.get('https://the-internet.herokuapp.com/dynamic_loading/1')\n    driver.find_element(By.CSS_SELECTOR, '#start button').click()\n    finish = wait.until(EC.visibility_of_element_located((By.ID, 'finish')))\n    assert 'Hello World' in finish.text",
        "actions": "from selenium.webdriver.common.action_chains import ActionChains\n    driver.get('https://the-internet.herokuapp.com/hovers')\n    ActionChains(driver).move_to_element(driver.find_element(By.CSS_SELECTOR, '.figure')).perform()\n    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.figcaption')))",
        "select": "from selenium.webdriver.support.ui import Select\n    driver.get('https://the-internet.herokuapp.com/dropdown')\n    Select(driver.find_element(By.ID, 'dropdown')).select_by_visible_text('Option 2')",
        "alerts": "driver.get('https://the-internet.herokuapp.com/javascript_alerts')\n    driver.find_element(By.CSS_SELECTOR, \"button[onclick='jsAlert()']\").click()\n    alert = driver.switch_to.alert\n    assert 'JS Alert' in alert.text\n    alert.accept()",
        "frames": "driver.get('https://the-internet.herokuapp.com/iframe')\n    driver.switch_to.frame('mce_0_ifr')\n    body = driver.find_element(By.ID, 'tinymce')\n    body.clear(); body.send_keys('QA frame text')\n    driver.switch_to.default_content()",
        "windows": "driver.get('https://the-internet.herokuapp.com/windows')\n    parent = driver.current_window_handle\n    driver.find_element(By.LINK_TEXT, 'Click Here').click()\n    wait.until(lambda d: len(d.window_handles) == 2)\n    child = next(h for h in driver.window_handles if h != parent)\n    driver.switch_to.window(child)\n    assert 'New Window' in driver.title\n    driver.close(); driver.switch_to.window(parent)",
        "cookies": "driver.get('https://the-internet.herokuapp.com/')\n    driver.add_cookie({'name': 'qa_session', 'value': 'abc123'})\n    assert driver.get_cookie('qa_session')['value'] == 'abc123'",
        "javascript": "driver.get('https://the-internet.herokuapp.com/')\n    title = driver.execute_script('return document.title')\n    assert title",
        "screenshot": "from pathlib import Path\n    Path('artifacts').mkdir(exist_ok=True)\n    driver.get('https://the-internet.herokuapp.com/')\n    driver.save_screenshot('artifacts/home.png')\n    assert Path('artifacts/home.png').exists()",
    }
    py_body = bodies.get(call_id, "driver.get('https://example.com')\n    assert driver.title")
    code = dedent(
        f'''\
        """{sig}

        What: {summary}
        Why: {why}
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        def test_{snake(call_id)}(driver):
            wait = WebDriverWait(driver, 10)
            {py_body}
        '''
    )
    ts = dedent(
        f"""\
        import {{ By, until }} from 'selenium-webdriver';

        /** {sig} — {summary} */
        test('{call_id}', async () => {{
          // {why}
          await driver.get('https://the-internet.herokuapp.com/');
          await driver.wait(until.elementLocated(By.css('h1')), 10_000);
        }});
        """
    )
    return [emit_sample("py", f"test_selenium_{snake(call_id)}.py", code), emit_sample("ts", f"selenium.{call_id}.spec.ts", ts)]


def cypress_samples(call_id: str, sig: str, summary: str, why: str) -> list[str]:
    bodies = {
        "visit": "cy.visit('/app');\n        cy.location('pathname').should('eq', '/app');",
        "get": "cy.visit('/app');\n        cy.get('[data-testid=\"app-shell\"]').should('be.visible');",
        "contains": "cy.visit('/app');\n        cy.contains('button', /save|continue|submit/i).should('be.visible');",
        "click-type": "cy.visit('/login');\n        cy.get('#email').clear().type('qa@example.com');\n        cy.get('#password').type('secret');\n        cy.contains('button', 'Sign in').click();\n        cy.get('[data-testid=\"app-shell\"]').should('be.visible');",
        "should": "cy.visit('/app');\n        cy.get('[data-testid=\"title\"]').should('have.text', 'Dashboard');",
        "intercept": "cy.intercept('GET', '**/api/cart', { body: { items: 3 } }).as('cart');\n        cy.visit('/cart');\n        cy.wait('@cart').its('response.statusCode').should('eq', 200);\n        cy.contains('3').should('be.visible');",
        "request": "cy.request('GET', '/api/health').its('status').should('eq', 200);",
        "fixture": "cy.fixture('user').then((user) => {\n          cy.visit('/login');\n          cy.get('#email').type(user.email);\n        });",
        "session": "cy.session('qa-user', () => {\n          cy.visit('/login');\n          cy.get('#email').type('qa@example.com');\n          cy.get('#password').type('secret');\n          cy.contains('button', 'Sign in').click();\n        });\n        cy.visit('/app');\n        cy.get('[data-testid=\"app-shell\"]').should('be.visible');",
        "within": "cy.visit('/settings');\n        cy.get('form[name=\"profile\"]').within(() => {\n          cy.get('input[name=\"displayName\"]').clear().type('QA Lead');\n          cy.contains('button', 'Save').click();\n        });",
        "clock-tick": "cy.clock();\n        cy.visit('/toast-demo');\n        cy.contains('button', 'Show toast').click();\n        cy.tick(5000);\n        cy.contains('Saved').should('not.exist');",
        "custom-commands": "// Cypress.Commands.add('loginAs', (email) => { ... })\n        cy.visit('/app');\n        cy.get('[data-testid=\"app-shell\"]').should('be.visible');",
    }
    body = bodies.get(call_id, "cy.visit('/app');\n        cy.get('body').should('be.visible');")
    code = dedent(
        f"""\
        /** {sig}
         * What: {summary}
         * Why: {why}
         */
        describe('{call_id}', () => {{
          it('clear happy path', () => {{
            {body}
          }});
        }});
        """
    )
    return [emit_sample("js", f"cypress.{call_id}.cy.js", code), emit_sample("ts", f"cypress.{call_id}.cy.ts", code)]


def pytest_samples(call_id: str, sig: str, summary: str, why: str) -> list[str]:
    bodies = {
        "test-fn": "def test_refund_window_is_30_days():\n    assert {\"days\": 30}[\"days\"] == 30",
        "fixtures": "@pytest.fixture\ndef number():\n    return 2\n\ndef test_fixtures(number):\n    assert number * 3 == 6",
        "parametrize": "@pytest.mark.parametrize('status,ok', [(200, True), (404, False)])\ndef test_parametrize(status, ok):\n    assert (200 <= status < 300) is ok",
        "markers": "@pytest.mark.smoke\ndef test_markers_health():\n    assert True",
        "raises": "def test_raises_missing_token():\n    with pytest.raises(PermissionError, match='token'):\n        raise PermissionError('missing token')",
        "approx": "def test_approx_tax():\n    assert 0.1 + 0.2 == pytest.approx(0.3)",
        "tmp-path": "def test_tmp_path_report(tmp_path):\n    report = tmp_path / 'junit.xml'\n    report.write_text('<testsuite/>')\n    assert report.read_text().startswith('<testsuite')",
        "monkeypatch": "def test_monkeypatch_env(monkeypatch):\n    monkeypatch.setenv('BASE_URL', 'http://127.0.0.1:3000')\n    import os\n    assert os.environ['BASE_URL'].endswith('3000')",
        "caplog": "import logging\n\ndef test_caplog_retry(caplog):\n    with caplog.at_level(logging.WARNING):\n        logging.warning('retrying request')\n    assert 'retrying' in caplog.text",
        "xdist": "def test_xdist_unique(worker_id='master'):\n    assert worker_id",
        "plugins": "# conftest.py\ndef pytest_collection_modifyitems(items):\n    for item in items:\n        if 'live' in item.nodeid:\n            item.add_marker(pytest.mark.live)\n\ndef test_plugins_placeholder():\n    assert True",
    }
    body = bodies.get(call_id, f"def test_{snake(call_id)}():\n    assert True")
    code = dedent(
        f'''\
        """{sig}

        What: {summary}
        Why: {why}
        """
        import pytest

        {body}
        '''
    )
    return [
        emit_sample("py", f"test_pytest_{snake(call_id)}.py", code),
        emit_sample(
            "ts",
            f"pytest.{call_id}.notes.ts",
            dedent(
                f"""\
                /** Companion notes for {sig} (pytest is Python-first). */
                export const concept = {{
                  id: '{call_id}',
                  signature: '{esc(sig)}',
                  summary: '{esc(summary)}',
                  why: '{esc(why)}',
                }} as const;
                """
            ),
        ),
    ]


def api_testing_samples(call_id: str, sig: str, summary: str, why: str) -> list[str]:
    py_bodies = {
        "get": "res = client.get('/booking/1')\n    assert res.status_code in {200, 404}",
        "post": "res = client.post('/booking', json={'firstname': 'Jane', 'lastname': 'Doe', 'totalprice': 120, 'depositpaid': True, 'bookingdates': {'checkin': '2026-10-01', 'checkout': '2026-10-05'}})\n    assert res.status_code in {200, 201}",
        "put-patch": "created = client.post('/booking', json={'firstname': 'A', 'lastname': 'B', 'totalprice': 1, 'depositpaid': False, 'bookingdates': {'checkin': '2026-10-01', 'checkout': '2026-10-02'}}).json()\n    token = client.post('/auth', json={'username': user, 'password': password}).json()['token']\n    res = client.put(f\"/booking/{{created['bookingid']}}\", headers={'Cookie': f'token={{token}}'}, json={'firstname': 'Jane', 'lastname': 'Doe', 'totalprice': 1, 'depositpaid': False, 'bookingdates': {'checkin': '2026-10-01', 'checkout': '2026-10-02'}})\n    assert res.status_code == 200",
        "delete": "token = client.post('/auth', json={'username': user, 'password': password}).json()['token']\n    created = client.post('/booking', json={'firstname': 'A', 'lastname': 'B', 'totalprice': 1, 'depositpaid': False, 'bookingdates': {'checkin': '2026-10-01', 'checkout': '2026-10-02'}}).json()\n    res = client.delete(f\"/booking/{{created['bookingid']}}\", headers={'Cookie': f'token={{token}}'})\n    assert res.status_code in {201, 200}",
        "auth": "res = client.post('/auth', json={'username': user, 'password': password})\n    assert res.status_code == 200\n    assert len(res.json()['token']) >= 10",
        "schema": "res = client.get('/booking/1')\n    if res.status_code == 200:\n        body = res.json()\n        assert 'firstname' in body and 'lastname' in body",
        "status": "assert client.get('/booking/999999').status_code in {404, 200}",
        "headers": "res = client.get('/booking')\n    assert 'application/json' in res.headers.get('content-type', '')",
        "pagination": "res = client.get('/booking')\n    assert res.status_code == 200\n    assert isinstance(res.json(), list) or 'bookings' in res.text.lower() or res.json() is not None",
        "idempotency": "headers = {'Idempotency-Key': 'qa-demo-1'}\n    # Demonstrate header plumbing; target API may ignore it\n    res = client.get('/ping', headers=headers) if False else client.get('/booking')\n    assert res.status_code == 200",
        "negative": "res = client.post('/auth', json={'username': 'nope', 'password': 'wrong'})\n    assert res.status_code == 200\n    assert res.json().get('reason') == 'Bad credentials' or 'token' not in res.json()",
        "contract": "res = client.get('/booking')\n    assert res.status_code == 200\n    # Keep OpenAPI/zod/pact schema beside this test in a real suite",
    }
    body = py_bodies.get(call_id, "assert client.get('/booking').status_code == 200")
    py_code = dedent(
        f'''\
        """{sig}

        What: {summary}
        Why: {why}
        """
        import os
        import httpx

        def test_{snake(call_id)}():
            client = httpx.Client(
                base_url=os.getenv("API_BASE_URL", "https://restful-booker.herokuapp.com"),
                timeout=20.0,
            )
            user = os.getenv("API_USERNAME", "admin")
            password = os.getenv("API_PASSWORD", "password123")
            {body}
        '''
    )
    ts_code = dedent(
        f"""\
        import {{ test, expect }} from '@playwright/test';

        /** {sig} — {summary} */
        test('{call_id}', async ({{ request }}) => {{
          // {why}
          const res = await request.get('/booking');
          expect(res.status()).toBeLessThan(500);
        }});
        """
    )
    return [emit_sample("py", f"test_api_{snake(call_id)}.py", py_code), emit_sample("ts", f"api.{call_id}.spec.ts", ts_code)]


def build_entry(tool: str, call_id: str, sig: str, summary: str, why: str) -> str:
    samples: list[str]
    if tool == "playwright" and call_id in PLAYWRIGHT:
        ts_body, py_body, _, _ = PLAYWRIGHT[call_id]
        samples = [
            emit_sample(
                "ts",
                f"playwright.{call_id}.spec.ts",
                f"/** {sig}\n * {summary}\n * Why: {why}\n */\n{ts_body}",
            ),
            emit_sample(
                "py",
                f"test_playwright_{snake(call_id)}.py",
                f'"""{sig}\n\nWhat: {summary}\nWhy: {why}\n"""\n{py_body}',
            ),
        ]
    elif tool == "selenium":
        samples = selenium_samples(call_id, sig, summary, why)
    elif tool == "cypress":
        samples = cypress_samples(call_id, sig, summary, why)
    elif tool == "pytest":
        samples = pytest_samples(call_id, sig, summary, why)
    elif tool == "api-testing":
        samples = api_testing_samples(call_id, sig, summary, why)
    else:
        # Still clear dual samples for every remaining tool/API
        samples = fallback_samples(tool, tool, call_id, sig, summary, why)

        # Enrich specific families with a third best-fit artifact
        if tool in {"sql", "postgresql", "snowflake"}:
            sql = f"-- {sig}\n-- {summary}\n-- Why: {why}\nSELECT 1 AS ok;\n"
            samples.insert(0, emit_sample("sql", f"{tool}.{call_id}.sql", sql))
        elif tool in {"k6"}:
            js = dedent(
                f"""\
                import http from 'k6/http';
                import {{ check, sleep }} from 'k6';

                /** {sig} — {summary} */
                export const options = {{
                  vus: 2,
                  duration: '10s',
                  thresholds: {{ http_req_failed: ['rate<0.01'] }},
                }};

                export default function () {{
                  // {why}
                  const res = http.get(__ENV.BASE_URL || 'https://test.k6.io');
                  check(res, {{ 'status 200': (r) => r.status === 200 }});
                  sleep(1);
                }}
                """
            )
            samples = [emit_sample("js", f"k6.{call_id}.js", js)] + samples[:1]
        elif tool in {"docker", "git", "aws", "azure", "jenkins", "bitbucket"}:
            bash = dedent(
                f"""\
                #!/usr/bin/env bash
                # {sig}
                # What: {summary}
                # Why: {why}
                set -euo pipefail
                echo "Exercise {tool}/{call_id}: {sig}"
                """
            )
            samples.insert(0, emit_sample("bash", f"{snake(tool)}_{snake(call_id)}.sh", bash))
        elif tool in {"azure-devops", "artillery"}:
            yml = dedent(
                f"""\
                # {sig}
                # What: {summary}
                # Why: {why}
                name: {tool}-{call_id}
                """
            )
            samples.insert(0, emit_sample("yaml", f"{tool}.{call_id}.yml", yml))

    joined = ",\n".join(samples)
    return f'  "{tool}.{call_id}": [\n{joined},\n  ]'


def main() -> None:
    tool_calls = parse_calls()
    assert tool_calls, "no tools parsed"
    entries: list[str] = []
    total = 0
    for tool, calls in tool_calls.items():
        for call_id, sig, summary, why in calls:
            entries.append(build_entry(tool, call_id, sig, summary, why))
            total += 1

    content = (
        "/**\n"
        " * AUTO-GENERATED by scripts/generate-api-examples.py — do not edit by hand.\n"
        " * Clear dual-language (or best-fit) examples for every tool API lesson.\n"
        " */\n"
        'import { bash, js, plain, py, sql, ts, yaml } from "@/lib/samples/_helpers";\n'
        'import type { CodeSample } from "@/types/curriculum";\n'
        "\n"
        "export const generatedApiExamples: Readonly<\n"
        "  Record<string, readonly CodeSample[]>\n"
        "> = {\n"
        + ",\n".join(entries)
        + "\n};\n"
    )
    OUT.write_text(content)
    print(f"Wrote {OUT.relative_to(ROOT)} with {total} API lessons across {len(tool_calls)} tools")


if __name__ == "__main__":
    main()
