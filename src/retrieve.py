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


# Models name their prompts differently in their own config; map to our two kinds.
_PROMPT_ALIASES = {
    "query": ("query", "queries", "search_query"),
    "document": ("document", "documents", "passage", "passages", "corpus", "search_document"),
}


def _normalize_prompts(raw: dict) -> dict:
    out = {}
    for kind, names in _PROMPT_ALIASES.items():
        for n in names:
            if raw.get(n):
                out[kind] = raw[n]
                break
    return out


def resolve_prompts(model_prompts: dict | None, model_name: str) -> tuple[dict, str]:
    """Pick the query/document prefixes. Returns (prompts, source).

    Order: EMBED_PREFIXES_OFF -> nothing; model's own NON-EMPTY prompts;
    config.EMBED_PREFIXES; else no prefix. "Non-empty" matters: bge-small
    ships {'query': '', 'document': ''}, so a plain `model.prompts or ...`
    would pick the empty strings and silently drop the query prefix.
    """
    import config
    if config.EMBED_PREFIXES_OFF:
        return {}, "off (EMBED_PREFIXES_OFF=1)"
    own = _normalize_prompts(model_prompts or {})
    if own:
        return own, "model config"
    if model_name in config.EMBED_PREFIXES:
        return _normalize_prompts(config.EMBED_PREFIXES[model_name]), "config.EMBED_PREFIXES"
    return {}, "none (unknown model, no prefixes)"


class VectorRetriever:
    def __init__(self, chunks: list[Chunk], model_name: str = None):
        import config
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name or config.EMBED_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.prompts, self.prompt_source = resolve_prompts(self.model.prompts, self.model_name)
        self.chunks = chunks
        self.matrix = self._load_or_encode(chunks, config.INDEX_DIR)

    def _encode(self, texts: list[str], kind: str, progress: bool = False) -> np.ndarray:
        p = self.prompts.get(kind, "")
        return self.model.encode([p + t for t in texts], normalize_embeddings=True,
                                 batch_size=32, show_progress_bar=progress)

    def cache_key(self, chunks: list[Chunk]) -> str:
        """Vectors depend on model, prefixes AND chunk contents. Hashing the
        texts (not just the count) also catches re-chunking that happens to
        keep the same number of chunks."""
        import hashlib, json
        h = hashlib.sha1()
        h.update(self.model_name.encode())
        h.update(json.dumps(self.prompts, sort_keys=True).encode())
        for c in chunks:
            h.update(c.text.encode("utf-8"))
            h.update(b"\0")
        return h.hexdigest()[:10]

    def _load_or_encode(self, chunks: list[Chunk], cache_dir) -> np.ndarray:
        self.cache_path = cache_dir / f"vectors_{self.cache_key(chunks)}.npy"
        if self.cache_path.exists():
            m = np.load(self.cache_path)
            if m.shape[0] == len(chunks):
                return m
        m = self._encode([c.text for c in chunks], "document", progress=True)
        np.save(self.cache_path, m)
        return m

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        q = self._encode([query], "query")[0]
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


RETRIEVERS = ("bm25", "vector", "hybrid")


def get_retriever(name: str, chunks: list[Chunk]) -> Retriever:
    """Build a retriever by name. Mirrors llm.get_llm so evals can swap stages."""
    if name == "bm25":
        return BM25Retriever(chunks)
    if name == "vector":
        return VectorRetriever(chunks)
    if name == "hybrid":
        import config
        return HybridRetriever(BM25Retriever(chunks), VectorRetriever(chunks),
                               config.BM25_WEIGHT)
    raise ValueError(f"unknown retriever {name!r}; choose from {list(RETRIEVERS)}")
