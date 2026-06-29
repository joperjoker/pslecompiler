# Prompt: extract MCQ items from a past paper

You are given the raw text (and, if needed, the page image) of a past-year PSLE
paper. Produce clean `RawItem` JSON objects (one per line) — `qnum`, `stem`,
`options` (exactly 4, in order), and `answer_index` (0-based) **only if** the
paper itself prints an answer key.

## Rules
- Preserve the question wording faithfully; fix only OCR/layout artefacts.
- Keep all four options, in their original order.
- Do not invent the answer — leave `answer_index` null unless the paper states it
  (the answer is verified later in the answer/feedback step).
- Drop non-question material (instructions, headers, page numbers).
- Note any item with a figure/diagram the text can't capture (set a `note`).
