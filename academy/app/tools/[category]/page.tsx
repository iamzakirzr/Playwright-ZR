import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/dashboard/AppShell";
import { ToolList } from "@/components/dashboard/ToolList";
import { getCategory, toolCategories } from "@/lib/tools-catalog";

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

  return (
    <AppShell>
      <main id="main" className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        <p className="text-sm text-muted-foreground">
          <Link href="/" className="text-primary hover:underline">
            Dashboard
          </Link>
          <span aria-hidden> / </span>
          {category.title}
        </p>
        <h1 className="font-display mt-3 text-3xl font-semibold tracking-tight">
          {category.title}
        </h1>
        <p className="mt-3 text-muted-foreground leading-relaxed">{category.summary}</p>
        <div className="mt-8">
          <ToolList categoryId={category.id} tools={category.tools} />
        </div>
      </main>
    </AppShell>
  );
}
