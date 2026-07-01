# FAIR Dataset Contract — Validation Report

- **Data file**: `examples/ex06_nonconformant.ttl`
- **Shapes file**: `/Users/fabio/projects/fair-scientific-data/shapes/dataset-contract.shacl.ttl`
- **Validated at**: 2026-07-01T22:23:52Z
- **Conforms**: NO ✗
- **Violations**: 3
- **Warnings**: 2
- **Infos**: 0

## SHACL Report

```
Validation Report
Conforms: False
Results (5):
Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:description Literal("At least one distribution with a download URL. FAIR A1.") ; sh:message Literal("Dataset MUST have at least one dcat:distribution with a downloadURL. FAIR A1.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:name Literal("Distribution") ; sh:node fsd:DistributionShape ; sh:path dcat:distribution ; sh:severity sh:Violation ]
	Focus Node: <urn:example:bad-dataset>
	Result Path: dcat:distribution
	Message: Dataset MUST have at least one dcat:distribution with a downloadURL. FAIR A1.
Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:description Literal("IRI of a license (e.g., https://creativecommons.org/licenses/by/4.0/). FAIR R1.1.") ; sh:message Literal("Dataset MUST have a dct:license IRI (e.g., CC-BY 4.0). FAIR R1.1.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:name Literal("License") ; sh:nodeKind sh:IRI ; sh:path dct:license ; sh:severity sh:Violation ]
	Focus Node: <urn:example:bad-dataset>
	Result Path: dct:license
	Message: Dataset MUST have a dct:license IRI (e.g., CC-BY 4.0). FAIR R1.1.
Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:description Literal("Persistent identifier (DOI, ARK, PURL, w3id, …). Must be an IRI. FAIR F1.") ; sh:message Literal("Dataset MUST have at least one IRI-valued dct:identifier (PID / DOI).") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:name Literal("Identifier/PID") ; sh:nodeKind sh:IRI ; sh:path dct:identifier ; sh:severity sh:Violation ]
	Focus Node: <urn:example:bad-dataset>
	Result Path: dct:identifier
	Message: Dataset MUST have at least one IRI-valued dct:identifier (PID / DOI).
Validation Result in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Warning
	Source Shape: [ sh:datatype xsd:string ; sh:description Literal("Free-text keyword(s) for discoverability. FAIR F2.") ; sh:message Literal("Dataset SHOULD have at least one dcat:keyword. FAIR F2.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:name Literal("Keyword") ; sh:path dcat:keyword ; sh:severity sh:Warning ]
	Focus Node: <urn:example:bad-dataset>
	Result Path: dcat:keyword
	Message: Dataset SHOULD have at least one dcat:keyword. FAIR F2.
Validation Result in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Warning
	Source Shape: [ sh:description Literal("Agent (person or organisation) who created the dataset. FAIR R1.2.") ; sh:message Literal("Dataset SHOULD have at least one dct:creator (person or org). FAIR R1.2.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:name Literal("Creator") ; sh:path dct:creator ; sh:severity sh:Warning ]
	Focus Node: <urn:example:bad-dataset>
	Result Path: dct:creator
	Message: Dataset SHOULD have at least one dct:creator (person or org). FAIR R1.2.
```