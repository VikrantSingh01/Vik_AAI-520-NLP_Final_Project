"""Filing chunking and retrieval with optional MiniLM embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from faangm_research.schemas import EvidenceItem


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    evidence_id: str
    ticker: str
    text: str


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk: Chunk
    score: float
    rank: int


def chunk_evidence(
    evidence: list[EvidenceItem],
    chunk_size: int = 900,
    overlap: int = 120,
) -> list[Chunk]:
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    chunks: list[Chunk] = []
    step = chunk_size - overlap
    for item in evidence:
        if item.document_type not in {"10-K", "10-Q", "8-K"}:
            continue
        for index, start in enumerate(range(0, len(item.clean_text), step)):
            text = item.clean_text[start : start + chunk_size].strip()
            if text:
                chunks.append(
                    Chunk(
                        chunk_id=f"{item.evidence_id}-CH{index:05d}",
                        evidence_id=item.evidence_id,
                        ticker=item.ticker,
                        text=text,
                    )
                )
            if start + chunk_size >= len(item.clean_text):
                break
    return chunks


class FilingRetriever:
    """Semantic MiniLM retriever with a deterministic TF-IDF fallback."""

    def __init__(self, chunks: list[Chunk], use_minilm: bool = False) -> None:
        if not chunks:
            raise ValueError("At least one filing chunk is required")
        self.chunks = chunks
        self.method = "tfidf"
        self._encoder = None
        self._vectors: np.ndarray | Any
        if use_minilm:
            try:
                from sentence_transformers import SentenceTransformer

                self._encoder = SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2"
                )
                self._vectors = self._encoder.encode(
                    [chunk.text for chunk in chunks],
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                self.method = "minilm"
            except (ImportError, OSError, RuntimeError):
                self._encoder = None
        if self._encoder is None:
            self._vectorizer = TfidfVectorizer(
                stop_words="english", max_features=30_000
            )
            self._vectors = self._vectorizer.fit_transform(
                [chunk.text for chunk in chunks]
            )

    def search(
        self, query: str, k: int = 3, ticker: str | None = None
    ) -> list[SearchResult]:
        indices = [
            index
            for index, chunk in enumerate(self.chunks)
            if ticker is None or chunk.ticker == ticker
        ]
        if not indices:
            return []
        if self._encoder is not None:
            query_vector = self._encoder.encode([query], normalize_embeddings=True)[0]
            scores = np.asarray(self._vectors[indices]) @ query_vector
        else:
            query_vector = self._vectorizer.transform([query])
            scores = cosine_similarity(query_vector, self._vectors[indices]).ravel()
        ranked = sorted(
            zip(indices, scores, strict=True), key=lambda item: item[1], reverse=True
        )
        return [
            SearchResult(chunk=self.chunks[index], score=float(score), rank=rank)
            for rank, (index, score) in enumerate(ranked[:k], start=1)
        ]
