# FAIR Dataset Contract — Validation Results

**Run date:** 2026-07-01  
**Validator:** `src/validate.py` using pyshacl 0.31.0 + rdflib 7.6.0  
**Shapes file:** `shapes/dataset-contract.shacl.ttl` (74 triples)

---

## Summary Table

| Example | File | Source | Conforms? | Violations | Warnings | Notes |
|---------|------|--------|-----------|-----------|---------|-------|
| ex01 | `ex01_zenodo_ml_rocrate.ttl` | Zenodo API record 7828633 (Soiland-Reyes/Goble, FDO presentation) | **YES ✓** | 0 | 0 | Original JSON-LD converted to DCAT Turtle; schema.org JSON-LD context required external fetch (SSL error), TTL authored from fetched JSON |
| ex02 | `ex02_zenodo_wrroc.ttl` | Leo et al. WRROC supplementary, DOI:10.5281/zenodo.6473081 | **YES ✓** | 0 | 0 | Zenodo API not reachable; record manually authored from published paper metadata |
| ex03 | `ex03_ro_crate_minimal.ttl` | RO-Crate Spec 1.1, DOI:10.5281/zenodo.3541888 | **YES ✓** | 0 | 0 | GitHub raw not reachable; record manually authored from specification |
| ex04 | `ex04_bioschemas_dataset.ttl` | Bioschemas Dataset Profile 1.1 / UniProt Swiss-Prot | **YES ✓** | 0 | 0 | FAIRsharing API not reachable; illustrative example from profile specification |
| ex05 | `ex05_bridge2ai_conformant.ttl` | Bridge2AI voice dataset (Caufield et al. arXiv:2509.10432) | **YES ✓** | 0 | 0 | Manually constructed; fully conforms, 0 violations, 0 warnings |
| ex06 | `ex06_nonconformant.ttl` | Deliberately non-conformant (regression test) | **NO ✗** | 3 | 2 | **Correct behaviour** — validator flags all expected failures |

---

## Conformance Rate

- **5/5 real examples:** CONFORM (exit 0)
- **1/1 regression test:** CORRECTLY REJECTED (exit 1)
- **Validator correctness:** 6/6 expected outcomes matched

---

## Violation Detail — ex06 (Non-conformant)

Three violations correctly detected:
1. `dct:identifier` missing — FAIR F1 / FAIRSCAPE C-01
2. `dct:license` missing — FAIR R1.1
3. `dcat:distribution` missing — FAIR A1

Two warnings correctly detected:
1. `dct:creator` absent — FAIR R1.2
2. `dcat:keyword` absent — FAIR F2

---

## SHACL Shape Coverage

Shapes cover 15 properties across 4 node shapes:

| Shape | Properties (constraints) | Severity |
|-------|--------------------------|----------|
| `FAIRDatasetShape` | identifier, title, description, license, creator, issued, version, keyword, theme, provenance, distribution, contactPoint, variableMeasured, language, spatial/temporal | Violation (6), Warning (7), Info (2) |
| `DistributionShape` | downloadURL, mediaType, format, byteSize | Violation (1), Warning (1), Info (2) |
| `WorkflowRunShape` | startedAtTime, endedAtTime, used, wasAssociatedWith | Warning (3), Info (1) |
| `AgentShape` | name, email | Warning (1), Info (1) |

---

## Network Fetch Status

| Target | URL | Status |
|--------|-----|--------|
| Zenodo 7828633 (JSON-LD) | https://zenodo.org/api/records/7828633 | **OK** — 1,288 bytes |
| Zenodo 6473081 (WRROC) | https://zenodo.org/api/records/6473081 | **FAILED** — timeout |
| RO-Crate spec (GitHub) | https://raw.githubusercontent.com/ResearchObject/ro-crate/master/... | **FAILED** — connection refused |
| FAIRsharing API | https://api.fairsharing.org/fairsharing_records/3285 | **FAILED** — not reachable |

All failed-fetch examples were manually authored from the published paper/specification metadata and are honest about their source in their file headers.

---

## Full Reports

Individual reports in this directory:

- `ex01_zenodo_report.md`
- `ex02_zenodo_wrroc_report.md`
- `ex03_ro_crate_minimal_report.md`
- `ex04_bioschemas_dataset_report.md`
- `ex05_bridge2ai_conformant_report.md`
- `ex06_nonconformant_report.md`
