import { notFound } from "next/navigation";
import { AppShell } from "@/components/dashboard/AppShell";
import { LearningCallList } from "@/components/dashboard/LearningCallList";
import { getTool, toolCategories } from "@/lib/tools-catalog";

export function generateStaticParams(): { category: string; tool: string }[] {
  return toolCategories.flatMap((category) =>
    category.tools.map((tool) => ({
      category: category.id,
      tool: tool.id,
    })),
  );
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string; tool: string }>;
}): Promise<{ title: string }> {
  const { category, tool } = await params;
  const match = getTool(category, tool);
  return { title: match?.tool.name ?? "Tool" };
}

export default async function ToolPage({
  params,
}: {
  params: Promise<{ category: string; tool: string }>;
}): Promise<React.JSX.Element> {
  const { category: categoryId, tool: toolId } = await params;
  const match = getTool(categoryId, toolId);
  if (!match) {
    notFound();
  }

  const { category, tool } = match;

  return (
    <AppShell>
      <main id="main" className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {category.title}
        </p>
        <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          {tool.name}
        </h1>
        <p className="mt-3 text-muted-foreground leading-relaxed">{tool.summary}</p>
        <a
          href={tool.docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex text-sm font-medium text-primary hover:underline"
        >
          {tool.docsLabel} — official docs ↗
        </a>

        <h2 className="font-display mt-10 text-xl font-semibold tracking-tight">
          Learning focus
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Practice these APIs and concepts using the vendor documentation.
        </p>
        <div className="mt-6">
          <LearningCallList calls={tool.calls} />
        </div>
      </main>
    </AppShell>
  );
}
