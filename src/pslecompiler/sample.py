"""Synthetic, fully-worked sample paper for tests + app seed.

Stands in for agent output (tagging + answer/feedback) so the whole question
pipeline runs before any real past paper is uploaded. When a base graph (the
Science syllabus artifacts) is provided, questions are tagged to *real*
LearningOutcomes via the symbolic candidate generator (`tag.suggest_tags`),
demonstrating the neurosymbolic join end to end.
"""
from __future__ import annotations

from .model import KnowledgeGraph
from .paper_parse import build_sample_paper
from .qmodel import AnswerFeedback, OptionFeedback, Tagging, build_paper_questions
from .qpipeline import apply_answer_feedback, apply_tagging
from .tag import suggest_tags

# Per-question worked answer/feedback, keyed by qnum (1..3 of the sample paper).
_FEEDBACK = {
    1: {"answer": "2", "cog": "comprehension", "diff": "core", "concepts":
        ["states of matter", "shape", "volume"], "theme": "Cycles", "opts": [
        ("1", "Incorrect. Gases do have mass, even though it is small and they are often invisible.", "Gases do not have mass."),
        ("2", "Correct. A liquid flows to take the shape of its container while its volume stays fixed.", ""),
        ("3", "Incorrect. A solid keeps a fixed shape and volume; it does not expand to fill a container.", "A solid can change its volume to fit a container."),
        ("4", "Incorrect. A liquid has no fixed shape; it takes the shape of its container.", "A liquid has a fixed shape."),
    ]},
    2: {"answer": "3", "cog": "knowledge", "diff": "foundational", "concepts":
        ["magnetic force", "magnetic materials", "magnetic poles"], "theme": "Interactions", "opts": [
        ("1", "Incorrect. Magnets attract only magnetic materials (iron, steel); aluminium is not attracted.", "A magnet attracts all metals."),
        ("2", "Incorrect. Strength depends on the magnet, not merely its size; a small magnet can be stronger.", "A larger magnet is always stronger than a smaller one."),
        ("3", "Correct. A magnet exerts a push (repulsion) or a pull (attraction) on magnetic materials.", ""),
        ("4", "Incorrect. Like poles repel; only unlike poles attract.", "Like poles attract each other."),
    ]},
    3: {"answer": "1", "cog": "application", "diff": "core", "concepts":
        ["electric circuit", "closed circuit", "electrical conductor"], "theme": "Systems", "opts": [
        ("1", "Correct. A break (open) anywhere in the circuit stops the current, so the bulb will not light.", ""),
        ("2", "Incorrect. Current is not used up; the same current flows through the whole series circuit.", "Electric current is used up by the bulb so less returns to the battery."),
        ("3", "Incorrect. A bulb lights only in a closed circuit, not an open one.", "A bulb lights up even in an open circuit."),
        ("4", "Incorrect. Plastic is an insulator; it does not conduct electricity away.", "Plastic is a good conductor of electricity."),
    ]},
}


def build_sample_question_graph(base: KnowledgeGraph | None = None) -> tuple[KnowledgeGraph, list[str]]:
    kg = base if base is not None else KnowledgeGraph()
    meta, items = build_sample_paper()
    qids = build_paper_questions(
        kg, code=meta["code"], subject=meta["subject"],
        version=meta["version"], items=items, year=meta["year"],
    )

    af, tags = [], []
    for qid, item in zip(qids, items):
        fb = _FEEDBACK[item.qnum]
        af.append(AnswerFeedback(
            qid=qid, answer_label=fb["answer"], cognitive_level=fb["cog"],
            difficulty_band=fb["diff"],
            options=[OptionFeedback(label=l, rationale=r, misconception=m)
                     for l, r, m in fb["opts"]],
        ))
        # symbolic candidate generation -> top real LearningOutcome (if present)
        cands = suggest_tags(kg, qid, k=1)
        tags.append(Tagging(
            qid=qid, concepts=fb["concepts"], theme=fb["theme"],
            learning_outcomes=[c.lo_uid for c in cands],
        ))

    apply_answer_feedback(kg, af)
    apply_tagging(kg, tags)
    return kg, qids
