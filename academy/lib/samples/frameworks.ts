import { py, ts } from "@/lib/samples/_helpers";
import type { CodeSample } from "@/types/curriculum";

export const frameworksSamples: Readonly<Record<string, readonly CodeSample[]>> = {
  "pytest.fixtures": [
    py(
      "conftest.py",
      `import pytest
import httpx

@pytest.fixture(scope="session")
def base_url() -> str:
    return "https://api.example.com"

@pytest.fixture
def api(base_url: str):
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client

@pytest.fixture
def auth_headers(api: httpx.Client) -> dict[str, str]:
    token = api.post("/oauth/token", json={"grant": "client"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}`,
    ),
    ts(
      "fixtures.spec.ts",
      `import { test as base } from '@playwright/test';

type Fixtures = { apiToken: string };

export const test = base.extend<Fixtures>({
  apiToken: async ({ request }, use) => {
    const res = await request.post('/oauth/token', { data: { grant: 'client' } });
    const { access_token } = await res.json();
    await use(access_token);
  },
});`,
    ),
  ],
  "pytest.parametrize": [
    py(
      "test_status_matrix.py",
      `import pytest

@pytest.mark.parametrize(
    ("code", "ok"),
    [(200, True), (201, True), (204, True), (400, False), (500, False)],
    ids=lambda v: str(v),
)
def test_success_matrix(code: int, ok: bool):
    assert (200 <= code < 300) is ok`,
    ),
    ts(
      "status-matrix.spec.ts",
      `const cases = [
  [200, true], [201, true], [204, true], [400, false], [500, false],
] as const;

test.each(cases)('HTTP %i success=%s', (code, ok) => {
  expect(code >= 200 && code < 300).toBe(ok);
});`,
    ),
  ],
  "pytest.markers": [
    py(
      "pytest.ini",
      `# markers registered in pytest.ini / pyproject.toml
# [pytest]
# markers =
#   smoke: critical path
#   slow: > 2s

import pytest

@pytest.mark.smoke
def test_health(api):
    assert api.get("/health").status_code == 200

@pytest.mark.slow
@pytest.mark.skip(reason="run nightly only")
def test_full_regression():
    ...`,
    ),
    ts(
      "markers.spec.ts",
      `test.describe('smoke', () => {
  test('health @smoke', async ({ request }) => {
    test.info().annotations.push({ type: 'tag', description: 'smoke' });
    const res = await request.get('/health');
    expect(res.status()).toBe(200);
  });
});`,
    ),
  ],
  "pytest.patterns": [
    py(
      "tests/test_factory.py",
      `from dataclasses import dataclass
import uuid

@dataclass
class UserFactory:
    def create(self, *, role: str = "user") -> dict:
        return {"id": str(uuid.uuid4()), "role": role, "email": f"{role}@example.com"}

def test_factory_isolation():
    factory = UserFactory()
    a, b = factory.create(), factory.create(role="admin")
    assert a["id"] != b["id"]
    assert b["role"] == "admin"`,
    ),
  ],

  "testng.annotations": [
    py(
      "test_annotations_equivalent.py",
      `"""TestNG @Test/@BeforeMethod mental model in pytest."""
import pytest

@pytest.fixture(autouse=True)
def before_method():
    # @BeforeMethod
    yield
    # @AfterMethod

@pytest.mark.smoke
def test_valid_login(auth_client):
    assert auth_client.login("qa@example.com", "secret").ok`,
    ),
    ts(
      "annotations.spec.ts",
      `test.describe('login @smoke', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('valid login', async ({ page }) => {
    await page.getByLabel('Email').fill('qa@example.com');
    await page.getByLabel('Password').fill('secret');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });
});`,
    ),
  ],
  "testng.groups": [
    py(
      "test_groups.py",
      `import pytest

@pytest.mark.smoke
def test_checkout_smoke():
    assert True

@pytest.mark.regression
def test_checkout_edge_coupon():
    assert True

# Run: pytest -m smoke`,
    ),
    ts(
      "groups.spec.ts",
      `test.describe('smoke group', () => {
  test('checkout smoke', async () => {
    test.skip(process.env.RUN_SMOKE !== '1', 'set RUN_SMOKE=1');
    expect(true).toBeTruthy();
  });
});`,
    ),
  ],
  "testng.parallel": [
    py(
      "pytest.ini",
      `# parallel with pytest-xdist
# pytest -n auto --dist loadscope`,
    ),
    ts(
      "playwright.config.parallel.ts",
      `import { defineConfig } from '@playwright/test';
export default defineConfig({
  workers: process.env.CI ? 4 : undefined,
  fullyParallel: true,
});`,
    ),
  ],

  "nunit.test": [
    py(
      "test_nunit_style.py",
      `def test_cart_total():
    assert sum([2, 3]) == 5`,
    ),
    ts(
      "cart.spec.ts",
      `test('cart total', () => {
  expect([2, 3].reduce((a, b) => a + b, 0)).toBe(5);
});`,
    ),
  ],
  "nunit.test-case": [
    py(
      "test_cases.py",
      `import pytest

@pytest.mark.parametrize("code", [200, 201, 204])
def test_success_statuses(code: int):
    assert 200 <= code < 300`,
    ),
    ts(
      "test-case.spec.ts",
      `test.each([200, 201, 204])('success status %i', (code) => {
  expect(code).toBeGreaterThanOrEqual(200);
  expect(code).toBeLessThan(300);
});`,
    ),
  ],
  "nunit.setup": [
    py(
      "conftest_setup.py",
      `import pytest

@pytest.fixture
def db_txn():
    # SetUp
    txn = {"open": True}
    yield txn
    # TearDown
    txn["open"] = False`,
    ),
    ts(
      "setup.spec.ts",
      `test.describe('db txn', () => {
  let open = false;
  test.beforeEach(() => { open = true; });
  test.afterEach(() => { open = false; });
  test('uses open txn', () => { expect(open).toBe(true); });
});`,
    ),
  ],

  "mocha.describe-it": [
    ts(
      "math.spec.ts",
      `import { expect } from 'chai';

describe('cart total', () => {
  it('sums line items', () => {
    const total = (items: { price: number }[]) =>
      items.reduce((s, i) => s + i.price, 0);
    expect(total([{ price: 2 }, { price: 3 }])).to.equal(5);
  });
});`,
    ),
    py(
      "test_math.py",
      `def total(items: list[dict]) -> int:
    return sum(i["price"] for i in items)

def test_sums_line_items():
    assert total([{"price": 2}, {"price": 3}]) == 5`,
    ),
  ],
  "mocha.hooks": [
    ts(
      "hooks.spec.ts",
      `describe('hooks', () => {
  before(async function () { this.timeout(10_000); /* suite setup */ });
  beforeEach(() => { /* per test */ });
  afterEach(function () {
    if (this.currentTest?.state === 'failed') {
      // attach logs
    }
  });
  it('runs', () => {});
});`,
    ),
    py(
      "test_hooks.py",
      `import pytest

@pytest.fixture(autouse=True)
def hooks():
    # beforeEach
    yield
    # afterEach`,
    ),
  ],
  "mocha.async": [
    ts(
      "async.spec.ts",
      `import { expect } from 'chai';

describe('async', () => {
  it('awaits promises', async () => {
    const value = await Promise.resolve(42);
    expect(value).to.equal(42);
  });
});`,
    ),
    py(
      "test_async.py",
      `import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_value():
    value = await asyncio.sleep(0, result=42)
    assert value == 42`,
    ),
  ],

  "robot.keywords": [
    py(
      "Libraries/AuthLibrary.py",
      `from robot.api.deco import keyword

class AuthLibrary:
    @keyword("Sign In As")
    def sign_in_as(self, email: str, password: str) -> None:
        # Drive Selenium/Playwright under the hood
        assert "@" in email
        assert len(password) >= 8`,
    ),
    ts(
      "robot-keyword-contract.ts",
      `/** Contract mirrored by Robot keyword "Sign In As" */
export function signInAs(email: string, password: string) {
  if (!email.includes('@')) throw new Error('email');
  if (password.length < 8) throw new Error('password');
}`,
    ),
  ],
  "robot.variables": [
    py(
      "variables.py",
      `BASE_URL = "https://staging.example.com"
BROWSER = "chromium"
TIMEOUT = "15s"`,
    ),
    ts(
      "variables.ts",
      `export const BASE_URL = process.env.BASE_URL ?? 'https://staging.example.com';
export const TIMEOUT_MS = 15_000;`,
    ),
  ],
  "robot.libraries": [
    py(
      "Libraries/ApiLibrary.py",
      `import httpx
from robot.api.deco import keyword

class ApiLibrary:
    def __init__(self, base_url: str) -> None:
        self.client = httpx.Client(base_url=base_url)

    @keyword("GET JSON")
    def get_json(self, path: str) -> dict:
        res = self.client.get(path)
        res.raise_for_status()
        return res.json()`,
    ),
  ],

  "webdriverio.browser-url": [
    ts(
      "nav.e2e.ts",
      `describe('checkout', () => {
  it('opens checkout', async () => {
    await browser.url('/checkout');
    await expect(browser).toHaveUrl(expect.stringContaining('checkout'));
    await expect($('h1=Checkout')).toBeDisplayed();
  });
});`,
    ),
    py(
      "test_wdio_companion.py",
      `import httpx

def test_checkout_route_exists():
    r = httpx.get("http://localhost:3000/checkout", follow_redirects=True)
    assert r.status_code < 500`,
    ),
  ],
  "webdriverio.dollar": [
    ts(
      "dollar.e2e.ts",
      `it('uses $ and $$', async () => {
  await browser.url('/inbox');
  const threads = await $$('[data-testid=thread]');
  expect(threads.length).toBeGreaterThan(0);
  await threads[0].click();
  await expect($('[data-testid=thread-detail]')).toBeDisplayed();
});`,
    ),
  ],
  "webdriverio.wait-until": [
    ts(
      "wait.e2e.ts",
      `it('waitUntil for inventory', async () => {
  await browser.url('/product/1');
  await browser.waitUntil(
    async () => (await $('#inventory').getText()).includes('in stock'),
    { timeout: 10_000, timeoutMsg: 'inventory never ready' },
  );
});`,
    ),
  ],
  "webdriverio.patterns": [
    ts(
      "pageobjects/login.page.ts",
      `class LoginPage {
  get email() { return $('#email'); }
  get password() { return $('#password'); }
  get submit() { return $('button[type=submit]'); }
  async open() { await browser.url('/login'); }
  async login(email: string, password: string) {
    await this.email.setValue(email);
    await this.password.setValue(password);
    await this.submit.click();
  }
}
export default new LoginPage();`,
    ),
  ],

  "nightwatch.navigate": [
    ts(
      "navigate.ts",
      `describe('navigate', () => {
  it('opens home', (browser) => {
    browser
      .navigateTo('http://localhost:3000')
      .assert.urlContains('localhost')
      .assert.visible('h1');
  });
});`,
    ),
    py(
      "test_nightwatch_companion.py",
      `import httpx
def test_home_ok():
    assert httpx.get("http://localhost:3000").status_code == 200`,
    ),
  ],
  "nightwatch.assert": [
    ts(
      "assert.ts",
      `it('asserts text', (browser) => {
  browser
    .navigateTo('/pricing')
    .assert.textContains('h1', 'Pricing')
    .assert.attributeEquals('a.cta', 'href', '/signup');
});`,
    ),
  ],
  "nightwatch.page-objects": [
    ts(
      "page-objects/login.ts",
      `module.exports = {
  url: '/login',
  elements: {
    email: '#email',
    password: '#password',
    submit: 'button[type=submit]',
  },
  commands: [{
    signIn(email: string, password: string) {
      return this
        .setValue('@email', email)
        .setValue('@password', password)
        .click('@submit');
    },
  }],
};`,
    ),
  ],

  "isafe.data-tables": [
    py(
      "test_isafe_tables.py",
      `import csv
from pathlib import Path

def test_data_table_headers():
    rows = list(csv.DictReader(Path("data/isafe_cases.csv").open()))
    assert {"case_id", "priority", "step"}.issubset(rows[0].keys())`,
    ),
    ts(
      "data-tables.spec.ts",
      `import { readFileSync } from 'node:fs';
const csv = readFileSync('data/isafe_cases.csv', 'utf8');
test('data table has headers', () => {
  expect(csv.split('\\n')[0]).toMatch(/case_id/);
});`,
    ),
  ],
  "isafe.pom": [
    ts(
      "pom/search.page.ts",
      `export class SearchPage {
  constructor(private goto: (path: string) => Promise<void>, private fill: Function) {}
  async open() { await this.goto('/search'); }
  async query(q: string) { await this.fill('#q', q); }
}`,
    ),
    py(
      "pom/search_page.py",
      `class SearchPage:
    def __init__(self, page):
        self.page = page
    def open(self):
        self.page.goto("/search")
    def query(self, q: str):
        self.page.fill("#q", q)`,
    ),
  ],
  "isafe.keywords": [
    py(
      "keywords.py",
      `def keyword_create_order(customer_id: str, sku: str) -> dict:
    assert customer_id and sku
    return {"order_id": f"ORD-{customer_id}-{sku}"}`,
    ),
    ts(
      "keywords.ts",
      `export function createOrder(customerId: string, sku: string) {
  if (!customerId || !sku) throw new Error('missing');
  return { orderId: \`ORD-\${customerId}-\${sku}\` };
}`,
    ),
  ],

  "bdd.three-amigos": [
    py(
      "three_amigos_notes.py",
      `"""Capture Three Amigos outcomes as executable examples."""
EXAMPLES = [
    {"rule": "refund < 30 days", "expect": "allowed"},
    {"rule": "refund > 30 days", "expect": "denied"},
]

def test_examples_are_binary():
    assert {e["expect"] for e in EXAMPLES} <= {"allowed", "denied"}`,
    ),
    ts(
      "three-amigos.spec.ts",
      `const examples = [
  { rule: 'refund < 30 days', expect: 'allowed' },
  { rule: 'refund > 30 days', expect: 'denied' },
];
test('examples stay decisive', () => {
  for (const e of examples) expect(['allowed', 'denied']).toContain(e.expect);
});`,
    ),
  ],
  "bdd.living-docs": [
    ts(
      "living-docs.ts",
      `/** Generate living doc snippets from scenarios */
export function toLivingDoc(scenario: { name: string; steps: string[] }) {
  return [\`## \${scenario.name}\`, ...scenario.steps.map((s) => \`- \${s}\`)].join('\\n');
}`,
    ),
    py(
      "living_docs.py",
      `def to_living_doc(name: str, steps: list[str]) -> str:
    return "\\n".join([f"## {name}", *[f"- {s}" for s in steps]])`,
    ),
  ],
  "bdd.ubiquitous": [
    py(
      "glossary.py",
      `GLOSSARY = {
    "Claim": "A request for benefit payment",
    "Adjudication": "Decision process for a claim",
}

def test_glossary_terms():
    assert "Claim" in GLOSSARY`,
    ),
    ts(
      "glossary.ts",
      `export const glossary = {
  Claim: 'A request for benefit payment',
  Adjudication: 'Decision process for a claim',
} as const;`,
    ),
  ],
};
