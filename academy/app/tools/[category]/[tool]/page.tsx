import Link from "next/link";
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
      <main id="main" className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        <p className="text-sm text-muted-foreground">
          <Link href="/" className="text-primary hover:underline">
            Dashboard
          </Link>
          <span aria-hidden> / </span>
          <Link href={`/tools/${category.id}`} className="text-primary hover:underline">
            {category.title}
          </Link>
          <span aria-hidden> / </span>
          {tool.name}
        </p>
        <h1 className="font-display mt-3 text-3xl font-semibold tracking-tight">
          {tool.name}
        </h1>
        <p className="mt-3 text-muted-foreground leading-relaxed">{tool.summary}</p>
        <a
          href={tool.docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block text-sm font-medium text-primary hover:underline"
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
