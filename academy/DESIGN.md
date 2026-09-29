# AI QA Academy — On-site Tools Learning Courses

## Purpose

An independent learning app for QA engineers. Categories and tools come from a
senior QA skill profile (automation, frameworks, API/performance, data, cloud/CI,
Salesforce, AI evals, collaboration).

**Learning happens on this site.** Every tool is a mini-course with clickable
guides (overview, concept lessons, practice checklist). Official vendor
documentation is linked only as a secondary reference.

Flow: **Dashboard → Category → Tool course → On-site guide**.

## Categories (milestones)

| ID | Category | Source skills |
| --- | --- | --- |
| `test-automation` | Test Automation Tools | AccelQ, Playwright, Selenium, Cypress, Cucumber, Appium, Squish |
| `frameworks` | Automation Frameworks | TestNG, PyTest, NUnit, Mocha, Robot Framework, Nightwatch, WebdriverIO, iSAFE, BDD |
| `api-performance` | API & Performance | REST API testing, JMeter, K6, Artillery |
| `databases` | Databases & Data | SQL, PostgreSQL, Snowflake |
| `cloud-cicd` | Cloud & CI/CD | AWS, Azure, Azure DevOps, Jenkins, Docker, Git, Bitbucket |
| `salesforce` | Salesforce | Service Cloud, Experience Cloud, Flows |
| `ai-evals` | AI & LLM Evaluation | DeepEval, RAGAS, LangSmith, RAG, Agentic AI, Copilot |
| `collaboration` | Collaboration & QA Ops | JIRA, STLC / defect management practices |

## Course shape (every tool)

1. **Getting started** — orientation guide (`/tools/{cat}/{tool}/overview`)
2. **Concept guides** — one on-site lesson per curated API/concept (clickable cards)
3. **Patterns that scale** — maintainable suite design (`.../patterns`)
4. **Shipping with the team** — CI / PR / release evidence (`.../delivery`)
5. **Practice checklist** — capstone drills (`.../practice`)
6. **Related curriculum** — cross-links into `/learn` where topics overlap
7. **Official reference** — vendor docs link inside each guide (secondary)

## Done when

- Every CV tool family above is represented  
- Every tool has a full on-site course (guides open on this site)  
- Learning cards are clickable routes, not docs-only teaser text  
- Official docs remain available as reference, not the primary CTA  
- `npm run build` passes locally  
- UI walkthrough confirms mobile/desktop course → guide flow  
