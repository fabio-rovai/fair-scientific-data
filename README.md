# fair-scientific-data v0.1

An open toolkit for FAIR dataset contracts, SHACL validation, and AI-readiness assessment for scientific R&D datasets.

Built on real published standards: DCAT 3, schema.org/Dataset, Bioschemas, RO-Crate 1.1, PROV-O, WRROC.
Grounded in real research: FAIRSCAPE (28 AI-readiness criteria), Bridge2AI (7 metadata dimensions).

---

## What's in this toolkit

```
shapes/
  dataset-contract.shacl.ttl     SHACL shapes enforcing the FAIR dataset contract
src/
  validate.py                    CLI: validate any TTL/JSON-LD dataset against the shapes
  fetch_examples.py              Fetches/authors real public dataset metadata examples
examples/
  ex01_zenodo_ml_rocrate.ttl     Zenodo record 7828633 (Soiland-Reyes/Goble — FDO/RO-Crate)
  ex02_zenodo_wrroc.ttl          WRROC supplementary data (Leo et al. PLoS One 2024)
  ex03_ro_crate_minimal.ttl      RO-Crate spec 1.1 (DOI:10.5281/zenodo.3541888)
  ex04_bioschemas_dataset.ttl    Bioschemas Dataset Profile 1.1 (UniProt Swiss-Prot)
  ex05_bridge2ai_conformant.ttl  Fully conformant Bridge2AI voice dataset
  ex06_nonconformant.ttl         Intentionally non-conformant (regression test)
  fetch_log.json                 Exact source URLs, dates, bytes fetched
fair-ai-readiness/
  rubric.yaml                    28-criterion AI-readiness self-assessment rubric (YAML)
  score.py                       Scorer: computes tier + action items from filled rubric
  ex05_bridge2ai_assessment.yaml Worked example assessment (60.9% — Developing tier)
results/
  results.md                     Validation run summary (6 examples, all correct)
  ex01–06_*_report.md            Per-example SHACL validation reports
  ex05_ai_readiness_score.md     Worked AI-readiness score report
```

---

## Quickstart

### 1. Set up environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install rdflib pyshacl requests pyyaml
```

### 2. Validate your dataset metadata

Create a Turtle or JSON-LD file describing your dataset using DCAT 3 vocabulary, then:

```bash
python src/validate.py path/to/your-dataset.ttl
```

For a file that passes:

```bash
python src/validate.py examples/ex05_bridge2ai_conformant.ttl
# Conforms: YES ✓ | Violations: 0 | Warnings: 0
```

For a file that fails:

```bash
python src/validate.py examples/ex06_nonconformant.ttl
# Conforms: NO ✗ | Violations: 3 | Warnings: 2
# Dataset MUST have at least one IRI-valued dct:identifier (PID / DOI).
# Dataset MUST have a dct:license IRI (e.g., CC-BY 4.0). FAIR R1.1.
# Dataset MUST have at least one dcat:distribution with a downloadURL. FAIR A1.
```

Save the report to a file:

```bash
python src/validate.py my-dataset.ttl --output report.md
```

### 3. Assess AI-readiness

Copy the rubric, fill in `status: YES / PARTIAL / NO` for each of the 28 criteria, then score:

```bash
cp fair-ai-readiness/rubric.yaml fair-ai-readiness/my-dataset.yaml
# Edit my-dataset.yaml — fill in each criterion's status and notes

python fair-ai-readiness/score.py fair-ai-readiness/my-dataset.yaml
# Outputs: per-dimension scores, overall %, readiness tier, action items
```

See `fair-ai-readiness/ex05_bridge2ai_assessment.yaml` for a complete worked example.

---

## The Dataset Contract

A dataset "conforms" to the FAIR contract when it carries:

| Property | Predicate | Severity | FAIR Principle |
|----------|-----------|----------|----------------|
| Persistent identifier | `dct:identifier` (IRI) | **Violation** | F1 |
| Title | `dct:title` | **Violation** | F2 |
| Description (≥ 20 chars) | `dct:description` | **Violation** | F2 |
| License | `dct:license` (IRI) | **Violation** | R1.1 |
| Distribution with URL | `dcat:distribution` → `dcat:downloadURL` | **Violation** | A1 |
| Creator | `dct:creator` | Warning | R1.2 |
| Keywords | `dcat:keyword` | Warning | F2 |
| Version | `owl:versionInfo` | Warning | F1 sub |
| Provenance | `prov:wasDerivedFrom` or `prov:wasGeneratedBy` | Warning | R1.2 |
| Contact point | `dcat:contactPoint` | Warning | A1.2 |
| Variables measured | `schema:variableMeasured` | Warning | Bridge2AI D3 |

Shapes grounded in: DCAT 3 (W3C 2023-08-22), schema.org/Dataset, Bioschemas Dataset 1.1, RO-Crate 1.1, PROV-O (W3C 2013-04-30).

---

## AI-Readiness Criteria

The rubric operationalises:

- **FAIRSCAPE 28 AI-readiness criteria** across 5 dimensions (Findability, Accessibility, Characterisation, Provenance, Ethics, Interoperability, Computability)  
  Al Manir S et al. "The FAIRSCAPE AI-readiness Framework for Biomedical Research."  
  bioRxiv:2024.12.23.629818 v4, March 2026. PMC:11703166.  
  https://www.biorxiv.org/content/10.1101/2024.12.23.629818

- **Bridge2AI 7 metadata dimensions** (D1–D7)  
  Caufield H, Ghosh S, Kong SW et al. "Standards in the Preparation of Biomedical Research Metadata: A Bridge2AI Perspective."  
  arXiv:2509.10432, September 2025.  
  https://arxiv.org/abs/2509.10432

### Readiness Tiers

| Tier | Score | Meaning |
|------|-------|---------|
| AI-Ready | ≥ 90% | Meets the bar for biomedical AI training/evaluation |
| Ready | 70–89% | FAIR and well-documented; minor gaps |
| Developing | 40–69% | Core FAIR present; significant AI-readiness gaps |
| Not Ready | < 40% | Substantial FAIR and AI-readiness work required |

---

## Worked Example

The Bridge2AI voice dataset example (`ex05_bridge2ai_conformant.ttl`) scores **60.9% (Developing)**:

- Strong on Findability (88%), Accessibility (88%), Interoperability (100%)
- Gaps in Computability/AI-Readiness (31%): no loading notebook, no baseline, no bias docs
- Key action items: add statistical summary, document train/test split, register in FAIRSCAPE

This is realistic for a dataset that has good FAIR metadata but hasn't yet been packaged for ML workflows.

---

## How we do it

At [Tesseract Academy](https://gov.tesseract.academy) we help research and industry teams:

- Design FAIR-compliant metadata schemas for scientific datasets
- Implement SHACL validation pipelines for data governance
- Assess and improve AI-readiness against FAIRSCAPE + Bridge2AI benchmarks
- Connect FAIR data infrastructure to knowledge graphs, ELNs, and ML pipelines

**Contact:** gov.tesseract.academy — or email fabio@thetesseractacademy.com

---

## Grounding references

All references verified against published sources (2024–2026):

1. **WRROC** — Leo S, Crusoe MR, Rodríguez-Navas L, Soiland-Reyes S et al. "Recording provenance of workflow runs with RO-Crate." *PLoS One* 19(9):e0309210, 2024. DOI:10.1371/journal.pone.0309210

2. **AnIML OWL+SHACL** — Morlidge W et al. "The AnIML Ontology: Enabling Semantic Interoperability for Large-Scale Experimental Data." arXiv:2604.01728, CAiSE 2026.

3. **Novo Nordisk OBDM** — Tan SZK et al. "Digital Evolution: Novo Nordisk's Shift to Ontology-Based Data Management." *J. Biomed. Semantics* (2025). DOI:10.1186/s13326-025-00327-4. arXiv:2405.05413

4. **Haendel/Mungall KG quality** — Cortes KG, Mungall C, Haendel M et al. "Improving Biomedical Knowledge Graph Quality: A Community Approach." arXiv:2508.21774, 2025.

5. **FAIR Workflows** — Wilkinson SR, Goble C et al. "Applying the FAIR Principles to computational workflows." arXiv:2410.03490, 2025.

---

## License

MIT — see [LICENSE](LICENSE).
