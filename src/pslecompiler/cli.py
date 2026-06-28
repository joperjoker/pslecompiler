"""Command-line entry point.

Subcommands:
  ingest   PDF -> parsed -> spine -> (embed) -> artifacts + extraction TODO
  enrich   merge agent extractions (+ communities, embed) -> artifacts
  retrieve query the local graph for MCQ question-spec bundles
  load     OPTIONAL: push artifacts to Neo4j via the HTTP Query API
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import config
from .community import detect_communities
from .embed import embed_graph
from .extract import apply_extractions, read_extractions, write_todo
from .graph_artifacts import write_artifacts
from .model import load_jsonl_graph
from .parse_pdf import parse_pdf, read_parsed, write_parsed
from .retrieve import QuestionSpec, retrieve
from .science2023 import parse_science_2023
from .sources import get_source
from .structure import build_spine

# Subjects whose real PDFs are table-based get a PDF-native parser instead of
# the heading-driven Section flow.
PDF_MAPPERS = {"science_2023": parse_science_2023}


def _artifact_dir(stem: str) -> Path:
    return config.ARTIFACTS_DIR / stem


def cmd_ingest(args: argparse.Namespace) -> int:
    config.ensure_dirs()
    src = get_source(args.source)
    pdf = config.SOURCES_DIR / src.filename
    if not pdf.exists():
        print(f"ERROR: {pdf} not found. Commit the PDF first "
              f"(see data/sources/README.md).", file=sys.stderr)
        return 2

    sections = parse_pdf(pdf)
    parsed_path = config.PARSED_DIR / f"{pdf.stem}.json"
    write_parsed(sections, parsed_path)

    if src.mapper in PDF_MAPPERS:
        kg = PDF_MAPPERS[src.mapper](pdf, src)
    else:
        kg = build_spine(sections, src)
    if not args.no_embed:
        embed_graph(kg)

    out = _artifact_dir(pdf.stem)
    manifest = write_artifacts(kg, out, provenance=asdict(src))
    todo_path = config.EXTRACTED_DIR / f"{pdf.stem}.todo.jsonl"
    n_todo = write_todo(kg, todo_path)

    print(f"Parsed {len(sections)} sections -> {parsed_path}")
    print(f"Spine: {manifest['label_counts']}")
    print(f"Artifacts -> {out}")
    print(f"Extraction TODO ({n_todo} outcomes) -> {todo_path}")
    return 0


def cmd_enrich(args: argparse.Namespace) -> int:
    config.ensure_dirs()
    out = _artifact_dir(args.stem)
    kg = load_jsonl_graph(out / "nodes.jsonl", out / "edges.jsonl")

    ext_path = Path(args.extractions)
    stats = apply_extractions(kg, read_extractions(ext_path))
    n_comm = detect_communities(kg)
    if not args.no_embed:
        embed_graph(kg)

    manifest = write_artifacts(kg, out, provenance={"enriched_from": str(ext_path)})
    print(f"Applied extractions: {stats}; communities: {n_comm}")
    print(f"Graph now: {manifest['label_counts']}")
    print(f"Artifacts updated -> {out}")
    return 0


def cmd_retrieve(args: argparse.Namespace) -> int:
    out = _artifact_dir(args.stem)
    kg = load_jsonl_graph(out / "nodes.jsonl", out / "edges.jsonl")
    spec = QuestionSpec(
        subject=args.subject, syllabus_version=args.version, theme=args.theme,
        primary_level=args.level, cognitive_level=args.cognitive,
        difficulty_band=args.difficulty, query=args.query, count=args.count,
    )
    bundles = retrieve(kg, spec)
    print(json.dumps([asdict(b) for b in bundles], indent=2, ensure_ascii=False))
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    from .graphdb import Neo4jQueryClient

    out = _artifact_dir(args.stem)
    client = Neo4jQueryClient()
    if not client.smoke_test():
        print("Neo4j smoke test failed.", file=sys.stderr)
        return 1
    schema = (config.ROOT / "schema" / "constraints.cypher").read_text("utf-8")
    client.run_script(schema)
    n = client.run_script((out / "load.cypher").read_text("utf-8"))
    print(f"Loaded {n} statements into Neo4j.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pslecompiler")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="PDF -> spine + artifacts + extraction TODO")
    pi.add_argument("--source", required=True, help="filename in data/sources/")
    pi.add_argument("--no-embed", action="store_true")
    pi.set_defaults(func=cmd_ingest)

    pe = sub.add_parser("enrich", help="merge extractions -> artifacts")
    pe.add_argument("--stem", required=True, help="artifact dir name (PDF stem)")
    pe.add_argument("--extractions", required=True, help="extractions JSONL path")
    pe.add_argument("--no-embed", action="store_true")
    pe.set_defaults(func=cmd_enrich)

    pr = sub.add_parser("retrieve", help="query for MCQ bundles")
    pr.add_argument("--stem", required=True)
    pr.add_argument("--subject", required=True)
    pr.add_argument("--version")
    pr.add_argument("--theme")
    pr.add_argument("--level")
    pr.add_argument("--cognitive")
    pr.add_argument("--difficulty")
    pr.add_argument("--query")
    pr.add_argument("--count", type=int, default=5)
    pr.set_defaults(func=cmd_retrieve)

    pl = sub.add_parser("load", help="OPTIONAL: push artifacts to Neo4j")
    pl.add_argument("--stem", required=True)
    pl.set_defaults(func=cmd_load)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
