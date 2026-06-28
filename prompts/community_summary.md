# Prompt: community summary (GraphRAG)

You are given a `Community` — a cluster of related concepts (with their
member names and the learning outcomes that cover them). Write a short summary
that captures what this cluster is *about* and how its concepts connect.

## Produce
- `summary` — 2–4 sentences: the unifying idea, the key concepts, and the main
  relationships/prerequisites among them.

## Use
These summaries power GraphRAG "global" retrieval — when a question targets a
broad or synthesis-level idea rather than a single outcome, the retriever pulls
the relevant community summaries as context. Keep them faithful to the member
concepts; do not add concepts that are not in the community.
