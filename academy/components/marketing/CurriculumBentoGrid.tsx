"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { bentoTopics } from "@/lib/curriculum";
import { cn } from "@/lib/utils";
import type { BentoTopic } from "@/types/curriculum";

const accentRing: Record<BentoTopic["accent"], string> = {
  cyan: "hover:border-primary/60 hover:shadow-[0_0_40px_-12px_oklch(0.78_0.14_195_/_0.45)]",
  teal: "hover:border-accent/60 hover:shadow-[0_0_40px_-12px_oklch(0.72_0.16_165_/_0.4)]",
  mint: "hover:border-accent/50",
  slate: "hover:border-border",
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
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Curriculum built on runnable tests
        </h2>
        <p className="mt-3 text-muted-foreground">
          Four pillars from Playwright-ZR — not invented TypeScript demos. Open a
          lesson and you will see the same Python surfaces the CI suite gates.
        </p>
      </div>

      <div className="grid auto-rows-[minmax(160px,auto)] gap-4 md:grid-cols-3">
        {bentoTopics.map((topic, index) => (
          <motion.div
            key={topic.id}
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: reduceMotion ? 0 : index * 0.06, duration: reduceMotion ? 0 : 0.45 }}
            whileHover={reduceMotion ? undefined : { scale: 1.015 }}
            className={cn(spanClass[topic.span])}
          >
            <Link
              href={topic.href}
              className={cn(
                "group flex h-full flex-col justify-between rounded-2xl border border-border/80 bg-surface-elevated/80 p-6 transition-colors",
                accentRing[topic.accent],
              )}
            >
              <div>
                <p className="font-[family-name:var(--font-code)] text-xs tracking-widest text-primary uppercase">
                  Track
                </p>
                <h3 className="mt-3 text-xl font-semibold tracking-tight group-hover:text-primary">
                  {topic.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  {topic.description}
                </p>
              </div>
              <span className="mt-6 text-sm text-primary opacity-80 group-hover:opacity-100">
                Open lesson →
              </span>
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
