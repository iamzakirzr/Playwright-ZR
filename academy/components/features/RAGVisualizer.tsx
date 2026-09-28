"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Stage = "split" | "embed" | "search" | "generate";

const stages: readonly { id: Stage; title: string; detail: string }[] = [
  {
    id: "split",
    title: "Text splitting",
    detail: "Policy docs chunked — returns, shipping, loyalty — for the fictional store.",
  },
  {
    id: "embed",
    title: "Vector embedding",
    detail: "Chunks become vectors; hybrid search later fuses BM25 + dense scores.",
  },
  {
    id: "search",
    title: "Semantic search",
    detail: "Top-k=3 passages retrieved. Below the floor → abstain (no invented numbers).",
  },
  {
    id: "generate",
    title: "Grounded generate",
    detail: "qwen2.5:1.5b answers ONLY from CONTEXT; tests score faithfulness + IR.",
  },
] as const;

export function RAGVisualizer(): React.JSX.Element {
  const reduceMotion = useReducedMotion();
  const [active, setActive] = useState<Stage>("split");
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing || reduceMotion) {
      return;
    }
    const order: Stage[] = ["split", "embed", "search", "generate"];
    const timer = window.setInterval(() => {
      setActive((current) => {
        const index = order.indexOf(current);
        return order[(index + 1) % order.length];
      });
    }, 2200);
    return () => window.clearInterval(timer);
  }, [playing, reduceMotion]);

  const activeMeta = stages.find((stage) => stage.id === active);

  return (
    <div className="rounded-2xl border border-border bg-surface-elevated p-6 shadow-sm">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold">RAG pipeline visualizer</h3>
          <p className="text-sm text-muted-foreground">
            Interactive diagram: Text Splitting → Embedding → Semantic Search → Generate
          </p>
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={Boolean(reduceMotion)}
          onClick={() => setPlaying((value) => !value)}
        >
          {playing ? "Pause" : "Play"}
        </Button>
      </div>

      <div className="relative grid gap-3 sm:grid-cols-4" role="group" aria-label="RAG pipeline stages">
        {stages.map((stage, index) => {
          const isActive = stage.id === active;
          return (
            <button
              key={stage.id}
              type="button"
              aria-pressed={isActive}
              onClick={() => {
                setPlaying(false);
                setActive(stage.id);
              }}
              className={cn(
                "relative rounded-xl border px-3 py-4 text-left transition-colors",
                isActive
                  ? "border-primary/70 bg-primary/10 node-pulse"
                  : "border-border/70 bg-secondary/40 hover:border-primary/40",
              )}
            >
              <Badge variant={isActive ? "default" : "secondary"} className="mb-2">
                {index + 1}
              </Badge>
              <p className="text-sm font-medium">{stage.title}</p>
              {index < stages.length - 1 ? (
                <span
                  className="pointer-events-none absolute top-1/2 -right-2 hidden h-px w-3 bg-primary/50 sm:block"
                  aria-hidden
                />
              ) : null}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -8 }}
          transition={{ duration: reduceMotion ? 0 : 0.28 }}
          className="mt-6 rounded-xl border border-border bg-secondary/50 p-4"
          aria-live="polite"
        >
          <p className="font-[family-name:var(--font-code)] text-xs tracking-widest text-primary uppercase">
            {activeMeta?.title}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {activeMeta?.detail}
          </p>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
