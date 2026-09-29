import { bash, dockerfile, plain, py, ts, yaml } from "@/lib/samples/_helpers";
import type { CodeSample } from "@/types/curriculum";

export const cloudSalesforceSamples: Readonly<
  Record<string, readonly CodeSample[]>
> = {
  "azure-devops.yaml-pipeline": [
    yaml(
      "azure-pipelines.yml",
      `trigger:
  - main
pool:
  vmImage: ubuntu-latest
variables:
  NODE_VERSION: '20.x'
steps:
  - task: NodeTool@0
    inputs:
      versionSpec: $(NODE_VERSION)
  - script: |
      npm ci
      npm run test -- --reporter=junit --outputFile=reports/junit.xml
    displayName: Unit + API tests
  - task: PublishTestResults@2
    inputs:
      testResultsFiles: 'reports/junit.xml'
      failTaskOnFailedTests: true`,
    ),
    py(
      "validate_pipeline.py",
      `import yaml
from pathlib import Path

def test_pipeline_publishes_results():
    doc = yaml.safe_load(Path("azure-pipelines.yml").read_text())
    steps = doc["steps"]
    assert any(s.get("task") == "PublishTestResults@2" for s in steps if isinstance(s, dict))`,
    ),
  ],
  "azure-devops.pr-validation": [
    yaml(
      "pr-validation.yml",
      `pr:
  - main
jobs:
  - job: validate
    steps:
      - script: npm ci && npm run lint && npm test
        displayName: PR gate`,
    ),
    ts(
      "pr-gate.ts",
      `/** Local mirror of the PR validation command */
import { execSync } from 'node:child_process';
execSync('npm run lint && npm test', { stdio: 'inherit' });`,
    ),
  ],
  "azure-devops.environments": [
    py(
      "deploy_env.py",
      `import os

def target_environment(branch: str) -> str:
    if branch == "main":
        return "production"
    if branch.startswith("release/"):
        return "staging"
    return "ephemeral"

def test_mapping():
    assert target_environment("main") == "production"`,
    ),
    ts(
      "environments.ts",
      `export function targetEnvironment(branch: string) {
  if (branch === 'main') return 'production';
  if (branch.startsWith('release/')) return 'staging';
  return 'ephemeral';
}`,
    ),
  ],

  "jenkins.pipeline": [
    plain(
      "Jenkinsfile",
      `pipeline {
  agent { label 'qa-docker' }
  options { timestamps(); ansiColor('xterm') }
  stages {
    stage('Test') {
      steps { sh 'npm ci && npm test' }
    }
  }
  post {
    always { junit 'reports/*.xml' }
  }
}`,
    ),
    py(
      "trigger_jenkins.py",
      `import os
import requests

def trigger_job(job: str) -> int:
    url = f"{os.environ['JENKINS_URL']}/job/{job}/build"
    r = requests.post(url, auth=(os.environ["JENKINS_USER"], os.environ["JENKINS_TOKEN"]))
    return r.status_code

def test_trigger_accepts():
    assert trigger_job("qa-smoke") in {201, 302}`,
    ),
  ],
  "jenkins.agents": [
    py(
      "test_agent_label.py",
      `AGENT_LABELS = {"qa-docker", "qa-windows"}

def test_known_labels():
    assert "qa-docker" in AGENT_LABELS`,
    ),
    ts(
      "agents.ts",
      `export const agentLabels = ['qa-docker', 'qa-windows'] as const;`,
    ),
  ],
  "jenkins.plugins": [
    ts(
      "plugins-contract.ts",
      `export const requiredPlugins = ['workflow-aggregator', 'junit', 'pipeline-stage-view'];
test('plugin list non-empty', () => expect(requiredPlugins.length).toBeGreaterThan(2));`,
    ),
    py(
      "plugins.py",
      `REQUIRED = ["workflow-aggregator", "junit", "pipeline-stage-view"]
assert len(REQUIRED) >= 3`,
    ),
  ],

  "docker.dockerfile": [
    dockerfile(
      "Dockerfile",
      `FROM mcr.microsoft.com/playwright:v1.48.0-jammy
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npx", "playwright", "test", "--reporter=line"]`,
    ),
    dockerfile(
      "Dockerfile.python",
      `FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["pytest", "-q"]`,
    ),
  ],
  "docker.compose": [
    yaml(
      "docker-compose.yml",
      `services:
  app:
    build: .
    environment:
      DATABASE_URL: postgres://qa:qa@db:5432/qa
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: qa
      POSTGRES_USER: qa
      POSTGRES_DB: qa
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U qa"]
      interval: 5s
      retries: 5`,
    ),
    py(
      "test_compose_config.py",
      `import yaml
from pathlib import Path

def test_db_healthcheck():
    doc = yaml.safe_load(Path("docker-compose.yml").read_text())
    assert "healthcheck" in doc["services"]["db"]`,
    ),
  ],
  "docker.run": [
    bash(
      "run-tests.sh",
      `#!/usr/bin/env bash
set -euo pipefail
docker compose up -d --build
docker compose run --rm app
docker compose down -v`,
    ),
    py(
      "test_docker_run.py",
      `import subprocess

def test_image_builds():
    subprocess.check_call(["docker", "build", "-t", "qa-tests", "."])`,
    ),
  ],

  "aws.iam": [
    py(
      "test_iam_least_privilege.py",
      `POLICY = {
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": ["arn:aws:s3:::qa-artifacts/*"],
}

def test_no_wildcard_admin():
    assert POLICY["Action"] != ["*"]
    assert not any(a.endswith(":*") for a in POLICY["Action"])`,
    ),
    ts(
      "iam-policy.ts",
      `export const qaReadPolicy = {
  Effect: 'Allow',
  Action: ['s3:GetObject'],
  Resource: ['arn:aws:s3:::qa-artifacts/*'],
} as const;`,
    ),
  ],
  "aws.s3": [
    py(
      "test_s3_upload.py",
      `import boto3
import os

def test_put_and_get_artifact():
    s3 = boto3.client("s3")
    bucket = os.environ["QA_BUCKET"]
    key = "ci/smoke.txt"
    s3.put_object(Bucket=bucket, Key=key, Body=b"ok")
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    assert body == b"ok"`,
    ),
    ts(
      "s3.ts",
      `import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';

export async function putSmoke(bucket: string) {
  const s3 = new S3Client({});
  await s3.send(new PutObjectCommand({ Bucket: bucket, Key: 'ci/smoke.txt', Body: 'ok' }));
  const out = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: 'ci/smoke.txt' }));
  return out.Body;
}`,
    ),
  ],
  "aws.ecs-ec2": [
    py(
      "test_ecs_task_def.py",
      `TASK = {
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [{"name": "api", "essential": True}],
}

def test_task_has_essential_container():
    assert any(c.get("essential") for c in TASK["containerDefinitions"])`,
    ),
    ts(
      "ecs-task.ts",
      `export const task = {
  cpu: '256',
  memory: '512',
  containerDefinitions: [{ name: 'api', essential: true }],
};`,
    ),
  ],

  "azure.app-service": [
    py(
      "test_app_service_health.py",
      `import httpx
import os

def test_slot_health():
    base = os.environ["APP_SERVICE_URL"]
    r = httpx.get(f"{base}/health", timeout=5)
    assert r.status_code == 200`,
    ),
    ts(
      "app-service.health.ts",
      `test('app service health', async ({ request }) => {
  const res = await request.get(process.env.APP_SERVICE_URL + '/health');
  expect(res.status()).toBe(200);
});`,
    ),
  ],
  "azure.key-vault": [
    py(
      "test_key_vault.py",
      `from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

def test_secret_round_trip():
    client = SecretClient(os.environ["VAULT_URL"], DefaultAzureCredential())
    name = "qa-smoke-secret"
    client.set_secret(name, "value")
    assert client.get_secret(name).value == "value"`,
    ),
    ts(
      "key-vault.ts",
      `/** Read secrets in CI via env injection from Key Vault — never log values. */
export function requiredSecret(name: string) {
  const v = process.env[name];
  if (!v) throw new Error(\`missing secret \${name}\`);
  return v;
}`,
    ),
  ],
  "azure.monitor": [
    py(
      "test_monitor_query.py",
      `QUERY = "requests | where success == false | summarize count() by bin(timestamp, 5m)"

def test_query_mentions_requests():
    assert "requests" in QUERY`,
    ),
    ts(
      "monitor.ts",
      `export const failedRequests = \`
requests
| where success == false
| summarize count() by bin(timestamp, 5m)
\`;`,
    ),
  ],

  "git.branch": [
    bash(
      "branch.sh",
      `#!/usr/bin/env bash
set -euo pipefail
git switch -c "feat/qa-$(date +%s)"
git status --short`,
    ),
    py(
      "test_branch_name.py",
      `import re

def test_branch_convention():
    name = "feat/login-tests"
    assert re.match(r"^(feat|fix|chore)/[a-z0-9-]+$", name)`,
    ),
    ts(
      "branch.ts",
      `export function assertBranch(name: string) {
  if (!/^(feat|fix|chore)\\/[a-z0-9-]+$/.test(name)) {
    throw new Error('bad branch');
  }
}`,
    ),
  ],
  "git.pr-flow": [
    py(
      "pr_checklist.py",
      `CHECKS = ["lint", "unit", "api-smoke", "a11y"]

def test_required_checks():
    assert "unit" in CHECKS`,
    ),
    ts(
      "pr-flow.ts",
      `export const requiredChecks = ['lint', 'unit', 'api-smoke', 'a11y'] as const;`,
    ),
  ],
  "git.bisect": [
    bash(
      "bisect.sh",
      `git bisect start
git bisect bad HEAD
git bisect good v1.2.0
git bisect run npm test`,
    ),
    py(
      "bisect_run.py",
      `import subprocess
import sys

def main() -> int:
    return subprocess.call(["npm", "test"])

if __name__ == "__main__":
    sys.exit(main())`,
    ),
  ],

  "bitbucket.pipelines": [
    yaml(
      "bitbucket-pipelines.yml",
      `pipelines:
  default:
    - step:
        name: Test
        image: node:20
        script:
          - npm ci
          - npm test
        artifacts:
          - reports/**`,
    ),
    py(
      "test_bb_pipeline.py",
      `import yaml
from pathlib import Path

def test_has_test_step():
    doc = yaml.safe_load(Path("bitbucket-pipelines.yml").read_text())
    step = doc["pipelines"]["default"][0]["step"]
    assert any("npm test" in s for s in step["script"])`,
    ),
  ],
  "bitbucket.branch-perms": [
    ts(
      "branch-perms.ts",
      `export const mainPolicy = {
  requireApprovals: 1,
  requireSuccessfulBuilds: true,
  preventForcePush: true,
};`,
    ),
    py(
      "branch_perms.py",
      `MAIN_POLICY = {
    "requireApprovals": 1,
    "requireSuccessfulBuilds": True,
    "preventForcePush": True,
}`,
    ),
  ],
  "bitbucket.prs": [
    py(
      "test_pr_title.py",
      `import re

def test_conventional_title():
    title = "feat(api): add refund endpoint"
    assert re.match(r"^(feat|fix|chore)(\\(.+\\))?: .+", title)`,
    ),
    ts(
      "pr-title.ts",
      `export function assertPrTitle(title: string) {
  if (!/^(feat|fix|chore)(\\(.+\\))?: .+/.test(title)) throw new Error('title');
}`,
    ),
  ],

  "service-cloud.cases": [
    py(
      "test_cases_api.py",
      `import httpx
import os

def test_create_case():
    instance = os.environ["SF_INSTANCE"]
    token = os.environ["SF_TOKEN"]
    r = httpx.post(
        f"{instance}/services/data/v59.0/sobjects/Case",
        headers={"Authorization": f"Bearer {token}"},
        json={"Subject": "QA smoke", "Origin": "Web", "Status": "New"},
    )
    assert r.status_code in (200, 201)
    assert r.json()["id"]`,
    ),
    ts(
      "cases.ts",
      `export async function createCase(instance: string, token: string) {
  const res = await fetch(\`\${instance}/services/data/v59.0/sobjects/Case\`, {
    method: 'POST',
    headers: {
      Authorization: \`Bearer \${token}\`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ Subject: 'QA smoke', Origin: 'Web', Status: 'New' }),
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}`,
    ),
  ],
  "service-cloud.omni": [
    py(
      "test_omni_routing.py",
      `def route_skill(case: dict) -> str:
    if case.get("Priority") == "High":
        return "tier1_voice"
    return "tier2_chat"

def test_high_priority_route():
    assert route_skill({"Priority": "High"}) == "tier1_voice"`,
    ),
    ts(
      "omni.ts",
      `export function routeSkill(case_: { Priority?: string }) {
  return case_.Priority === 'High' ? 'tier1_voice' : 'tier2_chat';
}`,
    ),
  ],
  "service-cloud.api": [
    py(
      "test_soql.py",
      `import httpx, os, urllib.parse

def test_soql_cases():
    q = urllib.parse.quote("SELECT Id, Subject FROM Case LIMIT 5")
    r = httpx.get(
        f"{os.environ['SF_INSTANCE']}/services/data/v59.0/query?q={q}",
        headers={"Authorization": f"Bearer {os.environ['SF_TOKEN']}"},
    )
    assert r.status_code == 200
    assert "records" in r.json()`,
    ),
    ts(
      "soql.ts",
      `export async function queryCases(instance: string, token: string) {
  const q = encodeURIComponent('SELECT Id, Subject FROM Case LIMIT 5');
  const res = await fetch(\`\${instance}/services/data/v59.0/query?q=\${q}\`, {
    headers: { Authorization: \`Bearer \${token}\` },
  });
  return res.json();
}`,
    ),
  ],

  "experience-cloud.sites": [
    py(
      "test_site_public.py",
      `import httpx, os

def test_site_home():
    r = httpx.get(os.environ["EXP_CLOUD_URL"], follow_redirects=True, timeout=10)
    assert r.status_code < 500`,
    ),
    ts(
      "sites.spec.ts",
      `test('experience cloud home', async ({ page }) => {
  await page.goto(process.env.EXP_CLOUD_URL!);
  await expect(page.locator('body')).toBeVisible();
});`,
    ),
  ],
  "experience-cloud.auth": [
    py(
      "test_exp_auth.py",
      `def test_auth_url_has_client_id():
    url = "https://login.salesforce.com/services/oauth2/authorize?client_id=ABC"
    assert "client_id=" in url`,
    ),
    ts(
      "auth.ts",
      `export function authorizeUrl(clientId: string) {
  const u = new URL('https://login.salesforce.com/services/oauth2/authorize');
  u.searchParams.set('client_id', clientId);
  u.searchParams.set('response_type', 'code');
  return u.toString();
}`,
    ),
  ],
  "experience-cloud.components": [
    ts(
      "lwc-contract.ts",
      `/** Assert public LWC API surface used by QA selectors */
export const heroApi = { tag: 'c-hero', publicProps: ['title', 'ctaLabel'] as const };`,
    ),
    py(
      "test_lwc_contract.py",
      `HERO = {"tag": "c-hero", "publicProps": ["title", "ctaLabel"]}
assert "title" in HERO["publicProps"]`,
    ),
  ],

  "flows.record-triggered": [
    py(
      "test_flow_trigger.py",
      `def should_run_flow(record: dict, old: dict | None) -> bool:
    return record.get("Status") == "Closed" and (not old or old.get("Status") != "Closed")

def test_fires_on_close():
    assert should_run_flow({"Status": "Closed"}, {"Status": "New"})`,
    ),
    ts(
      "record-triggered.ts",
      `export function shouldRunFlow(record: { Status?: string }, old?: { Status?: string }) {
  return record.Status === 'Closed' && old?.Status !== 'Closed';
}`,
    ),
  ],
  "flows.screen-flows": [
    py(
      "test_screen_flow_steps.py",
      `STEPS = ["capture_details", "confirm", "finish"]

def test_order():
    assert STEPS[0] == "capture_details"
    assert STEPS[-1] == "finish"`,
    ),
    ts(
      "screen-flow.ts",
      `export const steps = ['capture_details', 'confirm', 'finish'] as const;`,
    ),
  ],
  "flows.debug": [
    py(
      "flow_debug.py",
      `def summarize_fault(fault: dict) -> str:
    return f"{fault.get('element')}: {fault.get('message')}"

def test_summary():
    assert "Decision" in summarize_fault({"element": "Decision", "message": "null input"})`,
    ),
    ts(
      "flow-debug.ts",
      `export function summarizeFault(fault: { element?: string; message?: string }) {
  return \`\${fault.element}: \${fault.message}\`;
}`,
    ),
  ],
};
