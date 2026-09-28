"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowUpRight,
  Bell,
  LayoutGrid,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { curriculumTracks, discoverCards } from "@/lib/curriculum";
import { cn } from "@/lib/utils";
import type { DiscoverFilter, PastelAccent } from "@/types/curriculum";

const FILTERS: { id: DiscoverFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "playwright", label: "Playwright" },
  { id: "api", label: "API" },
  { id: "judges", label: "Judges" },
  { id: "rag", label: "RAG" },
  { id: "agents", label: "Agents" },
  { id: "mcp", label: "MCP" },
];

const pastelBg: Record<PastelAccent, string> = {
  mint: "bg-pastel-mint",
  sand: "bg-pastel-sand",
  blush: "bg-pastel-blush",
  sage: "bg-pastel-sage",
  sky: "bg-pastel-sky",
  lilac: "bg-pastel-lilac",
};

const trackMeta: Record<
  string,
  { role: string; accent: PastelAccent; href: string }
> = {
  framework: {
    role: "Playwright · API · CI foundations",
    accent: "mint",
    href: "/learn/framework-overview",
  },
  foundations: {
    role: "LLMs, prompts, and retrieval",
    accent: "sage",
    href: "/learn/how-llms-work",
  },
  evals: {
    role: "Judges, metrics, red teaming",
    accent: "blush",
    href: "/learn/evaluating-llms",
  },
  agents: {
    role: "Tool loops and trajectories",
    accent: "sky",
    href: "/learn/what-is-an-agent",
  },
  mcp: {
    role: "Server contracts and Playwright MCP",
    accent: "lilac",
    href: "/learn/how-mcp-works",
  },
  industry: {
    role: "Adoption playbook for QA teams",
    accent: "sand",
    href: "/learn/ai-in-qa-at-companies",
  },
};

export function DiscoverHome(): React.JSX.Element {
  const reduceMotion = useReducedMotion();
  const [filter, setFilter] = useState<DiscoverFilter>("all");
  const [query, setQuery] = useState("");

  const cards = useMemo(() => {
    const q = query.trim().toLowerCase();
    return discoverCards.filter((card) => {
      const byFilter = filter === "all" || card.filter === filter;
      const byQuery =
        !q ||
        card.title.toLowerCase().includes(q) ||
        card.description.toLowerCase().includes(q) ||
        card.shortLabel.toLowerCase().includes(q);
      return byFilter && byQuery;
    });
  }, [filter, query]);

  return (
    <section
      id="discover"
      aria-labelledby="discover-heading"
      className="relative scroll-mt-4 bg-[oklch(0.985_0.008_185)] px-5 pb-20 pt-6 sm:px-8"
    >
      <div className="mx-auto max-w-lg lg:max-w-3xl">
        <header className="mb-6 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex size-11 items-center justify-center rounded-2xl bg-secondary text-foreground transition-colors hover:bg-primary/15"
            aria-label="AI QA Academy home"
          >
            <LayoutGrid className="size-5" />
          </Link>
          <div className="flex items-center gap-2">
            <span
              className="inline-flex size-11 items-center justify-center rounded-2xl bg-secondary text-muted-foreground"
              aria-hidden
            >
              <Bell className="size-5" />
            </span>
            <Link
              href="/learn"
              className="inline-flex size-11 items-center justify-center rounded-full bg-primary font-display text-sm font-semibold text-primary-foreground"
              aria-label="Open full curriculum"
            >
              QA
            </Link>
          </div>
        </header>

        <h2
          id="discover-heading"
          className="font-display max-w-[16ch] text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-4xl"
        >
          Grow with expert-led QA lessons
        </h2>
        <p className="mt-3 max-w-md text-muted-foreground leading-relaxed">
          Pick a core heading — Playwright, Typed API, judges, RAG — and learn
          advanced skills without a rigid timetable.
        </p>

        <div className="mt-7 flex items-center gap-2">
          <label className="relative min-w-0 flex-1">
            <span className="sr-only">Search courses</span>
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search Playwright, RAG…"
              className="w-full rounded-2xl border border-border/80 bg-card py-3 pr-3 pl-10 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>
          <span
            className="inline-flex size-11 shrink-0 items-center justify-center rounded-2xl bg-secondary text-muted-foreground"
            aria-hidden
          >
            <SlidersHorizontal className="size-4" />
          </span>
        </div>

        <div
          role="tablist"
          aria-label="Course filters"
          className="-mx-1 mt-4 flex gap-2 overflow-x-auto px-1 pb-1"
        >
          {FILTERS.map((item) => {
            const active = filter === item.id;
            return (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setFilter(item.id)}
                className={cn(
                  "shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-foreground text-background"
                    : "bg-secondary text-muted-foreground hover:text-foreground",
                )}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
          {cards.map((card, index) => (
            <motion.div
              key={card.id}
              initial={reduceMotion ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-20px" }}
              transition={{
                delay: reduceMotion ? 0 : index * 0.05,
                duration: reduceMotion ? 0 : 0.4,
              }}
            >
              <Link
                href={card.href}
                className={cn(
                  "group relative flex aspect-square flex-col justify-between overflow-hidden rounded-[1.75rem] p-4 transition-transform hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:p-5",
                  pastelBg[card.accent],
                )}
              >
                <span
                  className="pointer-events-none absolute inset-x-0 bottom-[-8%] text-center font-display text-[clamp(2.4rem,12vw,3.6rem)] font-bold tracking-tight text-foreground/[0.07] select-none"
                  aria-hidden
                >
                  {card.title}
                </span>
                <span className="ml-auto inline-flex size-9 items-center justify-center rounded-xl bg-background/55 text-foreground backdrop-blur-sm transition-colors group-hover:bg-background/80">
                  <ArrowUpRight className="size-4" />
                </span>
                <div className="relative">
                  <p className="text-[11px] font-medium tracking-[0.14em] text-foreground/55 uppercase">
                    {card.shortLabel}
                  </p>
                  <h3 className="font-display mt-1 text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
                    {card.title}
                  </h3>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {cards.length === 0 ? (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            No courses match that filter. Try All or clear search.
          </p>
        ) : null}

        <div className="mt-12 flex items-baseline justify-between gap-4">
          <h3 className="font-display text-xl font-semibold tracking-tight">
            Core tracks
          </h3>
          <Link
            href="/learn"
            className="text-sm font-medium text-primary hover:underline"
          >
            See all
          </Link>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse by path — no calendar, learn whenever you are ready.
        </p>

        <ul className="mt-5 space-y-3">
          {curriculumTracks.map((track, index) => {
            const meta = trackMeta[track.id];
            return (
              <li key={track.id}>
                <Link
                  href={meta.href}
                  className="flex items-center gap-3 rounded-[1.35rem] bg-card px-3 py-3 shadow-[0_1px_0_oklch(0.9_0.02_185)] ring-1 ring-border/70 transition-colors hover:ring-primary/35"
                >
                  <span
                    className={cn(
                      "flex size-12 shrink-0 items-center justify-center rounded-full font-display text-sm font-semibold text-foreground",
                      pastelBg[meta.accent],
                    )}
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium text-foreground">
                      {track.title}
                    </span>
                    <span className="block truncate text-sm text-muted-foreground">
                      {meta.role}
                    </span>
                  </span>
                  <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                    <ArrowUpRight className="size-4" />
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
