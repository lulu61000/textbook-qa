from src.chunks import load_chunks
from src.retrieve import BM25Retriever
import config

r = BM25Retriever(load_chunks(config.INDEX_DIR / "chunks.jsonl"))
for q in ["how many pull requests were sampled",
          "what is AIdev-pop",
          "how many roles did AI fill"]:
    print(f"\n{q}")
    for c, s in r.search(q, 3):
        print(f"  {s:5.2f}  {c.text[:70]}")