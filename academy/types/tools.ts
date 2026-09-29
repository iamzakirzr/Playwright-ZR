import type { CodeSample, LessonSection } from "@/types/curriculum";

export type ToolCategoryId =
  | "test-automation"
  | "frameworks"
  | "api-performance"
  | "databases"
  | "cloud-cicd"
  | "salesforce"
  | "ai-evals"
  | "collaboration";

export interface LearningCall {
  readonly id: string;
  /** Official API / concept name from the vendor docs */
  readonly signature: string;
  readonly summary: string;
  readonly why: string;
  /** Deep-link into the tool's original documentation (reference only) */
  readonly docsUrl: string;
}

export interface AcademyTool {
  readonly id: string;
  readonly name: string;
  readonly summary: string;
  /** Landing page for the tool's official docs (reference) */
  readonly docsUrl: string;
  readonly docsLabel: string;
  readonly calls: readonly LearningCall[];
}

export interface ToolCategory {
  readonly id: ToolCategoryId;
  readonly title: string;
  readonly summary: string;
  readonly tools: readonly AcademyTool[];
}

/** On-site lesson for a tool course — primary learning surface */
export interface ToolGuide {
  readonly id: string;
  readonly title: string;
  readonly summary: string;
  readonly minutes: number;
  readonly order: number;
  readonly tip: readonly string[];
  readonly sections: readonly LessonSection[];
  /** Vendor deep-link kept as secondary reference */
  readonly docsUrl: string;
  readonly docsLabel: string;
  readonly kind: "overview" | "concept" | "practice";
  readonly signature?: string;
  readonly code?: CodeSample;
}

export interface ToolCourse {
  readonly categoryId: ToolCategoryId;
  readonly categoryTitle: string;
  readonly tool: AcademyTool;
  readonly guides: readonly ToolGuide[];
  readonly relatedLessonSlugs: readonly string[];
}
