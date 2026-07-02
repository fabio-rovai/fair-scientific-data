#!/usr/bin/env python3
"""
fair-scientific-data v0.1 — SHACL Dataset Contract Validator

Normalises input metadata to canonical schema.org form (via src/profiles.py)
then validates against the tier-1..tier-4 SHACL shapes.  A user running this
validator will get the same pass/fail result as the Python study analysis.

Usage:
    python src/validate.py <metadata-file.(ttl|jsonld|json-ld|json)> [--tier {1,2,3,4,all}]

Exit codes:
    0  Conforms (all checked tiers pass)
    1  Violations found in at least one tier
    2  Error (parse failure, missing file, etc.)
"""

import sys
import argparse
import pathlib
from datetime import datetime

try:
    import rdflib
    from rdflib import Graph
    from pyshacl import validate
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}\nRun: pip install rdflib pyshacl", file=sys.stderr)
    sys.exit(2)

# ── Path resolution ───────────────────────────────────────────────────────────
PROJ = pathlib.Path(__file__).parent.parent
SHAPES_DIR = PROJ / "shapes"

TIER_SHAPE_FILES = {
    1: SHAPES_DIR / "tier-1-findable.ttl",
    2: SHAPES_DIR / "tier-2-accessible-reusable.ttl",
    3: SHAPES_DIR / "tier-3-interoperable-schema.ttl",
    4: SHAPES_DIR / "tier-4-ai-ready.ttl",
}

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
    return FORMATS.get(path.suffix.lower(), "turtle")


def load_and_normalize(path: pathlib.Path, fmt: str | None = None) -> Graph:
    """Parse *path* and return a normalized schema.org graph.

    Normalization (src/profiles.normalize) remaps http://schema.org/ IRIs to
    https://schema.org/, maps dc:creator / schema:author → schema:creator,
    dcat:distribution → schema:distribution, etc., so the SHACL shapes (which
    all target https://schema.org/Dataset) can find their targets regardless of
    the source profile.
    """
    # Add project root to path so src.profiles can be imported
    if str(PROJ) not in sys.path:
        sys.path.insert(0, str(PROJ))
    from src.profiles import normalize  # lazy import avoids circular issues

    raw = Graph()
    raw.parse(str(path), format=fmt or detect_format(path))
    return normalize(raw)


def load_shapes(path: pathlib.Path) -> Graph:
    sg = Graph()
    sg.parse(str(path), format="turtle")
    return sg


def count_results(results_graph: Graph) -> dict:
    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    from rdflib.namespace import RDF
    violations = warnings = infos = 0
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        sev = results_graph.value(result, SH.resultSeverity)
        if sev == SH.Violation:
            violations += 1
        elif sev == SH.Warning:
            warnings += 1
        elif sev == SH.Info:
            infos += 1
    return {"violations": violations, "warnings": warnings, "infos": infos}


def run_tier(data_graph: Graph, shapes_path: pathlib.Path, tier_num: int) -> tuple:
    """Run pyshacl for one tier.  Returns (conforms, counts, results_text)."""
    sg = load_shapes(shapes_path)
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=sg,
        inference="none",
        abort_on_first=False,
        allow_warnings=True,
        meta_shacl=False,
        debug=False,
    )
    counts = count_results(results_graph)
    return conforms, counts, results_text


def emit_tier_report(tier_num: int, shapes_path: pathlib.Path,
                     conforms: bool, counts: dict, results_text: str) -> str:
    icon = "✓" if conforms else "✗"
    lines = [
        f"### Tier {tier_num} — {shapes_path.stem}",
        f"- **Conforms**: {'YES ' + icon if conforms else 'NO ' + icon}",
        f"- **Violations**: {counts['violations']}  "
        f"**Warnings**: {counts['warnings']}  **Infos**: {counts['infos']}",
        "",
        "```",
        results_text.strip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate a dataset metadata file against the FAIR-AI-Readiness tier "
            "SHACL shapes. Input is normalised to schema.org before validation."
        )
    )
    parser.add_argument("data", help="Path to dataset metadata file (TTL, JSON-LD, …)")
    parser.add_argument(
        "--tier", "-t",
        default="all",
        choices=["1", "2", "3", "4", "all"],
        help="Tier to validate against (default: all). "
             "Tiers are checked independently; cumulative logic is in the study layer.",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write report to this path (default: print to stdout)",
    )
    parser.add_argument(
        "--format", default=None,
        help="Force RDF format (turtle, json-ld, n3, xml, nt). Auto-detected by default.",
    )
    parser.add_argument(
        "--no-normalize", action="store_true",
        help="Skip normalization (advanced: use only with pre-normalized https://schema.org/ graphs).",
    )
    args = parser.parse_args()

    data_path = pathlib.Path(args.data)
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(2)

    # Parse and optionally normalize
    try:
        if args.no_normalize:
            data_graph = Graph()
            data_graph.parse(str(data_path), format=args.format or detect_format(data_path))
        else:
            data_graph = load_and_normalize(data_path, fmt=args.format)
    except Exception as e:
        print(f"ERROR: Could not parse/normalize '{data_path}': {e}", file=sys.stderr)
        sys.exit(2)

    # Select tiers
    tiers_to_check = [1, 2, 3, 4] if args.tier == "all" else [int(args.tier)]

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    report_lines = [
        "# FAIR-AI-Readiness — Tier Validation Report",
        "",
        f"- **Data file**: `{data_path}`",
        f"- **Validated at**: {now}",
        f"- **Tiers checked**: {', '.join(f'T{t}' for t in tiers_to_check)}",
        f"- **Normalised**: {'yes (http→https schema.org; profile aliases)' if not args.no_normalize else 'no'}",
        "",
        "## Results",
        "",
    ]

    overall_conforms = True
    for t in tiers_to_check:
        shapes_path = TIER_SHAPE_FILES[t]
        if not shapes_path.exists():
            print(f"ERROR: Shapes file not found: {shapes_path}", file=sys.stderr)
            sys.exit(2)
        try:
            conforms, counts, results_text = run_tier(data_graph, shapes_path, t)
        except Exception as e:
            print(f"ERROR: SHACL validation failed for Tier {t}: {e}", file=sys.stderr)
            sys.exit(2)

        if not conforms:
            overall_conforms = False
        report_lines.append(emit_tier_report(t, shapes_path, conforms, counts, results_text))

    # Summary line
    tier_labels = " ".join(
        f"T{t}:{'PASS' if True else 'FAIL'}" for t in tiers_to_check
    )
    report_lines += [
        "## Summary",
        "",
        f"- **Overall**: {'CONFORMS ✓' if overall_conforms else 'VIOLATIONS FOUND ✗'}",
        "",
    ]

    report = "\n".join(report_lines)
    if args.output:
        pathlib.Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to: {args.output}")
    else:
        print(report)

    sys.exit(0 if overall_conforms else 1)


if __name__ == "__main__":
    main()
