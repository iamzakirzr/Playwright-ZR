import Link from "next/link";

export function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <div className="min-h-dvh">
      <header className="border-b border-border/70 bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link href="/" className="font-display text-lg font-semibold tracking-tight">
            AI QA Academy
          </Link>
          <nav aria-label="Primary" className="flex items-center gap-4 text-sm font-medium">
            <Link href="/" className="text-foreground hover:text-primary">
              Dashboard
            </Link>
            <Link href="/learn" className="text-muted-foreground hover:text-primary">
              Lessons
            </Link>
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
