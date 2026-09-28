import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { AcademyTool, ToolCategoryId } from "@/types/tools";

export function ToolList({
  categoryId,
  tools,
}: Readonly<{
  categoryId: ToolCategoryId;
  tools: readonly AcademyTool[];
}>): React.JSX.Element {
  return (
    <ul className="space-y-3">
      {tools.map((tool) => (
        <li key={tool.id}>
          <Link
            href={`/tools/${categoryId}/${tool.id}`}
            className="flex items-start gap-3 rounded-2xl border border-border/70 bg-card px-4 py-4 transition-colors hover:border-primary/35"
          >
            <span className="min-w-0 flex-1">
              <span className="block font-display text-lg font-semibold tracking-tight">
                {tool.name}
              </span>
              <span className="mt-1 block text-sm text-muted-foreground">{tool.summary}</span>
              <span className="mt-2 block font-[family-name:var(--font-code)] text-xs text-primary">
                {tool.repoPath} · {tool.calls.length} calls
              </span>
            </span>
            <ArrowUpRight className="mt-1 size-4 shrink-0 text-muted-foreground" />
          </Link>
        </li>
      ))}
    </ul>
  );
}
