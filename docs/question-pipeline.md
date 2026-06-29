# Question pipeline (the product)

The question bank is the deliverable; the syllabus graph is its scaffolding. The
pipeline is **neurosymbolic**: the LLM proposes, the syllabus graph + validators
constrain and check.

```
past-paper PDF ─ingest-paper─▶ RawItems ─┐
                                          │  (agent: prompts/paper_extract.md)
                                          ▼
                              Question + Option nodes (qmodel.py)
                                          │
            symbolic candidates (tag.suggest_tags via retrieve.py)
                                          │  (agent: prompts/tagging.md)
                                          ▼
                         ASSESSES / TESTS tags  ── apply_tagging
                                          │  (agent: prompts/answer_feedback.md)
                                          ▼
              verified key + per-option rationale + Option-[:EMBODIES]->Misconception
                                          │  (agent: prompts/variant.md)
                                          ▼
                         controlled variants ── apply_variants
                                          │
                                 QA validators (qa_questions.py)
                                          │  errors -> repair loop
                                          ▼
                   export_questions ─▶ questions.json + import.sql ─▶ Supabase ─▶ app
```

## Symbolic vs neural
- **Symbolic:** the syllabus graph (Subject→Theme→Topic→LO→Concept→Misconception),
  `tag.suggest_tags` (candidate LOs), and `qa_questions.validate_questions`
  (exactly one key, 4 options, in-syllabus tag present, rationale per option,
  distractor↔misconception).
- **Neural:** the agent parses messy items, verifies answers, writes per-option
  rationales, picks tags, and writes variants — always emitting JSON the symbolic
  layer can validate and merge (same author→JSONL→merge pattern as `extract/`).
- **Loop (CLAUDE.md method):** proposer (agent) → challenger/judge (validators) →
  revise until QA passes, then publish.

## CLI
```
pslecompiler ingest-paper   --paper <file.pdf>        # PDF -> raw items
pslecompiler questions-demo --stem <syllabus-stem>    # worked sample -> bank
pslecompiler questions-qa   --stem <syllabus-stem>    # validate
```
Real papers: `ingest-paper`, then the agent authors tagging + answer/feedback +
variants (JSONL using the prompts), which are merged, QA'd, and exported.

## Data model additions
`Paper`, `Question`, `Option` nodes; edges `FROM_PAPER`, `HAS_OPTION`,
`ASSESSES`→LearningOutcome, `TESTS`→Concept, `BELONGS_TO`→SyllabusVersion,
`Option-[:EMBODIES]->Misconception`, `Question-[:VARIANT_OF]->Question`. See
`docs/data-model.md` and `schema/constraints.cypher`.
