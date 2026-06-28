"""LLM-extraction layer.

The *semantic* enrichment (concepts, prerequisites, misconceptions ->
distractors, cognitive level, difficulty) is produced by Claude Code itself
(this agent + Task subagents) under the user's subscription — there is no
external API key in the pipeline. The flow is:

  1. ``write_todo`` lists each LearningOutcome that needs extraction.
  2. The agent reads the todo + ``prompts/extract_lo.md`` and writes one
     ``Extraction`` JSON object per LO into an extractions JSONL file.
  3. ``apply_extractions`` merges those records into the graph (creating the
     Concept / Misconception / Distractor subgraph — the GraphRAG layer).

Keeping extraction as data (JSONL) makes it reproducible, reviewable, and
decoupled from whichever model produced it.
"""
from __future__ import annotations

import json
from pathlib import Path

from .schema import Extraction
from ..model import (
    ABOUT, COMMONLY_CONFUSED_WITH, CONCEPT, COVERS, DERIVED_FROM, DISTRACTOR,
    LEARNING_OUTCOME, MISCONCEPTION, PREREQUISITE_OF, RELATED_TO, TERM,
    KnowledgeGraph, make_uid,
)


def write_todo(kg: KnowledgeGraph, out_path: Path) -> int:
    """Write the list of LearningOutcomes awaiting extraction."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for lo in kg.nodes_with_label(LEARNING_OUTCOME):
        rows.append(json.dumps({
            "lo_uid": lo.uid,
            "subject": lo.props.get("subject"),
            "syllabus_version": lo.props.get("syllabus_version"),
            "primary_level": lo.props.get("primary_level"),
            "text": lo.props.get("text"),
        }, ensure_ascii=False))
    out_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    return len(rows)


def read_extractions(path: Path) -> list[Extraction]:
    records: list[Extraction] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(Extraction.model_validate_json(line))
    return records


def _concept_uid(subject: str, version: str, name: str) -> str:
    return make_uid(CONCEPT, subject, version, name)


def apply_extractions(kg: KnowledgeGraph, records: list[Extraction]) -> dict:
    """Merge extraction records into the graph in place. Returns counts."""
    stats = {"concepts": 0, "misconceptions": 0, "distractors": 0, "applied": 0}
    for rec in records:
        lo = kg.nodes.get(rec.lo_uid)
        if lo is None:
            continue
        subject = lo.props.get("subject", "")
        version = lo.props.get("syllabus_version", "")

        # cognitive level + difficulty land on the LO atom
        if rec.cognitive_level:
            lo.props["cognitive_level"] = rec.cognitive_level
        if rec.difficulty_band:
            lo.props["difficulty_band"] = rec.difficulty_band

        def cuid(name: str) -> str:
            return _concept_uid(subject, version, name)

        for name in rec.concepts:
            uid = kg.add_node(CONCEPT, cuid(name), name=name, subject=subject,
                              syllabus_version=version)
            kg.add_edge(rec.lo_uid, COVERS, uid)
            stats["concepts"] += 1

        for name in rec.key_terms:
            uid = kg.add_node(TERM, make_uid(TERM, subject, version, name),
                              name=name, subject=subject)
            kg.add_edge(rec.lo_uid, COVERS, uid)

        for name in rec.prerequisites:
            pre = kg.add_node(CONCEPT, cuid(name), name=name, subject=subject,
                              syllabus_version=version)
            for c in rec.concepts:
                kg.add_edge(pre, PREREQUISITE_OF, cuid(c))

        for name in rec.related:
            r = kg.add_node(CONCEPT, cuid(name), name=name, subject=subject,
                            syllabus_version=version)
            for c in rec.concepts:
                if cuid(c) != r:
                    kg.add_edge(cuid(c), RELATED_TO, r)

        for a, b in rec.commonly_confused_with:
            ua = kg.add_node(CONCEPT, cuid(a), name=a, subject=subject,
                             syllabus_version=version)
            ub = kg.add_node(CONCEPT, cuid(b), name=b, subject=subject,
                             syllabus_version=version)
            kg.add_edge(ua, COMMONLY_CONFUSED_WITH, ub)
            kg.add_edge(ub, COMMONLY_CONFUSED_WITH, ua)

        for m in rec.misconceptions:
            about = cuid(m.about_concept) if m.about_concept else None
            if about:
                kg.add_node(CONCEPT, about, name=m.about_concept, subject=subject,
                            syllabus_version=version)
            muid = kg.add_node(
                MISCONCEPTION,
                make_uid(MISCONCEPTION, subject, version, m.statement),
                statement=m.statement, subject=subject, syllabus_version=version,
            )
            if about:
                kg.add_edge(muid, ABOUT, about)
            stats["misconceptions"] += 1
            if m.distractor:
                duid = kg.add_node(
                    DISTRACTOR,
                    make_uid(DISTRACTOR, subject, version, m.distractor),
                    text=m.distractor, subject=subject, syllabus_version=version,
                )
                kg.add_edge(duid, DERIVED_FROM, muid)
                stats["distractors"] += 1
        stats["applied"] += 1
    return stats
