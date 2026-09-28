import Link from "next/link";
import { Button } from "@/components/ui/button";

export function SiteHeader(): React.JSX.Element {
  return (
    <header className="absolute inset-x-0 top-0 z-20">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 sm:px-8">
        <Link
          href="/"
          className="font-display text-lg font-semibold tracking-tight text-primary-foreground"
        >
          AI QA Academy
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-2">
          <Button
            asChild
            variant="ghost"
            size="sm"
            className="text-primary-foreground/90 hover:bg-white/10 hover:text-primary-foreground"
          >
            <Link href="/learn">Curriculum</Link>
          </Button>
          <Button
            asChild
            size="sm"
            className="bg-white text-foreground hover:bg-white/90"
          >
            <Link href="/learn/framework-overview">Begin</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
