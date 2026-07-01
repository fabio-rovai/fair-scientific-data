# Strictness analysis: are real scientific datasets "contract-ready"?

**Run date:** 2026-07-01. **Method:** 30 real public datasets (immune / single-cell / multi-omics / proteomics / spatial) were discovered via the Zenodo API (`type=dataset`), their schema.org metadata fetched by DOI content negotiation (`Accept: application/vnd.schemaorg.ld+json`, all HTTP 200, all `@type=Dataset`), and each validated with `pyshacl` against two contracts: a **minimal** contract (identity + description) and a **strict** hard-FAIR contract (adds machine-readable schema, distribution/access, licence, version, keywords, provenance).

Every DOI, title, HTTP status and per-dataset result is recorded in `results_real/fetch_log.json` and `results_real/strictness_analysis.json`. All numbers below are computed from that run.

## Headline

| Contract | Conforming | Rate |
|---|---|---|
| Minimal (catalogue-level) | 30 / 30 | **100%** |
| Strict (hard-FAIR, machine-readable) | 0 / 30 | **0%** |

**Every one of 30 real, published datasets is catalogued; none is contract-ready for automated reuse.**

## Where they fail (unambiguous fields)

| Requirement | Datasets missing it |
|---|---|
| `variableMeasured` (structured schema) | 100% (30/30) |
| `distribution` (machine-readable access) | 100% (30/30) |
| `version` | 73% (22/30) |
| `keywords` | 50% (15/30) |

## Honesty notes
- The strict shape also requires `schema:creator`; a share of the "missing creator" results reflect a `schema:creator` vs `schema:author` vocabulary mismatch in DataCite's schema.org export rather than truly absent provenance. The headline (0/30 strict-conform) holds on the unambiguous fields alone (`variableMeasured` and `distribution` are absent in 100% of records), so it does not depend on the creator field.
- This measures *published catalogue metadata*, not what may exist inside each dataset's files. The point is precisely that: reuse automation acts on the metadata, and the metadata is not contract-grade.

## So what
A dataset that is *findable* is not automatically *reusable*. For biotech/pharma R&D platforms building AI-ready data, the gap between "we deposited it" and "a machine can find, assemble, and trust it" is exactly this contract layer. The shapes, validator and readiness rubric in this repository make that gap measurable and closeable.
