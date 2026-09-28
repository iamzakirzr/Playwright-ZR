import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { curriculumTracks } from "@/lib/curriculum";
import { Badge } from "@/components/ui/badge";

export const metadata = {
  title: "Curriculum",
};

export default function LearnIndexPage(): React.JSX.Element {
  return (
    <div className="px-4 py-8 sm:px-6 sm:py-10">
      <p className="text-xs font-semibold tracking-[0.18em] text-primary uppercase">
        Learning path
      </p>
      <h1 className="font-display mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
        Curriculum
      </h1>
      <p className="mt-3 max-w-2xl text-muted-foreground leading-relaxed">
        Deep lessons across framework, foundations, evals, agents, MCP, and industry practice.
      </p>

      <div className="mt-10 space-y-10">
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
            <p className="mb-4 max-w-2xl text-sm text-muted-foreground">{track.description}</p>
            <ul className="space-y-2">
              {track.lessons.map((lesson) => (
                <li key={lesson.slug}>
                  <Link
                    href={`/learn/${lesson.slug}`}
                    className="bezel-card group flex items-center gap-3 px-3 py-3"
                  >
                    <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-secondary text-xs font-semibold text-primary">
                      {lesson.minutes}m
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block font-medium text-foreground group-hover:text-primary">
                        {lesson.title}
                      </span>
                      <span className="mt-0.5 block truncate text-sm text-muted-foreground">
                        {lesson.summary}
                      </span>
                    </span>
                    <ArrowUpRight className="size-4 shrink-0 text-muted-foreground" />
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
