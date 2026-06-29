"""Neurosymbolic tagging: symbolic candidate generation for a question.

Given a question stem, propose the most relevant LearningOutcomes (and their
concepts) from the syllabus graph. This is the *symbolic* half — it narrows the
search space using the same scoring as the retrieval engine. The agent (neural
half) then confirms the best tag(s) and writes a `Tagging` record, which
`qpipeline.apply_tagging` merges.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import COVERS, CONCEPT, LEARNING_OUTCOME, KnowledgeGraph
from .retrieve import _cosine, _keyword_score


@dataclass
class TagCandidate:
    lo_uid: str
    lo_text: str
    score: float
    concepts: list[str]


def suggest_tags(kg: KnowledgeGraph, quid: str, k: int = 5,
                 query_embedding: list[float] | None = None) -> list[TagCandidate]:
    q = kg.nodes.get(quid)
    if q is None:
        return []
    subject = q.props.get("subject")
    version = q.props.get("syllabus_version")
    stem = q.props.get("stem", "")

    scored: list[TagCandidate] = []
    for lo in kg.nodes_with_label(LEARNING_OUTCOME):
        if subject and lo.props.get("subject") != subject:
            continue
        if version and lo.props.get("syllabus_version") != version:
            continue
        if query_embedding and lo.props.get("embedding"):
            s = _cosine(query_embedding, lo.props["embedding"])
        else:
            s = _keyword_score(stem, lo.props.get("text", ""))
        if s <= 0:
            continue
        concepts = [
            kg.nodes[e.dst].props.get("name", "")
            for e in kg.out_edges(lo.uid, COVERS)
            if kg.nodes.get(e.dst) and kg.nodes[e.dst].label == CONCEPT
        ]
        scored.append(TagCandidate(lo.uid, lo.props.get("text", ""),
                                   round(s, 4), concepts))
    scored.sort(key=lambda c: -c.score)
    return scored[:k]
