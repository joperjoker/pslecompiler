"""Table-aware structural parser for the Primary Science Syllabus 2023.

Section 5 of the official PDF ("SYLLABUS LEARNING OUTCOMES", pp. 36-80) lays out
learning outcomes in four-column tables:

    Learning Outcomes | Core Ideas | Practices | Values, Ethics and Attitudes

Reverse-engineered facts about the real PDF that drive this parser:
  * Each theme is introduced by an "About <Theme>:" page (no outcomes there).
  * Each topic table title is a **bold** line containing a level marker
    "(P3)".."(P6)"; it is centred, so its x-position varies, and it repeats at
    the top of every page the table spans.
  * The Learning Outcomes column is the leftmost (content x0 < ~200). Other
    columns drift left/right per page (a Core/Practices bullet can sit at x~311),
    so we bound the LO column tightly and treat the rest as topic-level context.

We emit Theme -> Topic -> LearningOutcome (the MCQ atoms) and stash Core Ideas /
Practices as topic context for later use in distractor / wiki synthesis.
"""
from __future__ import annotations

import re
from pathlib import Path

from .model import (
    FOR_SUBJECT, PART_OF, LEARNING_OUTCOME, SUBJECT, SYLLABUS_VERSION, THEME,
    TOPIC, KnowledgeGraph, make_uid,
)
from .sources import SourceDoc

LO_RIGHT = 200.0       # right edge of the Learning Outcomes column
CORE_RIGHT = 405.0
PRACTICE_RIGHT = 560.0

LO_SECTION_START_PAGE = 38
LO_SECTION_END_PAGE = 80

THEMES = {"diversity", "cycles", "systems", "energy", "interactions"}
_ABOUT_RE = re.compile(r"About\s+([A-Z][a-z]+)\s*:")
_LEVEL_RE = re.compile(r"\(P[3-6]")
_BULLET = "•"
_COL_HEADERS = {
    "learning outcomes", "core ideas", "practices",
    "values, ethics and attitudes",
}
_SKIP_EXACT = {"official (open)"}


def _bold_lines(page):
    """Yield (x0, y0, text, bold) for non-empty lines, sorted top-to-bottom."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            spans = l["spans"]
            if not spans:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            bold = any(s.get("flags", 0) & 16 for s in spans)
            out.append((round(l["bbox"][0], 1), round(l["bbox"][1], 1), text, bold))
    out.sort(key=lambda r: (r[1], r[0]))
    return out


def _is_noise(text: str) -> bool:
    t = text.strip().lower()
    return (
        t in _SKIP_EXACT or t in _COL_HEADERS or t.isdigit()
        or t.startswith("about ") or t.startswith("essential takeaway")
        or t.startswith("key inquiry")
    )


def parse_science_2023(pdf_path: Path, src: SourceDoc) -> KnowledgeGraph:
    import fitz

    kg = KnowledgeGraph()
    subj_uid = kg.add_node(SUBJECT, make_uid(SUBJECT, src.subject), name=src.subject)
    ver_uid = kg.add_node(
        SYLLABUS_VERSION, make_uid(SYLLABUS_VERSION, src.subject, src.version),
        name=f"{src.subject} {src.version}", subject=src.subject, version=src.version,
        effective_year=src.effective_year, level=src.level, title=src.title,
        source_url=src.url,
    )
    kg.add_edge(ver_uid, FOR_SUBJECT, subj_uid)

    state = {
        "theme_uid": None, "theme_name": None,
        "topic_uid": None, "page": 0,
        "lo_buf": [], "core_buf": [], "practice_buf": [], "n_lo": 0,
    }

    def flush_lo():
        text = " ".join(state["lo_buf"]).strip()
        state["lo_buf"] = []
        if not state["topic_uid"] or len(text) < 8:
            return
        state["n_lo"] += 1
        lo_uid = kg.add_node(
            LEARNING_OUTCOME,
            make_uid(LEARNING_OUTCOME, src.subject, src.version, text),
            text=text, subject=src.subject, syllabus_version=src.version,
            effective_year=src.effective_year, level=src.level,
            primary_level=state["topic_level"], theme=state["theme_name"],
            source_citation=f"{src.filename} p.{state['page']}", order=state["n_lo"],
        )
        kg.add_edge(lo_uid, PART_OF, state["topic_uid"])

    def finalize_topic():
        flush_lo()
        tu = state["topic_uid"]
        if tu:
            if state["core_buf"]:
                kg.nodes[tu].props["core_ideas"] = list(dict.fromkeys(state["core_buf"]))
            if state["practice_buf"]:
                kg.nodes[tu].props["practices"] = list(dict.fromkeys(state["practice_buf"]))
        state["core_buf"], state["practice_buf"] = [], []

    state["topic_level"] = None

    with fitz.open(pdf_path) as doc:
        end = min(LO_SECTION_END_PAGE, doc.page_count)
        for pno in range(LO_SECTION_START_PAGE, end + 1):
            page = doc[pno - 1]
            state["page"] = pno

            about = _ABOUT_RE.search(page.get_text())
            if about and about.group(1).lower() in THEMES:
                finalize_topic()
                state["topic_uid"] = None
                state["topic_level"] = None
                tname = about.group(1)
                state["theme_uid"] = kg.add_node(
                    THEME, make_uid(THEME, src.subject, src.version, tname),
                    name=tname, subject=src.subject, syllabus_version=src.version,
                    kind="theme",
                )
                state["theme_name"] = tname
                kg.add_edge(state["theme_uid"], PART_OF, ver_uid)
                continue

            for x0, _y0, text, bold in _bold_lines(page):
                # Topic title: bold, carries a level marker, not a column header.
                if bold and _LEVEL_RE.search(text) and text.lower() not in _COL_HEADERS:
                    title = text.strip()
                    new_uid = make_uid(TOPIC, src.subject, src.version, title)
                    if new_uid != state["topic_uid"]:
                        finalize_topic()
                        levels = re.findall(r"P([3-6])", title)
                        state["topic_level"] = "P" + levels[0] if levels else None
                        track = ("Foundation" if "Foundation" in title
                                 else "Standard" if "Standard" in title else None)
                        state["topic_uid"] = kg.add_node(
                            TOPIC, new_uid, name=title, subject=src.subject,
                            syllabus_version=src.version,
                            primary_level=state["topic_level"], track=track,
                        )
                        kg.add_edge(state["topic_uid"], PART_OF,
                                    state["theme_uid"] or ver_uid)
                    continue

                if _is_noise(text):
                    continue

                if x0 < LO_RIGHT:                       # Learning Outcomes column
                    if x0 < 95 and text.strip() == _BULLET:
                        flush_lo()
                        state["lo_buf"] = [""]          # open a new outcome
                    elif text.startswith(_BULLET):
                        flush_lo()
                        state["lo_buf"].append(text.lstrip(_BULLET).strip())
                    elif text.startswith("Note:"):
                        flush_lo()
                    elif state["lo_buf"]:
                        state["lo_buf"].append(text)
                elif x0 < CORE_RIGHT:                    # Core Ideas (context)
                    if text not in (_BULLET, "-"):
                        state["core_buf"].append(text.lstrip("•- ").strip())
                elif x0 < PRACTICE_RIGHT:                # Practices (context)
                    if text not in (_BULLET, "-"):
                        state["practice_buf"].append(text.lstrip("•- ").strip())
                # Values column ignored for the spine.

    finalize_topic()
    return kg
