import Link from "next/link";

export function StudioPromise(): React.JSX.Element {
  return (
    <section className="mx-auto max-w-lg px-5 pb-24 sm:px-8 lg:max-w-3xl">
      <div className="rounded-[2rem] bg-[linear-gradient(160deg,oklch(0.9_0.05_185),oklch(0.96_0.02_185))] px-6 py-10 sm:px-8">
        <p className="text-xs font-semibold tracking-[0.18em] text-primary uppercase">
          Why this academy
        </p>
        <h2 className="font-display mt-3 max-w-xl text-2xl font-semibold tracking-tight sm:text-3xl">
          Organized practice — not slideware.
        </h2>
        <p className="mt-4 max-w-xl text-muted-foreground leading-relaxed">
          Lessons stay faithful to Playwright-ZR: hermetic PR CI, pydantic API
          contracts, calibrated LLM judges, and a fictional store policy so RAG
          answers cannot leak from pre-training. Grow advanced QA skills at your
          own pace — no timetable required.
        </p>
        <ul className="mt-8 space-y-4 text-sm">
          <li className="border-b border-foreground/10 pb-4">
            <span className="font-medium text-foreground">UI · API · SQL first</span>
            <p className="mt-1 text-muted-foreground">
              Classic automation layers before AI evals — same fixtures the AI suites reuse.
            </p>
          </li>
          <li className="border-b border-foreground/10 pb-4">
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
