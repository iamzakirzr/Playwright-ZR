import { mergeSamples } from "@/lib/samples/_helpers";
import { aiCollabSamples } from "@/lib/samples/ai-collab";
import { apiDataSamples } from "@/lib/samples/api-data";
import { cloudSalesforceSamples } from "@/lib/samples/cloud-salesforce";
import { frameworksSamples } from "@/lib/samples/frameworks";
import { testAutomationSamples } from "@/lib/samples/test-automation";
import type { CodeSample } from "@/types/curriculum";

const allSamples = mergeSamples(
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
