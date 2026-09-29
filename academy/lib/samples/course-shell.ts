import { py, ts } from "@/lib/samples/_helpers";
import { toolCategories } from "@/lib/tools-catalog";
import type { CodeSample } from "@/types/curriculum";

/**
 * Fallback advanced TS/Python for patterns + delivery when a tool has no
 * handcrafted samples yet. Handcrafted maps always win via merge order.
 */
export function buildCourseShellSamples(): Record<string, readonly CodeSample[]> {
  const out: Record<string, CodeSample[]> = {};

  for (const category of toolCategories) {
    for (const tool of category.tools) {
      const concepts = tool.calls.map((c) => c.signature).join(", ");
      out[`${tool.id}.patterns`] = [
        ts(
          `${tool.id}.patterns.ts`,
          `/**
 * ${tool.name} — scalable suite pattern (${category.title})
 * Concepts in this course: ${concepts}
 */
export type ${toPascal(tool.id)}Context = {
  baseUrl: string;
  traceId: string;
};

export class ${toPascal(tool.id)}Session {
  constructor(private readonly ctx: ${toPascal(tool.id)}Context) {}

  /** Arrange: isolate data / auth for one scenario */
  async arrange(seed: Record<string, string>) {
    if (!this.ctx.baseUrl) throw new Error('baseUrl required');
    return { ...seed, traceId: this.ctx.traceId };
  }

  /** Act + assert helper — keep assertions on user-visible outcomes */
  assertOutcome(actual: unknown, expected: unknown, label: string) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
      throw new Error(\`[\${toolLabel(this.ctx)}] \${label}: expected \${JSON.stringify(expected)} got \${JSON.stringify(actual)}\`);
    }
  }
}

function toolLabel(ctx: ${toPascal(tool.id)}Context) {
  return \`\${ctx.traceId}@\${ctx.baseUrl}\`;
}

// Smoke: pattern module loads
export function smoke${toPascal(tool.id)}Pattern() {
  const session = new ${toPascal(tool.id)}Session({
    baseUrl: process.env.BASE_URL ?? 'http://127.0.0.1:3000',
    traceId: 'qa-smoke',
  });
  session.assertOutcome(1 + 1, 2, 'math sanity');
  return session;
}`,
        ),
        py(
          `${tool.id}_patterns.py`,
          `"""${tool.name} — scalable suite pattern (${category.title}).

Concepts in this course: ${concepts}
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os


@dataclass
class ${toPascal(tool.id)}Context:
    base_url: str
    trace_id: str


class ${toPascal(tool.id)}Session:
    def __init__(self, ctx: ${toPascal(tool.id)}Context) -> None:
        self.ctx = ctx

    def arrange(self, seed: dict[str, str]) -> dict[str, str]:
        if not self.ctx.base_url:
            raise ValueError("base_url required")
        return {**seed, "trace_id": self.ctx.trace_id}

    def assert_outcome(self, actual, expected, label: str) -> None:
        if actual != expected:
            raise AssertionError(
                f"[{self.ctx.trace_id}@{self.ctx.base_url}] {label}: "
                f"expected {json.dumps(expected)} got {json.dumps(actual)}"
            )


def smoke_${tool.id.replace("-", "_")}_pattern() -> ${toPascal(tool.id)}Session:
    session = ${toPascal(tool.id)}Session(
        ${toPascal(tool.id)}Context(
            base_url=os.getenv("BASE_URL", "http://127.0.0.1:3000"),
            trace_id="qa-smoke",
        )
    )
    session.assert_outcome(1 + 1, 2, "math sanity")
    return session`,
        ),
      ];

      out[`${tool.id}.delivery`] = [
        ts(
          `${tool.id}.delivery.ts`,
          `/**
 * ${tool.name} — CI delivery contract
 * Gate: smoke on PR, broader suite on main/nightly.
 */
export type ${toPascal(tool.id)}Gate = {
  command: string;
  blocksMerge: boolean;
  artifacts: string[];
};

export const ${toCamel(tool.id)}PrGate: ${toPascal(tool.id)}Gate = {
  command: process.env.${envKey(tool.id)}_CMD ?? 'npm test -- --grep=${tool.id}',
  blocksMerge: true,
  artifacts: ['reports/junit.xml', 'artifacts/**'],
};

export function assertGate(gate: ${toPascal(tool.id)}Gate) {
  if (!gate.command.trim()) throw new Error('${tool.name}: empty CI command');
  if (!gate.artifacts.length) throw new Error('${tool.name}: no artifacts configured');
}

assertGate(${toCamel(tool.id)}PrGate);`,
        ),
        py(
          `${tool.id}_delivery.py`,
          `"""${tool.name} — CI delivery contract.

PR: fast smoke. Main/nightly: broader regression. Always publish artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ${toPascal(tool.id)}Gate:
    command: str
    blocks_merge: bool
    artifacts: list[str]


${toCamel(tool.id)}_pr_gate = ${toPascal(tool.id)}Gate(
    command=os.getenv("${envKey(tool.id)}_CMD", "pytest -q -k ${tool.id}"),
    blocks_merge=True,
    artifacts=["reports/junit.xml", "artifacts/**"],
)


def assert_gate(gate: ${toPascal(tool.id)}Gate) -> None:
    if not gate.command.strip():
        raise ValueError("${tool.name}: empty CI command")
    if not gate.artifacts:
        raise ValueError("${tool.name}: no artifacts configured")


assert_gate(${toCamel(tool.id)}_pr_gate)`,
        ),
      ];
    }
  }

  return out;
}

function toPascal(id: string): string {
  return id
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

function toCamel(id: string): string {
  const pascal = toPascal(id);
  return pascal.charAt(0).toLowerCase() + pascal.slice(1);
}

function envKey(id: string): string {
  return id.replace(/-/g, "_").toUpperCase();
}
