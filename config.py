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

# --- generation ---
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")   # "ollama" | "claude"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
