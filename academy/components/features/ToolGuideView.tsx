import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "@/components/features/CodeBlock";
import { getAdjacentGuides, getLesson } from "@/lib/tool-guides";
import type { ToolCourse, ToolGuide } from "@/types/tools";

const kindLabel: Record<ToolGuide["kind"], string> = {
  overview: "Course intro",
  concept: "Concept guide",
  practice: "Practice",
};

export async function ToolGuideView({
  course,
  guide,
}: Readonly<{
  course: ToolCourse;
  guide: ToolGuide;
}>): Promise<React.JSX.Element> {
  const { prev, next } = getAdjacentGuides(
    course.categoryId,
    course.tool.id,
    guide.id,
  );
  const base = `/tools/${course.categoryId}/${course.tool.id}`;
  const samples = guide.codeSamples ?? [];

  const sampleBlocks =
    samples.length > 0
      ? await Promise.all(
          samples.map(async (sample) => (
            <div key={`${sample.filename}-${sample.language}`} className="mt-5">
              <CodeBlock
                code={sample.code}
                language={sample.language}
                filename={sample.filename}
              />
            </div>
          )),
        )
      : [];

  const sectionBlocks = await Promise.all(
    guide.sections.map(async (section) => {
      const injectSamples = section.heading === "Advanced coding examples";
      return (
        <section key={section.heading}>
          <h2 className="font-display text-xl font-semibold tracking-tight">
            {section.heading}
          </h2>
          <p className="mt-3 text-muted-foreground leading-relaxed">{section.body}</p>
          {section.bullets ? (
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
              {section.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          ) : null}
          {injectSamples ? <div className="space-y-2">{sampleBlocks}</div> : null}
        </section>
      );
    }),
  );

  const hasAdvancedSection = guide.sections.some(
    (s) => s.heading === "Advanced coding examples",
  );
  const trailingSamples =
    samples.length > 0 && !hasAdvancedSection ? (
      <section>
        <h2 className="font-display text-xl font-semibold tracking-tight">
          Advanced coding examples
        </h2>
        <p className="mt-3 text-muted-foreground leading-relaxed">
          TypeScript and/or Python examples for this guide — adapt paths and credentials to
          your environment.
        </p>
        <div className="space-y-2">{sampleBlocks}</div>
      </section>
    ) : null;

  const related = course.relatedLessonSlugs
    .map((slug) => getLesson(slug))
    .filter((lesson): lesson is NonNullable<typeof lesson> => Boolean(lesson));

  const langBadges = [...new Set(samples.map((s) => s.language))];

  return (
    <article className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Badge>{kindLabel[guide.kind]}</Badge>
        <Badge variant="outline">{guide.minutes} min</Badge>
        <Badge variant="outline">{course.tool.name}</Badge>
        {langBadges.map((lang) => (
          <Badge key={lang} variant="outline">
            {lang}
          </Badge>
        ))}
      </div>

      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {course.categoryTitle} · course
      </p>
      <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
        {guide.title}
      </h1>
      <p className="mt-4 text-lg text-muted-foreground leading-relaxed">{guide.summary}</p>

      <aside className="mt-8 border-l-2 border-primary bg-secondary/60 py-4 pr-4 pl-5">
        <p className="font-[family-name:var(--font-code)] text-[11px] tracking-[0.18em] text-primary uppercase">
          In one minute
        </p>
        <ul className="mt-3 list-disc space-y-2 pl-4 text-sm text-ink-soft">
          {guide.tip.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </aside>

      <div className="mt-10 space-y-10">
        {sectionBlocks}
        {trailingSamples}
      </div>

      <div className="mt-12 rounded-2xl border border-border bg-secondary/40 px-4 py-4 sm:px-5">
        <p className="text-sm font-medium text-foreground">Official reference</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Use vendor docs to confirm API details — your lesson, exercises, and code samples
          stay on this site.
        </p>
        <a
          href={guide.docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex text-sm font-medium text-primary hover:underline"
        >
          {guide.docsLabel} ↗
        </a>
      </div>

      {related.length > 0 ? (
        <div className="mt-10">
          <h2 className="font-display text-lg font-semibold tracking-tight">
            Related academy curriculum
          </h2>
          <ul className="mt-3 space-y-2">
            {related.map((lesson) => (
              <li key={lesson.slug}>
                <Link
                  href={`/learn/${lesson.slug}`}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  {lesson.title} →
                </Link>
                <p className="text-sm text-muted-foreground">{lesson.summary}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <nav className="mt-14 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-6 text-sm">
        {prev ? (
          <Link href={`${base}/${prev.id}`} className="text-muted-foreground hover:text-primary">
            ← {prev.title}
          </Link>
        ) : (
          <Link href={base} className="text-muted-foreground hover:text-primary">
            ← {course.tool.name} course
          </Link>
        )}
        {next ? (
          <Link href={`${base}/${next.id}`} className="ml-auto text-primary hover:underline">
            {next.title} →
          </Link>
        ) : (
          <Link href={base} className="ml-auto text-primary hover:underline">
            Back to course →
          </Link>
        )}
      </nav>
    </article>
  );
}
