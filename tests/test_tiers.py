"""
tests/test_tiers.py — FAIR-AI-Readiness tier validation tests.

Validates that each tier SHACL shape discriminates correctly:
  - conformant fixtures produce zero Violations for that tier
  - non-conformant fixtures produce ≥1 Violations for that tier

Run with:
    uv run --with rdflib --with pyshacl pytest tests/test_tiers.py -v

Or standalone:
    uv run --with rdflib --with pyshacl python tests/test_tiers.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from any directory
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from rdflib import Graph, Namespace
from rdflib.namespace import RDF
import pyshacl

SCHEMA = Namespace("https://schema.org/")

SHAPES_DIR   = ROOT / "shapes"
FIXTURES_DIR = ROOT / "tests" / "fixtures"

TIER_SHAPES = {
    "T1": SHAPES_DIR / "tier-1-findable.ttl",
    "T2": SHAPES_DIR / "tier-2-accessible-reusable.ttl",
    "T3": SHAPES_DIR / "tier-3-interoperable-schema.ttl",
    "T4": SHAPES_DIR / "tier-4-ai-ready.ttl",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load(path: Path, fmt: str = "turtle") -> Graph:
    g = Graph()
    g.parse(str(path), format=fmt)
    return g


def count_violations(results_graph: Graph) -> int:
    SH = Namespace("http://www.w3.org/ns/shacl#")
    count = 0
    for _ in results_graph.subjects(RDF.type, SH.ValidationResult):
        severity = results_graph.value(_, SH.resultSeverity)
        if severity == SH.Violation:
            count += 1
    return count


def validate(data_path: Path, shapes_path: Path) -> tuple[bool, int, str]:
    """Return (conforms, violation_count, result_text)."""
    data_g   = load(data_path)
    shapes_g = load(shapes_path)
    conforms, results_g, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shapes_g,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        debug=False,
    )
    return conforms, count_violations(results_g), results_text


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestTier1:
    """FAIR F1–F4: PID, title, description, keywords."""

    def test_shapes_parse(self):
        g = load(TIER_SHAPES["T1"])
        assert len(g) > 0, "T1 shapes must not be empty"

    def test_conformant_has_zero_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t1_conformant.ttl", TIER_SHAPES["T1"])
        assert n == 0, f"T1 conformant fixture should have 0 Violations, got {n}:\n{text}"

    def test_nonconformant_has_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t1_nonconformant.ttl", TIER_SHAPES["T1"])
        # Missing: identifier, name, keywords → expect ≥3 Violations
        assert n >= 3, f"T1 non-conformant should have ≥3 Violations (PID, name, keywords), got {n}:\n{text}"

    def test_t2_conformant_also_passes_t1(self):
        _, n, _ = validate(FIXTURES_DIR / "t2_conformant.ttl", TIER_SHAPES["T1"])
        assert n == 0, f"T2 conformant should also pass T1 (0 violations), got {n}"

    def test_t4_conformant_passes_t1(self):
        _, n, _ = validate(FIXTURES_DIR / "t4_conformant.ttl", TIER_SHAPES["T1"])
        assert n == 0, f"T4 conformant should pass T1, got {n} violations"


class TestTier2:
    """FAIR A1/A2/R1–R1.2: license, distribution, creator, date."""

    def test_shapes_parse(self):
        g = load(TIER_SHAPES["T2"])
        assert len(g) > 0

    def test_conformant_has_zero_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t2_conformant.ttl", TIER_SHAPES["T2"])
        assert n == 0, f"T2 conformant fixture should have 0 Violations, got {n}:\n{text}"

    def test_nonconformant_has_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t2_nonconformant.ttl", TIER_SHAPES["T2"])
        # Missing: license, distribution, creator, datePublished → ≥4 Violations
        assert n >= 4, f"T2 non-conformant should have ≥4 Violations, got {n}:\n{text}"

    def test_t1_only_fails_t2(self):
        _, n, _ = validate(FIXTURES_DIR / "t1_conformant.ttl", TIER_SHAPES["T2"])
        # T1 fixture has no license/distribution/creator → should have T2 violations
        assert n >= 3, f"T1-only fixture should fail T2 with ≥3 violations, got {n}"

    def test_t4_conformant_passes_t2(self):
        _, n, _ = validate(FIXTURES_DIR / "t4_conformant.ttl", TIER_SHAPES["T2"])
        assert n == 0, f"T4 conformant should pass T2, got {n} violations"


class TestTier3:
    """FAIR I1–I3/R1.3: controlled vocab, variableMeasured, version."""

    def test_shapes_parse(self):
        g = load(TIER_SHAPES["T3"])
        assert len(g) > 0

    def test_conformant_has_zero_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t3_conformant.ttl", TIER_SHAPES["T3"])
        assert n == 0, f"T3 conformant fixture should have 0 Violations, got {n}:\n{text}"

    def test_nonconformant_has_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t3_nonconformant.ttl", TIER_SHAPES["T3"])
        # Missing: schema:about IRI, variableMeasured, version → ≥3 Violations
        assert n >= 3, f"T3 non-conformant should have ≥3 Violations, got {n}:\n{text}"

    def test_t2_only_fails_t3(self):
        _, n, _ = validate(FIXTURES_DIR / "t2_conformant.ttl", TIER_SHAPES["T3"])
        assert n >= 2, f"T2-only fixture should fail T3 with ≥2 violations, got {n}"

    def test_t4_conformant_passes_t3(self):
        _, n, _ = validate(FIXTURES_DIR / "t4_conformant.ttl", TIER_SHAPES["T3"])
        assert n == 0, f"T4 conformant should pass T3, got {n} violations"


class TestTier4:
    """FAIRSCAPE C1–C13: AI-readiness (data type, checksum, dict, ethics, pipeline provenance)."""

    def test_shapes_parse(self):
        g = load(TIER_SHAPES["T4"])
        assert len(g) > 0

    def test_conformant_has_zero_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t4_conformant.ttl", TIER_SHAPES["T4"])
        assert n == 0, f"T4 conformant fixture should have 0 Violations, got {n}:\n{text}"

    def test_nonconformant_has_violations(self):
        _, n, text = validate(FIXTURES_DIR / "t4_nonconformant.ttl", TIER_SHAPES["T4"])
        # Missing: additionalType, checksum, hasPart, conditionsOfAccess, wasGeneratedBy, numberOfItems
        assert n >= 5, f"T4 non-conformant should have ≥5 Violations, got {n}:\n{text}"

    def test_t3_only_fails_t4(self):
        _, n, _ = validate(FIXTURES_DIR / "t3_conformant.ttl", TIER_SHAPES["T4"])
        assert n >= 3, f"T3-only fixture should fail T4 with ≥3 violations, got {n}"


class TestNormalizerSanity:
    """profiles.py normalizer produces schema:Dataset with canonical predicates."""

    def test_normalizer_imports(self):
        from src.profiles import normalize, load_and_normalize
        assert callable(normalize)
        assert callable(load_and_normalize)

    def test_dcat_normalized_to_schema(self):
        from rdflib.namespace import DCTERMS, OWL
        DCAT = Namespace("http://www.w3.org/ns/dcat#")
        from src.profiles import normalize

        g = Graph()
        ds = SCHEMA["testDataset"]
        g.add((ds, RDF.type, DCAT.Dataset))
        g.add((ds, DCTERMS.title, __import__("rdflib").Literal("Test", datatype=__import__("rdflib").namespace.XSD.string)))
        g.add((ds, DCTERMS.creator, __import__("rdflib").URIRef("https://orcid.org/0000-0001-0000-0000")))
        g.add((ds, DCAT.keyword, __import__("rdflib").Literal("test")))
        g.add((ds, OWL.versionInfo, __import__("rdflib").Literal("1.0")))

        out = normalize(g)

        # DCAT.Dataset → schema:Dataset
        assert (ds, RDF.type, SCHEMA.Dataset) in out, "dcat:Dataset should map to schema:Dataset"
        # dct:title → schema:name
        assert any(str(o) == "Test" for o in out.objects(ds, SCHEMA.name)), "dct:title should map to schema:name"
        # dct:creator → schema:creator
        assert any(True for _ in out.objects(ds, SCHEMA.creator)), "dct:creator should map to schema:creator"
        # dcat:keyword → schema:keywords
        assert any(True for _ in out.objects(ds, SCHEMA.keywords)), "dcat:keyword should map to schema:keywords"
        # owl:versionInfo → schema:version
        assert any(str(o) == "1.0" for o in out.objects(ds, SCHEMA.version)), "owl:versionInfo → schema:version"

    def test_schema_http_remapped_to_https(self):
        from src.profiles import normalize
        SCHEMA_H = Namespace("http://schema.org/")

        g = Graph()
        ds = __import__("rdflib").URIRef("https://example.org/ds")
        g.add((ds, RDF.type, SCHEMA_H.Dataset))
        g.add((ds, SCHEMA_H.name, __import__("rdflib").Literal("HTTP Schema Test")))

        out = normalize(g)
        assert (ds, RDF.type, SCHEMA.Dataset) in out, "http://schema.org/Dataset → https://schema.org/Dataset"
        assert any(str(o) == "HTTP Schema Test" for o in out.objects(ds, SCHEMA.name))

    def test_author_mapped_to_creator(self):
        """schema:author (http) should normalize to schema:creator (https)."""
        from src.profiles import normalize
        SCHEMA_H = Namespace("http://schema.org/")

        g = Graph()
        ds = __import__("rdflib").URIRef("https://example.org/ds2")
        g.add((ds, RDF.type, SCHEMA_H.Dataset))
        agent = __import__("rdflib").BNode()
        g.add((agent, RDF.type, SCHEMA_H.Person))
        g.add((agent, SCHEMA_H.name, __import__("rdflib").Literal("Author Person")))
        g.add((ds, SCHEMA_H.author, agent))  # schema:author → schema:creator

        out = normalize(g)
        creators = list(out.objects(ds, SCHEMA.creator))
        assert len(creators) >= 1, "schema:author should be normalized to schema:creator"


class TestChecks:
    """Python-level checks for semantic FAIR-AI-Readiness criteria."""

    def _load_t4_normalized(self) -> Graph:
        from src.profiles import load_and_normalize
        return load_and_normalize(FIXTURES_DIR / "t4_conformant.ttl")

    def test_checks_import(self):
        from src.checks import run_all_checks
        assert callable(run_all_checks)

    def test_t4_conformant_passes_f1(self):
        from src.checks import check_f1_pid_format
        g = self._load_t4_normalized()
        results = check_f1_pid_format(g)
        assert len(results) > 0
        assert all(r.passed for r in results), \
            f"T4 fixture should pass F1 check: {[r.message for r in results if not r.passed]}"

    def test_t4_conformant_passes_r1_1(self):
        from src.checks import check_r1_1_licence
        g = self._load_t4_normalized()
        results = check_r1_1_licence(g)
        assert all(r.passed for r in results), \
            f"T4 fixture should have recognised CC-BY licence: {[r.message for r in results if not r.passed]}"

    def test_t4_conformant_passes_c8_ethics(self):
        from src.checks import check_c8_ethics_consent
        g = self._load_t4_normalized()
        results = check_c8_ethics_consent(g)
        assert all(r.passed for r in results), \
            f"T4 fixture should pass C8 ethics check: {[r.message for r in results if not r.passed]}"

    def test_t4_conformant_passes_c4_checksum(self):
        from src.checks import check_c4_checksum
        g = self._load_t4_normalized()
        results = check_c4_checksum(g)
        assert all(r.passed for r in results), \
            f"T4 fixture should pass C4 checksum check: {[r.message for r in results if not r.passed]}"

    def test_t4_conformant_passes_c11_sample_count(self):
        from src.checks import check_c11_sample_count
        g = self._load_t4_normalized()
        results = check_c11_sample_count(g)
        assert all(r.passed for r in results), \
            f"T4 fixture should pass C11 sample count check: {[r.message for r in results if not r.passed]}"

    def test_t1_fails_c8_ethics(self):
        """T1-only fixture should fail C8 (no ethics statement)."""
        from src.checks import check_c8_ethics_consent
        from src.profiles import load_and_normalize
        g = load_and_normalize(FIXTURES_DIR / "t1_conformant.ttl")
        results = check_c8_ethics_consent(g)
        assert any(not r.passed for r in results), \
            "T1-only fixture should fail C8 (no conditionsOfAccess with ethics keywords)"


# ---------------------------------------------------------------------------
# Standalone runner (not pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    PASS = "\033[92mPASS\033[0m"
    FAIL = "\033[91mFAIL\033[0m"

    test_classes = [TestTier1, TestTier2, TestTier3, TestTier4,
                    TestNormalizerSanity, TestChecks]
    total = 0
    passed = 0
    failed_tests: list[str] = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        print(f"\n{'='*60}")
        print(f"  {cls.__name__}")
        print(f"{'='*60}")
        for method in methods:
            total += 1
            try:
                getattr(instance, method)()
                print(f"  {PASS}  {method}")
                passed += 1
            except AssertionError as e:
                print(f"  {FAIL}  {method}")
                print(f"         {e}")
                failed_tests.append(f"{cls.__name__}.{method}: {e}")
            except Exception as e:
                print(f"  {FAIL}  {method} (ERROR)")
                traceback.print_exc()
                failed_tests.append(f"{cls.__name__}.{method}: {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} passed")
    if failed_tests:
        print(f"\n  Failures:")
        for f in failed_tests:
            print(f"    - {f}")
    print(f"{'='*60}\n")
    sys.exit(0 if passed == total else 1)
