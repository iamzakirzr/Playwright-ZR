"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  const [active, setActive] = useState<Stage>("split");
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    if (!playing) {
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
  }, [playing]);

  const activeMeta = stages.find((stage) => stage.id === active);

  return (
    <div className="rounded-2xl border border-border/80 bg-card/60 p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">RAG pipeline visualizer</h3>
          <p className="text-sm text-muted-foreground">
            Interactive diagram: Text Splitting → Embedding → Semantic Search → Generate
          </p>
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => setPlaying((value) => !value)}
        >
          {playing ? "Pause" : "Play"}
        </Button>
      </div>

      <div className="relative grid gap-3 sm:grid-cols-4">
        {stages.map((stage, index) => {
          const isActive = stage.id === active;
          return (
            <button
              key={stage.id}
              type="button"
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
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.28 }}
          className="mt-6 rounded-xl border border-border/60 bg-background/50 p-4"
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
