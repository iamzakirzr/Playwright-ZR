"""Concrete retrieval strategies: BM25 (keyword), embeddings (semantic) and hybrid."""

from __future__ import annotations

import math
import re
from collections import Counter

from ai.search.base import Document, Retriever

_TOKEN = re.compile(r"[a-z0-9$]+")
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "is",
        "are",
        "do",
        "does",
        "i",
        "my",
        "me",
        "you",
        "your",
        "we",
        "our",
        "of",
        "to",
        "for",
        "on",
        "in",
        "at",
        "and",
        "or",
        "can",
        "what",
        "how",
        "when",
        "will",
        "with",
        "it",
        "be",
    ]
)


def tokenize(text: str) -> list[str]:
    """Lower-case, split on non-alphanumerics and drop stop words."""
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS]


class BM25Retriever(Retriever):
    """Okapi BM25 keyword search: the classic lexical baseline that search teams benchmark against.

    Args:
        documents: Collection to index.
        k1: Term-frequency saturation.
        b: Document-length normalisation strength.
    """

    name = "bm25"

    def __init__(self, documents: list[Document], k1: float = 1.5, b: float = 0.75) -> None:
        """Create the BM25Retriever; arguments are described in the class docstring."""
        self.k1, self.b = k1, b
        super().__init__(documents)

    def _index(self) -> None:
        """Build term frequencies, document frequencies and length stats."""
        self._tfs = [Counter(tokenize(f"{d.title} {d.text}")) for d in self.documents]
        self._lengths = [sum(tf.values()) for tf in self._tfs]
        self._avg_len = sum(self._lengths) / len(self._lengths)
        df = Counter(term for tf in self._tfs for term in tf)
        n = len(self.documents)
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def _score(self, query: str) -> list[float]:
        """Sum the BM25 contribution of each query term for every document."""
        terms = tokenize(query)
        scores = []
        for tf, length in zip(self._tfs, self._lengths, strict=True):
            score = 0.0
            for term in terms:
                if term not in tf:
                    continue
                freq = tf[term]
                norm = freq + self.k1 * (1 - self.b + self.b * length / self._avg_len)
                score += self._idf[term] * freq * (self.k1 + 1) / norm
            scores.append(score)
        return scores


class SemanticRetriever(Retriever):
    """Dense retrieval: cosine similarity between sentence embeddings.

    Args:
        documents: Collection to index.
        model_name: Any sentence-transformers model id.
    """

    name = "semantic"

    def __init__(self, documents: list[Document], model_name: str) -> None:
        """Create the SemanticRetriever; arguments are described in the class docstring."""
        self.model_name = model_name
        super().__init__(documents)

    def _index(self) -> None:
        """Encode every document once; embeddings are L2-normalised."""
        from ai.evaluators.semantic_similarity import load_encoder

        self._encoder = load_encoder(self.model_name)
        self._matrix = self._encoder.encode(
            [f"{d.title}. {d.text}" for d in self.documents], normalize_embeddings=True, convert_to_tensor=True
        )

    def _score(self, query: str) -> list[float]:
        """Dot product of normalised vectors, which equals cosine similarity."""
        q = self._encoder.encode(query, normalize_embeddings=True, convert_to_tensor=True)
        return (self._matrix @ q).tolist()


class HybridRetriever(Retriever):
    """Reciprocal Rank Fusion of several retrievers (**Composite** pattern).

    RRF merges rankings rather than raw scores, so BM25 and cosine scores don't
    need calibrating against each other. This is the common production default.

    Args:
        retrievers: Child retrievers over the same documents.
        rrf_k: RRF damping constant (60 is the value from the original paper).
    """

    name = "hybrid"

    def __init__(self, retrievers: list[Retriever], rrf_k: int = 60) -> None:
        """Create the HybridRetriever; arguments are described in the class docstring."""
        self.retrievers = retrievers
        self.rrf_k = rrf_k
        super().__init__(retrievers[0].documents)

    def _index(self) -> None:
        """Children are already indexed; just check they share one collection."""
        ids = [d.id for d in self.documents]
        for r in self.retrievers:
            if [d.id for d in r.documents] != ids:
                raise ValueError("HybridRetriever children must index the same documents")

    def _score(self, query: str) -> list[float]:
        """RRF score: sum over children of 1 / (rrf_k + rank)."""
        fused = [0.0] * len(self.documents)
        for retriever in self.retrievers:
            scores = retriever._score(query)
            order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            for rank, i in enumerate(order, start=1):
                fused[i] += 1.0 / (self.rrf_k + rank)
        return fused
