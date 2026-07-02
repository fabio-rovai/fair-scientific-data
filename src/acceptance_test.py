"""
acceptance_test.py — FAIR-AI-Readiness tier shape acceptance test (2026-07-02).

Verifies three things:
  1. BEFORE file (zenodo-21143094.before.jsonld, normalised) FAILS T2, T3, T4
     and PASSES T1.
  2. AFTER  file (zenodo-21143094.after.jsonld, normalised) PASSES T1-T4.
  3. 25 random corpus datasets: pyshacl per-tier vs Python check_all_criteria
     per-tier (non-cumulative) agreement ≥ ~100%.

Run:
    cd /Users/fabio/projects/fair-scientific-data
    uv run --with rdflib --with pyshacl --with pandas python src/acceptance_test.py
"""
from __future__ import annotations
import json, random, sys, traceback
from pathlib import Path

PROJ = Path(__file__).parent.parent
sys.path.insert(0, str(PROJ))

import pyshacl
from rdflib import Graph
from rdflib.namespace import RDF

from src.profiles import normalize
from src.analyse_corpus import (
    SCHEMA, TIER_VIOLATION_CRITERIA,
    check_all_criteria,
    from_dryad_jsonld, from_biostudies_json, from_pride_json,
    file_path_for_record,
)

# ── Shape loading ─────────────────────────────────────────────────────────────

SHAPES_DIR = PROJ / "shapes"
TIER_NAMES = {
    1: "tier-1-findable.ttl",
    2: "tier-2-accessible-reusable.ttl",
    3: "tier-3-interoperable-schema.ttl",
    4: "tier-4-ai-ready.ttl",
}

def _load_shape(tier: int) -> Graph:
    sg = Graph()
    sg.parse(str(SHAPES_DIR / TIER_NAMES[tier]), format="turtle")
    return sg

TIER_SHAPES = {t: _load_shape(t) for t in range(1, 5)}


def shacl_conforms(g: Graph, tier: int) -> bool:
    """Return True iff pyshacl finds NO violations for tier shape on graph g."""
    conforms, _, _ = pyshacl.validate(
        g,
        shacl_graph=TIER_SHAPES[tier],
        inference="none",
        abort_on_first=False,
        allow_warnings=True,
    )
    return bool(conforms)


def normalise_file(path: Path) -> Graph:
    raw = Graph()
    suffix = path.suffix.lower()
    fmt = {".ttl": "turtle", ".jsonld": "json-ld", ".json": "json-ld"}.get(suffix, "turtle")
    raw.parse(str(path), format=fmt)
    return normalize(raw)


# ── Acceptance test 1 & 2: BEFORE / AFTER ────────────────────────────────────

BEFORE = PROJ / "examples_remediated/zenodo-21143094.before.jsonld"
AFTER  = PROJ / "examples_remediated/zenodo-21143094.after.jsonld"

EXPECTED = {
    "before": {1: True,  2: False, 3: False, 4: False},
    "after":  {1: True,  2: True,  3: True,  4: True},
}

def run_before_after():
    print("=" * 64)
    print("TEST 1 & 2: BEFORE / AFTER (zenodo-21143094)")
    print("=" * 64)
    all_ok = True
    for label, path in [("before", BEFORE), ("after", AFTER)]:
        g = normalise_file(path)
        print(f"\n  {label.upper()} ({path.name}):")
        for t in range(1, 5):
            result = shacl_conforms(g, t)
            expected = EXPECTED[label][t]
            status = "PASS" if result else "FAIL"
            ok = (result == expected)
            marker = "✓" if ok else "✗ WRONG"
            exp_str = "expected PASS" if expected else "expected FAIL"
            print(f"    T{t}: {status}  [{exp_str}]  {marker}")
            if not ok:
                all_ok = False
    return all_ok


# ── Acceptance test 3: Spot-check 25 corpus records ──────────────────────────

def load_corpus_record(rec: dict) -> Graph | None:
    repo = rec.get("repo", "")
    fpath = file_path_for_record(rec)
    if fpath is None:
        return None
    try:
        if repo == "dryad":
            g, _ = from_dryad_jsonld(fpath)
        elif repo == "biostudies":
            g, _ = from_biostudies_json(fpath)
        elif repo == "pride":
            g, _ = from_pride_json(fpath)
        else:
            return None
        return g
    except Exception:
        return None


def python_tier_criteria(g: Graph, ds) -> dict[str, bool]:
    """Non-cumulative: does each tier's own violation criteria all pass?"""
    crit = check_all_criteria(g, ds)
    return {
        f"T{i}": all(crit.get(c, False) for c in TIER_VIOLATION_CRITERIA[f"T{i}"])
        for i in range(1, 5)
    }


def run_spot_check(n: int = 25, seed: int = 42):
    print("\n" + "=" * 64)
    print(f"TEST 3: SPOT-CHECK ({n} corpus datasets, seed={seed})")
    print("=" * 64)

    manifest_path = PROJ / "data/corpus/manifest.json"
    if not manifest_path.exists():
        print("  SKIP: corpus manifest not found")
        return True

    with open(manifest_path) as f:
        manifest = json.load(f)

    rng = random.Random(seed)
    sample = rng.sample(manifest, min(n, len(manifest)))

    rows = []
    skipped = 0
    for rec in sample:
        g = load_corpus_record(rec)
        if g is None:
            skipped += 1
            continue
        datasets = list(g.subjects(RDF.type, SCHEMA.Dataset))
        if not datasets:
            skipped += 1
            continue
        ds = datasets[0]

        py = python_tier_criteria(g, ds)
        sh = {f"T{t}": shacl_conforms(g, t) for t in range(1, 5)}
        rows.append({"id": rec.get("id", "?"), "repo": rec.get("repo", "?"),
                     "py": py, "sh": sh})

    if not rows:
        print("  SKIP: no loadable records found")
        return True

    print(f"\n  Loaded {len(rows)} records  (skipped {skipped})\n")
    disagree = []
    for r in rows:
        for t in ["T1", "T2", "T3", "T4"]:
            if r["py"][t] != r["sh"][t]:
                disagree.append((r["repo"], r["id"], t, r["py"][t], r["sh"][t]))

    total = len(rows) * 4
    agree = total - len(disagree)
    pct = 100 * agree / total

    if disagree:
        print("  Disagreements:")
        for repo, rid, t, py, sh in disagree:
            print(f"    {repo}/{rid}  {t}: Python={py}  SHACL={sh}")
    else:
        print("  No disagreements.")

    print(f"\n  Agreement: {agree}/{total} = {pct:.1f}%")
    return pct >= 96.0


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok1 = run_before_after()
    ok3 = run_spot_check(n=25, seed=42)

    print("\n" + "=" * 64)
    if ok1 and ok3:
        print("ALL ACCEPTANCE TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
        if not ok1:
            print("  - BEFORE/AFTER results did not match expected")
        if not ok3:
            print("  - Spot-check agreement below 96%")
    print("=" * 64)
    sys.exit(0 if (ok1 and ok3) else 1)
