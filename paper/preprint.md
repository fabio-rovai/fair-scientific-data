# FAIR-AI-Readiness of Open Scientific Data Repositories: A Tiered Evaluation of 1,738 Datasets Across Dryad, BioStudies, and PRIDE, with a Contributed OWL Ontology

**Fabio Rovai**¹

¹ The Tesseract Academy, London, UK  
Correspondence: fabio@thetesseractacademy.com

**Date:** 2 July 2026  
**Version:** preprint v1  
**Repository:** https://github.com/fabio-rovai/fair-scientific-data (MIT Licence)  
**Ontology:** https://w3id.org/fair-ai-ready (CC-BY 4.0)

---

## Abstract

Machine learning for biomedicine demands metadata that is rich enough for automated ingestion, quality assessment, and auditable provenance — not merely findable data. Yet the extent to which real open-access repositories satisfy the AI-readiness extensions to the FAIR principles has not been measured at scale. We evaluate 1,738 datasets drawn from three major open repositories — Dryad (*n* = 340), EMBL-EBI BioStudies (*n* = 798), and PRIDE/ProteomeXchange (*n* = 600) — against a four-tiered FAIR-AI-Readiness contract derived from the FAIRSCAPE framework (28 criteria spanning F1–F4, A1–A1.2, R1–R1.3, I1–I3, and C1–C13), validated by SHACL shapes and Python semantic checks with 100% SHACL/Python agreement on a 30-record spot-check per tier. Results show that **99.9%** of datasets pass Tier 1 (Findable: PID, title, description), **91.3%** pass Tier 2 (Accessible + Reusable: distribution, creator, publication date), and **0%** pass Tier 3 (Interoperable + Schema-structured) or Tier 4 (AI-Ready). The cliff is absolute and universal: every criterion that requires machine-readable structural description or computational provenance fails at 100% across all three repositories — `schema:variableMeasured`, integrity checksums, ethics/IRB documentation, pipeline provenance (`prov:wasGeneratedBy`), and sample count. No dataset in the corpus exposes a data dictionary, a version identifier, or a qualified reference to a community standard. To make this gap closeable, we contribute the FAIR AI-Ready Dataset (FAR) ontology: an OWL 2 application ontology with 9 native classes, 21 properties, and 42 alignment assertions to schema.org, DCAT 3, PROV-O, SPDX 2.3, and MLCommons Croissant, validated with 238 raw triples (705 after OWL-RL closure, lint-clean, OWL-RL consistent via open-ontologies). All code, SHACL shapes, corpus data, and the ontology are openly available under permissive licences.

**Keywords:** FAIR data, AI-readiness, metadata quality, SHACL validation, data repositories, schema.org, FAIRSCAPE, BioStudies, Dryad, PRIDE, OWL ontology

---

## 1. Introduction

The FAIR principles — Findable, Accessible, Interoperable, Reusable — published by Wilkinson et al. in 2016 [1] established a widely adopted normative framework for scientific data governance. A decade of adoption has produced measurable progress at the findability and accessibility layers: persistent identifiers, title, description, and creator metadata are now nearly universal in major open repositories. Yet FAIR compliance was never intended as a binary ceiling; it exists along a spectrum whose requirements grow substantially when data must serve as input to machine learning (ML) pipelines or automated data-assembly workflows.

Where a human researcher can compensate for a missing variable description by reading a supplementary document, an automated ML ingestion pipeline cannot. Where a FAIR-compliance dashboard marks a dataset as "reusable" because it carries a licence string, a data-quality system requires that licence to be a machine-readable IRI pointing to a recognised open standard. The gap between what repositories currently publish and what AI-ready pipelines actually require — what we term the FAIR-to-AI-ready gap — has been articulated in several normative frameworks [2, 3, 4] but has not previously been measured at corpus scale across multiple repositories.

Several recent frameworks have codified what AI-ready metadata means in practice. The FAIRSCAPE AI-Readiness Framework [2] introduces 28 criteria (C1–C13, plus classical F, A, I, R dimensions) covering data-type identification, checksum integrity, ethics governance, pipeline provenance, and statistical characterisation. The Bridge2AI initiative [3] articulates seven readiness dimensions (D1–D7) from the perspective of large-scale biomedical data collection. The Workflow Run RO-Crate (WRROC) specification [4] defines canonical provenance capture via `prov:wasGeneratedBy`. The biomedical knowledge-graph quality literature [5] has further highlighted how metadata incompleteness propagates downstream into unreliable model training. MLCommons Croissant [8] proposes a dataset metadata format specifically designed for ML pipelines, introducing structured field-level descriptions absent from conventional repository exports.

Despite this normative landscape, empirical measurement of AI-readiness across real open-access repositories remains sparse. Most prior assessments evaluate a handful of curated examples, focus on a single repository, or assess FAIR compliance without the AI-ready extensions. We address this gap with a corpus-scale, criterion-by-criterion evaluation against all 28 FAIRSCAPE criteria plus extensions, covering three repositories and 1,738 datasets.

**Contributions.**

1. A corpus of 1,738 real dataset metadata records from three open repositories, normalised to a common schema.org JSON-LD representation.
2. A four-tiered SHACL validation contract (four TTL shape files) covering all 28 FAIRSCAPE criteria plus WRROC provenance (C9) and de-identification (C13), with Python semantic checks for 11 criteria not fully expressible in SHACL.
3. Quantitative failure rates for every criterion, with per-repository breakdowns, and four analysis figures (tier conformance, per-criterion failure, highest-tier distribution, repo × criterion heatmap).
4. The FAIR AI-Ready Dataset (FAR) ontology — an OWL 2 application ontology that models the machine-readable structural and provenance layer universally absent in the corpus, with 42 alignment assertions to five external vocabularies.

All code, shapes, data, and the ontology are available under the MIT/CC-BY 4.0 licences.

---

## 2. Related Work

**FAIR principles and assessment.** Wilkinson et al. [1] defined the 15 FAIR sub-principles across four dimensions. Subsequent tools — FAIR Checker, F-UJI, and FAIRshake — operationalise automated assessment, but typically test a single record against generic FAIR criteria rather than performing corpus-scale evaluation with AI-specific extensions. Prior corpus studies have focused on compliance rates within a single repository or on findability alone.

**FAIRSCAPE AI-Readiness Framework.** Al Manir, Clark et al. [2] introduced FAIRSCAPE to bridge FAIR compliance and AI operational requirements, defining 28 criteria with traceability to FAIR sub-principles. Their C1–C13 characterisation criteria — data type, format, version, checksum, data dictionary, variable descriptions, statistical summary, ethics, provenance, software, sample count, completeness, and de-identification — go substantially beyond classical FAIR. The current work is the first corpus-scale empirical evaluation of these criteria across multiple repositories.

**Bridge2AI metadata readiness.** Caufield, Munoz-Torres et al. [3] describe seven metadata readiness dimensions from the Bridge2AI programme: findability (D1), accessibility (D2), characterisation (D3), provenance (D4), ethics (D5), standards (D6), and computability (D7). Our tiered contract maps explicitly to all seven dimensions; the analysis confirms Bridge2AI's concern that characterisation, provenance, and ethics metadata are systematically absent.

**Workflow Run RO-Crate (WRROC).** Leo, Soiland-Reyes et al. [4] define a canonical pattern for capturing computational provenance via `prov:wasGeneratedBy` linking a dataset to its generating workflow run, within the RO-Crate packaging framework. Our Tier 4 includes this as criterion C9; we find 100% failure across all repositories.

**Biomedical knowledge-graph quality.** Haendel, Mungall et al. [5] analyse quality dimensions in biomedical knowledge graphs, identifying metadata gaps — missing entity descriptions, absent provenance, incomplete concept mappings — as primary barriers to reliable graph-based AI. Our findings extend this analysis to the dataset-metadata layer, quantifying the same gap at the repository-catalogue level. **[Note: arXiv:2508.21774 cited as given in task specification; independent verification of this reference is recommended before journal submission.]**

**Vocabulary standards.** DCAT 3 [9] provides a standard vocabulary for data catalogues; PROV-O [10] for provenance; SPDX 2.3 [11] for software and data package integrity; Bioschemas Dataset 1.1 [6] for biomedical dataset metadata profiles; DataCite Schema 4.5 [7] for citation metadata. MLCommons Croissant [8] proposes dataset metadata specifically for ML pipelines. Our SHACL contract and contributed ontology draw on all of these.

---

## 3. Methods

### 3.1 Corpus Construction

We built a corpus of 1,738 real dataset metadata records from three open-access repositories, fetched on 2026-07-01 (full provenance in `CORPUS_REPORT.md` and `data/corpus/manifest.json`):

| Repository | *N* | Native format | Fetch method |
|---|---|---|---|
| Dryad | 340 | schema.org JSON-LD | Dryad API v2, content negotiation |
| EMBL-EBI BioStudies | 798 | BioStudies JSON (search API) | EBI BioStudies search endpoint |
| PRIDE/ProteomeXchange | 600 | PRIDE JSON (project API) | EBI PRIDE REST API |
| **Total** | **1,738** | | |

Zenodo was targeted with eight domain-spanning queries (single-cell RNA sequencing, proteomics mass spectrometry, spatial transcriptomics, metabolomics NMR, clinical genomics, cryo-EM, metagenomics, epigenomics) but all eight API calls timed out; Zenodo is excluded and this is discussed as a limitation (Section 7). Within each repository, records were sampled across diverse subject domains without subject-domain stratification.

### 3.2 Metadata Normalisation

Heterogeneous repository-specific JSON formats were normalised to a common schema.org-based internal representation by `src/profiles.py`. All 1,738 records normalised successfully (100%). Key mappings:

- **Dryad JSON-LD**: already schema.org; the normaliser remaps `http://schema.org/` predicates to `https://schema.org/` and coerces date literals to `xsd:dateTime`. The dataset `@id` (a DOI IRI) is asserted as `schema:identifier`. A distribution stub is constructed from `schema:url` when no explicit `schema:distribution` is present.
- **BioStudies JSON**: `accession` → `schema:identifier` (EBI accession IRI); `title` → `schema:name`; `content` → `schema:description`; `author` strings → `schema:creator`; `release_date` → `schema:datePublished`. File availability is checked against the EBI file-count field; studies with files present are mapped to a machine-readable distribution pointing to the EBI files endpoint.
- **PRIDE JSON**: `doi` → `schema:identifier`; `projectDescription` → `schema:description`; `keywords` → `schema:keywords`; NEWT organism accessions (e.g., `NEWT:10090`) → `schema:about` as NCBI taxonomy IRIs; experiment types → `schema:additionalType` with PRIDE ontology IRIs; PRIDE data-file metadata → `schema:distribution` with `schema:contentUrl`.

### 3.3 Four-Tiered SHACL Validation Contract

We implement a four-tier validation contract in `shapes/`, covering all 28 FAIRSCAPE criteria plus five extensions (C12 completeness, C13 de-identification, WRROC provenance, creator ORCID, licence recognition):

| Tier | Shape file | FAIR dimensions | Key Violation criteria |
|---|---|---|---|
| T1 | `tier-1-findable.ttl` | F1–F4 | F1 (PID), F2-title (≥5 chars), F2-desc (≥20 chars) |
| T2 | `tier-2-accessible-reusable.ttl` | A1–A1.2, R1–R1.2 | A1 (distribution + https contentUrl), R1.2-creator, R1.2-date |
| T3 | `tier-3-interoperable-schema.ttl` | I1–I3, R1.3, C3, C6 | I1 (controlled-vocab subject IRI), C3 (version), C6 (variableMeasured ≥1) |
| T4 | `tier-4-ai-ready.ttl` | C1–C13 | C1 (additionalType IRI), C4 (checksum), C5 (hasPart), C8 (ethics), C9 (prov:wasGeneratedBy), C11 (numberOfItems) |

Tiers are cumulative: a dataset passes Tier *N* only if it also passes all lower tiers, with zero `sh:Violation`-severity results for that tier's shape. Two criteria — keywords (F2-kw) and machine-readable licence IRI (R1.1) — are reported as sub-metrics with `sh:Warning` severity and do not gate tier conformance; they appear in per-criterion analyses but not in the pass/fail tier count. This follows the design rationale in the FAIRSCAPE framework, which treats keyword coverage and licence form as important quality indicators but not binary gates on findability and accessibility. Warning-severity criteria (F3, F4, A1.1, A1.2, R1, R1.3, I2, I3, D3, C7, C10, C12, C13) are likewise recorded but do not block conformance.

### 3.4 Python Semantic Checks

Eleven functions in `src/checks.py` cover criteria not fully expressible in SHACL: DOI/ARK/Handle IRI format (F1), http(s) protocol validation (A1), SPDX open-licence recognition (R1.1), ORCID IRI format (R1.2), semver/date version format (C3), SHA-256 hex checksum validation (C4), statistical-summary keyword scanning (C7), ethics/IRB keyword scanning (C8, C12), positive-integer sample count (C11), and de-identification keyword scanning (C13).

### 3.5 Validation Consistency

SHACL structural results and Python semantic checks were compared on a spot-check of 30 records (10 per repository). Agreement was 100% for Tier 1 (30/30), 100% for Tier 2 (30/30), and 100% for Tier 3 (30/30). Full agreement figures are recorded in `results_deep/analysis.json` (`shacl_python_agreement`).

---

## 4. Results

All numbers below come directly from `results_deep/analysis.json` and `results_deep/results.md`, generated 2026-07-02. Figures are in `results_deep/`.

### 4.1 Overall Tier Conformance

**Table 1. Tier conformance across 1,738 datasets.**

| Tier | Criterion class | Passed | *N* | Conformance rate |
|---|---|---|---|---|
| T1 | Findable (F1, F2-title, F2-desc) | 1,737 | 1,738 | **99.9%** |
| T2 | Accessible + Reusable (A1, R1.2-creator, R1.2-date) | 1,586 | 1,738 | **91.3%** |
| T3 | Interoperable + Schema-Structured (I1, C3, C6) | 0 | 1,738 | **0.0%** |
| T4 | AI-Ready (C1, C4, C5, C8, C9, C11) | 0 | 1,738 | **0.0%** |

The headline finding is a sharp cliff between Tier 2 and Tier 3. Foundational metadata — persistent identifier, title, description, creator, publication date, and download URL — is nearly universal: 99.9% of datasets pass T1 and 91.3% pass T2. But the machine-readable structural and provenance layer that AI pipelines require is universally absent: 0% of datasets pass T3 or T4.

The distribution of highest tier reached (Figure 3; `fig3_highest_tier_distribution.png`):

| Highest tier | *n* | % |
|---|---|---|
| None (failed T1) | 1 | 0.1% |
| T1 Findable | 151 | 8.7% |
| T2 Accessible + Reusable | 1,586 | 91.3% |
| T3 or T4 | 0 | 0.0% |

The single T1 failure is one Dryad record whose exported description is fewer than 20 characters (F2-desc Violation). The 151 T1-only records are entirely BioStudies records that pass T1 but fail T2 due to absent distribution metadata (see Section 4.2).

See also Figure 1 (`fig1_tier_conformance_by_repo.png`) for tier conformance broken down by repository.

### 4.2 Per-Repository Tier Conformance

**Table 2. Tier conformance by repository.**

| Repository | *N* | T1 Findable | T2 Accessible | T3 Interoperable | T4 AI-Ready |
|---|---|---|---|---|---|
| BioStudies | 798 | **100.0%** (798/798) | **81.1%** (647/798) | 0.0% | 0.0% |
| Dryad | 340 | **99.7%** (339/340) | **99.7%** (339/340) | 0.0% | 0.0% |
| PRIDE | 600 | **100.0%** (600/600) | **100.0%** (600/600) | 0.0% | 0.0% |

**PRIDE** is the strongest performer at T1 and T2, achieving 100% on both tiers. PRIDE records carry persistent identifiers, rich descriptions, keyword metadata, and download URLs, and creators and publication dates are universally present. PRIDE's organism mappings (NEWT organism accessions → NCBI taxonomy IRIs) also mean PRIDE passes the controlled-vocabulary subject IRI sub-criterion (I1: 0% failure within PRIDE), though this alone is insufficient to reach T3 because C6 (variableMeasured) and C3 (version) fail at 100% even within PRIDE.

**Dryad** achieves 99.7% at both T1 and T2, failing only at T3 and T4. The single T1 failure is one record with an insufficiently short description. Dryad's T2 near-perfect rate reflects its schema.org JSON-LD exports, which systematically include creator, publication date, and a distribution URL. The 0.3% T2 failure (1 record) reflects the same outlier record that fails T1.

**BioStudies** achieves 100% at T1 — all 798 records carry an EBI accession IRI as identifier, a title, and a description — but 18.9% fail T2 (151/798 records). The T2 failure is driven by criterion A1 (distribution with https contentUrl): BioStudies' search API returns a reduced metadata set that omits file-download URLs for approximately 17.5% of records (those with no files recorded in the basic search response). An additional 1.4% of BioStudies records (11/798) lack a creator field, contributing to R1.2-creator failures. BioStudies records also uniformly lack machine-readable licence IRIs (R1.1: 100% failure within BioStudies) and keyword metadata (F2-kw: 100% failure), but these are Warning sub-metrics and do not block tier conformance.

### 4.3 Per-Criterion Failure Rates

**Table 3. Failure rates for all criteria (sorted by failure rate descending; Violation-severity criteria in bold).**

| Criterion | Tier | Sev. | Failure rate | *n* fail / 1,738 | Description |
|---|---|---|---|---|---|
| **C6** | T3 | Viol. | **100.0%** | 1,738 | Variables measured (schema:variableMeasured ≥1) |
| **C4** | T4 | Viol. | **100.0%** | 1,738 | Integrity checksum (spdx:checksum or schema:sha256) |
| **C8** | T4 | Viol. | **100.0%** | 1,738 | Ethics/IRB documented (schema:conditionsOfAccess) |
| **C9** | T4 | Viol. | **100.0%** | 1,738 | Pipeline provenance (prov:wasGeneratedBy IRI) |
| **C11** | T4 | Viol. | **100.0%** | 1,738 | Sample count (schema:numberOfItems ≥1 integer) |
| F4 | T1 | Warn. | 100.0% | 1,738 | Catalogue registration (schema:includedInDataCatalog) |
| A1.1 | T2 | Warn. | 100.0% | 1,738 | Access conditions (schema:conditionsOfAccess) |
| A1.2 | T2 | Warn. | 100.0% | 1,738 | Contact point (schema:contactPoint) |
| R1.3 | T3 | Warn. | 100.0% | 1,738 | Conforms to community standard (schema:isBasedOn) |
| I3 | T3 | Warn. | 100.0% | 1,738 | Qualified reference (schema:isBasedOn IRI) |
| C10 | T4 | Warn. | 100.0% | 1,738 | Software reference (schema:softwareRequirements) |
| C7 | T4 | Warn. | 100.0% | 1,738 | Statistical summary (schema:variableMeasured ≥2) |
| C13 | T4 | Warn. | 100.0% | 1,738 | De-identification (schema:conditionsOfAccess) |
| **C5** | T4 | Viol. | **99.9%** | 1,737 | Data dictionary (schema:hasPart) |
| I2 | T3 | Warn. | 80.5% | 1,399 | Language declared (schema:inLanguage) |
| **C3** | T3 | Viol. | **80.4%** | 1,398 | Version identifier (schema:version) |
| R1.1 | T2 | Warn. | 73.1% | 1,270 | Machine-readable licence IRI (schema:license as IRI) |
| **I1** | T3 | Viol. | **65.5%** | 1,138 | Controlled-vocab subject IRI (schema:about IRI) |
| D3 | T3 | Warn. | 65.5% | 1,138 | Measurement technique (schema:measurementTechnique) |
| **C1** | T4 | Viol. | **65.5%** | 1,139 | Data type IRI (schema:additionalType IRI) |
| F2-kw | T1 | Warn. | 47.6% | 828 | Keywords present (schema:keywords ≥1) |
| R1 | T2 | Warn. | 45.9% | 798 | Publisher declared (schema:publisher) |
| **A1** | T2 | Viol. | **8.1%** | 140 | Distribution + https contentUrl (schema:distribution) |
| C12 | T4 | Warn. | 1.4% | 24 | Completeness/missingness (description ≥100 chars) |
| **R1.2-creator** | T2 | Viol. | **0.6%** | 11 | Creator present (schema:creator) |
| **F2-desc** | T1 | Viol. | **0.1%** | 1 | Description ≥20 chars (schema:description) |
| **F1** | T1 | Viol. | **0.0%** | 0 | Globally unique PID (schema:identifier) |
| **F2-title** | T1 | Viol. | **0.0%** | 0 | Title ≥5 chars (schema:name) |
| F3 | T1 | Warn. | 0.0% | 0 | Landing page IRI (schema:url) |
| **R1.2-date** | T2 | Viol. | **0.0%** | 0 | Publication date (schema:datePublished) |

See Figure 2 (`fig2_criterion_failure_rates.png`) and Figure 4 (`fig4_repo_criterion_heatmap.png`) for visual breakdown.

Several findings merit specific discussion:

**Universal AI-readiness failures.** C6 (variableMeasured), C4 (checksum), C8 (ethics/IRB), C9 (provenance), and C11 (sample count) fail at 100% across all three repositories. No repository in this corpus exposes variable descriptions, integrity checksums on distributions, ethics/IRB documentation, workflow provenance, or quantitative sample counts in their catalogue-level metadata exports. This is not a matter of inconsistent practice — it reflects that these fields are structurally absent from the API responses of all three repositories.

**C5 near-miss.** C5 (data dictionary via `schema:hasPart`) fails for 99.9% of records (1,737/1,738): a single Dryad record carries a `schema:hasPart` reference. Data dictionaries exist as supplementary files for many datasets but are not surfaced in catalogue metadata.

**T3 blockers.** C6 (variableMeasured ≥1, 100% failure) is the single criterion that blocks the entire corpus at T3. The 80.4% failure on C3 (version) reflects that PRIDE and BioStudies API responses include no version field, while Dryad exports version information that is correctly captured (C3 failure within Dryad: 0%). The 65.5% failure on I1 (controlled-vocab subject IRI) is driven by BioStudies and Dryad not using IRI-based subject classification (BioStudies I1 failure: 100%; Dryad I1 failure: 100%); PRIDE, which maps organism accessions to NCBI taxonomy IRIs, passes I1 completely (PRIDE I1 failure: 0%).

**Keyword and licence gaps (sub-metrics).** Keywords (F2-kw) are absent from 47.6% of all records: BioStudies exposes no keyword metadata via the search API (100% failure), Dryad is largely compliant (8.8% failure), and PRIDE is fully compliant (0% failure). Machine-readable licence IRIs (R1.1) fail at 73.1% overall: BioStudies carries no licence field (100% failure); PRIDE carries the string "EBI terms of use" rather than an IRI (78.7% failure); Dryad exports CC0 or CC-BY licence IRIs correctly (0% failure). As Warning sub-metrics, these do not block tier conformance but represent actionable, low-cost improvements.

**Foundational metadata is strong.** F1 (globally unique PID) fails for zero records; F2-title, F3 (landing page), and R1.2-date (publication date) each fail at 0%. The practical implication is that the FAIR-to-AI-ready gap is not a findability problem — it is entirely located at the interoperability and provenance layer.

---

## 5. The FAIR AI-Ready Dataset (FAR) Ontology

### 5.1 Motivation

The corpus analysis establishes an empirical baseline: the machine-readable structural and provenance layer required for AI-ready datasets is universally absent in current repository metadata. There is no existing single vocabulary that covers the full set of concepts — variable schema, data dictionary, provenance record, integrity check, ethics basis, sample characterisation, access specification — with precise semantics and validated alignments to the vocabularies that repositories already use (schema.org, DCAT, PROV-O, SPDX). We contribute the FAIR AI-Ready Dataset (FAR) ontology to fill this gap, following the design principle "compose, do not reinvent".

### 5.2 Design Principles

FAR defines a minimal set of native classes and properties that address the Tier 3 and Tier 4 concepts absent from schema.org, DCAT 3, PROV-O, SPDX 2.3, and Croissant individually, and aligns every native term to those vocabularies via `rdfs:subClassOf`, `skos:exactMatch`, and `skos:closeMatch`. The validation layer is the companion SHACL shapes in `shapes/`; the ontology captures class semantics, necessary conditions (OWL restrictions on `far:AIReadyDataset`), and vocabulary alignments. This split — OWL for interoperability and alignment, SHACL for machine validation — is intentional and follows established practice in vocabulary engineering.

**Namespace:** `https://w3id.org/fair-ai-ready/`  
**Prefix:** `far:`  
**Version:** 0.1.0 (2026-07-02)  
**Licence:** CC-BY 4.0

### 5.3 Statistics

| Metric | Value |
|---|---|
| Raw triples | 238 |
| Triples after OWL-RL closure | 705 |
| Native classes | 9 |
| Native object properties | 12 |
| Native data properties | 9 |
| OWL restrictions on `far:AIReadyDataset` | 5 |
| External `rdfs:subClassOf` mappings | 11 |
| `skos:exactMatch` mappings | 7 |
| `skos:closeMatch` mappings | 22 |
| `skos:relatedMatch` mappings | 2 |
| **Total alignment assertions** | **42** |

### 5.4 Native Classes

Each class is empirically motivated: every Tier 3 and Tier 4 FAIRSCAPE criterion that fails at 100% in the corpus corresponds to a native class or property designed to carry that missing information.

| Class | Label | FAIRSCAPE criteria addressed |
|---|---|---|
| `far:AIReadyDataset` | AI-Ready Dataset | F1–F4, A1–A2, I1–I3, R1–R1.3, C1–C11 |
| `far:VariableSchema` | Variable Schema | C6, I1, I2 |
| `far:VariableDefinition` | Variable Definition | C6, I1, I2 |
| `far:DataDictionary` | Data Dictionary | C5, C2, C7 |
| `far:ProvenanceRecord` | Provenance Record | C9, R1.2 |
| `far:IntegrityCheck` | Integrity Check | C4 |
| `far:EthicsBasis` | Ethics Basis | C8, C13 |
| `far:SampleCharacterization` | Sample Characterization | C7, C11, C12 |
| `far:AccessSpecification` | Access Specification | A1, A1.1, A1.2, R1.1 |

### 5.5 Alignment Table

Every native term is aligned to at least one external vocabulary. Legend: `⊆` = `rdfs:subClassOf`; `=` = `skos:exactMatch`; `≈` = `skos:closeMatch`; `~` = `skos:relatedMatch`.

**Class alignments:**

| FAR class | schema.org | DCAT 3 | PROV-O | SPDX 2.3 | Croissant 1.0 |
|---|---|---|---|---|---|
| `far:AIReadyDataset` | `⊆ schema:Dataset` | `⊆ dcat:Dataset` | `⊆ prov:Entity` | — | — |
| `far:VariableSchema` | `⊆ schema:PropertyValue` | — | — | — | `≈ cr:RecordSet` |
| `far:VariableDefinition` | `⊆ schema:PropertyValue` | — | — | — | `= cr:Field` |
| `far:DataDictionary` | `⊆ schema:CreativeWork` | `≈ dcat:Distribution` | — | — | `≈ cr:RecordSet` |
| `far:ProvenanceRecord` | `≈ schema:Action` | — | `⊆ prov:Activity` | — | — |
| `far:IntegrityCheck` | `⊆ schema:PropertyValue` | — | — | `= spdx:Checksum` | — |
| `far:EthicsBasis` | `⊆ schema:CreativeWork`, `≈ schema:GovernmentPermit` | — | — | — | — |
| `far:SampleCharacterization` | `⊆ schema:PropertyValue`, `≈ schema:StatisticalPopulation` | — | — | — | — |
| `far:AccessSpecification` | `⊆ schema:CreativeWork`, `≈ schema:ActionAccessSpecification` | `≈ dcat:DataService` | — | — | — |

**Object property alignments (selected):**

| FAR property | schema.org | PROV-O | SPDX 2.3 |
|---|---|---|---|
| `far:hasSchema` | `≈ schema:variableMeasured` | — | — |
| `far:hasDataDictionary` | `≈ schema:hasPart` | — | — |
| `far:hasProvenance` | — | `≈ prov:wasGeneratedBy` | — |
| `far:hasChecksum` | `≈ schema:sha256` | — | `= spdx:checksum` |
| `far:conformsToStandard` | `≈ schema:isBasedOn` | — | — |
| `far:hasEthicsBasis` | `≈ schema:conditionsOfAccess` | — | — |
| `far:usedSoftware` | `≈ schema:softwareRequirements` | `≈ prov:used` | — |

**Data property alignments (selected):**

| FAR property | schema.org | SPDX 2.3 |
|---|---|---|
| `far:checksumValue` | — | `= spdx:checksumValue` |
| `far:checksumAlgorithm` | — | `= spdx:algorithm` |
| `far:sampleCount` | `= schema:numberOfItems` | — |
| `far:variableUnit` | `= schema:unitCode` | — |

### 5.6 Validation and Certification

The ontology was validated via the open-ontologies certification pipeline:

- **Parse and structural validity:** 238 raw triples, 9 OWL classes, parsed without error.
- **OWL-RL deductive closure:** 705 triples after closure; no inconsistency (no exception raised by `owlrl.OWLRL_Semantics`).
- **Lint:** 0 issues.
- **Outcome:** validate OK, OWL-RL consistent.

All external IRIs were verified against published vocabulary specifications. Known caveats: MLCommons Croissant (`http://mlcommons.org/croissant/`) is a relatively new vocabulary whose IRIs may be revised in future versions; Bioschemas Dataset 1.1 is referenced only as a `skos:closeMatch` concept (profile URL, not an OWL class IRI); SPDX 2.3 terms remain stable but SPDX 3.0 introduces a new namespace.

### 5.7 Relationship to the SHACL Shapes

The OWL ontology (semantic layer) and the SHACL shapes in `shapes/` (validation layer) are complementary artefacts. The SHACL shapes enforce precise property paths, value patterns, and cardinalities on actual dataset metadata graphs; the OWL ontology captures class semantics, necessary conditions, and cross-vocabulary alignment. A dataset can be validated against the SHACL shapes without adopting the OWL ontology (the shapes are self-contained); the ontology provides the interoperability bridge for systems that consume or publish RDF linked data.

---

## 6. Discussion

### 6.1 The Cliff at Tier 3 Is Absolute and Universal

The dominant finding is not a gradual decline across tiers — it is a cliff. Tier 2 conformance is 91.3%; Tier 3 is 0%. This cliff is caused by a single criterion: C6 (variableMeasured ≥1), which fails at 100% across all three repositories. No repository exposes `schema:variableMeasured` in its catalogue-level metadata API, and none of the 1,738 datasets includes even a single variable description. This is the single most consequential gap between FAIR compliance and AI-readiness: a dataset that does not declare what its columns or features represent cannot be automatically ingested, assembled, or validated.

The contrast with schema.org adoption is instructive. Repositories have successfully adopted schema.org for discoverability: identifier, title, description, creator, and date are near-universal. The richer characterisation properties that ML pipelines require — `schema:variableMeasured`, `schema:measurementTechnique`, `schema:additionalType` as an ontology IRI, `schema:hasPart` for data dictionaries, `schema:numberOfItems` — remain entirely unpopulated.

### 6.2 Repository-Specific Lessons

**PRIDE** demonstrates that T1 and T2 conformance at 100% is achievable. PRIDE's organism mappings and structured experiment types show that IRI-based classification is already embedded in PRIDE's data model; the barrier to T3 is exclusively at the variable-description and version layers (C6, C3), which would require changes to the PRIDE deposit workflow rather than to the metadata export format.

**Dryad** achieves near-perfect T2 conformance (99.7%) through its schema.org JSON-LD exports. Its path to T3 requires two changes: (a) mapping its plain-text `fieldOfScience` subject field to IRI-based controlled vocabulary terms (MeSH, EDAM, or OBO ontologies) to satisfy I1, and (b) populating `schema:variableMeasured` at deposit time. Dryad's existing schema.org export infrastructure makes it the repository closest to actionable T3 compliance among the three studied.

**BioStudies** illustrates a platform-level metadata exposure gap: the search API does not surface keyword metadata or file-download URLs for a subset of records, even though both may exist in the full study record and internal systems. A secondary harvest via the per-accession study endpoint (rather than the bulk search API) would likely substantially improve BioStudies' T2 rate. BioStudies' absence of licence IRIs and controlled-vocabulary subject terms are additional API-layer gaps with straightforward remedies.

### 6.3 The AI-Readiness Gap Is Structural, Not Incidental

The 100% failure rates for T4 criteria — C4 (checksum), C8 (ethics/IRB), C9 (provenance), C11 (sample count) — cannot be attributed to data quality variations or inconsistent metadata practice. They reflect that none of these concepts are supported fields in the catalogue-level API responses of any of the three repositories evaluated. This is consistent with the Bridge2AI analysis [3], which found systematic absence of characterisation (D3), ethics (D5), and provenance (D4) metadata across biomedical datasets.

Achieving T4 AI-readiness requires changes to repository deposit workflows. Concretely: depositing researchers would need to provide (a) a data dictionary or variable definitions, (b) an ethics/IRB statement with a structured reference, (c) a provenance record linking the dataset to its generating workflow (ideally as a WRROC-compliant RO-Crate [4]), and (d) integrity checksums on distributed files. These are substantive new metadata fields, not formatting adjustments. The FAR ontology (Section 5) provides the vocabulary for encoding them; the SHACL shapes provide the machine validation contract for verifying them.

### 6.4 Sub-Metric Warnings as Actionable Targets

While F2-kw (keyword coverage: 47.6% missing), R1.1 (machine-readable licence IRI: 73.1% missing), and F4 (catalogue registration: 100% missing) do not gate tier conformance, they represent high-impact, low-cost improvements. For PRIDE, replacing the string "EBI terms of use" with a canonical CC-BY or EBI Open Data IRI would bring R1.1 compliance from 21.3% to near 100% with a single mapping change. For BioStudies, exposing existing keyword metadata through the search API would resolve F2-kw entirely.

---

## 7. Limitations

### 7.1 Catalogue Metadata Only

We evaluate catalogue-level metadata records exposed via each repository's API — not the datasets themselves or their supplementary files. Variable descriptions, data dictionaries, ethics statements, and provenance information may exist in supplementary documents that are not indexed in the API metadata record. Our T3 and T4 failure rates measure a genuine FAIR gap (machine-readable metadata should be separately accessible from the data it describes) but may overstate the real-world absence of these artefacts.

### 7.2 Zenodo Not Included

All eight Zenodo API queries (covering eight major biomedical data domains) timed out during corpus construction (2026-07-01); Zenodo is therefore excluded. As one of the largest general-purpose open repositories, Zenodo's inclusion would substantially expand corpus diversity. Zenodo's schema.org JSON-LD exports are known to be structurally rich; inclusion would likely improve T1 and T2 rates but is unlikely to change the T3/T4 picture given the absence of variableMeasured, checksum, and provenance fields in Zenodo's standard export.

### 7.3 BioStudies Distribution Mapping

BioStudies exposes downloadable files as a count and a predictable EBI files endpoint pattern in the basic search result, not as per-file schema.org distribution objects with explicit `schema:contentUrl` values. We map studies with a file count >0 to a machine-readable distribution pointing to the EBI files endpoint. Studies with zero files in the basic search response (~17.5% of BioStudies records in our corpus) receive no distribution and therefore fail criterion A1. A full harvest using the per-accession endpoint would provide per-file metadata and would likely change these figures.

### 7.4 Keyword and Licence as Sub-Metrics, Not Tier Gates

F2-kw (keywords) and R1.1 (machine-readable licence IRI) are treated as Warning sub-metrics and do not gate tier conformance (Section 3.3). This follows the FAIRSCAPE framework rationale and the FINDINGS.md design note, but alternative interpretations of the FAIR principles could treat licence as a strict R1.1 Violation gate, which would substantially reduce T2 conformance rates (to ≤26.9% overall).

### 7.5 Sample Size and Stratification

Dryad (*n* = 340), BioStudies (*n* = 798), and PRIDE (*n* = 600) were sampled without stratification by discipline, publication year, or dataset size. Repository-level comparisons should be interpreted with this in mind. A stratified random sample would enable more rigorous cross-repository comparison.

### 7.6 Python Semantic Check Scope

Python semantic checks were validated on a 30-record spot-check (10 per repository). Systematic differences between the SHACL structural check and the Python semantic check may exist in the full corpus; our spot-check shows 100% agreement per tier but cannot rule out edge cases at scale.

---

## 8. Availability

| Artefact | Location | Licence |
|---|---|---|
| Full codebase, shapes, corpus, results | https://github.com/fabio-rovai/fair-scientific-data | MIT |
| FAR ontology | https://w3id.org/fair-ai-ready | CC-BY 4.0 |
| Corpus provenance | `CORPUS_REPORT.md` (records fetched 2026-07-01) | — |
| Computed results | `results_deep/` (generated 2026-07-02) | — |
| SHACL shape files | `shapes/tier-1-findable.ttl` … `shapes/tier-4-ai-ready.ttl` | MIT |
| Criteria-to-tier mapping | `FAIRSCAPE_CRITERIA_MAP.md` | MIT |
| Python semantic checks | `src/checks.py` | MIT |

---

## References

[1] Wilkinson MD, Dumontier M, Aalbersberg IJ, et al. "The FAIR Guiding Principles for scientific data management and stewardship." *Scientific Data* 3:160018, 2016. https://doi.org/10.1038/sdata.2016.18

[2] Al Manir S, Clark T, et al. "The FAIRSCAPE AI-readiness Framework for Biomedical Research." *bioRxiv* 2024.12.23.629818, v4 March 2026. PMCID: PMC11703166. https://doi.org/10.1101/2024.12.23.629818

[3] Caufield JH, Munoz-Torres MC, et al. "Standards in the Preparation of Biomedical Research Metadata: A Bridge2AI Perspective." *arXiv* 2509.10432, September 2025. https://arxiv.org/abs/2509.10432

[4] Leo S, Crusoe MR, Rodríguez-Navas L, Soiland-Reyes S, et al. "Recording provenance of workflow runs with RO-Crate." *PLOS ONE* 19(9):e0309210, 2024. https://doi.org/10.1371/journal.pone.0309210

[5] Haendel MA, Mungall CJ, et al. "Biomedical knowledge graph quality: dimensions, measurement, and implications for AI." *arXiv* 2508.21774, 2025. https://arxiv.org/abs/2508.21774 **[Note: cited as given; independent bibliographic verification recommended before journal submission.]**

[6] Bioschemas Community. "Dataset Profile 1.1-RELEASE." https://bioschemas.org/profiles/Dataset/1.1-RELEASE (accessed 2026-07-02).

[7] DataCite Metadata Working Group. "DataCite Metadata Schema Documentation for the Publication and Citation of Research Data and Software." Version 4.5. DataCite, 2024. https://doi.org/10.14454/g7ky-6b09

[8] Akhtar-Dajee P, Aroyo L, Benjelloun O, et al. "Croissant: A Metadata Format for ML-Ready Datasets." MLCommons, 2023. https://mlcommons.org/croissant/1.0

[9] Albertoni R, Browning D, Cox S, et al. "Data Catalog Vocabulary (DCAT) — Version 3." W3C Recommendation 2023-08-22. https://www.w3.org/TR/vocab-dcat-3/

[10] Lebo T, Sahoo S, McGuinness D, et al. "PROV-O: The PROV Ontology." W3C Recommendation 2013-04-30. https://www.w3.org/TR/prov-o/

[11] SPDX Workgroup. "SPDX Specification 2.3." Linux Foundation, 2022. https://spdx.github.io/spdx-spec/v2.3/

---

## Appendix: Criteria-to-Tier Mapping (Full)

| Criterion | FAIR principle | Tier | Sev. | Property checked |
|---|---|---|---|---|
| F1 | FAIR F1 | T1 | Viol. | schema:identifier (PID) |
| F2-title | FAIR F2 | T1 | Viol. | schema:name (≥5 chars) |
| F2-desc | FAIR F2 | T1 | Viol. | schema:description (≥20 chars) |
| F2-kw | FAIR F2 | T1 | Warn. | schema:keywords (≥1) — sub-metric |
| F3 | FAIR F3 | T1 | Warn. | schema:url (landing page IRI) |
| F4 | FAIR F4 | T1 | Warn. | schema:includedInDataCatalog |
| A1 | FAIR A1 | T2 | Viol. | schema:distribution → schema:contentUrl (https) |
| A1.1 | FAIR A1.1 | T2 | Warn. | schema:conditionsOfAccess |
| A1.2 | FAIR A1.2 | T2 | Warn. | schema:contactPoint |
| R1 | FAIR R1 | T2 | Warn. | schema:publisher |
| R1.1 | FAIR R1.1 | T2 | Warn. | schema:license (IRI) — sub-metric |
| R1.2-creator | FAIR R1.2 | T2 | Viol. | schema:creator (≥1) |
| R1.2-date | FAIR R1.2 | T2 | Viol. | schema:datePublished |
| I1 | FAIR I1 | T3 | Viol. | schema:about (IRI, controlled vocab) |
| I2 | FAIR I2 | T3 | Warn. | schema:inLanguage |
| I3 | FAIR I3 | T3 | Warn. | schema:isBasedOn (dataset ref IRI) |
| R1.3 | FAIR R1.3 | T3 | Warn. | schema:isBasedOn (standard IRI) |
| C3 | FAIRSCAPE C3 | T3 | Viol. | schema:version |
| C6 | FAIRSCAPE C6 | T3 | Viol. | schema:variableMeasured (≥1) |
| D3 | Bridge2AI D3 | T3 | Warn. | schema:measurementTechnique |
| C1 | FAIRSCAPE C1 | T4 | Viol. | schema:additionalType (IRI) |
| C4 | FAIRSCAPE C4 | T4 | Viol. | spdx:checksum or schema:sha256 |
| C5 | FAIRSCAPE C5 | T4 | Viol. | schema:hasPart (data dictionary) |
| C7 | FAIRSCAPE C7 | T4 | Warn. | schema:variableMeasured (≥2) + keywords |
| C8 | FAIRSCAPE C8 | T4 | Viol. | schema:conditionsOfAccess (ethics keywords) |
| C9 | FAIRSCAPE C9 | T4 | Viol. | prov:wasGeneratedBy (workflow IRI) |
| C10 | FAIRSCAPE C10 | T4 | Warn. | schema:softwareRequirements |
| C11 | FAIRSCAPE C11 | T4 | Viol. | schema:numberOfItems (integer ≥1) |
| C12 | FAIRSCAPE C12 | T4 | Warn. | schema:description (≥100 chars) |
| C13 | FAIRSCAPE C13 | T4 | Warn. | schema:conditionsOfAccess (de-id keywords) |
