"""Central config. Everything tunable lives here, not scattered in the code."""
import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
INDEX_DIR = ROOT / "index"

# --- retrieval ---
TOP_K = 3              # chunks passed to the LLM
BM25_WEIGHT = 0.7      # term queries favour lexical match; tune this with evals
CHUNK_TARGET_TOKENS = 150

# --- evals ---
# Page fallback (expect_pages) only switches on when the corpus has MORE pages
# than this. On a short document most chunks sit on an "expected" page, so a
# page match says nothing about whether the chunk holds the answer.
PAGE_AMOUNT_TRIGGER_PAGE_HIT = 50

# --- generation ---
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")   # "ollama" | "claude" | "openai"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")   # key: ANTHROPIC_API_KEY

# Any OpenAI-compatible endpoint: OpenAI, vLLM, LM Studio, DeepSeek, OpenRouter...
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")   # None -> official OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
