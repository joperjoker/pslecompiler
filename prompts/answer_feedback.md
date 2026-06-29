# Prompt: verify answer + write per-option feedback

For each question (with its tagged concepts + the misconceptions in the graph),
emit one `AnswerFeedback` JSON object.

## Output (`AnswerFeedback`)
- `qid`, `answer_label` (the verified correct option "1".."4").
- `options`: for EACH option `{label, rationale, misconception}`:
  - correct option: `rationale` explains *why it is right*; `misconception` "".
  - each distractor: `rationale` explains *why it is wrong*, and `misconception`
    states the specific wrong belief it embodies (reuse a graph misconception
    statement where one fits).
- `cognitive_level` ∈ knowledge|comprehension|application|analysis.
- `difficulty_band` ∈ foundational|core|challenging.

## Rules
- Verify the key yourself from first principles — do not trust an unstated key.
- Exactly one correct option.
- Feedback is pitched at a primary pupil: short, concrete, non-condescending.
- Ground distractor rationales in real misconceptions — this is the whole point.
