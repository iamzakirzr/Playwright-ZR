import { AppShell } from "@/components/dashboard/AppShell";
import { CurriculumSidebar } from "@/components/features/CurriculumSidebar";

export default function LearnLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <AppShell>
      <div className="mx-auto flex max-w-6xl gap-0 lg:gap-2">
        <CurriculumSidebar />
        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </AppShell>
  );
}
