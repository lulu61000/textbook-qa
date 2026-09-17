# Textbook QA

Ask questions about terms in a PDF textbook. Answers cite the page they came from.

## Setup

    uv venv --python 3.11 && source .venv/bin/activate
    uv pip install pymupdf rank-bm25 numpy openai streamlit
    ollama pull qwen2.5:7b-instruct

`sentence-transformers` and `anthropic` are only needed in phase 2.

## Test Before Use
    python -m evals.run_eval --retrieval-only     # check retriever if hit key words
    python -m evals.llm_test                      # llm running test

## Use

    python -m scripts.build_index data/book.pdf   # PDF -> index/chunks.jsonl
    python -m evals.run_eval                      # metrics
    streamlit run app.py                          # demo

## Build order

1. Extraction + chunking, checked by hand on a few pages
2. BM25 retrieval, 30-50 golden questions, **record the baseline**
3. Prompt iteration, measured against that baseline
4. Vector retrieval -> hybrid, report the delta over BM25
5. Local 7B vs hosted model on the same set, report the gap and the cost

Each step's number is the deliverable. A pipeline with no baseline cannot
show improvement, and unmeasured improvement is indistinguishable from none.

## Ollama
Runs on the Windows host (not inside WSL).
Requires `networkingMode=mirrored` in `C:\Users\<user>\.wslconfig`.
Verify: `cat /etc/resolv.conf` should show `nameserver 127.0.0.1`.
If localhost:11434 refuses, fully close VSCode, then `wsl --shutdown`, wait 10s.