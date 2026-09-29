import { notFound } from "next/navigation";
import { AppShell } from "@/components/dashboard/AppShell";
import { ToolGuideView } from "@/components/features/ToolGuideView";
import { getToolGuide, listAllGuideParams } from "@/lib/tool-guides";

export function generateStaticParams(): {
  category: string;
  tool: string;
  guide: string;
}[] {
  return listAllGuideParams();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string; tool: string; guide: string }>;
}): Promise<{ title: string }> {
  const { category, tool, guide } = await params;
  const match = getToolGuide(category, tool, guide);
  if (!match) {
    return { title: "Guide" };
  }
  return { title: `${match.guide.title} · ${match.course.tool.name}` };
}

export default async function ToolGuidePage({
  params,
}: {
  params: Promise<{ category: string; tool: string; guide: string }>;
}): Promise<React.JSX.Element> {
  const { category, tool, guide } = await params;
  const match = getToolGuide(category, tool, guide);
  if (!match) {
    notFound();
  }

  return (
    <AppShell>
      <main id="main">
        <ToolGuideView course={match.course} guide={match.guide} />
      </main>
    </AppShell>
  );
}
