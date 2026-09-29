import { py, ts } from "@/lib/samples/_helpers";
import type { CodeSample } from "@/types/curriculum";

export const aiCollabSamples: Readonly<Record<string, readonly CodeSample[]>> = {
  "deepeval.llm-test-case": [
    py(
      "test_rag_case.py",
      `from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

def test_refund_answer(rag_answer, chunks):
    case = LLMTestCase(
        input="What is the refund policy?",
        actual_output=rag_answer,
        retrieval_context=chunks,
        expected_output="Refunds are available within 30 days.",
    )
    assert_test(case, [
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
    ])`,
    ),
    ts(
      "llm-test-case.ts",
      `/** Mirror DeepEval case shape for TypeScript harnesses / CI payloads */
export type LlmTestCase = {
  input: string;
  actualOutput: string;
  retrievalContext: string[];
  expectedOutput?: string;
};

export function buildRefundCase(answer: string, chunks: string[]): LlmTestCase {
  return {
    input: 'What is the refund policy?',
    actualOutput: answer,
    retrievalContext: chunks,
    expectedOutput: 'Refunds are available within 30 days.',
  };
}`,
    ),
  ],
  "deepeval.faithfulness": [
    py(
      "test_faithfulness.py",
      `from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

def test_faithfulness_threshold():
    metric = FaithfulnessMetric(threshold=0.75)
    case = LLMTestCase(
        input="hours",
        actual_output="We are open 9-5 on weekdays.",
        retrieval_context=["Hours: Mon-Fri 9am-5pm"],
    )
    metric.measure(case)
    assert metric.score is not None
    assert metric.score >= 0.75`,
    ),
    ts(
      "faithfulness.ts",
      `export function faithfulnessGate(score: number, threshold = 0.75) {
  if (score < threshold) throw new Error(\`faithfulness \${score} < \${threshold}\`);
}`,
    ),
  ],
  "deepeval.g-eval": [
    py(
      "test_geval.py",
      `from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase

correctness = GEval(
    name="Correctness",
    criteria="Determine if the output is factually correct given the expected output.",
    evaluation_params=["actual_output", "expected_output"],
    threshold=0.7,
)

def test_geval_correctness():
    case = LLMTestCase(
        input="2+2",
        actual_output="4",
        expected_output="4",
    )
    correctness.measure(case)
    assert correctness.score >= 0.7`,
    ),
  ],
  "deepeval.patterns": [
    py(
      "conftest_eval.py",
      `import pytest

@pytest.fixture(scope="session")
def eval_dataset():
    return [
        {"input": "refund window", "expected": "30 days"},
        {"input": "support hours", "expected": "9-5 weekdays"},
    ]`,
    ),
    ts(
      "dataset.ts",
      `export const evalDataset = [
  { input: 'refund window', expected: '30 days' },
  { input: 'support hours', expected: '9-5 weekdays' },
];`,
    ),
  ],

  "ragas.faithfulness": [
    py(
      "test_ragas_faithfulness.py",
      `from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness

def test_faithfulness_batch():
    ds = Dataset.from_dict({
        "question": ["What are hours?"],
        "answer": ["Open 9-5 weekdays"],
        "contexts": [["Hours: Mon-Fri 9am-5pm"]],
    })
    result = evaluate(ds, metrics=[faithfulness])
    assert result["faithfulness"] >= 0.7`,
    ),
    ts(
      "ragas-faithfulness.ts",
      `export type RagasRow = { question: string; answer: string; contexts: string[] };
export function assertFaithfulness(score: number) {
  if (score < 0.7) throw new Error('faithfulness below threshold');
}`,
    ),
  ],
  "ragas.context-precision": [
    py(
      "test_context_precision.py",
      `from ragas.metrics import context_precision
from datasets import Dataset
from ragas import evaluate

def test_context_precision():
    ds = Dataset.from_dict({
        "question": ["refund?"],
        "contexts": [["Refunds within 30 days", "Unrelated promo"]],
        "ground_truth": ["30 days"],
    })
    result = evaluate(ds, metrics=[context_precision])
    assert "context_precision" in result`,
    ),
  ],
  "ragas.answer-relevancy": [
    py(
      "test_answer_relevancy.py",
      `from ragas.metrics import answer_relevancy
from datasets import Dataset
from ragas import evaluate

def test_relevancy():
    ds = Dataset.from_dict({
        "question": ["What is the refund policy?"],
        "answer": ["You can refund within 30 days of purchase."],
    })
    result = evaluate(ds, metrics=[answer_relevancy])
    assert result["answer_relevancy"] >= 0.5`,
    ),
    ts(
      "relevancy.ts",
      `export function relevancyGate(score: number, threshold = 0.5) {
  return score >= threshold;
}`,
    ),
  ],

  "langsmith.tracing": [
    py(
      "trace_chain.py",
      `from langsmith import traceable
import os

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

@traceable(name="answer_question")
def answer(question: str, chain) -> str:
    return chain.invoke({"q": question})`,
    ),
    ts(
      "trace.ts",
      `import { traceable } from 'langsmith/traceable';

export const answer = traceable(
  async (question: string, chain: { invoke: (x: any) => Promise<string> }) =>
    chain.invoke({ q: question }),
  { name: 'answer_question' },
);`,
    ),
  ],
  "langsmith.datasets": [
    py(
      "test_dataset.py",
      `from langsmith import Client

def test_upsert_examples():
    client = Client()
    ds = client.create_dataset("qa-refunds")
    client.create_examples(
        inputs=[{"question": "refund window?"}],
        outputs=[{"answer": "30 days"}],
        dataset_id=ds.id,
    )`,
    ),
    ts(
      "datasets.ts",
      `import { Client } from 'langsmith';

export async function seedRefundDataset() {
  const client = new Client();
  const ds = await client.createDataset('qa-refunds');
  await client.createExamples({
    inputs: [{ question: 'refund window?' }],
    outputs: [{ answer: '30 days' }],
    datasetId: ds.id,
  });
}`,
    ),
  ],
  "langsmith.feedback": [
    py(
      "feedback.py",
      `from langsmith import Client

def attach_score(run_id: str, score: float) -> None:
    Client().create_feedback(run_id, key="correctness", score=score)`,
    ),
    ts(
      "feedback.ts",
      `import { Client } from 'langsmith';
export async function attachScore(runId: string, score: number) {
  await new Client().createFeedback(runId, 'correctness', { score });
}`,
    ),
  ],

  "rag.retrieval": [
    py(
      "test_retrieval.py",
      `def retrieve(index, query: str, k: int = 4) -> list[str]:
    return index.search(query, k=k)

def test_retrieval_k(index):
    hits = retrieve(index, "refund policy", k=4)
    assert 1 <= len(hits) <= 4
    assert any("refund" in h.lower() for h in hits)`,
    ),
    ts(
      "retrieval.ts",
      `export async function retrieve(
  index: { search: (q: string, k: number) => Promise<string[]> },
  query: string,
  k = 4,
) {
  const hits = await index.search(query, k);
  if (!hits.length) throw new Error('empty retrieval');
  return hits;
}`,
    ),
  ],
  "rag.goldens": [
    py(
      "goldens.py",
      `from pydantic import BaseModel

class Golden(BaseModel):
    question: str
    expected_answer: str
    must_include: list[str] = []

GOLDENS = [
    Golden(question="refund window?", expected_answer="30 days", must_include=["30"]),
]

def test_goldens_load():
    assert GOLDENS[0].must_include == ["30"]`,
    ),
    ts(
      "goldens.ts",
      `export type Golden = { question: string; expectedAnswer: string; mustInclude?: string[] };
export const goldens: Golden[] = [
  { question: 'refund window?', expectedAnswer: '30 days', mustInclude: ['30'] },
];`,
    ),
  ],
  "rag.abstention": [
    py(
      "test_abstention.py",
      `def should_abstain(confidence: float, max_context_score: float) -> bool:
    return confidence < 0.4 or max_context_score < 0.25

def test_abstain_on_low_confidence():
    assert should_abstain(0.2, 0.9)
    assert should_abstain(0.9, 0.1)
    assert not should_abstain(0.8, 0.8)`,
    ),
    ts(
      "abstention.ts",
      `export function shouldAbstain(confidence: number, maxContextScore: number) {
  return confidence < 0.4 || maxContextScore < 0.25;
}`,
    ),
  ],
  "rag.patterns": [
    py(
      "rag_pipeline.py",
      `def answer(query: str, retrieve, generate, judge) -> dict:
    ctx = retrieve(query)
    if not ctx:
        return {"answer": None, "abstain": True}
    text = generate(query, ctx)
    score = judge(query, text, ctx)
    return {"answer": text, "score": score, "abstain": score < 0.5}`,
    ),
    ts(
      "rag-pipeline.ts",
      `export async function answer(query: string, deps: {
  retrieve: (q: string) => Promise<string[]>;
  generate: (q: string, ctx: string[]) => Promise<string>;
  judge: (q: string, a: string, ctx: string[]) => Promise<number>;
}) {
  const ctx = await deps.retrieve(query);
  if (!ctx.length) return { answer: null, abstain: true };
  const text = await deps.generate(query, ctx);
  const score = await deps.judge(query, text, ctx);
  return { answer: text, score, abstain: score < 0.5 };
}`,
    ),
  ],

  "agentic-ai.tool-use": [
    py(
      "test_tool_use.py",
      `TOOLS = {"get_order": lambda order_id: {"id": order_id, "status": "shipped"}}

def agent_step(intent: str, order_id: str) -> dict:
    if intent == "order_status":
        return TOOLS["get_order"](order_id)
    raise ValueError("unknown intent")

def test_tool_routing():
    assert agent_step("order_status", "A1")["status"] == "shipped"`,
    ),
    ts(
      "tool-use.ts",
      `const tools = {
  getOrder: (orderId: string) => ({ id: orderId, status: 'shipped' as const }),
};

export function agentStep(intent: 'order_status', orderId: string) {
  if (intent === 'order_status') return tools.getOrder(orderId);
  throw new Error('unknown intent');
}`,
    ),
  ],
  "agentic-ai.trajectory": [
    py(
      "test_trajectory.py",
      `def score_trajectory(steps: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0
    matched = sum(1 for a, b in zip(steps, expected) if a == b)
    return matched / len(expected)

def test_exact_path():
    assert score_trajectory(["search", "open", "reply"], ["search", "open", "reply"]) == 1.0`,
    ),
    ts(
      "trajectory.ts",
      `export function scoreTrajectory(steps: string[], expected: string[]) {
  if (!expected.length) return 1;
  let matched = 0;
  for (let i = 0; i < expected.length; i++) if (steps[i] === expected[i]) matched++;
  return matched / expected.length;
}`,
    ),
  ],
  "agentic-ai.task-completion": [
    py(
      "test_task_completion.py",
      `def completed(result: dict) -> bool:
    return bool(result.get("success")) and not result.get("needs_human")

def test_completion_gate():
    assert completed({"success": True, "needs_human": False})
    assert not completed({"success": True, "needs_human": True})`,
    ),
    ts(
      "task-completion.ts",
      `export function completed(result: { success?: boolean; needsHuman?: boolean }) {
  return Boolean(result.success) && !result.needsHuman;
}`,
    ),
  ],

  "github-copilot.suggestions": [
    ts(
      "copilot-review.ts",
      `/** Treat Copilot output as untrusted — always add tests. */
export function sum(items: number[]) {
  return items.reduce((a, b) => a + b, 0);
}

test('sum', () => expect(sum([2, 3])).toBe(5));`,
    ),
    py(
      "test_copilot_suggestion.py",
      `def sum_items(items: list[int]) -> int:
    return sum(items)

def test_sum():
    assert sum_items([2, 3]) == 5`,
    ),
  ],
  "github-copilot.chat": [
    py(
      "prompt_template.py",
      `SYSTEM = "You are a senior QA engineer. Prefer Playwright locators by role."

def build_prompt(failure_log: str) -> str:
    return f"{SYSTEM}\\n\\nExplain root cause:\\n{failure_log[:4000]}"`,
    ),
    ts(
      "prompt-template.ts",
      `const SYSTEM = 'You are a senior QA engineer. Prefer Playwright locators by role.';
export function buildPrompt(failureLog: string) {
  return \`\${SYSTEM}\\n\\nExplain root cause:\\n\${failureLog.slice(0, 4000)}\`;
}`,
    ),
  ],
  "github-copilot.policies": [
    ts(
      "policies.ts",
      `export const policy = {
  allowPublicCode: false,
  blockSecrets: true,
  requireHumanReview: true,
};`,
    ),
    py(
      "policies.py",
      `POLICY = {"allowPublicCode": False, "blockSecrets": True, "requireHumanReview": True}
assert POLICY["requireHumanReview"]`,
    ),
  ],

  "ms-copilot.prompts": [
    py(
      "m365_prompt.py",
      `def grounding_prompt(question: str, snippets: list[str]) -> str:
    ctx = "\\n".join(f"- {s}" for s in snippets)
    return f"Use only this context:\\n{ctx}\\n\\nQuestion: {question}"`,
    ),
    ts(
      "m365-prompt.ts",
      `export function groundingPrompt(question: string, snippets: string[]) {
  const ctx = snippets.map((s) => \`- \${s}\`).join('\\n');
  return \`Use only this context:\\n\${ctx}\\n\\nQuestion: \${question}\`;
}`,
    ),
  ],
  "ms-copilot.grounding": [
    py(
      "test_grounding.py",
      `def grounded(answer: str, snippets: list[str]) -> bool:
    return any(s.lower() in answer.lower() or answer.lower() in s.lower() for s in snippets)

def test_grounded_answer():
    assert grounded("Refunds within 30 days", ["Refunds within 30 days of purchase"])`,
    ),
    ts(
      "grounding.ts",
      `export function grounded(answer: string, snippets: string[]) {
  const a = answer.toLowerCase();
  return snippets.some((s) => a.includes(s.toLowerCase()) || s.toLowerCase().includes(a));
}`,
    ),
  ],
  "ms-copilot.responsible": [
    ts(
      "responsible.ts",
      `export function redactSecrets(text: string) {
  return text.replace(/sk-[a-zA-Z0-9]+/g, '[REDACTED]');
}`,
    ),
    py(
      "responsible.py",
      `import re

def redact_secrets(text: str) -> str:
    return re.sub(r"sk-[a-zA-Z0-9]+", "[REDACTED]", text)`,
    ),
  ],

  "jira.workflows": [
    py(
      "test_jira_transition.py",
      `TRANSITIONS = {"To Do": ["In Progress"], "In Progress": ["In Review", "To Do"], "In Review": ["Done"]}

def can_transition(src: str, dest: str) -> bool:
    return dest in TRANSITIONS.get(src, [])

def test_happy_path():
    assert can_transition("To Do", "In Progress")
    assert not can_transition("To Do", "Done")`,
    ),
    ts(
      "workflows.ts",
      `const transitions: Record<string, string[]> = {
  'To Do': ['In Progress'],
  'In Progress': ['In Review', 'To Do'],
  'In Review': ['Done'],
};
export function canTransition(src: string, dest: string) {
  return (transitions[src] ?? []).includes(dest);
}`,
    ),
  ],
  "jira.jql": [
    py(
      "test_jql.py",
      `import os
import httpx

JQL = 'project = QA AND status = "In Progress" AND assignee = currentUser() ORDER BY updated DESC'

def test_jql_search():
    base = os.environ["JIRA_BASE"]
    r = httpx.get(
        f"{base}/rest/api/3/search",
        params={"jql": JQL, "maxResults": 5},
        auth=(os.environ["JIRA_USER"], os.environ["JIRA_TOKEN"]),
    )
    assert r.status_code == 200
    assert "issues" in r.json()`,
    ),
    ts(
      "jql.ts",
      `export const openMine =
  'project = QA AND status = "In Progress" AND assignee = currentUser() ORDER BY updated DESC';

export async function search(base: string, email: string, token: string) {
  const url = new URL('/rest/api/3/search', base);
  url.searchParams.set('jql', openMine);
  const res = await fetch(url, {
    headers: { Authorization: 'Basic ' + Buffer.from(\`\${email}:\${token}\`).toString('base64') },
  });
  return res.json();
}`,
    ),
  ],
  "jira.boards": [
    py(
      "boards.py",
      `COLUMNS = ["To Do", "In Progress", "In Review", "Done"]

def test_wip_limit():
    wip = {"In Progress": 3}
    assert wip["In Progress"] >= 1`,
    ),
    ts(
      "boards.ts",
      `export const columns = ['To Do', 'In Progress', 'In Review', 'Done'] as const;
export const wip = { 'In Progress': 3 };`,
    ),
  ],

  "stlc.strategy": [
    py(
      "strategy.py",
      `STRATEGY = {
    "levels": ["unit", "api", "ui", "exploratory"],
    "environments": ["ephemeral", "staging", "prod-readonly"],
}

def test_has_api_level():
    assert "api" in STRATEGY["levels"]`,
    ),
    ts(
      "strategy.ts",
      `export const strategy = {
  levels: ['unit', 'api', 'ui', 'exploratory'] as const,
  environments: ['ephemeral', 'staging', 'prod-readonly'] as const,
};`,
    ),
  ],
  "stlc.defect-mgmt": [
    py(
      "defects.py",
      `SEVERITY = ["S1", "S2", "S3", "S4"]

def prioritize(severity: str, customer_impact: bool) -> str:
    if severity == "S1" or customer_impact:
        return "P1"
    return "P3"

def test_p1():
    assert prioritize("S2", True) == "P1"`,
    ),
    ts(
      "defects.ts",
      `export function prioritize(severity: 'S1' | 'S2' | 'S3' | 'S4', customerImpact: boolean) {
  if (severity === 'S1' || customerImpact) return 'P1';
  return 'P3';
}`,
    ),
  ],
  "stlc.traceability": [
    py(
      "trace.py",
      `TRACE = [
    {"requirement": "REQ-1", "cases": ["TC-1", "TC-2"], "defects": []},
]

def coverage(rows=TRACE) -> float:
    covered = sum(1 for r in rows if r["cases"])
    return covered / len(rows)

def test_full_coverage():
    assert coverage() == 1.0`,
    ),
    ts(
      "trace.ts",
      `type Row = { requirement: string; cases: string[]; defects: string[] };
export function coverage(rows: Row[]) {
  return rows.filter((r) => r.cases.length).length / rows.length;
}`,
    ),
  ],
};
