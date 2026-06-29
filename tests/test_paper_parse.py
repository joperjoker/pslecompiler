from pslecompiler.paper_parse import parse_paper_text, build_sample_paper


def test_parse_paper_text_extracts_items():
    text = (
        "1. What is the boiling point of water at sea level?\n"
        "(1) 0 degrees C (2) 50 degrees C (3) 100 degrees C (4) 150 degrees C\n"
        "2. Which is a magnetic material?\n"
        "(1) copper (2) iron (3) plastic (4) glass\n"
    )
    items = parse_paper_text(text)
    assert len(items) == 2
    assert items[0].qnum == 1
    assert len(items[0].options) == 4
    assert "boiling point" in items[0].stem.lower()


def test_build_sample_paper():
    meta, items = build_sample_paper()
    assert meta["subject"] == "Science"
    assert len(items) == 3
    assert all(len(it.options) == 4 for it in items)
    assert all(it.answer_index is not None for it in items)
