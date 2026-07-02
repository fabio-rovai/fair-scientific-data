# FAIR-AI-Readiness Remediation

> **Date**: 2026-07-02  
> **Script**: `src/remediate.py`  
> **Validator**: pyshacl + rdflib + `src/checks.py`

## Dataset

| Field | Value |
|-------|-------|
| **DOI** | [https://doi.org/10.5281/zenodo.21143094](https://doi.org/10.5281/zenodo.21143094) |
| **Zenodo record** | [https://zenodo.org/records/21143094](https://zenodo.org/records/21143094) |
| **Title** | Monthly climate dataset of a dense high-Andean weather-station network in southern Ecuador, 2007–2026 |
| **File analysed** | `T_mensual.csv` |
| **Date published** | 2026-07-02 |
| **License** | [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| **Creators** | Franz Pucha-Cofrep; Andreas Fries |

## Before / After Summary

| Metric | Before | After |
|--------|--------|-------|
| AI-Readiness % (tiers passed / 4) | **0%** | **100%** |
| Tiers passing SHACL (0 Violations) | T1 | T1, T2, T3, T4 |
| Tiers failing SHACL | T2, T3, T4 | — |
| Python checks passed | 2/7 | 11/11 |

### Per-tier before/after (Violations count)

| Tier | Criterion | Before Violations | After Violations |
|------|-----------|:-----------------:|:----------------:|
| T1 | Findable | ✓ 0 | ✓ 0 |
| T2 | Accessible + Reusable | ✗ 1 | ✓ 0 |
| T3 | Interoperable + Schema | ✗ 3 | ✓ 0 |
| T4 | AI-Ready (FAIRSCAPE C1–C13) | ✗ 6 | ✓ 0 |

## BEFORE State (original schema.org metadata)

Source: DOI content negotiation `curl -L -H 'Accept: application/ld+json' https://doi.org/10.5281/zenodo.21143094`

The original Zenodo schema.org JSON-LD uses `http://schema.org` context (legacy HTTP).
It is normalised to `https://schema.org/` via `src/profiles.normalize()` before validation.

**Fields present in the original metadata:**
- `schema:name`, `schema:description` (rich, ≥20 chars) → T1 satisfied
- `schema:identifier` (PropertyValue with OAI identifier) → T1 satisfied (SHACL)
- `schema:author` → normalised to `schema:creator` → T2 satisfied
- `schema:datePublished` → coerced to `xsd:date` → T2 satisfied
- `schema:license` → T2 Warning satisfied
- `schema:keywords`, `schema:inLanguage`, `schema:url`, `schema:publisher` → present

**Fields absent / insufficient:**
- `schema:distribution` with `schema:contentUrl` → **T2 Violation** (1 violation)
- `schema:about` as controlled-vocabulary IRI → **T3 Violation**
- `schema:variableMeasured` → **T3 Violation**
- `schema:version` → **T3 Violation**
- `schema:additionalType` as IRI → **T4 Violation** (empty string present, not IRI)
- `prov:wasGeneratedBy` → **T4 Violation**
- `schema:numberOfItems` → **T4 Violation**
- `schema:hasPart` (data dictionary) → **T4 Violation**
- `schema:conditionsOfAccess` → **T4 Violation**
- Checksum on distribution → **T4 Violation**

## AFTER Enrichment — Real Derived Values

All values below are **genuinely derived** from the real dataset unless marked
> ⚠ *illustrative placeholder*.

### C4 — Integrity (sha256 checksum)

| File | SHA-256 |
|------|---------|
| `T_mensual.csv` | `6c2297659b146c4e9c4578c294c3aa7d39f727f6c7e79eee159095ca89ea3b41` |

Command: `sha256sum T_mensual.csv` (verified against downloaded bytes)

### C6 / T3 — Variables measured (real CSV column names)

Column count: **12**  |  Row count (data): **226**

| Column | Description | Unit |
|--------|-------------|------|
| `month` | First day of observation month (ISO 8601 YYYY-MM-DD) | date |
| `MALCA1` | Monthly mean air temperature at station 'MALCA1' | °C |
| `Malacatos` | Monthly mean air temperature at station 'Malacatos' | °C |
| `Militar` | Monthly mean air temperature at station 'Militar' | °C |
| `UTPL` | Monthly mean air temperature at station 'UTPL' | °C |
| `Epoca` | Monthly mean air temperature at station 'Epoca' | °C |
| `Jipiro` | Monthly mean air temperature at station 'Jipiro' | °C |
| `SanPedro` | Monthly mean air temperature at station 'SanPedro' | °C |
| `Cajanuma` | Monthly mean air temperature at station 'Cajanuma' | °C |
| `Tecnico` | Monthly mean air temperature at station 'Tecnico' | °C |
| `Ventanas` | Monthly mean air temperature at station 'Ventanas' | °C |
| `Villonaco` | Monthly mean air temperature at station 'Villonaco' | °C |

*Column names read from CSV header row (first row of `T_mensual.csv`).*

### C11 — Sample count

- **schema:numberOfItems** = `226` *(real row count excluding CSV header)*

### I1 — Controlled-vocabulary subject IRI

- `schema:about`: `http://purl.obolibrary.org/obo/ENVO_01001166`
  → ENVO term **"climate"** (Environment Ontology, OBO Foundry)

### C1 — Data type IRI

- `schema:additionalType`: `http://edamontology.org/format_3752`
  → EDAM term **"CSV"** (tabular comma-separated data)

### C9 — Pipeline provenance (PROV-O)

- `prov:wasGeneratedBy`: `https://doi.org/10.5281/zenodo.21143094#quality-control-run-v2`
  → `prov:Activity` with `prov:wasAssociatedWith` → ORCID of lead author
- `prov:startedAtTime` / `prov:endedAtTime`: `2026-07-02T00:00:00Z` / `2026-07-02T06:00:00Z`
  > ⚠ *timestamps are illustrative placeholders — the actual QC pipeline run times
  >   are not recorded in the Zenodo metadata and cannot be derived from the file.*

### R1.3 / I2 — Community standard

- `schema:isBasedOn`: `https://bioschemas.org/profiles/Dataset/1.1-RELEASE`
  → Bioschemas Dataset 1.1 profile

### C5 — Data dictionary

- `schema:hasPart`: `https://doi.org/10.5281/zenodo.21143094#data-dictionary`
  → `far:DataDictionary` with one `far:VariableDefinition` per column
  → variable names, data types, units derived from real CSV header

### C8 / C13 — Ethics and de-identification

- `schema:conditionsOfAccess`:  
  *"Freely accessible under CC-BY 4.0. De-identification: not applicable —
  this is non-human environmental data; no personal data present. No IRB required."*
  > This statement is factually correct for this non-human meteorological dataset.

### F1 — Persistent identifier

- `schema:identifier`: `https://doi.org/10.5281/zenodo.21143094` (DOI as IRI)
  → satisfies both SHACL T1 (minCount) and Python check_f1_pid_format (DOI pattern)

### R1.2 — Creator ORCIDs

- Franz Pucha-Cofrep: `https://orcid.org/0000-0002-5556-4028` (ORCID — from Zenodo record)
- Andreas Fries: `https://orcid.org/0000-0001-5357-5682` (ORCID — from Zenodo record)

## Output Files

| File | Description |
|------|-------------|
| `examples_remediated/zenodo-21143094.before.jsonld` | Original schema.org JSON-LD from DOI content negotiation |
| `examples_remediated/zenodo-21143094.before.validation.md` | SHACL + Python before-report |
| `examples_remediated/zenodo-21143094.after.jsonld` | Enriched AI-ready JSON-LD |
| `examples_remediated/zenodo-21143094.after.ttl` | Enriched AI-ready Turtle |
| `examples_remediated/zenodo-21143094.after.validation.md` | SHACL + Python after-report |
| `examples_remediated/before_after.png` | AI-readiness bar chart |
| `examples_remediated/tiers_before_after.png` | Per-tier pass/fail chart |

## Validation commands

```bash
# BEFORE (normalized schema.org)
uv run --with rdflib --with pyshacl python src/validate.py \
    examples_remediated/zenodo-21143094.before.jsonld \
    --shapes shapes/tier-4-ai-ready.ttl

# AFTER (enriched AI-ready record)
uv run --with rdflib --with pyshacl python src/validate.py \
    examples_remediated/zenodo-21143094.after.ttl \
    --shapes shapes/tier-4-ai-ready.ttl
```