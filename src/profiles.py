"""
profiles.py — FAIR metadata profile normalizer.

Maps the five major metadata profiles into a common schema.org-based graph
so that the tiered SHACL shapes can validate uniformly across sources.

Profiles handled:
  1. schema.org Dataset (schema: https://schema.org/ or http://schema.org/)
  2. DataCite JSON (DataCite Schema 4.5)
  3. DCAT 3 / DC Terms (W3C Rec 2023-08-22)
  4. Bioschemas Dataset 1.1 (schema.org superset — mostly pass-through)
  5. RO-Crate 1.1 (JSON-LD with schema.org context)

Key reconciliations:
  - dct:title, dc:title → schema:name
  - dct:creator, dcterms:creator, foaf:maker, schema:author → schema:creator
  - dct:license, dct:rights, datacite:rights → schema:license
  - dct:identifier, datacite:identifier → schema:identifier
  - dct:issued, datacite:publicationYear → schema:datePublished
  - dcat:keyword → schema:keywords
  - dcat:theme, dct:subject, dc:subject → schema:about
  - dcat:distribution → schema:distribution (DataDownload)
  - dcat:downloadURL → schema:contentUrl
  - dcat:mediaType, dct:format → schema:encodingFormat
  - dcat:byteSize → schema:contentSize
  - owl:versionInfo, dcat:version → schema:version
  - dcat:landingPage, foaf:page → schema:url
  - dct:conformsTo → schema:isBasedOn
  - prov:wasDerivedFrom → schema:isBasedOn
  - foaf:name → schema:name (on agents)
  - foaf:Person → schema:Person
  - foaf:Organization → schema:Organization
  - dcat:Dataset → schema:Dataset
  - dcat:Distribution → schema:DataDownload

Usage:
    from src.profiles import normalize
    g_norm = normalize(input_graph)

Grounded in:
  Wilkinson 2016 (FAIR F1–R1.3); Caufield 2025 (Bridge2AI D1–D7);
  DataCite Schema 4.5; DCAT 3 W3C Rec; Bioschemas Dataset 1.1; RO-Crate 1.1.
"""

from __future__ import annotations

import json
from pathlib import Path

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import (
    RDF, RDFS, XSD, OWL,
    DC, DCTERMS, FOAF, PROV,
)

SCHEMA   = Namespace("https://schema.org/")
SCHEMA_H = Namespace("http://schema.org/")   # legacy http variant
DCAT     = Namespace("http://www.w3.org/ns/dcat#")
DCT      = DCTERMS  # alias
VCARD    = Namespace("http://www.w3.org/2006/vcard/ns#")
SPDX     = Namespace("http://spdx.org/rdf/terms#")


# ---------------------------------------------------------------------------
# Property alias tables
# ---------------------------------------------------------------------------

# Maps (predicate IRI) → canonical schema.org predicate.
# Applied at the dataset node level.
DATASET_PROP_MAP: dict[URIRef, URIRef] = {
    # Title
    DCT.title:             SCHEMA.name,
    DC.title:              SCHEMA.name,
    RDFS.label:            SCHEMA.name,
    # Description
    DCT.description:       SCHEMA.description,
    DC.description:        SCHEMA.description,
    # Creator/author — critical fix for the v0.1 creator/author artefact
    DCT.creator:           SCHEMA.creator,
    DC.creator:            SCHEMA.creator,
    SCHEMA_H.author:       SCHEMA.creator,
    SCHEMA_H.creator:      SCHEMA.creator,
    FOAF.maker:            SCHEMA.creator,
    # Publisher
    DCT.publisher:         SCHEMA.publisher,
    DC.publisher:          SCHEMA.publisher,
    SCHEMA_H.publisher:    SCHEMA.publisher,
    # Date
    DCT.issued:            SCHEMA.datePublished,
    DC.date:               SCHEMA.datePublished,
    SCHEMA_H.datePublished: SCHEMA.datePublished,
    DCT.modified:          SCHEMA.dateModified,
    SCHEMA_H.dateModified: SCHEMA.dateModified,
    # Identifier
    DCT.identifier:        SCHEMA.identifier,
    DC.identifier:         SCHEMA.identifier,
    SCHEMA_H.identifier:   SCHEMA.identifier,
    # License
    DCT.license:           SCHEMA.license,
    DC.rights:             SCHEMA.license,
    DCT.rights:            SCHEMA.license,
    SCHEMA_H.license:      SCHEMA.license,
    # Keywords
    DCAT.keyword:          SCHEMA.keywords,
    DC.subject:            SCHEMA.keywords,
    SCHEMA_H.keywords:     SCHEMA.keywords,
    # Subjects / controlled vocab
    DCAT.theme:            SCHEMA.about,
    DCT.subject:           SCHEMA.about,
    SCHEMA_H.about:        SCHEMA.about,
    # Distribution
    DCAT.distribution:     SCHEMA.distribution,
    SCHEMA_H.distribution: SCHEMA.distribution,
    # Landing page
    DCAT.landingPage:      SCHEMA.url,
    FOAF.page:             SCHEMA.url,
    SCHEMA_H.url:          SCHEMA.url,
    # Contact
    DCAT.contactPoint:     SCHEMA.contactPoint,
    SCHEMA_H.contactPoint: SCHEMA.contactPoint,
    # Version
    OWL.versionInfo:       SCHEMA.version,
    DCAT.version:          SCHEMA.version,
    SCHEMA_H.version:      SCHEMA.version,
    # Standards / provenance references
    DCT.conformsTo:        SCHEMA.isBasedOn,
    SCHEMA_H.isBasedOn:    SCHEMA.isBasedOn,
    # In language
    DCT.language:          SCHEMA.inLanguage,
    SCHEMA_H.inLanguage:   SCHEMA.inLanguage,
    # Measurement technique
    SCHEMA_H.measurementTechnique: SCHEMA.measurementTechnique,
    # variableMeasured
    SCHEMA_H.variableMeasured: SCHEMA.variableMeasured,
    # numberOfItems
    SCHEMA_H.numberOfItems: SCHEMA.numberOfItems,
    # softwareRequirements
    SCHEMA_H.softwareRequirements: SCHEMA.softwareRequirements,
    # additionalType
    SCHEMA_H.additionalType: SCHEMA.additionalType,
    # hasPart
    SCHEMA_H.hasPart:      SCHEMA.hasPart,
    # conditionsOfAccess
    SCHEMA_H.conditionsOfAccess: SCHEMA.conditionsOfAccess,
    # includedInDataCatalog
    SCHEMA_H.includedInDataCatalog: SCHEMA.includedInDataCatalog,
    # Provenance (prov)
    PROV.wasDerivedFrom:   SCHEMA.isBasedOn,
    PROV.wasGeneratedBy:   PROV.wasGeneratedBy,  # keep prov: for T4
}

# Distribution (dcat:Distribution / schema:DataDownload) property aliases
DISTRIBUTION_PROP_MAP: dict[URIRef, URIRef] = {
    DCAT.downloadURL:      SCHEMA.contentUrl,
    DCAT.accessURL:        SCHEMA.contentUrl,
    SCHEMA_H.contentUrl:   SCHEMA.contentUrl,
    DCAT.mediaType:        SCHEMA.encodingFormat,
    DCT.format:            SCHEMA.encodingFormat,
    SCHEMA_H.encodingFormat: SCHEMA.encodingFormat,
    DCAT.byteSize:         SCHEMA.contentSize,
    SCHEMA_H.contentSize:  SCHEMA.contentSize,
    DCT.title:             SCHEMA.name,
    SCHEMA_H.name:         SCHEMA.name,
    # checksum passthrough
    SPDX.checksum:         SPDX.checksum,
    SCHEMA_H.sha256:       SCHEMA.sha256,
}

# Agent (foaf:Person / foaf:Organization) property aliases
AGENT_PROP_MAP: dict[URIRef, URIRef] = {
    FOAF.name:          SCHEMA.name,
    VCARD.fn:           SCHEMA.name,
    SCHEMA_H.name:      SCHEMA.name,
    FOAF.mbox:          SCHEMA.email,
    SCHEMA_H.email:     SCHEMA.email,
    FOAF.homepage:      SCHEMA.url,
    SCHEMA_H.url:       SCHEMA.url,
    SCHEMA_H.identifier: SCHEMA.identifier,
    DCT.identifier:     SCHEMA.identifier,
}

# Class remap: source class → canonical class
CLASS_MAP: dict[URIRef, URIRef] = {
    DCAT.Dataset:          SCHEMA.Dataset,
    SCHEMA_H.Dataset:      SCHEMA.Dataset,
    DCAT.Distribution:     SCHEMA.DataDownload,
    SCHEMA_H.DataDownload: SCHEMA.DataDownload,
    FOAF.Person:           SCHEMA.Person,
    SCHEMA_H.Person:       SCHEMA.Person,
    FOAF.Organization:     SCHEMA.Organization,
    URIRef("http://xmlns.com/foaf/0.1/Organisation"): SCHEMA.Organization,
    SCHEMA_H.Organization: SCHEMA.Organization,
    SCHEMA_H.Person:       SCHEMA.Person,
}


# ---------------------------------------------------------------------------
# Core normalizer
# ---------------------------------------------------------------------------

def normalize(g: Graph) -> Graph:
    """
    Return a new Graph with all triples remapped to the canonical
    schema.org-based representation. The input graph is not modified.
    """
    out = Graph()

    # Bind canonical prefixes for readability
    out.bind("schema", SCHEMA)
    out.bind("prov", PROV)
    out.bind("spdx", SPDX)
    out.bind("xsd", XSD)

    for s, p, o in g:
        s_norm = _norm_node(s)
        p_norm = _norm_prop(p, s, g)
        o_norm = _norm_value(o, p, g)

        if s_norm is None or p_norm is None:
            continue

        # Apply class remapping (rdf:type triples)
        if p == RDF.type:
            if isinstance(o, URIRef):
                o_mapped = CLASS_MAP.get(o, o)
                out.add((s_norm, RDF.type, o_mapped))
            continue

        if o_norm is not None:
            out.add((s_norm, p_norm, o_norm))

    return out


def _norm_node(node: rdflib.term.Node) -> rdflib.term.Node | None:
    """Keep IRIs and BNodes; remap http://schema.org/ IRIs to https://."""
    if isinstance(node, URIRef):
        return _remap_schema_iri(node)
    if isinstance(node, BNode):
        return node
    return None  # Literals as subjects: skip (rare/invalid)


def _norm_prop(p: URIRef, s: rdflib.term.Node, g: Graph) -> URIRef | None:
    """Remap predicate through the alias tables, choosing by subject class."""
    # Determine subject type
    subject_types = set(g.objects(s, RDF.type))
    if _is_distribution(subject_types):
        mapped = DISTRIBUTION_PROP_MAP.get(p)
    elif _is_agent(subject_types):
        mapped = AGENT_PROP_MAP.get(p)
    else:
        mapped = DATASET_PROP_MAP.get(p)

    if mapped is not None:
        return mapped
    # Remap unmapped http://schema.org/ predicates to canonical https: form
    # (Dryad JSON-LD uses context "http://schema.org" which expands all properties
    #  to http:// IRIs; the alias map handles non-trivial remappings like author→creator,
    #  but simple passthroughs like schema:name, schema:description need this fallback.)
    if str(p).startswith("http://schema.org/"):
        return URIRef("https://schema.org/" + str(p)[len("http://schema.org/"):])
    # Passthrough for known schema.org (https) predicates not in the map
    if str(p).startswith("https://schema.org/"):
        return p
    # Passthrough for prov, spdx, rdf, rdfs, owl
    ns = str(p).rsplit("#", 1)[0] if "#" in str(p) else str(p).rsplit("/", 1)[0]
    passthrough_ns = {
        "http://www.w3.org/ns/prov",
        "http://spdx.org/rdf/terms",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns",
        "http://www.w3.org/2002/07/owl",
    }
    if ns in passthrough_ns:
        return p
    # Drop unmapped predicates silently
    return None


def _norm_value(o: rdflib.term.Node, p: URIRef, g: Graph) -> rdflib.term.Node | None:
    """Remap object nodes; normalise schema.org IRIs; coerce date literals."""
    if isinstance(o, URIRef):
        return _remap_schema_iri(o)
    if isinstance(o, BNode):
        return o
    if isinstance(o, Literal):
        return _coerce_literal(o, p)
    return None


def _remap_schema_iri(iri: URIRef) -> URIRef:
    """Remap http://schema.org/X → https://schema.org/X."""
    s = str(iri)
    if s.startswith("http://schema.org/"):
        return URIRef("https://schema.org/" + s[len("http://schema.org/"):])
    return iri


_DATE_PREDICATES = {
    SCHEMA.datePublished, SCHEMA.dateModified,
    URIRef("http://schema.org/datePublished"),
    URIRef("http://schema.org/dateModified"),
    DCT.issued, DCT.modified, DC.date,
}
_SCHEMA_DATE_TYPES = {
    URIRef("http://schema.org/Date"),
    URIRef("https://schema.org/Date"),
    URIRef("http://schema.org/DateTime"),
    URIRef("https://schema.org/DateTime"),
}


def _coerce_literal(lit: Literal, p: URIRef) -> Literal:
    """
    Coerce date-ish literals to XSD date types.
    Handles: xsd:gYear, xsd:date, xsd:dateTime, schema.org Date/DateTime,
    plain strings (YYYY, YYYY-MM-DD, ISO 8601 datetime).
    """
    if p not in _DATE_PREDICATES:
        return lit
    # Already correct XSD type
    if lit.datatype in (XSD.date, XSD.dateTime, XSD.gYear):
        return lit
    val = str(lit).strip()
    # schema.org Date/DateTime typed — coerce by value format
    if lit.datatype in _SCHEMA_DATE_TYPES or lit.datatype is None:
        if len(val) == 4 and val.isdigit():
            return Literal(val, datatype=XSD.gYear)
        if len(val) == 10 and val[4:5] == "-" and val[7:8] == "-":
            return Literal(val, datatype=XSD.date)
        # ISO 8601 datetime: 2023-01-17T00:00:00Z or 2023-01-17T00:00:00+00:00
        if len(val) >= 19 and val[4:5] == "-" and val[7:8] == "-" and ("T" in val or "t" in val):
            return Literal(val, datatype=XSD.dateTime)
    return lit


def _is_distribution(types: set) -> bool:
    return bool(types & {
        DCAT.Distribution,
        SCHEMA.DataDownload,
        SCHEMA_H.DataDownload,
    })


def _is_agent(types: set) -> bool:
    return bool(types & {
        FOAF.Person, FOAF.Organization, URIRef("http://xmlns.com/foaf/0.1/Organisation"),
        SCHEMA.Person, SCHEMA_H.Person,
        SCHEMA.Organization, SCHEMA_H.Organization,
        PROV.Agent,
    })


# ---------------------------------------------------------------------------
# DataCite JSON → RDF normalizer
# ---------------------------------------------------------------------------

def from_datacite_json(data: dict) -> Graph:
    """
    Convert a DataCite JSON record (Schema 4.5) to a normalized schema.org graph.

    DataCite JSON structure reference:
    https://support.datacite.org/docs/schema-optional-properties-v45

    Returns a Graph ready for SHACL validation (no further normalize() call needed).
    """
    g = Graph()
    g.bind("schema", SCHEMA)

    doi = data.get("doi", data.get("id", ""))
    if doi and not doi.startswith("http"):
        doi = f"https://doi.org/{doi}"

    dataset = URIRef(doi) if doi else BNode()
    g.add((dataset, RDF.type, SCHEMA.Dataset))

    if doi:
        g.add((dataset, SCHEMA.identifier, URIRef(doi)))
        g.add((dataset, SCHEMA.url, URIRef(doi.replace("https://doi.org/", "https://zenodo.org/doi/"))))

    attrs = data.get("attributes", data)

    # Titles
    for t in _listify(attrs.get("titles", attrs.get("title", []))):
        title = t.get("title", t) if isinstance(t, dict) else t
        g.add((dataset, SCHEMA.name, Literal(str(title), datatype=XSD.string)))

    # Descriptions
    for d in _listify(attrs.get("descriptions", attrs.get("description", []))):
        desc = d.get("description", d) if isinstance(d, dict) else d
        g.add((dataset, SCHEMA.description, Literal(str(desc), datatype=XSD.string)))

    # Creators
    for c in _listify(attrs.get("creators", [])):
        agent_node = BNode()
        name = c.get("name", c.get("familyName", ""))
        g.add((agent_node, RDF.type, SCHEMA.Person))
        g.add((agent_node, SCHEMA.name, Literal(name, datatype=XSD.string)))
        orcid = next((ni["nameIdentifier"] for ni in c.get("nameIdentifiers", [])
                      if "orcid" in ni.get("nameIdentifierScheme", "").lower()), None)
        if orcid:
            if not orcid.startswith("http"):
                orcid = f"https://orcid.org/{orcid}"
            g.add((agent_node, SCHEMA.identifier, URIRef(orcid)))
        g.add((dataset, SCHEMA.creator, agent_node))

    # License / rights
    for r in _listify(attrs.get("rightsList", attrs.get("rights", []))):
        rights_uri = r.get("rightsUri", r.get("rightsUrl", "")) if isinstance(r, dict) else ""
        if rights_uri:
            g.add((dataset, SCHEMA.license, URIRef(rights_uri)))
            break

    # Publication year
    pub_year = attrs.get("publicationYear", "")
    if pub_year:
        g.add((dataset, SCHEMA.datePublished, Literal(str(pub_year), datatype=XSD.gYear)))

    # Subjects / keywords
    for s in _listify(attrs.get("subjects", [])):
        subject = s.get("subject", s) if isinstance(s, dict) else s
        scheme_uri = s.get("schemeUri", "") if isinstance(s, dict) else ""
        val_uri = s.get("valueUri", "") if isinstance(s, dict) else ""
        if val_uri:
            g.add((dataset, SCHEMA.about, URIRef(val_uri)))
        elif scheme_uri:
            g.add((dataset, SCHEMA.about, URIRef(scheme_uri + str(subject))))
        else:
            g.add((dataset, SCHEMA.keywords, Literal(str(subject), datatype=XSD.string)))

    # Version
    ver = attrs.get("version", "")
    if ver:
        g.add((dataset, SCHEMA.version, Literal(str(ver), datatype=XSD.string)))

    # Publisher
    pub = attrs.get("publisher", "")
    if isinstance(pub, dict):
        pub = pub.get("name", "")
    if pub:
        pub_node = BNode()
        g.add((pub_node, RDF.type, SCHEMA.Organization))
        g.add((pub_node, SCHEMA.name, Literal(str(pub), datatype=XSD.string)))
        g.add((dataset, SCHEMA.publisher, pub_node))

    # Sizes / content sizes → distribution stub
    sizes = _listify(attrs.get("sizes", []))
    formats = _listify(attrs.get("formats", []))
    url = attrs.get("url", "")
    if url or sizes or formats:
        dist = BNode()
        g.add((dist, RDF.type, SCHEMA.DataDownload))
        if url:
            g.add((dist, SCHEMA.contentUrl, URIRef(url)))
        for fmt in formats:
            g.add((dist, SCHEMA.encodingFormat, Literal(str(fmt), datatype=XSD.string)))
        for sz in sizes:
            g.add((dist, SCHEMA.contentSize, Literal(str(sz), datatype=XSD.string)))
        g.add((dataset, SCHEMA.distribution, dist))

    # ResourceType → additionalType
    resource_type = attrs.get("types", {}).get("resourceTypeGeneral", "")
    if resource_type:
        rt_iri = f"https://schema.datacite.org/meta/kernel-4/resourceType#{resource_type}"
        g.add((dataset, SCHEMA.additionalType, URIRef(rt_iri)))

    return g


def _listify(val) -> list:
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


# ---------------------------------------------------------------------------
# High-level load + normalize
# ---------------------------------------------------------------------------

FORMATS = {
    ".ttl": "turtle",
    ".jsonld": "json-ld",
    ".json": "json-ld",  # assumes JSON-LD; DataCite JSON needs from_datacite_json()
    ".n3": "n3",
    ".nt": "nt",
    ".xml": "xml",
    ".rdf": "xml",
}


def load_and_normalize(path: Path) -> Graph:
    """
    Load a metadata file (RDF/JSON-LD/TTL) and return a normalized schema.org graph.
    Detects DataCite JSON by checking for 'doi' or 'attributes.creators' keys.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        # Heuristic: DataCite JSON has 'data.attributes.creators' or top-level 'doi'
        if "doi" in raw or ("data" in raw and "creators" in raw.get("data", {}).get("attributes", {})):
            inner = raw.get("data", raw)
            return from_datacite_json(inner)

    g = Graph()
    fmt = FORMATS.get(suffix, "turtle")
    g.parse(str(path), format=fmt)
    return normalize(g)
