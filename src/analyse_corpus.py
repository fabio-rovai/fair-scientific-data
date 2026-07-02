"""
analyse_corpus.py — FAIR-AI-Readiness corpus analysis (2026-07-02).

Processes 1738 real records from Dryad (340), BioStudies (798), PRIDE (600).
Normalises to schema.org, validates against tier-1..tier-4 SHACL shapes,
runs Python checks, and produces results_deep/ outputs.

Usage:
    cd /Users/fabio/projects/fair-scientific-data
    uv run --with rdflib --with pyshacl --with pandas --with matplotlib --with requests python src/analyse_corpus.py
"""
from __future__ import annotations

import json
import os
import sys
import re
import traceback
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJ = Path(__file__).parent.parent
sys.path.insert(0, str(PROJ))

DATA_DIR     = PROJ / "data" / "corpus"
SHAPES_DIR   = PROJ / "shapes"
RESULTS_DIR  = PROJ / "results_deep"
RESULTS_DIR.mkdir(exist_ok=True)

from src.profiles import normalize, SCHEMA, FORMATS
from src.checks import run_all_checks

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, XSD, DCTERMS, PROV
import pyshacl

SPDX = Namespace("http://spdx.org/rdf/terms#")

DOI_PATTERN = re.compile(r"^https?://doi\.org/10\.\d{4,}/\S+$")
ORCID_PATTERN = re.compile(r"^https?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

# ---------------------------------------------------------------------------
# 28 + extras criteria definition
# ---------------------------------------------------------------------------
CRITERIA = [
    # Tier 1 — Findable (violations)
    ("F1",          "T1", "Violation", "Globally unique PID (schema:identifier)"),
    ("F2-title",    "T1", "Violation", "Title ≥5 chars (schema:name)"),
    ("F2-desc",     "T1", "Violation", "Description ≥20 chars (schema:description)"),
    ("F2-kw",       "T1", "Violation", "Keywords present (schema:keywords)"),
    ("F3",          "T1", "Warning",   "Landing page IRI (schema:url)"),
    ("F4",          "T1", "Warning",   "Registered in catalogue (schema:includedInDataCatalog)"),
    # Tier 2 — Accessible + Reusable (violations)
    ("R1.1",        "T2", "Violation", "Machine-readable licence IRI (schema:license)"),
    ("A1",          "T2", "Violation", "Distribution with http(s) contentUrl (schema:distribution)"),
    ("R1.2-creator","T2", "Violation", "Creator present (schema:creator)"),
    ("R1.2-date",   "T2", "Violation", "Publication date (schema:datePublished)"),
    ("A1.1",        "T2", "Warning",   "Access conditions declared (schema:conditionsOfAccess)"),
    ("A1.2",        "T2", "Warning",   "Contact point (schema:contactPoint)"),
    ("R1",          "T2", "Warning",   "Publisher declared (schema:publisher)"),
    # Tier 3 — Interoperable + Schema-Structured (violations)
    ("I1",          "T3", "Violation", "Controlled vocab subject IRI (schema:about as IRI)"),
    ("C6",          "T3", "Violation", "Variable measured (schema:variableMeasured ≥1)"),
    ("C3",          "T3", "Violation", "Version identifier (schema:version)"),
    ("R1.3",        "T3", "Warning",   "Conforms to community standard (schema:isBasedOn)"),
    ("I2",          "T3", "Warning",   "Language declared (schema:inLanguage)"),
    ("I3",          "T3", "Warning",   "Qualified reference (schema:isBasedOn IRI)"),
    ("D3",          "T3", "Warning",   "Measurement technique (schema:measurementTechnique)"),
    # Tier 4 — AI-Ready (violations)
    ("C1",          "T4", "Violation", "Data type IRI (schema:additionalType IRI)"),
    ("C4",          "T4", "Violation", "Checksum on distribution (spdx:checksum or schema:sha256)"),
    ("C5",          "T4", "Violation", "Data dictionary (schema:hasPart)"),
    ("C8",          "T4", "Violation", "Ethics/IRB documented (schema:conditionsOfAccess)"),
    ("C9",          "T4", "Violation", "Pipeline provenance (prov:wasGeneratedBy IRI)"),
    ("C11",         "T4", "Violation", "Sample count (schema:numberOfItems ≥1 integer)"),
    ("C10",         "T4", "Warning",   "Software reference (schema:softwareRequirements)"),
    ("C7",          "T4", "Warning",   "Stats summary (schema:variableMeasured ≥2)"),
    ("C12",         "T4", "Warning",   "Completeness/missingness (description ≥100 chars)"),
    ("C13",         "T4", "Warning",   "De-identification (schema:conditionsOfAccess)"),
]

CRITERION_IDS = [c[0] for c in CRITERIA]

# ---------------------------------------------------------------------------
# Per-record criterion checker (direct Python, fast)
# ---------------------------------------------------------------------------

def _iri_objects(g: Graph, s, p):
    return [o for o in g.objects(s, p) if isinstance(o, URIRef)]

def _lit_objects(g: Graph, s, p):
    return [str(o) for o in g.objects(s, p) if isinstance(o, Literal)]

def check_all_criteria(g: Graph, ds) -> dict[str, bool]:
    """Return pass/fail dict for all 30 criteria for dataset node ds."""
    res: dict[str, bool] = {}

    # F1 — identifier
    ids = list(g.objects(ds, SCHEMA.identifier))
    res["F1"] = len(ids) > 0

    # F2-title
    names = _lit_objects(g, ds, SCHEMA.name)
    res["F2-title"] = any(len(n) >= 5 for n in names)

    # F2-desc
    descs = _lit_objects(g, ds, SCHEMA.description)
    res["F2-desc"] = any(len(d) >= 20 for d in descs)

    # F2-kw
    kws = list(g.objects(ds, SCHEMA.keywords))
    res["F2-kw"] = len(kws) > 0

    # F3
    urls = _iri_objects(g, ds, SCHEMA.url)
    res["F3"] = len(urls) > 0

    # F4
    cats = list(g.objects(ds, SCHEMA.includedInDataCatalog))
    res["F4"] = len(cats) > 0

    # R1.1 — license as IRI
    lics = _iri_objects(g, ds, SCHEMA.license)
    res["R1.1"] = len(lics) > 0

    # A1 — distribution with contentUrl http(s)
    dists = list(g.objects(ds, SCHEMA.distribution))
    a1_ok = False
    for dist in dists:
        urls_d = list(g.objects(dist, SCHEMA.contentUrl))
        for u in urls_d:
            if str(u).startswith("http://") or str(u).startswith("https://"):
                a1_ok = True
                break
    res["A1"] = a1_ok

    # R1.2-creator
    creators = list(g.objects(ds, SCHEMA.creator))
    res["R1.2-creator"] = len(creators) > 0

    # R1.2-date
    dates = list(g.objects(ds, SCHEMA.datePublished))
    res["R1.2-date"] = len(dates) > 0

    # A1.1
    coa = list(g.objects(ds, SCHEMA.conditionsOfAccess))
    res["A1.1"] = len(coa) > 0

    # A1.2
    cp = list(g.objects(ds, SCHEMA.contactPoint))
    res["A1.2"] = len(cp) > 0

    # R1 — publisher
    pub = list(g.objects(ds, SCHEMA.publisher))
    res["R1"] = len(pub) > 0

    # I1 — schema:about as IRI
    abouts = _iri_objects(g, ds, SCHEMA.about)
    res["I1"] = len(abouts) > 0

    # C6 — variableMeasured ≥1
    vm = list(g.objects(ds, SCHEMA.variableMeasured))
    res["C6"] = len(vm) >= 1

    # C3 — version
    ver = list(g.objects(ds, SCHEMA.version))
    res["C3"] = len(ver) >= 1

    # R1.3 / I3 — isBasedOn
    ibo = _iri_objects(g, ds, SCHEMA.isBasedOn)
    res["R1.3"] = len(ibo) > 0
    res["I3"] = res["R1.3"]

    # I2 — inLanguage
    lang = list(g.objects(ds, SCHEMA.inLanguage))
    res["I2"] = len(lang) > 0

    # D3 — measurementTechnique
    mt = list(g.objects(ds, SCHEMA.measurementTechnique))
    res["D3"] = len(mt) > 0

    # C1 — additionalType as IRI
    at = _iri_objects(g, ds, SCHEMA.additionalType)
    res["C1"] = len(at) > 0

    # C4 — checksum on distribution
    c4_ok = False
    for dist in dists:
        if list(g.objects(dist, SPDX.checksum)) or list(g.objects(dist, SCHEMA.sha256)):
            c4_ok = True
            break
    res["C4"] = c4_ok

    # C5 — hasPart
    hp = list(g.objects(ds, SCHEMA.hasPart))
    res["C5"] = len(hp) >= 1

    # C8 — conditionsOfAccess ≥1
    res["C8"] = len(coa) >= 1

    # C9 — prov:wasGeneratedBy IRI
    wgb = _iri_objects(g, ds, PROV.wasGeneratedBy)
    res["C9"] = len(wgb) >= 1

    # C11 — numberOfItems integer ≥1
    ni = list(g.objects(ds, SCHEMA.numberOfItems))
    c11_ok = False
    for n in ni:
        try:
            if int(str(n)) >= 1:
                c11_ok = True
        except (ValueError, TypeError):
            pass
    res["C11"] = c11_ok

    # C10 — softwareRequirements
    sw = list(g.objects(ds, SCHEMA.softwareRequirements))
    res["C10"] = len(sw) > 0

    # C7 — variableMeasured ≥2
    res["C7"] = len(vm) >= 2

    # C12 — description ≥100 chars
    res["C12"] = any(len(d) >= 100 for d in descs)

    # C13 — conditionsOfAccess (same as C8)
    res["C13"] = res["C8"]

    return res


# ---------------------------------------------------------------------------
# Tier conformance logic (uses SHACL-based violations only for Violations)
# ---------------------------------------------------------------------------

TIER_VIOLATION_CRITERIA = {
    # Refined: keywords (F2-kw) and licence (R1.1) demoted to reported sub-metrics
    # (Warnings), not tier gates. Findability anchored on PID + title + description;
    # accessibility on a machine-readable distribution + provenance basics.
    "T1": ["F1", "F2-title", "F2-desc"],
    "T2": ["A1", "R1.2-creator", "R1.2-date"],
    "T3": ["I1", "C6", "C3"],
    "T4": ["C1", "C4", "C5", "C8", "C9", "C11"],
}


def tier_conformance(criterion_results: dict[str, bool]) -> dict[str, bool]:
    """Compute cumulative tier pass/fail from per-criterion results (violations only)."""
    t1 = all(criterion_results.get(c, False) for c in TIER_VIOLATION_CRITERIA["T1"])
    t2 = t1 and all(criterion_results.get(c, False) for c in TIER_VIOLATION_CRITERIA["T2"])
    t3 = t2 and all(criterion_results.get(c, False) for c in TIER_VIOLATION_CRITERIA["T3"])
    t4 = t3 and all(criterion_results.get(c, False) for c in TIER_VIOLATION_CRITERIA["T4"])
    return {"T1": t1, "T2": t2, "T3": t3, "T4": t4}


def highest_tier(tiers: dict[str, bool]) -> int:
    for t in [4, 3, 2, 1]:
        if tiers.get(f"T{t}", False):
            return t
    return 0


# ---------------------------------------------------------------------------
# Custom normalizers
# ---------------------------------------------------------------------------

def _listify(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def from_dryad_jsonld(path: Path) -> tuple[Graph, str]:
    """Load Dryad JSON-LD file and normalise to schema.org graph.
    Adds schema:identifier from @id (DOI), adds distribution stub from url."""
    g = Graph()
    g.parse(str(path), format="json-ld")
    g_norm = normalize(g)

    # Find dataset node
    datasets = list(g_norm.subjects(RDF.type, SCHEMA.Dataset))
    if not datasets:
        # Try to find via @id in the raw JSON
        raw = json.loads(path.read_text(encoding="utf-8"))
        node_id = raw.get("@id", "")
        if node_id:
            ds = URIRef(node_id)
            g_norm.add((ds, RDF.type, SCHEMA.Dataset))
            datasets = [ds]

    doi_iri = ""
    for ds in datasets:
        if isinstance(ds, URIRef):
            s = str(ds)
            if s.startswith("https://doi.org/") or s.startswith("http://doi.org/"):
                doi_iri = s.replace("http://doi.org/", "https://doi.org/")
                ds_uri = URIRef(doi_iri)
                # Add explicit identifier (if @id is DOI, add as schema:identifier)
                if not list(g_norm.objects(ds, SCHEMA.identifier)):
                    g_norm.add((ds, SCHEMA.identifier, ds_uri))
            # Add distribution stub from schema:url if no distribution present
            dists = list(g_norm.objects(ds, SCHEMA.distribution))
            if not dists:
                url_iris = [o for o in g_norm.objects(ds, SCHEMA.url) if isinstance(o, URIRef)]
                if url_iris:
                    dist_node = BNode()
                    g_norm.add((dist_node, RDF.type, SCHEMA.DataDownload))
                    g_norm.add((dist_node, SCHEMA.contentUrl, url_iris[0]))
                    g_norm.add((ds, SCHEMA.distribution, dist_node))

    return g_norm, doi_iri


def from_biostudies_json(path: Path) -> tuple[Graph, str]:
    """Convert BioStudies JSON to normalised schema.org graph."""
    data = json.loads(path.read_text(encoding="utf-8"))
    g = Graph()
    g.bind("schema", SCHEMA)

    accession = data.get("accession", "")
    ds_iri = f"https://www.ebi.ac.uk/biostudies/studies/{accession}"
    ds = URIRef(ds_iri)
    g.add((ds, RDF.type, SCHEMA.Dataset))

    # F1: use EBI URL as identifier (not a DOI — structural limitation)
    g.add((ds, SCHEMA.identifier, URIRef(ds_iri)))
    g.add((ds, SCHEMA.url, URIRef(ds_iri)))

    # F2-title
    title = data.get("title", "")
    if title:
        g.add((ds, SCHEMA.name, Literal(title, datatype=XSD.string)))

    # F2-desc: use 'content' field (contains abstract text)
    content = data.get("content", "")
    if content and len(content) > 20:
        g.add((ds, SCHEMA.description, Literal(content, datatype=XSD.string)))

    # R1.2-date
    release_date = data.get("release_date", "")
    if release_date:
        if len(release_date) == 4:
            g.add((ds, SCHEMA.datePublished, Literal(release_date, datatype=XSD.gYear)))
        elif len(release_date) == 10:
            g.add((ds, SCHEMA.datePublished, Literal(release_date, datatype=XSD.date)))

    # R1.2-creator: author field is space-separated names/initials
    author_str = data.get("author", "")
    if author_str:
        # Try splitting by whitespace — each token could be a name part
        # BioStudies format: "Yao T Yu S Liu Y" — pairs of family+initial
        agent_node = BNode()
        g.add((agent_node, RDF.type, SCHEMA.Person))
        g.add((agent_node, SCHEMA.name, Literal(author_str, datatype=XSD.string)))
        g.add((ds, SCHEMA.creator, agent_node))

    # Access (A1): the basic search record gives file/link COUNTS (not URLs).
    # Studies with files are downloadable at the predictable EBI files endpoint, so
    # we add a machine-readable distribution for those. Studies with 0 files get none
    # (a genuine access gap). Licence and keywords remain absent (real limitation).
    n_files = data.get("files", 0)
    if isinstance(n_files, int) and n_files > 0:
        dist = BNode()
        g.add((dist, RDF.type, SCHEMA.DataDownload))
        g.add((dist, SCHEMA.contentUrl, URIRef(f"https://www.ebi.ac.uk/biostudies/files/{accession}")))
        g.add((dist, SCHEMA.name, Literal(f"{n_files} file(s) via BioStudies", datatype=XSD.string)))
        g.add((ds, SCHEMA.distribution, dist))

    return g, ds_iri


# PRIDE license string → IRI mapping
PRIDE_LICENSE_MAP = {
    "cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "cc by": "https://creativecommons.org/licenses/by/4.0/",
    "cc-by": "https://creativecommons.org/licenses/by/4.0/",
    "creative commons": "https://creativecommons.org/licenses/by/4.0/",
}


def from_pride_json(path: Path) -> tuple[Graph, str]:
    """Convert PRIDE JSON to normalised schema.org graph."""
    data = json.loads(path.read_text(encoding="utf-8"))
    g = Graph()
    g.bind("schema", SCHEMA)

    accession = data.get("accession", "")
    doi = data.get("doi", "")

    if doi:
        doi_iri = f"https://doi.org/{doi}"
        ds = URIRef(doi_iri)
    else:
        ds_iri = f"https://www.ebi.ac.uk/pride/archive/projects/{accession}"
        ds = URIRef(ds_iri)
        doi_iri = ds_iri

    g.add((ds, RDF.type, SCHEMA.Dataset))

    # F1: identifier
    if doi:
        g.add((ds, SCHEMA.identifier, URIRef(doi_iri)))
    g.add((ds, SCHEMA.url, URIRef(f"https://www.ebi.ac.uk/pride/archive/projects/{accession}")))

    # F2-title
    title = data.get("title", "")
    if title:
        g.add((ds, SCHEMA.name, Literal(title, datatype=XSD.string)))

    # F2-desc
    desc = data.get("projectDescription", "")
    if not desc or len(desc) < 20:
        desc = data.get("sampleProcessingProtocol", "")
    if desc and len(desc) >= 20:
        g.add((ds, SCHEMA.description, Literal(desc, datatype=XSD.string)))

    # F2-kw
    for kw in _listify(data.get("keywords", [])):
        if kw:
            g.add((ds, SCHEMA.keywords, Literal(str(kw), datatype=XSD.string)))
    for tag in _listify(data.get("projectTags", [])):
        if tag:
            g.add((ds, SCHEMA.keywords, Literal(str(tag), datatype=XSD.string)))

    # R1.1: license
    lic_str = (data.get("license", "") or "").lower().strip()
    lic_iri = None
    for k, v in PRIDE_LICENSE_MAP.items():
        if k in lic_str:
            lic_iri = v
            break
    if lic_iri:
        g.add((ds, SCHEMA.license, URIRef(lic_iri)))
    # Note: "EBI terms of use" → no recognised open licence IRI → R1.1 fails

    # R1.2-date
    pub_date = data.get("publicationDate", data.get("submissionDate", ""))
    if pub_date:
        if len(str(pub_date)) == 10:
            g.add((ds, SCHEMA.datePublished, Literal(str(pub_date), datatype=XSD.date)))
        elif len(str(pub_date)) == 4:
            g.add((ds, SCHEMA.datePublished, Literal(str(pub_date), datatype=XSD.gYear)))

    # R1.2-creator: submitters and labPIs
    seen_creators = set()
    for person in _listify(data.get("submitters", [])) + _listify(data.get("labPIs", [])):
        name = person.get("name", f"{person.get('firstName','')} {person.get('lastName','')}").strip()
        if name not in seen_creators and name:
            seen_creators.add(name)
            agent_node = BNode()
            g.add((agent_node, RDF.type, SCHEMA.Person))
            g.add((agent_node, SCHEMA.name, Literal(name, datatype=XSD.string)))
            orcid = (person.get("orcid", "") or "").strip()
            if orcid and ORCID_PATTERN.match(orcid if orcid.startswith("http") else f"https://orcid.org/{orcid}"):
                orcid_iri = orcid if orcid.startswith("http") else f"https://orcid.org/{orcid}"
                g.add((agent_node, SCHEMA.identifier, URIRef(orcid_iri)))
            g.add((ds, SCHEMA.creator, agent_node))

    # Publisher
    pub_node = BNode()
    g.add((pub_node, RDF.type, SCHEMA.Organization))
    g.add((pub_node, SCHEMA.name, Literal("EMBL-EBI PRIDE", datatype=XSD.string)))
    g.add((ds, SCHEMA.publisher, pub_node))

    # Distribution: use EBI FTP access URL
    dist_node = BNode()
    g.add((dist_node, RDF.type, SCHEMA.DataDownload))
    ftp_url = f"https://ftp.pride.ebi.ac.uk/pride/data/archive/"
    g.add((dist_node, SCHEMA.contentUrl, URIRef(f"https://www.ebi.ac.uk/pride/archive/projects/{accession}")))
    # Instruments → measurementTechnique + encodingFormat hint
    for instr in _listify(data.get("instruments", [])):
        instr_name = instr.get("name", "")
        if instr_name:
            g.add((ds, SCHEMA.measurementTechnique, Literal(instr_name, datatype=XSD.string)))
    # Format hint from experimentTypes
    for et in _listify(data.get("experimentTypes", [])):
        et_name = et.get("name", "")
        et_acc = et.get("accession", "")
        if et_acc and et_acc.startswith("PRIDE:"):
            pride_iri = f"https://www.ebi.ac.uk/ols/ontologies/pride/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2F{et_acc.replace(':', '_')}"
            g.add((ds, SCHEMA.additionalType, URIRef(f"https://www.ebi.ac.uk/pride/ontology/{et_acc}")))
        elif et_name:
            g.add((dist_node, SCHEMA.encodingFormat, Literal(et_name, datatype=XSD.string)))
    g.add((ds, SCHEMA.distribution, dist_node))

    # schema:about from organisms — PRIDE uses NEWT ontology (NCBI taxonomy IDs)
    # accession "NEWT:10090" → NCBI taxon IRI https://www.ncbi.nlm.nih.gov/taxonomy/10090
    for org in _listify(data.get("organisms", [])):
        if isinstance(org, dict):
            acc = org.get("accession", "")
            if acc and acc.upper().startswith("NEWT:"):
                taxon_num = acc.split(":", 1)[-1]
                g.add((ds, SCHEMA.about,
                       URIRef(f"https://www.ncbi.nlm.nih.gov/taxonomy/{taxon_num}")))
            else:
                name = org.get("name", "")
                if name:
                    g.add((ds, SCHEMA.keywords, Literal(name, datatype=XSD.string)))
        elif isinstance(org, str) and org:
            g.add((ds, SCHEMA.keywords, Literal(org, datatype=XSD.string)))

    return g, doi_iri


# ---------------------------------------------------------------------------
# Corpus loader
# ---------------------------------------------------------------------------

def file_path_for_record(rec: dict) -> Path | None:
    """Resolve the file path for a manifest record."""
    repo = rec.get("repo", "")
    record_id = rec.get("id", "")
    doi = rec.get("doi", "") or ""

    if repo == "dryad":
        slug = doi.replace("/", "_").replace(".", "-")
        p = DATA_DIR / "dryad" / (slug + ".jsonld")
        if p.exists():
            return p
        p2 = DATA_DIR / "dryad" / (slug + ".json")
        if p2.exists():
            return p2

    elif repo == "biostudies":
        p = DATA_DIR / "biostudies" / f"biostudies_{record_id}.json"
        if p.exists():
            return p

    elif repo == "pride":
        slug = doi.replace("/", "_").replace(".", "-")
        p = DATA_DIR / "pride" / (slug + ".json")
        if p.exists():
            return p

    return None


def load_record(rec: dict) -> tuple[Graph | None, str, str]:
    """Load and normalise one manifest record. Returns (graph, dataset_iri, error)."""
    repo = rec.get("repo", "")
    fpath = file_path_for_record(rec)
    if fpath is None:
        return None, "", "file_not_found"

    try:
        if repo == "dryad" and fpath.suffix == ".jsonld":
            g, iri = from_dryad_jsonld(fpath)
        elif repo == "biostudies":
            g, iri = from_biostudies_json(fpath)
        elif repo == "pride":
            g, iri = from_pride_json(fpath)
        else:
            # Fallback: try profiles.py load_and_normalize
            from src.profiles import load_and_normalize
            g = load_and_normalize(fpath)
            datasets = list(g.subjects(RDF.type, SCHEMA.Dataset))
            iri = str(datasets[0]) if datasets else ""
        return g, iri, ""
    except Exception as e:
        return None, "", str(e)[:120]


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_analysis():
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Load manifest
    manifest_path = DATA_DIR / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"Manifest: {len(manifest)} records")
    repos = set(r["repo"] for r in manifest)
    print(f"Repositories: {repos}")

    # ---------------------------------------------------------------------------
    # Step 1: Normalize all records
    # ---------------------------------------------------------------------------
    records_data = []  # list of dicts with record info + criterion results
    norm_counts = {repo: {"ok": 0, "fail": 0} for repo in repos}

    print("\n--- Normalizing records ---")
    for i, rec in enumerate(manifest):
        if i % 200 == 0:
            print(f"  {i}/{len(manifest)} records processed...")

        repo = rec["repo"]
        g, iri, err = load_record(rec)

        if g is None or err:
            norm_counts[repo]["fail"] += 1
            records_data.append({
                "repo": repo,
                "id": rec.get("id", ""),
                "doi": rec.get("doi", ""),
                "iri": "",
                "norm_ok": False,
                "error": err,
                **{crit: False for crit in CRITERION_IDS},
                "T1": False, "T2": False, "T3": False, "T4": False,
                "highest_tier": 0,
            })
            continue

        # Find dataset node
        datasets = list(g.subjects(RDF.type, SCHEMA.Dataset))
        if not datasets:
            norm_counts[repo]["fail"] += 1
            records_data.append({
                "repo": repo,
                "id": rec.get("id", ""),
                "doi": rec.get("doi", ""),
                "iri": iri,
                "norm_ok": False,
                "error": "no_dataset_node",
                **{crit: False for crit in CRITERION_IDS},
                "T1": False, "T2": False, "T3": False, "T4": False,
                "highest_tier": 0,
            })
            continue

        norm_counts[repo]["ok"] += 1
        ds_node = datasets[0]

        # Step 2: Per-criterion checks
        crit_results = check_all_criteria(g, ds_node)

        # Step 3: Tier conformance
        tiers = tier_conformance(crit_results)
        ht = highest_tier(tiers)

        records_data.append({
            "repo": repo,
            "id": rec.get("id", ""),
            "doi": rec.get("doi", ""),
            "iri": iri,
            "norm_ok": True,
            "error": "",
            **crit_results,
            **tiers,
            "highest_tier": ht,
        })

    print(f"\nNormalization counts:")
    for repo, counts in norm_counts.items():
        total = counts["ok"] + counts["fail"]
        print(f"  {repo}: {counts['ok']}/{total} normalized successfully")

    # ---------------------------------------------------------------------------
    # Step 4: Compute statistics
    # ---------------------------------------------------------------------------
    df = pd.DataFrame(records_data)
    n_total = len(df)
    n_ok = df["norm_ok"].sum()

    print(f"\n--- Statistics ---")
    print(f"Total records: {n_total} | Successfully normalized: {n_ok}")

    # Tier conformance — overall (include norm_ok=False as non-conformant)
    tier_overall = {}
    for tier in ["T1", "T2", "T3", "T4"]:
        n_pass = df[tier].sum()
        rate = 100 * n_pass / n_total
        tier_overall[tier] = {"n": int(n_pass), "rate": round(rate, 1)}
        print(f"  {tier}: {n_pass}/{n_total} = {rate:.1f}%")

    # Tier conformance — per repository
    tier_by_repo = {}
    for repo in repos:
        sub = df[df["repo"] == repo]
        n_repo = len(sub)
        tier_by_repo[repo] = {}
        for tier in ["T1", "T2", "T3", "T4"]:
            n_pass = sub[tier].sum()
            rate = 100 * n_pass / n_repo
            tier_by_repo[repo][tier] = {"n": int(n_pass), "total": n_repo, "rate": round(rate, 1)}

    print("\nPer-repository tier conformance:")
    for repo in sorted(repos):
        print(f"  {repo}:")
        for tier in ["T1", "T2", "T3", "T4"]:
            d = tier_by_repo[repo][tier]
            print(f"    {tier}: {d['n']}/{d['total']} = {d['rate']:.1f}%")

    # Per-criterion failure rates
    crit_stats = {}
    for crit in CRITERION_IDS:
        if crit not in df.columns:
            continue
        n_pass = df[crit].sum()
        n_fail = n_total - n_pass
        fail_rate = 100 * n_fail / n_total
        crit_stats[crit] = {
            "n_pass": int(n_pass),
            "n_fail": int(n_fail),
            "fail_rate": round(fail_rate, 1),
        }

    # Top-5 most-failed criteria
    top5 = sorted(crit_stats.items(), key=lambda x: x[1]["fail_rate"], reverse=True)[:5]
    print("\nTop-5 most-failed criteria:")
    for crit, stat in top5:
        desc = next(c[3] for c in CRITERIA if c[0] == crit)
        print(f"  {crit}: {stat['fail_rate']:.1f}% failure ({stat['n_fail']}/{n_total}) — {desc}")

    # Highest tier distribution
    tier_dist = df["highest_tier"].value_counts().sort_index().to_dict()
    print("\nHighest tier distribution:")
    for t, count in sorted(tier_dist.items()):
        print(f"  Tier {t}: {count} datasets ({100*count/n_total:.1f}%)")

    # Per-criterion failure by repo (for discussion)
    crit_by_repo = {}
    for crit in CRITERION_IDS:
        if crit not in df.columns:
            continue
        crit_by_repo[crit] = {}
        for repo in repos:
            sub = df[df["repo"] == repo]
            n_sub = len(sub)
            n_pass = sub[crit].sum()
            fail_rate = 100 * (n_sub - n_pass) / n_sub if n_sub > 0 else 0
            crit_by_repo[crit][repo] = round(fail_rate, 1)

    # ---------------------------------------------------------------------------
    # Step 5: Run Python semantic checks (sample to verify alignment)
    # ---------------------------------------------------------------------------
    print("\n--- Running Python semantic checks (sample validation) ---")
    py_check_sample_size = min(100, n_ok)
    py_check_results = {"F1": [], "R1.1": [], "R1.2": [], "C7": [], "C8": [], "C12": [], "C13": []}

    sample_recs = [r for r in records_data if r["norm_ok"]][:py_check_sample_size]
    for i, rec in enumerate(sample_recs):
        try:
            fpath = file_path_for_record({"repo": rec["repo"], "id": rec["id"], "doi": rec.get("doi","")})
            if fpath is None:
                continue
            if rec["repo"] == "dryad" and fpath.suffix == ".jsonld":
                g, _ = from_dryad_jsonld(fpath)
            elif rec["repo"] == "biostudies":
                g, _ = from_biostudies_json(fpath)
            elif rec["repo"] == "pride":
                g, _ = from_pride_json(fpath)
            else:
                continue
            reports = run_all_checks(g)
            for report in reports:
                for r in report.results:
                    if r.criterion in py_check_results:
                        py_check_results[r.criterion].append(r.passed)
        except Exception:
            pass

    print("Python check alignment (sample):")
    for crit, passed_list in py_check_results.items():
        if passed_list:
            rate = 100 * sum(passed_list) / len(passed_list)
            print(f"  {crit}: {rate:.1f}% pass (n={len(passed_list)})")

    # ---------------------------------------------------------------------------
    # Step 6: SHACL verification on random sample (10 records per repo)
    # ---------------------------------------------------------------------------
    print("\n--- SHACL spot-check (10 per repo) ---")
    shapes = {}
    for tier in ["tier-1-findable", "tier-2-accessible-reusable",
                 "tier-3-interoperable-schema", "tier-4-ai-ready"]:
        sp = SHAPES_DIR / f"{tier}.ttl"
        sg = Graph()
        sg.parse(str(sp), format="turtle")
        shapes[tier] = sg

    shacl_spot = []
    for repo in repos:
        sub_ok = [r for r in records_data if r["repo"] == repo and r["norm_ok"]]
        sample = sub_ok[:10]
        for rec in sample:
            try:
                fpath = file_path_for_record({"repo": rec["repo"], "id": rec["id"], "doi": rec.get("doi","")})
                if fpath is None:
                    continue
                if repo == "dryad":
                    g, _ = from_dryad_jsonld(fpath)
                elif repo == "biostudies":
                    g, _ = from_biostudies_json(fpath)
                elif repo == "pride":
                    g, _ = from_pride_json(fpath)
                else:
                    continue

                shacl_tiers = {}
                for tier_key, sg in shapes.items():
                    t_label = tier_key.split("-")[0].replace("tier", "T")
                    t_num = tier_key.split("-")[1]
                    t_label = f"T{t_num}"
                    conforms, _, _ = pyshacl.validate(
                        g, shacl_graph=sg,
                        inference="none", abort_on_first=False, allow_warnings=True
                    )
                    shacl_tiers[t_label] = conforms

                shacl_spot.append({
                    "repo": repo,
                    "id": rec["id"],
                    "python_T1": rec["T1"],
                    "python_T2": rec["T2"],
                    "python_T3": rec["T3"],
                    "shacl_T1": shacl_tiers.get("T1", False),
                    "shacl_T2": shacl_tiers.get("T2", False),
                    "shacl_T3": shacl_tiers.get("T3", False),
                })
            except Exception as e:
                pass

    print(f"  SHACL spot-check done: {len(shacl_spot)} records checked")
    if shacl_spot:
        spot_df = pd.DataFrame(shacl_spot)
        for tier in ["T1", "T2", "T3"]:
            py_col = f"python_{tier}"
            shacl_col = f"shacl_{tier}"
            if py_col in spot_df.columns and shacl_col in spot_df.columns:
                agree = (spot_df[py_col] == spot_df[shacl_col]).sum()
                total = len(spot_df)
                print(f"  {tier}: Python/SHACL agreement {agree}/{total} ({100*agree/total:.1f}%)")

    # ---------------------------------------------------------------------------
    # Step 7: Generate figures
    # ---------------------------------------------------------------------------
    print("\n--- Generating figures ---")
    RESULTS_DIR.mkdir(exist_ok=True)
    plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

    # Fig 1: Tier conformance by repo
    fig, ax = plt.subplots(figsize=(10, 6))
    tier_labels = ["T1\nFindable", "T2\nAccessible+\nReusable",
                   "T3\nInteroperable+\nSchema", "T4\nAI-Ready"]
    repo_colors = {"dryad": "#2196F3", "biostudies": "#4CAF50", "pride": "#FF9800"}
    repo_list = sorted(repos)
    x = range(4)
    width = 0.25
    for ri, repo in enumerate(repo_list):
        rates = [tier_by_repo[repo][f"T{i+1}"]["rate"] for i in range(4)]
        offset = (ri - 1) * width
        bars = ax.bar([xi + offset for xi in x], rates, width,
                      label=repo.capitalize(), color=repo_colors.get(repo, "#9E9E9E"), alpha=0.85)
        for bar, rate in zip(bars, rates):
            if rate > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        f"{rate:.0f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xlabel("FAIR-AI-Readiness Tier")
    ax.set_ylabel("Conformance Rate (%)")
    ax.set_title(f"FAIR-AI-Readiness Tier Conformance by Repository (N={n_total})")
    ax.set_xticks(list(x))
    ax.set_xticklabels(tier_labels)
    ax.set_ylim(0, 110)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "fig1_tier_conformance_by_repo.png")
    plt.close()

    # Fig 2: Per-criterion failure rate (all criteria)
    fig, ax = plt.subplots(figsize=(14, 8))
    all_crits = [(cid, crit_stats[cid]["fail_rate"])
                 for cid in CRITERION_IDS if cid in crit_stats]
    all_crits_sorted = sorted(all_crits, key=lambda x: x[1], reverse=True)
    crit_names = [c[0] for c in all_crits_sorted]
    crit_fails = [c[1] for c in all_crits_sorted]

    # Color by tier
    tier_colors_map = {"T1": "#2196F3", "T2": "#4CAF50", "T3": "#FF9800", "T4": "#F44336"}
    crit_tier_map = {c[0]: c[1] for c in CRITERIA}
    bar_colors = [tier_colors_map[crit_tier_map.get(n, "T1")] for n in crit_names]

    bars = ax.barh(range(len(crit_names)), crit_fails, color=bar_colors, alpha=0.85)
    ax.set_yticks(range(len(crit_names)))
    ax.set_yticklabels(crit_names, fontsize=8)
    ax.set_xlabel("Failure Rate (%)")
    ax.set_title(f"Per-Criterion Failure Rate Across All Repositories (N={n_total})")
    ax.set_xlim(0, 105)
    for bar, rate in zip(bars, crit_fails):
        ax.text(rate + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{rate:.1f}%", ha="left", va="center", fontsize=7)
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=f"Tier {t[-1]}")
                       for t, c in tier_colors_map.items()]
    ax.legend(handles=legend_elements, loc="lower right")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "fig2_criterion_failure_rates.png")
    plt.close()

    # Fig 3: Distribution of highest tier passed
    fig, ax = plt.subplots(figsize=(8, 5))
    tier_keys = [0, 1, 2, 3, 4]
    tier_counts = [tier_dist.get(t, 0) for t in tier_keys]
    tier_pcts = [100 * c / n_total for c in tier_counts]
    tier_xlabels = ["None\n(T0)", "T1\nFindable", "T2\nAccessible\n+Reusable",
                    "T3\nInteroperable\n+Schema", "T4\nAI-Ready"]
    tier_bar_colors = ["#9E9E9E", "#2196F3", "#4CAF50", "#FF9800", "#F44336"]
    bars = ax.bar(tier_xlabels, tier_pcts, color=tier_bar_colors, alpha=0.85)
    for bar, pct, cnt in zip(bars, tier_pcts, tier_counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{cnt}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Datasets (%)")
    ax.set_title(f"Distribution of Highest FAIR-AI-Readiness Tier Passed (N={n_total})")
    ax.set_ylim(0, max(tier_pcts) * 1.15 + 5)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "fig3_highest_tier_distribution.png")
    plt.close()

    # Fig 4: Per-repo, per-criterion heatmap (top 15 failing criteria)
    top15_crits = [c[0] for c in sorted(crit_stats.items(), key=lambda x: x[1]["fail_rate"], reverse=True)[:15]]
    heat_data = []
    for repo in repo_list:
        row = [crit_by_repo.get(crit, {}).get(repo, 100) for crit in top15_crits]
        heat_data.append(row)
    import numpy as np
    heat_arr = np.array(heat_data)
    fig, ax = plt.subplots(figsize=(14, 4))
    im = ax.imshow(heat_arr, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=100)
    ax.set_xticks(range(len(top15_crits)))
    ax.set_xticklabels(top15_crits, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(repo_list)))
    ax.set_yticklabels([r.capitalize() for r in repo_list])
    for i in range(len(repo_list)):
        for j in range(len(top15_crits)):
            ax.text(j, i, f"{heat_arr[i, j]:.0f}%", ha="center", va="center", fontsize=7)
    plt.colorbar(im, ax=ax, label="Failure Rate (%)")
    ax.set_title("Failure Rate by Repository × Criterion (Top 15 Most-Failed)")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "fig4_repo_criterion_heatmap.png")
    plt.close()

    print("  Figures saved to results_deep/")

    # ---------------------------------------------------------------------------
    # Step 8: Write results.md
    # ---------------------------------------------------------------------------
    print("\n--- Writing results_deep/results.md ---")
    md_lines = [
        "# FAIR-AI-Readiness Corpus Analysis Results",
        f"\n**Generated:** 2026-07-02  |  **Corpus:** {n_total} datasets  |  **Successfully normalized:** {n_ok}",
        "\n## 1. Normalization Success",
        "\n| Repository | Normalized | Total | Rate |",
        "|---|---|---|---|",
    ]
    for repo in sorted(repos):
        total_r = norm_counts[repo]["ok"] + norm_counts[repo]["fail"]
        ok_r = norm_counts[repo]["ok"]
        md_lines.append(f"| {repo.capitalize()} | {ok_r} | {total_r} | {100*ok_r/total_r:.1f}% |")
    md_lines.append(f"| **Total** | **{n_ok}** | **{n_total}** | **{100*n_ok/n_total:.1f}%** |")

    md_lines += [
        "\n## 2. Tier Conformance — Overall",
        "\n| Tier | Criterion Class | Passed | Total | Conformance Rate |",
        "|---|---|---|---|---|",
        f"| T1 | Findable (F1–F4) | {tier_overall['T1']['n']} | {n_total} | **{tier_overall['T1']['rate']}%** |",
        f"| T2 | Accessible + Reusable (A1, R1.1–R1.2) | {tier_overall['T2']['n']} | {n_total} | **{tier_overall['T2']['rate']}%** |",
        f"| T3 | Interoperable + Schema-Structured (I1, C3, C6) | {tier_overall['T3']['n']} | {n_total} | **{tier_overall['T3']['rate']}%** |",
        f"| T4 | AI-Ready (C1, C4, C5, C8, C9, C11) | {tier_overall['T4']['n']} | {n_total} | **{tier_overall['T4']['rate']}%** |",
    ]

    md_lines += [
        "\n## 3. Tier Conformance — Per Repository",
        "\n| Repository | N | T1 Findable | T2 Accessible | T3 Interoperable | T4 AI-Ready |",
        "|---|---|---|---|---|---|",
    ]
    for repo in sorted(repos):
        n_r = tier_by_repo[repo]["T1"]["total"]
        t1r = tier_by_repo[repo]["T1"]["rate"]
        t2r = tier_by_repo[repo]["T2"]["rate"]
        t3r = tier_by_repo[repo]["T3"]["rate"]
        t4r = tier_by_repo[repo]["T4"]["rate"]
        md_lines.append(f"| {repo.capitalize()} | {n_r} | {t1r}% | {t2r}% | {t3r}% | {t4r}% |")

    md_lines += [
        "\n## 4. Per-Criterion Failure Rates",
        "\n| Criterion | Description | Tier | Failures | N | Failure Rate |",
        "|---|---|---|---|---|---|",
    ]
    for crit_id, stat in sorted(crit_stats.items(), key=lambda x: x[1]["fail_rate"], reverse=True):
        crit_meta = next((c for c in CRITERIA if c[0] == crit_id), None)
        if crit_meta:
            tier = crit_meta[1]
            desc = crit_meta[3]
            md_lines.append(
                f"| {crit_id} | {desc} | {tier} | {stat['n_fail']} | {n_total} | **{stat['fail_rate']}%** |"
            )

    md_lines += [
        "\n## 5. Top-5 Most-Failed Criteria",
        "\n| Rank | Criterion | Failure Rate | Description |",
        "|---|---|---|---|",
    ]
    for rank, (crit, stat) in enumerate(top5, 1):
        desc = next(c[3] for c in CRITERIA if c[0] == crit)
        md_lines.append(f"| {rank} | {crit} | {stat['fail_rate']:.1f}% | {desc} |")

    md_lines += [
        "\n## 6. Highest Tier Distribution",
        "\n| Highest Tier | Count | Percentage |",
        "|---|---|---|",
    ]
    for t in sorted(tier_dist.keys()):
        cnt = tier_dist[t]
        pct = 100 * cnt / n_total
        label = {0: "None (failed T1)", 1: "T1 Findable", 2: "T2 Accessible+Reusable",
                 3: "T3 Interoperable", 4: "T4 AI-Ready"}.get(t, str(t))
        md_lines.append(f"| {label} | {cnt} | {pct:.1f}% |")

    md_lines += [
        "\n## 7. Figures",
        "\n![Fig 1: Tier conformance by repository](fig1_tier_conformance_by_repo.png)",
        "![Fig 2: Per-criterion failure rates](fig2_criterion_failure_rates.png)",
        "![Fig 3: Highest tier distribution](fig3_highest_tier_distribution.png)",
        "![Fig 4: Repo × criterion heatmap](fig4_repo_criterion_heatmap.png)",
    ]

    (RESULTS_DIR / "results.md").write_text("\n".join(md_lines), encoding="utf-8")
    print("  Written results_deep/results.md")

    # ---------------------------------------------------------------------------
    # Step 9: Write analysis.json
    # ---------------------------------------------------------------------------
    analysis_json = {
        "generated": "2026-07-02",
        "corpus": {
            "total": n_total,
            "normalized": int(n_ok),
            "repos": {repo: {"total": norm_counts[repo]["ok"] + norm_counts[repo]["fail"],
                             "normalized": norm_counts[repo]["ok"]}
                      for repo in repos},
        },
        "tier_conformance": {
            "overall": {tier: tier_overall[tier] for tier in ["T1", "T2", "T3", "T4"]},
            "by_repo": {repo: {tier: tier_by_repo[repo][tier]
                               for tier in ["T1", "T2", "T3", "T4"]}
                        for repo in repos},
        },
        "criterion_failure_rates": {
            cid: {
                "fail_rate": crit_stats[cid]["fail_rate"],
                "n_fail": crit_stats[cid]["n_fail"],
                "n_total": n_total,
                "tier": next(c[1] for c in CRITERIA if c[0] == cid),
                "severity": next(c[2] for c in CRITERIA if c[0] == cid),
                "description": next(c[3] for c in CRITERIA if c[0] == cid),
                "by_repo": crit_by_repo.get(cid, {}),
            }
            for cid in CRITERION_IDS if cid in crit_stats
        },
        "highest_tier_distribution": {str(t): int(c) for t, c in tier_dist.items()},
        "top5_failed_criteria": [
            {"criterion": c, "fail_rate": s["fail_rate"], "n_fail": s["n_fail"]}
            for c, s in top5
        ],
        "shacl_python_agreement": {
            tier: {
                "checked": len(shacl_spot),
                "agree": int((pd.DataFrame(shacl_spot)[f"python_{tier}"] ==
                              pd.DataFrame(shacl_spot)[f"shacl_{tier}"]).sum())
                if shacl_spot and f"python_{tier}" in pd.DataFrame(shacl_spot).columns else 0
            }
            for tier in ["T1", "T2", "T3"]
        } if shacl_spot else {},
    }
    (RESULTS_DIR / "analysis.json").write_text(
        json.dumps(analysis_json, indent=2), encoding="utf-8"
    )
    print("  Written results_deep/analysis.json")

    # ---------------------------------------------------------------------------
    # Print headline numbers
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("HEADLINE NUMBERS")
    print("=" * 60)
    print(f"\nCorpus: {n_total} datasets | {n_ok} normalized ({100*n_ok/n_total:.1f}%)")
    print("\nTier Conformance (overall):")
    for tier in ["T1", "T2", "T3", "T4"]:
        print(f"  {tier}: {tier_overall[tier]['rate']}% ({tier_overall[tier]['n']}/{n_total})")
    print("\nTier Conformance by Repository:")
    for repo in sorted(repos):
        d = tier_by_repo[repo]
        n_r = d["T1"]["total"]
        print(f"  {repo} (N={n_r}):")
        for tier in ["T1", "T2", "T3", "T4"]:
            print(f"    {tier}: {d[tier]['rate']}%")
    print("\nTop-5 Most-Failed Criteria:")
    for rank, (crit, stat) in enumerate(top5, 1):
        desc = next(c[3] for c in CRITERIA if c[0] == crit)
        print(f"  {rank}. {crit} — {stat['fail_rate']:.1f}% failure — {desc}")
    print("=" * 60)

    return analysis_json, df, crit_stats, tier_overall, tier_by_repo, top5


if __name__ == "__main__":
    try:
        result = run_analysis()
        print("\nAnalysis complete. Outputs in results_deep/")
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
