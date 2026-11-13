"""LLM backends behind one interface.

The point is not convenience later -- it is that you can run the SAME golden
set through a local 7B and through a hosted model and report the gap. That
comparison is the interesting result, and it is only cheap if the seam exists
from day one.
"""
from typing import Protocol
import config


class LLM(Protocol):
    name: str
    def generate(self, prompt: str) -> str: ...


class OpenAICompatLLM:
    """Any server speaking the OpenAI chat-completions API."""

    def __init__(self, model: str = None, base_url: str = None,
                 api_key: str = None, label: str = "openai"):
        from openai import OpenAI
        model = model or config.OPENAI_MODEL
        if label == "openai":
            base_url = base_url or config.OPENAI_BASE_URL
            api_key = api_key or config.OPENAI_API_KEY
            if not api_key:
                raise RuntimeError(
                    "LLM_BACKEND=openai needs OPENAI_API_KEY "
                    "(use any non-empty string for local servers that ignore it)"
                )
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.name = f"{label}:{model}"

    def generate(self, prompt: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,          # deterministic: evals must be repeatable
        )
        return r.choices[0].message.content


class OllamaLLM(OpenAICompatLLM):
    def __init__(self, model: str = config.OLLAMA_MODEL):
        super().__init__(model=model, base_url=config.OLLAMA_BASE_URL,
                         api_key="ollama", label="ollama")


class ClaudeLLM:
    def __init__(self, model: str = config.CLAUDE_MODEL):
        import anthropic
        self.client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY
        self.model = model
        self.name = f"claude:{model}"

    def generate(self, prompt: str) -> str:
        r = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text



def get_llm(backend: str = None) -> LLM:
    backend = backend or config.LLM_BACKEND
    backends = {"ollama": OllamaLLM, "claude": ClaudeLLM, "openai": OpenAICompatLLM}
    if backend not in backends:
        raise ValueError(f"unknown LLM_BACKEND={backend!r}; choose from {list(backends)}")
    return backends[backend]()
