import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { ToolCategory } from "@/types/tools";

export function CategoryCard({
  category,
}: Readonly<{
  category: ToolCategory;
}>): React.JSX.Element {
  const callCount = category.tools.reduce((sum, tool) => sum + tool.calls.length, 0);

  return (
    <Link
      href={`/tools/${category.id}`}
      className="group flex flex-col rounded-2xl border border-border/80 bg-card p-5 transition-colors hover:border-primary/40 hover:bg-secondary/40"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-display text-xl font-semibold tracking-tight group-hover:text-primary">
          {category.title}
        </h2>
        <ArrowRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
      </div>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">
        {category.summary}
      </p>
      <p className="mt-4 text-xs font-medium tracking-wide text-ink-soft uppercase">
        {category.tools.length} tools · {callCount} learning calls
      </p>
    </Link>
  );
}
