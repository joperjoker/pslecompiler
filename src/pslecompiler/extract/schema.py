"""Pydantic schema for a single LearningOutcome extraction record.

One JSON object per line in the extractions JSONL. This is the contract between
the agent that does the semantic extraction and ``apply_extractions``.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Misconception(BaseModel):
    statement: str                 # the wrong belief, stated plainly
    about_concept: str = ""        # concept it concerns (matches a concept name)
    distractor: str = ""           # an MCQ wrong-option phrasing of it


class Extraction(BaseModel):
    lo_uid: str
    concepts: list[str] = Field(default_factory=list)
    key_terms: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)   # concept names
    related: list[str] = Field(default_factory=list)         # concept names
    # pairs of concept names that pupils confuse
    commonly_confused_with: list[tuple[str, str]] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    cognitive_level: str = ""      # one of config.COGNITIVE_LEVELS
    difficulty_band: str = ""      # one of config.DIFFICULTY_BANDS
