export interface CodeSample {
  readonly language: string;
  readonly filename: string;
  readonly code: string;
}

export interface LessonSection {
  readonly heading: string;
  readonly body: string;
  readonly bullets?: readonly string[];
  readonly code?: CodeSample;
}

export interface Lesson {
  readonly slug: string;
  readonly title: string;
  readonly summary: string;
  readonly track: CurriculumTrackId;
  readonly minutes: number;
  readonly tip: readonly string[];
  readonly sections: readonly LessonSection[];
  readonly relatedRepoPaths: readonly string[];
}

export type CurriculumTrackId =
  | "framework"
  | "foundations"
  | "evals"
  | "agents"
  | "mcp"
  | "industry";

export interface CurriculumTrack {
  readonly id: CurriculumTrackId;
  readonly title: string;
  readonly description: string;
  readonly lessons: readonly Lesson[];
}

export interface BentoTopic {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly href: string;
  readonly accent: "cyan" | "teal" | "slate" | "mint";
  readonly span: "wide" | "tall" | "normal";
}
