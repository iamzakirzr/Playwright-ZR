"""LLM-as-judge factories.

Both DeepEval and Ragas are pointed at a local open-source model served by
Ollama, so evaluation needs no paid API. Swap the judge by changing
`JUDGE_MODEL` — a larger judge (e.g. llama3.1:8b, qwen2.5:7b) gives more
reliable claim extraction at the cost of CI time.
"""
from __future__ import annotations

from deepeval.models import OllamaModel


def deepeval_judge(model: str, ollama_host: str) -> OllamaModel:
    """Return a DeepEval judge backed by a local Ollama model (temperature 0 for repeatable verdicts)."""
    return OllamaModel(model=model, base_url=ollama_host, temperature=0)


def ragas_judge(model: str, ollama_host: str):
    """Return a Ragas-compatible judge backed by a local Ollama model.

    Ragas needs a judge that reliably emits its structured JSON; in practice that
    means 7B parameters or more. 3B models fail with OUTPUT_PARSING_FAILURE.
    """
    from langchain_ollama import ChatOllama
    from ragas.llms import LangchainLLMWrapper

    return LangchainLLMWrapper(ChatOllama(model=model, base_url=ollama_host, temperature=0))
