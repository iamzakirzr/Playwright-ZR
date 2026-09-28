import { notFound } from "next/navigation";
import { AppShell } from "@/components/dashboard/AppShell";
import { ToolList } from "@/components/dashboard/ToolList";
import { getCategory, toolCategories } from "@/lib/tools-catalog";
import { categoryMeta } from "@/lib/category-meta";

export function generateStaticParams(): { category: string }[] {
  return toolCategories.map((category) => ({ category: category.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string }>;
}): Promise<{ title: string }> {
  const { category: categoryId } = await params;
  const category = getCategory(categoryId);
  return { title: category?.title ?? "Tools" };
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ category: string }>;
}): Promise<React.JSX.Element> {
  const { category: categoryId } = await params;
  const category = getCategory(categoryId);
  if (!category) {
    notFound();
  }
  const meta = categoryMeta[category.id];

  return (
    <AppShell>
      <main id="main" className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-border bg-secondary/80 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
            {meta.difficulty}
          </span>
          <span className="rounded-full border border-border bg-secondary/80 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
            {category.tools.length} tools
          </span>
        </div>
        <h1 className="font-display mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
          {category.title}
        </h1>
        <p className="mt-3 max-w-2xl text-muted-foreground leading-relaxed">{category.summary}</p>
        <div className="mt-8">
          <ToolList categoryId={category.id} tools={category.tools} />
        </div>
      </main>
    </AppShell>
  );
}
