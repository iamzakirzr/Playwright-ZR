import Link from "next/link";

export function StudioPromise(): React.JSX.Element {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-28 sm:px-8">
      <div className="grid gap-10 border-t border-border pt-16 md:grid-cols-[1.2fr_1fr] md:gap-16">
        <div>
          <p className="font-[family-name:var(--font-code)] text-xs tracking-[0.2em] text-primary uppercase">
            Why this academy
          </p>
          <h2 className="font-display mt-3 max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">
            Numbers you can reproduce — not slideware.
          </h2>
          <p className="mt-5 max-w-xl text-muted-foreground leading-relaxed">
            Lessons stay faithful to Playwright-ZR: hermetic PR CI, pydantic API
            contracts, calibrated LLM judges, and a fictional store policy so RAG
            answers cannot leak from pre-training. If a tip cites a score, a test
            in this repository produced it.
          </p>
        </div>
        <ul className="space-y-5 text-sm text-ink-soft">
          <li className="border-b border-border pb-4">
            <span className="font-medium text-foreground">UI · API · SQL first</span>
            <p className="mt-1 text-muted-foreground">
              Classic automation layers before AI evals — same fixtures the AI suites reuse.
            </p>
          </li>
          <li className="border-b border-border pb-4">
            <span className="font-medium text-foreground">Judges that earn the gate</span>
            <p className="mt-1 text-muted-foreground">
              Calibration on known-good and known-bad answers before any metric may block a build.
            </p>
          </li>
          <li>
            <span className="font-medium text-foreground">Open source courseware</span>
            <p className="mt-1 text-muted-foreground">
              Browse the{" "}
              <Link href="/learn" className="text-primary underline-offset-4 hover:underline">
                full curriculum
              </Link>{" "}
              or jump into the{" "}
              <a
                href="https://github.com/iamzakirzr/Playwright-ZR"
                className="text-primary underline-offset-4 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                repository
              </a>
              .
            </p>
          </li>
        </ul>
      </div>
    </section>
  );
}
