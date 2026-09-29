import type { ToolCategoryId } from "@/types/tools";

export const categoryMeta: Record<
  ToolCategoryId,
  { accent: string; glow: string; difficulty: "Foundation" | "Intermediate" | "Advanced"; cta: string }
> = {
  "test-automation": {
    accent: "from-sky-500/20 to-cyan-400/5",
    glow: "rgba(14,165,233,0.35)",
    difficulty: "Foundation",
    cta: "View roadmap",
  },
  frameworks: {
    accent: "from-indigo-500/20 to-blue-400/5",
    glow: "rgba(99,102,241,0.35)",
    difficulty: "Intermediate",
    cta: "View roadmap",
  },
  "api-performance": {
    accent: "from-amber-500/20 to-orange-400/5",
    glow: "rgba(245,158,11,0.35)",
    difficulty: "Intermediate",
    cta: "Launch practice",
  },
  databases: {
    accent: "from-emerald-500/20 to-teal-400/5",
    glow: "rgba(16,185,129,0.35)",
    difficulty: "Intermediate",
    cta: "View roadmap",
  },
  "cloud-cicd": {
    accent: "from-violet-500/20 to-fuchsia-400/5",
    glow: "rgba(139,92,246,0.35)",
    difficulty: "Advanced",
    cta: "View roadmap",
  },
  salesforce: {
    accent: "from-blue-500/20 to-sky-400/5",
    glow: "rgba(59,130,246,0.35)",
    difficulty: "Advanced",
    cta: "View roadmap",
  },
  "ai-evals": {
    accent: "from-emerald-400/25 to-lime-400/5",
    glow: "rgba(52,211,153,0.4)",
    difficulty: "Advanced",
    cta: "Launch sandbox",
  },
  collaboration: {
    accent: "from-rose-500/20 to-pink-400/5",
    glow: "rgba(244,63,94,0.3)",
    difficulty: "Foundation",
    cta: "View roadmap",
  },
};
