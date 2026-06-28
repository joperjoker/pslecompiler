"""Emit portable load artifacts from a KnowledgeGraph.

Produces, under data/artifacts/<name>/:
  * nodes.jsonl   - one node per line
  * edges.jsonl   - one edge per line
  * load.cypher   - idempotent MERGE script for Neo4j (run from your machine)
  * manifest.json - counts + provenance

The Cypher uses parameter-free MERGE statements so it can be pasted into the
Neo4j Browser, cypher-shell, or the HTTP Query API without a driver. Embeddings
(if present) are written as list properties; the vector indexes themselves come
from schema/constraints.cypher.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import KnowledgeGraph, nodes_to_jsonl, edges_to_jsonl


def _cypher_value(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_cypher_value(x) for x in v) + "]"
    # string: escape backslash, quote, newline
    s = str(v).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return f"'{s}'"


def _props_to_cypher(props: dict[str, Any]) -> str:
    items = [f"{k}: {_cypher_value(v)}" for k, v in props.items()]
    return "{" + ", ".join(items) + "}"


def emit_cypher(kg: KnowledgeGraph) -> str:
    lines: list[str] = [
        "// Auto-generated load script. Idempotent (MERGE on uid).",
        "// Run schema/constraints.cypher FIRST for uniqueness + vector indexes.",
        "",
    ]
    for n in kg.nodes.values():
        props = {"uid": n.uid, **n.props}
        lines.append(
            f"MERGE (x:{n.label} {{uid: {_cypher_value(n.uid)}}}) "
            f"SET x += {_props_to_cypher(props)};"
        )
    lines.append("")
    for e in kg.edges.values():
        set_clause = f" SET r += {_props_to_cypher(e.props)}" if e.props else ""
        lines.append(
            f"MATCH (a {{uid: {_cypher_value(e.src)}}}), "
            f"(b {{uid: {_cypher_value(e.dst)}}}) "
            f"MERGE (a)-[r:{e.rel}]->(b){set_clause};"
        )
    return "\n".join(lines) + "\n"


def write_artifacts(
    kg: KnowledgeGraph, out_dir: Path, *, provenance: dict[str, Any] | None = None
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "nodes.jsonl").write_text(
        "\n".join(nodes_to_jsonl(kg)) + "\n", encoding="utf-8"
    )
    (out_dir / "edges.jsonl").write_text(
        "\n".join(edges_to_jsonl(kg)) + "\n", encoding="utf-8"
    )
    (out_dir / "load.cypher").write_text(emit_cypher(kg), encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(kg.nodes),
        "edge_count": len(kg.edges),
        "label_counts": kg.label_counts(),
        "rel_counts": kg.rel_counts(),
        "provenance": provenance or {},
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest
