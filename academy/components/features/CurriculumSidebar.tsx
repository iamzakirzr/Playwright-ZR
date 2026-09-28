"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { ChevronLeft, ChevronRight, Menu, X } from "lucide-react";
import { curriculumTracks } from "@/lib/curriculum";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function CurriculumSidebar(): React.JSX.Element {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const panelId = useId();

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const nav = (
    <nav aria-label="Curriculum" className="space-y-6">
      {curriculumTracks.map((track) => (
        <div key={track.id}>
          {!collapsed ? (
            <p className="mb-2 px-2 font-[family-name:var(--font-code)] text-[10px] tracking-[0.18em] text-muted-foreground uppercase">
              {track.title}
            </p>
          ) : null}
          <ul className="space-y-1">
            {track.lessons.map((lesson) => {
              const href = `/learn/${lesson.slug}`;
              const active = pathname === href;
              return (
                <li key={lesson.slug}>
                  <Link
                    href={href}
                    onClick={() => setOpen(false)}
                    title={lesson.title}
                    aria-label={lesson.title}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "block rounded-2xl px-2 py-2 text-sm transition-colors",
                      active
                        ? "bg-primary/15 font-medium text-primary"
                        : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                      collapsed && "truncate text-center text-xs",
                    )}
                  >
                    {collapsed ? lesson.title.charAt(0) : lesson.title}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );

  return (
    <>
      <div className="flex items-center justify-between border-b border-border/60 bg-[oklch(0.97_0.015_185)] px-4 py-3 lg:hidden">
        <Link href="/" className="font-display text-sm font-semibold text-foreground">
          AI QA Academy
        </Link>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="rounded-2xl"
          aria-label={open ? "Close curriculum" : "Open curriculum"}
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X /> : <Menu />}
        </Button>
      </div>

      {open ? (
        <div id={panelId} className="max-h-[70dvh] overflow-y-auto border-b border-border/60 bg-card p-4 lg:hidden">
          {nav}
        </div>
      ) : null}

      <aside
        className={cn(
          "sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-border/70 bg-surface-elevated/95 p-4 lg:flex",
          collapsed ? "w-[72px]" : "w-72",
        )}
      >
        <div className="mb-6 flex items-center justify-between gap-2">
          {!collapsed ? (
            <Link href="/" className="font-display text-sm font-semibold tracking-tight text-foreground">
              AI QA Academy
            </Link>
          ) : (
            <Link
              href="/"
              className="font-display text-xs font-semibold text-primary"
              aria-label="AI QA Academy"
            >
              AQ
            </Link>
          )}
          <Button
            type="button"
            size="icon"
            variant="ghost"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-pressed={collapsed}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? <ChevronRight /> : <ChevronLeft />}
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto">{nav}</div>
      </aside>
    </>
  );
}
