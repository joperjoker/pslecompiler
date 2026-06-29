# Prompt: generate a controlled item variant

Given a published question, produce a `Variant` that assesses the **same concept
at the same difficulty and cognitive level**, changing only surface features
(numbers, names, context) so pupils can't pass by memorising the original.

## Output (`Variant`)
- `parent_qid`, `stem`, `options` (4), `answer_index` (0-based), `note` (what you
  changed).

## Rules
- Keep the assessed concept and difficulty identical to the parent.
- Keep the distractors embodying the **same misconceptions** as the parent (re-skin
  them to the new context).
- Exactly one correct option; options plausible and mutually exclusive.
- Stay within syllabus scope.
