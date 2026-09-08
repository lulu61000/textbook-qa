"""Wires retrieval and generation together.

answer() returns the retrieved chunks alongside the text, not just a string.
Evaluation needs to distinguish "retrieval missed it" from "retrieval found
it and the model ignored it" -- those are different bugs with different fixes,
and a bare string cannot tell them apart.
"""
from dataclasses import dataclass, field
from .chunks import Chunk
from .retrieve import Retriever
from .llm import LLM


PROMPT = """\
You are helping a student understand a textbook. Answer using ONLY the
excerpts below. If they do not contain the answer, say so plainly rather
than filling the gap from general knowledge.

Cite the location after each claim, like [4.2 p.137].

Excerpts:
{context}

Question: {question}

Answer:"""
# TODO: this is a first draft, not a finished prompt. Things to test against
# your golden set: whether few-shot examples improve citation formatting;
# whether asking for a definition-then-elaboration structure helps term
# lookups; how it behaves when the excerpts genuinely lack the answer
# (abstention is a measurable behaviour -- test it deliberately).


@dataclass
class Answer:
    text: str
    chunks: list[Chunk] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)

    @property
    def citations(self) -> list[str]:
        return [c.cite() for c in self.chunks]


def format_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[{c.cite()}]\n{c.text}" for c in chunks)


def answer(question: str, retriever: Retriever, llm: LLM, k: int) -> Answer:
    hits = retriever.search(question, k)
    chunks = [c for c, _ in hits]
    scores = [s for _, s in hits]
    prompt = PROMPT.format(context=format_context(chunks), question=question)
    return Answer(text=llm.generate(prompt), chunks=chunks, scores=scores)
