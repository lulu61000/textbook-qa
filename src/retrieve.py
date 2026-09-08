"""Retrieval. Swappable by design so you can measure each stage's contribution.

Build order matters: get BM25 working and evaluated first, then add vectors
and measure the delta. A hybrid you never compared against a baseline is a
hybrid you cannot justify.
"""
from typing import Protocol
import numpy as np
from rank_bm25 import BM25Okapi
from .chunks import Chunk


class Retriever(Protocol):
    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]: ...


def tokenize(text: str) -> list[str]:
    """TODO: lowercase, strip punctuation, split. Do NOT stem aggressively --
    technical terms are precisely what you must not mangle."""
    return text.lower().split()


class BM25Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c.text) for c in chunks])

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        scores = self.bm25.get_scores(tokenize(query))
        top = np.argsort(scores)[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top]


class VectorRetriever:
    """Add this in phase 2, once BM25 has a measured baseline."""

    def __init__(self, chunks: list[Chunk], model_name="BAAI/bge-small-en-v1.5"):
        from sentence_transformers import SentenceTransformer
        self.chunks = chunks
        self.model = SentenceTransformer(model_name)
        self.matrix = self.model.encode(
            [c.text for c in chunks], normalize_embeddings=True, show_progress_bar=True
        )

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.matrix @ q          # cosine, since both are normalized
        top = np.argsort(scores)[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top]


class HybridRetriever:
    def __init__(self, bm25: BM25Retriever, vector: VectorRetriever, bm25_weight: float):
        self.bm25, self.vector, self.w = bm25, vector, bm25_weight

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        """TODO: fuse the two rankings.

        BM25 scores are unbounded, cosine is [-1,1] -- you cannot add them
        directly. Either normalize each to [0,1] first, or use Reciprocal
        Rank Fusion (score = sum of 1/(60+rank)), which sidesteps scale
        entirely and is usually the more robust choice.

        Pull k*3 from each retriever before fusing, or you will fuse two
        already-truncated lists and lose recall.
        """
        raise NotImplementedError
