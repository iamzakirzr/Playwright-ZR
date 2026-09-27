import { CurriculumBentoGrid } from "@/components/marketing/CurriculumBentoGrid";
import { HeroSection } from "@/components/marketing/HeroSection";
import { Badge } from "@/components/ui/badge";

export default function HomePage(): React.JSX.Element {
  return (
    <main>
      <HeroSection />
      <CurriculumBentoGrid />
      <section className="mx-auto max-w-6xl px-6 pb-28 sm:px-8">
        <div className="rounded-2xl border border-border/70 bg-card/50 p-8 sm:p-10">
          <Badge variant="accent" className="mb-4">
            Grounded in Playwright-ZR
          </Badge>
          <h2 className="max-w-2xl text-2xl font-semibold tracking-tight sm:text-3xl">
            Premium UI. Real Python QA facts.
          </h2>
          <p className="mt-4 max-w-2xl text-muted-foreground leading-relaxed">
            Gemini&apos;s stack (Next.js 15, Tailwind v4, Shadcn, Motion, Shiki) powers the
            experience. Content stays faithful to this repository: hermetic PR CI, pydantic API
            contracts, calibrated LLM judges, and a fictional store policy so RAG answers cannot
            leak from pre-training.
          </p>
        </div>
      </section>
    </main>
  );
}
