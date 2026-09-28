"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/SiteHeader";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.11, delayChildren: 0.06 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  },
};

export function HeroSection(): React.JSX.Element {
  const reduceMotion = useReducedMotion();

  return (
    <section className="relative isolate min-h-[100dvh] overflow-hidden">
      <div className="hero-ink-band absolute inset-0" aria-hidden />
      <div
        className="hero-ink-glow pointer-events-none absolute -top-24 right-[-10%] h-[70%] w-[70%] rounded-full bg-[radial-gradient(circle,oklch(0.65_0.12_185_/_0.35),transparent_65%)]"
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-0 bg-notebook opacity-40 mix-blend-soft-light" aria-hidden />

      <SiteHeader />

      <div className="relative mx-auto flex min-h-[100dvh] max-w-6xl flex-col justify-center px-6 pb-24 pt-32 sm:px-8">
        <motion.div
          variants={reduceMotion ? undefined : container}
          initial={reduceMotion ? false : "hidden"}
          animate={reduceMotion ? undefined : "show"}
          className="max-w-3xl text-primary-foreground"
        >
          <motion.h1
            variants={reduceMotion ? undefined : item}
            className="font-display text-balance text-5xl leading-[0.96] font-semibold tracking-tight sm:text-7xl"
          >
            AI QA Academy
          </motion.h1>
          <motion.p
            variants={reduceMotion ? undefined : item}
            className="mt-6 max-w-xl text-pretty text-xl text-primary-foreground/90 sm:text-2xl"
          >
            Learn how AI works by testing it.
          </motion.p>
          <motion.p
            variants={reduceMotion ? undefined : item}
            className="mt-4 max-w-xl text-pretty text-base text-primary-foreground/75 sm:text-lg"
          >
            Six tracks from Playwright page objects to calibrated judges and
            agents — every claim ties to a test you can run in this repo.
          </motion.p>
          <motion.div
            variants={reduceMotion ? undefined : item}
            className="mt-10 flex flex-wrap gap-3"
          >
            <Button
              asChild
              size="lg"
              className="bg-white text-foreground hover:bg-white/90"
            >
              <Link href="/learn">
                Start learning
                <ArrowRight />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="border-white/35 bg-transparent text-primary-foreground hover:bg-white/10 hover:text-primary-foreground"
            >
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
