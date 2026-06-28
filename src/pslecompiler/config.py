"""Central paths and environment configuration."""
from __future__ import annotations

import os
from pathlib import Path

try:  # optional, only needed for the live-load / embeddings paths
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience only
    pass

# Repo layout -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SOURCES_DIR = DATA / "sources"
PARSED_DIR = DATA / "parsed"
EXTRACTED_DIR = DATA / "extracted"
ARTIFACTS_DIR = DATA / "artifacts"


def ensure_dirs() -> None:
    for d in (PARSED_DIR, EXTRACTED_DIR, ARTIFACTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


# Neo4j (optional live load) --------------------------------------------------
NEO4J_QUERY_URL = os.environ.get("NEO4J_QUERY_URL", "")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

# Embeddings (optional) -------------------------------------------------------
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")

# Cognitive-science vocabularies ---------------------------------------------
# MOE assessment objectives map onto Bloom-style cognitive demand.
COGNITIVE_LEVELS = (
    "knowledge",        # recall facts/terms
    "comprehension",    # understand/explain
    "application",      # apply to new/familiar contexts
    "analysis",         # analyse/interpret/evaluate
)
DIFFICULTY_BANDS = ("foundational", "core", "challenging")
