import Link from "next/link";
import { ArrowRight, BookOpen, ClipboardCheck, Sparkles } from "lucide-react";
import type { ToolGuide } from "@/types/tools";
import { cn } from "@/lib/utils";

const kindIcon = {
  overview: Sparkles,
  concept: BookOpen,
  practice: ClipboardCheck,
} as const;

export function LearningCallList({
  categoryId,
  toolId,
  guides,
}: Readonly<{
  categoryId: string;
  toolId: string;
  guides: readonly ToolGuide[];
}>): React.JSX.Element {
  return (
    <ol className="space-y-3">
      {guides.map((guide, index) => {
        const Icon = kindIcon[guide.kind];
        const href = `/tools/${categoryId}/${toolId}/${guide.id}`;
        return (
          <li key={guide.id}>
            <Link
              href={href}
              className={cn(
                "bezel-card group flex flex-col gap-3 px-4 py-4 transition-colors sm:px-5",
                "hover:border-primary/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 flex-wrap items-center gap-2">
                  <span className="font-[family-name:var(--font-code)] text-xs text-muted-foreground">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background/60 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                    <Icon className="size-3" aria-hidden />
                    {guide.kind === "overview"
                      ? "Intro"
                      : guide.kind === "practice"
                        ? "Practice"
                        : "Guide"}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {guide.minutes} min
                  </span>
                </div>
                <ArrowRight
                  className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                  aria-hidden
                />
              </div>
              <div>
                <h3 className="font-display text-base font-semibold tracking-tight text-foreground group-hover:text-primary">
                  {guide.signature ?? guide.title}
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  {guide.summary}
                </p>
              </div>
              <span className="text-sm font-medium text-primary">
                Open guide →
              </span>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
