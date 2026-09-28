"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, X } from "lucide-react";
import { toolCategories } from "@/lib/tools-catalog";
import { curriculumTracks } from "@/lib/curriculum";
import { cn } from "@/lib/utils";

type Hit = {
  id: string;
  title: string;
  subtitle: string;
  href: string;
  kind: "tool" | "category" | "lesson";
};

function buildIndex(): Hit[] {
  const hits: Hit[] = [];
  for (const category of toolCategories) {
    hits.push({
      id: `cat-${category.id}`,
      title: category.title,
      subtitle: category.summary,
      href: `/tools/${category.id}`,
      kind: "category",
    });
    for (const tool of category.tools) {
      hits.push({
        id: `tool-${category.id}-${tool.id}`,
        title: tool.name,
        subtitle: `${category.title} · ${tool.docsLabel}`,
        href: `/tools/${category.id}/${tool.id}`,
        kind: "tool",
      });
    }
  }
  for (const track of curriculumTracks) {
    for (const lesson of track.lessons) {
      hits.push({
        id: `lesson-${lesson.slug}`,
        title: lesson.title,
        subtitle: `${track.title} · lesson`,
        href: `/learn/${lesson.slug}`,
        kind: "lesson",
      });
    }
  }
  return hits;
}

export function SearchModal(): React.JSX.Element {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const index = useMemo(() => buildIndex(), []);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      return index.slice(0, 8);
    }
    return index
      .filter(
        (hit) =>
          hit.title.toLowerCase().includes(q) || hit.subtitle.toLowerCase().includes(q),
      )
      .slice(0, 12);
  }, [index, query]);

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
    setActive(0);
  }, []);

  const go = useCallback(
    (href: string) => {
      close();
      router.push(href);
    },
    [close, router],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent): void => {
      const meta = event.metaKey || event.ctrlKey;
      if (meta && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") {
        close();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [close]);

  useEffect(() => {
    setActive(0);
  }, [query]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex h-9 items-center gap-2 rounded-full border border-border bg-secondary/70 px-3 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <Search className="size-3.5" />
        <span className="hidden sm:inline">Search</span>
        <kbd className="ml-1 hidden rounded-md border border-border bg-background px-1.5 py-0.5 font-[family-name:var(--font-code)] text-[10px] text-muted-foreground sm:inline">
          ⌘K
        </kbd>
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-background/60 px-4 pt-[12vh] backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Search academy"
          onClick={close}
        >
          <div
            className="glass-panel w-full max-w-lg overflow-hidden rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center gap-2 border-b border-border px-3">
              <Search className="size-4 text-muted-foreground" />
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "ArrowDown") {
                    event.preventDefault();
                    setActive((value) => Math.min(value + 1, results.length - 1));
                  } else if (event.key === "ArrowUp") {
                    event.preventDefault();
                    setActive((value) => Math.max(value - 1, 0));
                  } else if (event.key === "Enter" && results[active]) {
                    event.preventDefault();
                    go(results[active].href);
                  }
                }}
                placeholder="Search tools, frameworks, lessons…"
                className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
              <button type="button" aria-label="Close search" onClick={close} className="p-1 text-muted-foreground">
                <X className="size-4" />
              </button>
            </div>
            <ul className="max-h-80 overflow-y-auto p-2">
              {results.length === 0 ? (
                <li className="px-3 py-6 text-center text-sm text-muted-foreground">No matches</li>
              ) : (
                results.map((hit, index) => (
                  <li key={hit.id}>
                    <button
                      type="button"
                      onMouseEnter={() => setActive(index)}
                      onClick={() => go(hit.href)}
                      className={cn(
                        "flex w-full flex-col rounded-xl px-3 py-2.5 text-left transition-colors",
                        index === active ? "bg-secondary text-foreground" : "text-foreground",
                      )}
                    >
                      <span className="text-sm font-medium">{hit.title}</span>
                      <span className="truncate text-xs text-muted-foreground">{hit.subtitle}</span>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>
      ) : null}
    </>
  );
}
