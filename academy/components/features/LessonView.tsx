import Link from "next/link";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "@/components/features/CodeBlock";
import { RAGVisualizer } from "@/components/features/RAGVisualizer";
import { getAdjacentLessons } from "@/lib/curriculum";
import type { Lesson } from "@/types/curriculum";

export interface LessonViewProps {
  readonly lesson: Lesson;
}

const trackLabels: Record<Lesson["track"], string> = {
  framework: "QA framework",
  foundations: "Foundations",
  evals: "Evaluating AI",
  agents: "Agents",
  mcp: "MCP",
  industry: "Industry",
};

export async function LessonView({ lesson }: LessonViewProps): Promise<React.JSX.Element> {
  const { prev, next } = getAdjacentLessons(lesson.slug);

  const sectionBlocks = await Promise.all(
    lesson.sections.map(async (section) => {
      const code =
        section.code !== undefined ? (
          <div className="mt-5">
            <CodeBlock
              code={section.code.code}
              language={section.code.language}
              filename={section.code.filename}
            />
          </div>
        ) : null;

      return (
        <section key={section.heading}>
          <h2 className="font-display text-xl font-semibold tracking-tight">{section.heading}</h2>
          <p className="mt-3 text-muted-foreground leading-relaxed">{section.body}</p>
          {section.bullets ? (
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
              {section.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          ) : null}
          {code}
        </section>
      );
    }),
  );

  return (
    <article className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Badge>{trackLabels[lesson.track]}</Badge>
        <Badge variant="outline">{lesson.minutes} min read</Badge>
      </div>
      <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
        {lesson.title}
      </h1>
      <p className="mt-4 text-lg text-muted-foreground leading-relaxed">{lesson.summary}</p>

      <aside className="mt-8 border-l-2 border-primary bg-secondary/60 py-4 pr-4 pl-5">
        <p className="font-[family-name:var(--font-code)] text-[11px] tracking-[0.18em] text-primary uppercase">
          In one minute
        </p>
        <ul className="mt-3 list-disc space-y-2 pl-4 text-sm text-ink-soft">
          {lesson.tip.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </aside>

      <div className="mt-10 space-y-10">{sectionBlocks}</div>

      {lesson.slug === "rag" ? (
        <div className="mt-12">
          <RAGVisualizer />
        </div>
      ) : null}

      <div className="mt-12">
        <h2 className="font-display mb-3 text-lg font-semibold">Repository surfaces</h2>
        <p className="mb-3 text-sm text-muted-foreground">
          Open the matching path in Playwright-ZR — the source of truth behind this lesson.
        </p>
        <Accordion type="single" collapsible className="rounded-xl border border-border px-4">
          {lesson.relatedRepoPaths.map((path) => (
            <AccordionItem key={path} value={path}>
              <AccordionTrigger className="font-[family-name:var(--font-code)] text-sm">
                {path}
              </AccordionTrigger>
              <AccordionContent>
                <a
                  className="text-primary underline-offset-4 hover:underline"
                  href={`https://github.com/iamzakirzr/Playwright-ZR/tree/main/${path.replace(/\/$/, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View on GitHub →
                </a>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      <nav className="mt-14 flex items-center justify-between gap-4 border-t border-border pt-6 text-sm">
        {prev ? (
          <Link href={`/learn/${prev.slug}`} className="text-muted-foreground hover:text-primary">
            ← {prev.title}
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link href={`/learn/${next.slug}`} className="font-medium text-primary hover:underline">
            {next.title} →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </article>
  );
}
