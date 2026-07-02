# FAIR AI-Ready Dataset Ontology (FAR)

**Namespace:** `https://w3id.org/fair-ai-ready/`  
**Prefix:** `far:`  
**Version:** 0.1.0 (2026-07-02)  
**Licence:** CC-BY 4.0

---

## What it is

A composed OWL 2 application ontology modelling the machine-readable structural
and provenance layer that is **universally absent** in real biomedical datasets.

**Empirical basis:** 0 % of 1,738 public datasets (Dryad 340 + EMBL-EBI
BioStudies 798 + PRIDE/ProteomeXchange 600) reached Tier 3 Interoperable or
Tier 4 AI-ready in a tiered SHACL audit of all 28 FAIRSCAPE criteria + 7
Bridge2AI dimensions. Every Tier 3 / 4 signal — machine-readable schema,
provenance record, checksum, data dictionary, ethics basis, sample
characterisation — is absent in essentially every deposited dataset. See
`FINDINGS.md` for the full results.

**Design principle — compose, do not reinvent:** the ontology defines a small
set of native classes and properties that fill the gaps not addressed by DCAT,
PROV-O, schema.org, SPDX, or Croissant individually, then aligns every native
term to those vocabularies via `rdfs:subClassOf`, `skos:exactMatch`, and
`skos:closeMatch`. The validation layer is the companion SHACL shapes in
`shapes/tier-*.ttl`.

---

## Statistics

| Metric | Count |
|---|---|
| Total triples (raw) | 238 |
| Triples after OWL-RL closure | 705 |
| Native classes | 9 |
| Native object properties | 12 |
| Native data properties | 9 |
| OWL restrictions on AIReadyDataset | 5 |
| External `rdfs:subClassOf` mappings | 11 |
| `skos:exactMatch` mappings | 7 |
| `skos:closeMatch` mappings | 22 |
| `skos:relatedMatch` mappings | 2 |
| **Total alignment assertions** | **42** |

---

## Native Classes

| Class | Label | FAIRSCAPE Criteria |
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

---

## Composition / Alignment Table

Every native term is aligned to at least one external vocabulary.  
Legend: `⊆` subClassOf · `=` exactMatch · `≈` closeMatch · `~` relatedMatch

### Classes

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

### Object Properties

| FAR property | schema.org | DCAT 3 | PROV-O | SPDX 2.3 |
|---|---|---|---|---|
| `far:hasSchema` | `≈ schema:variableMeasured` | — | — | — |
| `far:hasDataDictionary` | `≈ schema:hasPart` | — | — | — |
| `far:hasProvenance` | — | — | `≈ prov:wasGeneratedBy` | — |
| `far:hasChecksum` | `≈ schema:sha256` | — | — | `= spdx:checksum` |
| `far:conformsToStandard` | `≈ schema:isBasedOn` | — | — | — |
| `far:hasEthicsBasis` | `≈ schema:conditionsOfAccess` | — | — | — |
| `far:executedBy` | — | — | `≈ prov:wasAttributedTo` | — |
| `far:usedSoftware` | `≈ schema:softwareRequirements` | — | `≈ prov:used` | — |

### Data Properties

| FAR property | schema.org | SPDX 2.3 |
|---|---|---|
| `far:checksumValue` | — | `= spdx:checksumValue` |
| `far:checksumAlgorithm` | — | `= spdx:algorithm` |
| `far:sampleCount` | `= schema:numberOfItems` | — |
| `far:variableUnit` | `= schema:unitCode` | — |
| `far:deIdentificationMethod` | `~ schema:conditionsOfAccess` | — |

---

## Relationship to the SHACL Tiers

This OWL ontology is the **semantic layer**; the SHACL shapes in `shapes/` are the **validation layer**. They are designed as complementary artefacts:

| SHACL shape file | Tier | OWL coverage |
|---|---|---|
| `shapes/tier-1-findable.ttl` | T1 — Findable | F1–F4 criteria on `far:AIReadyDataset` (via `schema:Dataset`) |
| `shapes/tier-2-accessible-reusable.ttl` | T2 — Accessible / Reusable | A1, A1.1, A1.2, R1.1, R1.2 — modelled in `far:AccessSpecification` |
| `shapes/tier-3-interoperable-schema.ttl` | T3 — Interoperable | I1–I3, C3, C6 — modelled in `far:VariableSchema`, `far:conformsToStandard` |
| `shapes/tier-4-ai-ready.ttl` | T4 — AI-Ready | C1–C13 — all T4 classes (`far:ProvenanceRecord`, `far:IntegrityCheck`, `far:DataDictionary`, `far:EthicsBasis`, `far:SampleCharacterization`) |

The OWL ontology captures class semantics, necessary conditions (via OWL
restrictions on `far:AIReadyDataset`), and vocabulary alignments.  The SHACL
shapes enforce precise property paths, value patterns, and cardinalities on
actual dataset metadata graphs — the split is intentional: OWL for
interoperability and alignment; SHACL for machine validation.

---

## Validation

Parse + statistics (structural validity):

```bash
uv run --with rdflib python -c "
from rdflib import Graph, RDF, OWL
g = Graph()
g.parse('ontology/fair-ai-ready-dataset.ttl', format='turtle')
print('Triples:', len(g))
print('Classes:', sum(1 for _ in g.subjects(RDF.type, OWL.Class)))
"
```

OWL-RL deductive closure (consistency):

```bash
uv run --with rdflib --with owlrl python -c "
import owlrl
from rdflib import Graph
g = Graph()
g.parse('ontology/fair-ai-ready-dataset.ttl', format='turtle')
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
print('Triples after closure:', len(g), '— no inconsistency')
"
```

Expected output: 238 raw triples, 705 after closure, no exceptions.

---

## External IRI Confidence Notes

All external IRIs were verified against published vocabulary specifications
before use.  Known caveats:

- **MLCommons Croissant** (`http://mlcommons.org/croissant/`): namespace and
  terms `RecordSet`, `Field`, `FileObject`, `FileSet` confirmed against the
  Croissant 1.0 specification (mlcommons.org/croissant/1.0, 2023). This is a
  relatively new vocabulary; IRIs may be revised in future Croissant versions.
- **Bioschemas Dataset 1.1** (`https://bioschemas.org/profiles/Dataset/1.1-RELEASE`):
  this is a profile page URL, not an OWL class IRI. It is used only as a
  `skos:closeMatch` concept reference, not in a `rdf:type` or `rdfs:subClassOf`
  position.
- **SPDX 2.3** (`http://spdx.org/rdf/terms#`): confirmed against the SPDX 2.3
  RDF/OWL ontology. SPDX 3.0 introduces a new namespace; the 2.3 terms remain
  stable.
- All schema.org terms use the `https://schema.org/` namespace (HTTPS), matching
  the SHACL shapes in `shapes/`.

---

## Citations

```
Al Manir S, Clark T et al. "The FAIRSCAPE AI-readiness Framework for Biomedical
Research." bioRxiv 2024.12.23.629818 (v4 March 2026; PMC11703166)
https://doi.org/10.1101/2024.12.23.629818

Caufield H et al. "Standards in the Preparation of Biomedical Research Metadata:
A Bridge2AI Perspective." arXiv:2509.10432 (September 2025)
https://arxiv.org/abs/2509.10432

Wilkinson MD et al. "The FAIR Guiding Principles for scientific data management
and stewardship." Sci Data 3:160018, 2016
https://doi.org/10.1038/sdata.2016.18

Leo S et al. "Recording provenance of workflow runs with RO-Crate (WRROC)."
PLoS One 19(9):e0309210, 2024
https://doi.org/10.1371/journal.pone.0309210

W3C DCAT 3. "Data Catalog Vocabulary." W3C Recommendation 2023-08-22
https://www.w3.org/TR/vocab-dcat-3/

W3C PROV-O. "The PROV Ontology." W3C Recommendation 2013-04-30
https://www.w3.org/TR/prov-o/

SPDX 2.3 RDF Ontology. Linux Foundation / SPDX Workgroup
http://spdx.org/rdf/terms

MLCommons Croissant 1.0. "A metadata format for ML-ready datasets."
http://mlcommons.org/croissant/1.0
```
