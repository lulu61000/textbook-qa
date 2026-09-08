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


class OllamaLLM:
    def __init__(self, model: str = config.OLLAMA_MODEL):
        from openai import OpenAI
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = model
        self.name = f"ollama:{model}"

    def generate(self, prompt: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,          # deterministic: evals must be repeatable
        )
        return r.choices[0].message.content


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
    return {"ollama": OllamaLLM, "claude": ClaudeLLM}[backend]()
