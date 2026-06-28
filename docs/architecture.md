# Architecture

```
 MOE PDF ──parse──▶ Sections ──structure──▶ Spine (Theme/Topic/LearningOutcome)
                                                   │
                                  agent extraction │ (concepts, prerequisites,
                                                   ▼  misconceptions→distractors)
                                            GraphRAG subgraph
                                                   │
                              community detection  │  + wiki synthesis
                                                   ▼
                          KnowledgeGraph ──emit──▶ nodes.jsonl / edges.jsonl
                                          ──emit──▶ load.cypher ──▶ Neo4j AuraDB
                                                   │
                                       retrieve ◀──┘  (MCQ question-spec bundles)
```

## Why graph-native
A question bank needs more than chunks: it needs *relationships* — which concept
is a prerequisite of which, which concepts pupils confuse, which misconceptions
yield good distractors. A property graph models all three layers (spine, wiki,
GraphRAG) in one store and lets retrieval traverse them. Neo4j adds a native
vector index so semantic RAG lives in the same place.

## Backend-agnostic core
`model.KnowledgeGraph` is an in-memory graph that serializes to JSONL + Cypher
and reloads for querying. This means:
- the retrieval/matching algorithm is **fully runnable and tested without
  Neo4j or the network** (the local NetworkX-style backend), and
- the same graph compiles to Cypher for the production AuraDB backend.

## Module map (`src/pslecompiler/`)
| Module | Responsibility |
|--------|----------------|
| `sources.py` | registry mapping each subject+version to a PDF + source URL |
| `parse_pdf.py` | PDF → ordered `Section`s (font-size heading inference) |
| `structure.py` | heading-driven mappers → spine (generic subjects) |
| `science2023.py` | table-aware parser for the Science 2023 PDF |
| `extract/` | extraction schema + `apply_extractions` (GraphRAG subgraph) |
| `embed.py` | pluggable embeddings (no-op default, BGE-M3 when available) |
| `community.py` | offline community detection (NetworkX) for GraphRAG |
| `graph_artifacts.py` | emit `nodes.jsonl` / `edges.jsonl` / `load.cypher` |
| `graphdb.py` | optional live Neo4j HTTP Query API client |
| `retrieve.py` | the retrieval + matching algorithm |
| `cli.py` | `ingest` / `enrich` / `retrieve` / `load` |

## Environment constraints that shaped the design
- `moe.gov.sg` egress blocked → PDFs are committed to `data/sources/`.
- Neo4j Bolt (:7687) blocked by HTTPS-only proxy → use the **HTTP Query API**.
- `huggingface.co` blocked → embeddings optional; the graph works without them.
- Neo4j AuraDB Free has no GDS → community detection runs offline in NetworkX.
