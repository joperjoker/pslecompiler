"""PDF -> structured sections.

Uses PyMuPDF (``fitz``) to extract text spans with font sizes, then infers a
heading hierarchy from relative font size. Output is a flat, ordered list of
``Section`` blocks (heading level + title + body text + page), which the
subject-specific mappers in ``structure.py`` turn into graph nodes.

Kept deterministic and dependency-light so it is testable without a real PDF:
``sections_from_blocks`` operates on plain (size, text, page) tuples and has no
PyMuPDF dependency.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Section:
    level: int          # 1 = biggest heading, larger = deeper; 99 = body text
    title: str          # heading text (or "" for body-only block)
    text: str           # body text under this heading (may be "")
    page: int

    def to_dict(self) -> dict:
        return asdict(self)


def _rank_sizes(sizes: list[float], max_levels: int = 4) -> dict[float, int]:
    """Map distinct font sizes to heading levels 1..max_levels (desc)."""
    distinct = sorted({round(s, 1) for s in sizes}, reverse=True)
    ranking: dict[float, int] = {}
    for i, s in enumerate(distinct):
        ranking[s] = min(i + 1, max_levels)
    return ranking


def sections_from_blocks(
    blocks: list[tuple[float, str, int]], body_size_threshold: float | None = None
) -> list[Section]:
    """Turn (font_size, text, page) blocks into ordered Sections.

    Blocks at or below the body-size threshold are treated as body text and
    attached to the most recent heading.
    """
    blocks = [(s, t.strip(), p) for s, t, p in blocks if t and t.strip()]
    if not blocks:
        return []

    sizes = [s for s, _, _ in blocks]
    if body_size_threshold is None:
        # Heuristic: the modal (most common) size is body text.
        from collections import Counter

        body_size_threshold = Counter(round(s, 1) for s in sizes).most_common(1)[0][0]

    heading_sizes = [s for s in sizes if round(s, 1) > body_size_threshold]
    ranking = _rank_sizes(heading_sizes) if heading_sizes else {}

    sections: list[Section] = []
    for size, text, page in blocks:
        r = round(size, 1)
        if r > body_size_threshold and r in ranking:
            sections.append(Section(level=ranking[r], title=text, text="", page=page))
        else:
            if sections:
                sep = "\n" if sections[-1].text else ""
                sections[-1].text += sep + text
            else:
                sections.append(Section(level=99, title="", text=text, page=page))
    return sections


def parse_pdf(path: Path) -> list[Section]:
    """Parse a real PDF into Sections (requires PyMuPDF)."""
    import fitz  # type: ignore

    blocks: list[tuple[float, str, int]] = []
    with fitz.open(path) as doc:
        for pno, page in enumerate(doc, start=1):
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    text = "".join(sp.get("text", "") for sp in spans)
                    size = max(sp.get("size", 0.0) for sp in spans)
                    if text.strip():
                        blocks.append((size, text, pno))
    return sections_from_blocks(blocks)


def write_parsed(sections: list[Section], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps([s.to_dict() for s in sections], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def read_parsed(path: Path) -> list[Section]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Section(**d) for d in data]
