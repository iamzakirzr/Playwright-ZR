import { CurriculumSidebar } from "@/components/features/CurriculumSidebar";

export default function LearnLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <div className="min-h-dvh lg:flex">
      <CurriculumSidebar />
      <main id="main" className="min-w-0 flex-1">
        {children}
      </main>
    </div>
  );
}
