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

## 2026-11-16 13:38 · bm25 · k=3

- note: BM25 baseline re-recorded with page fallback OFF (7 pages <= PAGE_AMOUNT_TRIGGER_PAGE_HIT=50); supersedes the previous entry, which counted page-only matches
- corpus: My_words.pdf — `index/chunks.jsonl`, 169 chunks, sha1 `c6d96f65`
- config: k=3, k_wide=10, rank_depth=50, chunk_target_tokens=150, tokenizer sha1 `9a889766`
- page fallback OFF (7 pages <= 50)
- code: git `c6d385b + uncommitted changes`
- ranks: `N` keyword match, `Np` page match only (keywords missed), `>50` neither, `n/a` untestable (no keywords or pages)

| type | n | recall@3 | recall@10 | MRR | page-only | ranks |
|---|---|---|---|---|---|---|
| numeric | 13 | 0.69 | 0.77 | 0.65 | 0 | num01:10 num02:26 num03:1 num04:1 num05:1 num06:1 num07:1 num08:1 num09:1 num10:1 num11:>50 num12:>50 num13:3 |
| definition | 5 | 0.20 | 0.80 | 0.30 | 0 | def01:5 def02:1 def03:7 def04:>50 def05:7 |
| lexical | 3 | 0.67 | 1.00 | 0.75 | 0 | lex01:1 lex02:1 lex03:4 |
| paraphrase | 7 | 0.29 | 0.43 | 0.33 | 0 | par01:15 par02:5 par03:>50 par04:25 par05:>50 par06:1 par07:1 |
| cross_section | 4 | 0.00 | 0.25 | 0.05 | 0 | xsec01:>50 xsec02:24 xsec03:>50 xsec04:7 |
| conflict | 1 | 1.00 | 1.00 | 1.00 | 0 | conf01:1 |
| abstention | 4 | n/a | n/a | n/a | n/a | abs01:n/a abs02:n/a abs03:n/a abs04:n/a |
| **all** | 37 | 0.45 | 0.67 | 0.48 | 0 |  |

## 2026-11-16 15:20 · vector · k=3

- note: vector (bge-small) WITH query prefix
- corpus: My_words.pdf — `index/chunks.jsonl`, 169 chunks, sha1 `c6d96f65`
- config: k=3, k_wide=10, rank_depth=50, chunk_target_tokens=150, tokenizer sha1 `9a889766`
- page fallback OFF (7 pages <= 50)
- embed: BAAI/bge-small-en-v1.5, prefixes from config.EMBED_PREFIXES, query prefix 'Represent this sentence for searching relevant passages: ', document prefix '', cache `vectors_76addaf10d.npy`
- code: git `85432b5 + uncommitted changes`
- ranks: `N` keyword match, `Np` page match only (keywords missed), `>50` neither, `n/a` untestable (no keywords or pages)

| type | n | recall@3 | recall@10 | MRR | page-only | ranks |
|---|---|---|---|---|---|---|
| numeric | 13 | 0.62 | 0.85 | 0.60 | 0 | num01:3 num02:9 num03:1 num04:1 num05:1 num06:1 num07:1 num08:6 num09:1 num10:1 num11:>50 num12:6 num13:>50 |
| definition | 5 | 1.00 | 1.00 | 0.80 | 0 | def01:1 def02:1 def03:2 def04:1 def05:2 |
| lexical | 3 | 0.67 | 1.00 | 0.57 | 0 | lex01:1 lex02:5 lex03:2 |
| paraphrase | 7 | 0.14 | 0.57 | 0.22 | 0 | par01:8 par02:4 par03:50 par04:>50 par05:>50 par06:1 par07:7 |
| cross_section | 4 | 0.25 | 0.50 | 0.18 | 0 | xsec01:30 xsec02:7 xsec03:25 xsec04:2 |
| conflict | 1 | 1.00 | 1.00 | 1.00 | 0 | conf01:1 |
| abstention | 4 | n/a | n/a | n/a | n/a | abs01:n/a abs02:n/a abs03:n/a abs04:n/a |
| **all** | 37 | 0.55 | 0.79 | 0.51 | 0 |  |

## 2026-11-16 15:20 · vector · k=3

- note: vector (bge-small) WITHOUT prefix (EMBED_PREFIXES_OFF=1), to measure the prefix
- corpus: My_words.pdf — `index/chunks.jsonl`, 169 chunks, sha1 `c6d96f65`
- config: k=3, k_wide=10, rank_depth=50, chunk_target_tokens=150, tokenizer sha1 `9a889766`
- page fallback OFF (7 pages <= 50)
- embed: BAAI/bge-small-en-v1.5, prefixes from off (EMBED_PREFIXES_OFF=1), query prefix '', document prefix '', cache `vectors_7631cebb4e.npy`
- code: git `85432b5 + uncommitted changes`
- ranks: `N` keyword match, `Np` page match only (keywords missed), `>50` neither, `n/a` untestable (no keywords or pages)

| type | n | recall@3 | recall@10 | MRR | page-only | ranks |
|---|---|---|---|---|---|---|
| numeric | 13 | 0.62 | 0.77 | 0.60 | 0 | num01:3 num02:7 num03:1 num04:1 num05:1 num06:1 num07:1 num08:14 num09:1 num10:1 num11:48 num12:5 num13:>50 |
| definition | 5 | 1.00 | 1.00 | 0.80 | 0 | def01:1 def02:1 def03:2 def04:1 def05:2 |
| lexical | 3 | 0.67 | 1.00 | 0.58 | 0 | lex01:1 lex02:4 lex03:2 |
| paraphrase | 7 | 0.14 | 0.43 | 0.13 | 0 | par01:7 par02:6 par03:>50 par04:>50 par05:>50 par06:2 par07:11 |
| cross_section | 4 | 0.25 | 0.25 | 0.16 | 0 | xsec01:>50 xsec02:11 xsec03:30 xsec04:2 |
| conflict | 1 | 1.00 | 1.00 | 1.00 | 0 | conf01:1 |
| abstention | 4 | n/a | n/a | n/a | n/a | abs01:n/a abs02:n/a abs03:n/a abs04:n/a |
| **all** | 37 | 0.55 | 0.70 | 0.49 | 0 |  |

