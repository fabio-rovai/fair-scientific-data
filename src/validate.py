#!/usr/bin/env python3
"""
fair-scientific-data v0.1 — SHACL Dataset Contract Validator

Usage:
    python src/validate.py <metadata-file.(ttl|jsonld|json-ld|json)> [--shapes shapes/dataset-contract.shacl.ttl]

Exit codes:
    0  Conforms
    1  Violations found
    2  Error (parse failure, missing file, etc.)
"""

import sys
import argparse
import json
import pathlib
from datetime import datetime

try:
    import rdflib
    from rdflib import Graph
    from pyshacl import validate
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}\nRun: pip install rdflib pyshacl", file=sys.stderr)
    sys.exit(2)

DEFAULT_SHAPES = pathlib.Path(__file__).parent.parent / "shapes" / "dataset-contract.shacl.ttl"
FORMATS = {
    ".ttl": "turtle",
    ".jsonld": "json-ld",
    ".json": "json-ld",
    ".n3": "n3",
    ".nt": "nt",
    ".xml": "xml",
    ".rdf": "xml",
}


def detect_format(path: pathlib.Path) -> str:
    suffix = path.suffix.lower()
    return FORMATS.get(suffix, "turtle")


def load_graph(path: pathlib.Path) -> Graph:
    g = Graph()
    fmt = detect_format(path)
    g.parse(str(path), format=fmt)
    return g


def count_results(results_graph: Graph) -> dict:
    """Count violations, warnings, and infos from pyshacl result graph."""
    from rdflib.namespace import RDF
    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

    violation_count = 0
    warning_count = 0
    info_count = 0
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        severity = results_graph.value(result, SH.resultSeverity)
        if severity == SH.Violation:
            violation_count += 1
        elif severity == SH.Warning:
            warning_count += 1
        elif severity == SH.Info:
            info_count += 1

    return {"violations": violation_count, "warnings": warning_count, "infos": info_count}


def emit_report(
    data_path: pathlib.Path,
    shapes_path: pathlib.Path,
    conforms: bool,
    results_graph: Graph,
    results_text: str,
    counts: dict,
    output_path: pathlib.Path | None,
):
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# FAIR Dataset Contract — Validation Report",
        f"",
        f"- **Data file**: `{data_path}`",
        f"- **Shapes file**: `{shapes_path}`",
        f"- **Validated at**: {now}",
        f"- **Conforms**: {'YES ✓' if conforms else 'NO ✗'}",
        f"- **Violations**: {counts['violations']}",
        f"- **Warnings**: {counts['warnings']}",
        f"- **Infos**: {counts['infos']}",
        f"",
        "## SHACL Report",
        "",
        "```",
        results_text.strip(),
        "```",
    ]
    report = "\n".join(lines)

    if output_path:
        output_path.write_text(report, encoding="utf-8")
        print(f"Report written to: {output_path}")
    else:
        print(report)

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate a dataset metadata file against the FAIR Dataset Contract SHACL shapes."
    )
    parser.add_argument("data", help="Path to dataset metadata file (TTL, JSON-LD, etc.)")
    parser.add_argument(
        "--shapes",
        default=str(DEFAULT_SHAPES),
        help=f"Path to SHACL shapes file (default: {DEFAULT_SHAPES})",
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Write report to this path (default: print to stdout)"
    )
    parser.add_argument(
        "--format",
        default=None,
        help="Force RDF format (turtle, json-ld, n3, xml, nt). Auto-detected from extension by default.",
    )
    args = parser.parse_args()

    data_path = pathlib.Path(args.data)
    shapes_path = pathlib.Path(args.shapes)

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(2)

    if not shapes_path.exists():
        print(f"ERROR: Shapes file not found: {shapes_path}", file=sys.stderr)
        sys.exit(2)

    # Parse data graph
    try:
        data_graph = Graph()
        fmt = args.format or detect_format(data_path)
        data_graph.parse(str(data_path), format=fmt)
    except Exception as e:
        print(f"ERROR: Could not parse data file '{data_path}': {e}", file=sys.stderr)
        sys.exit(2)

    # Parse shapes graph
    try:
        shapes_graph = Graph()
        shapes_graph.parse(str(shapes_path), format="turtle")
    except Exception as e:
        print(f"ERROR: Could not parse shapes file '{shapes_path}': {e}", file=sys.stderr)
        sys.exit(2)

    # Run SHACL validation
    try:
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference="rdfs",
            abort_on_first=False,
            meta_shacl=False,
            debug=False,
        )
    except Exception as e:
        print(f"ERROR: SHACL validation failed: {e}", file=sys.stderr)
        sys.exit(2)

    counts = count_results(results_graph)

    output_path = pathlib.Path(args.output) if args.output else None
    emit_report(data_path, shapes_path, conforms, results_graph, results_text, counts, output_path)

    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
