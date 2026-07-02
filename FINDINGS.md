# Findings — FAIR-AI-Readiness of 1,738 real biomedical datasets

**Analysis date:** 2026-07-02. **Corpus:** 1,738 real public datasets, fetched live and normalized (100%): **Dryad 340, EMBL-EBI BioStudies 798, PRIDE/ProteomeXchange 600**. Provenance in `data/corpus/manifest.json` and `CORPUS_REPORT.md`. Full results + figures in `results_deep/`. Every number is computed, not asserted.

## Tier conformance

| Tier | Overall | BioStudies (798) | Dryad (340) | PRIDE (600) |
|---|---|---|---|---|
| T1 Findable (PID, title, description) | **99.9%** | 100% | 99.7% | 100% |
| T2 Accessible + Reusable (distribution, creator, date) | **91.3%** | 81.1% | 99.7% | 100% |
| T3 Interoperable + schema-structured (schema, version, controlled subject) | **0.0%** | 0% | 0% | 0% |
| T4 AI-ready (checksums, provenance, data dictionary, ethics, sample count) | **0.0%** | 0% | 0% | 0% |

Tiers are cumulative (T2 requires T1, etc.). Findability is anchored on a persistent identifier + title + description; keywords and licence are reported as sub-metrics (Warnings), not tier gates.

## Where FAIR breaks (100% failure across all 1,738 unless noted)

- **Machine-readable schema** (`variableMeasured`): 100% absent
- **Provenance** (`prov:wasGeneratedBy`): 100% absent
- **Checksums**: 100% absent
- **Data dictionary** (`hasPart`): 99.9% absent
- **Ethics/IRB, sample count, access conditions, contact point, catalogue registration**: 100% absent
- **Version**: 80.4% absent · **Language**: 80.5% absent

## The point

Datasets are overwhelmingly **findable** and mostly **accessible**, but **none is interoperable or AI-ready**. The FAIR promise fails precisely at the machine-readable structural and provenance layer that automated assembly, trust, and AI reuse depend on. A deposited dataset is not a reusable data product. This repository makes that gap measurable (the tiered SHACL contract + validator) and closeable.

*Method note: BioStudies exposes downloadable files as counts + a predictable EBI files endpoint (not per-file schema.org distributions); we map studies with files to a machine-readable distribution, which is why ~19% of BioStudies studies (those with zero files in the basic record) do not reach T2. Licence and keyword coverage are reported as sub-metrics, not gates.*
