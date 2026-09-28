import Link from "next/link";
import { CurriculumSidebar } from "@/components/features/CurriculumSidebar";

export default function LearnLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <div className="min-h-dvh">
      <div className="border-b border-border/60 px-4 py-3 lg:px-6">
        <Link href="/" className="text-sm font-medium text-primary hover:underline">
          ← Tools dashboard
        </Link>
      </div>
      <div className="lg:flex">
        <CurriculumSidebar />
        <main id="main" className="min-w-0 flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
