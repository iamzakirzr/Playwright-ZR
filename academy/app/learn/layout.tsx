import { AppShell } from "@/components/dashboard/AppShell";
import { CurriculumSidebar } from "@/components/features/CurriculumSidebar";

export default function LearnLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <AppShell>
      {/* flex-col on small screens: CurriculumSidebar's mobile "Lessons" bar must
          stack above content. A row flex made that bar a left column (~25% width)
          and shoved the lesson body into the remaining gutter. */}
      <div className="mx-auto flex max-w-6xl flex-col gap-0 lg:flex-row lg:gap-2">
        <CurriculumSidebar />
        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </AppShell>
  );
}
