"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { bentoTopics } from "@/lib/curriculum";
import { cn } from "@/lib/utils";
import type { BentoTopic } from "@/types/curriculum";

const accentBar: Record<BentoTopic["accent"], string> = {
  cyan: "bg-primary",
  teal: "bg-[oklch(0.5_0.1_200)]",
  mint: "bg-[oklch(0.55_0.12_160)]",
  slate: "bg-ink-soft",
};

const spanClass: Record<BentoTopic["span"], string> = {
  wide: "md:col-span-2",
  tall: "md:row-span-2",
  normal: "",
};

export function CurriculumBentoGrid(): React.JSX.Element {
  const reduceMotion = useReducedMotion();

  return (
    <section className="relative mx-auto max-w-6xl px-6 py-24 sm:px-8">
      <div className="mb-12 max-w-2xl">
        <p className="font-[family-name:var(--font-code)] text-xs tracking-[0.2em] text-primary uppercase">
          Start here
        </p>
        <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Four doors into the craft
        </h2>
        <p className="mt-3 text-muted-foreground leading-relaxed">
          Pick a pillar. Each lesson uses the same Python surfaces the hermetic
          CI suite already gates — page objects, pydantic clients, judges, and RAG.
        </p>
      </div>

      <div className="grid auto-rows-[minmax(168px,auto)] gap-4 md:grid-cols-3">
        {bentoTopics.map((topic, index) => (
          <motion.div
            key={topic.id}
            initial={reduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{
              delay: reduceMotion ? 0 : index * 0.05,
              duration: reduceMotion ? 0 : 0.4,
            }}
            whileHover={reduceMotion ? undefined : { y: -2 }}
            className={cn(spanClass[topic.span])}
          >
            <Link
              href={topic.href}
              className="group relative flex h-full flex-col justify-between overflow-hidden rounded-xl border border-border/90 bg-surface-elevated p-6 transition-colors hover:border-primary/40"
            >
              <span
                className={cn(
                  "absolute inset-y-0 left-0 w-1 transition-all group-hover:w-1.5",
                  accentBar[topic.accent],
                )}
                aria-hidden
              />
              <div className="pl-2">
                <p className="font-[family-name:var(--font-code)] text-[11px] tracking-[0.18em] text-muted-foreground uppercase">
                  Pathway {String(index + 1).padStart(2, "0")}
                </p>
                <h3 className="font-display mt-3 text-xl font-semibold tracking-tight group-hover:text-primary">
                  {topic.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  {topic.description}
                </p>
              </div>
              <span className="mt-6 pl-2 text-sm font-medium text-primary">
                Enter lesson →
              </span>
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
