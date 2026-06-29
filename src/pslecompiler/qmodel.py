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

import json

from pydantic import BaseModel, Field

from .model import (
    ASSESSES, BELONGS_TO, EMBODIES, FROM_PAPER, HAS_OPTION, MISCONCEPTION,
    OPTION, PAPER, QUESTION, SYLLABUS_VERSION, TESTS, VARIANT_OF,
    CONCEPT, LEARNING_OUTCOME, KnowledgeGraph, make_uid,
)

OPTION_LABELS = ("1", "2", "3", "4")


# --- Rich content blocks -----------------------------------------------------
# PSLE MCQs routinely carry figures, tables, and full-page layouts. A question
# stem is an ordered list of blocks so any mix of text/image/table renders
# faithfully in the app and survives ingestion.
class Block(BaseModel):
    type: str                          # "text" | "image" | "table"
    text: str = ""                     # for type=text
    src: str = ""                      # for type=image (URL / path / data-URI)
    alt: str = ""                      # image alt / caption
    header: list[str] = Field(default_factory=list)   # for type=table
    rows: list[list[str]] = Field(default_factory=list)


# --- Raw ingest ---------------------------------------------------------------
class RawItem(BaseModel):
    """A raw MCQ pulled from a past paper before answer/feedback/tagging."""
    qnum: int
    stem: str = ""                     # plain-text stem (always keep for search)
    options: list[str] = Field(default_factory=list)
    answer_index: int | None = None    # 0-based, if the paper supplies a key
    # rich extras (default empty -> backward compatible)
    blocks: list[Block] = Field(default_factory=list)   # ordered stem content
    option_images: list[str] = Field(default_factory=list)  # per-option image src
    hint: str = ""                     # shown before a 2nd attempt
    assets: list[str] = Field(default_factory=list)     # extracted asset refs
    needs_vision: bool = False         # parser couldn't read it; agent must look


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
    # stem_blocks/assets are stored as JSON strings (Neo4j props must be scalars
    # or arrays of scalars, not nested objects).
    blocks = item.blocks or ([Block(type="text", text=item.stem)] if item.stem else [])
    kg.add_node(
        QUESTION, quid, stem=item.stem, qnum=item.qnum, subject=subject,
        syllabus_version=version, status="draft", provenance=provenance,
        stem_blocks=json.dumps([b.model_dump() for b in blocks], ensure_ascii=False),
        hint=item.hint, needs_vision=item.needs_vision,
        assets=item.assets or [],
    )
    kg.add_edge(quid, FROM_PAPER, paper_uid)
    kg.add_edge(quid, BELONGS_TO,
                make_uid(SYLLABUS_VERSION, subject, version))
    for i, text in enumerate(item.options):
        label = OPTION_LABELS[i] if i < len(OPTION_LABELS) else str(i + 1)
        ouid = make_uid(OPTION, quid, label)
        is_correct = (item.answer_index is not None and i == item.answer_index)
        img = item.option_images[i] if i < len(item.option_images) else ""
        kg.add_node(OPTION, ouid, label=label, text=text, is_correct=is_correct,
                    image=img)
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
