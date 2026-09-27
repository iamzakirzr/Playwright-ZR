"use client";

import { useEffect, useState } from "react";
import { codeToHtml } from "shiki";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { CodeSample } from "@/types/curriculum";

export interface CodeBlockTabsProps {
  readonly samples: readonly CodeSample[];
}

export function CodeBlockTabs({ samples }: CodeBlockTabsProps): React.JSX.Element {
  const [htmlByFile, setHtmlByFile] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    async function highlight(): Promise<void> {
      const entries = await Promise.all(
        samples.map(async (sample) => {
          const html = await codeToHtml(sample.code.trim(), {
            lang: sample.language,
            theme: "github-dark-default",
          });
          return [sample.filename, html] as const;
        }),
      );
      if (!cancelled) {
        setHtmlByFile(Object.fromEntries(entries));
      }
    }
    void highlight();
    return () => {
      cancelled = true;
    };
  }, [samples]);

  if (samples.length === 0) {
    return <></>;
  }

  const defaultValue = samples[0].filename;

  return (
    <Tabs defaultValue={defaultValue} className="w-full">
      <TabsList className="mb-2 h-auto flex-wrap justify-start gap-1">
        {samples.map((sample) => (
          <TabsTrigger key={sample.filename} value={sample.filename}>
            {sample.filename}
          </TabsTrigger>
        ))}
      </TabsList>
      {samples.map((sample) => (
        <TabsContent key={sample.filename} value={sample.filename}>
          <div className="overflow-hidden rounded-xl border border-border/80 bg-[oklch(0.12_0.02_250)]">
            <div
              className="overflow-x-auto p-4 text-sm [&_pre]:m-0 [&_pre]:bg-transparent! [&_code]:font-[family-name:var(--font-code)]"
              dangerouslySetInnerHTML={{
                __html:
                  htmlByFile[sample.filename] ??
                  `<pre><code>${sample.code}</code></pre>`,
              }}
            />
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
