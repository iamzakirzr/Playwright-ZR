import { mergeSamples } from "@/lib/samples/_helpers";
import { aiCollabSamples } from "@/lib/samples/ai-collab";
import { apiDataSamples } from "@/lib/samples/api-data";
import { generatedApiExamples } from "@/lib/samples/api-examples.generated";
import { cloudSalesforceSamples } from "@/lib/samples/cloud-salesforce";
import { buildConceptShellSamples } from "@/lib/samples/concept-shell";
import { buildCourseShellSamples } from "@/lib/samples/course-shell";
import { frameworksSamples } from "@/lib/samples/frameworks";
import { testAutomationSamples } from "@/lib/samples/test-automation";
import type { CodeSample } from "@/types/curriculum";

/**
 * Merge order (later wins):
 * course/concept shells → generated per-API examples → handcrafted maps.
 */
const allSamples = mergeSamples(
  buildCourseShellSamples(),
  buildConceptShellSamples(),
  generatedApiExamples,
  testAutomationSamples,
  frameworksSamples,
  apiDataSamples,
  cloudSalesforceSamples,
  aiCollabSamples,
);

/** Advanced TypeScript / Python samples keyed by `${toolId}.${guideId}` */
export function getToolSamples(toolId: string, guideId: string): readonly CodeSample[] {
  return allSamples[`${toolId}.${guideId}`] ?? [];
}

export function countSampleKeys(): number {
  return Object.keys(allSamples).length;
}
