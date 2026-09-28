import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { curriculumTracks, discoverCards } from "@/lib/curriculum";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PastelAccent } from "@/types/curriculum";

export const metadata = {
  title: "Curriculum",
};

const pastelBg: Record<PastelAccent, string> = {
  mint: "bg-pastel-mint",
  sand: "bg-pastel-sand",
  blush: "bg-pastel-blush",
  sage: "bg-pastel-sage",
  sky: "bg-pastel-sky",
  lilac: "bg-pastel-lilac",
};

export default function LearnIndexPage(): React.JSX.Element {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-8">
      <p className="text-xs font-semibold tracking-[0.18em] text-primary uppercase">
        Learning path
      </p>
      <h1 className="font-display mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
        Curriculum
      </h1>
      <p className="mt-3 max-w-2xl text-muted-foreground leading-relaxed">
        Six tracks at your own pace — no calendar. Start with Playwright and typed
        APIs, then move into judges, RAG, agents, and MCP.
      </p>

      <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {discoverCards.map((card) => (
          <Link
            key={card.id}
            href={card.href}
            className={cn(
              "group relative flex min-h-[140px] flex-col justify-between overflow-hidden rounded-[1.5rem] p-4",
              pastelBg[card.accent],
            )}
          >
            <span className="ml-auto inline-flex size-8 items-center justify-center rounded-xl bg-background/55">
              <ArrowUpRight className="size-4" />
            </span>
            <div>
              <p className="text-[11px] font-medium tracking-[0.14em] text-foreground/55 uppercase">
                {card.shortLabel}
              </p>
              <h2 className="font-display mt-1 text-lg font-semibold tracking-tight">
                {card.title}
              </h2>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-14 space-y-12">
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
            <ul className="space-y-2">
              {track.lessons.map((lesson) => (
                <li key={lesson.slug}>
                  <Link
                    href={`/learn/${lesson.slug}`}
                    className="group flex items-center gap-3 rounded-[1.25rem] bg-card px-3 py-3 ring-1 ring-border/70 transition-colors hover:ring-primary/35"
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
                    <ArrowUpRight className="size-4 shrink-0 text-muted-foreground group-hover:text-primary" />
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
