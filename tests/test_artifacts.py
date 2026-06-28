from pslecompiler.graph_artifacts import write_artifacts, emit_cypher
from pslecompiler.model import load_jsonl_graph


def test_artifact_roundtrip(science_kg, tmp_path):
    manifest = write_artifacts(science_kg, tmp_path)
    assert manifest["node_count"] == len(science_kg.nodes)
    assert (tmp_path / "nodes.jsonl").exists()
    assert (tmp_path / "edges.jsonl").exists()
    assert (tmp_path / "load.cypher").exists()

    reloaded = load_jsonl_graph(tmp_path / "nodes.jsonl", tmp_path / "edges.jsonl")
    assert len(reloaded.nodes) == len(science_kg.nodes)
    assert len(reloaded.edges) == len(science_kg.edges)


def test_cypher_is_merge_based(science_kg):
    cy = emit_cypher(science_kg)
    assert "MERGE" in cy
    assert "LearningOutcome" in cy
    # CJK / quotes must be escaped safely (no raw unescaped single quotes break)
    assert cy.count("MERGE") >= len(science_kg.nodes)
