"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";

export function BackButton({
  fallbackHref = "/",
  className,
}: Readonly<{
  fallbackHref?: string;
  className?: string;
}>): React.JSX.Element {
  const router = useRouter();

  return (
    <button
      type="button"
      onClick={() => {
        if (typeof window !== "undefined" && window.history.length > 1) {
          router.back();
          return;
        }
        router.push(fallbackHref);
      }}
      className={cn(
        "inline-flex h-9 items-center gap-1.5 rounded-full border border-border bg-secondary/70 px-3 text-sm font-medium text-foreground transition-colors hover:bg-secondary",
        className,
      )}
    >
      <ArrowLeft className="size-3.5" />
      Back
    </button>
  );
}
