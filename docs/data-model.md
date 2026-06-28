# Data model

## Node labels
| Label | Meaning | Key properties |
|-------|---------|----------------|
| `Subject` | English / Mathematics / Science / Chinese | `name` |
| `SyllabusVersion` | one syllabus edition | `version`, `effective_year`, `level`, `source_url` |
| `Theme` | theme / strand | `name`, `kind` |
| `Topic` | topic within a theme | `name`, `primary_level`, `track`, `core_ideas[]`, `practices[]` |
| `LearningOutcome` | **MCQ-ready atom** | `text`, `primary_level`, `cognitive_level`, `difficulty_band`, `source_citation`, `embedding` |
| `Concept` | a concept covered by outcomes | `name`, `embedding` |
| `Term` | key vocabulary | `name` |
| `Misconception` | a documented wrong belief | `statement` |
| `Distractor` | an MCQ wrong-option phrasing | `text` |
| `WikiArticle` | synthesized, cited article | `title`, `body_md`, `citations[]`, `embedding` |
| `Community` | a cluster of related concepts | `member_names[]`, `summary`, `embedding` |

Every content node carries `subject` + `syllabus_version` so **all syllabus
versions coexist** and queries can target a specific edition.

## Relationships
```
(:SyllabusVersion)-[:FOR_SUBJECT]->(:Subject)
(:Theme)-[:PART_OF]->(:SyllabusVersion)
(:Topic)-[:PART_OF]->(:Theme)
(:LearningOutcome)-[:PART_OF]->(:Topic)
(:LearningOutcome)-[:COVERS]->(:Concept|:Term)
(:Concept)-[:PREREQUISITE_OF]->(:Concept)
(:Concept)-[:RELATED_TO]->(:Concept)
(:Concept)-[:COMMONLY_CONFUSED_WITH]->(:Concept)   // ← distractor source
(:Misconception)-[:ABOUT]->(:Concept)
(:Distractor)-[:DERIVED_FROM]->(:Misconception)     // ← distractor source
(:WikiArticle)-[:SYNTHESIZES]->(:Topic|:Concept)
(:WikiArticle)-[:CITES]->(:LearningOutcome)
(:Community)-[:CONTAINS]->(:Concept)
```

## The three layers, on the graph
- **Structured spine** = the `PART_OF` hierarchy under each `SyllabusVersion`.
- **Wiki synthesis** = `WikiArticle` nodes (`SYNTHESIZES` / `CITES`).
- **GraphRAG** = the `Concept`/`Misconception`/`Distractor` subgraph +
  `Community` summaries.

## Cognitive-science metadata
`cognitive_level ∈ {knowledge, comprehension, application, analysis}` (MOE
assessment objectives ≈ Bloom) and `difficulty_band ∈ {foundational, core,
challenging}` are attached to each `LearningOutcome`, so the question bank can
target cognitive demand and support spaced-repetition / interleaving downstream.

Schema (constraints + vector indexes): `schema/constraints.cypher`.
