from pslecompiler.model import THEME, TOPIC, LEARNING_OUTCOME, SYLLABUS_VERSION


def test_spine_builds_themes_topics_outcomes(science_kg):
    themes = {n.props["name"] for n in science_kg.nodes_with_label(THEME)}
    assert {"Cycles", "Systems"} <= themes

    topics = {n.props["name"] for n in science_kg.nodes_with_label(TOPIC)}
    assert "Matter (P3)" in topics
    assert "Plant System (P5)" in topics

    los = science_kg.nodes_with_label(LEARNING_OUTCOME)
    assert len(los) == 3  # two under Matter, one under Plant System


def test_primary_level_tagging(science_kg):
    los = science_kg.nodes_with_label(LEARNING_OUTCOME)
    levels = {lo.props.get("primary_level") for lo in los}
    assert "P3" in levels and "P5" in levels


def test_versioning_present(science_kg):
    ver = science_kg.nodes_with_label(SYLLABUS_VERSION)[0]
    assert ver.props["version"] == "2023"
    assert ver.props["effective_year"] == 2023
