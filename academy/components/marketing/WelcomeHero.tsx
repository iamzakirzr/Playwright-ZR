"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 18 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
  },
};

export function WelcomeHero(): React.JSX.Element {
  const reduceMotion = useReducedMotion();

  return (
    <section className="welcome-wash relative isolate flex min-h-[100dvh] flex-col px-6 pb-10 pt-8 sm:px-10">
      <div className="mx-auto flex w-full max-w-lg flex-1 flex-col">
        <motion.div
          variants={reduceMotion ? undefined : container}
          initial={reduceMotion ? false : "hidden"}
          animate={reduceMotion ? undefined : "show"}
          className="flex flex-1 flex-col items-center text-center"
        >
          <motion.div
            variants={reduceMotion ? undefined : item}
            className={`mt-6 mb-2 ${reduceMotion ? "" : "book-float"}`}
            aria-hidden
          >
            <div className="book-stack">
              <span />
              <span />
              <span />
              <span />
            </div>
          </motion.div>

          <motion.p
            variants={reduceMotion ? undefined : item}
            className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl"
          >
            AI QA Academy
          </motion.p>

          <motion.h1
            variants={reduceMotion ? undefined : item}
            className="font-display mt-5 max-w-[18ch] text-balance text-2xl font-semibold tracking-tight text-foreground sm:text-3xl"
          >
            A calm way to grow advanced QA skills
          </motion.h1>

          <motion.p
            variants={reduceMotion ? undefined : item}
            className="mt-4 max-w-md text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg"
          >
            Stay organized, motivated, and confident — learn Playwright, typed
            APIs, judges, and RAG at your own pace.
          </motion.p>

          <motion.div
            variants={reduceMotion ? undefined : item}
            className="mt-auto flex flex-col items-center gap-3 pt-12 pb-4"
          >
            <Link
              href="#discover"
              aria-label="Start discovering courses"
              className={`cta-ring flex size-16 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-[1.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                reduceMotion ? "" : "cta-breathe"
              }`}
            >
              <ArrowUpRight className="size-7" strokeWidth={2.25} />
            </Link>
            <span className="text-sm text-muted-foreground">Enter Discover</span>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
