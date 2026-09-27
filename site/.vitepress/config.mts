import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

const REPO = 'https://github.com/iamzakirzr/Playwright-ZR'

// One sidebar group per learning track. Every page listed here must exist under site/.
const sidebar = [
  {
    text: 'Start here',
    items: [
      { text: 'How to use this site', link: '/start/' },
      { text: 'Learning roadmap', link: '/start/roadmap' },
      { text: 'Glossary', link: '/start/glossary' },
    ],
  },
  {
    text: '1 · How LLMs work',
    collapsed: false,
    items: [
      { text: 'LLMs from the inside', link: '/foundations/how-llms-work' },
      { text: 'Prompting and prompt testing', link: '/foundations/prompting' },
      { text: 'Prompt chaining', link: '/foundations/prompt-chaining' },
      { text: 'AI search and its testing', link: '/foundations/ai-search' },
      { text: 'RAG', link: '/foundations/rag' },
    ],
  },
  {
    text: '2 · Evaluating AI',
    collapsed: false,
    items: [
      { text: 'Evaluating LLM output', link: '/evals/evaluating-llms' },
      { text: 'LLM judges and calibration', link: '/evals/judges-and-calibration' },
      { text: 'Performance evals', link: '/evals/performance-evals' },
      { text: 'Production metrics', link: '/evals/production-metrics' },
      { text: 'Observing AI in production', link: '/evals/observability' },
      { text: 'Red teaming and guardrails', link: '/evals/red-teaming' },
    ],
  },
  {
    text: '3 · Agents',
    collapsed: false,
    items: [
      { text: 'What an agent is', link: '/agents/what-is-an-agent' },
      { text: 'Testing AI agents', link: '/agents/testing-agents' },
      { text: 'Building an agent by hand', link: '/agents/building-agents' },
      { text: 'LangChain', link: '/agents/langchain' },
      { text: 'LangGraph', link: '/agents/langgraph' },
      { text: 'Voice agents', link: '/agents/voice-agents' },
    ],
  },
  {
    text: '4 · MCP',
    collapsed: false,
    items: [
      { text: 'How MCP works', link: '/mcp/how-mcp-works' },
      { text: 'Testing an MCP server', link: '/mcp/testing-mcp-servers' },
      { text: 'Playwright MCP', link: '/mcp/playwright-mcp' },
    ],
  },
  {
    text: '5 · The QA framework',
    collapsed: false,
    items: [
      { text: 'Tour of the repository', link: '/framework/overview' },
      { text: 'UI testing with Playwright', link: '/framework/ui-testing' },
      { text: 'API testing', link: '/framework/api-testing' },
      { text: 'SQL and cross-layer tests', link: '/framework/sql-and-hybrid' },
      { text: 'CI/CD', link: '/framework/ci-cd' },
    ],
  },
  {
    text: '6 · AI for QA at work',
    collapsed: false,
    items: [
      { text: 'How companies use AI in QA', link: '/industry/ai-in-qa-at-companies' },
      { text: 'Adopting AI testing: a playbook', link: '/industry/adoption-playbook' },
    ],
  },
]

export default withMermaid(
  defineConfig({
    title: 'AI QA Academy',
    description:
      'Learn how LLMs, RAG, agents, LangChain, LangGraph and MCP work, and how to test them, from a real open-source QA framework.',
    lang: 'en-US',
    cleanUrls: true,
    srcExclude: ['WRITING.md', 'README.md'],
    lastUpdated: false,
    head: [
      ['link', { rel: 'icon', href: '/favicon.svg', type: 'image/svg+xml' }],
      ['meta', { name: 'theme-color', content: '#4f46e5' }],
    ],
    themeConfig: {
      logo: '/favicon.svg',
      nav: [
        { text: 'Start', link: '/start/' },
        { text: 'LLMs', link: '/foundations/how-llms-work' },
        { text: 'Evals', link: '/evals/evaluating-llms' },
        { text: 'Agents', link: '/agents/what-is-an-agent' },
        { text: 'MCP', link: '/mcp/how-mcp-works' },
        { text: 'Framework', link: '/framework/overview' },
        { text: 'At work', link: '/industry/ai-in-qa-at-companies' },
      ],
      sidebar,
      outline: { level: [2, 3], label: 'On this page' },
      search: { provider: 'local' },
      socialLinks: [{ icon: 'github', link: REPO }],
      editLink: { pattern: `${REPO}/edit/main/site/:path`, text: 'Suggest an edit' },
      footer: {
        message: 'Every measured number on this site comes from a test in the repository.',
        copyright: 'Open source, MIT licensed',
      },
    },
    mermaid: { theme: 'neutral' },
  }),
)
