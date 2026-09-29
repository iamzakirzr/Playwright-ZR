"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { categoryMeta } from "@/lib/category-meta";
import { cn } from "@/lib/utils";
import type { AcademyTool, ToolCategory, ToolCategoryId } from "@/types/tools";

export function CategoryBentoCard({
  category,
  index,
}: Readonly<{
  category: ToolCategory;
  index: number;
}>): React.JSX.Element {
  const reduceMotion = useReducedMotion();
  const meta = categoryMeta[category.id];
  // Each tool course = overview + concepts + patterns + delivery + practice
  const guideCount = category.tools.reduce(
    (sum, tool) => sum + tool.calls.length + 4,
    0,
  );

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: reduceMotion ? 0 : index * 0.05, duration: 0.4 }}
    >
      <Link
        href={`/tools/${category.id}`}
        className={cn("bezel-card group block p-5 sm:p-6")}
        style={{ ["--card-glow" as string]: meta.glow }}
        onMouseMove={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          event.currentTarget.style.setProperty("--mx", `${event.clientX - rect.left}px`);
          event.currentTarget.style.setProperty("--my", `${event.clientY - rect.top}px`);
        }}
      >
        <div
          className={cn(
            "pointer-events-none absolute inset-0 bg-gradient-to-br opacity-80",
            meta.accent,
          )}
          aria-hidden
        />
        <div className="relative flex h-full flex-col">
          <div className="flex items-start justify-between gap-3">
            <span className="rounded-full border border-border bg-background/50 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
              {meta.difficulty}
            </span>
            <span className="rounded-full border border-border bg-background/40 px-2.5 py-1 text-[11px] font-medium text-foreground/80">
              {category.tools.length} tools
            </span>
          </div>
          <h2 className="font-display mt-5 text-xl font-semibold tracking-tight sm:text-2xl">
            {category.title}
          </h2>
          <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">
            {category.summary}
          </p>
          <div className="mt-5 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{guideCount} on-site guides</span>
            <span className="inline-flex items-center gap-1 font-medium text-primary opacity-80 transition-opacity group-hover:opacity-100">
              {meta.cta}
              <ArrowUpRight className="size-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export function ToolBentoCard({
  categoryId,
  tool,
  index,
}: Readonly<{
  categoryId: ToolCategoryId;
  tool: AcademyTool;
  index: number;
}>): React.JSX.Element {
  const reduceMotion = useReducedMotion();
  const meta = categoryMeta[categoryId];

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: reduceMotion ? 0 : index * 0.04, duration: 0.35 }}
    >
      <Link
        href={`/tools/${categoryId}/${tool.id}`}
        className="bezel-card group block p-4 sm:p-5"
        style={{ ["--card-glow" as string]: meta.glow }}
      >
        <div className="relative flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="font-display text-lg font-semibold tracking-tight">{tool.name}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{tool.summary}</p>
            <p className="mt-3 text-xs text-muted-foreground">
              {tool.calls.length + 4} on-site guides · {tool.docsLabel} reference
            </p>
          </div>
          <ArrowUpRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-primary" />
        </div>
        <div className="relative mt-4 flex gap-2">
          <span className="rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
            Start course
          </span>
          <span className="rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
            Open guides →
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

export function CardSkeleton(): React.JSX.Element {
  return (
    <div className="bezel-card p-5">
      <div className="skeleton h-5 w-20 rounded-full" />
      <div className="skeleton mt-5 h-7 w-2/3 rounded-lg" />
      <div className="skeleton mt-3 h-4 w-full rounded" />
      <div className="skeleton mt-2 h-4 w-4/5 rounded" />
      <div className="skeleton mt-6 h-4 w-28 rounded" />
    </div>
  );
}
