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
  /** Deep-link into the tool's original documentation */
  readonly docsUrl: string;
}

export interface AcademyTool {
  readonly id: string;
  readonly name: string;
  readonly summary: string;
  /** Landing page for the tool's official docs */
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
