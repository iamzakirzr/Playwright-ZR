"""Search abstractions shared by every retriever.

``Retriever`` is an abstract **Strategy**: keyword, semantic and hybrid search
are interchangeable, so the same retrieval-quality tests run against each one.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

CORPUS_FILE = Path(__file__).with_name("corpus.json")


@dataclass(frozen=True)
class Document:
    """One searchable passage."""

    id: str
    title: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    """A ranked hit. ``score`` is only comparable within a single retriever."""

    document: Document
    score: float
    rank: int


def load_corpus(path: Path = CORPUS_FILE) -> dict:
    """Load the raw corpus JSON (documents, labelled queries and probes)."""
    return json.loads(path.read_text())


def load_documents(path: Path = CORPUS_FILE) -> list[Document]:
    """Load only the documents from the corpus as :class:`Document` objects."""
    return [Document(**d) for d in load_corpus(path)["documents"]]


class Retriever(ABC):
    """Abstract retriever over a fixed document collection.

    Args:
        documents: The collection to index. Indexing happens once, in ``__init__``.
    """

    name: str = "retriever"

    def __init__(self, documents: list[Document]) -> None:
        """Create the Retriever; arguments are described in the class docstring."""
        self.documents = documents
        self._index()

    @abstractmethod
    def _index(self) -> None:
        """Build whatever index the strategy needs (inverted index, embeddings...)."""

    @abstractmethod
    def _score(self, query: str) -> list[float]:
        """Return one relevance score per document, aligned with ``self.documents``."""

    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[SearchResult]:
        """Return the top ``k`` documents for ``query``, best first (Template Method).

        Args:
            query: Free-text query.
            k: Maximum number of results.
            min_score: Drop hits scoring below this, so off-topic queries return nothing.
        """
        scores = self._score(query)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in order[:k]:
            if min_score is not None and scores[i] < min_score:
                break
            results.append(SearchResult(self.documents[i], scores[i], rank=len(results) + 1))
        return results

    def search_ids(self, query: str, k: int = 3) -> list[str]:
        """Convenience wrapper returning only the ranked document ids."""
        return [r.document.id for r in self.search(query, k)]
