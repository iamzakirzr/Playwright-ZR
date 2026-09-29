import type { AcademyTool, LearningCall } from "@/types/tools";

/** Clear, non-boilerplate walkthrough copy for each API lesson. */
export function walkthrough(tool: AcademyTool, call: LearningCall): {
  what: { body: string; bullets: string[] };
  steps: { body: string; bullets: string[] };
  mistakes: string[];
} {
  return {
    what: {
      body: `${call.summary} In ${tool.name}, you write or configure “${call.signature}” when ${uncapitalize(call.why)}`,
      bullets: [
        `API / concept: ${call.signature}`,
        `Plain language: ${call.summary}`,
        `Use it because: ${call.why}`,
        `Tool context: ${tool.summary}`,
      ],
    },
    steps: {
      body: `Follow this sequence so the example on this page is not just something you read — you prove “${call.signature}” works in a tiny experiment.`,
      bullets: [
        `Skim the signature: ${call.signature}`,
        "Open the coding examples below (TypeScript/Python or best-fit language).",
        "Type the happy-path example once without copy-paste.",
        "Change one input (URL, selector, payload, metric threshold) and re-run.",
        "Add one negative/failure path that should fail for a clear reason.",
        "Write a one-line note: when you would choose this API in a real suite.",
      ],
    },
    mistakes: [
      `Calling ${call.signature} without a readiness check / precondition`,
      "Copying the academy example without swapping env-specific values",
      "Asserting implementation details instead of the user-visible or contract outcome",
      "Skipping the negative path and calling the suite “done”",
      `Jumping to ${tool.docsLabel} before running the on-site example once`,
    ],
  };
}

function uncapitalize(value: string): string {
  if (!value) return value;
  return value.charAt(0).toLowerCase() + value.slice(1);
}
