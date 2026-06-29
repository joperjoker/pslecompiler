"""Past-paper PDF -> raw MCQ items.

PSLE MCQ papers number questions (1, 2, 3, ...) each with four options, commonly
written as "(1) ... (2) ... (3) ... (4) ...". Layouts vary across years and
scans, so this is a best-effort regex extractor; genuinely messy items are left
for the agent to repair (it reads the page text and emits clean `RawItem`s).

`build_sample_paper` returns a small synthetic Science paper aligned to the
enriched Science 2023 outcomes, so the engine, tests, and app demo run end to end
before any real paper is uploaded.
"""
from __future__ import annotations

import re
from pathlib import Path

from .qmodel import Block, RawItem

_Q_SPLIT = re.compile(r"(?m)^\s*(\d{1,2})[\.\)]\s+")
_OPT = re.compile(r"\((\d)\)\s*(.+?)(?=\s*\(\d\)|\s*$)", re.S)


def parse_paper_text(text: str) -> list[RawItem]:
    """Heuristic parse of a paper's plain text into RawItems."""
    items: list[RawItem] = []
    parts = _Q_SPLIT.split(text)
    # parts = [pre, qnum, body, qnum, body, ...]
    for i in range(1, len(parts) - 1, 2):
        qnum = int(parts[i])
        body = parts[i + 1]
        opts = [(int(n), t.strip()) for n, t in _OPT.findall(body)]
        if len(opts) >= 4:
            opts = sorted(opts, key=lambda o: o[0])[:4]
            stem = body[: body.find("(1)")].strip() if "(1)" in body else body.strip()
            items.append(RawItem(qnum=qnum, stem=stem,
                                 options=[t for _, t in opts]))
    return items


def render_page_png(path: Path, pno: int, dpi: int = 150) -> bytes:
    """Render a 1-based page to PNG bytes (for full-page/image-only questions
    and the agent vision fallback)."""
    import fitz

    with fitz.open(path) as doc:
        page = doc[pno - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        return pix.tobytes("png")


def extract_page_tables(page) -> list[Block]:
    """Detect tables on a page and return them as table Blocks."""
    blocks: list[Block] = []
    try:
        tables = page.find_tables()
    except Exception:
        return blocks
    for t in getattr(tables, "tables", []):
        rows = [[(c or "").strip() for c in row] for row in t.extract()]
        rows = [r for r in rows if any(r)]
        if len(rows) >= 2:
            blocks.append(Block(type="table", header=rows[0], rows=rows[1:]))
    return blocks


def count_page_images(page) -> int:
    try:
        return len(page.get_images(full=True))
    except Exception:
        return 0


def parse_paper_pdf(path: Path, assets_dir: Path | None = None) -> list[RawItem]:
    """Page-aware parse. Extracts text MCQs, attaches detected tables, and flags
    image-heavy / full-page items for the agent vision pass (needs_vision).

    If ``assets_dir`` is given, embedded page images are saved there and added to
    each item's ``assets`` (relative paths the app/Supabase can serve)."""
    import fitz

    items: list[RawItem] = []
    with fitz.open(path) as doc:
        for pno, page in enumerate(doc, start=1):
            text = page.get_text()
            page_items = parse_paper_text(text)
            tables = extract_page_tables(page)
            n_images = count_page_images(page)

            saved_assets: list[str] = []
            if assets_dir and n_images:
                assets_dir.mkdir(parents=True, exist_ok=True)
                rel = f"{path.stem}-p{pno}.png"
                (assets_dir / rel).write_bytes(render_page_png(path, pno))
                saved_assets.append(rel)

            if page_items:
                for it in page_items:
                    # prepend text block, then any tables/images on the page
                    it.blocks = [Block(type="text", text=it.stem)] + tables
                    if saved_assets:
                        it.assets = saved_assets
                        it.blocks.append(Block(type="image", src=saved_assets[0],
                                               alt=f"figure on page {pno}"))
                    items.append(it)
            elif n_images or tables:
                # likely a full-page / image-only question: defer to the agent
                items.append(RawItem(
                    qnum=pno, stem="", blocks=tables, assets=saved_assets,
                    needs_vision=True,
                ))
    return items


def build_sample_paper() -> tuple[dict, list[RawItem]]:
    """Synthetic Science paper aligned to the enriched Science 2023 slice.

    Demonstrates the rich format: a hint (2nd-attempt scaffold) on every item and
    a table-based question (Q4) — all asset-light (no binary images)."""
    meta = {"code": "SAMPLE-SCI-2023", "subject": "Science",
            "version": "2023", "year": 2023}
    items = [
        RawItem(
            qnum=1,
            stem="Which statement about the three states of matter is correct?",
            options=[
                "A gas has no mass.",
                "A liquid takes the shape of its container but has a fixed volume.",
                "A solid changes its volume to fill its container.",
                "A liquid has its own fixed shape.",
            ],
            answer_index=1,
            hint="Think about which states keep a fixed shape and which keep a fixed volume.",
        ),
        RawItem(
            qnum=2,
            stem="A bar magnet is brought near several objects. Which statement is correct?",
            options=[
                "The magnet attracts all metals, including aluminium.",
                "A bigger magnet is always stronger than a smaller magnet.",
                "The magnet can exert a push or a pull on magnetic materials.",
                "Two north poles placed together will attract each other.",
            ],
            answer_index=2,
            hint="Recall which materials are magnetic and what like/unlike poles do.",
        ),
        RawItem(
            qnum=3,
            stem="In a circuit with a battery, wires and a bulb, the bulb does not light up. Which is the most likely reason?",
            options=[
                "The circuit is open at one point.",
                "Current is used up by the bulb so none returns to the battery.",
                "The bulb can only light in an open circuit.",
                "Plastic wires conduct the electricity away.",
            ],
            answer_index=0,
            hint="A bulb only lights when current can flow all the way round.",
        ),
        RawItem(
            qnum=4,
            stem="The table shows whether four objects are attracted to a magnet. "
                 "Which object is most likely made of a magnetic material?",
            blocks=[
                Block(type="text", text="The table shows whether four objects are "
                      "attracted to a magnet. Which object is most likely made of a "
                      "magnetic material?"),
                Block(type="table", header=["Object", "Attracted to magnet?"],
                      rows=[["W", "No"], ["X", "Yes"], ["Y", "No"], ["Z", "No"]]),
            ],
            options=["W", "X", "Y", "Z"],
            answer_index=1,
            hint="Only magnetic materials are attracted to a magnet.",
        ),
    ]
    return meta, items
