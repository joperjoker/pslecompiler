"""QA validators for the question bank (the symbolic guardrails).

Each generated/ingested question must pass these before it is published. This is
the "challenger/judge" stage of the neurosymbolic loop: the neural layer
proposes answers/feedback/tags, and these hard checks accept or flag them.
"""
from __future__ import annotations

from .model import (
    ASSESSES, HAS_OPTION, EMBODIES, QUESTION, TESTS, KnowledgeGraph,
)

SEVERITY_ERROR = "error"
SEVERITY_WARN = "warn"


def validate_questions(kg: KnowledgeGraph, require_answer: bool = True) -> list[dict]:
    issues: list[dict] = []

    def add(qid, sev, msg):
        issues.append({"qid": qid, "severity": sev, "message": msg})

    for q in kg.nodes_with_label(QUESTION):
        opts = [kg.nodes[e.dst] for e in kg.out_edges(q.uid, HAS_OPTION)
                if e.dst in kg.nodes]
        if len(opts) != 4:
            add(q.uid, SEVERITY_ERROR, f"expected 4 options, found {len(opts)}")

        correct = [o for o in opts if o.props.get("is_correct")]
        if require_answer and len(correct) != 1:
            add(q.uid, SEVERITY_ERROR,
                f"must have exactly one correct option, found {len(correct)}")

        if require_answer:
            missing = [o.props.get("label") for o in opts
                       if not o.props.get("rationale")]
            if missing:
                add(q.uid, SEVERITY_WARN,
                    f"options without rationale: {missing}")

        tags = kg.out_edges(q.uid, ASSESSES) + kg.out_edges(q.uid, TESTS)
        if not tags:
            add(q.uid, SEVERITY_ERROR, "no syllabus tag (ASSESSES/TESTS)")

        # distractors should embody a misconception (quality signal)
        if require_answer:
            for o in opts:
                if not o.props.get("is_correct") and not kg.out_edges(o.uid, EMBODIES):
                    add(q.uid, SEVERITY_WARN,
                        f"distractor {o.props.get('label')} not linked to a misconception")
    return issues


def summarize(issues: list[dict]) -> dict:
    return {
        "errors": sum(1 for i in issues if i["severity"] == SEVERITY_ERROR),
        "warnings": sum(1 for i in issues if i["severity"] == SEVERITY_WARN),
        "total": len(issues),
    }
