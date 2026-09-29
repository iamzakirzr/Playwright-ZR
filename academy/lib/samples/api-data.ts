import { bash, py, sql, ts, yaml } from "@/lib/samples/_helpers";
import type { CodeSample } from "@/types/curriculum";

export const apiDataSamples: Readonly<Record<string, readonly CodeSample[]>> = {
  "api-testing.status": [
    ts(
      "status.spec.ts",
      `import { test, expect } from '@playwright/test';

test('health returns 200 with latency budget', async ({ request }) => {
  const started = Date.now();
  const res = await request.get('/health');
  expect(res.status()).toBe(200);
  expect(Date.now() - started).toBeLessThan(500);
  expect(res.headers()['content-type']).toMatch(/json/);
});`,
    ),
    py(
      "test_status.py",
      `import time
import httpx

def test_health_status_and_latency():
    started = time.perf_counter()
    r = httpx.get("https://api.example.com/health", timeout=2.0)
    assert r.status_code == 200
    assert (time.perf_counter() - started) < 0.5
    assert "json" in r.headers.get("content-type", "")`,
    ),
  ],
  "api-testing.schema": [
    ts(
      "schema.spec.ts",
      `import { z } from 'zod';

const User = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  roles: z.array(z.enum(['admin', 'user'])).nonempty(),
});

test('user payload matches schema', async ({ request }) => {
  const res = await request.get('/users/me');
  expect(res.status()).toBe(200);
  User.parse(await res.json());
});`,
    ),
    py(
      "test_schema.py",
      `from pydantic import BaseModel, EmailStr, Field
import httpx

class User(BaseModel):
    id: str
    email: EmailStr
    roles: list[str] = Field(min_length=1)

def test_user_schema():
    data = httpx.get("https://api.example.com/users/me").json()
    user = User.model_validate(data)
    assert user.roles`,
    ),
  ],
  "api-testing.auth": [
    ts(
      "auth.spec.ts",
      `test('bearer auth round-trip', async ({ request }) => {
  const tokenRes = await request.post('/oauth/token', {
    form: { grant_type: 'client_credentials' },
  });
  expect(tokenRes.status()).toBe(200);
  const { access_token } = await tokenRes.json();

  const me = await request.get('/users/me', {
    headers: { Authorization: \`Bearer \${access_token}\` },
  });
  expect(me.status()).toBe(200);
});`,
    ),
    py(
      "test_auth.py",
      `import httpx

def test_bearer_round_trip():
    token = httpx.post(
        "https://api.example.com/oauth/token",
        data={"grant_type": "client_credentials"},
    ).json()["access_token"]
    me = httpx.get(
        "https://api.example.com/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200`,
    ),
  ],
  "api-testing.patterns": [
    ts(
      "api/client.ts",
      `export class ApiClient {
  constructor(private request: APIRequestContext, private token?: string) {}
  async get<T>(path: string): Promise<T> {
    const res = await this.request.get(path, {
      headers: this.token ? { Authorization: \`Bearer \${this.token}\` } : undefined,
    });
    if (!res.ok()) throw new Error(\`\${res.status()} \${path}\`);
    return res.json() as Promise<T>;
  }
}`,
    ),
    py(
      "api/client.py",
      `import httpx

class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self._client = httpx.Client(base_url=base_url)
        self._token = token

    def get(self, path: str) -> dict:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else None
        r = self._client.get(path, headers=headers)
        r.raise_for_status()
        return r.json()`,
    ),
  ],

  "jmeter.thread-group": [
    py(
      "run_jmeter.py",
      `"""Drive JMeter non-GUI from Python and assert summary metrics."""
import csv
import subprocess
from pathlib import Path

def test_thread_group_smoke(tmp_path: Path):
    jtl = tmp_path / "results.jtl"
    subprocess.check_call([
        "jmeter", "-n",
        "-t", "plans/smoke.jmx",
        "-l", str(jtl),
        "-Jusers=5", "-Jramp=5",
    ])
    rows = list(csv.DictReader(jtl.open()))
    assert rows, "no samples"
    error_rate = sum(r["success"] == "false" for r in rows) / len(rows)
    assert error_rate < 0.01`,
    ),
    ts(
      "run-jmeter.ts",
      `import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

execFileSync('jmeter', ['-n', '-t', 'plans/smoke.jmx', '-l', 'results.jtl', '-Jusers=5'], {
  stdio: 'inherit',
});
const lines = readFileSync('results.jtl', 'utf8').trim().split('\\n');
expect(lines.length).toBeGreaterThan(1);`,
    ),
  ],
  "jmeter.http-sampler": [
    py(
      "assert_sampler_plan.py",
      `"""Validate JMX-equivalent sampler config before running the plan."""
SAMPLER = {
    "method": "GET",
    "path": "/health",
    "assertions": [{"type": "response_code", "value": "200"}],
}

def test_sampler_contract():
    assert SAMPLER["method"] in {"GET", "POST", "PUT", "DELETE"}
    assert SAMPLER["path"].startswith("/")`,
    ),
    ts(
      "sampler-contract.ts",
      `export const sampler = {
  method: 'GET' as const,
  path: '/health',
  assertions: [{ type: 'response_code', value: '200' }],
};
test('sampler contract', () => {
  expect(sampler.path.startsWith('/')).toBe(true);
});`,
    ),
  ],
  "jmeter.listeners": [
    py(
      "parse_jtl.py",
      `import csv
from statistics import mean

def p95(values: list[float]) -> float:
    values = sorted(values)
    return values[int(0.95 * (len(values) - 1))]

def test_listener_thresholds():
    rows = list(csv.DictReader(open("results.jtl")))
    latencies = [float(r["elapsed"]) for r in rows]
    assert p95(latencies) < 500
    assert mean(latencies) < 200`,
    ),
    ts(
      "parse-jtl.ts",
      `import { readFileSync } from 'node:fs';
const rows = readFileSync('results.jtl', 'utf8').trim().split('\\n').slice(1);
const elapsed = rows.map((r) => Number(r.split(',')[1])).sort((a, b) => a - b);
const p95 = elapsed[Math.floor(0.95 * (elapsed.length - 1))];
test('p95 under budget', () => expect(p95).toBeLessThan(500));`,
    ),
  ],

  "k6.http-get": [
    ts(
      "smoke.js",
      `import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = { vus: 5, duration: '30s' };

export default function () {
  const res = http.get('https://test.k6.io');
  check(res, {
    'status 200': (r) => r.status === 200,
    'body present': (r) => !!r.body && r.body.length > 0,
  });
  sleep(1);
}`,
    ),
    py(
      "test_k6_companion.py",
      `import httpx

def test_target_reachable():
    r = httpx.get("https://test.k6.io", timeout=5)
    assert r.status_code == 200
    assert r.text`,
    ),
  ],
  "k6.thresholds": [
    ts(
      "thresholds.js",
      `export const options = {
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
  },
};`,
    ),
    py(
      "assert_k6_summary.py",
      `import json
from pathlib import Path

def test_thresholds_passed():
    summary = json.loads(Path("summary.json").read_text())
    # k6 --summary-export=summary.json
    assert summary["metrics"]["http_req_failed"]["values"]["rate"] < 0.01`,
    ),
  ],
  "k6.checks": [
    ts(
      "checks.js",
      `import http from 'k6/http';
import { check } from 'k6';

export default function () {
  const res = http.get('https://test.k6.io');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'proto is HTTP/2 or 1.1': (r) => String(r.proto).includes('HTTP'),
  });
}`,
    ),
  ],
  "k6.patterns": [
    ts(
      "scenarios.js",
      `export const options = {
  scenarios: {
    smoke: { executor: 'constant-vus', vus: 2, duration: '1m' },
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },
        { duration: '1m', target: 0 },
      ],
      startTime: '1m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};`,
    ),
  ],

  "artillery.scenarios": [
    yaml(
      "load.yml",
      `config:
  target: https://api.example.com
  phases:
    - duration: 60
      arrivalRate: 5
  defaults:
    headers:
      x-request-id: "qa-{{ $randomString() }}"
scenarios:
  - name: health
    flow:
      - get:
          url: /health
      - think: 1`,
    ),
    py(
      "test_artillery_config.py",
      `import yaml
from pathlib import Path

def test_phases_are_positive():
    cfg = yaml.safe_load(Path("load.yml").read_text())
    for phase in cfg["config"]["phases"]:
        assert phase["duration"] > 0
        assert phase["arrivalRate"] > 0`,
    ),
  ],
  "artillery.engines": [
    ts(
      "processor.ts",
      `export function setAuth(requestParams: any, context: any, ee: any, next: any) {
  requestParams.headers = {
    ...requestParams.headers,
    Authorization: \`Bearer \${context.vars.token}\`,
  };
  return next();
}`,
    ),
    py(
      "artillery_engine_notes.py",
      `# Prefer http engine for REST; playwright engine for UI journeys.
ENGINES = {"http", "playwright"}
assert "http" in ENGINES`,
    ),
  ],
  "artillery.processors": [
    ts(
      "processors.ts",
      `export function pickUser(context, events, done) {
  context.vars.email = \`user_\${Date.now()}@example.com\`;
  return done();
}`,
    ),
    py(
      "processors_contract.py",
      `def pick_user() -> str:
    import time
    return f"user_{int(time.time())}@example.com"`,
    ),
  ],

  "sql.select-join": [
    sql(
      "orders.sql",
      `SELECT o.id, c.email, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'paid'
  AND o.created_at >= NOW() - INTERVAL '7 days'
ORDER BY o.created_at DESC
LIMIT 100;`,
    ),
    py(
      "test_orders_query.py",
      `import psycopg

SQL = '''
SELECT o.id, c.email, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = %s
LIMIT 100
'''

def test_paid_orders(conn):
    with conn.cursor() as cur:
        cur.execute(SQL, ("paid",))
        rows = cur.fetchall()
    for order_id, email, total in rows:
        assert "@" in email
        assert total >= 0`,
    ),
    ts(
      "orders.query.ts",
      `import { sql } from './db';

export async function paidOrders() {
  return sql\`
    SELECT o.id, c.email, o.total_cents
    FROM orders o
    JOIN customers c ON c.id = o.customer_id
    WHERE o.status = 'paid'
    LIMIT 100\`;
}`,
    ),
  ],
  "sql.aggregates": [
    sql(
      "aggregates.sql",
      `SELECT date_trunc('day', created_at) AS day,
       COUNT(*) AS orders,
       SUM(total_cents)::bigint AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY 1
HAVING COUNT(*) > 0
ORDER BY 1 DESC;`,
    ),
    py(
      "test_aggregates.py",
      `def test_revenue_non_negative(rows):
    for day, orders, revenue in rows:
        assert orders > 0
        assert revenue >= 0`,
    ),
  ],
  "sql.constraints": [
    py(
      "test_constraints.py",
      `import psycopg
import pytest

def test_unique_email(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO customers(email) VALUES ('dup@example.com')")
        with pytest.raises(psycopg.errors.UniqueViolation):
            cur.execute("INSERT INTO customers(email) VALUES ('dup@example.com')")
            conn.commit()`,
    ),
    ts(
      "constraints.spec.ts",
      `test('unique email enforced', async () => {
  await db.query(\`INSERT INTO customers(email) VALUES ('dup@example.com')\`);
  await expect(db.query(\`INSERT INTO customers(email) VALUES ('dup@example.com')\`))
    .rejects.toThrow(/unique/i);
});`,
    ),
  ],

  "postgresql.psql": [
    bash(
      "psql-smoke.sh",
      `#!/usr/bin/env bash
set -euo pipefail
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT 1 AS ok;"`,
    ),
    py(
      "test_psql_connect.py",
      `import os
import psycopg

def test_select_one():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1`,
    ),
    ts(
      "db.smoke.ts",
      `import pg from 'pg';
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
test('select 1', async () => {
  const { rows } = await pool.query('SELECT 1 AS ok');
  expect(rows[0].ok).toBe(1);
});`,
    ),
  ],
  "postgresql.transactions": [
    py(
      "test_transactions.py",
      `def test_transfer_is_atomic(conn):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("UPDATE accounts SET balance = balance - 10 WHERE id = 1")
            cur.execute("UPDATE accounts SET balance = balance + 10 WHERE id = 2")
    with conn.cursor() as cur:
        cur.execute("SELECT SUM(balance) FROM accounts WHERE id IN (1,2)")
        assert cur.fetchone()[0] is not None`,
    ),
    ts(
      "transactions.ts",
      `export async function transfer(client: PoolClient, from: number, to: number, amount: number) {
  try {
    await client.query('BEGIN');
    await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, from]);
    await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, to]);
    await client.query('COMMIT');
  } catch (e) {
    await client.query('ROLLBACK');
    throw e;
  }
}`,
    ),
  ],
  "postgresql.explain": [
    sql(
      "explain.sql",
      `EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE customer_id = 42 AND status = 'paid';`,
    ),
    py(
      "test_explain.py",
      `def test_uses_index(plan: str):
    assert "Seq Scan" not in plan or "Index" in plan`,
    ),
  ],

  "snowflake.warehouses": [
    py(
      "test_warehouse.py",
      `import snowflake.connector
import os

def test_warehouse_alive():
    ctx = snowflake.connector.connect(
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        warehouse=os.environ["SNOWFLAKE_WH"],
    )
    cur = ctx.cursor()
    cur.execute("SELECT CURRENT_WAREHOUSE()")
    assert cur.fetchone()[0]`,
    ),
    ts(
      "warehouse.ts",
      `/** Use snowflake-sdk or REST; assert warehouse name from env in CI smoke. */
test('warehouse env present', () => {
  expect(process.env.SNOWFLAKE_WH).toBeTruthy();
});`,
    ),
  ],
  "snowflake.time-travel": [
    sql(
      "time_travel.sql",
      `SELECT COUNT(*) FROM orders AT (OFFSET => -60 * 60);
-- compare to current count for accidental delete detection`,
    ),
    py(
      "test_time_travel.py",
      `def test_offset_query_shape():
    sql = "SELECT COUNT(*) FROM orders AT (OFFSET => -3600)"
    assert "AT (OFFSET" in sql`,
    ),
  ],
  "snowflake.snowsql": [
    bash(
      "snowsql-smoke.sh",
      `snowsql -c qa -q "SELECT 1"`,
    ),
    py(
      "test_snowsql_wrapper.py",
      `import subprocess

def test_snowsql_select_one():
    out = subprocess.check_output(["snowsql", "-c", "qa", "-q", "SELECT 1"], text=True)
    assert "1" in out`,
    ),
  ],
};
