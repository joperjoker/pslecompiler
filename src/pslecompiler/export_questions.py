"""Export the published question bank for serving.

Emits, under data/questions/<name>/:
  * questions.json - denormalised bank (questions + options + tags + feedback);
                     the Next.js app seeds / serves from this.
  * import.sql     - INSERT statements for Supabase (questions/options/tags).
  * manifest.json  - counts.

Keeping serving data separate from the Neo4j authoring graph means the app reads
Supabase only (no graph at runtime), per the architecture.
"""
from __future__ import annotations

import json
from pathlib import Path

from .model import (
    ASSESSES, EMBODIES, HAS_OPTION, QUESTION, TESTS, KnowledgeGraph,
)


def questions_to_records(kg: KnowledgeGraph, published_only: bool = False) -> list[dict]:
    records = []
    for q in kg.nodes_with_label(QUESTION):
        if published_only and q.props.get("status") not in ("answered", "published"):
            continue
        options = []
        for e in kg.out_edges(q.uid, HAS_OPTION):
            o = kg.nodes.get(e.dst)
            if not o:
                continue
            misc = [kg.nodes[me.dst].props.get("statement")
                    for me in kg.out_edges(o.uid, EMBODIES) if me.dst in kg.nodes]
            options.append({
                "label": o.props.get("label"),
                "text": o.props.get("text"),
                "is_correct": bool(o.props.get("is_correct")),
                "rationale": o.props.get("rationale", ""),
                "misconception": misc[0] if misc else None,
            })
        options.sort(key=lambda x: x["label"] or "")
        records.append({
            "qid": q.uid,
            "stem": q.props.get("stem"),
            "subject": q.props.get("subject"),
            "syllabus_version": q.props.get("syllabus_version"),
            "theme": q.props.get("theme"),
            "cognitive_level": q.props.get("cognitive_level"),
            "difficulty_band": q.props.get("difficulty_band"),
            "status": q.props.get("status"),
            "provenance": q.props.get("provenance"),
            "options": options,
            "learning_outcomes": [e.dst for e in kg.out_edges(q.uid, ASSESSES)],
            "concepts": [kg.nodes[e.dst].props.get("name")
                         for e in kg.out_edges(q.uid, TESTS) if e.dst in kg.nodes],
        })
    return records


def _sql_str(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    return "'" + str(v).replace("'", "''") + "'"


def emit_sql(records: list[dict]) -> str:
    lines = ["-- Generated question bank import for Supabase", "BEGIN;"]
    for r in records:
        lines.append(
            "INSERT INTO questions (qid, stem, subject, syllabus_version, theme, "
            "cognitive_level, difficulty_band, status, provenance) VALUES ("
            f"{_sql_str(r['qid'])}, {_sql_str(r['stem'])}, {_sql_str(r['subject'])}, "
            f"{_sql_str(r['syllabus_version'])}, {_sql_str(r['theme'])}, "
            f"{_sql_str(r['cognitive_level'])}, {_sql_str(r['difficulty_band'])}, "
            f"{_sql_str(r['status'])}, {_sql_str(r['provenance'])}) "
            "ON CONFLICT (qid) DO UPDATE SET stem=EXCLUDED.stem;"
        )
        for o in r["options"]:
            lines.append(
                "INSERT INTO options (qid, label, text, is_correct, rationale, misconception) VALUES ("
                f"{_sql_str(r['qid'])}, {_sql_str(o['label'])}, {_sql_str(o['text'])}, "
                f"{_sql_str(o['is_correct'])}, {_sql_str(o['rationale'])}, "
                f"{_sql_str(o['misconception'])}) "
                "ON CONFLICT (qid, label) DO UPDATE SET text=EXCLUDED.text, "
                "is_correct=EXCLUDED.is_correct, rationale=EXCLUDED.rationale;"
            )
        for c in r["concepts"]:
            lines.append(
                "INSERT INTO question_tags (qid, kind, value) VALUES ("
                f"{_sql_str(r['qid'])}, 'concept', {_sql_str(c)}) ON CONFLICT DO NOTHING;"
            )
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def write_question_bank(kg: KnowledgeGraph, out_dir: Path,
                        published_only: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = questions_to_records(kg, published_only=published_only)
    (out_dir / "questions.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "import.sql").write_text(emit_sql(records), encoding="utf-8")
    manifest = {"question_count": len(records),
                "option_count": sum(len(r["options"]) for r in records)}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
