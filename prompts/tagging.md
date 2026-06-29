# Prompt: neurosymbolic question tagging

You are given a question stem plus **candidate** LearningOutcomes (from the
symbolic retriever, `tag.suggest_tags`) with their concepts. Choose the tags that
the question actually assesses and emit one `Tagging` JSON object.

## Output (`Tagging`)
- `qid` — copy verbatim.
- `learning_outcomes` — uids of the LO(s) the question assesses (usually 1).
- `concepts` — concept names tested (reuse syllabus concept names so they merge).
- `theme` — the theme name.

## Rules
- Tag to the **most specific** outcome the item assesses; add a second only if it
  genuinely spans two.
- Prefer candidates from the retriever; only go outside them if all are wrong
  (then say so and pick the correct syllabus concept).
- Never tag out-of-syllabus content — if the item is off-syllabus, flag it.
