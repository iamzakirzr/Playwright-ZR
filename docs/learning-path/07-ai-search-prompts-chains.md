# 07 · AI search, prompts and chains

## Why
Most LLM bugs are not in the model: they are in retrieval that fetched the wrong passage, a prompt
someone edited without review, or a multi-step chain that passed bad output to the next step.
All three can be tested **without** a model.

## AI search: [`ai/search/`](../../ai/search)
- Three retrievers behind one interface: `BM25Retriever` (keywords), `SemanticRetriever`
  (embeddings), `HybridRetriever` (Reciprocal Rank Fusion of both).
- IR metrics in `metrics.py`: precision/recall/hit-rate@k, MRR, nDCG.
- Tests: [`tests/ai/search/`](../../tests/ai/search). Quality gates against labelled queries,
  robustness (typos, paraphrases, off-topic queries that must return nothing).

## Prompts as code: [`ai/prompts/`](../../ai/prompts)
- Templates live in `library.json` with a name and version; `PromptRegistry.get("grounded_qa")`
  returns the latest, `version=1` pins an old one for A/B or rollback.
- [`tests/ai/prompts/test_prompt_registry.py`](../../tests/ai/prompts/test_prompt_registry.py):
  missing or misspelt variables fail, user input can't inject template syntax, security rules are
  linted, and a **snapshot** of every prompt's fingerprint catches unreviewed edits
  (`UPDATE_PROMPT_SNAPSHOTS=1` accepts an intended change).

## Prompt chaining: [`ai/chains/`](../../ai/chains)
- A chain is a list of `ChainStep`s sharing a `ChainState`; each step's trace is recorded.
- [`tests/ai/chains/test_chain_unit.py`](../../tests/ai/chains/test_chain_unit.py) drives the
  chain with a `ScriptedChatbot` (a fake that returns fixed replies) to test routing, error
  wrapping (`ChainError` names the failing step) and early exits, in milliseconds.

## Run
```bash
make test-ai-offline
```

## Try it
Change one word in `grounded_qa` in `library.json` and run the prompt tests. Read the failure,
then accept it with `UPDATE_PROMPT_SNAPSHOTS=1`.

## Test your knowledge
1. Why can hybrid search beat both of its parts?
2. What does a prompt snapshot test protect against that code review alone doesn't?
3. Why test a chain with a scripted model before a real one?

<details><summary>Answers</summary>

1. BM25 wins on exact terms (SKUs, names), embeddings on paraphrases; RRF keeps what either ranks high.
2. Silent edits: a prompt change made in a JSON file or a merge with no reviewer who knew to look.
3. It isolates the chain's logic (routing, state, error handling) from model randomness, so a
   failure points at one cause.
</details>
