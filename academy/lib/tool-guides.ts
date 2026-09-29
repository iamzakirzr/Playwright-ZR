import { getLesson } from "@/lib/curriculum";
import { getToolSamples } from "@/lib/samples";
import { toolCategories } from "@/lib/tools-catalog";
import type {
  AcademyTool,
  LearningCall,
  ToolCategory,
  ToolCourse,
  ToolGuide,
} from "@/types/tools";

/** Curriculum lesson slugs related to a tool (cross-links into /learn). */
const relatedLessonsByTool: Readonly<Record<string, readonly string[]>> = {
  playwright: ["ui-testing", "framework-overview", "playwright-mcp"],
  selenium: ["ui-testing", "framework-overview"],
  cypress: ["ui-testing", "framework-overview"],
  accelq: ["framework-overview", "ci-cd", "adoption-playbook"],
  cucumber: ["framework-overview"],
  appium: ["ui-testing"],
  squish: ["ui-testing", "framework-overview"],
  pytest: ["framework-overview", "api-testing"],
  testng: ["framework-overview"],
  nunit: ["framework-overview"],
  mocha: ["framework-overview"],
  robot: ["framework-overview"],
  webdriverio: ["ui-testing"],
  nightwatch: ["ui-testing"],
  isafe: ["framework-overview", "api-testing"],
  bdd: ["framework-overview"],
  "api-testing": ["api-testing", "framework-overview"],
  jmeter: ["api-testing", "performance-evals"],
  k6: ["api-testing", "performance-evals"],
  artillery: ["api-testing", "performance-evals"],
  sql: ["sql-and-hybrid"],
  postgresql: ["sql-and-hybrid"],
  snowflake: ["sql-and-hybrid"],
  "azure-devops": ["ci-cd"],
  jenkins: ["ci-cd"],
  docker: ["ci-cd"],
  aws: ["ci-cd"],
  azure: ["ci-cd"],
  git: ["ci-cd"],
  bitbucket: ["ci-cd"],
  "service-cloud": ["api-testing", "adoption-playbook"],
  "experience-cloud": ["ui-testing", "adoption-playbook"],
  flows: ["api-testing", "framework-overview"],
  deepeval: ["evaluating-llms", "judges-and-calibration"],
  ragas: ["evaluating-llms", "rag", "judges-and-calibration"],
  langsmith: ["observability", "evaluating-llms"],
  rag: ["rag", "ai-search"],
  "agentic-ai": ["what-is-an-agent", "testing-agents", "building-agents"],
  "github-copilot": ["prompting", "adoption-playbook"],
  "ms-copilot": ["prompting", "ai-in-qa-at-companies"],
  jira: ["adoption-playbook"],
  stlc: ["framework-overview", "adoption-playbook"],
};

function overviewGuide(category: ToolCategory, tool: AcademyTool): ToolGuide {
  return {
    id: "overview",
    title: `Getting started with ${tool.name}`,
    summary: `Course orientation for ${tool.name}: what it is, when QA teams use it, and how this academy path is structured.`,
    minutes: 6,
    order: 0,
    kind: "overview",
    docsUrl: tool.docsUrl,
    docsLabel: tool.docsLabel,
    tip: [
      `${tool.name} sits in the ${category.title} track of this academy.`,
      "Complete the concept guides in order, then finish the practice checklist.",
      "Official vendor docs are linked as reference — learning happens here first.",
    ],
    sections: [
      {
        heading: "What this tool is for",
        body: tool.summary,
        bullets: [
          `Category: ${category.title}`,
          `Official reference hub: ${tool.docsLabel}`,
          `${tool.calls.length} core concepts in this course, plus practice`,
        ],
      },
      {
        heading: "How this academy course works",
        body: "Each tool is a mini-course. You stay on AI QA Academy for explanations, examples, and exercises. Vendor documentation is available when you want the authoritative API surface.",
        bullets: [
          "Read Getting started (this guide)",
          "Work through each concept guide — cards on the tool page open these lessons",
          "Finish Practice & checklist to prove you can apply the ideas",
          "Optionally deepen via related curriculum lessons under /learn",
        ],
      },
      {
        heading: "Skills you will build",
        body: "By the end of this course you should be able to explain the tool’s role in a QA stack and apply each highlighted concept in a real workflow.",
        bullets: tool.calls.map(
          (call) => `${call.signature} — ${call.summary}`,
        ),
      },
      {
        heading: "Suggested study session",
        body: "Block 25–40 minutes: skim this overview, complete one concept guide with the practice prompt, then note one question to verify against official docs.",
        bullets: [
          "Keep a scratch pad for commands or UI paths you try",
          "Prefer small reproducible experiments over reading alone",
          "Mark the practice checklist items as you complete them",
        ],
      },
    ],
  };
}

function conceptGuide(
  tool: AcademyTool,
  call: LearningCall,
  index: number,
): ToolGuide {
  const samples = getToolSamples(tool.id, call.id);
  const langs = [...new Set(samples.map((s) => s.language))];
  return {
    id: call.id,
    title: call.signature,
    summary: call.summary,
    minutes: samples.length ? 10 : 7,
    order: index + 1,
    kind: "concept",
    signature: call.signature,
    docsUrl: call.docsUrl,
    docsLabel: tool.docsLabel,
    codeSamples: samples,
    tip: [
      call.why,
      samples.length
        ? `Work the ${langs.join(" + ")} examples on this page — type them, then adapt to your app.`
        : "Primary learning is on this page with exercises you can run locally.",
      "Finish the practice drill before moving to the next function.",
    ],
    sections: [
      {
        heading: "Why this matters in QA",
        body: `${call.why} In ${tool.name}, mastering “${call.signature}” is a building block you will reuse across suites, reviews, and production gates.`,
        bullets: [
          call.summary,
          "Treat this as a skill, not a one-off API lookup",
          "Be ready to explain it in a PR or test-plan review",
        ],
      },
      {
        heading: "Concept deep dive",
        body: `In ${tool.name}, “${call.signature}” means: ${call.summary} ${call.why}`,
        bullets: [
          `Tool context: ${tool.summary}`,
          `Primary signal: ${call.summary}`,
          `Why teams invest here: ${call.why}`,
          "Map inputs → behavior → observable outcome → failure modes before coding",
        ],
      },
      {
        heading: "How to apply it",
        body: `Build a minimal ${tool.name} exercise centered on ${call.signature}, then add one negative path. Prefer a real journey (auth, CRUD, contract, pipeline stage, eval case) over a toy demo.`,
        bullets: [
          `Bootstrap ${tool.name} against a known-good environment`,
          `Implement the happy path that requires ${call.signature}`,
          "Add one failure case (timeout, 4xx/5xx, empty data, bad locator, low score)",
          "Capture evidence you would attach to a PR or defect",
        ],
      },
      ...(samples.length
        ? [
            {
              heading: "Advanced coding examples",
              body: `Production-minded ${langs.join(" / ")} examples for ${call.signature}. Study both when present — teams often mix Python services with TypeScript UI/API tests.`,
              bullets: [
                "Type the example once without copy-paste",
                "Swap URLs, selectors, and credentials for your environment",
                "Add one assertion that would catch a real regression",
              ],
            },
          ]
        : []),
      {
        heading: "Practice exercise",
        body: `Design a 10-minute drill that forces you to use ${call.signature} deliberately.`,
        bullets: [
          `Write a short goal statement that requires ${call.signature}`,
          "Implement or configure the smallest working version",
          "Break it on purpose once, then fix it using the tool’s feedback",
          "Note one insight you would teach a junior teammate",
        ],
      },
      {
        heading: "Common mistakes",
        body: "Most learners stumble on the same patterns. Check these before blaming the tool.",
        bullets: [
          "Skipping waits / readiness and calling the result “flaky”",
          "Hard-coding environment details instead of config or fixtures",
          "Asserting implementation details instead of user-visible outcomes",
          "Reading vendor docs without a concrete experiment to validate",
        ],
      },
    ],
  };
}

function patternsGuide(tool: AcademyTool, order: number): ToolGuide {
  const samples = getToolSamples(tool.id, "patterns");
  return {
    id: "patterns",
    title: `${tool.name} patterns that scale`,
    summary: `Reusable design patterns for keeping ${tool.name} suites maintainable as coverage grows.`,
    minutes: samples.length ? 12 : 9,
    order,
    kind: "concept",
    docsUrl: tool.docsUrl,
    docsLabel: tool.docsLabel,
    codeSamples: samples,
    tip: [
      "Prefer composition and clear names over copy-pasted flows.",
      "A pattern is only good if a teammate can extend it next week.",
      samples.length
        ? "Advanced TypeScript / Python pattern code is below — refactor a real flow against it."
        : "Official docs describe APIs — this guide focuses on how QA teams structure work.",
    ],
    sections: [
      {
        heading: "Structure before syntax",
        body: `In ${tool.name}, long-term speed comes from how you organize suites, fixtures, and shared helpers — not from memorizing every API flag.`,
        bullets: [
          "Separate arrange / act / assert clearly in each scenario",
          "Share setup through fixtures, factories, or page/action objects",
          "Keep environment config out of hard-coded strings",
          "Name tests after user-visible outcomes",
        ],
      },
      {
        heading: "Stability patterns",
        body: "Flakes are usually design bugs. Bake readiness and isolation into the default path.",
        bullets: [
          "Wait on conditions the product guarantees, not fixed sleeps",
          "Isolate data so parallel runs do not collide",
          "Prefer deterministic seeds or known fixtures for evals and UI",
          "Fail with actionable messages (what was expected vs observed)",
        ],
      },
      ...(samples.length
        ? [
            {
              heading: "Advanced coding examples",
              body: `Pattern-level ${tool.name} code in TypeScript and/or Python — page objects, factories, clients, and suite structure.`,
            },
          ]
        : []),
      {
        heading: "Practice: refactor one messy flow",
        body: `Take an existing ${tool.name} scenario (or draft one) and extract at least one reusable helper or page/action object.`,
        bullets: [
          "Before: note duplication or brittle selectors/queries",
          "After: one shared abstraction + two call sites",
          "Document the pattern in a two-line comment for your team",
        ],
      },
    ],
  };
}

function deliveryGuide(tool: AcademyTool, order: number): ToolGuide {
  const samples = getToolSamples(tool.id, "delivery");
  return {
    id: "delivery",
    title: `Shipping ${tool.name} with the team`,
    summary: `How ${tool.name} shows up in PRs, CI gates, and release evidence — not only on a local laptop.`,
    minutes: samples.length ? 11 : 8,
    order,
    kind: "concept",
    docsUrl: tool.docsUrl,
    docsLabel: tool.docsLabel,
    codeSamples: samples,
    tip: [
      "If it only runs on your machine, it is a demo — not a quality gate.",
      "Define the signal you will trust before you automate the run.",
      samples.length
        ? "Use the CI / config samples below as a starting point for your pipeline."
        : "Vendor docs cover runners; this guide covers team delivery habits.",
    ],
    sections: [
      {
        heading: "Make runs repeatable",
        body: `Decide how anyone on the team starts ${tool.name}: scripts, containers, pipeline tasks, or a shared workspace.`,
        bullets: [
          "One command (or pipeline job) to install and execute",
          "Pinned versions for browsers, runners, or CLI tools",
          "Secrets via env / vault — never committed credentials",
          "Artifacts: reports, traces, logs, or metric summaries",
        ],
      },
      {
        heading: "Gate thoughtfully",
        body: "Not every check belongs on every PR. Map smoke vs deep suites to the risk of the change.",
        bullets: [
          "PR: fast smoke that protects the main journey",
          "Nightly / main: broader regression or load profiles",
          "Release: evidence pack reviewers can open without re-running",
          "Owner: who triages failures within one business day",
        ],
      },
      ...(samples.length
        ? [
            {
              heading: "Advanced coding examples",
              body: `Delivery configs and scripts for ${tool.name} — TypeScript/Python where teams wire CI, plus pipeline YAML when relevant.`,
            },
          ]
        : []),
      {
        heading: "Practice: write the gate contract",
        body: `Draft a short “definition of done” for ${tool.name} in your squad.`,
        bullets: [
          "Which suite blocks merge?",
          "What artifact proves a green run?",
          "Who is on-call when it fails?",
          "Where do you look in official docs when the runner API changes?",
        ],
      },
    ],
  };
}

function practiceGuide(tool: AcademyTool, order: number): ToolGuide {
  return {
    id: "practice",
    title: `${tool.name} practice checklist`,
    summary: `Capstone drills for the ${tool.name} course — prove you can apply every concept without leaving the academy learning path.`,
    minutes: 12,
    order,
    kind: "practice",
    docsUrl: tool.docsUrl,
    docsLabel: tool.docsLabel,
    tip: [
      "Complete every concept guide before this checklist.",
      "Evidence beats vibes: keep links, screenshots, or command output.",
      "Official docs are a reference shelf — your checklist answers live here.",
    ],
    sections: [
      {
        heading: "Course mastery checklist",
        body: `Tick these only when you can demonstrate them in ${tool.name} (sandbox or project).`,
        bullets: tool.calls.map(
          (call, index) =>
            `${String(index + 1).padStart(2, "0")}. Demonstrate ${call.signature}: ${call.summary}`,
        ),
      },
      {
        heading: "Integration drill",
        body: `Combine at least two concepts from this course into one realistic ${tool.name} workflow (e.g. navigate + locate + assert, or request + schema + auth).`,
        bullets: [
          "Name the user or system story you are validating",
          "List the concepts you composed and why that order",
          "Record pass/fail criteria before you run",
          "Capture one failure and your root-cause note",
        ],
      },
      {
        heading: "Review questions",
        body: "Answer in your own words — this is how interview and design reviews work.",
        bullets: [
          `When is ${tool.name} the right tool versus an adjacent option in this category?`,
          "What signal tells you a run is flaky versus incorrectly designed?",
          "How would you gate a release with evidence from this tool?",
          `Where do you look in ${tool.docsLabel} when APIs change?`,
        ],
      },
      {
        heading: "Next steps",
        body: "Promote this course into team practice: add the workflow to CI, share a short demo, or link a related academy curriculum lesson for deeper theory.",
        bullets: [
          "Bookmark this tool page as your course home",
          "Revisit any weak concept guide before the next sprint",
          "Use related /learn lessons when you need framework-level depth",
        ],
      },
    ],
  };
}

export function buildToolCourse(
  category: ToolCategory,
  tool: AcademyTool,
): ToolCourse {
  const conceptGuides = tool.calls.map((call, index) =>
    conceptGuide(tool, call, index),
  );
  const afterConcepts = conceptGuides.length + 1;
  const guides = [
    overviewGuide(category, tool),
    ...conceptGuides,
    patternsGuide(tool, afterConcepts),
    deliveryGuide(tool, afterConcepts + 1),
    practiceGuide(tool, afterConcepts + 2),
  ];
  return {
    categoryId: category.id,
    categoryTitle: category.title,
    tool,
    guides,
    relatedLessonSlugs: relatedLessonsByTool[tool.id] ?? [],
  };
}

export function getToolCourse(categoryId: string, toolId: string): ToolCourse | undefined {
  const category = toolCategories.find((item) => item.id === categoryId);
  if (!category) {
    return undefined;
  }
  const tool = category.tools.find((item) => item.id === toolId);
  if (!tool) {
    return undefined;
  }
  return buildToolCourse(category, tool);
}

export function getToolGuide(
  categoryId: string,
  toolId: string,
  guideId: string,
): { course: ToolCourse; guide: ToolGuide } | undefined {
  const course = getToolCourse(categoryId, toolId);
  if (!course) {
    return undefined;
  }
  const guide = course.guides.find((item) => item.id === guideId);
  if (!guide) {
    return undefined;
  }
  return { course, guide };
}

export function getAdjacentGuides(
  categoryId: string,
  toolId: string,
  guideId: string,
): { prev?: ToolGuide; next?: ToolGuide } {
  const course = getToolCourse(categoryId, toolId);
  if (!course) {
    return {};
  }
  const index = course.guides.findIndex((guide) => guide.id === guideId);
  if (index < 0) {
    return {};
  }
  return {
    prev: index > 0 ? course.guides[index - 1] : undefined,
    next: index < course.guides.length - 1 ? course.guides[index + 1] : undefined,
  };
}

export function listAllGuideParams(): {
  category: string;
  tool: string;
  guide: string;
}[] {
  return toolCategories.flatMap((category) =>
    category.tools.flatMap((tool) => {
      const course = buildToolCourse(category, tool);
      return course.guides.map((guide) => ({
        category: category.id,
        tool: tool.id,
        guide: guide.id,
      }));
    }),
  );
}

export { getLesson };
