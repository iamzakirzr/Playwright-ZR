import type { LearningCall } from "@/types/tools";

export function LearningCallList({
  calls,
}: Readonly<{
  calls: readonly LearningCall[];
}>): React.JSX.Element {
  return (
    <ol className="space-y-3">
      {calls.map((call, index) => (
        <li key={call.id} className="bezel-card px-4 py-4 sm:px-5">
          <div className="flex flex-wrap items-baseline gap-2">
            <span className="font-[family-name:var(--font-code)] text-xs text-muted-foreground">
              {String(index + 1).padStart(2, "0")}
            </span>
            <code className="font-[family-name:var(--font-code)] text-sm font-medium break-all text-foreground">
              {call.signature}
            </code>
          </div>
          <p className="mt-2 text-sm font-medium text-foreground">{call.summary}</p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{call.why}</p>
          <a
            href={call.docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex text-sm font-medium text-primary hover:underline"
          >
            Official docs →
          </a>
        </li>
      ))}
    </ol>
  );
}
