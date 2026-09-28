# AI QA Academy — CV Tools Learning Dashboard

## Purpose

An independent learning app for QA engineers. Categories and tools come from a
senior QA skill profile (automation, frameworks, API/performance, data, cloud/CI,
Salesforce, AI evals, collaboration). Every tool links to **that product’s official
documentation** — not an internal code repository.

Flow: **Dashboard → Category → Tool → curated learning APIs/concepts**.

## Categories (milestones)

| ID | Category | Source skills |
| --- | --- | --- |
| `test-automation` | Test Automation Tools | AccelQ, Playwright, Selenium, Cypress, Cucumber, Appium, Squish |
| `frameworks` | Automation Frameworks | TestNG, PyTest, NUnit, Mocha, Robot Framework, Nightwatch, WebdriverIO, BDD |
| `api-performance` | API & Performance | REST API testing, JMeter, K6, Artillery |
| `databases` | Databases & Data | SQL, PostgreSQL, Snowflake |
| `cloud-cicd` | Cloud & CI/CD | AWS, Azure, Azure DevOps, Jenkins, Docker, Git, Bitbucket |
| `salesforce` | Salesforce | Service Cloud, Experience Cloud, Flows |
| `ai-evals` | AI & LLM Evaluation | DeepEval, RAGAS, LangSmith, RAG, Agentic AI, Copilot |
| `collaboration` | Collaboration & QA Ops | JIRA, STLC / defect management practices |

## Phases

1. Catalog typed from CV + official docs URLs  
2. Dashboard lists all categories  
3. Category pages list tools  
4. Tool pages list ≥3 learning concepts/APIs each, with docs links  
5. UI has no repository path / internal code references  
6. Local build + UI walkthrough (no CI required for acceptance)

## Done when

- Every CV tool family above is represented  
- Every tool has ≥3 docs-backed learning items  
- Navigation works dashboard → category → tool  
- `npm run build` passes locally  
- UI eval confirms mobile/desktop lists and external docs links  
- PR merged to `main`
