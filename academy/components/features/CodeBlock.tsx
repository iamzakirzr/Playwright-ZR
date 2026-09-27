import { codeToHtml } from "shiki";
import { CopyButton } from "@/components/features/CopyButton";
import { cn } from "@/lib/utils";

export interface CodeBlockProps {
  readonly code: string;
  readonly language: string;
  readonly filename?: string;
  readonly className?: string;
}

export async function CodeBlock({
  code,
  language,
  filename,
  className,
}: CodeBlockProps): Promise<React.JSX.Element> {
  const trimmed = code.trim();
  const html = await codeToHtml(trimmed, {
    lang: language,
    theme: "github-dark-default",
  });

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-border/80 bg-[oklch(0.12_0.02_250)]",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-2">
        <span className="font-[family-name:var(--font-code)] text-xs text-muted-foreground">
          {filename ?? language}
        </span>
        <div className="flex items-center gap-2">
          <span className="font-[family-name:var(--font-code)] text-[10px] tracking-wider text-primary/80 uppercase">
            {language}
          </span>
          <CopyButton value={trimmed} />
        </div>
      </div>
      <div
        className="overflow-x-auto p-4 text-sm [&_pre]:m-0 [&_pre]:bg-transparent! [&_code]:font-[family-name:var(--font-code)]"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
