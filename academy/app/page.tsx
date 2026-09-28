import { AppShell } from "@/components/dashboard/AppShell";
import { CategoryCard } from "@/components/dashboard/CategoryCard";
import { toolCategories } from "@/lib/tools-catalog";

export default function DashboardPage(): React.JSX.Element {
  return (
    <AppShell>
      <main id="main" className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <p className="text-xs font-semibold tracking-[0.18em] text-primary uppercase">
          Dashboard
        </p>
        <h1 className="font-display mt-3 max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
          Learn QA tools by category
        </h1>
        <p className="mt-3 max-w-2xl text-muted-foreground leading-relaxed">
          Automation, frameworks, API & performance, databases, cloud/CI, Salesforce,
          AI evals, and collaboration — each tool links to its official documentation.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {toolCategories.map((category) => (
            <CategoryCard key={category.id} category={category} />
          ))}
        </div>
      </main>
    </AppShell>
  );
}
