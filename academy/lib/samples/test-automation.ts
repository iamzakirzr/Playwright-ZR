import { py, ts } from "@/lib/samples/_helpers";
import type { CodeSample } from "@/types/curriculum";

export const testAutomationSamples: Readonly<
  Record<string, readonly CodeSample[]>
> = {
  "playwright.goto": [
    ts(
      "navigate.advanced.spec.ts",
      `import { test, expect } from '@playwright/test';

test.describe('resilient navigation', () => {
  test('waits for network idle + app shell', async ({ page }) => {
    const failures: string[] = [];
    page.on('response', (res) => {
      if (res.status() >= 500) failures.push(\`\${res.status()} \${res.url()}\`);
    });

    await page.goto('/app', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('app-shell')).toBeVisible();
    await expect.poll(() => failures, { timeout: 5_000 }).toEqual([]);
  });
});`,
    ),
    py(
      "test_navigate_advanced.py",
      `import re
from playwright.sync_api import Page, expect

def test_goto_waits_for_shell(page: Page):
    failures: list[str] = []
    page.on("response", lambda res: failures.append(f"{res.status} {res.url}")
            if res.status >= 500 else None)

    page.goto("/app", wait_until="domcontentloaded")
    expect(page.get_by_test_id("app-shell")).to_be_visible()
    assert failures == [], failures
    expect(page).to_have_url(re.compile(r"/app/?$"))`,
    ),
  ],
  "playwright.get-by-role": [
    ts(
      "locators.advanced.spec.ts",
      `import { test, expect } from '@playwright/test';

test('composes accessible locators with filters', async ({ page }) => {
  await page.goto('/settings');
  const dialog = page.getByRole('dialog', { name: 'Edit profile' });
  await page.getByRole('button', { name: 'Edit profile' }).click();
  await expect(dialog).toBeVisible();

  await dialog.getByRole('textbox', { name: 'Display name' }).fill('QA Lead');
  await dialog.getByRole('button', { name: 'Save' }).click();
  await expect(dialog).toBeHidden();
  await expect(page.getByRole('status')).toHaveText(/saved/i);
});`,
    ),
    py(
      "test_locators_advanced.py",
      `from playwright.sync_api import Page, expect

def test_role_locators_with_dialog(page: Page):
    page.goto("/settings")
    page.get_by_role("button", name="Edit profile").click()
    dialog = page.get_by_role("dialog", name="Edit profile")
    expect(dialog).to_be_visible()
    dialog.get_by_role("textbox", name="Display name").fill("QA Lead")
    dialog.get_by_role("button", name="Save").click()
    expect(dialog).to_be_hidden()
    expect(page.get_by_role("status")).to_contain_text("saved")`,
    ),
  ],
  "playwright.expect": [
    ts(
      "assert.advanced.spec.ts",
      `import { test, expect } from '@playwright/test';

test('soft asserts + auto-retry polling', async ({ page }) => {
  await page.goto('/cart');
  await expect.soft(page.getByTestId('cart-count')).toHaveText('3');
  await expect(page.getByTestId('subtotal')).toHaveText(/\\$[0-9]+\\.\\d{2}/);

  await expect
    .poll(async () => page.getByTestId('inventory').innerText(), { timeout: 10_000 })
    .toMatch(/in stock/i);
});`,
    ),
    py(
      "test_expect_advanced.py",
      `import re
from playwright.sync_api import Page, expect

def test_web_first_assertions(page: Page):
    page.goto("/cart")
    expect(page.get_by_test_id("cart-count")).to_have_text("3")
    expect(page.get_by_test_id("subtotal")).to_have_text(re.compile(r"\\$\\d+\\.\\d{2}"))
    expect(page.get_by_test_id("inventory")).to_contain_text("in stock", timeout=10_000)`,
    ),
  ],
  "playwright.patterns": [
    ts(
      "pages/checkout.page.ts",
      `import { type Page, expect } from '@playwright/test';

export class CheckoutPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto('/checkout');
    await expect(this.page.getByRole('heading', { name: 'Checkout' })).toBeVisible();
  }

  async payWithCard(card: { number: string; exp: string; cvc: string }) {
    await this.page.getByLabel('Card number').fill(card.number);
    await this.page.getByLabel('Expiry').fill(card.exp);
    await this.page.getByLabel('CVC').fill(card.cvc);
    await this.page.getByRole('button', { name: 'Pay now' }).click();
  }
}`,
    ),
    py(
      "pages/checkout_page.py",
      `from playwright.sync_api import Page, expect

class CheckoutPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto("/checkout")
        expect(self.page.get_by_role("heading", name="Checkout")).to_be_visible()

    def pay_with_card(self, number: str, exp: str, cvc: str) -> None:
        self.page.get_by_label("Card number").fill(number)
        self.page.get_by_label("Expiry").fill(exp)
        self.page.get_by_label("CVC").fill(cvc)
        self.page.get_by_role("button", name="Pay now").click()`,
    ),
  ],
  "playwright.delivery": [
    ts(
      "playwright.config.ts",
      `import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never' }], ['junit', { outputFile: 'reports/junit.xml' }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],
});`,
    ),
    py(
      "conftest.py",
      `import os
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "base_url": os.getenv("BASE_URL", "http://127.0.0.1:3000"),
        "record_video_dir": "artifacts/video" if os.getenv("CI") else None,
    }

@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}`,
    ),
  ],

  "selenium.get": [
    py(
      "test_navigation.py",
      `from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_get_loads_title():
    opts = Options()
    opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.set_page_load_timeout(20)
        driver.get("https://example.com")
        assert "Example" in driver.title
        assert driver.current_url.startswith("https://")
    finally:
        driver.quit()`,
    ),
    ts(
      "navigation.spec.ts",
      `import { Builder, until } from 'selenium-webdriver';
import chrome from 'selenium-webdriver/chrome.js';

test('driver.get loads a document', async () => {
  const options = new chrome.Options().addArguments('--headless=new');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();
  try {
    await driver.manage().setTimeouts({ pageLoad: 20_000 });
    await driver.get('https://example.com');
    await driver.wait(until.titleContains('Example'), 5_000);
  } finally {
    await driver.quit();
  }
});`,
    ),
  ],
  "selenium.find-element": [
    py(
      "test_locators.py",
      `from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def test_find_element_with_explicit_wait(driver):
    driver.get("https://the-internet.herokuapp.com/login")
    wait = WebDriverWait(driver, 10)
    user = wait.until(EC.visibility_of_element_located((By.ID, "username")))
    user.clear()
    user.send_keys("tomsmith")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    flash = wait.until(EC.visibility_of_element_located((By.ID, "flash")))
    assert "logged into" in flash.text.lower() or "invalid" in flash.text.lower()`,
    ),
    ts(
      "locators.spec.ts",
      `import { By, until } from 'selenium-webdriver';

test('findElement strategies', async () => {
  await driver.get('https://the-internet.herokuapp.com/login');
  const user = await driver.wait(until.elementLocated(By.id('username')), 10_000);
  await user.sendKeys('tomsmith');
  await driver.findElement(By.css('button[type=submit]')).click();
  const flash = await driver.wait(until.elementLocated(By.id('flash')), 10_000);
  expect((await flash.getText()).toLowerCase()).toMatch(/logged into|invalid/);
});`,
    ),
  ],
  "selenium.waits": [
    py(
      "test_waits.py",
      `from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_fluent_wait_for_dynamic_content(driver):
    driver.get("https://the-internet.herokuapp.com/dynamic_loading/1")
    driver.find_element(By.CSS_SELECTOR, "#start button").click()
    finish = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.ID, "finish"))
    )
    assert "Hello World" in finish.text`,
    ),
    ts(
      "waits.spec.ts",
      `import { By, until } from 'selenium-webdriver';

test('explicit wait beats sleep', async () => {
  await driver.get('https://the-internet.herokuapp.com/dynamic_loading/1');
  await driver.findElement(By.css('#start button')).click();
  const finish = await driver.wait(until.elementLocated(By.id('finish')), 15_000);
  await driver.wait(until.elementIsVisible(finish), 15_000);
  expect(await finish.getText()).toContain('Hello World');
});`,
    ),
  ],
  "selenium.patterns": [
    py(
      "pages/login_page.py",
      `from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def open(self) -> None:
        self.driver.get("/login")

    def sign_in(self, email: str, password: str) -> None:
        self.wait.until(EC.visibility_of_element_located((By.NAME, "email"))).send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()`,
    ),
    ts(
      "pages/login.page.ts",
      `import { By, until, type WebDriver } from 'selenium-webdriver';

export class LoginPage {
  constructor(private driver: WebDriver) {}
  async open() { await this.driver.get('/login'); }
  async signIn(email: string, password: string) {
    const emailEl = await this.driver.wait(until.elementLocated(By.name('email')), 10_000);
    await emailEl.sendKeys(email);
    await this.driver.findElement(By.name('password')).sendKeys(password);
    await this.driver.findElement(By.css('button[type=submit]')).click();
  }
}`,
    ),
  ],

  "cypress.visit": [
    ts(
      "visit.advanced.cy.ts",
      `describe('advanced visit', () => {
  it('injects auth cookie before load', () => {
    cy.setCookie('session', Cypress.env('SESSION_TOKEN'), { httpOnly: true });
    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('feature:newNav', 'on');
      },
    });
    cy.location('pathname').should('eq', '/dashboard');
    cy.get('[data-cy=welcome]').should('be.visible');
  });
});`,
    ),
    py(
      "test_visit_companion.py",
      `# Companion API check before Cypress UI visit (pytest + httpx)
import httpx

def test_dashboard_requires_session():
    r = httpx.get("http://localhost:3000/api/me", cookies={"session": "bad"})
    assert r.status_code in (401, 403)`,
    ),
  ],
  "cypress.get": [
    ts(
      "get.advanced.cy.ts",
      `it('retries get + within scoped root', () => {
  cy.visit('/inbox');
  cy.get('[data-cy=thread-list]').within(() => {
    cy.contains('[data-cy=thread]', 'Refund').click();
  });
  cy.get('[data-cy=thread-detail]').should('contain', 'Refund');
  cy.get('[data-cy=reply]').type('Looking into this{enter}');
});`,
    ),
  ],
  "cypress.intercept": [
    ts(
      "intercept.advanced.cy.ts",
      `it('stubs GraphQL + asserts outgoing variables', () => {
  cy.intercept('POST', '/graphql', (req) => {
    const { operationName, variables } = req.body;
    if (operationName === 'GetUser') {
      expect(variables.id).to.match(/^user_/);
      req.reply({ fixture: 'user.json' });
    }
  }).as('getUser');

  cy.visit('/profile');
  cy.wait('@getUser').its('response.statusCode').should('eq', 200);
  cy.get('[data-cy=email]').should('contain', '@');
});`,
    ),
    py(
      "test_contract_for_intercept.py",
      `"""Keep Cypress fixtures honest: validate fixture schema in Python."""
from pathlib import Path
import json

def test_user_fixture_schema():
    data = json.loads(Path("cypress/fixtures/user.json").read_text())
    assert "id" in data and "email" in data
    assert "@" in data["email"]`,
    ),
  ],
  "cypress.patterns": [
    ts(
      "support/commands.ts",
      `declare global {
  namespace Cypress {
    interface Chainable {
      loginAs(role: 'admin' | 'user'): Chainable<void>;
    }
  }
}

Cypress.Commands.add('loginAs', (role) => {
  cy.session(role, () => {
    cy.request('POST', '/api/test/login', { role }).then((res) => {
      window.localStorage.setItem('token', res.body.token);
    });
  });
});`,
    ),
    py(
      "cypress_fixture_guard.py",
      `"""Keep Cypress fixtures aligned with API contracts (pytest companion)."""
from pathlib import Path
import json

def test_login_fixture_shape():
    data = json.loads(Path("cypress/fixtures/user.json").read_text())
    assert "token" in data or "email" in data`,
    ),
  ],
  "cypress.delivery": [
    ts(
      "cypress.config.ts",
      `import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: process.env.BASE_URL ?? 'http://127.0.0.1:3000',
    specPattern: 'cypress/e2e/**/*.cy.ts',
    video: !!process.env.CI,
    retries: { runMode: 2, openMode: 0 },
    setupNodeEvents(on, config) {
      on('after:spec', (_spec, results) => {
        if (results?.stats?.failures) {
          console.error('spec failed', results.stats.failures);
        }
      });
      return config;
    },
  },
});`,
    ),
    py(
      "run_cypress_ci.py",
      `import os
import subprocess

def test_cypress_ci_command():
    cmd = os.getenv("CYPRESS_CMD", "npx cypress run --browser chrome")
    assert "cypress" in cmd
    # Uncomment in real CI: subprocess.check_call(cmd, shell=True)`,
    ),
  ],
  "accelq.actions": [
    py(
      "accelq_actions_model.py",
      `"""Model AccelQ-style reusable actions as Python callables for local dry-runs."""
from dataclasses import dataclass

@dataclass
class ActionContext:
    base_url: str
    user: str

def action_open_claim(ctx: ActionContext, claim_id: str) -> dict:
    # In AccelQ this is a visual action; here we document the contract.
    assert claim_id.startswith("CLM-")
    return {"url": f"{ctx.base_url}/claims/{claim_id}", "user": ctx.user}`,
    ),
    ts(
      "accelq-action-contract.ts",
      `/** Contract for an AccelQ reusable business action */
export type ActionContext = { baseUrl: string; user: string };

export function openClaim(ctx: ActionContext, claimId: string) {
  if (!/^CLM-\\d+$/.test(claimId)) throw new Error('invalid claim id');
  return { url: \`\${ctx.baseUrl}/claims/\${claimId}\`, user: ctx.user };
}`,
    ),
  ],
  "accelq.data-driven": [
    py(
      "test_accelq_data_driven.py",
      `import csv
import pytest
from pathlib import Path

rows = list(csv.DictReader(Path("data/claims.csv").open()))

@pytest.mark.parametrize("row", rows, ids=[r["claim_id"] for r in rows])
def test_claim_row_shape(row):
    assert row["claim_id"].startswith("CLM-")
    assert float(row["amount"]) >= 0`,
    ),
    ts(
      "data-driven.spec.ts",
      `import { readFileSync } from 'node:fs';
import { parse } from 'csv-parse/sync';

const rows = parse(readFileSync('data/claims.csv'), { columns: true }) as Array<{
  claim_id: string; amount: string;
}>;

test.each(rows)('claim $claim_id is well-formed', (row) => {
  expect(row.claim_id).toMatch(/^CLM-/);
  expect(Number(row.amount)).toBeGreaterThanOrEqual(0);
});`,
    ),
  ],
  "accelq.ci-hooks": [
    ts(
      "scripts/trigger-accelq.ts",
      `/** CI hook pattern: trigger AccelQ job and fail the pipeline on non-zero. */
import { execFileSync } from 'node:child_process';

const jobId = process.env.ACCELQ_JOB_ID;
if (!jobId) throw new Error('ACCELQ_JOB_ID required');

execFileSync('accelq-cli', ['run', '--job', jobId, '--wait'], { stdio: 'inherit' });`,
    ),
    py(
      "scripts/trigger_accelq.py",
      `import os
import subprocess
import sys

job = os.environ.get("ACCELQ_JOB_ID")
if not job:
    sys.exit("ACCELQ_JOB_ID required")

subprocess.check_call(["accelq-cli", "run", "--job", job, "--wait"])`,
    ),
  ],

  "cucumber.feature": [
    ts(
      "features/login.feature",
      `Feature: Sign in
  Scenario Outline: Valid credentials
    Given I am on the login page
    When I sign in as "<email>" with password "<password>"
    Then I see the dashboard

    Examples:
      | email            | password |
      | qa@example.com   | Secret1! |
      | lead@example.com | Secret2! |`,
    ),
    py(
      "features/login.feature",
      `# Same Gherkin consumed by behave / pytest-bdd
Feature: Sign in
  Scenario: Valid credentials
    Given I am on the login page
    When I sign in as "qa@example.com"
    Then I see the dashboard`,
    ),
  ],
  "cucumber.step-defs": [
    ts(
      "steps/login.steps.ts",
      `import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import type { IWorld } from '../support/world';

Given('I am on the login page', async function (this: IWorld) {
  await this.page.goto('/login');
});

When('I sign in as {string} with password {string}', async function (this: IWorld, email, password) {
  await this.page.getByLabel('Email').fill(email);
  await this.page.getByLabel('Password').fill(password);
  await this.page.getByRole('button', { name: 'Sign in' }).click();
});

Then('I see the dashboard', async function (this: IWorld) {
  await expect(this.page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});`,
    ),
    py(
      "steps/test_login_bdd.py",
      `from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, expect

scenarios("../features/login.feature")

@given("I am on the login page")
def on_login(page: Page):
    page.goto("/login")

@when(parsers.parse('I sign in as "{email}"'))
def sign_in(page: Page, email: str):
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill("Secret1!")
    page.get_by_role("button", name="Sign in").click()

@then("I see the dashboard")
def see_dashboard(page: Page):
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()`,
    ),
  ],
  "cucumber.hooks": [
    ts(
      "support/hooks.ts",
      `import { Before, After, Status } from '@cucumber/cucumber';
import type { IWorld } from './world';

Before(async function (this: IWorld) {
  this.page = await this.context.newPage();
});

After(async function (this: IWorld, { result }) {
  if (result?.status === Status.FAILED) {
    await this.page.screenshot({ path: \`artifacts/\${Date.now()}.png\` });
  }
  await this.page.close();
});`,
    ),
    py(
      "conftest_bdd.py",
      `import pytest
from playwright.sync_api import Page

@pytest.fixture(autouse=True)
def _screenshot_on_failure(request, page: Page):
    yield
    if request.node.rep_call.failed:
        page.screenshot(path=f"artifacts/{request.node.name}.png")`,
    ),
  ],

  "appium.create-session": [
    py(
      "test_android_session.py",
      `from appium import webdriver
from appium.options.android import UiAutomator2Options

def test_create_android_session():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Pixel_7"
    options.app = "/apps/demo.apk"
    options.no_reset = True
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    try:
        assert driver.session_id
        assert driver.capabilities.get("platformName") == "Android"
    finally:
        driver.quit()`,
    ),
    ts(
      "session.spec.ts",
      `import { remote } from 'webdriverio';

test('creates an Appium session', async () => {
  const driver = await remote({
    hostname: '127.0.0.1',
    port: 4723,
    capabilities: {
      platformName: 'Android',
      'appium:deviceName': 'Pixel_7',
      'appium:app': '/apps/demo.apk',
      'appium:automationName': 'UiAutomator2',
    },
  });
  try {
    expect(driver.sessionId).toBeTruthy();
  } finally {
    await driver.deleteSession();
  }
});`,
    ),
  ],
  "appium.find-element": [
    py(
      "test_mobile_locators.py",
      `from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_find_login_fields(driver):
    wait = WebDriverWait(driver, 15)
    email = wait.until(EC.presence_of_element_located(
        (AppiumBy.ACCESSIBILITY_ID, "email")
    ))
    email.send_keys("qa@example.com")
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().text("Sign in")').click()`,
    ),
    ts(
      "mobile-locators.spec.ts",
      `test('prefers accessibility ids', async () => {
  const email = await driver.$('~email');
  await email.setValue('qa@example.com');
  await driver.$('android=new UiSelector().text("Sign in")').click();
});`,
    ),
  ],
  "appium.gestures": [
    py(
      "test_gestures.py",
      `from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

def test_swipe_up(driver):
    size = driver.get_window_size()
    start = (size["width"] // 2, int(size["height"] * 0.8))
    end = (size["width"] // 2, int(size["height"] * 0.2))
    finger = PointerInput("touch", "finger")
    actions = ActionBuilder(driver, mouse=finger)
    actions.pointer_action.move_to_location(*start).pointer_down()
    actions.pointer_action.pause(0.2).move_to_location(*end).pointer_up()
    actions.perform()`,
    ),
    ts(
      "gestures.spec.ts",
      `test('swipe up via performActions', async () => {
  const { width, height } = await driver.getWindowSize();
  await driver.performActions([{
    type: 'pointer', id: 'finger', parameters: { pointerType: 'touch' },
    actions: [
      { type: 'pointerMove', duration: 0, x: width / 2, y: height * 0.8 },
      { type: 'pointerDown', button: 0 },
      { type: 'pointerMove', duration: 400, x: width / 2, y: height * 0.2 },
      { type: 'pointerUp', button: 0 },
    ],
  }]);
  await driver.releaseActions();
});`,
    ),
  ],

  "squish.object-names": [
    py(
      "squish_object_map.py",
      `"""Symbolic object names — keep GUI maps stable across builds."""
OBJECT_MAP = {
    "Login.Email": {"type": "QLineEdit", "name": "emailEdit"},
    "Login.Submit": {"type": "QPushButton", "text": "Sign in"},
}

def resolve(name: str) -> dict:
    if name not in OBJECT_MAP:
        raise KeyError(f"unknown symbolic name: {name}")
    return OBJECT_MAP[name]`,
    ),
    ts(
      "squish-object-map.ts",
      `export const objectMap = {
  'Login.Email': { type: 'QLineEdit', name: 'emailEdit' },
  'Login.Submit': { type: 'QPushButton', text: 'Sign in' },
} as const;

export function resolve(name: keyof typeof objectMap) {
  return objectMap[name];
}`,
    ),
  ],
  "squish.bdd": [
    py(
      "test_squish_bdd_bridge.py",
      `# Bridge Squish BDD scenarios to pytest markers for CI reporting
import pytest

@pytest.mark.bdd
@pytest.mark.parametrize("scenario", ["valid_login", "locked_user"])
def test_squish_scenario_registered(scenario):
    assert scenario in {"valid_login", "locked_user", "empty_password"}`,
    ),
    ts(
      "squish-bdd-bridge.spec.ts",
      `const scenarios = ['valid_login', 'locked_user'] as const;
test.each(scenarios)('registers Squish BDD scenario %s', (scenario) => {
  expect(scenario.length).toBeGreaterThan(3);
});`,
    ),
  ],
  "squish.vp": [
    py(
      "test_verification_point.py",
      `"""Verification points: compare property bags, not raw screenshots only."""
def assert_vp(actual: dict, expected: dict, ignore: set[str] | None = None):
    ignore = ignore or set()
    for key, value in expected.items():
        if key in ignore:
            continue
        assert actual.get(key) == value, f"{key}: {actual.get(key)!r} != {value!r}"

def test_button_vp():
    assert_vp({"text": "Sign in", "enabled": True}, {"text": "Sign in", "enabled": True})`,
    ),
    ts(
      "verification-point.spec.ts",
      `function assertVp(actual: Record<string, unknown>, expected: Record<string, unknown>) {
  for (const [k, v] of Object.entries(expected)) {
    expect(actual[k], k).toEqual(v);
  }
}

test('button verification point', () => {
  assertVp({ text: 'Sign in', enabled: true }, { text: 'Sign in', enabled: true });
});`,
    ),
  ],
};
