# Prompt: wiki article synthesis

You are a master teacher writing a concise, accurate "second-brain" article for a
topic or concept, to ground later question authoring. Use ONLY the supplied
syllabus context (the topic, its learning outcomes, core ideas, and the
concept/misconception subgraph). Do not introduce content beyond the syllabus
level.

## Produce
- `title` — the topic/concept name.
- `body_md` — short Markdown: what it is, the key ideas a PSLE pupil must master,
  worked intuition, and an explicit **"Common misconceptions"** section drawn
  from the graph (each paired with the correct idea).
- `citations` — the `lo_uid`s (and `source_citation` page refs) the article rests
  on. Every factual claim must trace to a cited learning outcome.

## Rules
- Pitch at primary level; precise but not over-scoped.
- The misconceptions section is mandatory — it is what makes the article useful
  for distractor design.
- Stay faithful: if the syllabus doesn't cover it, leave it out.
