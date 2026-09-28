import Link from "next/link";
import { curriculumTracks } from "@/lib/curriculum";
import { Badge } from "@/components/ui/badge";

export const metadata = {
  title: "Curriculum",
};

export default function LearnIndexPage(): React.JSX.Element {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-8">
      <p className="font-[family-name:var(--font-code)] text-xs tracking-[0.2em] text-primary uppercase">
        Learning path
      </p>
      <h1 className="font-display mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
        Curriculum
      </h1>
      <p className="mt-3 max-w-2xl text-muted-foreground leading-relaxed">
        Six tracks, ordered the way the repository teaches: framework → foundations →
        evals → agents → MCP → industry. Start anywhere, but week one still belongs to
        page objects and service clients.
      </p>

      <div className="mt-12 space-y-12">
        {curriculumTracks.map((track, trackIndex) => (
          <section key={track.id} aria-labelledby={`track-${track.id}`}>
            <div className="mb-4 flex flex-wrap items-baseline gap-3">
              <span className="font-[family-name:var(--font-code)] text-xs text-muted-foreground">
                {String(trackIndex + 1).padStart(2, "0")}
              </span>
              <h2 id={`track-${track.id}`} className="font-display text-2xl font-semibold">
                {track.title}
              </h2>
              <Badge variant="outline">{track.lessons.length} lessons</Badge>
            </div>
            <p className="mb-5 max-w-2xl text-sm text-muted-foreground">{track.description}</p>
            <ul className="divide-y divide-border border-y border-border">
              {track.lessons.map((lesson) => (
                <li key={lesson.slug}>
                  <Link
                    href={`/learn/${lesson.slug}`}
                    className="group flex flex-col gap-1 py-4 transition-colors sm:flex-row sm:items-baseline sm:justify-between sm:gap-6"
                  >
                    <span>
                      <span className="font-medium text-foreground group-hover:text-primary">
                        {lesson.title}
                      </span>
                      <span className="mt-1 block text-sm text-muted-foreground sm:mt-0.5">
                        {lesson.summary}
                      </span>
                    </span>
                    <span className="shrink-0 text-xs font-medium text-primary whitespace-nowrap">
                      {lesson.minutes} min →
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
