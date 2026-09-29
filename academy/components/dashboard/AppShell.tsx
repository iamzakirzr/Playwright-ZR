"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Flame } from "lucide-react";
import { BackButton } from "@/components/ui/back-button";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { SearchModal } from "@/components/navigation/search-modal";

export function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <div className="min-h-dvh">
      <div className="sticky top-0 z-40 px-3 pt-3 sm:px-4">
        <header className="glass-header mx-auto flex max-w-5xl flex-col gap-3 rounded-2xl px-3 py-3 sm:px-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2 sm:gap-3">
              {!isHome ? <BackButton /> : null}
              <Link
                href="/"
                className="font-display truncate text-base font-semibold tracking-tight sm:text-lg"
              >
                AI QA Academy
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 rounded-full border border-border bg-secondary/70 px-2.5 py-1 text-xs font-medium text-muted-foreground sm:inline-flex">
                <Flame className="size-3.5 text-amber-500" />
                Streak 7
              </span>
              <SearchModal />
              <ThemeToggle />
            </div>
          </div>
          {!isHome ? (
            <div className="border-t border-border px-1 pt-2">
              <Breadcrumbs />
            </div>
          ) : null}
        </header>
      </div>
      {children}
    </div>
  );
}
