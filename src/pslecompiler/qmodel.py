"""Question-bank domain: schemas + graph builders.

The question layer sits on top of the syllabus backbone. A `Paper` yields
`Question`s, each with four `Option`s; questions are tagged into the syllabus
graph (`ASSESSES`/`TESTS`/`BELONGS_TO`) and their distractor options are linked
to the `Misconception`s they embody (`EMBODIES`) — the neurosymbolic join
between real exam items and the curriculum.

Agent-produced records (tagging, answer+feedback, variants) follow the same
"author JSONL -> validate -> merge" pattern as `extract/`.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .model import (
    ASSESSES, BELONGS_TO, EMBODIES, FROM_PAPER, HAS_OPTION, MISCONCEPTION,
    OPTION, PAPER, QUESTION, SYLLABUS_VERSION, TESTS, VARIANT_OF,
    CONCEPT, LEARNING_OUTCOME, KnowledgeGraph, make_uid,
)

OPTION_LABELS = ("1", "2", "3", "4")


# --- Raw ingest ---------------------------------------------------------------
class RawItem(BaseModel):
    """A raw MCQ pulled from a past paper before answer/feedback/tagging."""
    qnum: int
    stem: str
    options: list[str]
    answer_index: int | None = None   # 0-based, if the paper supplies a key


# --- Agent records ------------------------------------------------------------
class OptionFeedback(BaseModel):
    label: str                         # "1".."4"
    rationale: str                     # why correct / why wrong
    misconception: str = ""            # for distractors: the wrong belief it embodies


class AnswerFeedback(BaseModel):
    qid: str
    answer_label: str                  # the verified correct option label
    options: list[OptionFeedback] = Field(default_factory=list)
    cognitive_level: str = ""
    difficulty_band: str = ""


class Tagging(BaseModel):
    qid: str
    learning_outcomes: list[str] = Field(default_factory=list)  # LO uids
    concepts: list[str] = Field(default_factory=list)           # concept names
    theme: str = ""


class Variant(BaseModel):
    parent_qid: str
    stem: str
    options: list[str]
    answer_index: int                  # 0-based
    note: str = ""                     # what was changed


# --- Graph builders -----------------------------------------------------------
def add_paper(kg: KnowledgeGraph, *, code: str, subject: str, version: str,
              year: int | None = None, level: str = "Standard") -> str:
    return kg.add_node(
        PAPER, make_uid(PAPER, code),
        name=code, code=code, subject=subject, syllabus_version=version,
        year=year, level=level,
    )


def question_uid(subject: str, version: str, paper_code: str, qnum: int) -> str:
    return make_uid(QUESTION, subject, version, paper_code, str(qnum))


def add_question(kg: KnowledgeGraph, paper_uid: str, item: RawItem, *,
                 subject: str, version: str, paper_code: str,
                 provenance: str = "ingested") -> str:
    quid = question_uid(subject, version, paper_code, item.qnum)
    kg.add_node(
        QUESTION, quid, stem=item.stem, qnum=item.qnum, subject=subject,
        syllabus_version=version, status="draft", provenance=provenance,
    )
    kg.add_edge(quid, FROM_PAPER, paper_uid)
    kg.add_edge(quid, BELONGS_TO,
                make_uid(SYLLABUS_VERSION, subject, version))
    for i, text in enumerate(item.options):
        label = OPTION_LABELS[i] if i < len(OPTION_LABELS) else str(i + 1)
        ouid = make_uid(OPTION, quid, label)
        is_correct = (item.answer_index is not None and i == item.answer_index)
        kg.add_node(OPTION, ouid, label=label, text=text, is_correct=is_correct)
        kg.add_edge(quid, HAS_OPTION, ouid)
    return quid


def build_paper_questions(kg: KnowledgeGraph, *, code: str, subject: str,
                          version: str, items: list[RawItem],
                          year: int | None = None) -> list[str]:
    puid = add_paper(kg, code=code, subject=subject, version=version, year=year)
    return [
        add_question(kg, puid, it, subject=subject, version=version,
                     paper_code=code)
        for it in items
    ]
