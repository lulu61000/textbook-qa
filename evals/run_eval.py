"""Run the golden set and report per-category metrics.

Report retrieval and generation separately. An aggregate score tells you the
system got worse; it does not tell you which half to fix.

    python -m evals.run_eval
    LLM_BACKEND=claude python -m evals.run_eval     # same set, other model
    python -m evals.run_eval --retriever hybrid     # bm25 (default) | vector | hybrid
"""
import json, time, argparse
from pathlib import Path
from collections import defaultdict
import config
from src.chunks import load_chunks
from src.retrieve import get_retriever, RETRIEVERS
from src.llm import get_llm
from src.pipeline import answer

GOLDEN = Path(__file__).parent / "golden.jsonl"


def load_golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def retrieval_hit(ans, case) -> tuple[bool | None, str | None]:
    """Did the chunks handed to the LLM hold the evidence? Same rule as
    retrieval-only: keywords first, expect_pages as fallback.
    Returns (hit, "keyword" | "page" | None); hit is None if untestable."""
    if not case["expect_keywords"] and not case.get("expect_pages"):
        return None, None
    rank, how = correct_rank(list(zip(ans.chunks, ans.scores)), case)
    return rank is not None, how


def keyword_recall(ans, keywords) -> float | None:
    """Crude proxy for answer completeness. Replace with an LLM judge once
    the pipeline is stable -- but keep this too: it is free, deterministic,
    and catches regressions a judge might wave through."""
    if not keywords:
        return None
    text = ans.text.lower()
    return sum(k.lower() in text for k in keywords) / len(keywords)


# ---------------------------------------------------------------- retrieval-only

def correct_rank(hits, case) -> tuple[int | None, str | None]:
    """(1-based rank, how it matched). Keywords first, pages as fallback.

    1. "keyword": smallest r such that the top-r chunks together contain every
       expect_keyword (so hit@k == rank <= k, matching the old all-keywords check).
    2. "page": keywords not all found within the search depth, but some chunk
       sits on an expect_page -> rank of the first such chunk. Weaker evidence:
       right page, but the chunk may not hold the answer.
    3. (None, None): neither found within the search depth.
    expect_pages is optional; questions without it skip step 2.
    """
    pages = set(case.get("expect_pages", []))
    missing = {k.lower() for k in case["expect_keywords"]}
    if missing:
        for r, (c, _) in enumerate(hits, 1):
            text = c.text.lower()
            missing = {k for k in missing if k not in text}
            if not missing:
                return r, "keyword"
    if pages:
        for r, (c, _) in enumerate(hits, 1):
            if c.page in pages:
                return r, "page"
    return None, None


def run_retrieval_only(args, retriever, chunks):
    depth = max(args.k, args.k_wide, args.rank_depth)
    rows, by_type = [], defaultdict(list)
    for case in load_golden():
        row = {"id": case["id"], "type": case["type"], "rank": None, "how": None, "na": False}
        if not case["expect_keywords"] and not case.get("expect_pages"):
            row["na"] = True            # abstention: only testable end to end
        else:
            row["rank"], row["how"] = correct_rank(
                retriever.search(case["question"], depth), case)
        rows.append(row)
        by_type[case["type"]].append(row)

    def stats(rs):
        scored = [r for r in rs if not r["na"]]
        if not scored:
            return None
        ranks = [r["rank"] for r in scored]
        return {
            "n": len(rs),
            "at_k": sum(x is not None and x <= args.k for x in ranks) / len(ranks),
            "at_wide": sum(x is not None and x <= args.k_wide for x in ranks) / len(ranks),
            "mrr": sum(1 / x for x in ranks if x) / len(ranks),
            "page_only": sum(r["how"] == "page" for r in scored),
        }

    def fmt_rank(r):
        if r["na"]:
            return f"{r['id']}:n/a"
        if r["rank"] is None:
            return f"{r['id']}:>{depth}"
        return f"{r['id']}:{r['rank']}{'p' if r['how'] == 'page' else ''}"

    head = ["type", "n", f"recall@{args.k}", f"recall@{args.k_wide}", "MRR",
            "page-only", "ranks"]
    table = []
    for t, rs in list(by_type.items()) + [("**all**", rows)]:
        s = stats(rs)
        cells = ([f"{s['at_k']:.2f}", f"{s['at_wide']:.2f}", f"{s['mrr']:.2f}",
                  str(s["page_only"])] if s else ["n/a"] * 4)
        ranks = "" if t == "**all**" else " ".join(fmt_rank(r) for r in rs)
        table.append([t, str(len(rs)), *cells, ranks])

    # terminal
    print(f"\nretriever={args.retriever}  k={args.k}  k_wide={args.k_wide}  depth={depth}")
    print(f"ranks: N = keyword match, Np = page match only, >{depth} = neither, n/a = untestable\n")
    print(f"{head[0]:<14}{head[1]:>4}{head[2]:>11}{head[3]:>12}{head[4]:>7}{head[5]:>11}  {head[6]}")
    for row in table:
        print(f"{row[0]:<14}{row[1]:>4}{row[2]:>11}{row[3]:>12}{row[4]:>7}{row[5]:>11}  {row[6]}")

    if not args.no_record:
        out = record_baseline(args, chunks, depth, head, table)
        print(f"\n-> appended to {out}")


def _run_info(chunks) -> dict:
    """Everything needed to know, weeks later, what produced a number."""
    import hashlib, inspect, subprocess
    from datetime import datetime
    from src import retrieve

    chunks_file = config.INDEX_DIR / "chunks.jsonl"
    try:
        git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=config.ROOT,
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=config.ROOT,
                               capture_output=True, text=True).stdout.strip()
        git = (git or "?") + (" + uncommitted changes" if dirty else "")
    except OSError:
        git = "?"
    return {
        "when": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chunks": len(chunks),
        "chunks_sha": hashlib.sha1(chunks_file.read_bytes()).hexdigest()[:8],
        "tokenizer_sha": hashlib.sha1(inspect.getsource(retrieve.tokenize).encode()).hexdigest()[:8],
        "git": git,
    }


BASELINES = Path(__file__).parent / "baselines.md"


def record_baseline(args, chunks, depth, head, table) -> Path:
    info = _run_info(chunks)
    lines = []
    if not BASELINES.exists():
        lines += ["# Retrieval baselines", "",
                  "Appended by `python -m evals.run_eval --retrieval-only`. "
                  "Newest at the bottom. Ranks: position where the correct chunk "
                  f"is first fully retrieved; `>N` = not found in the top N.", ""]
    weight = f", bm25_weight={config.BM25_WEIGHT}" if args.retriever == "hybrid" else ""
    lines += [
        f"## {info['when']} · {args.retriever} · k={args.k}",
        "",
        f"- note: {args.note or '—'}",
        f"- corpus: {args.corpus or 'not given'} — `index/chunks.jsonl`, "
        f"{info['chunks']} chunks, sha1 `{info['chunks_sha']}`",
        f"- config: k={args.k}, k_wide={args.k_wide}, rank_depth={depth}, "
        f"chunk_target_tokens={config.CHUNK_TARGET_TOKENS}{weight}, "
        f"tokenizer sha1 `{info['tokenizer_sha']}`",
        f"- code: git `{info['git']}`",
        f"- ranks: `N` keyword match, `Np` page match only (keywords missed), "
        f"`>{depth}` neither, `n/a` untestable (no keywords or pages)",
        "",
        "| " + " | ".join(head) + " |",
        "|" + "|".join(["---"] * len(head)) + "|",
        *["| " + " | ".join(row) + " |" for row in table],
        "", "",
    ]
    with open(BASELINES, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return BASELINES


# ---------------------------------------------------------------- end to end

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--k", type=int, default=config.TOP_K)
    p.add_argument("--retrieval-only", action="store_true")
    p.add_argument("--retriever", choices=RETRIEVERS, default="bm25")
    p.add_argument("--k-wide", type=int, default=10,
                   help="second cutoff; recall@k low but @k-wide high = ranking problem")
    p.add_argument("--rank-depth", type=int, default=50,
                   help="how deep to look for the correct chunk's rank")
    p.add_argument("--corpus", default="",
                   help="which source the index was built from, e.g. Britt-Marie.pdf")
    p.add_argument("--note", default="", help="what changed since the last run")
    p.add_argument("--no-record", action="store_true",
                   help="print only, don't append to evals/baselines.md")
    args = p.parse_args()


    chunks = load_chunks(config.INDEX_DIR / "chunks.jsonl")
    retriever = get_retriever(args.retriever, chunks)
    if args.retrieval_only:
        run_retrieval_only(args, retriever, chunks)
        return

    llm = get_llm()   # after the branch: retrieval-only needs no model or API key
    rows, by_type = [], defaultdict(list)

    for case in load_golden():
        t0 = time.perf_counter()
        ans = answer(case["question"], retriever, llm, args.k)
        elapsed = time.perf_counter() - t0
        hit, how = retrieval_hit(ans, case)
        row = {
            "id": case["id"],
            "type": case["type"],
            "retrieval_hit": hit,
            "retrieval_match": how,          # "keyword" | "page" | None
            "keyword_recall": keyword_recall(ans, case["expect_keywords"]),
            "latency_s": round(elapsed, 2),
            "answer": ans.text,
            "cited": ans.citations,
        }
        rows.append(row)
        by_type[case["type"]].append(row)

    print(f"\nretriever={args.retriever}  backend={llm.name}  k={args.k}  n={len(rows)}\n")
    print(f"{'type':<14}{'n':>4}{'retr_hit':>10}{'page-only':>11}{'kw_recall':>11}{'latency':>9}")
    for t, rs in by_type.items():
        hits = [r['retrieval_hit'] for r in rs if r['retrieval_hit'] is not None]
        kws = [r['keyword_recall'] for r in rs if r['keyword_recall'] is not None]
        h = f"{sum(hits)/len(hits):.2f}" if hits else "-"
        po = str(sum(r['retrieval_match'] == "page" for r in rs)) if hits else "-"
        k = f"{sum(kws)/len(kws):.2f}" if kws else "-"
        lat = sum(r['latency_s'] for r in rs) / len(rs)
        print(f"{t:<14}{len(rs):>4}{h:>10}{po:>11}{k:>11}{lat:>8.2f}s")

    out = Path(__file__).parent / f"results_{args.retriever}_{llm.name.replace(':', '_')}.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
