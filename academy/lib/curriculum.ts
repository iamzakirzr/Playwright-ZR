import type {
  BentoTopic,
  CurriculumTrack,
  DiscoverCard,
  Lesson,
} from "@/types/curriculum";

/** Pastel Discover course cards — core QA headings (not Data Science / ML). */
export const discoverCards: readonly DiscoverCard[] = [
  {
    id: "playwright",
    title: "Playwright",
    shortLabel: "UI",
    description:
      "Page objects, web-first expect(), traces when a run fails.",
    href: "/learn/ui-testing",
    accent: "mint",
    filter: "playwright",
  },
  {
    id: "typed-api",
    title: "Typed API",
    shortLabel: "Contracts",
    description:
      "Service clients + pydantic — renamed fields fail even on HTTP 200.",
    href: "/learn/api-testing",
    accent: "sand",
    filter: "api",
  },
  {
    id: "llm-judges",
    title: "LLM Judges",
    shortLabel: "Evals",
    description:
      "Calibrate known-good vs known-bad before a judge gates a build.",
    href: "/learn/judges-and-calibration",
    accent: "blush",
    filter: "judges",
  },
  {
    id: "rag",
    title: "RAG",
    shortLabel: "Retrieval",
    description:
      "Faithfulness and retrieval scores on a policy the model cannot memorize.",
    href: "/learn/rag",
    accent: "sage",
    filter: "rag",
  },
  {
    id: "agents",
    title: "Agents",
    shortLabel: "Loops",
    description:
      "Tool loops, trajectories, and shop-assistant patterns in this repo.",
    href: "/learn/what-is-an-agent",
    accent: "sky",
    filter: "agents",
  },
  {
    id: "mcp",
    title: "MCP",
    shortLabel: "Tools",
    description:
      "Contract-test MCP servers the same way you test any API surface.",
    href: "/learn/how-mcp-works",
    accent: "lilac",
    filter: "mcp",
  },
] as const;

export const bentoTopics: readonly BentoTopic[] = [
  {
    id: "playwright-ui",
    title: "Playwright UI Testing",
    description:
      "Own locators in page objects, assert with web-first expect(), keep traces when a run fails.",
    href: "/learn/ui-testing",
    accent: "cyan",
    span: "wide",
  },
  {
    id: "api-contracts",
    title: "Typed API Automation",
    description:
      "Service clients + pydantic: a renamed field fails the suite even when status is still 200.",
    href: "/learn/api-testing",
    accent: "teal",
    span: "normal",
  },
  {
    id: "llm-judges",
    title: "LLM-as-a-Judge Calibration",
    description:
      "Prove the judge separates known-good from known-bad before it may gate a build. Eight metrics need a stronger judge here.",
    href: "/learn/judges-and-calibration",
    accent: "mint",
    span: "tall",
  },
  {
    id: "rag-eval",
    title: "RAG Architecture Evaluation",
    description:
      "Retrieve, augment, generate — then score faithfulness and retrieval on a policy the model cannot know from training.",
    href: "/learn/rag",
    accent: "slate",
    span: "normal",
  },
] as const;

const lesson_framework_overview: Lesson = {
  slug: "framework-overview",
  title: "A tour of the framework",
  summary: "The Playwright-ZR repository folder by folder - its layers, its three rules, how markers are applied, how to run each suite, and the learning path.",
  track: "framework",
  minutes: 12,
  tip: [
    "The repository is a layered Python test framework: tests say what to check; page objects, service clients and repositories say how.",
    "It covers UI (Playwright), API, SQL, cross-layer (\"hybrid\"), BDD, visual, self-healing, mobile, an MCP server and AI testing, all runnable locally without paid keys.",
    "Three rules: tests say *what*, objects say *how*; configuration comes from one place (config/settings.py); every AI threshold is calibrated.",
    "Markers come from the folder a test lives in, so pytest -m api or make test-api selects a layer with no decorators.",
    "The docs/learning-path/ chapters are a course through the code; this site explains the ideas behind them.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A test suite grows in two directions: more tests, and more kinds of tests. Without structure, both turn into copy-paste. This framework uses one idea everywhere: put the \"how\" in an object and keep the test about the \"what\". A page object knows the login form's selectors. A service client knows the booking API's URLs. A repository knows the SQL. The test reads like a user story.",
    },
    {
      heading: "How it works",
      body: "Tests never build these objects themselves. They ask for them by name as pytest fixtures, and the fixtures in conftest.py construct them from the settings. That is dependency injection, and it is why swapping a browser, a base URL or a model is a configuration change, not a code change.",
    },
  ],
  relatedRepoPaths: ["README.md", "pyproject.toml", ".github/workflows/tests.yml", "site/framework/overview.md"],
};

const lesson_ui_testing: Lesson = {
  slug: "ui-testing",
  title: "UI testing with Playwright",
  summary: "Page objects, locators and web-first assertions, fixtures, saved login state, network interception, cross-browser runs, failure evidence, visual testing, self-healing locators and mobile emulation in Playwright-ZR.",
  track: "framework",
  minutes: 18,
  tip: [
    "Page objects in pages/ own the locators and actions; tests call methods like login_as() and assert on the result.",
    "Use user-facing locators (test ids, roles, names) and web-first assertions (expect(...)), which wait and retry, so tests need no sleeps.",
    "Fixtures hand tests ready-made page objects; storage_state logs in once per session; StaticSite serves a local app with network interception.",
    "The same tests run on Chromium, Firefox and WebKit, and on emulated phones. Failures keep a trace, screenshot and video.",
    "Two AI-adjacent helpers: visual comparison (pixels decide) and self-healing locators (an LLM proposes, validation decides).",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A UI test has two jobs that change at different speeds. What the user can do (log in, add to cart, check out) changes rarely. How the page is built (selectors, markup) changes every sprint. A page object separates them: when a selector changes you edit one line in one class, not forty tests.",
    },
    {
      heading: "How it works",
      body: "Every page extends BasePage in pages/base_page.py, which gives it open(), by_test_id() and expect_loaded(). Locators are created once in __init__. Playwright locators are lazy (they find the element when used, not when created), so this costs nothing. Sauce Demo marks its elements with data-test attributes, which survive restyling better than CSS classes.",
    },
    {
      heading: "Page objects and locators",
      body: "Every page extends BasePage in pages/base_page.py. Locators are created once in __init__. Sauce Demo marks elements with data-test attributes.",
      code: {
        language: "python",
        filename: "pages/login_page.py",
        code: `class LoginPage(BasePage):
    path = "/"

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self.username_input = self.by_test_id("username")
        self.password_input = self.by_test_id("password")
        self.login_button = self.by_test_id("login-button")
        self.error_message = self.by_test_id("error")

    def login_as(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()`,
      },
    },
  ],
  relatedRepoPaths: ["pages/", "tests/ui/", "pages/login_page.py", "site/framework/ui-testing.md"],
};

const lesson_api_testing: Lesson = {
  slug: "api-testing",
  title: "API testing with service objects",
  summary: "Service clients, pydantic contract validation, authentication, negative tests and Faker test data for the Restful Booker API in Playwright-ZR.",
  track: "framework",
  minutes: 16,
  tip: [
    "A service object (client) is the page object idea for HTTP: one class per API, one method per endpoint. Tests never build URLs or headers.",
    "pydantic schemas turn every response into a typed object. A renamed, missing or retyped field fails loudly, even when the status is 200. That is contract testing for free.",
    "Auth is a fixture: a token is created once per session and attached by authenticate().",
    "Negative tests pin down how the API really signals failure. Restful Booker reports bad credentials with HTTP 200 and a reason in the body.",
    "Test data comes from factories (Faker, seeded and replayable), and every created booking is deleted afterwards.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "An API test that says request.post(\"https://.../booking\", data={...}) mixes three things: where the API lives, what the request looks like, and what the test is checking. When the URL or the auth scheme changes, every test changes. The service-object pattern moves the first two into a client, so the test keeps only the third.",
    },
    {
      heading: "How it works",
      body: "The second idea is contract validation. assert response.status == 200 says nothing about the body. If the API renames firstname to first_name, a status check stays green and some consumer breaks in production. Parsing the body into a strict schema catches that on the first run.",
    },
    {
      heading: "Service client + pydantic body",
      body: "BookingClient methods return Playwright APIResponse. Request bodies come from pydantic models via model_dump(by_alias=True). Contract checks parse the JSON in the test.",
      code: {
        language: "python",
        filename: "api/booking_client.py",
        code: `class BookingClient(BaseClient):
    RESOURCE = "/booking"

    def create_booking(self, booking: Booking) -> APIResponse:
        """Create a booking from a validated model."""
        return self.post(self.RESOURCE, data=booking.model_dump(by_alias=True))`,
      },
    },
  ],
  relatedRepoPaths: ["api/booking_client.py", "api/schemas/", "tests/api/", "site/framework/api-testing.md"],
};

const lesson_sql_and_hybrid: Lesson = {
  slug: "sql-and-hybrid",
  title: "SQL and hybrid tests",
  summary: "Repository-based SQL tests over a seeded SQLite database, rolled-back transactions for isolation, and cross-layer tests that create through the API and verify in the database.",
  track: "framework",
  minutes: 14,
  tip: [
    "Repositories in db/repositories/ hold every SQL statement; tests call methods like find_by_username(). Every query uses ? placeholders.",
    "The database is SQLite, seeded from db/seed.sql, in memory by default. No server to install.",
    "Isolation: each test runs inside a transaction that the db fixture rolls back, so tests never see each other's writes and need no cleanup.",
    "SQL tests check constraints, cascades, aggregates and reconciliation (orphans, price mismatches), not just \"a row exists\".",
    "Hybrid tests cross layers: create a booking through the API, read it back, store it, and compare every column with the request. They test the mapping, where renames and type conversions break.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "The UI can say \"saved\" while the database says otherwise. The API can return 201 while a field is silently truncated. Testing each layer alone misses the seams between them. This part of the framework does two things: tests the data layer directly, and tests that data survives the trip from one layer to the next.",
    },
    {
      heading: "How it works",
      body: "The repository pattern is the same idea as page objects and service clients: keep the \"how\" (SQL) out of the test, keep the \"what\" (the rule being checked) in it.",
    },
  ],
  relatedRepoPaths: ["db/", "tests/sql/", "tests/hybrid/", "site/framework/sql-and-hybrid.md"],
};

const lesson_ci_cd: Lesson = {
  slug: "ci-cd",
  title: "CI/CD",
  summary: "Playwright-ZR's CI policy - hermetic lint/unit/SQL/essentials/AI-offline on every PR, Sauce Demo and Restful Booker only on merge to main, live AI and mobile by manual dispatch.",
  track: "framework",
  minutes: 10,
  tip: [
    "PR + main: .github/workflows/tests.yml runs lint and a hermetic job (unit, SQL, local Playwright essentials, healing, AI offline). No Sauce Demo, Restful Booker, or Ollama on the PR gate (api/hybrid are main-only).",
    "Main only: the same workflow also runs API (Restful Booker) and UI/BDD (Sauce Demo) after merge.",
    "Manual: .github/workflows/optional-suites.yml holds mobile, live AI, Docker and Allure, started from the Actions tab.",
    "Local PR gate: make lint and make test-hermetic.",
    "Ollama in Docker Compose is pinned to 0.34.4 (same as the live AI CI job).",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A pipeline is a promise: \"if this is green, the change is safe enough\". Running everything on every change sounds safest, but it is slow, and for LLM tests it is noisy: a small model on a different machine can give a different answer at temperature 0. A red build that is red for no reason trains people to ignore red builds.",
    },
    {
      heading: "How it works",
      body: "So this repository splits its suites by how deterministic and how expensive they are. Pull requests get a hermetic signal; public demo sites and live models stay off the critical path.",
    },
  ],
  relatedRepoPaths: [".github/workflows/tests.yml", "conftest.py", "site/framework/ci-cd.md"],
};

const lesson_how_llms_work: Lesson = {
  slug: "how-llms-work",
  title: "LLMs from the inside",
  summary: "Tokens, next-token prediction, sampling, embeddings, messages, JSON mode and tool calling, explained for testers with the local Ollama models this repository uses.",
  track: "foundations",
  minutes: 15,
  tip: [
    "A large language model (LLM) reads text as tokens and does one thing: predict the next token. A reply is that prediction run in a loop.",
    "Sampling settings (temperature, top-p, seed) decide how the next token is picked. Temperature 0 makes runs repeatable on one machine, not across machines or model versions. This repository saw that in CI.",
    "Embeddings turn text into vectors. Cosine similarity between vectors measures \"same meaning\", and the repo uses it for search and for cheap, deterministic checks.",
    "Chat APIs take messages (system, user, assistant) and can be asked for JSON or offered tools. Each of those is a contract you can test.",
    "The repo runs small open models locally with Ollama: qwen2.5:1.5b is the bot under test, llama3.2:3b and qwen2.5:7b are judges.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Think of the phone keyboard that suggests the next word. An LLM is that idea scaled up: a neural network trained on a huge amount of text to answer one question, \"given everything so far, what comes next?\". It has no database of facts and no rule engine. Everything it \"knows\" is stored as patterns in billions of numbers (its parameters, or weights).",
    },
    {
      heading: "How it works",
      body: "That single fact explains most of what a tester sees:",
    },
  ],
  relatedRepoPaths: ["site/foundations/how-llms-work.md", "docs/learning-path/06-ai-evals-fundamentals.md"],
};

const lesson_prompting: Lesson = {
  slug: "prompting",
  title: "Prompting and prompt testing",
  summary: "How system prompts, few-shot examples and constraints shape a model's output, and how this repository versions prompts as code and tests their behaviour.",
  track: "foundations",
  minutes: 12,
  tip: [
    "A prompt is the text you send the model: a system message with rules and context, plus the user's message. It is the main lever you have on behaviour.",
    "Few-shot examples and explicit constraints (label sets, word limits, JSON keys) make small models far more predictable.",
    "Treat prompts as versioned code: one registry, a version per behavioural change, and a snapshot test that fails on any unreviewed wording change.",
    "Test prompt behaviour against the live model: accuracy on labelled inputs, format adherence, limits, A/B against the previous version, and consistency across paraphrases.",
    "Real results here: few-shot intent_classifier v2 routed 14/14 against v1's 10/14, and summarizer v2 kept every number in 16/16 runs against 4 to 8 of 16 for v1.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A prompt is a specification written in English, read by a component that follows it most of the time. If you have written test cases for a vague requirement, you already know the problem: whatever is ambiguous gets interpreted differently. A small model like qwen2.5:1.5b fills gaps in the prompt with whatever looks likely.",
    },
    {
      heading: "How it works",
      body: "So a prompt needs what any specification needs: clear rules, examples, a defined output format, and a regression suite. One word changed in a prompt can change behaviour as much as a code change. Unlike code, nobody's compiler complains.",
    },
  ],
  relatedRepoPaths: ["site/foundations/prompting.md", "apps/shop_assistant/"],
};

const lesson_prompt_chaining: Lesson = {
  slug: "prompt-chaining",
  title: "Prompt chaining",
  summary: "Splitting one LLM task into small steps, why errors propagate between steps, and how to test each link and the whole chain with a scripted model and a live one.",
  track: "foundations",
  minutes: 10,
  tip: [
    "A prompt chain splits one big request into small steps, each with its own prompt or plain code: classify, route, rewrite, retrieve, answer.",
    "Small steps are easier for small models and easier to test, because each step has a narrow contract.",
    "Chains fail between links: a wrong label sends the question down the wrong path, a lossy rewrite finds the wrong document, and the final answer is wrong for a reason three steps earlier.",
    "Test each link on its own with a scripted fake model (fast, offline, deterministic), then test the live chain link by link and end to end.",
    "The repo's support chain is intent → handoff → rewrite → retrieve → answer, with a per-step trace and errors tagged with the failing step's name.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Think of an assembly line instead of one craftsperson. Instead of one prompt that must understand the question, decide whether it is in scope, search the knowledge base and write an answer, you build stations. Each station does one job and hands its output to the next.",
    },
    {
      heading: "How it works",
      body: "A chain has three advantages for a tester:",
    },
  ],
  relatedRepoPaths: ["site/foundations/prompt-chaining.md"],
};

const lesson_ai_search: Lesson = {
  slug: "ai-search",
  title: "AI search and its testing",
  summary: "Keyword (BM25), semantic (embedding) and hybrid retrieval, and how to test search quality with labelled queries, IR metrics, robustness probes and off-domain checks.",
  track: "foundations",
  minutes: 14,
  tip: [
    "Keyword search (BM25) scores documents by shared words. It is exact and explainable, and misses paraphrases.",
    "Semantic search compares embeddings, so it finds meaning without shared words, and can drift on exact terms and negation.",
    "Hybrid search fuses both rankings. This repo uses Reciprocal Rank Fusion (RRF), the common production default.",
    "Test search like a ranking system, not like a chatbot: a labelled query set plus IR metrics (Recall@k, MRR, nDCG@k gate here; Precision@k and hit rate are implemented too).",
    "Also test robustness (typos, casing, synonyms, paraphrases) and the negative space: off-topic queries must return nothing, so the bot abstains instead of guessing.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Before a RAG bot can answer \"is express delivery expensive?\", something has to find the passage that says \"Express shipping costs $14.99\". That something is search, and it is the step most often at fault when an AI answer is wrong. If the right passage is not retrieved, no prompt can save the answer.",
    },
    {
      heading: "How it works",
      body: "Search is also the easiest part of an AI system to test well. It is deterministic, it needs no LLM, and the information-retrieval field has decades of standard metrics. A tester can hold it to numeric quality bars in seconds.",
    },
  ],
  relatedRepoPaths: ["site/foundations/ai-search.md", "apps/shop_assistant/"],
};

const lesson_rag: Lesson = {
  slug: "rag",
  title: "Retrieval-augmented generation (RAG)",
  summary: "How RAG retrieves passages, puts them in the prompt and generates an answer, how it fails, and how this repository tests grounding, faithfulness and retrieval quality.",
  track: "foundations",
  minutes: 20,
  tip: [
    "RAG answers a question in three steps: retrieve relevant passages, augment the prompt with them, generate an answer from them.",
    "It fails in four typical ways: the right passage is not retrieved, the model ignores the context, the model adds claims the context doesn't support (hallucination), or the source data is stale.",
    "Test each failure separately: IR metrics for retrieval, faithfulness for grounding, abstention and counterfactual probes for \"context beats prior knowledge\", fact coverage for completeness.",
    "A judged metric gates only on a judge that passed calibration for it. Here, faithfulness and completeness gate on llama3.2:3b; relevancy, correctness, hallucination and the contextual metrics need qwen2.5:7b.",
    "In an agent, make retrieval a fixed graph step unless the model is strong enough to decide to search. qwen2.5:1.5b called the search tool 0 of 6 times and invented \"30 days\".",
  ],
  sections: [
    {
      heading: "The idea",
      body: "An LLM only knows what was in its training data, and it cannot tell you where a fact came from. RAG is an open-book exam: before the model answers, the application looks up the relevant pages and puts them in front of it with the instruction \"answer from these\".",
    },
    {
      heading: "How it works",
      body: "That gives three benefits: answers about private or recent data (your store's return policy), fewer invented facts, and a way to check the answer, because you know exactly which text it was supposed to use. That last point is what makes RAG testable.",
    },
    {
      heading: "How it works here",
      body: "Retrieve top k=3 via hybrid search. Below the floor → abstain. Otherwise augment with the grounded_qa system prompt and generate, returning answer + passages for judging.",
      code: {
        language: "python",
        filename: "ai/prompts/library.json",
        code: `# grounded_qa system prompt (abbreviated from the shop assistant)
# "Answer ONLY from the CONTEXT below. Include every relevant fact
#  from it, such as prices, limits and exceptions. If the context
#  does not contain the answer, reply exactly:
#  I don't know based on the provided information."`,
      },
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "ai/prompts/library.json", "tests/ai/rag/", "site/foundations/rag.md"],
};

const lesson_evaluating_llms: Lesson = {
  slug: "evaluating-llms",
  title: "Evaluating LLM output",
  summary: "Why exact-match assertions fail for LLMs, the families of checks that replace them, and which check fits which requirement.",
  track: "evals",
  minutes: 14,
  tip: [
    "An LLM rarely says the same thing twice in the same words, so assert answer == expected breaks on correct answers.",
    "Replace it with a stack of checks, cheapest first: rules (keywords, JSON schema, word limits, refusal), embeddings (does it mean the same?), reference overlap (BLEU/ROUGE, only where wording matters) and LLM judges (faithfulness, relevancy, G-Eval).",
    "In this repo a correct paraphrase scores ROUGE-L 0.32 and BLEU 0.08. Overlap metrics punish correct answers.",
    "A golden dataset (question, context, reference answer, required facts) is the test data every check runs against.",
    "Rule of thumb from the README: use a rule if a rule can express the requirement, a classifier if one exists, and an LLM judge only for what needs understanding.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Think of grading an essay exam instead of a multiple-choice sheet. A multiple-choice sheet has one right mark per question: a machine can grade it. An essay has many right answers. A good grader asks narrower questions instead. Did the student mention the three key facts? Did they stay on topic? Did they invent anything that is not in the textbook?",
    },
    {
      heading: "How it works",
      body: "Testing an LLM is essay grading. Ask the shop assistant \"How many days do I have to return an item?\" and all of these are correct:",
    },
  ],
  relatedRepoPaths: ["ai/evaluators/", "tests/ai/", "site/evals/evaluating-llms.md"],
};

const lesson_judges_and_calibration: Lesson = {
  slug: "judges-and-calibration",
  title: "Judges and calibration",
  summary: "How LLM-as-a-judge works, why every judge must prove it separates known-good from known-bad answers before it may gate a build, and what failed calibration in this repository.",
  track: "evals",
  minutes: 22,
  tip: [
    "An LLM judge is a second model that scores the first model's answer for a property that needs understanding (faithfulness, relevancy, role adherence).",
    "A judge is a test oracle, and oracles can be wrong. Calibration runs the judge on a hand-written good answer and a hand-written bad answer first. It may gate only if it scores them on the right sides of the threshold.",
    "In this repo the default llama3.2:3b judge passed calibration for faithfulness, G-Eval completeness and conversation completeness, and failed it for eight other metrics. Those run on a qwen2.5:7b judge or are replaced by rules.",
    "Calibrate on the machine that gates: role adherence passed locally on the 3B judge and scored 0.0 / 0.0 in CI.",
    "Read the score, not the reason. Judges write reasons that contradict their own verdicts.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Before you trust a new thermometer, you put it in ice water and in boiling water. If it reads 0 and 100, you use it. If it reads 40 in both, you throw it away, however confident its display looks.",
    },
    {
      heading: "How it works",
      body: "An LLM judge is a thermometer for answer quality. Calibration is the ice-and-boiling-water check. You already know the right verdict for two inputs because you wrote them by hand: a reference answer that is correct, and an answer that contradicts the context. A judge that cannot separate those two cannot be trusted on live output, where you do not know the right verdict.",
    },
    {
      heading: "G-Eval completeness rubric (factory)",
      body: "From ai/evaluators/factory.py — the completeness rubric the default 3B judge passed calibration for (threshold 0.7).",
      code: {
        language: "python",
        filename: "ai/evaluators/factory.py",
        code: `evaluation_steps=[
    "List the facts in 'retrieval context' that are needed to fully answer 'input'.",
    "Check which of those facts appear in 'actual output'.",
    "Heavily penalise every needed fact that is missing, especially prices, limits and exceptions.",
    "Do not penalise brevity when all needed facts are present.",
]`,
      },
    },
    {
      heading: "Why judges fail here",
      body: "Self-preference bias is why the bot (qwen2.5:1.5b) and default judge (llama3.2:3b) are different families. Small models are noisy and fail structured JSON parsing. Role adherence scored 0.0/0.0 in CI on the 3B judge. Eight metrics need qwen2.5:7b or a rule/classifier instead of the default judge.",
      bullets: [
        "Default judge llama3.2:3b: faithfulness, G-Eval completeness, conversation completeness",
        "Strong judge qwen2.5:7b (opt-in): relevancy, correctness, hallucination, contextual metrics, role adherence, turn relevancy, judged safety",
        "Knowledge retention failed on both judges — replaced by RetentionProbeMetric",
        "Calibrate where the gate runs; read the score, not the reason",
      ],
    },
  ],
  relatedRepoPaths: ["ai/evaluators/factory.py", "tests/ai/rag/test_faithfulness.py", "ai/evaluators/judge.py", "site/evals/judges-and-calibration.md"],
};

const lesson_production_metrics: Lesson = {
  slug: "production-metrics",
  title: "Production metrics",
  summary: "The metrics that matter once an AI feature is live, and how this repository encodes them as regression budgets against recorded baselines.",
  track: "evals",
  minutes: 12,
  tip: [
    "Once an AI feature is live, the questions change from \"does this answer pass?\" to \"how often does it succeed, how often does it fail badly, and is that getting worse?\"",
    "The core metrics: task success, answer completeness, hallucination rate, refusal and over-refusal rate, attack success rate, latency percentiles, cost, and user feedback.",
    "Each metric becomes a budget: a limit recorded from a measured baseline, with headroom. The build fails when the metric crosses the budget, not when it misses perfection.",
    "This repo encodes budgets in config/settings.py: guarded_max_asr = 0.0, raw_model_max_asr = 0.85, max_over_refusal_rate = 0.25, min_mean_helpful_coverage = 0.60, min_mean_completeness = 0.55.",
    "Drift (the model, the server, the prompt or the data changing under you) is caught by pinning versions and re-running the same budgets.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A pass/fail test answers \"is this one answer acceptable?\". A production metric answers \"what share of answers are acceptable, and is the share moving?\". A web team already thinks this way about error rates: nobody expects zero 500s across a million requests, but everyone wants an alert when the rate doubles.",
    },
    {
      heading: "How it works",
      body: "AI features need the same shift, because an LLM never reaches 100%. A 1.5B model in this repo reliably states the fact a question needs but often drops the extras. You cannot make that test green by wishing. You *can* record where it is today, and fail the build if it gets worse.",
    },
  ],
  relatedRepoPaths: ["tests/ai/rag/test_production_metrics.py", "site/evals/production-metrics.md"],
};

const lesson_performance_evals: Lesson = {
  slug: "performance-evals",
  title: "Performance and reliability evals",
  summary: "Latency, time to first token, token budgets, cost, throughput, and reproducibility across seeds and paraphrases, and how this repository turns them into test budgets.",
  track: "evals",
  minutes: 10,
  tip: [
    "An answer can be correct and still unusable: too slow, too long, too expensive, or different every time you ask.",
    "Measure latency (total, and time to first token when streaming), tokens (the unit of cost), throughput, and reproducibility (same input, same output) and stability (different seeds or phrasings, same meaning).",
    "This repo gates each answer at max_latency_ms = 60000 and max_completion_tokens = 150, asserts identical output at temperature 0 with a fixed seed, and asserts similarity of at least 0.6 across seeds and paraphrases.",
    "Budgets depend on the hardware. CPU CI runners are slow and produce different small-model output from a laptop, so budgets are generous and the model server version is pinned.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A tester already knows non-functional requirements from web apps: a page must load in under two seconds, an API must handle a hundred requests per second. LLM features have the same kind of contract, with two twists.",
    },
    {
      heading: "How it works",
      body: "First, cost and length are linked. Hosted models charge per token (a chunk of a word, roughly three quarters of an English word on average). A longer answer is slower *and* more expensive. So a token budget is a cost control and a latency control at once.",
    },
  ],
  relatedRepoPaths: ["site/evals/performance-evals.md"],
};

const lesson_observability: Lesson = {
  slug: "observability",
  title: "Observability for AI features",
  summary: "Logging prompts, responses and tool calls, tracing LLM and tool spans, LangSmith and OpenTelemetry GenAI conventions, and turning production traces into regression tests; what this repository implements and what is general practice.",
  track: "evals",
  minutes: 10,
  tip: [
    "When an AI feature misbehaves, the final answer rarely tells you why. You need the prompt, the retrieved context, every tool call, the answer, the model, the latency and the tokens: a record of what happened.",
    "Logging stores those records. Tracing links them into a tree of spans (one per LLM call, retrieval or tool call) under one request. Dashboards and alerts watch the aggregates.",
    "This repository records test-time evidence: every LLM exchange is attached to the Allure report, agents return their tool trajectory (AgentTurn, ToolCallRecord), chains record a StepTrace per step, and LangSmith tracing can be switched on with two environment variables.",
    "Not implemented here: OpenTelemetry instrumentation, production dashboards, alerts and traffic sampling. This page teaches them as general practice, clearly labelled.",
    "The payoff loop: production traces become labelled cases, labelled cases become regression tests.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A flight data recorder does not prevent crashes. It makes every crash explainable, and each explanation becomes a new check for the next flight. Observability does the same job for an AI feature.",
    },
    {
      heading: "How it works",
      body: "For a classic web service, a log line with a status code and a stack trace is often enough. For an LLM feature it is not: the \"bug\" may be a passage the retriever did not find, a tool the agent called with a placeholder argument, or a prompt version nobody reviewed. None of that is in the final answer. You have to record the steps.",
    },
  ],
  relatedRepoPaths: ["site/evals/observability.md"],
};

const lesson_red_teaming: Lesson = {
  slug: "red-teaming",
  title: "Red teaming and guardrails",
  summary: "Attack categories for LLM apps, layered guardrails, attack success rate and over-refusal, and how this repository attacks its own chatbot and measures the defence.",
  track: "evals",
  minutes: 14,
  tip: [
    "Red teaming means attacking your own AI feature on purpose: prompt injection (direct and hidden in documents), system-prompt leaks, PII extraction, jailbreaks, harmful content, toxicity, bias and off-topic misuse.",
    "The key metric is attack success rate (ASR): the share of attacks that got through. Its partner is over-refusal: the share of legitimate questions wrongly refused. Both must be low.",
    "Defend in layers: a regex filter for known attack phrasings, a moderator LLM that classifies each message, and output redaction as a last line. This repo's GuardedChatbot does exactly that.",
    "Measured here on qwen2.5:1.5b: raw model 9 of 14 attacks succeeded; guarded 0 of 14, with 1 of 8 legitimate questions refused.",
    "Guards cause false positives too. A bare DAN regex refused every customer named Dan until code review caught it.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A penetration tester attacks a web app before criminals do. Red teaming is the same job for an LLM feature, with one difference: the attack surface is plain language. Anyone who can type can try \"ignore all previous instructions\", and any document the bot reads can carry hidden instructions.",
    },
    {
      heading: "How it works",
      body: "The categories this repo covers, mapped to the OWASP Top 10 for LLM Applications:",
    },
  ],
  relatedRepoPaths: ["ai/safety/patterns.py", "tests/ai/", "site/evals/red-teaming.md"],
};

const lesson_what_is_an_agent: Lesson = {
  slug: "what-is-an-agent",
  title: "What an agent is",
  summary: "An agent is an LLM that can call tools in a loop, with memory and state; how that differs from a chatbot or a chain, and the ways it fails.",
  track: "agents",
  minutes: 12,
  tip: [
    "An agent is an LLM plus tools it may call, run in a loop, with memory of the conversation and access to some state (a cart, a database, a file system).",
    "The loop is simple: the model reads the situation, either answers or asks for a tool call; the program runs the tool and shows the result to the model; repeat until it answers.",
    "A chatbot only talks. A chain runs fixed steps you wrote. An agent decides its own next step, which is what makes it useful and what makes it hard to test.",
    "Agents fail in ways chatbots can't: wrong tool, wrong arguments, claiming an action that never happened, forgetting context, looping, and acting outside their job.",
    "The repository's running example is the Sauce Demo shop assistant, which adds, removes and shows cart items by calling tools.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A plain LLM is a text predictor (see how LLMs work). Given a conversation, it writes the next message. On its own it cannot *do* anything: it cannot read your cart, charge a card or open a browser. It can only produce text.",
    },
    {
      heading: "How it works",
      body: "An agent is what you get when you let that text trigger actions. You describe some functions to the model (\"add_to_cart(product, quantity): add a product to the shopping cart\"). Instead of answering in prose, the model can now reply with a structured request: \"call add_to_cart with product = Sauce Labs Backpack, quantity = 2\". Your program runs the function, and hands the result back to the model. The model reads the result and decides what to do next.",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "site/agents/", "site/agents/what-is-an-agent.md"],
};

const lesson_testing_agents: Lesson = {
  slug: "testing-agents",
  title: "Testing AI agents",
  summary: "How to test a tool-calling agent - state first, then the tool trajectory, then the text - with single-turn and multi-turn tests, scripted and live.",
  track: "agents",
  minutes: 14,
  tip: [
    "Rank your oracles: state (read the cart through the API) beats trajectory (which tools, which arguments) beats text (what the agent said).",
    "Trajectory can be scored without a judge: DeepEval's ToolCorrectnessMetric compares called tools and arguments to expected ones, by rule.",
    "Multi-turn tests drive a whole conversation (run_conversation builds a DeepEval ConversationalTestCase) and check memory with a rule-based RetentionProbeMetric.",
    "Two layers: scripted-model unit tests pin the loop's logic in milliseconds; live tests check what a real model actually does.",
    "Put the per-turn trajectory in every assertion message. Small models behave differently on different machines, and the trajectory is how you find out why.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "When you test a web form, you don't trust the green \"Saved!\" banner. You query the database. An agent's reply is that banner, generated by a model that is allowed to be wrong. So an agent test asks three questions, in order of trust:",
    },
    {
      heading: "How it works",
      body: "1. State. Did the world change as the user asked? Read it from the system of record, never from the chat. 2. Trajectory. Did the agent get there the right way? The trajectory is the ordered list of tool calls with their arguments. A correct cart reached by a wrong path (two adds and a remove instead of one add) is a bug waiting to happen. 3. Text. Only for what the user must be told: the total, how many are left, a refusal. Check it with rules where you can, and with a calibrated judge only where you must.",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/shared.py", "tests/ai/", "site/agents/testing-agents.md"],
};

const lesson_building_agents: Lesson = {
  slug: "building-agents",
  title: "Building an agent by hand",
  summary: "A walk through the repository's hand-written shop assistant agent - tool schemas, the bounded loop, argument repair, the live cart in the prompt, the false-claim nudge, the scope guard and atomic turns.",
  track: "agents",
  minutes: 14,
  tip: [
    "The shop assistant in apps/shop_assistant/agent.py is about 400 lines of plain Python over Ollama's HTTP API: no framework, so every mechanism is visible.",
    "Its parts: JSON tool schemas, a loop bounded by MAX_TOOL_ROUNDS = 3, argument repair for small-model mistakes, the live cart rebuilt into the system prompt every round, a one-time nudge when the model claims an action without a tool call, a hybrid scope guard, and turns that roll back on failure.",
    "Almost every one of those was added because a test caught a real failure.",
    "The biggest lesson from code review: regex guards over the user's words kept breaking on new phrasings. Fixes that changed what the model sees (the cart, a required argument, an enum) held.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Frameworks such as LangGraph hide the loop. That is convenient, but it also hides the decisions you need to test. Building an agent once by hand shows you what any agent must decide:",
    },
    {
      heading: "How it works",
      body: "- how to describe tools so the model calls them correctly; - when to stop the loop; - what to do with bad arguments; - what the model needs to see on each call; - what to do when the model lies about what it did; - what to do when the request is off topic; - what happens to state when a call fails halfway.",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "site/agents/building-agents.md"],
};

const lesson_langchain: Lesson = {
  slug: "langchain",
  title: "LangChain",
  summary: "The LangChain building blocks - chat models, messages, LCEL runnables, tools, structured output, retrievers - and how to test LangChain code without a model.",
  track: "agents",
  minutes: 12,
  tip: [
    "LangChain is a Python library of common parts for LLM apps: chat models behind one interface, messages, composable runnables (LCEL, joined with |), tools, structured output and retrievers.",
    "Everything is a Runnable with .invoke(). That one fact is what makes LangChain code testable: any step, including the model, can be swapped for a fake.",
    "The repository ships a LangChain RAG app, ai/chatbot/langchain_client.py: retrieve | build messages | ChatOllama, behind the same interface as the plain Ollama client, so every existing metric runs against it.",
    "Test it with no model at all: a recording RunnableLambda for chains, and ScriptedChatModel (which can bind_tools) for agents.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Every LLM app needs the same plumbing: talk to a model, format messages, call a search index, parse the output, describe tools. LangChain packages that plumbing behind shared interfaces, so you can swap one model or vector store for another without rewriting the app.",
    },
    {
      heading: "How it works",
      body: "For a tester, the interesting part is the interface, not the features. LangChain's core idea is the Runnable: an object with invoke(input) -> output. A model is a runnable. A prompt is a runnable. A plain Python function wrapped in RunnableLambda is a runnable. You join runnables with the pipe operator, and the result is again a runnable. This is LCEL, the LangChain Expression Language.",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "site/agents/langchain.md"],
};

const lesson_langgraph: Lesson = {
  slug: "langgraph",
  title: "LangGraph",
  summary: "Building an agent as a LangGraph state machine - state, nodes, edges, ToolNode, checkpointer memory and the recursion limit - using the repository's LangGraph shop agent and its tests.",
  track: "agents",
  minutes: 12,
  tip: [
    "LangGraph builds an agent as a graph: a shared state, nodes (functions that update it) and edges (which node runs next). A conditional edge lets the model's reply choose the path.",
    "The repository's LangGraph agent is retrieve -> agent -> (tools -> agent)* -> END: ToolNode runs tools, tools_condition routes, a checkpointer (InMemorySaver) gives each thread_id its memory.",
    "Invalid tool arguments are fed back to the model as an error message, not repaired by hand. In LangGraph 1.2 a schema violation raises ToolInvocationError, not ValueError.",
    "Loops are bounded by recursion_limit: 2n − 1 steps for n model calls, plus one when the graph starts with a retrieve node.",
    "Measured: as a tool, policy search was called in 0 of 6 policy questions by qwen2.5:1.5b. As a graph node, it always runs. Put decisions a small model can't be trusted with into edges.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "The hand-written agent is a for loop with if statements. LangGraph turns that loop into a drawing you can inspect: boxes for steps, arrows for \"what next\". The loop is still there, but it is now data, which means a test can check its shape.",
    },
    {
      heading: "How it works",
      body: "The analogy is a flowchart on the wall of a call centre. Every call starts at the top. Some boxes are always visited (look up the policy). At some boxes the operator decides which arrow to follow (call a tool, or answer). The chart itself never changes; only the path through it does.",
    },
  ],
  relatedRepoPaths: ["apps/shop_assistant/", "site/agents/langgraph.md"],
};

const lesson_voice_agents: Lesson = {
  slug: "voice-agents",
  title: "Voice agents",
  summary: "How voice agents work (speech-to-text, agent, text-to-speech, streaming, turn-taking, barge-in, latency) and how to test them, with an illustrative example that wraps the repository's agent.",
  track: "agents",
  minutes: 10,
  tip: [
    "A voice agent is a pipeline: STT (speech-to-text) turns audio into words, an agent decides and acts, TTS (text-to-speech) turns the reply back into audio.",
    "Real systems stream every stage and must handle turn-taking (when has the user finished?) and barge-in (the user interrupts while the bot is talking).",
    "Latency is a feature: set a budget per stage and end to end, and measure it.",
    "Test each stage: STT with WER (word error rate), TTS with a round trip (synthesize, transcribe, compare), plus latency, interruptions, noise and accents.",
    "Underneath, it is still an agent: the state and trajectory oracles from testing AI agents stay the most important checks.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "A voice agent is the shop assistant with a microphone and a speaker bolted on. The customer says \"add two backpacks to my cart\", and the cart changes. Everything in the middle is the same agent you have already met; the new parts are the ears and the mouth.",
    },
    {
      heading: "How it works",
      body: "The ears and mouth add three problems a text chatbot never has:",
    },
  ],
  relatedRepoPaths: ["site/agents/voice-agents.md"],
};

const lesson_how_mcp_works: Lesson = {
  slug: "how-mcp-works",
  title: "How MCP works",
  summary: "The Model Context Protocol explained for testers - hosts, clients, servers, JSON-RPC messages, tools, resources, prompts, transports and the security risks.",
  track: "mcp",
  minutes: 12,
  tip: [
    "The Model Context Protocol (MCP) is a standard way for an AI application to discover and call outside capabilities: tools, data and prompt templates.",
    "Three roles: a host (the AI app, such as Claude Desktop, Cursor or Claude Code), a client inside the host (one per server), and a server that exposes the capabilities.",
    "Messages are JSON-RPC 2.0. A session starts with an initialize handshake, then the client typically calls tools/list and later tools/call.",
    "Two standard transports: stdio (the host launches the server as a subprocess) and Streamable HTTP (the server runs as a web service and may stream with Server-Sent Events).",
    "A server is code the model can trigger, so treat it like any other API with a contract, and like any other dependency with a security review.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Before MCP, every AI app had its own way of plugging in tools. If you wanted your assistant to read Jira, query a database and drive a browser, each integration had to be written again for each app. MCP is a shared plug shape, a bit like USB for AI tools: write a server once, and any MCP-aware host can use it.",
    },
    {
      heading: "How it works",
      body: "For a tester, the most useful mental model is this: an MCP server is an API whose caller is a language model. The model reads the tool names and descriptions, decides which tool to call, and fills in the arguments. The server runs the code and returns a result that goes back into the model's context. (If \"context\" is new to you, see how LLMs work.)",
    },
  ],
  relatedRepoPaths: ["site/mcp/how-mcp-works.md"],
};

const lesson_testing_mcp_servers: Lesson = {
  slug: "testing-mcp-servers",
  title: "Testing MCP servers",
  summary: "Contract-test an MCP server - tool list and schemas, happy paths, tool errors, look-alike inputs, idempotency and side effects - over in-process and stdio transports.",
  track: "mcp",
  minutes: 12,
  tip: [
    "An MCP server is an API whose caller is a model. Test it like an API: contract first.",
    "Assert the exact tool list, the input schemas (required arguments, defaults) and that every tool has a useful description.",
    "Check results against a source of truth (the catalogue, the corpus), not against hand-typed values.",
    "Bad input must come back as a tool error the model can read, and the server must survive it.",
    "Run the same client code over two transports: in-process for speed, and a real stdio subprocess to prove the server starts the way a host launches it.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "When an agent uses your MCP server, it plans from three things only: the tool names, their descriptions and their JSON Schemas. Then it trusts what comes back. So a server can break an agent in ways a normal unit test would not notice:",
    },
    {
      heading: "How it works",
      body: "- a tool is renamed, and the agent's plan points at nothing; - an argument becomes required, and every call fails; - a result changes shape, and the agent reads the wrong field; - an error is raised as a crash, and the agent gets nothing useful to recover from; - a tool \"helpfully\" guesses, and the agent gets a confident wrong answer.",
    },
  ],
  relatedRepoPaths: ["site/mcp/testing-mcp-servers.md"],
};

const lesson_playwright_mcp: Lesson = {
  slug: "playwright-mcp",
  title: "Playwright MCP",
  summary: "Let an AI client drive a real browser through a Playwright MCP server, then turn what it did into maintainable page-object tests.",
  track: "mcp",
  minutes: 10,
  tip: [
    "A Playwright MCP server gives an AI client browser tools: navigate, click, type, read the page, take screenshots.",
    "You describe a flow in plain English (\"open Sauce Demo, log in as standard_user, add the backpack\") and the model performs it in a real browser.",
    "Two popular servers: Microsoft's @playwright/mcp, which reads the page as an accessibility snapshot, and ExecuteAutomation's @executeautomation/playwright-mcp-server. The repository's mcp.example.json registers both.",
    "It is excellent for exploring and for drafting code. The draft is codegen output: move the locators into page objects and add real assertions before it joins the suite.",
    "Limits: it is slow, non-deterministic, and the model acts with your browser and your sessions. Keep it away from production credentials.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "Record-and-playback tools have existed for years: you click, the tool writes a script. Playwright itself has codegen. A Playwright MCP server changes who does the clicking. Instead of you, a language model drives the browser, one tool call at a time, following an instruction written in plain English.",
    },
    {
      heading: "How it works",
      body: "A useful picture: a new colleague who can use a browser but has never seen your app. You tell them what to do; they look at the screen, act, look again, and tell you what they saw. They are quick to explore, and they can write down the steps. You would still review their notes before turning them into a regression suite.",
    },
  ],
  relatedRepoPaths: ["site/mcp/playwright-mcp.md"],
};

const lesson_ai_in_qa_at_companies: Lesson = {
  slug: "ai-in-qa-at-companies",
  title: "How companies use AI in QA",
  summary: "The two ways engineering teams bring AI into quality work today, using AI to help testing and testing AI features, with roles, governance and common anti-patterns.",
  track: "industry",
  minutes: 12,
  tip: [
    "AI shows up in QA in two directions: AI that helps you test (drafting cases and data, healing locators, triaging failures) and testing AI features (evals, red teaming, monitoring).",
    "In the first direction AI is an assistant. Its output is a draft that a person reviews, because generators hallucinate too.",
    "In the second direction AI is the system under test. You need golden sets, calibrated judges, attacks and budgets, not only pass/fail assertions.",
    "The QA role grows into an \"AI quality engineer\": someone who can say how good is good enough, and prove it.",
    "Most failures come from over-trust: a single green run, an uncalibrated judge, an eval set that never changes, or checking the reply text instead of the real state.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "This page describes general industry practice in plain terms, without statistics or company names, because practices vary a lot and change quickly. Where the page says in this repository, it points to something you can run and check.",
    },
    {
      heading: "How it works",
      body: "Think of two different jobs that both say \"AI\" on the ticket.",
    },
  ],
  relatedRepoPaths: ["site/industry/ai-in-qa-at-companies.md"],
};

const lesson_adoption_playbook: Lesson = {
  slug: "adoption-playbook",
  title: "Adopting AI testing: a playbook",
  summary: "A step-by-step plan for a QA team that must start testing an AI feature, from writing its risks to CI budgets and production feedback, with a maturity table, roles and a checklist.",
  track: "industry",
  minutes: 12,
  tip: [
    "Start with one AI feature and write down how it can hurt users. Everything else follows from that list.",
    "Build a small golden set, then add checks in order of trust: deterministic rules first, classifiers next, calibrated LLM judges last.",
    "Red-team it, with a budget for attacks that succeed and a budget for legitimate requests refused.",
    "In CI, decide per check whether it gates or reports. Small models behave differently across machines, so only well-calibrated, stable checks should block a merge.",
    "Close the loop: production traces become new goldens. Then, and only then, scale to the next feature.",
  ],
  sections: [
    {
      heading: "The idea",
      body: "The steps below are a general plan. Each one points to the part of this repository that practises it, so you can see a working version before you build your own.",
    },
    {
      heading: "How it works",
      body: "Testing an AI feature is like testing a service whose output is a little different every time and sometimes confidently wrong. You cannot write one assertion per expected value. You can still do what testers always do: list the risks, pick an oracle per risk, make results repeatable, and set a bar.",
    },
  ],
  relatedRepoPaths: ["site/industry/adoption-playbook.md"],
};

export const allLessons: readonly Lesson[] = [
  lesson_framework_overview,
  lesson_ui_testing,
  lesson_api_testing,
  lesson_sql_and_hybrid,
  lesson_ci_cd,
  lesson_how_llms_work,
  lesson_prompting,
  lesson_prompt_chaining,
  lesson_ai_search,
  lesson_rag,
  lesson_evaluating_llms,
  lesson_judges_and_calibration,
  lesson_production_metrics,
  lesson_performance_evals,
  lesson_observability,
  lesson_red_teaming,
  lesson_what_is_an_agent,
  lesson_testing_agents,
  lesson_building_agents,
  lesson_langchain,
  lesson_langgraph,
  lesson_voice_agents,
  lesson_how_mcp_works,
  lesson_testing_mcp_servers,
  lesson_playwright_mcp,
  lesson_ai_in_qa_at_companies,
  lesson_adoption_playbook,
];

export const curriculumTracks: readonly CurriculumTrack[] = [
  {
    id: "framework",
    title: "QA framework",
    description: "Page objects, service clients, SQL repositories, and the hermetic CI gate.",
    lessons: [lesson_framework_overview, lesson_ui_testing, lesson_api_testing, lesson_sql_and_hybrid, lesson_ci_cd],
  },
  {
    id: "foundations",
    title: "Foundations",
    description: "How models work, how prompts fail, and how retrieval is tested.",
    lessons: [lesson_how_llms_work, lesson_prompting, lesson_prompt_chaining, lesson_ai_search, lesson_rag],
  },
  {
    id: "evals",
    title: "Evaluating AI",
    description: "What to measure, which judge to trust, and how to attack the system.",
    lessons: [lesson_evaluating_llms, lesson_judges_and_calibration, lesson_production_metrics, lesson_performance_evals, lesson_observability, lesson_red_teaming],
  },
  {
    id: "agents",
    title: "Agents",
    description: "Tool loops, trajectories, and the shop-assistant patterns in this repo.",
    lessons: [lesson_what_is_an_agent, lesson_testing_agents, lesson_building_agents, lesson_langchain, lesson_langgraph, lesson_voice_agents],
  },
  {
    id: "mcp",
    title: "MCP",
    description: "How MCP servers expose tools — and how to contract-test them.",
    lessons: [lesson_how_mcp_works, lesson_testing_mcp_servers, lesson_playwright_mcp],
  },
  {
    id: "industry",
    title: "AI for QA at work",
    description: "Industry patterns and a concrete adoption playbook for QA teams.",
    lessons: [lesson_ai_in_qa_at_companies, lesson_adoption_playbook],
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
