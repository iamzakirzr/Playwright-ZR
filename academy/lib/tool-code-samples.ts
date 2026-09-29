import type { CodeSample } from "@/types/curriculum";

/** Optional inline examples keyed by `${toolId}.${guideOrCallId}` */
export const toolCodeSamples: Readonly<Record<string, CodeSample>> = {
  "playwright.goto": {
    language: "typescript",
    filename: "navigate.spec.ts",
    code: `import { test, expect } from '@playwright/test';

test('opens the app home', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/\\/$/);
});`,
  },
  "playwright.get-by-role": {
    language: "typescript",
    filename: "locators.spec.ts",
    code: `await page.getByRole('button', { name: 'Sign in' }).click();
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();`,
  },
  "playwright.expect": {
    language: "typescript",
    filename: "assert.spec.ts",
    code: `await expect(page.getByTestId('toast')).toBeVisible();
await expect(page.getByLabel('Email')).toHaveValue(/@/);`,
  },
  "selenium.get": {
    language: "java",
    filename: "Navigate.java",
    code: `driver.get("https://example.com");
Assertions.assertEquals("Example Domain", driver.getTitle());`,
  },
  "selenium.find-element": {
    language: "java",
    filename: "Locate.java",
    code: `WebElement email = driver.findElement(By.cssSelector("#email"));
email.sendKeys("qa@example.com");`,
  },
  "selenium.waits": {
    language: "java",
    filename: "Waits.java",
    code: `WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("ready")));`,
  },
  "cypress.visit": {
    language: "javascript",
    filename: "visit.cy.js",
    code: `cy.visit('/login');
cy.contains('h1', 'Sign in').should('be.visible');`,
  },
  "cypress.get": {
    language: "javascript",
    filename: "get.cy.js",
    code: `cy.get('[data-cy=email]').type('qa@example.com');
cy.get('[data-cy=submit]').click();`,
  },
  "cypress.intercept": {
    language: "javascript",
    filename: "intercept.cy.js",
    code: `cy.intercept('GET', '/api/user', { fixture: 'user.json' }).as('user');
cy.visit('/profile');
cy.wait('@user');`,
  },
  "cucumber.feature": {
    language: "gherkin",
    filename: "login.feature",
    code: `Feature: Sign in
  Scenario: Valid credentials
    Given I am on the login page
    When I sign in as "qa@example.com"
    Then I see the dashboard`,
  },
  "pytest.fixtures": {
    language: "python",
    filename: "conftest.py",
    code: `import pytest

@pytest.fixture
def api_client():
    client = ApiClient(base_url="https://api.example.com")
    yield client
    client.close()`,
  },
  "pytest.parametrize": {
    language: "python",
    filename: "test_status.py",
    code: `@pytest.mark.parametrize("code", [200, 201, 204])
def test_success_codes(code, api_client):
    assert api_client.ok_status(code)`,
  },
  "k6.http-get": {
    language: "javascript",
    filename: "smoke.js",
    code: `import http from 'k6/http';
import { check } from 'k6';

export default function () {
  const res = http.get('https://test.k6.io');
  check(res, { 'status is 200': (r) => r.status === 200 });
}`,
  },
  "k6.thresholds": {
    language: "javascript",
    filename: "thresholds.js",
    code: `export const options = {
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};`,
  },
  "api-testing.status": {
    language: "typescript",
    filename: "status.spec.ts",
    code: `const res = await request.get('/health');
expect(res.status()).toBe(200);`,
  },
  "api-testing.schema": {
    language: "typescript",
    filename: "schema.spec.ts",
    code: `const body = await res.json();
expect(body).toEqual(expect.objectContaining({
  id: expect.any(String),
  email: expect.stringMatching(/@/),
}));`,
  },
  "sql.select-join": {
    language: "sql",
    filename: "orders.sql",
    code: `SELECT o.id, c.email, o.total
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'paid';`,
  },
  "postgresql.transactions": {
    language: "sql",
    filename: "tx.sql",
    code: `BEGIN;
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
UPDATE accounts SET balance = balance + 10 WHERE id = 2;
COMMIT;`,
  },
  "docker.dockerfile": {
    language: "dockerfile",
    filename: "Dockerfile",
    code: `FROM mcr.microsoft.com/playwright:v1.48.0-jammy
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npx", "playwright", "test"]`,
  },
  "git.branch": {
    language: "bash",
    filename: "branch.sh",
    code: `git switch -c feat/login-tests
git status
git push -u origin HEAD`,
  },
  "azure-devops.yaml-pipeline": {
    language: "yaml",
    filename: "azure-pipelines.yml",
    code: `trigger:
  - main
pool:
  vmImage: ubuntu-latest
steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '20.x'
  - script: npm ci && npm test
    displayName: Run tests`,
  },
  "jenkins.pipeline": {
    language: "groovy",
    filename: "Jenkinsfile",
    code: `pipeline {
  agent any
  stages {
    stage('Test') {
      steps { sh 'npm ci && npm test' }
    }
  }
}`,
  },
  "deepeval.llm-test-case": {
    language: "python",
    filename: "test_rag.py",
    code: `from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

case = LLMTestCase(
    input="What is the refund policy?",
    actual_output=answer,
    retrieval_context=chunks,
)
assert_test(case, [FaithfulnessMetric()])`,
  },
  "ragas.faithfulness": {
    language: "python",
    filename: "eval_rag.py",
    code: `from ragas import evaluate
from ragas.metrics import faithfulness

result = evaluate(dataset, metrics=[faithfulness])
print(result)`,
  },
  "appium.create-session": {
    language: "javascript",
    filename: "session.js",
    code: `const driver = await remote({
  capabilities: {
    platformName: 'Android',
    'appium:deviceName': 'Pixel_7',
    'appium:app': '/apps/demo.apk',
  },
});`,
  },
  "webdriverio.browser-url": {
    language: "javascript",
    filename: "nav.e2e.js",
    code: `await browser.url('/checkout');
await expect(browser).toHaveUrl(expect.stringContaining('checkout'));`,
  },
  "mocha.describe-it": {
    language: "javascript",
    filename: "math.spec.js",
    code: `describe('cart total', () => {
  it('sums line items', () => {
    expect(total([{ price: 2 }, { price: 3 }])).to.equal(5);
  });
});`,
  },
  "testng.annotations": {
    language: "java",
    filename: "LoginTest.java",
    code: `@Test(groups = "smoke")
public void validLogin() {
  loginPage.signIn("qa@example.com", "secret");
  Assert.assertTrue(dashboard.isLoaded());
}`,
  },
  "nunit.test-case": {
    language: "csharp",
    filename: "StatusTests.cs",
    code: `[TestCase(200)]
[TestCase(201)]
public void SuccessStatuses(int code)
{
    Assert.That(IsSuccess(code), Is.True);
}`,
  },
  "robot.keywords": {
    language: "robotframework",
    filename: "login.robot",
    code: `*** Test Cases ***
Valid Login
    Open Browser To Login
    Input Credentials    qa@example.com    secret
    Dashboard Should Be Visible`,
  },
  "jmeter.thread-group": {
    language: "xml",
    filename: "thread-group.jmx",
    code: `<!-- Thread Group: users=50, ramp=30s, loops=1 -->
<!-- Pair with HTTP Request sampler + Summary Report listener -->`,
  },
  "artillery.scenarios": {
    language: "yaml",
    filename: "load.yml",
    code: `config:
  target: https://api.example.com
  phases:
    - duration: 60
      arrivalRate: 5
scenarios:
  - name: health
    flow:
      - get:
          url: /health`,
  },
  "flows.screen-flows": {
    language: "text",
    filename: "screen-flow-checklist.txt",
    code: `1. Map each screen to a user decision
2. Assert field visibility + required rules
3. Validate finish navigation + record updates`,
  },
  "langsmith.tracing": {
    language: "python",
    filename: "trace.py",
    code: `from langsmith import traceable

@traceable(name="answer_question")
def answer(question: str) -> str:
    return chain.invoke({"q": question})`,
  },
};
