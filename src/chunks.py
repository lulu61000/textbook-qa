"""The unit that flows through the whole pipeline.

Provenance is not optional: a teaching tool is only trustworthy if every
answer can be traced back to a page the student can open. Carry page and
section from extraction all the way through to the citation.
"""
from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class Chunk:
    id: str
    text: str
    page: int                      # 1-based, as printed in the book
    section: Optional[str] = None  # e.g. "4.2 Monads"
    chapter: Optional[str] = None

    def cite(self) -> str:
        loc = self.section or self.chapter or ""
        return f"{loc} p.{self.page}".strip()


def save_chunks(chunks: list[Chunk], path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")


def load_chunks(path) -> list[Chunk]:
    with open(path, encoding="utf-8") as f:
        return [Chunk(**json.loads(line)) for line in f if line.strip()]
