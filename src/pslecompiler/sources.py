"""Registry of MOE source syllabus documents.

Each entry pins a subject + syllabus version to a local PDF filename and the
official source URL. Versioning is first-class: multiple versions of the same
subject coexist, tagged by ``version`` / ``effective_year`` on every node they
produce (per the user's "ingest all versions" decision).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDoc:
    filename: str          # expected file in data/sources/
    subject: str           # English | Mathematics | Science | Chinese
    version: str           # syllabus year, e.g. "2023"
    effective_year: int    # year the syllabus takes effect
    level: str             # "Standard" (Foundation can be added later)
    title: str
    url: str
    # Which structure mapper turns the parsed PDF into hierarchy nodes.
    mapper: str


REGISTRY: dict[str, SourceDoc] = {
    s.filename: s
    for s in [
        SourceDoc(
            filename="science-primary-2023.pdf",
            subject="Science",
            version="2023",
            effective_year=2023,
            level="Standard",
            title="Primary Science Teaching & Learning Syllabus 2023",
            url="https://www.moe.gov.sg/-/media/files/primary/syllabus/2023-primary-science.pdf",
            mapper="science_2023",
        ),
        SourceDoc(
            filename="maths-primary-2021.pdf",
            subject="Mathematics",
            version="2021",
            effective_year=2021,
            level="Standard",
            title="Primary Mathematics Teaching & Learning Syllabus 2021",
            url="https://www.moe.gov.sg/-/media/files/primary/2021-primary-mathematics-syllabus-p1-to-p6-updated-october-2025.pdf",
            mapper="generic",
        ),
        SourceDoc(
            filename="english-primary-2020.pdf",
            subject="English",
            version="2020",
            effective_year=2020,
            level="Standard",
            title="English Language Syllabus 2020 (Primary)",
            url="https://libris.nie.edu.sg/sites/default/files/2020-01/primary_els-2020-_syllabus.pdf",
            mapper="generic",
        ),
        SourceDoc(
            filename="chinese-primary-2015.pdf",
            subject="Chinese",
            version="2015",
            effective_year=2015,
            level="Standard",
            title="小学华文课程标准 2015",
            url="https://www.moe.gov.sg/-/media/files/primary/chinese-primary-2015.pdf",
            mapper="generic",
        ),
        SourceDoc(
            filename="chinese-primary-2024.pdf",
            subject="Chinese",
            version="2024",
            effective_year=2026,
            level="Standard",
            title="小学华文课程标准 2024 (wef 2026 P1)",
            url="https://www.moe.gov.sg/-/media/files/primary/cl-syllabus-pri-2024.pdf",
            mapper="generic",
        ),
    ]
}


def get_source(filename: str) -> SourceDoc:
    if filename not in REGISTRY:
        known = ", ".join(REGISTRY)
        raise KeyError(f"Unknown source '{filename}'. Known sources: {known}")
    return REGISTRY[filename]
