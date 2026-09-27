import type { BentoTopic, CurriculumTrack, Lesson } from "@/types/curriculum";

export const bentoTopics: readonly BentoTopic[] = [
  {
    id: "playwright-ui",
    title: "Playwright UI Testing",
    description:
      "Page objects, web-first assertions, storage_state, traces, and self-healing locators from Playwright-ZR.",
    href: "/learn/ui-testing",
    accent: "cyan",
    span: "wide",
  },
  {
    id: "api-contracts",
    title: "Typed API Automation",
    description:
      "Service clients + pydantic schemas so renamed or retyped fields fail the suite — even on HTTP 200.",
    href: "/learn/api-testing",
    accent: "teal",
    span: "normal",
  },
  {
    id: "llm-judges",
    title: "LLM-as-a-Judge Calibration",
    description:
      "A judge may gate only after it separates known-good from known-bad. This repo's 3B judge fails eight metrics.",
    href: "/learn/judges-and-calibration",
    accent: "mint",
    span: "tall",
  },
  {
    id: "rag-eval",
    title: "RAG Architecture Evaluation",
    description:
      "Retrieve → augment → generate, then score faithfulness, abstention, and IR metrics on a fictional store policy.",
    href: "/learn/rag",
    accent: "slate",
    span: "normal",
  },
] as const;

const uiTesting: Lesson = {
  slug: "ui-testing",
  title: "UI testing with Playwright",
  summary:
    "Page objects, locators, fixtures, network interception, cross-browser runs, and AI-adjacent helpers in Playwright-ZR.",
  track: "framework",
  minutes: 18,
  tip: [
    "Page objects in pages/ own locators and actions; tests call methods like login_as().",
    "Prefer role/name/test-id locators and web-first expect(...) — no sleeps.",
    "Failures keep a trace, screenshot, and video; visual compare and self-healing are opt-in helpers.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A UI test has two jobs that change at different speeds. What the user can do changes rarely. How the page is built changes every sprint. A page object separates them: when a selector changes you edit one line in one class, not forty tests.",
    },
    {
      heading: "Page objects and locators",
      body: "Every page extends BasePage in pages/base_page.py, which gives it open(), by_test_id() and expect_loaded(). Locators are created once in __init__. Sauce Demo marks elements with data-test attributes, which survive restyling better than CSS classes.",
      code: {
        language: "python",
        filename: "pages/login_page.py",
        code: `class LoginPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username = self.by_test_id("username")
        self.password = self.by_test_id("password")
        self.submit = self.by_test_id("login-button")

    def login_as(self, user: str, password: str) -> None:
        self.username.fill(user)
        self.password.fill(password)
        self.submit.click()`,
      },
    },
    {
      heading: "What ships in this repo",
      body: "Hermetic PR CI runs unit, SQL, essentials, healing, and AI offline suites without Sauce Demo or Restful Booker. Full UI + BDD matrices and external booker jobs stay on main.",
      bullets: [
        "Fixtures inject ready page objects; storage_state logs in once per session",
        "StaticSite serves a local app with network interception for hermetic UI",
        "Self-healing locators: an LLM proposes, validation decides (tests/ui/healing/)",
      ],
    },
  ],
  relatedRepoPaths: ["pages/", "tests/ui/", "mobile/driver_factory.py"],
};

const apiTesting: Lesson = {
  slug: "api-testing",
  title: "API testing with service objects",
  summary:
    "Service clients, pydantic contract validation, auth fixtures, and Faker factories for Restful Booker.",
  track: "framework",
  minutes: 16,
  tip: [
    "One client class per API, one method per endpoint — tests never build URLs.",
    "pydantic schemas turn every response into a typed object; contract breaks fail loudly.",
    "Restful Booker can return HTTP 200 with a reason body for bad credentials — negative tests pin that.",
  ],
  sections: [
    {
      heading: "Contract validation",
      body: "assert response.status == 200 says nothing about the body. If the API renames firstname to first_name, a status check stays green and a consumer breaks in production. Parsing into a strict schema catches that on the first run.",
      code: {
        language: "python",
        filename: "api/clients/booking_client.py",
        code: `def create_booking(self, booking: Booking) -> CreatedBooking:
    response = self._request.post("/booking", data=booking.model_dump())
    response.raise_for_status()
    return CreatedBooking.model_validate(response.json())`,
      },
    },
    {
      heading: "Auth and data",
      body: "A token is created once per session and attached by authenticate(). Test data comes from Faker factories (seeded and replayable); every created booking is deleted afterwards.",
    },
  ],
  relatedRepoPaths: ["api/", "tests/api/", "models/"],
};

const judges: Lesson = {
  slug: "judges-and-calibration",
  title: "Judges and calibration",
  summary:
    "How LLM-as-a-judge works, why every judge must prove it separates known-good from known-bad before it may gate a build, and what failed calibration in this repository.",
  track: "evals",
  minutes: 22,
  tip: [
    "An LLM judge is a second model that scores the first model's answer.",
    "Calibration runs the judge on a hand-written good answer and a hand-written bad answer first.",
    "Default llama3.2:3b passed faithfulness / G-Eval completeness / conversation completeness; failed eight other metrics.",
  ],
  sections: [
    {
      heading: "The thermometer test",
      body: "Before you trust a new thermometer, you put it in ice water and boiling water. An LLM judge is a thermometer for answer quality. Calibration is the ice-and-boiling-water check on answers you wrote by hand.",
    },
    {
      heading: "Biases that corrupt automated QA",
      body: "Position, recency, provenance, and score-rubric biases systematically skew LLM judges. A paid-grade curriculum teaches swapping A/B order, stripping provenance tags, and randomizing rubrics — then proving the gate still holds on calibrated metrics only.",
      bullets: [
        "Position bias: favor options by prompt placement — swap A/B during evals",
        "Recency bias: prefer temporally newer labels — strip dates from judge prompts",
        "Provenance bias: favor Expert/Human over LLM/Unknown tags",
        "Score rubric bias: ascending vs descending scales shift grade distributions",
      ],
    },
    {
      heading: "Repo rule",
      body: "A judged metric is only trusted with a judge that passes calibration for it. Calibrate on the machine that gates: role adherence passed locally on the 3B judge and scored 0.0 / 0.0 in CI.",
      code: {
        language: "python",
        filename: "ai/evaluators/factory.py",
        code: `evaluation_steps = [
    "List the facts in 'retrieval context' needed to fully answer 'input'.",
    "Check which of those facts appear in 'actual output'.",
    "Heavily penalise every needed fact that is missing, especially prices.",
    "Do not penalise brevity when all needed facts are present.",
]`,
      },
    },
  ],
  relatedRepoPaths: ["ai/evaluators/", "tests/ai/", "docs/learning-path/06-ai-evals-fundamentals.md"],
};

const rag: Lesson = {
  slug: "rag",
  title: "Retrieval-augmented generation (RAG)",
  summary:
    "How RAG retrieves passages, augments the prompt, and generates an answer — and how this repository tests grounding, faithfulness, and retrieval quality.",
  track: "foundations",
  minutes: 20,
  tip: [
    "RAG: retrieve → augment → generate. Failures: miss, ignore context, hallucinate, incomplete, stale.",
    "Test each failure separately: IR metrics, faithfulness, abstention, counterfactual probes.",
    "This repo uses a fictional store policy (45-day returns) so correct answers cannot come from pre-training.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "An LLM only knows training data and cannot tell you where a fact came from. RAG is an open-book exam: look up relevant pages, put them in front of the model with \"answer from these\".",
    },
    {
      heading: "How it works here",
      body: "Retrieve top k=3 via hybrid search. If nothing clears the floor, abstain. Otherwise augment with the grounded_qa v2 system prompt and generate with qwen2.5:1.5b, returning answer + passages for judging.",
      code: {
        language: "python",
        filename: "apps/shop_assistant (grounded_qa)",
        code: `# System prompt (grounded_qa v2) — abbreviated
# "Answer ONLY from the CONTEXT below. Include every relevant fact
#  from it, such as prices, limits and exceptions. If the context
#  does not contain the answer, reply exactly:
#  I don't know based on the provided information."`,
      },
    },
    {
      heading: "Agent lesson",
      body: "In an agent, make retrieval a fixed graph step unless the model is strong enough to decide to search. qwen2.5:1.5b called the search tool 0 of 6 times and invented \"30 days\".",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "ai/", "site/foundations/rag.md"],
};

const overview: Lesson = {
  slug: "framework-overview",
  title: "Tour of the QA framework",
  summary:
    "Page objects, API service clients, SQL repositories, cross-layer tests, and a CI pipeline that runs on merge.",
  track: "framework",
  minutes: 12,
  tip: [
    "UI, API, and SQL share fixtures and settings from config/settings.py.",
    "PR CI is hermetic; Sauce Demo and Restful Booker suites are main-only.",
    "Install extras: pip install -e '.[ui,apps,ai,visual,mobile]' as needed.",
  ],
  sections: [
    {
      heading: "Layers",
      body: "Playwright-ZR is a Python framework: UI page objects, API clients with pydantic, SQL repositories, BDD, mobile (lazy Appium), and AI evals with calibrated judges. Packaging extras keep PR CI lean.",
    },
  ],
  relatedRepoPaths: ["README.md", ".github/workflows/tests.yml", "pyproject.toml"],
};

const agentsLesson: Lesson = {
  slug: "what-is-an-agent",
  title: "What is an agent?",
  summary:
    "Agents decide which tools to call. This academy tests state, trajectory, and text — then builds with shared TOOLS across shop assistant variants.",
  track: "agents",
  minutes: 14,
  tip: [
    "An agent is a model plus tools plus a loop (or graph) that chooses actions.",
    "Test trajectory (which tools, in what order) separately from final text.",
    "Dual shop agents share TOOLS from apps/shop_assistant/shared.py.",
  ],
  sections: [
    {
      heading: "Testing agents",
      body: "Score state transitions, tool trajectories, and answer text independently. Weak models may skip retrieval and invent policy numbers — catch that with trajectory assertions before judging prose.",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "site/agents/"],
};

const mcpLesson: Lesson = {
  slug: "how-mcp-works",
  title: "How MCP works",
  summary:
    "Model Context Protocol servers expose tools to models. Contract-test the server, then drive a browser with Playwright MCP.",
  track: "mcp",
  minutes: 12,
  tip: [
    "MCP standardizes how hosts discover and call tools.",
    "Contract-test tool schemas the same way you contract-test HTTP APIs.",
    "Playwright MCP is one way to give an agent a real browser.",
  ],
  sections: [
    {
      heading: "Why QA cares",
      body: "When a model can call tools, your test surface expands: schema drift, unauthorized tools, and unsafe side effects. Treat MCP servers like APIs with stricter discoverability.",
    },
  ],
  relatedRepoPaths: ["site/mcp/", "ai/safety/patterns.py"],
};

export const allLessons: readonly Lesson[] = [
  overview,
  uiTesting,
  apiTesting,
  rag,
  judges,
  agentsLesson,
  mcpLesson,
];

export const curriculumTracks: readonly CurriculumTrack[] = [
  {
    id: "framework",
    title: "QA framework",
    description: "UI, API, SQL, hybrid, and hermetic CI from Playwright-ZR.",
    lessons: [overview, uiTesting, apiTesting],
  },
  {
    id: "foundations",
    title: "Foundations",
    description: "LLMs, prompting, search, and RAG grounded in runnable tests.",
    lessons: [rag],
  },
  {
    id: "evals",
    title: "Evaluating AI",
    description: "Metrics, calibrated judges, performance, and red teaming.",
    lessons: [judges],
  },
  {
    id: "agents",
    title: "Agents",
    description: "State, trajectory, and text — plus shop assistant patterns.",
    lessons: [agentsLesson],
  },
  {
    id: "mcp",
    title: "MCP",
    description: "Protocol basics, contract tests, Playwright MCP.",
    lessons: [mcpLesson],
  },
] as const;

export function getLesson(slug: string): Lesson | undefined {
  return allLessons.find((lesson) => lesson.slug === slug);
}

export function getAdjacentLessons(slug: string): {
  prev: Lesson | undefined;
  next: Lesson | undefined;
} {
  const index = allLessons.findIndex((lesson) => lesson.slug === slug);
  if (index < 0) {
    return { prev: undefined, next: undefined };
  }
  return {
    prev: index > 0 ? allLessons[index - 1] : undefined,
    next: index < allLessons.length - 1 ? allLessons[index + 1] : undefined,
  };
}
