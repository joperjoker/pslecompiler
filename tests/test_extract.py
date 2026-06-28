from pslecompiler.model import (
    CONCEPT, MISCONCEPTION, DISTRACTOR, LEARNING_OUTCOME, COMMONLY_CONFUSED_WITH,
)


def test_extraction_creates_subgraph(science_kg):
    concepts = {n.props["name"] for n in science_kg.nodes_with_label(CONCEPT)}
    assert "states of matter" in concepts
    assert science_kg.nodes_with_label(MISCONCEPTION)
    assert science_kg.nodes_with_label(DISTRACTOR)


def test_cognitive_and_difficulty_on_outcome(science_kg):
    los = sorted(science_kg.nodes_with_label(LEARNING_OUTCOME),
                 key=lambda n: n.props.get("order", 0))
    assert los[0].props["cognitive_level"] == "comprehension"
    assert los[0].props["difficulty_band"] == "core"


def test_confused_with_is_bidirectional(science_kg):
    rels = [e for e in science_kg.edges.values()
            if e.rel == COMMONLY_CONFUSED_WITH]
    assert len(rels) == 2  # melting<->dissolving both directions
