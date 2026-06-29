from pslecompiler.sample import build_sample_question_graph
from pslecompiler.qa_questions import validate_questions, summarize
from pslecompiler.export_questions import questions_to_records
from pslecompiler.model import QUESTION, OPTION


def test_sample_questions_build_and_pass_qa(science_kg):
    kg, qids = build_sample_question_graph(science_kg)
    assert len(qids) == 4
    assert len(kg.nodes_with_label(QUESTION)) == 4
    assert len(kg.nodes_with_label(OPTION)) == 16

    issues = validate_questions(kg)
    assert summarize(issues)["errors"] == 0


def test_table_question_has_blocks_and_hint(science_kg):
    kg, _ = build_sample_question_graph(science_kg)
    recs = questions_to_records(kg, published_only=True)
    tbl = next(r for r in recs if any(b["type"] == "table" for b in r["stem_blocks"]))
    assert tbl["hint"]
    table_block = next(b for b in tbl["stem_blocks"] if b["type"] == "table")
    assert table_block["rows"]


def test_each_question_has_one_key_and_rationales(science_kg):
    kg, _ = build_sample_question_graph(science_kg)
    recs = questions_to_records(kg, published_only=True)
    assert len(recs) == 4
    for r in recs:
        correct = [o for o in r["options"] if o["is_correct"]]
        assert len(correct) == 1
        assert all(o["rationale"] for o in r["options"])
        # distractors carry the misconception they embody
        assert all(o["misconception"] for o in r["options"] if not o["is_correct"])


def test_questions_tagged_to_syllabus(science_kg):
    kg, _ = build_sample_question_graph(science_kg)
    recs = questions_to_records(kg, published_only=True)
    # concepts always present; learning outcomes resolved when syllabus has them
    assert all(r["concepts"] for r in recs)
    assert any(r["learning_outcomes"] for r in recs)
