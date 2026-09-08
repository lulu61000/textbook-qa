"""Run the golden set and report per-category metrics.

Report retrieval and generation separately. An aggregate score tells you the
system got worse; it does not tell you which half to fix.

    python -m evals.run_eval
    LLM_BACKEND=claude python -m evals.run_eval     # same set, other model
"""
import json, time, argparse
from pathlib import Path
from collections import defaultdict
import config
from src.chunks import load_chunks
from src.retrieve import BM25Retriever
from src.llm import get_llm
from src.pipeline import answer

GOLDEN = Path(__file__).parent / "golden.jsonl"


def load_golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def retrieval_hit(ans, expect_pages) -> bool | None:
    """Did retrieval surface at least one expected page? None if N/A."""
    if not expect_pages:
        return None
    got = {c.page for c in ans.chunks}
    return bool(got & set(expect_pages))


def keyword_recall(ans, keywords) -> float | None:
    """Crude proxy for answer completeness. Replace with an LLM judge once
    the pipeline is stable -- but keep this too: it is free, deterministic,
    and catches regressions a judge might wave through."""
    if not keywords:
        return None
    text = ans.text.lower()
    return sum(k.lower() in text for k in keywords) / len(keywords)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--k", type=int, default=config.TOP_K)
    p.add_argument("--retrieval-only", action="store_true")
    args = p.parse_args()
    

    chunks = load_chunks(config.INDEX_DIR / "chunks.jsonl")
    retriever = BM25Retriever(chunks)
    llm = get_llm()
    rows, by_type = [], defaultdict(list)

    
    print(args.retrieval_only)#to test if bm25 hit right key words in pdf chunk run with: python -m evals.run_eval --retrieval-only
    if args.retrieval_only:
        for case in load_golden():
            hits = retriever.search(case["question"], args.k)
            text = " ".join(c.text for c, _ in hits)
            kws = case["expect_keywords"]
            hit = None if not kws else all(k.lower() in text.lower() for k in kws)
            print(hit)
        return
    

    for case in load_golden():
        t0 = time.perf_counter()
        ans = answer(case["question"], retriever, llm, args.k)
        elapsed = time.perf_counter() - t0
        row = {
            "id": case["id"],
            "type": case["type"],
            "retrieval_hit": retrieval_hit(ans, case["expect_pages"]),
            "keyword_recall": keyword_recall(ans, case["expect_keywords"]),
            "latency_s": round(elapsed, 2),
            "answer": ans.text,
            "cited": ans.citations,
        }
        rows.append(row)
        by_type[case["type"]].append(row)

    print(f"\nbackend={llm.name}  k={args.k}  n={len(rows)}\n")
    print(f"{'type':<14}{'n':>4}{'retr_hit':>10}{'kw_recall':>11}{'latency':>9}")
    for t, rs in by_type.items():
        hits = [r['retrieval_hit'] for r in rs if r['retrieval_hit'] is not None]
        kws = [r['keyword_recall'] for r in rs if r['keyword_recall'] is not None]
        h = f"{sum(hits)/len(hits):.2f}" if hits else "-"
        k = f"{sum(kws)/len(kws):.2f}" if kws else "-"
        lat = sum(r['latency_s'] for r in rs) / len(rs)
        print(f"{t:<14}{len(rs):>4}{h:>10}{k:>11}{lat:>8.2f}s")

    out = Path(__file__).parent / f"results_{llm.name.replace(':', '_')}.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
