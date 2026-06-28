from pslecompiler.retrieve import QuestionSpec, retrieve, filter_outcomes


def test_filter_by_subject_and_level(science_kg):
    spec = QuestionSpec(subject="Science", syllabus_version="2023", primary_level="P5")
    los = filter_outcomes(science_kg, spec)
    # P5 outcome + the untagged ones (primary_level None pass-through)
    assert all(lo.props.get("primary_level") in ("P5", None) for lo in los)
    assert any(lo.props.get("primary_level") == "P5" for lo in los)


def test_retrieve_returns_grounded_distractors(science_kg):
    spec = QuestionSpec(subject="Science", syllabus_version="2023",
                        theme="Cycles", count=5)
    bundles = retrieve(science_kg, spec)
    assert bundles
    first = next(b for b in bundles if b.focus_concepts)
    assert "states of matter" in first.focus_concepts
    # distractors come from the misconception AND the confused-with concepts
    assert any("mass" in d.lower() for d in first.distractor_options)
    assert first.source_citation


def test_keyword_query_ranks(science_kg):
    spec = QuestionSpec(subject="Science", query="three states of matter", count=3)
    bundles = retrieve(science_kg, spec)
    assert bundles
    assert bundles[0].score >= 0
