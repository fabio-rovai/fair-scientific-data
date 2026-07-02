# FAIRSCAPE AI-Readiness Criteria Mapping

**Sources:**
- FAIRSCAPE 28 criteria: Al Manir S et al. "The FAIRSCAPE AI-readiness Framework for Biomedical Research." *bioRxiv*:2024.12.23.629818 (v4 March 2026; PMC11703166)
- Bridge2AI dimensions D1–D7: Caufield H et al. "Standards in the Preparation of Biomedical Research Metadata: A Bridge2AI Perspective." *arXiv*:2509.10432 (September 2025)
- FAIR principles F1–R1.3: Wilkinson MD et al. *Sci Data* 3:160018, 2016
- WRROC provenance: Leo S et al. *PLoS One* 19(9):e0309210, 2024
- Bioschemas Dataset 1.1: https://bioschemas.org/profiles/Dataset/1.1-RELEASE
- DataCite Schema 4.5: https://schema.datacite.org/meta/kernel-4/
- DCAT 3: W3C Rec 2023-08-22

**Notation:**
- `SHACL` = expressible as a SHACL constraint (shapes file listed)
- `Python` = requires semantic/content check in `src/checks.py`
- `Both` = structural check in SHACL + semantic verification in Python

| # | Criterion ID | FAIRSCAPE Description | Tier | Shape / Rule ID | Property Checked | How Tested | Expressible? | Citation |
|---|---|---|---|---|---|---|---|---|
| 1 | **F1** | Globally unique and persistent identifier | T1 | `fsd:Tier1FindableShape / F1-PID` | `schema:identifier` minCount 1 | SHACL + Python format check | Both | Wilkinson 2016 §F1; DataCite 4.5 mandatory Identifier |
| 2 | **F2-title** | Rich metadata — title | T1 | `fsd:Tier1FindableShape / F2-Title` | `schema:name` minLength 5 | SHACL | SHACL | Wilkinson 2016 §F2; Bioschemas Dataset 1.1 MINIMUM |
| 3 | **F2-desc** | Rich metadata — description | T1 | `fsd:Tier1FindableShape / F2-Description` | `schema:description` minLength 20 | SHACL | SHACL | Wilkinson 2016 §F2; Bioschemas Dataset 1.1 MINIMUM |
| 4 | **F2-kw** | Rich metadata — keywords | T1 | `fsd:Tier1FindableShape / F2-Keywords` | `schema:keywords` minCount 1 | SHACL | SHACL | Wilkinson 2016 §F2; Bridge2AI D1 |
| 5 | **F3** | Metadata includes identifier of data (landing page) | T1 | `fsd:Tier1FindableShape / F3-LandingPage` | `schema:url` nodeKind IRI (Warning) | SHACL | SHACL | Wilkinson 2016 §F3; Bioschemas RECOMMENDED |
| 6 | **F4** | Metadata registered/indexed in searchable resource | T1 | `fsd:Tier1FindableShape / F4-Catalog` | `schema:includedInDataCatalog` nodeKind IRI (Warning) | SHACL | SHACL | Wilkinson 2016 §F4; DCAT 3 dcat:catalog |
| 7 | **A1** | Open, free, standard retrieval protocol | T2 | `fsd:DataDownloadShape / A1-ContentUrl` | `schema:contentUrl` pattern `^https?://` | SHACL (pattern) + Python scheme check | Both | Wilkinson 2016 §A1; `checks.check_a1_open_protocol` |
| 8 | **A1.1** | Protocol supports authentication/authorisation | T2 | `fsd:Tier2AccessibleShape / A1.1-ConditionsOfAccess` | `schema:conditionsOfAccess` (Warning) | SHACL (presence only) | SHACL | Wilkinson 2016 §A1.1 |
| 9 | **A1.2** | Procedure for access when data removed | T2 | `fsd:Tier2AccessibleShape / A1.2-ContactPoint` | `schema:contactPoint` (Warning) | SHACL | SHACL | Wilkinson 2016 §A1.2; DCAT 3 |
| 10 | **A2** | Metadata accessible even if data no longer available | T3 | `fsd:Tier3InteroperableShape / R1.3-ConformsTo` | `schema:isBasedOn` (standard IRI) | SHACL (presence; semantics via repository policy) | SHACL | Wilkinson 2016 §A2 — structural proxy |
| 11 | **I1** | Formal, accessible knowledge representation language | T3 | `fsd:Tier3InteroperableShape / I1-ControlledVocabSubject` | `schema:about` nodeKind IRI minCount 1 (Violation) | SHACL | SHACL | Wilkinson 2016 §I1; Bridge2AI D6 |
| 12 | **I2** | FAIR vocabularies used | T3 | `fsd:Tier3InteroperableShape / I2-Language` + `I1-ControlledVocabSubject` | `schema:about` IRI + `schema:inLanguage` | SHACL (IRI presence); Python verifiable | SHACL | Wilkinson 2016 §I2 |
| 13 | **I3** | Qualified references to other datasets | T3 | `fsd:Tier3InteroperableShape / I3-QualifiedReference` | `schema:isBasedOn` nodeKind IRI (Warning) | SHACL | SHACL | Wilkinson 2016 §I3; WRROC prov:wasDerivedFrom |
| 14 | **R1** | Multiple, rich attributes for reuse | T2 | Multiple properties across T1+T2 | Count of defined properties | SHACL (cumulative) | SHACL | Wilkinson 2016 §R1 |
| 15 | **R1.1** | Clear, accessible data usage licence (machine-readable IRI) | T2 | `fsd:Tier2AccessibleShape / R1.1-License` | `schema:license` nodeKind IRI (Violation) | SHACL + Python recognised-licence check | Both | Wilkinson 2016 §R1.1; `checks.check_r1_1_licence` |
| 16 | **R1.2** | Detailed data provenance (creator + date) | T2 | `fsd:Tier2AccessibleShape / R1.2-Creator`, `R1.2-DatePublished` | `schema:creator` + `schema:datePublished` | SHACL + Python ORCID check | Both | Wilkinson 2016 §R1.2; DataCite mandatory Creator; `checks.check_r1_2_creator_orcid` |
| 17 | **R1.3** | Meets domain community standards | T3 | `fsd:Tier3InteroperableShape / R1.3-ConformsTo` | `schema:isBasedOn` IRI (Warning) | SHACL | SHACL | Wilkinson 2016 §R1.3; Bridge2AI D6 |
| 18 | **C1** | Data type identified (omics, imaging, clinical, …) | T4 | `fsd:Tier4AIReadyShape / C1-DataType` | `schema:additionalType` nodeKind IRI (Violation) | SHACL | SHACL | Al Manir 2024 criterion C1; Bridge2AI D3 |
| 19 | **C2** | Data format identified (CSV, HDF5, FASTQ, …) | T2/T4 | `fsd:DataDownloadShape / C2-Format` | `schema:encodingFormat` (Warning in T2) | SHACL | SHACL | Al Manir 2024 criterion C2 |
| 20 | **C3** | Data version identified | T3 | `fsd:Tier3InteroperableShape / C3-Version` | `schema:version` minCount 1 (Violation) | SHACL + Python semver format check | Both | Al Manir 2024 criterion C3; `checks.check_c3_version_format` |
| 21 | **C4** | Checksum for data integrity verification | T4 | `fsd:Tier4AIReadyShape / C4-Checksum-Distribution` → `fsd:DataDownloadAIShape` | `schema:sha256` pattern `[0-9a-fA-F]{64}` OR `spdx:checksum` (Violation) | SHACL (format) + Python hex validation | Both | Al Manir 2024 criterion C4; `checks.check_c4_checksum` |
| 22 | **C5** | Data dictionary / data model / schema provided | T4 | `fsd:Tier4AIReadyShape / C5-DataDictionary` | `schema:hasPart` minCount 1 (Violation) | SHACL (presence; content needs Python) | SHACL | Al Manir 2024 criterion C5; Bridge2AI D3 |
| 23 | **C6** | Variables / features measured described | T3 | `fsd:Tier3InteroperableShape / I1-C6-VariableMeasured` | `schema:variableMeasured` minCount 1 (Violation) | SHACL | SHACL | Al Manir 2024 criterion C6; Bioschemas RECOMMENDED |
| 24 | **C7** | Statistical summary / characterisation provided | T4 | `fsd:Tier4AIReadyShape / C7-StatsSummary` (Warning) | `schema:variableMeasured` minCount 2; description keyword scan | SHACL (count) + Python keywords | Both | Al Manir 2024 criterion C7; `checks.check_c7_stats_summary` |
| 25 | **C8** | Ethics / IRB approval / consent documented | T4 | `fsd:Tier4AIReadyShape / C8-EthicsConsent` | `schema:conditionsOfAccess` minCount 1 (Violation) | SHACL (presence) + Python keyword scan | Both | Al Manir 2024 criterion C8; Bridge2AI D5; `checks.check_c8_ethics_consent` |
| 26 | **C9** | Data collection / processing provenance (workflow/pipeline) | T4 | `fsd:Tier4AIReadyShape / C9-PipelineProvenance` | `prov:wasGeneratedBy` nodeKind IRI (Violation) | SHACL | SHACL | Al Manir 2024 criterion C9; WRROC (Leo 2024 PLoS One 19:e0309210) |
| 27 | **C10** | Associated software / code availability | T4 | `fsd:Tier4AIReadyShape / C10-Software` | `schema:softwareRequirements` (Warning) | SHACL | SHACL | Al Manir 2024 criterion C10; Bridge2AI D7 |
| 28 | **C11** | Sample count / record count documented | T4 | `fsd:Tier4AIReadyShape / C11-SampleCount` | `schema:numberOfItems` datatype integer minInclusive 1 (Violation) | SHACL + Python positive int | Both | Al Manir 2024 criterion C11; `checks.check_c11_sample_count` |

---

## Additional criteria covered (beyond 28 FAIRSCAPE core)

| Criterion | Source | Shape / Check |
|---|---|---|
| **C12** Completeness / missingness | Al Manir 2024 (extended); Bridge2AI D3 | `C12-Completeness` (T4 Warning) + `checks.check_c12_completeness` |
| **C13** De-identification method | Al Manir 2024 (extended); Bridge2AI D5 | `C13-DeIdentification` (T4 Warning) + `checks.check_c13_deidentification` |
| **B2AI-D7** Computability / software citation | Caufield 2025 D7 | `C10-Software` shape |
| **WRROC** Full workflow run provenance | Leo 2024 PLoS One | `fsd:WorkflowRunAIShape` (targetClass prov:Activity) |
| **R1.2-ORCID** Creator ORCID identifier | DataCite nameIdentifier | `checks.check_r1_2_creator_orcid` |
| **Licence recognition** | SPDX licence list | `checks.check_r1_1_licence` |

---

## SHACL-expressible vs Python-only split summary

| Type | Count | Examples |
|---|---|---|
| **SHACL-expressible** (structural) | 19 | F1 presence, F2 minLength, R1.1 IRI, A1 protocol pattern, C1 additionalType, C5 hasPart, C9 wasGeneratedBy, C11 integer |
| **Python-only** (semantic) | 0 | (none are purely Python — all have a structural SHACL proxy) |
| **Both** (SHACL structural + Python semantic) | 9 | F1 DOI format, A1 open protocol, R1.1 licence recognition, R1.2 ORCID, C3 semver, C4 hex checksum, C7 stats keywords, C8 ethics keywords, C12 completeness keywords |

**Total FAIRSCAPE criteria covered: 28/28 (100%)**
Additional criteria (C12, C13, WRROC, ORCID, licence recognition): +5

---

## Bridge2AI Dimension Coverage

| Dimension | Description | Covered by |
|---|---|---|
| D1 Findability | PID, title, description, keywords | Tier 1 shapes |
| D2 Accessibility | Licence, distribution, access conditions | Tier 2 shapes |
| D3 Characterisation | variableMeasured, data type, stats, sample count, data dict | Tier 3+4 shapes + C7/C11 checks |
| D4 Provenance | Creator, date, pipeline (WRROC) | Tier 2+4 shapes |
| D5 Ethics | IRB, consent, de-identification | Tier 4 C8/C13 shapes + checks |
| D6 Standards | conformsTo, controlled vocab (EDAM/MeSH/OBO) | Tier 3 shapes |
| D7 Computability | Software reference, version, checksum | Tier 3+4 shapes |

**All 7 Bridge2AI dimensions covered.**

---

## Python check functions in `src/checks.py`

| Function | Criterion | What it checks |
|---|---|---|
| `check_f1_pid_format` | F1 | DOI/ARK/Handle IRI format (regex) |
| `check_a1_open_protocol` | A1 | contentUrl scheme is http(s) |
| `check_r1_1_licence` | R1.1 | Licence IRI in known-open-licence set |
| `check_r1_2_creator_orcid` | R1.2 | At least one creator has ORCID IRI |
| `check_c3_version_format` | C3 | Version matches semver or date convention |
| `check_c4_checksum` | C4 | SHA-256 hex length; SPDX checksumValue format |
| `check_c7_stats_summary` | C7 | Statistical keywords in description |
| `check_c8_ethics_consent` | C8 | IRB/consent keywords in conditionsOfAccess |
| `check_c11_sample_count` | C11 | numberOfItems is positive integer |
| `check_c12_completeness` | C12 | Completeness/missingness keywords in description |
| `check_c13_deidentification` | C13 | De-identification keywords in conditionsOfAccess |
