# 06 · AI evaluation fundamentals

## Why
An LLM's answer is never byte-for-byte the same, so `assert answer == expected` is useless.
Instead you ask measurable questions: *does it mean the same?* (similarity), *is every claim
supported by the context?* (faithfulness), *is anything important missing?* (completeness).

## Read
1. [`ai/chatbot/base.py`](../../ai/chatbot/base.py): the `ChatbotClient` interface. The Ollama
   client, a scripted fake, the guarded decorator and the browser widget all implement it, so every
   test works against any of them.
2. [`ai/evaluators/`](../../ai/evaluators): `semantic_similarity.py` (embeddings, no LLM),
   `deterministic.py` (rule-based metrics), `factory.py` (DeepEval LLM-judge metrics, one place
   to set the judge and thresholds), `classifiers.py` (toxic-bert, a non-LLM safety classifier).
3. [`ai/datasets/golden_qa.json`](../../ai/datasets/golden_qa.json): question, context,
   reference answer, **required** facts and **helpful** facts per case.
4. Tests in [`tests/ai/rag/`](../../tests/ai/rag), starting with `test_semantic_similarity.py`.

## The three tiers (cheapest first)
| Tier | Example | Cost | Marker |
|---|---|---|---|
| Deterministic | required facts present, JSON valid, no canary leak | ms | none |
| Embedding | cosine similarity vs the reference | ~50 ms | none |
| LLM judge | faithfulness, G-Eval completeness | seconds–minutes on CPU | `judge` |

Always put the cheap checks first; a judge should never be the only thing that can fail.

## Calibration: test the test
Before trusting a threshold, prove the metric separates good from bad on *this* model.
`TestMetricCalibration` scores a paraphrase (must pass) and an unrelated sentence (must fail).
[`tests/ai/validation/test_metric_calibration.py`](../../tests/ai/validation/test_metric_calibration.py)
does the same for the judge metrics; the thresholds in `settings.py` carry comments with the
measured scores that justified them.

## Run
```bash
ollama serve & make models
make test-ai-live      # the bot's real behaviour
make test-ai-judged    # judged metrics (slow on CPU)
```

## Try it
Add a case to `golden_qa.json` about a policy in the context text, run
`pytest tests/ai/rag -k <your_id>`, and read the judge's `reason` in the output.

## Test your knowledge
1. Why is the judge model (`llama3.2:3b`) from a different family than the bot (`qwen2.5:1.5b`)?
2. A faithfulness score is 0.9 but the answer is useless. How?
3. Why is the dataset-level threshold (`min_mean_completeness`) lower than the per-case one?

<details><summary>Answers</summary>

1. Models tend to rate their own family's outputs higher (self-preference bias).
2. Faithfulness only checks that claims are supported, so "Please see our policy." is perfectly
   faithful. That is why completeness and required-facts checks exist.
3. It is a regression budget over many cases: a few weak answers are tolerated, a drop in the
   average is not.
</details>
