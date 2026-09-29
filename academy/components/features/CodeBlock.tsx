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
  const langMap: Record<string, string> = {
    gherkin: "plaintext",
    robotframework: "plaintext",
    text: "plaintext",
    plaintext: "plaintext",
    csharp: "csharp",
    dockerfile: "docker",
    groovy: "java",
  };
  const lang = langMap[language] ?? language;
  let html: string;
  try {
    html = await codeToHtml(trimmed, {
      lang,
      theme: "github-dark-default",
    });
  } catch {
    html = await codeToHtml(trimmed, {
      lang: "plaintext",
      theme: "github-dark-default",
    });
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-[oklch(0.3_0.03_255)] bg-[var(--code-bg)] shadow-sm",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
        <span className="font-[family-name:var(--font-code)] text-xs text-white/65">
          {filename ?? language}
        </span>
        <div className="flex items-center gap-2">
          <span className="font-[family-name:var(--font-code)] text-[10px] tracking-wider text-[oklch(0.78_0.1_185)] uppercase">
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
