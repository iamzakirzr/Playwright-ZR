import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LessonView } from "@/components/features/LessonView";
import { allLessons, getLesson } from "@/lib/curriculum";

interface LessonPageProps {
  readonly params: Promise<{ slug: string }>;
}

export function generateStaticParams(): { slug: string }[] {
  return allLessons.map((lesson) => ({ slug: lesson.slug }));
}

export async function generateMetadata({ params }: LessonPageProps): Promise<Metadata> {
  const { slug } = await params;
  const lesson = getLesson(slug);
  if (!lesson) {
    return { title: "Lesson" };
  }
  return {
    title: lesson.title,
    description: lesson.summary,
  };
}

export default async function LessonPage({
  params,
}: LessonPageProps): Promise<React.JSX.Element> {
  const { slug } = await params;
  const lesson = getLesson(slug);
  if (!lesson) {
    notFound();
  }
  return <LessonView lesson={lesson} />;
}
