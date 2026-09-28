import { DiscoverHome } from "@/components/marketing/DiscoverHome";
import { StudioPromise } from "@/components/marketing/StudioPromise";
import { WelcomeHero } from "@/components/marketing/WelcomeHero";

export default function HomePage(): React.JSX.Element {
  return (
    <main id="main">
      <WelcomeHero />
      <DiscoverHome />
      <StudioPromise />
    </main>
  );
}
