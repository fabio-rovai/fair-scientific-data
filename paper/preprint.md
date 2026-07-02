# FAIR-AI-Readiness of Open Scientific Data Repositories: A Tiered Evaluation of 1,738 Datasets Across Dryad, BioStudies, and PRIDE

**Fabio Lora**¹  

¹ The Tesseract Academy, London, UK  
Correspondence: fabio@thetesseractacademy.com  

**Date:** 2 July 2026  
**Version:** preprint v1  
**Repository:** https://github.com/fabiolora/fair-scientific-data (MIT Licence)

---

## Abstract

Machine learning for biomedicine demands not merely findable data, but data whose metadata is rich enough for automated ingestion, quality assessment, and auditable provenance. Yet the degree to which real open-access repositories satisfy the emerging AI-readiness extensions to the FAIR principles has not been measured at scale. We evaluate 1,738 datasets drawn from three major open repositories — Dryad (n = 340), BioStudies (n = 798), and PRIDE (n = 600) — against a four-tiered FAIR-AI-Readiness contract derived from the FAIRSCAPE framework (28 criteria spanning F1–F4, A1–A1.2, R1–R1.3, I1–I3, and C1–C13), validated using SHACL shapes and Python semantic checks, with 96.7–100% Python/SHACL agreement on a spot-checked sample. Results show **52.3% of datasets pass Tier 1** (Findable: identifier, title, description, keywords), **25.1% pass Tier 2** (Accessible + Reusable: licence IRI, distribution, creator, publication date), and **0% pass Tier 3** (Interoperable + Schema-structured) or **Tier 4** (AI-Ready). The most universally failed criteria are: variableMeasured (100% failure across all repositories), integrity checksums (100%), ethics/IRB documentation (100%), pipeline provenance (100%), and sample count (100%). Repository performance varies sharply: Dryad achieves 90.9% at Tiers 1–2 but fails Tier 3 due to absent controlled-vocabulary subject IRIs; PRIDE reaches 100% at Tier 1 but only 21.3% at Tier 2 due to non-standard licence strings; BioStudies fails Tier 1 entirely because its search API omits keyword metadata. These findings reveal a systematic gap between the metadata that repositories currently publish and what AI-ready data pipelines require, and motivate specific, actionable recommendations for each repository type.

**Keywords:** FAIR data, AI-readiness, metadata quality, SHACL validation, data repositories, schema.org, FAIRSCAPE, BioStudies, Dryad, PRIDE

---

## 1. Introduction

The FAIR principles — Findable, Accessible, Interoperable, Reusable — published by Wilkinson et al. in 2016 [1] established a widely adopted framework for scientific data governance. FAIR compliance, however, was never intended to be binary; it exists along a spectrum whose depth requirements grow considerably when data must serve as input to machine learning (ML) pipelines. Where a human can compensate for a missing variable description by reading a supplementary document, an automated ML ingestion script cannot.

Several recent frameworks have codified what "AI-ready" metadata means in practice. The FAIRSCAPE AI-Readiness Framework [2] introduces 28 criteria (labelled C1–C13, plus the classical F, A, I, R dimensions) covering data-type identification, checksum integrity, ethics governance, pipeline provenance, and statistical characterisation. The Bridge2AI initiative [3] articulates seven readiness dimensions (D1–D7) from the perspective of large-scale biomedical data collection. The WRROC provenance profile [4] specifies how workflow runs should be captured to enable reproducible AI training. The biomedical knowledge-graph quality literature [5] has further highlighted how metadata incompleteness propagates downstream into unreliable model training.

Despite this growing normative landscape, empirical measurement of AI-readiness across real open-access repositories remains sparse. Most prior assessments either evaluate a handful of curated examples, focus on a single repository type, or assess FAIR compliance without the AI-ready extensions. We address this gap with a corpus-scale, criterion-by-criterion evaluation.

**Contributions.** (1) A fully open corpus of 1,738 real dataset metadata records from three repositories, normalised to a common schema.org representation using a profile-mapping library (profiles.py). (2) A tiered SHACL contract (four TTL shape files) covering all 28 FAIRSCAPE criteria plus extensions for WRROC provenance (C9) and de-identification (C13). (3) Quantitative failure rates computed from the real corpus for every criterion, with per-repository breakdowns. (4) Actionable recommendations grounded in the empirical results. All code, shapes, and data are available under the MIT licence.

---

## 2. Related Work

**FAIR principles and assessment.** Wilkinson et al. [1] defined the 15 FAIR sub-principles across the four dimensions. Subsequent tools such as FAIR Checker, F-UJI, and FAIRshake operationalise automated assessment, but typically test a single record against generic FAIR criteria rather than performing corpus-scale evaluation with AI-specific extensions.

**FAIRSCAPE AI-Readiness Framework.** Al Manir and Clark [2] introduced FAIRSCAPE to bridge FAIR compliance and AI operational requirements, defining 28 criteria with explicit traceability to the FAIR sub-principles. Their C1–C13 characterisation criteria (data type, format, version, checksum, data dictionary, variable descriptions, statistical summary, ethics, provenance, software, sample count, completeness, de-identification) go substantially beyond classical FAIR. Our work is the first corpus-scale empirical evaluation of these criteria across multiple repositories.

**Bridge2AI metadata readiness.** Caufield et al. [3] describe seven metadata readiness dimensions from the Bridge2AI programme, covering findability, accessibility, characterisation (D3), provenance (D4), ethics (D5), standards (D6), and computability (D7). Our tiered contract is explicitly mapped to these dimensions.

**WRROC provenance.** The Workflow Run RO-Crate (WRROC) specification [4] (Leo et al., *PLoS One*, 2024) defines a canonical pattern for capturing computational provenance via prov:wasGeneratedBy linking a dataset to its generating workflow run. Our Tier 4 includes this as criterion C9.

**Biomedical knowledge-graph quality.** Haendel, Mungall et al. [5] (arXiv:2508.21774) analyse quality dimensions in biomedical knowledge graphs, finding that metadata gaps — missing entity descriptions, absent provenance, and incomplete concept mappings — are the primary barriers to reliable graph-based AI. Our findings extend this analysis to the dataset-metadata layer.

---

## 3. Methods

### 3.1 Corpus

We built a corpus of 1,738 real dataset metadata records from three open-access repositories, collected on 2026-07-01 (see CORPUS_REPORT.md):

| Repository | N | Metadata format | Fetch method |
|---|---|---|---|
| Dryad | 340 | schema.org JSON-LD | Dryad API v2 |
| BioStudies | 798 | BioStudies JSON | EBI BioStudies search API |
| PRIDE | 600 | PRIDE JSON | EBI PRIDE API |

Zenodo was targeted (8 queries) but all requests timed out; this is noted as a limitation (Section 6.1). Within each repository, records were sampled without subject-domain filtering to ensure diversity.

### 3.2 Metadata Normalisation

Heterogeneous repository-specific formats were normalised to a common schema.org-based RDF representation using `src/profiles.py`. Key mappings applied:

- **Dryad JSON-LD**: already schema.org; the normaliser remaps `http://schema.org/` predicates to `https://schema.org/` and coerces `schema:Date`-typed date literals to `xsd:dateTime`. The dataset `@id` (a DOI IRI) is asserted as `schema:identifier`. A distribution stub is added from `schema:url` when no `schema:distribution` is present.
- **BioStudies JSON**: `accession` → `schema:identifier` (EBI URL); `title` → `schema:name`; `content` → `schema:description`; `author` string → `schema:creator`; `release_date` → `schema:datePublished`.
- **PRIDE JSON**: `doi` → `schema:identifier`; `projectDescription` → `schema:description`; `keywords` → `schema:keywords`; PRIDE NEWT organism accessions (e.g., `NEWT:10090`) → `schema:about` with NCBI taxonomy IRIs; experiment types → `schema:additionalType` with PRIDE ontology IRIs.

All 1,738 records were normalised successfully (100% success rate).

### 3.3 SHACL Validation Contract

We define a four-tier SHACL contract in `shapes/`:

| Tier | File | FAIR dimensions | Key criteria (Violations) |
|---|---|---|---|
| T1 | tier-1-findable.ttl | F1–F4 | F1 (identifier), F2-title, F2-desc, F2-kw |
| T2 | tier-2-accessible-reusable.ttl | A1–A1.2, R1–R1.2 | R1.1 (licence IRI), A1 (distribution+contentUrl), R1.2-creator, R1.2-date |
| T3 | tier-3-interoperable-schema.ttl | I1–I3, R1.3, C3, C6 | I1 (schema:about IRI), C6 (variableMeasured), C3 (version) |
| T4 | tier-4-ai-ready.ttl | C1–C13 | C1 (additionalType IRI), C4 (checksum), C5 (hasPart), C8 (ethics), C9 (provenance), C11 (sample count) |

A dataset "passes" tier N when it has zero `sh:Violation`-severity results for that tier's shape, cumulatively (passing T2 requires also passing T1, etc.). `sh:Warning` results are recorded but do not block conformance.

### 3.4 Python Semantic Checks

Eleven checks in `src/checks.py` cover criteria not fully expressible in SHACL: DOI/ARK/Handle format validation (F1), http(s) protocol verification (A1), recognised open-licence detection against the SPDX list (R1.1), ORCID IRI format check (R1.2), semver/date version format (C3), SHA-256 hex checksum validation (C4), statistical-summary keyword scanning (C7), ethics/IRB keyword scanning (C8, C12), positive-integer sample count (C11), and de-identification keyword scanning (C13). These complement the structural SHACL constraints.

### 3.5 Validation Consistency

Python per-criterion checks and SHACL results were compared on a spot-check sample of 30 records (10 per repository). Agreement was 100% for T1, 96.7% for T2 (one Dryad record with an edge-case date format), and 100% for T3.

---

## 4. Results

### 4.1 Overall Tier Conformance

**Table 1. Tier conformance across 1,738 datasets.**

| Tier | Criteria class | Passed | N | Conformance rate |
|---|---|---|---|---|
| T1 | Findable (F1–F4 Violations) | 909 | 1738 | **52.3%** |
| T2 | Accessible + Reusable (A1, R1.1–R1.2 Violations) | 437 | 1738 | **25.1%** |
| T3 | Interoperable + Schema-Structured (I1, C3, C6 Violations) | 0 | 1738 | **0.0%** |
| T4 | AI-Ready (C1, C4, C5, C8, C9, C11 Violations) | 0 | 1738 | **0.0%** |

Fewer than half of all datasets meet even the minimum Findability requirement (T1). No dataset in the corpus passes Tier 3 or Tier 4.

The distribution of highest tier passed (Figure 3) shows:

- **47.7%** (n = 829) fail even T1 — primarily all BioStudies records
- **27.2%** (n = 472) reach T1 only — principally PRIDE records with a problematic licence
- **25.1%** (n = 437) reach T2 — Dryad records (n = 309) plus a subset of PRIDE (n = 128)
- **0%** reach T3 or T4

### 4.2 Per-Repository Tier Conformance

**Table 2. Tier conformance by repository.**

| Repository | N | T1 Findable | T2 Accessible | T3 Interoperable | T4 AI-Ready |
|---|---|---|---|---|---|
| Dryad | 340 | **90.9%** | **90.9%** | 0.0% | 0.0% |
| BioStudies | 798 | 0.0% | 0.0% | 0.0% | 0.0% |
| PRIDE | 600 | **100.0%** | 21.3% | 0.0% | 0.0% |

**Dryad** is the strongest performer: 309/340 records (90.9%) pass both T1 and T2. The 31 T1 failures arise from records missing keywords in the exported JSON-LD (8.8% F2-kw failure rate within Dryad). Dryad records uniformly carry a CC0 or CC-BY licence IRI and a schema:distribution stub, and their schema.org JSON-LD exports include creator and publication date, explaining the identical T1 and T2 rates.

**PRIDE** achieves 100% at T1 (all 600 records have identifier, title, description, keywords) but only 21.3% at T2. The blocking criterion is R1.1 (licence IRI): 78.7% of PRIDE records carry the string "EBI terms of use" as the licence value, which is a natural-language description rather than a machine-readable IRI pointing to a recognised open-licence standard. PRIDE data is publicly accessible under EBI's open data policy, but the metadata does not encode this in a SHACL-verifiable form.

**BioStudies** scores 0% at all tiers. The proximate cause is F2-kw: the BioStudies basic search API returns no `keywords` field for any of the 798 records in our sample, causing a 100% failure on the keyword presence criterion (F2-kw). This is a metadata-exposure gap at the API level: keyword metadata exists in BioStudies' internal systems but is not surfaced in the search-result JSON. Additionally, BioStudies records carry no licence IRI, no distribution/download URL, and no controlled-vocabulary subject terms — all requirements for T2 and beyond.

### 4.3 Per-Criterion Failure Rates

**Table 3. Failure rates for all 30 criteria (sorted by failure rate, Violations highlighted).**

| Criterion | Tier | Severity | Failure rate | Description |
|---|---|---|---|---|
| C6 | T3 | **Violation** | **100.0%** | Variables measured (schema:variableMeasured ≥1) |
| C4 | T4 | **Violation** | **100.0%** | Integrity checksum (spdx:checksum or schema:sha256) |
| C8 | T4 | **Violation** | **100.0%** | Ethics/IRB documentation (schema:conditionsOfAccess) |
| C9 | T4 | **Violation** | **100.0%** | Pipeline provenance (prov:wasGeneratedBy IRI) |
| C11 | T4 | **Violation** | **100.0%** | Sample count (schema:numberOfItems ≥1 integer) |
| C5 | T4 | **Violation** | 99.9% | Data dictionary (schema:hasPart) |
| C3 | T3 | **Violation** | 80.4% | Version identifier (schema:version) |
| R1.1 | T2 | **Violation** | 73.1% | Machine-readable licence IRI (schema:license as IRI) |
| I1 | T3 | **Violation** | 65.5% | Controlled-vocabulary subject IRI (schema:about IRI) |
| C1 | T4 | **Violation** | 65.5% | Data type IRI (schema:additionalType IRI) |
| F2-kw | T1 | **Violation** | 47.6% | Keywords (schema:keywords ≥1) |
| A1 | T2 | **Violation** | 45.9% | Distribution with http(s) contentUrl |
| F4 | T1 | Warning | 100.0% | Registered in catalogue (schema:includedInDataCatalog) |
| A1.1 | T2 | Warning | 100.0% | Access conditions declared (schema:conditionsOfAccess) |
| A1.2 | T2 | Warning | 100.0% | Contact point (schema:contactPoint) |
| R1.3 | T3 | Warning | 100.0% | Conforms to community standard (schema:isBasedOn) |
| I3 | T3 | Warning | 100.0% | Qualified reference (schema:isBasedOn) |
| C10 | T4 | Warning | 100.0% | Software reference (schema:softwareRequirements) |
| C7 | T4 | Warning | 100.0% | Statistical summary (schema:variableMeasured ≥2) |
| C13 | T4 | Warning | 100.0% | De-identification (schema:conditionsOfAccess) |
| I2 | T3 | Warning | 80.5% | Language declared (schema:inLanguage) |
| D3 | T3 | Warning | 65.5% | Measurement technique (schema:measurementTechnique) |
| R1 | T2 | Warning | 45.9% | Publisher declared (schema:publisher) |
| C12 | T4 | Warning | 1.4% | Completeness/missingness (description ≥100 chars) |
| R1.2-creator | T2 | **Violation** | 0.6% | Creator present (schema:creator) |
| F2-desc | T1 | **Violation** | 0.1% | Description ≥20 chars (schema:description) |
| F1 | T1 | **Violation** | 0.0% | Globally unique PID (schema:identifier) |
| F2-title | T1 | **Violation** | 0.0% | Title (schema:name ≥5 chars) |
| F3 | T1 | Warning | 0.0% | Landing page IRI (schema:url) |
| R1.2-date | T2 | **Violation** | 0.0% | Publication date (schema:datePublished) |

Several findings merit emphasis:

**Universal AI-readiness failures.** C6 (variableMeasured), C4 (checksum), C8 (ethics), C9 (provenance), and C11 (sample count) fail at 100% across all three repositories. No repository in this corpus provides variable descriptions, integrity checksums on distributions, ethics/IRB documentation, workflow provenance, or quantitative sample counts in their exported metadata.

**The C5 near-miss.** C5 (data dictionary/schema:hasPart) fails for 99.9% of records: only one Dryad record carries a `schema:hasPart` reference. Data dictionaries exist in supplementary files for many datasets but are not exposed in the metadata record.

**Version (C3) and controlled vocabulary (I1) are the T3 blockers.** The 80.4% failure on C3 reflects that PRIDE and BioStudies records have no version field in their API outputs, and that Dryad's version field (present) was correctly captured. The 65.5% failure on I1 reflects that Dryad does not use controlled-vocabulary term IRIs (e.g., MeSH, EDAM, OBO ontologies) for subject classification — its `fieldOfScience` is a plain text string. PRIDE records, by contrast, pass I1 (0% failure within PRIDE) because organism accessions are mapped to NCBI taxonomy IRIs.

**The licence gap is surmountable.** The 73.1% overall failure on R1.1 (licence IRI) is almost entirely a PRIDE artefact: PRIDE records carry "EBI terms of use" as a literal string. Adding a single canonical CC0/CC-BY IRI mapping in PRIDE metadata export would bring their R1.1 compliance to near 100%.

**Metadata bottoms out at F2-kw.** For BioStudies, the single criterion causing all 798 records to fail Tier 1 is keyword absence (100% failure). All other T1 criteria (F1: identifier, F2-title, F2-desc, F3: landing page URL) pass at near 100%.

### 4.4 Python Semantic Check Results (Sample, n = 100)

Eleven semantic checks from `src/checks.py` were run on a 100-record sample:

| Check | Pass rate | Notes |
|---|---|---|
| F1 (DOI/ARK/Handle format) | 99% | 1 BioStudies record with non-DOI URL |
| R1.1 (recognised open licence) | 100% | All licences in sample were CC or EBI (flagged via warnings) |
| R1.2 (creator ORCID IRI) | 0% | No record in sample has creator with valid ORCID IRI |
| C7 (statistical-summary keywords) | 4% | Very few descriptions mention sample sizes, distributions |
| C8 (ethics/IRB keywords) | 0% | No record mentions IRB, consent, or ethics approval |
| C12 (completeness keywords) | 26% | Some long descriptions mention missingness |
| C13 (de-identification keywords) | 2% | Almost no records document de-identification |

The 0% ORCID rate confirms a known gap: even repositories that expose creator names rarely expose structured ORCID identifiers in exported metadata.

---

## 5. Discussion

### 5.1 The Cliff After Tier 2

The most striking finding is the cliff: from 25.1% conformance at T2 to 0% at T3. This is not a gradual decline. Every single dataset fails Tier 3 because C6 (variableMeasured) fails at 100% across all repositories. Variable descriptions — what the columns or features in a dataset represent — are the single most critical metadata gap for AI pipelines, and no repository in our sample exposes them.

The contrast with schema.org adoption is instructive. Foundational metadata — title, identifier, description, creator, publication date — is universally or near-universally present. Repositories have adopted schema.org for discoverability. But the richer characterisation properties (`variableMeasured`, `measurementTechnique`, `additionalType` as ontology IRI, `hasPart` for data dictionaries, `numberOfItems`) that ML pipelines actually need remain largely unpopulated.

### 5.2 Repository-Specific Lessons

**Dryad** is the closest to AI-readiness readiness among the three repositories, but is blocked by two structural choices. First, its subject classification uses plain-text strings (`fieldOfScience: "Biological sciences"`) rather than IRI-based controlled vocabulary terms. Mapping to MeSH or EDAM would immediately address I1 and enable T3. Second, Dryad's JSON-LD export does not include `schema:variableMeasured`, `schema:version` for sub-file distributions, or integrity checksums — gaps that would need to be addressed upstream at deposit time.

**PRIDE** demonstrates that a single metadata field can determine two entire tiers. The licence string "EBI terms of use" blocks R1.1 for 78.7% of records, keeping them at T1 despite otherwise rich metadata. PRIDE's experiment-type taxonomy (PRIDE ontology, already used for `schema:additionalType`) and organism mappings (NEWT → NCBI taxon IRIs) show that structured, IRI-based classification is already happening in PRIDE's internal systems — it simply needs to be surfaced as `schema:about` and `schema:license`.

**BioStudies** illustrates a platform-level FAIR gap: the search API does not expose keyword metadata even when such metadata exists internally. This is a relatively low-cost fix with high FAIR impact. BioStudies records also lack licence IRIs and download URLs in the search API response — fields that are likely present in the full study record but not in the search-result API endpoint we harvested.

### 5.3 The AI-Readiness Gap Is Structural, Not Incidental

The near-100% failure rates for T4 criteria (C4 checksum, C8 ethics, C9 provenance, C11 sample count, C5 data dictionary) cannot be attributed to inconsistent metadata practice. They reflect systematic absences: none of these criteria are commonly supported fields in the export formats of any of the three repositories. This aligns with the Bridge2AI analysis [3], which found that biomedical datasets systematically lack characterisation metadata (D3), ethics documentation (D5), and computational provenance (D4). The FAIRSCAPE framework [2] was motivated precisely by this gap.

The implication is that achieving T4 AI-readiness will require changes to repository deposit workflows, not merely metadata export improvements. Researchers depositing data would need to provide: (a) variable definitions or a data dictionary at deposit time, (b) an ethics statement with IRB approval reference, (c) a provenance record linking the dataset to its generating workflow, and (d) integrity checksums. These are substantive metadata additions, not formatting changes.

---

## 6. Limitations

### 6.1 Zenodo Not Included

All eight Zenodo API queries timed out during corpus construction. Zenodo is one of the largest open-data repositories and would provide important coverage of general scientific datasets. Inclusion of Zenodo records would likely improve T1 and T2 rates (Zenodo's schema.org JSON-LD exports are rich) but might not change the T3/T4 picture.

### 6.2 Catalogue Metadata Only

We evaluate only the catalogue-level metadata record (the metadata exposed via each repository's API), not the datasets themselves or their supplementary files. Many datasets have variable descriptions, data dictionaries, or ethics statements in supplementary documents that are not indexed in the metadata record. This is a genuine FAIR limitation — metadata and data should be separately accessible — but it means our T3/T4 failure rates may overstate the real absence of these artefacts.

### 6.3 Sample Sizes Are Unequal and Not Stratified

Dryad (n = 340), BioStudies (n = 798), and PRIDE (n = 600) were not stratified by discipline, publication year, or dataset size. Repository-level comparisons should be interpreted with this in mind.

### 6.4 BioStudies API Limitation

The BioStudies search result API returns a reduced metadata set that omits keywords and download URLs. A secondary harvest via the full study record endpoint (one request per accession rather than the bulk search endpoint) would likely substantially improve BioStudies' T1 conformance rate and change the interpretation of the BioStudies results.

### 6.5 Normalisation Choices

Several normalisation decisions affect the results. Adding `schema:identifier` from the JSON-LD `@id` field for Dryad records (when no explicit identifier property is present) follows the RDF convention that the subject IRI IS the identifier, but a stricter interpretation would flag these as F1 failures. The PRIDE distribution node is synthetic (pointing to the EBI project page rather than a file-level download URL). These choices are documented in `src/profiles.py` and `src/analyse_corpus.py`.

---

## 7. Availability

All code, shapes, corpus data, and results are available at:

**Repository:** https://github.com/fabiolora/fair-scientific-data  
**Licence:** MIT  
**Corpus provenance:** `CORPUS_REPORT.md` (records fetched 2026-07-01)  
**Results:** `results_deep/` (generated 2026-07-02)  
**Shape files:** `shapes/tier-1-findable.ttl` … `shapes/tier-4-ai-ready.ttl`

---

## References

[1] Wilkinson MD, Dumontier M, Aalbersberg IJ, et al. "The FAIR Guiding Principles for scientific data management and stewardship." *Scientific Data* 3:160018, 2016. https://doi.org/10.1038/sdata.2016.18

[2] Al Manir S, Clark T, et al. "The FAIRSCAPE AI-readiness Framework for Biomedical Research." *bioRxiv* 2024.12.23.629818, March 2026. PMCID: PMC11703166. https://doi.org/10.1101/2024.12.23.629818

[3] Caufield JH, Munoz-Torres MC, et al. "Standards in the Preparation of Biomedical Research Metadata: A Bridge2AI Perspective." *arXiv* 2509.10432, September 2025. https://arxiv.org/abs/2509.10432

[4] Leo S, Crusoe MR, Rodríguez-Navas L, Soiland-Reyes S, et al. "Recording provenance of workflow runs with RO-Crate." *PLOS ONE* 19(9):e0309210, 2024. https://doi.org/10.1371/journal.pone.0309210

[5] Haendel MA, Mungall CJ, et al. "Biomedical knowledge graph quality: dimensions, measurement, and implications for AI." *arXiv* 2508.21774, 2025. https://arxiv.org/abs/2508.21774 **[Note: cited as given in task specification; independent verification recommended before submission.]**

[6] Bioschemas Community. "Dataset Profile 1.1-RELEASE." https://bioschemas.org/profiles/Dataset/1.1-RELEASE (accessed 2026-07-02).

[7] DataCite Metadata Working Group. "DataCite Metadata Schema Documentation for the Publication and Citation of Research Data and Software." DataCite, Version 4.5, 2024. https://doi.org/10.14454/g7ky-6b09

[8] Albertoni R, Browning D, Cox S, et al. "Data Catalog Vocabulary (DCAT) — Version 3." W3C Recommendation 2023-08-22. https://www.w3.org/TR/vocab-dcat-3/

---

## Appendix A: Criteria-to-Tier Mapping

| Criterion | FAIR Principle | Tier | Severity | Property Checked |
|---|---|---|---|---|
| F1 | FAIR F1 | T1 | Violation | schema:identifier (PID) |
| F2-title | FAIR F2 | T1 | Violation | schema:name (≥5 chars) |
| F2-desc | FAIR F2 | T1 | Violation | schema:description (≥20 chars) |
| F2-kw | FAIR F2 | T1 | Violation | schema:keywords (≥1) |
| F3 | FAIR F3 | T1 | Warning | schema:url (landing page IRI) |
| F4 | FAIR F4 | T1 | Warning | schema:includedInDataCatalog |
| R1.1 | FAIR R1.1 | T2 | Violation | schema:license (IRI) |
| A1 | FAIR A1 | T2 | Violation | schema:distribution → contentUrl |
| R1.2-creator | FAIR R1.2 | T2 | Violation | schema:creator (≥1) |
| R1.2-date | FAIR R1.2 | T2 | Violation | schema:datePublished (typed) |
| A1.1 | FAIR A1.1 | T2 | Warning | schema:conditionsOfAccess |
| A1.2 | FAIR A1.2 | T2 | Warning | schema:contactPoint |
| R1 | FAIR R1 | T2 | Warning | schema:publisher |
| I1 | FAIR I1 | T3 | Violation | schema:about (IRI, controlled vocab) |
| C6 | FAIRSCAPE C6 | T3 | Violation | schema:variableMeasured (≥1) |
| C3 | FAIRSCAPE C3 | T3 | Violation | schema:version |
| R1.3 | FAIR R1.3 | T3 | Warning | schema:isBasedOn (standard IRI) |
| I2 | FAIR I2 | T3 | Warning | schema:inLanguage |
| I3 | FAIR I3 | T3 | Warning | schema:isBasedOn (dataset reference) |
| D3 | Bridge2AI D3 | T3 | Warning | schema:measurementTechnique |
| C1 | FAIRSCAPE C1 | T4 | Violation | schema:additionalType (IRI) |
| C4 | FAIRSCAPE C4 | T4 | Violation | spdx:checksum or schema:sha256 |
| C5 | FAIRSCAPE C5 | T4 | Violation | schema:hasPart (data dictionary) |
| C8 | FAIRSCAPE C8 | T4 | Violation | schema:conditionsOfAccess (ethics) |
| C9 | FAIRSCAPE C9 | T4 | Violation | prov:wasGeneratedBy (workflow IRI) |
| C11 | FAIRSCAPE C11 | T4 | Violation | schema:numberOfItems (integer ≥1) |
| C10 | FAIRSCAPE C10 | T4 | Warning | schema:softwareRequirements |
| C7 | FAIRSCAPE C7 | T4 | Warning | schema:variableMeasured (≥2) |
| C12 | FAIRSCAPE C12 | T4 | Warning | schema:description (≥100 chars) |
| C13 | FAIRSCAPE C13 | T4 | Warning | schema:conditionsOfAccess (de-id) |
