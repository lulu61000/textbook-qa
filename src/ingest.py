"""PDF -> Chunk list.

This is where most of the quality is won or lost. If extraction gets the
reading order wrong, or chunks straddle section boundaries, nothing
downstream can recover.
"""
import fitz  # PyMuPDF
from .chunks import Chunk


def extract_pages(pdf_path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...]. Page numbers are 1-based."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        # "blocks" preserves reading order better than plain get_text()
        # on multi-column layouts, which most textbooks use.
        text = page.get_text("text")
        pages.append((i, text))
    doc.close()
    return pages


def strip_furniture(text: str) -> str:
    """Remove running headers/footers and page numbers.

    TODO: these repeat on nearly every page, so the cheap approach is to
    collect the first and last line of every page, count frequencies, and
    drop lines that appear on more than ~30% of pages. Do this globally,
    not per page.
    """

    return text


def detect_headings(pages: list[tuple[int, str]]) -> dict[int, str]:
    """Map page number -> section heading in effect on that page.

    TODO: textbook headings are usually numbered ("4.2 Monads"). A regex for
    ^\\d+(\\.\\d+)*\\s+[A-Z] catches most of them. Carry the last seen heading
    forward so every page gets a label.
    """
    return {}


def chunk_pages(pages: list[tuple[int, str]], target_tokens: int) -> list[Chunk]:
    """Split into retrieval units.

    TODO: split on section boundaries first, then subdivide anything still
    too long at paragraph breaks. Do NOT split at a fixed token count with no
    regard for structure -- a definition cut in half is unrecoverable, and the
    book's own structure is free information.

    Consider a small overlap (1-2 sentences) between adjacent chunks so a
    definition spanning a boundary still lands intact somewhere.
    """
    idd = 1
    final_chunks =  []
    for page in pages:
        for line in page[1].split("."):
            line = line.replace("\n", "")
            if not line.strip():
                continue
            line_chunk = Chunk(idd, line, page[0])
            final_chunks.append(line_chunk)
            idd += 1
    return final_chunks


def parse_book_index(pages: list[tuple[int, str]]) -> dict[str, list[int]]:
    """Parse the back-of-book index into {term: [page, ...]}.

    The index is a human-curated term->location map sitting in the PDF for
    free. For term lookups it beats anything retrieval will infer. Worth
    doing early -- it lifts accuracy more than chunk-size tuning will.

    TODO: find the index section (usually after the last chapter, entries
    look like "monad, 137, 140-142"), then parse entry lines.
    """
    return {}


def build(pdf_path, target_tokens: int) -> list[Chunk]:
    pages = extract_pages(pdf_path)
    pages = [(n, strip_furniture(t)) for n, t in pages]
    return chunk_pages(pages, target_tokens)
