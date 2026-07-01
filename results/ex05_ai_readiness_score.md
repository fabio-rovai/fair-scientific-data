# FAIR AI-Readiness Score Report

**Assessment file**: `fair-ai-readiness/ex05_bridge2ai_assessment.yaml`

## Dimension Scores

| Dimension | Earned | Max | Score | Unanswered |
|-----------|--------|-----|-------|-----------|
| Findability | 3.5 | 4 | 88% | 0 |
| Accessibility | 3.5 | 4 | 88% | 0 |
| Characterisation | 2.5 | 5 | 50% | 0 |
| Provenance | 2.5 | 5 | 50% | 0 |
| Ethics & Consent | 2.0 | 3 | 67% | 0 |
| Interoperability & Standards | 3.0 | 3 | 100% | 0 |
| Computability / AI-Readiness | 2.5 | 8 | 31% | 0 |

## Overall Score

**19.5 / 32 = 60.9%**

**Readiness Tier: Developing**
> Core FAIR properties present; significant AI-readiness gaps.

| Tier | Range |
|------|-------|
| AI-Ready | ≥ 90% |
| Ready | 70–89% |
| Developing | 40–69% |
| Not Ready | < 40% |

## Action Items (Criteria scoring < YES)

| ID | Label | Status | Source |
|----|-------|--------|--------|
| F-04 | Keywords from controlled vocabulary _Keywords present but as free-text strings; not yet mapped to MeSH/EDAM IRIs._ | PARTIAL | FAIR F2; Bioschemas Dataset 1.1 |
| A-02 | Authentication/authorisation documented _IRB approval noted but specific access protocol not spelled out._ | PARTIAL | FAIR A1.2 |
| C-03 | Statistical summary / quality metrics provided _No statistical summary in this metadata record. TODO: add dqv:QualityMeasurement._ | NO | FAIRSCAPE C-07; Bridge2AI D3 |
| C-04 | Known biases and limitations documented _No bias statement in current record. TODO: add dct:rights extension or dedicated bias note._ | NO | FAIRSCAPE C-10; arXiv:2508.21774 |
| C-05 | Version and provenance of reference ontologies/vocabularies _OMOP CDM referenced but no version IRI. MeSH term used without version._ | PARTIAL | FAIRSCAPE C-11; Tan et al. arXiv:2405.05413 |
| P-02 | Software versions and containers recorded _No software/container provenance in current record._ | NO | FAIRSCAPE C-12; yProv4ML arXiv:2507.01075 |
| P-03 | Input datasets and parameters logged _prov:wasDerivedFrom links upstream dataset but no parameter record._ | PARTIAL | FAIRSCAPE C-13; WRROC |
| P-05 | Execution environment reproducible _No environment specification file. TODO: add Dockerfile or conda env._ | NO | FAIRSCAPE C-15 |
| E-03 | Data use restrictions machine-readable _Use restrictions in prose only. TODO: add GA4GH DUO terms (HMB, DS)._ | NO | FAIRSCAPE C-18; GA4GH DUO |
| M-02 | Programmatic access via API or package _Zenodo has a Python API (zenodo-get) but no dedicated dataset package._ | PARTIAL | FAIRSCAPE C-22 |
| M-03 | Data loading verified (end-to-end test) _No loading notebook provided. TODO: add Jupyter notebook example._ | NO | FAIRSCAPE C-23 |
| M-04 | Training/test split methodology documented _Split strategy not documented. TODO: describe in metadata or README._ | NO | FAIRSCAPE C-24 |
| M-05 | Benchmark or baseline metrics provided _No baseline provided. TODO: cite relevant Parkinson voice ML literature._ | NO | FAIRSCAPE C-25 |
| M-06 | Dataset registered in AI-ready catalogue _Zenodo registration present; FAIRSCAPE FAIR Commons registration not done._ | PARTIAL | FAIRSCAPE C-26; Bridge2AI D7 |
| M-07 | Known failure modes for ML documented _No failure mode documentation. TODO: document known covariate shifts._ | NO | FAIRSCAPE C-27 |
| M-08 | Citation and attribution metadata machine-readable _DOI + dct:creator present; no CITATION.cff or DataCite JSON._ | PARTIAL | FAIRSCAPE C-28; Bridge2AI D1 |