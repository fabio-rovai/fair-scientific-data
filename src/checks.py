"""
checks.py — Python-level FAIR-AI-Readiness checks for criteria not expressible in SHACL.

SHACL can check structural metadata (property presence, cardinality, datatype, pattern).
These Python checks cover semantic / content-level criteria from:
  FAIRSCAPE 28 AI-readiness criteria — Al Manir/Clark, bioRxiv:2024.12.23.629818
  Bridge2AI metadata dimensions — Caufield et al., arXiv:2509.10432

Criteria requiring Python checks (SHACL-expressible vs Python split noted in FAIRSCAPE_CRITERIA_MAP.md):
  F1  — DOI/PID format validity (SHACL checks presence; Python checks format)
  A1  — Access protocol is http(s) (SHACL pattern; Python verifies scheme semantics)
  R1.1 — License IRI is a recognised open licence
  C4  — Checksum format validity (64-char hex for SHA-256; SPDX checksum algorithm)
  C7  — Statistical summary keywords present in description
  C8  — Ethics/IRB/consent keywords present in conditionsOfAccess
  C11 — Sample count is a positive integer (SHACL checks type; Python checks value)
  C12 — Completeness/missingness keywords present in description
  C13 — De-identification keywords present in conditionsOfAccess

Usage:
    from src.checks import run_all_checks
    results = run_all_checks(graph)
    for r in results:
        print(r)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

SCHEMA = Namespace("https://schema.org/")
PROV   = Namespace("http://www.w3.org/ns/prov#")
SPDX   = Namespace("http://spdx.org/rdf/terms#")

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    criterion: str          # e.g. "F1", "C4", "R1.1"
    passed: bool
    severity: str           # "error" | "warning" | "info"
    message: str
    subject: str = ""       # dataset IRI/BNode label
    citation: str = ""


@dataclass
class CheckReport:
    dataset: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def errors(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed and r.severity == "error"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed and r.severity == "warning"]

    @property
    def passed(self) -> list[CheckResult]:
        return [r for r in self.results if r.passed]

    def summary(self) -> str:
        total = len(self.results)
        ok = len(self.passed)
        err = len(self.errors)
        warn = len(self.warnings)
        return (
            f"Dataset: {self.dataset}\n"
            f"  Passed: {ok}/{total}  Errors: {err}  Warnings: {warn}\n"
            + "\n".join(
                f"  [{'PASS' if r.passed else r.severity.upper()}] {r.criterion}: {r.message}"
                for r in self.results
            )
        )


# ---------------------------------------------------------------------------
# Known open licences (SPDX expressions and canonical URLs)
# ---------------------------------------------------------------------------

KNOWN_OPEN_LICENCES = {
    # Creative Commons
    "https://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by/4.0",
    "https://creativecommons.org/licenses/by-sa/4.0/",
    "https://creativecommons.org/licenses/by-nc/4.0/",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "https://creativecommons.org/licenses/by/3.0/",
    "http://creativecommons.org/licenses/by/4.0/",
    "http://creativecommons.org/publicdomain/zero/1.0/",
    # Open Data
    "https://opendatacommons.org/licenses/odbl/1-0/",
    "https://opendatacommons.org/licenses/by/1-0/",
    "https://opendatacommons.org/licenses/pddl/1-0/",
    # Code licences (sometimes applied to datasets)
    "https://opensource.org/licenses/MIT",
    "https://opensource.org/licenses/Apache-2.0",
    "https://www.gnu.org/licenses/gpl-3.0.html",
}

# SPDX identifiers as partial matches (the IRI may contain these)
KNOWN_SPDX_FRAGMENTS = {
    "CC-BY", "CC0", "ODbL", "PDDL", "MIT", "Apache-2.0", "GPL",
    "creativecommons", "opendatacommons",
}

# Recognised PID patterns
DOI_PATTERN       = re.compile(r"^https?://doi\.org/10\.\d{4,}/\S+$")
HANDLE_PATTERN    = re.compile(r"^https?://hdl\.handle\.net/\d+/\S+$")
ARK_PATTERN       = re.compile(r"^https?://n2t\.net/ark:/\d+/\S+$")
ORCID_PATTERN     = re.compile(r"^https?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ROR_PATTERN       = re.compile(r"^https?://ror\.org/0[a-z0-9]{6}\d{2}$")

# Checksum
SHA256_PATTERN    = re.compile(r"^[0-9a-fA-F]{64}$")
MD5_PATTERN       = re.compile(r"^[0-9a-fA-F]{32}$")
SHA512_PATTERN    = re.compile(r"^[0-9a-fA-F]{128}$")

# Ethics keywords
ETHICS_KEYWORDS = {
    "irb", "institutional review board", "ethics committee", "informed consent",
    "consent", "ethical approval", "hipaa", "gdpr", "data protection",
    "privacy", "anonymi", "de-identif", "pseudonymous",
}

# Completeness keywords
COMPLETENESS_KEYWORDS = {
    "missing", "missing data", "completeness", "complete", "dropout",
    "missingness", "na values", "null", "nan", "percent available",
    "coverage", "data quality",
}

# De-identification keywords
DEIDENT_KEYWORDS = {
    "de-identif", "deidentif", "anonymi", "pseudonym",
    "hipaa safe harbor", "k-anonymity", "differential privacy",
    "redact", "suppres",
}

# Statistical summary keywords
STATS_KEYWORDS = {
    "mean", "median", "standard deviation", "std", "distribution",
    "histogram", "summary statistic", "descriptive statistic",
    "n=", "n =", "sample size", "quartile", "interquartile",
    "proportion", "percentage", "prevalence",
}


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def _get_datasets(g: Graph) -> list[URIRef | rdflib.BNode]:
    return list(g.subjects(RDF.type, SCHEMA.Dataset))


def check_f1_pid_format(g: Graph) -> list[CheckResult]:
    """F1: PID must be a recognised persistent identifier (DOI, ARK, Handle)."""
    results = []
    for ds in _get_datasets(g):
        identifiers = list(g.objects(ds, SCHEMA.identifier))
        if not identifiers:
            results.append(CheckResult(
                criterion="F1",
                passed=False,
                severity="error",
                message="No schema:identifier found. SHACL Tier-1 should have caught this.",
                subject=str(ds),
                citation="Wilkinson 2016 §F1; Al Manir 2024 criterion F1",
            ))
            continue
        recognised = False
        for ident in identifiers:
            s = str(ident)
            if DOI_PATTERN.match(s) or HANDLE_PATTERN.match(s) or ARK_PATTERN.match(s):
                recognised = True
                break
            # Also accept non-http PIDs as literals (DataCite publicationYear style)
            if re.match(r"^10\.\d{4,}/", s):
                recognised = True
                break
        results.append(CheckResult(
            criterion="F1",
            passed=recognised,
            severity="error" if not recognised else "info",
            message=(
                "PID recognised as DOI/ARK/Handle IRI."
                if recognised else
                f"Identifier '{identifiers[0]}' does not match DOI/ARK/Handle patterns. "
                "Use a resolvable https://doi.org/ IRI."
            ),
            subject=str(ds),
            citation="Wilkinson 2016 §F1; DataCite Schema 4.5 mandatory Identifier",
        ))
    return results


def check_a1_open_protocol(g: Graph) -> list[CheckResult]:
    """A1: Each distribution contentUrl must use http(s) (open, free, standard protocol)."""
    results = []
    for ds in _get_datasets(g):
        dists = list(g.objects(ds, SCHEMA.distribution))
        if not dists:
            continue
        for dist in dists:
            urls = list(g.objects(dist, SCHEMA.contentUrl))
            for url in urls:
                s = str(url)
                ok = s.startswith("http://") or s.startswith("https://")
                results.append(CheckResult(
                    criterion="A1",
                    passed=ok,
                    severity="error" if not ok else "info",
                    message=(
                        f"contentUrl '{s}' uses open http(s) protocol." if ok else
                        f"contentUrl '{s}' uses non-open protocol (expected https?://). FAIR A1."
                    ),
                    subject=str(ds),
                    citation="Wilkinson 2016 §A1; Al Manir 2024 criterion A1",
                ))
    return results


def check_r1_1_licence(g: Graph) -> list[CheckResult]:
    """R1.1: License IRI must be a recognised open licence."""
    results = []
    for ds in _get_datasets(g):
        licences = list(g.objects(ds, SCHEMA.license))
        if not licences:
            results.append(CheckResult(
                criterion="R1.1",
                passed=False,
                severity="error",
                message="No schema:license found.",
                subject=str(ds),
                citation="Wilkinson 2016 §R1.1; Al Manir 2024 criterion R1",
            ))
            continue
        for lic in licences:
            s = str(lic)
            known = s in KNOWN_OPEN_LICENCES or any(frag.lower() in s.lower() for frag in KNOWN_SPDX_FRAGMENTS)
            results.append(CheckResult(
                criterion="R1.1",
                passed=known,
                severity="warning" if not known else "info",
                message=(
                    f"License '{s}' is a recognised open licence." if known else
                    f"License '{s}' not in known open licence list. "
                    "If this is an open licence, add it to checks.KNOWN_OPEN_LICENCES."
                ),
                subject=str(ds),
                citation="Wilkinson 2016 §R1.1; SPDX licence list",
            ))
    return results


def check_c3_version_format(g: Graph) -> list[CheckResult]:
    """C3: Version string should follow semver or date-based convention."""
    SEMVER = re.compile(r"^\d+\.\d+(\.\d+)?([.-].+)?$")
    DATEVER = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
    results = []
    for ds in _get_datasets(g):
        versions = list(g.objects(ds, SCHEMA.version))
        if not versions:
            continue
        for v in versions:
            s = str(v)
            ok = bool(SEMVER.match(s) or DATEVER.match(s))
            results.append(CheckResult(
                criterion="C3",
                passed=ok,
                severity="warning" if not ok else "info",
                message=(
                    f"Version '{s}' matches semver/date convention." if ok else
                    f"Version '{s}' does not follow semver (X.Y.Z) or date (YYYY-MM-DD) convention."
                ),
                subject=str(ds),
                citation="Al Manir 2024 criterion C3 (data version identified); semver.org",
            ))
    return results


def check_c4_checksum(g: Graph) -> list[CheckResult]:
    """C4: Distributions must carry a checksum with valid format."""
    results = []
    for ds in _get_datasets(g):
        dists = list(g.objects(ds, SCHEMA.distribution))
        if not dists:
            continue
        for dist in dists:
            # Check spdx:checksum (node with spdx:checksumValue)
            spdx_checksums = list(g.objects(dist, SPDX.checksum))
            sha256_vals = list(g.objects(dist, SCHEMA.sha256))
            if not spdx_checksums and not sha256_vals:
                results.append(CheckResult(
                    criterion="C4",
                    passed=False,
                    severity="error",
                    message=f"Distribution '{dist}' has no checksum (spdx:checksum or schema:sha256).",
                    subject=str(ds),
                    citation="Al Manir 2024 criterion C4; Brewer 2025 arXiv:2507.23018 DRL-1",
                ))
                continue
            # Validate SHA-256 format if present
            for sha in sha256_vals:
                s = str(sha)
                ok = bool(SHA256_PATTERN.match(s))
                results.append(CheckResult(
                    criterion="C4",
                    passed=ok,
                    severity="error" if not ok else "info",
                    message=(
                        "SHA-256 checksum is a valid 64-char hex string." if ok else
                        f"schema:sha256 value '{s[:16]}…' is not a valid 64-char hex SHA-256."
                    ),
                    subject=str(ds),
                    citation="Al Manir 2024 criterion C4",
                ))
            # Validate SPDX checksum nodes
            for spdx_node in spdx_checksums:
                values = list(g.objects(spdx_node, SPDX.checksumValue))
                algos  = list(g.objects(spdx_node, SPDX.algorithm))
                if not values:
                    results.append(CheckResult(
                        criterion="C4",
                        passed=False,
                        severity="error",
                        message="spdx:checksum node has no spdx:checksumValue.",
                        subject=str(ds),
                        citation="Al Manir 2024 criterion C4; SPDX spec §4.4",
                    ))
                    continue
                for val in values:
                    v = str(val)
                    algo = str(algos[0]) if algos else ""
                    if "sha256" in algo.lower() or "sha-256" in algo.lower():
                        ok = bool(SHA256_PATTERN.match(v))
                    elif "md5" in algo.lower():
                        ok = bool(MD5_PATTERN.match(v))
                    elif "sha512" in algo.lower():
                        ok = bool(SHA512_PATTERN.match(v))
                    else:
                        ok = bool(re.match(r"^[0-9a-fA-F]+$", v))
                    results.append(CheckResult(
                        criterion="C4",
                        passed=ok,
                        severity="error" if not ok else "info",
                        message=(
                            f"SPDX checksum value valid (algo={algo})." if ok else
                            f"SPDX checksum value '{v[:16]}…' invalid hex for algo={algo}."
                        ),
                        subject=str(ds),
                        citation="Al Manir 2024 criterion C4; SPDX RDF spec",
                    ))
    return results


def check_c7_stats_summary(g: Graph) -> list[CheckResult]:
    """C7: Description should mention statistical summary terms."""
    results = []
    for ds in _get_datasets(g):
        texts: list[str] = []
        for obj in list(g.objects(ds, SCHEMA.description)) + list(g.objects(ds, SCHEMA.abstract)):
            texts.append(str(obj).lower())
        combined = " ".join(texts)
        found = [kw for kw in STATS_KEYWORDS if kw in combined]
        ok = len(found) >= 2
        results.append(CheckResult(
            criterion="C7",
            passed=ok,
            severity="warning" if not ok else "info",
            message=(
                f"Statistical summary keywords found: {found}." if ok else
                "Description lacks statistical summary terms (mean, n=, distribution, etc.). "
                "Add a characterisation section. FAIRSCAPE C7."
            ),
            subject=str(ds),
            citation="Al Manir 2024 criterion C7 (statistical summary); Bridge2AI D3",
        ))
    return results


def check_c8_ethics_consent(g: Graph) -> list[CheckResult]:
    """C8: conditionsOfAccess or description must contain ethics/consent keywords."""
    results = []
    for ds in _get_datasets(g):
        texts: list[str] = []
        for pred in [SCHEMA.conditionsOfAccess, SCHEMA.description]:
            for obj in g.objects(ds, pred):
                texts.append(str(obj).lower())
        combined = " ".join(texts)
        found = [kw for kw in ETHICS_KEYWORDS if kw in combined]
        ok = len(found) >= 1
        results.append(CheckResult(
            criterion="C8",
            passed=ok,
            severity="error" if not ok else "info",
            message=(
                f"Ethics/consent keywords found: {found}." if ok else
                "No ethics/IRB/consent keywords detected in conditionsOfAccess or description. "
                "Add IRB approval number, consent type, or 'not applicable' statement."
            ),
            subject=str(ds),
            citation="Al Manir 2024 criterion C8 (ethics/IRB/consent); Bridge2AI D5; Caufield 2025",
        ))
    return results


def check_c11_sample_count(g: Graph) -> list[CheckResult]:
    """C11: numberOfItems must be a positive integer."""
    results = []
    for ds in _get_datasets(g):
        counts = list(g.objects(ds, SCHEMA.numberOfItems))
        if not counts:
            continue
        for c in counts:
            try:
                n = int(str(c))
                ok = n > 0
            except ValueError:
                ok = False
                n = None
            results.append(CheckResult(
                criterion="C11",
                passed=ok,
                severity="error" if not ok else "info",
                message=(
                    f"Sample count {n} is a positive integer." if ok else
                    f"numberOfItems '{c}' is not a positive integer."
                ),
                subject=str(ds),
                citation="Al Manir 2024 criterion C11 (sample count); Bridge2AI D3",
            ))
    return results


def check_c12_completeness(g: Graph) -> list[CheckResult]:
    """C12: Description should mention data completeness or missingness."""
    results = []
    for ds in _get_datasets(g):
        texts = [str(obj).lower() for obj in g.objects(ds, SCHEMA.description)]
        combined = " ".join(texts)
        found = [kw for kw in COMPLETENESS_KEYWORDS if kw in combined]
        ok = len(found) >= 1
        results.append(CheckResult(
            criterion="C12",
            passed=ok,
            severity="warning" if not ok else "info",
            message=(
                f"Completeness keywords found: {found}." if ok else
                "Description does not mention data completeness or missingness. "
                "Needed for AI training suitability assessment (FAIRSCAPE C12)."
            ),
            subject=str(ds),
            citation="Al Manir 2024 criterion C12 (completeness/missingness); Bridge2AI D3",
        ))
    return results


def check_c13_deidentification(g: Graph) -> list[CheckResult]:
    """C13: conditionsOfAccess or description must mention de-identification method."""
    results = []
    for ds in _get_datasets(g):
        texts: list[str] = []
        for pred in [SCHEMA.conditionsOfAccess, SCHEMA.description]:
            for obj in g.objects(ds, pred):
                texts.append(str(obj).lower())
        combined = " ".join(texts)
        found = [kw for kw in DEIDENT_KEYWORDS if kw in combined]
        ok = len(found) >= 1
        results.append(CheckResult(
            criterion="C13",
            passed=ok,
            severity="warning" if not ok else "info",
            message=(
                f"De-identification keywords found: {found}." if ok else
                "No de-identification method mentioned. Add a statement such as "
                "'HIPAA Safe Harbor' or 'not applicable for non-human data'."
            ),
            subject=str(ds),
            citation="Al Manir 2024 criterion C13 (de-identification); Bridge2AI D5",
        ))
    return results


def check_r1_2_creator_orcid(g: Graph) -> list[CheckResult]:
    """R1.2: At least one creator should have an ORCID IRI identifier."""
    results = []
    for ds in _get_datasets(g):
        creators = list(g.objects(ds, SCHEMA.creator))
        if not creators:
            continue
        has_orcid = False
        for creator in creators:
            for ident in g.objects(creator, SCHEMA.identifier):
                if ORCID_PATTERN.match(str(ident)):
                    has_orcid = True
                    break
        results.append(CheckResult(
            criterion="R1.2",
            passed=has_orcid,
            severity="warning" if not has_orcid else "info",
            message=(
                "At least one creator has an ORCID identifier." if has_orcid else
                "No creator has an ORCID IRI (https://orcid.org/XXXX-XXXX-XXXX-XXXX). "
                "Strongly recommended for R1.2 provenance. DataCite nameIdentifier."
            ),
            subject=str(ds),
            citation="Wilkinson 2016 §R1.2; DataCite Schema 4.5 nameIdentifier; Al Manir 2024 criterion R2",
        ))
    return results


# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------

CHECK_FUNCTIONS = [
    check_f1_pid_format,
    check_a1_open_protocol,
    check_r1_1_licence,
    check_r1_2_creator_orcid,
    check_c3_version_format,
    check_c4_checksum,
    check_c7_stats_summary,
    check_c8_ethics_consent,
    check_c11_sample_count,
    check_c12_completeness,
    check_c13_deidentification,
]


def run_all_checks(g: Graph) -> list[CheckReport]:
    """
    Run all Python-level FAIR-AI-Readiness checks on a normalized graph.
    Returns one CheckReport per dataset node found in the graph.
    """
    datasets = _get_datasets(g)
    if not datasets:
        return [CheckReport(
            dataset="(none)",
            results=[CheckResult(
                criterion="meta",
                passed=False,
                severity="error",
                message="No schema:Dataset found in graph. Did you run profiles.normalize() first?",
            )]
        )]

    reports = []
    for ds in datasets:
        report = CheckReport(dataset=str(ds))
        for fn in CHECK_FUNCTIONS:
            # Filter to results for this dataset only
            all_results = fn(g)
            for r in all_results:
                if r.subject == str(ds) or r.subject == "":
                    report.results.append(r)
        reports.append(report)
    return reports


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.profiles import load_and_normalize

    if len(sys.argv) < 2:
        print("Usage: python src/checks.py <metadata-file>")
        sys.exit(1)

    g = load_and_normalize(Path(sys.argv[1]))
    reports = run_all_checks(g)
    for rep in reports:
        print(rep.summary())
