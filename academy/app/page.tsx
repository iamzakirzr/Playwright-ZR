import { CurriculumBentoGrid } from "@/components/marketing/CurriculumBentoGrid";
import { HeroSection } from "@/components/marketing/HeroSection";
import { StudioPromise } from "@/components/marketing/StudioPromise";

export default function HomePage(): React.JSX.Element {
  return (
    <main id="main">
      <HeroSection />
      <CurriculumBentoGrid />
      <StudioPromise />
    </main>
  );
}
