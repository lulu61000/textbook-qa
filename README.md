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
set; results are saved per backend as `evals/results_<backend>_<model>.json`.

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