# Textbook QA

Ask questions about terms in a PDF textbook. Answers cite the page they came from.

## First Time Setup
# Asumming Linux
    uv venv --python 3.11 && source .venv/bin/activate
    uv pip install pymupdf rank-bm25 numpy openai streamlit
    ollama pull qwen2.5:7b-instruct

# Asumming Windows with python 3.11  
    rmdir /s /q .venv
    uv venv --python 3.11
    .venv\Scripts\activate
    uv pip install pymupdf rank-bm25 numpy openai streamlit

`sentence-transformers` and `anthropic` are only needed in phase 2.

## Test Before Use
    python -m evals.run_eval --retrieval-only     # check retriever if hit key words
    python -m evals.llm_test                      # llm running test

## Use

    python -m scripts.build_index data/book.pdf   # PDF -> index/chunks.jsonl
    python -m evals.run_eval                      # metrics
    streamlit run app.py                          # demo

## Recording retrieval baselines

Every `--retrieval-only` run prints a per-type table and appends it to
[`evals/baselines.md`](evals/baselines.md), together with the date, corpus,
config (k, chunk size, tokenizer hash, chunks.jsonl hash) and git commit, so
each number can be traced to what produced it.

    python -m evals.run_eval --retrieval-only --corpus My_words.pdf --note "what changed"

| Flag | Default | Meaning |
|------|---------|---------|
| `--retriever` | `bm25` | `bm25` \| `vector` \| `hybrid` (vector/hybrid not finished yet) |
| `--k` | `TOP_K` (3) | main cutoff |
| `--k-wide` | 10 | second cutoff: recall@k low but recall@k-wide high = ranking problem; both low = recall problem |
| `--rank-depth` | 50 | how deep to search for the correct chunk's rank |
| `--corpus`, `--note` | — | written into the record; the index doesn't store its source PDF |
| `--no-record` | off | print only |

Columns: recall@k, recall@k-wide, MRR, page-only count, and every question's
rank. A question counts as found when the top-r chunks together contain all
its `expect_keywords`. If they don't (within the search depth), it falls back
to `expect_pages` (optional in `golden.jsonl`). Ranks read `N` = keyword match,
`Np` = page match only, `>50` = neither, `n/a` = no keywords or pages
(abstention). End-to-end runs use the same rule on the k chunks given to the
model, saved as `retrieval_match` in the results JSON.

The page fallback only switches on when the corpus has more pages than
`PAGE_AMOUNT_TRIGGER_PAGE_HIT` in `config.py` (default 50): on a short
document most chunks sit on an "expected" page, so a page match proves
nothing. Each run prints and records whether it was ON or OFF. When ON,
retrieval-only checks keywords across the whole depth before trying pages,
so it can still disagree with end-to-end on the same question.

## Choosing the LLM

Set via environment variables (read in `config.py`; no `.env` file is loaded).
`LLM_BACKEND` picks the backend, default `ollama`.

| Backend  | Variables (default)                                                                 |
|----------|-------------------------------------------------------------------------------------|
| `ollama` | `OLLAMA_MODEL` (`qwen2.5-coder:1.5b`), `OLLAMA_BASE_URL` (`http://localhost:11434/v1`) |
| `claude` | `CLAUDE_MODEL` (`claude-sonnet-5-5`), `ANTHROPIC_API_KEY` (required)                 |
| `openai` | `OPENAI_MODEL` (`gpt-4o-mini`), `OPENAI_BASE_URL` (unset = official OpenAI), `OPENAI_API_KEY` (required) |

- **model**: which model the server should run, e.g. `gpt-4o-mini`, `deepseek-chat`.
- **base URL**: where requests are sent. Point it at any OpenAI-compatible
  server (vLLM, LM Studio, DeepSeek, OpenRouter, a remote Ollama...).
- **API key**: proves who you are to that server and gets billed. Local servers
  that don't check it still need a non-empty string.

Linux / bash (one-off for a single command):

    LLM_BACKEND=openai OPENAI_BASE_URL=https://api.deepseek.com/v1 \
      OPENAI_API_KEY=<key> OPENAI_MODEL=deepseek-chat python -m evals.llm_test

Windows / PowerShell (lasts for the current window):

    $env:LLM_BACKEND="openai"; $env:OPENAI_BASE_URL="https://api.deepseek.com/v1"
    $env:OPENAI_API_KEY="<key>"; $env:OPENAI_MODEL="deepseek-chat"
    python -m evals.llm_test

Run `evals.run_eval` under each backend to compare models on the same golden
set; results are saved as `evals/results_<retriever>_<backend>_<model>.json`.
Pick the retriever with `--retriever bm25|vector|hybrid` (default `bm25`).

## Build order

1. Extraction + chunking, checked by hand on a few pages
2. BM25 retrieval, 30-50 golden questions, **record the baseline**
3. Prompt iteration, measured against that baseline
4. Vector retrieval -> hybrid, report the delta over BM25
5. Local 7B vs hosted model on the same set, report the gap and the cost

Each step's number is the deliverable. A pipeline with no baseline cannot
show improvement, and unmeasured improvement is indistinguishable from none.

## Next steps (planned, not started)

The point of this project is the evaluation: an empirical look at *why* RAG
retrieval fails, with an eval setup anyone can re-run. Building the RAG is
the easy part. Plan: get the full comparison numbers, put them in this
README, then stop adding features.

**0. Record the baseline first.** (Done for BM25 on `My_words.pdf`, see
`evals/baselines.md`.) Run A and save its numbers before touching
any code. Otherwise, after several changes, there's no telling which one
helped.

**1. Four runs**

| Run | Retrieval | Generation | Command |
|-----|-----------|------------|---------|
| A | BM25   | skipped  | `python -m evals.run_eval --retrieval-only` |
| B | hybrid | skipped  | `--retrieval-only --retriever hybrid` |
| C | hybrid | local 7B | `LLM_BACKEND=ollama` |
| D | hybrid | Claude   | `LLM_BACKEND=claude` |

Prerequisites: the `--retriever {bm25,vector,hybrid}` flag exists, but
`HybridRetriever.search` is still a stub and `VectorRetriever` is untested.
A cost-per-query column is also still needed (latency is already recorded).

The findings are the differences between runs:
- **B − A**: what vector retrieval adds. This is the only evidence that hybrid retrieval is worth it.
- **B − C**: loss at the generation step. The answer was in the retrieved text, but the model didn't use it.
- **D − C**: what a stronger model adds.

B is the upper limit for C and D. If C or D scores higher than B, the model
is answering from what it already knew before seeing the document, which is
a bad sign.

**2. What to expect for each question type** (counts from the novel's golden set)

| Type | n | What it tests / what to expect |
|------|---|--------------------------------|
| entity        | 10 | Sanity check: rare names that appear word-for-word in the text. A should be near perfect; if not, fix the pipeline before anything else. B may dip slightly: hybrid has a cost, and that's worth reporting. |
| attribute     | 6  | Facts about entities. If the number is in the passage but the model gets it wrong, it shows up in B − C. |
| paraphrase    | 5  | Questions worded differently from the text (asks "sampled", text says "chose"). Most important cell: expect A low, B much higher. If B doesn't improve, look for a bug in the score merging or a bad embedding model. C/D can exceed B here because keyword matching follows the text's wording, so this is a grading artifact. |
| pronoun       | 3  | The answer passage says "she", not the name. Expect A low, B only slightly better. Still unsolved; fixing it needs resolving who "she" is, or adding the scene's subject to each chunk. Report it as a known limit. |
| cross_section | 4  | Answer spread across distant passages. Changes with TOP_K, not with retrieval method. `xsec01` is expected to fail and kept on purpose to show the upper limit. |
| abstention    | 6  | Questions the document can't answer; the right answer is to decline. Leave A/B as N/A, since this can only be tested end to end. Expect C clearly worse than D. `abs05` (author's comments) tests whether the model answers from prior knowledge instead of the document, i.e. makes things up. |

**3. Cost table**

|   | Retrieval accuracy | Avg latency | Cost per query |
|---|--------------------|-------------|----------------|
| C (local 7B) | | | $0 |
| D (Claude)   | | | |

Target conclusion, if the data supports it: outside abstention and
cross_section, the local 7B model is within a few points of Claude. If so,
sending each question type to the cheaper model when it's good enough would
cut cost by X.

**4. Write up.** Fill the tables above, add one or two sentences on why each
change helped, and rewrite the opening of this README: "A study of why RAG
retrieval fails, with a re-runnable evaluation setup" instead of "a textbook
QA tool".

## Ollama
Runs on the Windows host (not inside WSL).
Requires `networkingMode=mirrored` in `C:\Users\<user>\.wslconfig`.
Verify: `cat /etc/resolv.conf` should show `nameserver 127.0.0.1`.
If localhost:11434 refuses, fully close VSCode, then `wsl --shutdown`, wait 10s.