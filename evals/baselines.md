# Retrieval baselines

Appended by `python -m evals.run_eval --retrieval-only`. Newest at the bottom. Ranks: position where the correct chunk is first fully retrieved; `>N` = not found in the top N.

## 2026-11-14 13:26 · bm25 · k=3

- note: BM25 baseline, before any changes
- corpus: My_words.pdf — `index/chunks.jsonl`, 169 chunks, sha1 `c6d96f65`
- config: k=3, k_wide=10, rank_depth=50, chunk_target_tokens=150, tokenizer sha1 `9a889766`
- code: git `d5b823a + uncommitted changes`
- ranks: `N` keyword match, `Np` page match only (keywords missed), `>50` neither, `n/a` untestable (no keywords or pages)

| type | n | recall@3 | recall@10 | MRR | page-only | ranks |
|---|---|---|---|---|---|---|
| numeric | 13 | 0.85 | 0.92 | 0.77 | 2 | num01:10 num02:26 num03:1 num04:1 num05:1 num06:1 num07:1 num08:1 num09:1 num10:1 num11:1p num12:2p num13:3 |
| definition | 5 | 0.40 | 1.00 | 0.50 | 1 | def01:5 def02:1 def03:7 def04:1p def05:7 |
| lexical | 3 | 0.67 | 1.00 | 0.75 | 0 | lex01:1 lex02:1 lex03:4 |
| paraphrase | 7 | 0.57 | 0.71 | 0.62 | 2 | par01:15 par02:5 par03:1p par04:25 par05:1p par06:1 par07:1 |
| cross_section | 4 | 0.50 | 0.75 | 0.42 | 2 | xsec01:2p xsec02:24 xsec03:1p xsec04:7 |
| conflict | 1 | 1.00 | 1.00 | 1.00 | 0 | conf01:1 |
| abstention | 4 | n/a | n/a | n/a | n/a | abs01:n/a abs02:n/a abs03:n/a abs04:n/a |
| **all** | 37 | 0.67 | 0.88 | 0.66 | 7 |  |

