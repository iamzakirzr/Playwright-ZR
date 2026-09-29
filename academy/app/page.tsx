"use client";

import { motion, useReducedMotion } from "framer-motion";
import { AppShell } from "@/components/dashboard/AppShell";
import { CategoryCard } from "@/components/dashboard/CategoryCard";
import { toolCategories } from "@/lib/tools-catalog";

export default function DashboardPage(): React.JSX.Element {
  const reduceMotion = useReducedMotion();

  return (
    <AppShell>
      <main id="main" className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <p className="text-xs font-semibold tracking-[0.18em] text-primary uppercase">
            Academy
          </p>
          <h1 className="font-display mt-3 max-w-2xl text-3xl font-semibold tracking-tight sm:text-5xl">
            Master QA tooling with a fluid learning path
          </h1>
          <p className="mt-4 max-w-2xl text-muted-foreground leading-relaxed">
            Browse categories, open interactive tool paths, and jump to official docs —
            built for speed, keyboard nav, and system themes.
          </p>
        </motion.div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {toolCategories.map((category, index) => (
            <CategoryCard key={category.id} category={category} index={index} />
          ))}
        </div>
      </main>
    </AppShell>
  );
}
