import { bash, js, py, sql, ts, yaml } from "@/lib/samples/_helpers";
import { toolCategories } from "@/lib/tools-catalog";
import type { CodeSample } from "@/types/curriculum";
import type { AcademyTool, LearningCall } from "@/types/tools";

/**
 * On-site dual-language (or best-fit) examples for every LearningCall.
 * Handcrafted maps in `test-automation.ts` etc. override these via merge order.
 */
export function buildConceptShellSamples(): Record<string, readonly CodeSample[]> {
  const out: Record<string, CodeSample[]> = {};

  for (const category of toolCategories) {
    for (const tool of category.tools) {
      for (const call of tool.calls) {
        out[`${tool.id}.${call.id}`] = samplesFor(tool, call);
      }
    }
  }

  return out;
}

function samplesFor(tool: AcademyTool, call: LearningCall): CodeSample[] {
  const id = tool.id;
  if (id === "playwright") return playwrightSamples(call);
  if (id === "selenium") return seleniumSamples(call);
  if (id === "cypress") return cypressSamples(call);
  if (id === "pytest" || id === "robot") return pythonFirst(tool, call);
  if (id === "k6") return k6Samples(call);
  if (id === "artillery") return artillerySamples(call);
  if (id === "jmeter") return jmeterSamples(call);
  if (id === "sql" || id === "postgresql" || id === "snowflake") return sqlSamples(tool, call);
  if (
    id === "docker" ||
    id === "git" ||
    id === "aws" ||
    id === "azure" ||
    id === "jenkins" ||
    id === "azure-devops" ||
    id === "bitbucket"
  ) {
    return opsSamples(tool, call);
  }
  if (id === "deepeval" || id === "ragas" || id === "rag" || id === "agentic-ai" || id === "langsmith") {
    return aiSamples(tool, call);
  }
  return defaultSamples(tool, call);
}

function playwrightSamples(call: LearningCall): CodeSample[] {
  const sig = call.signature;
  const key = call.id;
  const needsRe = key === "goto";
  return [
    ts(
      `playwright.${key}.spec.ts`,
      `import { test, expect } from '@playwright/test';

/** On-site academy example — ${sig} */
test('${key}: ${call.summary}', async ({ page, context, request }) => {
  // ${call.why}
  await page.goto('/app');

  ${playwrightBody(key)}
});`,
    ),
    py(
      `test_playwright_${key.replace(/-/g, "_")}.py`,
      `"""On-site academy example — ${sig}"""
${needsRe ? "import re\n" : ""}from playwright.sync_api import Page, expect

def test_${key.replace(/-/g, "_")}(page: Page):
    # ${call.why}
    page.goto("/app")
${playwrightBodyPy(key)}`,
    ),
  ];
}

function playwrightBody(key: string): string {
  const map: Record<string, string> = {
    goto: `await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/dashboard/);`,
    "get-by-role": `await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('status')).toContainText(/saved/i);`,
    "get-by-label": `await page.getByLabel('Email').fill('qa@example.com');
  await expect(page.getByLabel('Email')).toHaveValue('qa@example.com');`,
    "get-by-test-id": `await expect(page.getByTestId('app-shell')).toBeVisible();`,
    "locator-actions": `const email = page.getByLabel('Email');
  await email.fill('qa@example.com');
  await email.press('Tab');
  await page.getByRole('button', { name: 'Continue' }).click();`,
    expect: `await expect(page.getByTestId('title')).toHaveText('Dashboard');
  await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();`,
    "expect-soft": `await expect.soft(page.getByTestId('a')).toHaveText('1');
  await expect.soft(page.getByTestId('b')).toHaveText('2');
  await expect(page.getByTestId('ready')).toBeVisible();`,
    "expect-poll": `await expect.poll(async () => {
    const res = await request.get('/api/health');
    return res.status();
  }).toBe(200);`,
    "wait-for-url": `await page.getByRole('button', { name: 'Checkout' }).click();
  await page.waitForURL('**/checkout');`,
    "wait-for-response": `const wait = page.waitForResponse((r) => r.url().includes('/api/cart') && r.ok());
  await page.getByRole('button', { name: 'Add' }).click();
  const res = await wait;
  expect(res.status()).toBe(200);`,
    route: `await page.route('**/api/pricing', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ total: 9.99 }) });
  });
  await page.reload();
  await expect(page.getByTestId('total')).toHaveText('$9.99');`,
    request: `const res = await request.post('/api/bookings', { data: { room: 1 } });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body).toHaveProperty('bookingid');`,
    "storage-state": `await context.storageState({ path: 'playwright/.auth/user.json' });
  // Reuse via project: use: { storageState: 'playwright/.auth/user.json' }`,
    fixtures: `// Prefer test.extend in a fixtures file — see patterns guide.
  await expect(page.getByTestId('app-shell')).toBeVisible();`,
    "test-step": `await test.step('open settings', async () => {
    await page.getByRole('link', { name: 'Settings' }).click();
  });
  await test.step('save profile', async () => {
    await page.getByRole('button', { name: 'Save' }).click();
  });`,
    "frame-locator": `const frame = page.frameLocator('#payment-iframe');
  await frame.getByLabel('Card number').fill('4242424242424242');`,
    "file-upload": `await page.getByLabel('Upload').setInputFiles('fixtures/sample.pdf');
  await expect(page.getByText('sample.pdf')).toBeVisible();`,
    download: `const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Export CSV' }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/\\.csv$/);`,
    dialog: `page.once('dialog', async (dialog) => {
    expect(dialog.type()).toBe('confirm');
    await dialog.accept();
  });
  await page.getByRole('button', { name: 'Delete' }).click();`,
    screenshot: `await expect(page.getByTestId('hero')).toHaveScreenshot('hero.png');`,
    trace: `// Enable in config: use: { trace: 'on-first-retry' }
  await expect(page.getByTestId('app-shell')).toBeVisible();`,
    evaluate: `const theme = await page.evaluate(() => document.documentElement.dataset.theme);
  expect(['light', 'dark', 'system']).toContain(theme);`,
    viewport: `await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByTestId('mobile-nav')).toBeVisible();`,
    parallel: `// fullyParallel: true + projects[] in playwright.config.ts
  await expect(page.getByTestId('app-shell')).toBeVisible();`,
  };
  return map[key] ?? `await expect(page.getByTestId('app-shell')).toBeVisible();`;
}

function playwrightBodyPy(key: string): string {
  const map: Record<string, string> = {
    goto: `    page.goto("/dashboard", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r".*/dashboard"))`,
    "get-by-role": `    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("status")).to_contain_text("saved")`,
    "get-by-label": `    page.get_by_label("Email").fill("qa@example.com")
    expect(page.get_by_label("Email")).to_have_value("qa@example.com")`,
    "get-by-test-id": `    expect(page.get_by_test_id("app-shell")).to_be_visible()`,
    "locator-actions": `    email = page.get_by_label("Email")
    email.fill("qa@example.com")
    email.press("Tab")
    page.get_by_role("button", name="Continue").click()`,
    expect: `    expect(page.get_by_test_id("title")).to_have_text("Dashboard")`,
    "expect-soft": `    expect(page.get_by_test_id("ready")).to_be_visible()`,
    "expect-poll": `    expect(page.get_by_test_id("ready")).to_be_visible(timeout=10_000)`,
    "wait-for-url": `    page.get_by_role("button", name="Checkout").click()
    page.wait_for_url("**/checkout")`,
    "wait-for-response": `    with page.expect_response(lambda r: "/api/cart" in r.url and r.ok) as resp_info:
        page.get_by_role("button", name="Add").click()
    assert resp_info.value.status == 200`,
    route: `    page.route("**/api/pricing", lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"total": 9.99}'
    ))
    page.reload()
    expect(page.get_by_test_id("total")).to_have_text("$9.99")`,
    request: `    # Prefer APIRequestContext fixture in real suites
    expect(page.get_by_test_id("app-shell")).to_be_visible()`,
    "storage-state": `    page.context.storage_state(path="playwright/.auth/user.json")`,
    fixtures: `    expect(page.get_by_test_id("app-shell")).to_be_visible()`,
    "test-step": `    page.get_by_role("link", name="Settings").click()
    page.get_by_role("button", name="Save").click()`,
    "frame-locator": `    frame = page.frame_locator("#payment-iframe")
    frame.get_by_label("Card number").fill("4242424242424242")`,
    "file-upload": `    page.get_by_label("Upload").set_input_files("fixtures/sample.pdf")
    expect(page.get_by_text("sample.pdf")).to_be_visible()`,
    download: `    with page.expect_download() as dl_info:
        page.get_by_role("button", name="Export CSV").click()
    assert dl_info.value.suggested_filename.endswith(".csv")`,
    dialog: `    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Delete").click()`,
    screenshot: `    expect(page.get_by_test_id("hero")).to_have_screenshot("hero.png")`,
    trace: `    expect(page.get_by_test_id("app-shell")).to_be_visible()`,
    evaluate: `    theme = page.evaluate("() => document.documentElement.dataset.theme")
    assert theme in {"light", "dark", "system"}`,
    viewport: `    page.set_viewport_size({"width": 390, "height": 844})
    expect(page.get_by_test_id("mobile-nav")).to_be_visible()`,
    parallel: `    expect(page.get_by_test_id("app-shell")).to_be_visible()`,
  };
  return map[key] ?? `    expect(page.get_by_test_id("app-shell")).to_be_visible()`;
}

function seleniumSamples(call: LearningCall): CodeSample[] {
  return [
    py(
      `test_selenium_${call.id.replace(/-/g, "_")}.py`,
      `"""${call.signature} — ${call.summary}"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_${call.id.replace(/-/g, "_")}(driver):
    # ${call.why}
    driver.get("https://the-internet.herokuapp.com/")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    assert "internet" in driver.title.lower() or driver.current_url`,
    ),
    ts(
      `selenium.${call.id}.spec.ts`,
      `import { By, until } from 'selenium-webdriver';

/** ${call.signature} */
test('${call.id}', async () => {
  // ${call.why}
  await driver.get('https://the-internet.herokuapp.com/');
  await driver.wait(until.elementLocated(By.css('h1')), 10_000);
});`,
    ),
  ];
}

function cypressSamples(call: LearningCall): CodeSample[] {
  return [
    js(
      `cypress.${call.id}.cy.js`,
      `/** ${call.signature} — ${call.summary} */
describe('${call.id}', () => {
  it('exercises the command on-site', () => {
    // ${call.why}
    cy.visit('/app');
    cy.get('[data-testid="app-shell"]').should('be.visible');
  });
});`,
    ),
    ts(
      `cypress.${call.id}.cy.ts`,
      `/** ${call.signature} */
describe('${call.id}', () => {
  it('typescript variant', () => {
    cy.visit('/app');
    cy.contains('button', /save|continue|submit/i).should('exist');
  });
});`,
    ),
  ];
}

function pythonFirst(tool: AcademyTool, call: LearningCall): CodeSample[] {
  return [
    py(
      `${tool.id}_${call.id.replace(/-/g, "_")}.py`,
      `"""${tool.name}: ${call.signature}

${call.summary}
Why: ${call.why}
"""
import pytest

def test_${call.id.replace(/-/g, "_")}_smoke():
    # Minimal on-site example — expand with your app under test.
    assert "${call.id}"  # concept marker
    result = {"tool": "${tool.id}", "call": "${call.id}"}
    assert result["tool"] == "${tool.id}"


@pytest.mark.parametrize("case_id", ["happy", "edge"])
def test_${call.id.replace(/-/g, "_")}_cases(case_id: str):
    assert case_id in {"happy", "edge"}`,
    ),
    ts(
      `${tool.id}.${call.id}.ts`,
      `/** ${tool.name}: ${call.signature} */
export function demo${toPascal(call.id)}() {
  // ${call.why}
  return { tool: '${tool.id}', call: '${call.id}', ok: true as const };
}

demo${toPascal(call.id)}();`,
    ),
  ];
}

function k6Samples(call: LearningCall): CodeSample[] {
  return [
    js(
      `k6.${call.id}.js`,
      `import http from 'k6/http';
import { check, sleep } from 'k6';

/** ${call.signature} — ${call.summary} */
export const options = {
  vus: 2,
  duration: '10s',
  thresholds: { http_req_failed: ['rate<0.01'] },
};

export default function () {
  // ${call.why}
  const res = http.get(__ENV.BASE_URL || 'https://test.k6.io');
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}`,
    ),
    ts(
      `k6.${call.id}.ts`,
      `/** TypeScript-shaped k6 snippet for ${call.signature} */
export const options = { vus: 1, duration: '5s' };
// Run with: k6 run k6.${call.id}.js`,
    ),
  ];
}

function artillerySamples(call: LearningCall): CodeSample[] {
  return [
    yaml(
      `artillery.${call.id}.yml`,
      `# ${call.signature}
# ${call.summary}
config:
  target: "https://httpbin.org"
  phases:
    - duration: 10
      arrivalRate: 1
scenarios:
  - name: ${call.id}
    flow:
      - get:
          url: "/get"
      - think: 1`,
    ),
    js(
      `artillery.${call.id}.processor.js`,
      `/** Processor hook for ${call.signature} */
function setId(userContext, events, done) {
  userContext.vars.id = Date.now().toString(36);
  return done();
}
module.exports = { setId };`,
    ),
  ];
}

function jmeterSamples(call: LearningCall): CodeSample[] {
  return [
    bash(
      `jmeter_${call.id.replace(/-/g, "_")}.sh`,
      `#!/usr/bin/env bash
# ${call.signature} — ${call.summary}
# ${call.why}
set -euo pipefail
jmeter -n -t plans/${call.id}.jmx -l results/${call.id}.jtl -e -o reports/${call.id}`,
    ),
    py(
      `jmeter_${call.id.replace(/-/g, "_")}_gate.py`,
      `"""Parse JMeter JTL summary for ${call.signature}."""
from pathlib import Path

def assert_error_rate(jtl: Path, max_rate: float = 0.01) -> None:
    lines = jtl.read_text().strip().splitlines()
    # simplified: real parsers use CSV headers
    assert lines, "empty JTL"
    assert max_rate >= 0`,
    ),
  ];
}

function sqlSamples(tool: AcademyTool, call: LearningCall): CodeSample[] {
  return [
    sql(
      `${tool.id}.${call.id}.sql`,
      `-- ${tool.name}: ${call.signature}
-- ${call.summary}
-- ${call.why}
SELECT id, email, created_at
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 50;`,
    ),
    py(
      `test_${tool.id.replace(/-/g, "_")}_${call.id.replace(/-/g, "_")}.py`,
      `"""${tool.name} — ${call.signature}"""
import os
import psycopg

def test_${call.id.replace(/-/g, "_")}_query():
    dsn = os.getenv("DATABASE_URL", "postgresql://qa:qa@127.0.0.1:5432/qa")
    # ${call.why}
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1`,
    ),
  ];
}

function opsSamples(tool: AcademyTool, call: LearningCall): CodeSample[] {
  return [
    bash(
      `${tool.id}_${call.id.replace(/-/g, "_")}.sh`,
      `#!/usr/bin/env bash
# ${tool.name}: ${call.signature}
# ${call.summary}
set -euo pipefail
echo "Running ${tool.id}/${call.id}"
# ${call.why}
true`,
    ),
    yaml(
      `${tool.id}.${call.id}.yml`,
      `# ${tool.name} — ${call.signature}
# ${call.why}
name: ${tool.id}-${call.id}
on: [push]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: ${call.id}
        run: echo "${call.signature}"`,
    ),
  ];
}

function aiSamples(tool: AcademyTool, call: LearningCall): CodeSample[] {
  return [
    py(
      `${tool.id}_${call.id.replace(/-/g, "_")}.py`,
      `"""${tool.name}: ${call.signature}

${call.summary}
Why: ${call.why}
"""
from __future__ import annotations

def demo_${call.id.replace(/-/g, "_")}() -> dict:
    case = {
        "tool": "${tool.id}",
        "call": "${call.id}",
        "input": "What is the refund policy?",
        "actual_output": "Refunds are available within 30 days.",
        "retrieval_context": ["Refunds within 30 days with receipt."],
    }
    assert case["actual_output"]
    return case


if __name__ == "__main__":
    print(demo_${call.id.replace(/-/g, "_")}())`,
    ),
    ts(
      `${tool.id}.${call.id}.ts`,
      `/** ${tool.name}: ${call.signature} */
export type EvalCase = {
  input: string;
  actualOutput: string;
  context: string[];
};

export function demo${toPascal(call.id)}(): EvalCase {
  // ${call.why}
  return {
    input: 'What is the refund policy?',
    actualOutput: 'Refunds are available within 30 days.',
    context: ['Refunds within 30 days with receipt.'],
  };
}`,
    ),
  ];
}

function defaultSamples(tool: AcademyTool, call: LearningCall): CodeSample[] {
  return [
    ts(
      `${tool.id}.${call.id}.ts`,
      `/**
 * ${tool.name} — ${call.signature}
 * ${call.summary}
 *
 * Why teams use this: ${call.why}
 */
export function exercise${toPascal(call.id)}(input: Record<string, unknown> = {}) {
  const result = {
    tool: '${tool.id}' as const,
    call: '${call.id}' as const,
    signature: '${call.signature.replace(/'/g, "\\'")}',
    input,
    ok: true,
  };
  if (!result.tool) throw new Error('tool required');
  return result;
}

exercise${toPascal(call.id)}({ scenario: 'happy-path' });`,
    ),
    py(
      `${tool.id}_${call.id.replace(/-/g, "_")}.py`,
      `"""${tool.name} — ${call.signature}

${call.summary}
Why: ${call.why}
"""
from __future__ import annotations

def exercise_${call.id.replace(/-/g, "_")}(input_data: dict | None = None) -> dict:
    payload = input_data or {"scenario": "happy-path"}
    result = {
        "tool": "${tool.id}",
        "call": "${call.id}",
        "signature": """${call.signature}""",
        "input": payload,
        "ok": True,
    }
    assert result["ok"]
    return result


if __name__ == "__main__":
    print(exercise_${call.id.replace(/-/g, "_")}())`,
    ),
  ];
}

function toPascal(id: string): string {
  return id
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}
