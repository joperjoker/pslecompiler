# Retrieval & matching algorithm

Goal: given a `QuestionSpec`, return grounded **question-spec bundles** an item
writer (or an LLM author) can turn into MCQs. Implemented in `retrieve.py` on
the in-memory graph; Cypher equivalents for AuraDB are given below.

## Input
```python
QuestionSpec(subject, syllabus_version, theme, primary_level,
             cognitive_level, difficulty_band, query, count)
```

## Steps
1. **Structured filter** — keep `LearningOutcome`s matching subject / version /
   primary level / cognitive level / difficulty, and (if given) whose ancestor
   Theme/Topic name contains `theme`.
2. **Semantic / keyword rank** — cosine over `embedding` if a query vector and
   vectors exist; otherwise a token-overlap score against the query; otherwise
   neutral. Ties broken by syllabus order.
3. **Graph expansion** (`expand_outcome`) — for each outcome's concepts gather:
   - prerequisites (`PREREQUISITE_OF`) → scaffolding,
   - commonly-confused concepts (`COMMONLY_CONFUSED_WITH`) → distractor seeds,
   - misconceptions (`ABOUT`) and their `Distractor`s → **grounded distractors**,
   - community summaries (`CONTAINS`) → GraphRAG context for synthesis items.
4. **Assemble + dedup** — build the bundle; skip outcomes whose token set
   overlaps a chosen one by > 0.85 (avoid near-duplicate items).

## Output bundle
`lo_text`, `subject`, `syllabus_version`, `primary_level`, `cognitive_level`,
`difficulty_band`, `focus_concepts`, `prerequisite_concepts`,
`distractor_options`, `community_context`, `source_citation`, `score`.

The distractors are **pedagogically grounded** — they come from documented
misconceptions and concepts pupils actually confuse, not random wrong answers.

## Cypher equivalents (AuraDB backend)
Structured filter:
```cypher
MATCH (lo:LearningOutcome {subject:$subject, syllabus_version:$version})
WHERE ($level IS NULL OR lo.primary_level = $level)
  AND ($cog   IS NULL OR lo.cognitive_level = $cog)
RETURN lo;
```
Vector search:
```cypher
CALL db.index.vector.queryNodes('lo_embedding', $k, $queryVec)
YIELD node, score RETURN node, score;
```
Grounded distractors for an outcome:
```cypher
MATCH (lo:LearningOutcome {uid:$uid})-[:COVERS]->(c:Concept)
OPTIONAL MATCH (c)<-[:ABOUT]-(:Misconception)<-[:DERIVED_FROM]-(d:Distractor)
OPTIONAL MATCH (c)-[:COMMONLY_CONFUSED_WITH]->(cc:Concept)
RETURN c.name, collect(DISTINCT d.text) AS distractors,
       collect(DISTINCT cc.name) AS confusedWith;
```

## Downstream (cognitive science)
Bundles carry difficulty + cognitive level so the practice app can sequence
items for **spaced repetition** and **interleaving**, and target a pupil's
weak prerequisites via the `PREREQUISITE_OF` chain.
