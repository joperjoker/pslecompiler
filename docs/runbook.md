# Runbook — stand up your AuraDB second brain

The pipeline produces portable artifacts in this environment; you load them into
your own Neo4j from a machine with normal network access.

## 1. Create a free Neo4j AuraDB instance
1. Sign up at https://console.neo4j.io and create a **free** AuraDB instance.
2. Save the generated password and note the instance connection details.
3. The HTTP **Query API** endpoint looks like:
   `https://<dbid>.databases.neo4j.io/db/neo4j/query/v2`

## 2. Apply the schema, then the data
From a networked machine (or this environment if `*.databases.neo4j.io` is
allowlisted):

```bash
cp .env.example .env   # fill NEO4J_QUERY_URL / NEO4J_USER / NEO4J_PASSWORD
pslecompiler load --stem science-primary-2023
```
`load` runs `schema/constraints.cypher` (constraints + vector indexes) then the
generated `data/artifacts/science-primary-2023/load.cypher` (idempotent MERGEs).

Prefer the Neo4j Browser? Paste `constraints.cypher` then `load.cypher` directly.

## 3. Add embeddings (optional vector layer)
Where `huggingface.co` is reachable:
```bash
uv pip install -e '.[embeddings]'
pslecompiler ingest --source science-primary-2023.pdf      # now embeds
pslecompiler enrich --stem science-primary-2023 \
    --extractions data/extracted/science-primary-2023.extractions.jsonl
```
BGE-M3 is 1024-dim (matches `schema/constraints.cypher`). Using a different
model? Update the `vector.dimensions` in the schema.

## 4. Replicate to the other subjects (Phase B)
For each of `maths-primary-2021.pdf`, `english-primary-2020.pdf`,
`chinese-primary-2015.pdf`, `chinese-primary-2024.pdf`:
1. `pslecompiler ingest --source <file> --no-embed` and inspect the spine.
2. If outcomes are noisy, the PDF is table-based — add a dedicated parser
   modelled on `science2023.py` and register it in `cli.PDF_MAPPERS`.
3. Author extractions for the TODO, then `enrich` and `load`.

## 5. Verify
```bash
pytest -q
pslecompiler retrieve --stem science-primary-2023 --subject Science \
    --version 2023 --query "changes of state" --count 3
```
In Neo4j, sanity-check counts:
```cypher
MATCH (lo:LearningOutcome {subject:'Science'}) RETURN count(lo);
MATCH (d:Distractor)-[:DERIVED_FROM]->(:Misconception) RETURN count(d);
```
