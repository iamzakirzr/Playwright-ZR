import Link from "next/link";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeBlock } from "@/components/features/CodeBlock";
import { RAGVisualizer } from "@/components/features/RAGVisualizer";
import { getAdjacentLessons } from "@/lib/curriculum";
import type { Lesson } from "@/types/curriculum";

export interface LessonViewProps {
  readonly lesson: Lesson;
}

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
          <h2 className="text-xl font-semibold tracking-tight">{section.heading}</h2>
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
        <Badge>{lesson.track}</Badge>
        <Badge variant="outline">{lesson.minutes} min</Badge>
      </div>
      <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{lesson.title}</h1>
      <p className="mt-4 text-lg text-muted-foreground">{lesson.summary}</p>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>In one minute</CardTitle>
          <CardDescription>Facts from Playwright-ZR docs — not invented demos.</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
            {lesson.tip.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="mt-10 space-y-10">{sectionBlocks}</div>

      {lesson.slug === "rag" ? (
        <div className="mt-12">
          <RAGVisualizer />
        </div>
      ) : null}

      <div className="mt-12">
        <h2 className="mb-3 text-lg font-semibold">Repository surfaces</h2>
        <Accordion type="single" collapsible className="rounded-xl border border-border/70 px-4">
          {lesson.relatedRepoPaths.map((path) => (
            <AccordionItem key={path} value={path}>
              <AccordionTrigger>{path}</AccordionTrigger>
              <AccordionContent>
                Open this path in{" "}
                <a
                  className="text-primary underline-offset-4 hover:underline"
                  href={`https://github.com/iamzakirzr/Playwright-ZR/tree/main/${path.replace(/\/$/, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Playwright-ZR
                </a>{" "}
                to run the matching tests and read the source of truth.
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      <nav className="mt-14 flex items-center justify-between gap-4 border-t border-border/70 pt-6 text-sm">
        {prev ? (
          <Link href={`/learn/${prev.slug}`} className="text-muted-foreground hover:text-primary">
            ← {prev.title}
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link href={`/learn/${next.slug}`} className="text-primary hover:underline">
            {next.title} →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </article>
  );
}
