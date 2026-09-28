export type ToolCategoryId =
  | "ui"
  | "api"
  | "db"
  | "ai-evals"
  | "rag"
  | "agents-mcp"
  | "mobile";

export interface LearningCall {
  readonly id: string;
  readonly signature: string;
  readonly summary: string;
  readonly why: string;
  readonly repoPath: string;
  readonly relatedTest?: string;
  readonly lessonSlug?: string;
}

export interface AcademyTool {
  readonly id: string;
  readonly name: string;
  readonly summary: string;
  readonly repoPath: string;
  readonly calls: readonly LearningCall[];
}

export interface ToolCategory {
  readonly id: ToolCategoryId;
  readonly title: string;
  readonly summary: string;
  readonly tools: readonly AcademyTool[];
}
