"""Graph data model: nodes, edges, and the KnowledgeGraph container.

This is backend-agnostic. The same graph can be:
  * serialized to JSONL + a Cypher load script (portable artifacts), and
  * loaded into an in-memory NetworkX graph for querying/testing, and
  * (optionally) pushed live to Neo4j via the HTTP Query API.

Node labels and relationship types mirror schema/constraints.cypher.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, Field

# --- Node labels -------------------------------------------------------------
SUBJECT = "Subject"
SYLLABUS_VERSION = "SyllabusVersion"
THEME = "Theme"              # also used for Math "Strand"
TOPIC = "Topic"
SUBTOPIC = "SubTopic"
LEARNING_OUTCOME = "LearningOutcome"   # the MCQ-ready atom
CONCEPT = "Concept"
TERM = "Term"
SKILL = "Skill"
MISCONCEPTION = "Misconception"
DISTRACTOR = "Distractor"
WIKI_ARTICLE = "WikiArticle"
COMMUNITY = "Community"

# --- Relationship types ------------------------------------------------------
FOR_SUBJECT = "FOR_SUBJECT"
PART_OF = "PART_OF"
COVERS = "COVERS"
PREREQUISITE_OF = "PREREQUISITE_OF"
RELATED_TO = "RELATED_TO"
COMMONLY_CONFUSED_WITH = "COMMONLY_CONFUSED_WITH"
ABOUT = "ABOUT"
DERIVED_FROM = "DERIVED_FROM"
SYNTHESIZES = "SYNTHESIZES"
CITES = "CITES"
CONTAINS = "CONTAINS"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w一-鿿]+", "-", text)  # keep CJK chars
    return text.strip("-")[:80] or "x"


def make_uid(label: str, *parts: str) -> str:
    """Stable, human-readable-ish uid; hash guards against collisions/length."""
    base = "/".join(p for p in parts if p)
    h = hashlib.sha1(f"{label}|{base}".encode("utf-8")).hexdigest()[:10]
    return f"{label.lower()}:{slugify(base)}:{h}"


class Node(BaseModel):
    uid: str
    label: str
    props: dict[str, Any] = Field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.props.get("name") or self.props.get("text") or self.uid


class Edge(BaseModel):
    src: str           # source uid
    rel: str           # relationship type
    dst: str           # destination uid
    props: dict[str, Any] = Field(default_factory=dict)

    def key(self) -> tuple[str, str, str]:
        return (self.src, self.rel, self.dst)


class KnowledgeGraph(BaseModel):
    """In-memory collection of nodes + edges with de-duplication on uid/key."""

    nodes: dict[str, Node] = Field(default_factory=dict)
    edges: dict[tuple, Edge] = Field(default_factory=dict)

    # -- mutation -------------------------------------------------------------
    def add_node(self, label: str, uid: str, **props: Any) -> str:
        if uid in self.nodes:
            # merge props (later writes win for non-empty values)
            existing = self.nodes[uid].props
            for k, v in props.items():
                if v is not None and v != "":
                    existing[k] = v
        else:
            self.nodes[uid] = Node(uid=uid, label=label, props=dict(props))
        return uid

    def add_edge(self, src: str, rel: str, dst: str, **props: Any) -> None:
        e = Edge(src=src, rel=rel, dst=dst, props=dict(props))
        self.edges[e.key()] = e

    def merge(self, other: "KnowledgeGraph") -> None:
        for n in other.nodes.values():
            self.add_node(n.label, n.uid, **n.props)
        for e in other.edges.values():
            self.edges[e.key()] = e

    # -- queries --------------------------------------------------------------
    def nodes_with_label(self, label: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.label == label]

    def out_edges(self, uid: str, rel: str | None = None) -> list[Edge]:
        return [
            e for e in self.edges.values()
            if e.src == uid and (rel is None or e.rel == rel)
        ]

    def in_edges(self, uid: str, rel: str | None = None) -> list[Edge]:
        return [
            e for e in self.edges.values()
            if e.dst == uid and (rel is None or e.rel == rel)
        ]

    # -- stats ----------------------------------------------------------------
    def label_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for n in self.nodes.values():
            counts[n.label] = counts.get(n.label, 0) + 1
        return counts

    def rel_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self.edges.values():
            counts[e.rel] = counts.get(e.rel, 0) + 1
        return counts


# --- Serialization helpers used by graph_artifacts ---------------------------
def nodes_to_jsonl(kg: KnowledgeGraph) -> Iterable[str]:
    for n in kg.nodes.values():
        yield json.dumps(
            {"uid": n.uid, "label": n.label, **n.props}, ensure_ascii=False
        )


def edges_to_jsonl(kg: KnowledgeGraph) -> Iterable[str]:
    for e in kg.edges.values():
        rec = {"src": e.src, "rel": e.rel, "dst": e.dst}
        if e.props:
            rec["props"] = e.props
        yield json.dumps(rec, ensure_ascii=False)


def load_jsonl_graph(nodes_path: Path, edges_path: Path) -> KnowledgeGraph:
    kg = KnowledgeGraph()
    for line in nodes_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        uid = rec.pop("uid")
        label = rec.pop("label")
        kg.add_node(label, uid, **rec)
    for line in edges_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        kg.add_edge(rec["src"], rec["rel"], rec["dst"], **rec.get("props", {}))
    return kg
