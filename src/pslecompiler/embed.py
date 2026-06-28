"""Pluggable embedding layer (the vector half of RAG).

Default is a no-op so the whole pipeline runs without network/model weights
(huggingface egress is blocked in some environments). When weights are
available, ``SentenceTransformerEmbedder`` produces real multilingual vectors
(BGE-M3 by default — strong on Chinese). Embeddings are attached to nodes as an
``embedding`` list property; the Neo4j vector indexes live in
schema/constraints.cypher.
"""
from __future__ import annotations

from typing import Protocol

from .config import EMBEDDING_MODEL
from .model import (
    CONCEPT, LEARNING_OUTCOME, WIKI_ARTICLE, KnowledgeGraph,
)

EMBED_LABELS = (LEARNING_OUTCOME, CONCEPT, WIKI_ARTICLE)


class Embedder(Protocol):
    dim: int

    def encode(self, texts: list[str]) -> list[list[float]]: ...


class NullEmbedder:
    """Returns nothing; lets the pipeline run with no vectors."""

    dim = 0

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[] for _ in texts]


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vecs]


def get_embedder() -> Embedder:
    """Best-effort: real embedder if available, else no-op."""
    try:
        return SentenceTransformerEmbedder()
    except Exception:
        return NullEmbedder()


def _node_text(node) -> str:
    return node.props.get("text") or node.props.get("name") or node.props.get("statement") or ""


def embed_graph(kg: KnowledgeGraph, embedder: Embedder | None = None) -> int:
    """Attach embeddings to embeddable nodes. Returns count embedded."""
    embedder = embedder or get_embedder()
    if getattr(embedder, "dim", 0) == 0:
        return 0
    targets = [n for n in kg.nodes.values() if n.label in EMBED_LABELS]
    texts = [_node_text(n) for n in targets]
    vectors = embedder.encode(texts)
    n = 0
    for node, vec in zip(targets, vectors):
        if vec:
            node.props["embedding"] = vec
            n += 1
    return n
