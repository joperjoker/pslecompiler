"""Build the structured spine (hierarchy nodes) from parsed Sections.

Deterministic, no LLM. Subject/version-specific mappers are registered by name
(``SourceDoc.mapper``). Each mapper returns a KnowledgeGraph containing:
  Subject -> SyllabusVersion -> Theme/Strand -> Topic -> LearningOutcome

LearningOutcome nodes are the MCQ-ready atoms; the LLM extraction pass
(``extract/``) later attaches Concept/Misconception/Distractor nodes to them.
"""
from __future__ import annotations

import re
from typing import Callable

from .model import (
    FOR_SUBJECT, PART_OF, LEARNING_OUTCOME, SUBJECT, SYLLABUS_VERSION, THEME,
    TOPIC, KnowledgeGraph, make_uid,
)
from .parse_pdf import Section
from .sources import SourceDoc

# Primary level detection, e.g. "P3", "Primary 5", "(P6)"
_LEVEL_RE = re.compile(r"\b[Pp](?:rimary)?\s*([3-6])\b")
# Science 2023 themes (also accept Strand for other subjects).
SCIENCE_THEMES = {"diversity", "cycles", "systems", "energy", "interactions"}


def _detect_level(*texts: str) -> str | None:
    for t in texts:
        m = _LEVEL_RE.search(t or "")
        if m:
            return f"P{m.group(1)}"
    return None


def _split_outcomes(text: str) -> list[str]:
    """Split a body blob into individual learning-outcome statements."""
    out: list[str] = []
    for raw in re.split(r"[\n\r]+", text):
        line = raw.strip()
        # strip common bullet / numbering prefixes
        line = re.sub(r"^[•\-\*•·]\s*", "", line)
        line = re.sub(r"^\(?[a-zA-Z0-9]{1,3}[\.\)]\s+", "", line)
        if len(line) >= 12:  # ignore stray fragments
            out.append(line)
    return out


def _add_spine_roots(kg: KnowledgeGraph, src: SourceDoc) -> tuple[str, str]:
    subj_uid = kg.add_node(SUBJECT, make_uid(SUBJECT, src.subject), name=src.subject)
    ver_uid = kg.add_node(
        SYLLABUS_VERSION,
        make_uid(SYLLABUS_VERSION, src.subject, src.version),
        name=f"{src.subject} {src.version}",
        subject=src.subject,
        version=src.version,
        effective_year=src.effective_year,
        level=src.level,
        title=src.title,
        source_url=src.url,
    )
    kg.add_edge(ver_uid, FOR_SUBJECT, subj_uid)
    return subj_uid, ver_uid


def _add_outcome(kg: KnowledgeGraph, topic_uid: str, src: SourceDoc,
                 text: str, level: str | None, page: int, idx: int) -> str:
    lo_uid = kg.add_node(
        LEARNING_OUTCOME,
        make_uid(LEARNING_OUTCOME, src.subject, src.version, text),
        text=text,
        subject=src.subject,
        syllabus_version=src.version,
        effective_year=src.effective_year,
        level=src.level,
        primary_level=level,
        source_citation=f"{src.filename} p.{page}",
        # cognitive_level / difficulty_band filled by the extraction pass
        order=idx,
    )
    kg.add_edge(lo_uid, PART_OF, topic_uid)
    return lo_uid


def map_generic(sections: list[Section], src: SourceDoc) -> KnowledgeGraph:
    """Heading-driven mapper: level-1/2 headings -> Theme, deeper -> Topic,
    body text -> LearningOutcomes. Works for any subject as a baseline."""
    kg = KnowledgeGraph()
    _, ver_uid = _add_spine_roots(kg, src)

    cur_theme = None
    cur_topic = None
    cur_topic_level = None
    n_lo = 0
    for sec in sections:
        if sec.title and sec.level <= 2:
            cur_theme = kg.add_node(
                THEME, make_uid(THEME, src.subject, src.version, sec.title),
                name=sec.title, subject=src.subject, syllabus_version=src.version,
            )
            kg.add_edge(cur_theme, PART_OF, ver_uid)
            cur_topic = None
            cur_topic_level = None
        elif sec.title and sec.level <= 4:
            parent = cur_theme or ver_uid
            cur_topic_level = _detect_level(sec.title)
            cur_topic = kg.add_node(
                TOPIC, make_uid(TOPIC, src.subject, src.version, sec.title),
                name=sec.title, subject=src.subject, syllabus_version=src.version,
                primary_level=cur_topic_level,
            )
            kg.add_edge(cur_topic, PART_OF, parent)
        if sec.text:
            topic = cur_topic or cur_theme
            if topic is None:  # no heading seen yet; skip preamble
                continue
            lvl = _detect_level(sec.title, sec.text) or cur_topic_level
            for stmt in _split_outcomes(sec.text):
                n_lo += 1
                _add_outcome(kg, topic, src, stmt, lvl, sec.page, n_lo)
    return kg


def map_science_2023(sections: list[Section], src: SourceDoc) -> KnowledgeGraph:
    """Science-specific mapper: recognises the five themes explicitly and tags
    primary level (P3-P6) on topics/outcomes."""
    kg = KnowledgeGraph()
    _, ver_uid = _add_spine_roots(kg, src)

    cur_theme = None
    cur_topic = None
    cur_topic_level = None
    n_lo = 0
    for sec in sections:
        title_l = (sec.title or "").strip().lower()
        is_theme = any(t in title_l for t in SCIENCE_THEMES) and len(title_l) < 40
        if sec.title and (is_theme or sec.level == 1):
            cur_theme = kg.add_node(
                THEME, make_uid(THEME, src.subject, src.version, sec.title),
                name=sec.title, subject=src.subject, syllabus_version=src.version,
                kind="theme",
            )
            kg.add_edge(cur_theme, PART_OF, ver_uid)
            cur_topic = None
            cur_topic_level = None
        elif sec.title and sec.level <= 4 and cur_theme:
            cur_topic_level = _detect_level(sec.title)
            cur_topic = kg.add_node(
                TOPIC, make_uid(TOPIC, src.subject, src.version, sec.title),
                name=sec.title, subject=src.subject, syllabus_version=src.version,
                primary_level=cur_topic_level,
            )
            kg.add_edge(cur_topic, PART_OF, cur_theme)
        if sec.text and (cur_topic or cur_theme):
            topic = cur_topic or cur_theme
            lvl = _detect_level(sec.title, sec.text) or cur_topic_level
            for stmt in _split_outcomes(sec.text):
                n_lo += 1
                _add_outcome(kg, topic, src, stmt, lvl, sec.page, n_lo)
    return kg


MAPPERS: dict[str, Callable[[list[Section], SourceDoc], KnowledgeGraph]] = {
    "generic": map_generic,
    "science_2023": map_science_2023,
}


def build_spine(sections: list[Section], src: SourceDoc) -> KnowledgeGraph:
    mapper = MAPPERS.get(src.mapper, map_generic)
    return mapper(sections, src)
