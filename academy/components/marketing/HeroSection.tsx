"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";

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

export function HeroSection(): React.JSX.Element {
  return (
    <section className="relative isolate min-h-[100dvh] overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-grid" aria-hidden />
      <div
        className="hero-beam pointer-events-none absolute -left-1/4 top-0 h-[70%] w-[150%] bg-[radial-gradient(ellipse_at_center,oklch(0.7_0.14_195_/_0.18),transparent_60%)]"
        aria-hidden
      />

      <div className="relative mx-auto flex min-h-[100dvh] max-w-6xl flex-col justify-center px-6 pb-24 pt-28 sm:px-8">
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="max-w-3xl"
        >
          <motion.h1
            variants={item}
            className="text-balance text-5xl leading-[0.98] font-semibold tracking-tight text-foreground sm:text-7xl"
          >
            AI QA Academy
          </motion.h1>
          <motion.p
            variants={item}
            className="mt-6 max-w-xl text-pretty text-xl text-muted-foreground sm:text-2xl"
          >
            Learn how AI works by testing it
          </motion.p>
          <motion.p
            variants={item}
            className="mt-4 max-w-xl text-pretty text-base text-muted-foreground/90 sm:text-lg"
          >
            LLMs, RAG, agents, and MCP — from the real Playwright-ZR Python
            framework. Every number comes from a test you can run.
          </motion.p>
          <motion.div variants={item} className="mt-10 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/learn">
                Start learning
                <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link
                href="https://github.com/iamzakirzr/Playwright-ZR"
                target="_blank"
                rel="noopener noreferrer"
              >
                <GitBranch />
                View the code
              </Link>
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
