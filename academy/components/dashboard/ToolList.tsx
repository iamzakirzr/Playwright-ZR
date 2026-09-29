"use client";

import { ToolBentoCard } from "@/components/cards/tool-card";
import type { AcademyTool, ToolCategoryId } from "@/types/tools";

export function ToolList({
  categoryId,
  tools,
}: Readonly<{
  categoryId: ToolCategoryId;
  tools: readonly AcademyTool[];
}>): React.JSX.Element {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {tools.map((tool, index) => (
        <ToolBentoCard key={tool.id} categoryId={categoryId} tool={tool} index={index} />
      ))}
    </div>
  );
}
