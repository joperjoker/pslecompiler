"""Merge agent-authored question records into the graph.

apply_tagging          - link Question -> LearningOutcome / Concept (+ theme)
apply_answer_feedback  - set the key, per-option rationale, distractor->misconception
apply_variants         - create controlled variants linked to their parent
"""
from __future__ import annotations

import json
from pathlib import Path

from .model import (
    ASSESSES, CONCEPT, EMBODIES, HAS_OPTION, MISCONCEPTION, OPTION, QUESTION,
    TESTS, VARIANT_OF, KnowledgeGraph, make_uid,
)
from .qmodel import (
    AnswerFeedback, OPTION_LABELS, Tagging, Variant, add_question, RawItem,
)


def _read_jsonl(path: Path, model):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(model.model_validate_json(line))
    return out


def _subject_version(kg: KnowledgeGraph, quid: str) -> tuple[str, str]:
    q = kg.nodes[quid]
    return q.props.get("subject", ""), q.props.get("syllabus_version", "")


def apply_tagging(kg: KnowledgeGraph, records: list[Tagging]) -> dict:
    stats = {"tagged": 0, "assesses": 0, "tests": 0}
    for rec in records:
        if rec.qid not in kg.nodes:
            continue
        subject, version = _subject_version(kg, rec.qid)
        for lo_uid in rec.learning_outcomes:
            if lo_uid in kg.nodes:
                kg.add_edge(rec.qid, ASSESSES, lo_uid)
                stats["assesses"] += 1
        for name in rec.concepts:
            cuid = kg.add_node(CONCEPT, make_uid(CONCEPT, subject, version, name),
                               name=name, subject=subject, syllabus_version=version)
            kg.add_edge(rec.qid, TESTS, cuid)
            stats["tests"] += 1
        if rec.theme:
            kg.nodes[rec.qid].props["theme"] = rec.theme
        stats["tagged"] += 1
    return stats


def apply_answer_feedback(kg: KnowledgeGraph, records: list[AnswerFeedback]) -> dict:
    stats = {"answered": 0, "rationales": 0, "misconceptions": 0}
    for rec in records:
        q = kg.nodes.get(rec.qid)
        if q is None:
            continue
        subject, version = _subject_version(kg, rec.qid)
        opt_by_label = {}
        for e in kg.out_edges(rec.qid, HAS_OPTION):
            o = kg.nodes.get(e.dst)
            if o:
                opt_by_label[o.props.get("label")] = o
        for of in rec.options:
            o = opt_by_label.get(of.label)
            if not o:
                continue
            o.props["is_correct"] = (of.label == rec.answer_label)
            o.props["rationale"] = of.rationale
            stats["rationales"] += 1
            if of.misconception and of.label != rec.answer_label:
                muid = kg.add_node(
                    MISCONCEPTION,
                    make_uid(MISCONCEPTION, subject, version, of.misconception),
                    statement=of.misconception, subject=subject,
                    syllabus_version=version,
                )
                kg.add_edge(o.uid, EMBODIES, muid)
                stats["misconceptions"] += 1
        q.props["answer_label"] = rec.answer_label
        if rec.cognitive_level:
            q.props["cognitive_level"] = rec.cognitive_level
        if rec.difficulty_band:
            q.props["difficulty_band"] = rec.difficulty_band
        q.props["status"] = "answered"
        stats["answered"] += 1
    return stats


def apply_variants(kg: KnowledgeGraph, records: list[Variant]) -> dict:
    stats = {"variants": 0}
    for i, rec in enumerate(records, start=1):
        parent = kg.nodes.get(rec.parent_qid)
        if parent is None:
            continue
        subject = parent.props.get("subject", "")
        version = parent.props.get("syllabus_version", "")
        item = RawItem(qnum=900 + i, stem=rec.stem, options=rec.options,
                       answer_index=rec.answer_index)
        # reuse add_question with a synthetic paper code "variant"
        from .qmodel import add_paper
        puid = add_paper(kg, code=f"variant-{subject}-{version}", subject=subject,
                         version=version)
        quid = add_question(kg, puid, item, subject=subject, version=version,
                            paper_code=f"variant-{subject}-{version}",
                            provenance="variant")
        kg.add_edge(quid, VARIANT_OF, rec.parent_qid)
        # inherit the parent's syllabus tags
        for e in kg.out_edges(rec.parent_qid, ASSESSES):
            kg.add_edge(quid, ASSESSES, e.dst)
        for e in kg.out_edges(rec.parent_qid, TESTS):
            kg.add_edge(quid, TESTS, e.dst)
        kg.nodes[quid].props["status"] = "answered"
        kg.nodes[quid].props["note"] = rec.note
        stats["variants"] += 1
    return stats


# convenience JSONL loaders
def read_tagging(path: Path) -> list[Tagging]:
    return _read_jsonl(path, Tagging)


def read_answer_feedback(path: Path) -> list[AnswerFeedback]:
    return _read_jsonl(path, AnswerFeedback)


def read_variants(path: Path) -> list[Variant]:
    return _read_jsonl(path, Variant)
