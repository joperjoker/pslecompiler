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

from .qmodel import RawItem

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


def parse_paper_pdf(path: Path) -> list[RawItem]:
    import fitz

    text_parts = []
    with fitz.open(path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return parse_paper_text("\n".join(text_parts))


def build_sample_paper() -> tuple[dict, list[RawItem]]:
    """Synthetic Science paper aligned to the enriched Science 2023 slice."""
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
        ),
    ]
    return meta, items
