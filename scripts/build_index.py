"""One-off: PDF -> chunks.jsonl. Run once per textbook.

    python -m scripts.build_index data/book.pdf
"""
import sys
from pathlib import Path
import config
from src.ingest import build
from src.chunks import save_chunks


def main(pdf_path: str):
    config.INDEX_DIR.mkdir(exist_ok=True)
    chunks = build(pdf_path, config.CHUNK_TARGET_TOKENS)
    out = config.INDEX_DIR / "chunks.jsonl"
    save_chunks(chunks, out)
    print(f"{len(chunks)} chunks -> {out}")
    # Sanity-check by hand before trusting anything downstream.
    for c in chunks[:3]:
        print(f"\n--- {c.cite()} ---\n{c.text[:300]}")


if __name__ == "__main__":
    main(sys.argv[1])
