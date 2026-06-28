"""Retrieval & matching algorithm for setting MCQ items.

Given a QuestionSpec, assemble grounded "question-spec bundles": the target
learning outcome, its focus concepts, prerequisite scaffolding, and — crucially
for MCQs — *grounded distractors* mined from misconceptions and commonly-confused
concepts. This runs directly on the in-memory KnowledgeGraph (the local backend),
so it is fully testable without Neo4j. The Cypher equivalents for an AuraDB
backend are documented in docs/retrieval-algorithm.md.

Pipeline:
  1. Structured filter  - subject/version/level/theme/cognitive/difficulty.
  2. Semantic rank      - cosine over embeddings if a query + vectors exist,
                          else a keyword overlap score (graceful fallback).
  3. Graph expansion    - concepts, prerequisites, confused-with, misconceptions
                          -> distractors.
  4. Assemble + dedup   - build bundles; drop near-duplicate outcomes.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from .model import (
    ABOUT, COMMONLY_CONFUSED_WITH, COVERS, CONCEPT, DERIVED_FROM, DISTRACTOR,
    LEARNING_OUTCOME, MISCONCEPTION, PART_OF, PREREQUISITE_OF, THEME, TOPIC,
    KnowledgeGraph, Node,
)


@dataclass
class QuestionSpec:
    subject: str
    syllabus_version: str | None = None
    theme: str | None = None            # theme/topic name substring
    primary_level: str | None = None    # "P3".."P6"
    cognitive_level: str | None = None  # config.COGNITIVE_LEVELS
    difficulty_band: str | None = None  # config.DIFFICULTY_BANDS
    query: str | None = None            # free-text focus (semantic/keyword)
    count: int = 5


@dataclass
class QuestionSpecBundle:
    lo_uid: str
    lo_text: str
    subject: str
    syllabus_version: str
    primary_level: str | None
    cognitive_level: str | None
    difficulty_band: str | None
    focus_concepts: list[str] = field(default_factory=list)
    prerequisite_concepts: list[str] = field(default_factory=list)
    distractor_options: list[str] = field(default_factory=list)
    community_context: list[str] = field(default_factory=list)
    source_citation: str = ""
    score: float = 0.0


_WORD_RE = re.compile(r"[\w一-鿿]+")


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text or "") if len(w) > 1}


def _keyword_score(query: str, text: str) -> float:
    q, t = _tokens(query), _tokens(text)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# --- Step 1: structured filter ----------------------------------------------
def _ancestor_theme_names(kg: KnowledgeGraph, lo_uid: str) -> list[str]:
    names: list[str] = []
    seen = {lo_uid}
    frontier = [lo_uid]
    while frontier:
        cur = frontier.pop()
        for e in kg.out_edges(cur, PART_OF):
            parent = kg.nodes.get(e.dst)
            if parent and parent.uid not in seen:
                seen.add(parent.uid)
                if parent.label in (TOPIC, THEME):
                    names.append(parent.props.get("name", ""))
                    frontier.append(parent.uid)
    return names


def filter_outcomes(kg: KnowledgeGraph, spec: QuestionSpec) -> list[Node]:
    out: list[Node] = []
    for lo in kg.nodes_with_label(LEARNING_OUTCOME):
        p = lo.props
        if spec.subject and p.get("subject") != spec.subject:
            continue
        if spec.syllabus_version and p.get("syllabus_version") != spec.syllabus_version:
            continue
        if spec.primary_level and p.get("primary_level") not in (spec.primary_level, None):
            continue
        if spec.cognitive_level and p.get("cognitive_level") != spec.cognitive_level:
            continue
        if spec.difficulty_band and p.get("difficulty_band") != spec.difficulty_band:
            continue
        if spec.theme:
            ancestors = " ".join(_ancestor_theme_names(kg, lo.uid)).lower()
            if spec.theme.lower() not in ancestors:
                continue
        out.append(lo)
    return out


# --- Step 3: graph expansion ------------------------------------------------
def expand_outcome(kg: KnowledgeGraph, lo_uid: str) -> dict:
    focus, prereq, distractors, communities = [], [], [], []

    concept_uids = []
    for e in kg.out_edges(lo_uid, COVERS):
        c = kg.nodes.get(e.dst)
        if c and c.label == CONCEPT:
            concept_uids.append(c.uid)
            focus.append(c.props.get("name", ""))

    for cuid in concept_uids:
        # prerequisites: things that are PREREQUISITE_OF this concept
        for e in kg.in_edges(cuid, PREREQUISITE_OF):
            pre = kg.nodes.get(e.src)
            if pre:
                prereq.append(pre.props.get("name", ""))
        # commonly-confused concepts -> distractor candidates
        for e in kg.out_edges(cuid, COMMONLY_CONFUSED_WITH):
            other = kg.nodes.get(e.dst)
            if other:
                distractors.append(other.props.get("name", ""))
        # misconceptions about this concept -> their distractors
        for e in kg.in_edges(cuid, ABOUT):
            misc = kg.nodes.get(e.src)
            if misc and misc.label == MISCONCEPTION:
                for de in kg.in_edges(misc.uid, DERIVED_FROM):
                    d = kg.nodes.get(de.src)
                    if d and d.label == DISTRACTOR:
                        distractors.append(d.props.get("text", ""))
        # community context
        for e in kg.in_edges(cuid, "CONTAINS"):
            comm = kg.nodes.get(e.src)
            if comm and comm.props.get("summary"):
                communities.append(comm.props["summary"])

    dedupe = lambda xs: list(dict.fromkeys(x for x in xs if x))  # noqa: E731
    return {
        "focus": dedupe(focus),
        "prereq": dedupe(prereq),
        "distractors": dedupe(distractors),
        "communities": dedupe(communities),
    }


# --- Step 2 + 4: rank, assemble, dedup --------------------------------------
def retrieve(kg: KnowledgeGraph, spec: QuestionSpec,
             query_embedding: list[float] | None = None) -> list[QuestionSpecBundle]:
    candidates = filter_outcomes(kg, spec)

    # rank
    scored: list[tuple[float, Node]] = []
    for lo in candidates:
        if query_embedding and lo.props.get("embedding"):
            s = _cosine(query_embedding, lo.props["embedding"])
        elif spec.query:
            s = _keyword_score(spec.query, lo.props.get("text", ""))
        else:
            s = 1.0
        scored.append((s, lo))
    scored.sort(key=lambda x: (-x[0], x[1].props.get("order", 0)))

    bundles: list[QuestionSpecBundle] = []
    seen_tokens: list[set[str]] = []
    for score, lo in scored:
        toks = _tokens(lo.props.get("text", ""))
        # dedup: skip if >0.85 token overlap with an already-chosen outcome
        if any(toks and len(toks & s) / len(toks) > 0.85 for s in seen_tokens):
            continue
        exp = expand_outcome(kg, lo.uid)
        bundles.append(QuestionSpecBundle(
            lo_uid=lo.uid,
            lo_text=lo.props.get("text", ""),
            subject=lo.props.get("subject", ""),
            syllabus_version=lo.props.get("syllabus_version", ""),
            primary_level=lo.props.get("primary_level"),
            cognitive_level=lo.props.get("cognitive_level"),
            difficulty_band=lo.props.get("difficulty_band"),
            focus_concepts=exp["focus"],
            prerequisite_concepts=exp["prereq"],
            distractor_options=exp["distractors"],
            community_context=exp["communities"],
            source_citation=lo.props.get("source_citation", ""),
            score=round(score, 4),
        ))
        seen_tokens.append(toks)
        if len(bundles) >= spec.count:
            break
    return bundles
