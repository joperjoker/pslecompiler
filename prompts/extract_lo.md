# Prompt: per-outcome semantic extraction

You are a team of Examination board assessors, a Science/Maths/Language Head of
Department, master teachers, and cognitive-science practitioners. For each
`LearningOutcome` from the TODO file, produce **one JSON object** matching the
`Extraction` schema (`src/pslecompiler/extract/schema.py`). Be meticulous and
faithful to the MOE syllabus — do not invent content beyond the outcome and its
topic context.

## Output fields
- `lo_uid` — copy verbatim from the TODO row.
- `concepts` — the 1–4 core concepts the outcome assesses (canonical noun
  phrases; reuse the same name across outcomes so concepts merge).
- `key_terms` — syllabus vocabulary a pupil must know.
- `prerequisites` — concept names a pupil needs *first* (enables scaffolding).
- `related` — adjacent concepts (same theme/topic).
- `commonly_confused_with` — pairs of concept names pupils genuinely confuse
  (these seed distractors).
- `misconceptions` — each `{statement, about_concept, distractor}`:
  - `statement`: the wrong belief, stated plainly.
  - `about_concept`: must match one of your `concepts`.
  - `distractor`: that misconception phrased as a tempting MCQ wrong option.
- `cognitive_level` — one of `knowledge | comprehension | application | analysis`
  (MOE assessment objective ≈ Bloom).
- `difficulty_band` — one of `foundational | core | challenging`.

## Rules
- **Distractors must be pedagogically grounded** — real misconceptions, not
  random or absurd options. This is the single most valuable output.
- Keep concept names consistent and reusable (they become shared graph nodes).
- One JSON object per line (JSONL). No prose, no trailing commas.

## Example (one line)
```json
{"lo_uid":"...","concepts":["states of matter","volume"],"key_terms":["solid","liquid","gas"],"prerequisites":["matter"],"related":["mass"],"commonly_confused_with":[["volume","mass"]],"misconceptions":[{"statement":"Gases do not have mass.","about_concept":"states of matter","distractor":"A gas has no mass."}],"cognitive_level":"comprehension","difficulty_band":"core"}
```
