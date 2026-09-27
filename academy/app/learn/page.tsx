import Link from "next/link";
import { curriculumTracks } from "@/lib/curriculum";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata = {
  title: "Learn",
};

export default function LearnIndexPage(): React.JSX.Element {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-8">
      <h1 className="text-3xl font-semibold tracking-tight">Curriculum</h1>
      <p className="mt-3 max-w-2xl text-muted-foreground">
        Mapped from the VitePress site tracks into the Next.js learn shell. Start with the QA
        framework, then foundations, evals, agents, and MCP.
      </p>

      <div className="mt-10 space-y-8">
        {curriculumTracks.map((track) => (
          <section key={track.id}>
            <div className="mb-4 flex items-center gap-3">
              <h2 className="text-xl font-semibold">{track.title}</h2>
              <Badge variant="outline">{track.lessons.length}</Badge>
            </div>
            <p className="mb-4 text-sm text-muted-foreground">{track.description}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {track.lessons.map((lesson) => (
                <Link key={lesson.slug} href={`/learn/${lesson.slug}`}>
                  <Card className="h-full transition-colors hover:border-primary/50">
                    <CardHeader>
                      <CardTitle className="text-base">{lesson.title}</CardTitle>
                      <CardDescription>{lesson.summary}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <span className="text-xs text-primary">{lesson.minutes} min →</span>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
