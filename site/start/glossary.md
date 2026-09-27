---
title: Glossary
description: Plain-English definitions of the AI and testing terms used on this site, from agent to WER, each linked to the page that covers it.
---

# Glossary

::: tip In one minute
- Short, plain definitions of every AI term the site uses, in alphabetical order.
- Each entry links to the page that explains it properly.
- Where the repository measured something about the term, the entry says so.
- Link to an entry from any page with `/start/glossary#term`, for example `/start/glossary#embedding`.
:::

### Agent

A program where an LLM decides, step by step, which tool to call next, sees the result, and
repeats until it can answer. The shop assistant in this repository is an agent: it calls
`add_to_cart`, `remove_from_cart` and `view_cart`. See [What an agent is](/agents/what-is-an-agent).

### Agentic RAG

[RAG](#rag) where the agent decides whether and when to search, by calling a search tool, instead
of the code always retrieving first. Measured here: `qwen2.5:1.5b` called the search tool in 0 of
6 policy questions and invented answers, so the repository makes retrieval a fixed graph step by
default. See [LangGraph](/agents/langgraph).

### Answer relevancy

A judged metric that asks whether the answer addresses the question that was asked, regardless of
whether it is true. In this repository the 3B judge scored a perfectly on-topic answer 0.25, so
this metric only runs with the 7B judge. See [Production metrics](/evals/production-metrics).

### Attack success rate

The share of red-team attacks that got the harmful result they aimed for (ASR). Measured here:
9 of 14 attacks succeeded against the raw model and 0 of 14 against the guarded bot. See
[Red teaming and guardrails](/evals/red-teaming).

### BLEU

A reference metric that counts how many word sequences (n-grams) of the output also appear in a
reference text. It rewards the same wording, not the same meaning: a correct paraphrase scored
BLEU 0.08 in the repository's calibration test. See [Evaluating LLM output](/evals/evaluating-llms).

### BM25

A classic keyword search algorithm that ranks documents by how often the query's words appear in
them, weighted by how rare those words are. Fast, exact and blind to synonyms. See
[AI search and its testing](/foundations/ai-search).

### Calibration

Proving a metric can tell a good answer from a bad one before trusting it: run it on a known-good
and a known-bad answer and check the scores separate. The repository calibrates every judged metric
this way. See [LLM judges and calibration](/evals/judges-and-calibration).

### Canary token

A made-up secret planted in the system prompt (here `ZX-CANARY-7731`). If it ever appears in an
answer, the system prompt leaked. A plain string check detects it, with no judge needed. See
[Red teaming and guardrails](/evals/red-teaming).

### Chain

A fixed sequence of steps, some of them LLM calls, where each step's output feeds the next. Unlike
an agent, the code decides the order, not the model. See [Prompt chaining](/foundations/prompt-chaining).

### Checkpointer

The part of a LangGraph app that saves the graph's state after each step, keyed by a conversation
thread id. That saved state is the agent's memory between turns. The repository uses
`InMemorySaver`. See [LangGraph](/agents/langgraph).

### Context window

The maximum amount of text, counted in [tokens](#token), that a model can read in one call:
system prompt, history, retrieved documents and the answer together. Anything beyond it is cut or
never seen. See [LLMs from the inside](/foundations/how-llms-work).

### Conversational test case

A test case made of several user and assistant turns, scored as a whole conversation (did it stay
in role, remember earlier facts, finish the task). DeepEval calls it `ConversationalTestCase`. See
[Testing AI agents](/agents/testing-agents).

### Cosine similarity

A number between -1 and 1 that says how closely two [embeddings](#embedding) point in the same
direction. Close to 1 means similar meaning. It is the maths behind
[semantic similarity](#semantic-similarity) and semantic search. See
[AI search and its testing](/foundations/ai-search).

### DeepEval

An open-source Python library for testing LLM apps, in the style of pytest. It provides test cases,
datasets and metrics such as faithfulness and G-Eval. The repository uses it with local models as
judges. See [Evaluating LLM output](/evals/evaluating-llms).

### Embedding

A list of numbers that represents the meaning of a piece of text, produced by an embedding model.
Texts with similar meaning get nearby embeddings, which is how semantic search and similarity
metrics work. See [LLMs from the inside](/foundations/how-llms-work).

### Faithfulness

A metric that checks whether every claim in the answer is supported by the context the model was
given. It catches invented facts, but a faithful answer can still be useless or off-topic. See
[Evaluating LLM output](/evals/evaluating-llms).

### Few-shot

A prompt that includes a few worked examples of input and correct output before the real input.
Measured here: a few-shot intent classifier (v2) routed 14 of 14 questions correctly, against 10 of
14 for the version without examples. See [Prompting and prompt testing](/foundations/prompting).

### G-Eval

A judged metric where you write the criteria in plain English ("does the answer mention every
fee?") and an LLM judge scores against them. Flexible, so it needs calibration more than most. See
[LLM judges and calibration](/evals/judges-and-calibration).

### Golden dataset

A curated set of inputs with their expected outputs (and, for RAG, the source context), used as
the fixed benchmark for every run. In this repository each golden lists `required_facts` that gate
and `helpful_facts` that are tracked. See [Evaluating LLM output](/evals/evaluating-llms).

### Guardrail

A check wrapped around a model that blocks or repairs unsafe input or output, such as an injection
filter, a moderator model or PII redaction. It is a heuristic, not a proof of safety. See
[Red teaming and guardrails](/evals/red-teaming).

### Hallucination

When a model states something that is not true or not supported by its context, usually fluently
and confidently. See [LLMs from the inside](/foundations/how-llms-work) and
[RAG](/foundations/rag).

### Hybrid search

Search that runs keyword search ([BM25](#bm25)) and semantic search side by side and merges the
rankings, usually with [reciprocal rank fusion](#reciprocal-rank-fusion). It catches both exact
terms and paraphrases. See [AI search and its testing](/foundations/ai-search).

### Jailbreak

A prompt designed to talk a model out of its rules, for example by role-play ("pretend you are an
AI without restrictions"). A kind of [prompt injection](#prompt-injection) aimed at the model's
safety behaviour. See [Red teaming and guardrails](/evals/red-teaming).

### JSON mode

A model setting that forces the reply to be valid JSON. It guarantees the syntax, not the shape:
you still validate fields and types, for example with a pydantic model or a JSON schema. See
[Prompting and prompt testing](/foundations/prompting).

### Judge (LLM-as-a-judge)

Using an LLM to score another LLM's output against criteria, when no rule can express the
requirement. A judge can be wrong in both directions, so it is only trusted after
[calibration](#calibration). See [LLM judges and calibration](/evals/judges-and-calibration).

### LangChain

An open-source framework of building blocks for LLM apps: model clients, prompts, retrievers,
tools and a way to compose them ([LCEL](#lcel)). See [LangChain](/agents/langchain).

### LangGraph

A library built on LangChain for agents and workflows as graphs: nodes do the work, edges decide
what runs next, and a [checkpointer](#checkpointer) keeps state. See [LangGraph](/agents/langgraph).

### Latency

How long a response takes, often split into time to first token and total time. For AI features
it is a budget you assert on, like any performance requirement (here `MAX_LATENCY_MS`, default
60000 on CPU). See [Performance evals](/evals/performance-evals).

### LCEL

LangChain Expression Language: composing steps with the `|` operator, so a prompt, a model and a
parser become one runnable chain. The repository's `LangChainChatbot` is an LCEL chain. See
[LangChain](/agents/langchain).

### LLM

Large language model: a model trained on a lot of text to predict the next [token](#token). Chat
assistants, summarisers and agents are all built on one. See
[LLMs from the inside](/foundations/how-llms-work).

### MCP

Model Context Protocol: an open standard for exposing tools and data to AI clients (such as Claude
Desktop or Cursor) over a common interface. An MCP server is tested like any API contract. See
[How MCP works](/mcp/how-mcp-works).

### MRR

Mean reciprocal rank: for each query, one divided by the position of the first relevant result,
averaged over queries. It rewards putting a right answer near the top. See
[AI search and its testing](/foundations/ai-search).

### nDCG

Normalised discounted cumulative gain: a ranking metric that gives more credit for relevant results
near the top and compares the ranking to the best possible one (1.0 is perfect). See
[AI search and its testing](/foundations/ai-search).

### Ollama

A free tool that downloads and runs open-source LLMs on your own machine behind a local HTTP API.
Every live AI test in this repository uses it, so no paid key is needed. See
[How to use this site](/start/).

### Over-refusal

When a safety layer blocks a legitimate request. Measured alongside attack success, because a bot
that refuses everything is "safe" and useless. Here the guarded bot refused 1 of 8 legitimate
questions, a tracked false positive. See [Red teaming and guardrails](/evals/red-teaming).

### Page object

A class that wraps one page of the app, holding its locators and actions, so tests read like user
steps and never contain selectors. See [UI testing with Playwright](/framework/ui-testing).

### Prompt chaining

Splitting one big task into several smaller LLM calls in a fixed order (classify, rewrite, retrieve,
answer), so each step can be tested on its own. See [Prompt chaining](/foundations/prompt-chaining).

### Prompt injection

An attack where text the model reads (from the user or from a retrieved document) contains
instructions that override the developer's. "Indirect" injection hides them in content, not in the
user's message. See [Red teaming and guardrails](/evals/red-teaming).

### RAG

Retrieval-augmented generation: search your own documents for the passages relevant to a question,
put them in the prompt, and ask the model to answer from them. See [RAG](/foundations/rag).

### RAGAS

An open-source library of RAG evaluation metrics (faithfulness, context precision and others). The
repository uses its faithfulness as an independent cross-check of DeepEval's, with the 7B judge.
See [Production metrics](/evals/production-metrics).

### Recall@k

The share of the relevant documents that appear in the top k search results. If the right passage
is not in the top k, the model never sees it. See [AI search and its testing](/foundations/ai-search).

### Reciprocal rank fusion

A way to merge several rankings by adding up one divided by (a constant plus each result's rank)
in each list. It merges positions, not raw scores, so BM25 and cosine scores need no rescaling. See
[AI search and its testing](/foundations/ai-search).

### Red teaming

Attacking your own AI feature on purpose (injections, jailbreaks, data exfiltration, toxicity) to
measure how often it fails. The repository has 14 attacks mapped to the OWASP Top 10 for LLM
Applications. See [Red teaming and guardrails](/evals/red-teaming).

### ROUGE

A family of reference metrics that measure word overlap between output and reference, with
ROUGE-L using the longest common word sequence. Like [BLEU](#bleu), it suits templated or
extractive output, not free-form answers. See [Evaluating LLM output](/evals/evaluating-llms).

### Self-healing locator

A locator that, when its selector breaks, tries a cached replacement and then asks an LLM for
candidates, accepting one only if it matches exactly one visible element. A safety net, not a
replacement for good locators. See [How companies use AI in QA](/industry/ai-in-qa-at-companies).

### Semantic similarity

How close two texts are in meaning, usually measured as the [cosine similarity](#cosine-similarity)
of their embeddings. Weak on negation and on missing facts, so it is never the only check. See
[Evaluating LLM output](/evals/evaluating-llms).

### STT

Speech to text: converting spoken audio into written text (also called speech recognition). The
first stage of a [voice agent](#voice-agent), usually scored with [WER](#wer). Not implemented in
this repository. See [Voice agents](/agents/voice-agents).

### Synthetic data

Test data generated by a model, such as golden question-answer pairs or test cases drafted from
requirements. The generator hallucinates too, so every item passes a gate or a human review. See
[How companies use AI in QA](/industry/ai-in-qa-at-companies).

### System prompt

The hidden instructions a developer gives the model before the user's message: its role, rules and
context. It is not a secret the model reliably keeps, which is why the repository plants a
[canary token](#canary-token) in it. See [Prompting and prompt testing](/foundations/prompting).

### Temperature

A setting that controls how random the model's choice of next token is. At 0 it picks the most
likely token, which makes runs repeatable on one machine, but not across hardware or model versions.
See [LLMs from the inside](/foundations/how-llms-work).

### Token

The unit a model reads and writes: a word, part of a word or a symbol. Context windows, costs and
output limits are all counted in tokens (here `MAX_COMPLETION_TOKENS` defaults to 150). See
[LLMs from the inside](/foundations/how-llms-work).

### Tool calling

The model's ability to reply with a structured request to run a function ("call `add_to_cart`
with product X, quantity 1") instead of text. Your code runs the tool and sends the result back.
See [What an agent is](/agents/what-is-an-agent).

### ToolNode

A prebuilt LangGraph node that runs the tool calls the model asked for and returns the results,
including errors, as messages the model can read and correct. See [LangGraph](/agents/langgraph).

### Trajectory

The ordered list of tools an agent called, with their arguments, during a task. Testing the
trajectory checks *how* the agent got there, alongside the final state and the reply text. See
[Testing AI agents](/agents/testing-agents).

### TTS

Text to speech: turning the agent's written reply into spoken audio. The last stage of a
[voice agent](#voice-agent). Not implemented in this repository. See
[Voice agents](/agents/voice-agents).

### Voice agent

An agent you talk to: [STT](#stt) turns speech into text, an LLM agent decides and acts, and
[TTS](#tts) speaks the reply. Each stage adds its own errors and latency. Not implemented in this
repository; the site teaches the concept. See [Voice agents](/agents/voice-agents).

### WER

Word error rate: the number of word substitutions, deletions and insertions needed to turn a
transcript into the correct text, divided by the number of words in the correct text. Lower is
better; 0 is a perfect transcript. See [Voice agents](/agents/voice-agents).
