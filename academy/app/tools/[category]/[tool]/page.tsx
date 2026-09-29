import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/dashboard/AppShell";
import { LearningCallList } from "@/components/dashboard/LearningCallList";
import { getLesson, getToolCourse } from "@/lib/tool-guides";
import { toolCategories } from "@/lib/tools-catalog";

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
  const course = getToolCourse(category, tool);
  return { title: course ? `${course.tool.name} course` : "Tool" };
}

export default async function ToolPage({
  params,
}: {
  params: Promise<{ category: string; tool: string }>;
}): Promise<React.JSX.Element> {
  const { category: categoryId, tool: toolId } = await params;
  const course = getToolCourse(categoryId, toolId);
  if (!course) {
    notFound();
  }

  const { tool, guides, relatedLessonSlugs, categoryTitle } = course;
  const related = relatedLessonSlugs
    .map((slug) => getLesson(slug))
    .filter((lesson): lesson is NonNullable<typeof lesson> => Boolean(lesson));
  const totalMinutes = guides.reduce((sum, guide) => sum + guide.minutes, 0);

  return (
    <AppShell>
      <main id="main" className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {categoryTitle} · on-site course
        </p>
        <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          {tool.name}
        </h1>
        <p className="mt-3 text-muted-foreground leading-relaxed">{tool.summary}</p>

        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-full border border-border bg-secondary/60 px-2.5 py-1">
            {guides.length} guides
          </span>
          <span className="rounded-full border border-border bg-secondary/60 px-2.5 py-1">
            ~{totalMinutes} min
          </span>
          <a
            href={tool.docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-border px-2.5 py-1 font-medium text-primary hover:underline"
          >
            {tool.docsLabel} reference ↗
          </a>
        </div>

        <h2 className="font-display mt-10 text-xl font-semibold tracking-tight">
          Course outline
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Tap any card to open the full guide on this site. Official documentation is
          linked inside each lesson as a secondary reference.
        </p>
        <div className="mt-6">
          <LearningCallList
            categoryId={categoryId}
            toolId={toolId}
            guides={guides}
          />
        </div>

        {related.length > 0 ? (
          <section className="mt-12">
            <h2 className="font-display text-xl font-semibold tracking-tight">
              Related curriculum lessons
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Deeper academy tracks that pair with this tool course.
            </p>
            <ul className="mt-4 space-y-3">
              {related.map((lesson) => (
                <li key={lesson.slug}>
                  <Link
                    href={`/learn/${lesson.slug}`}
                    className="bezel-card block px-4 py-4 transition-colors hover:border-primary/30 sm:px-5"
                  >
                    <p className="font-medium text-foreground">{lesson.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{lesson.summary}</p>
                    <span className="mt-2 inline-flex text-sm font-medium text-primary">
                      Open lesson →
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </main>
    </AppShell>
  );
}
