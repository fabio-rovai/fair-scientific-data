#!/usr/bin/env python3
"""Strictness analysis: fetch ~30 REAL public datasets (schema.org JSON-LD via DOI
content negotiation) and validate each against MINIMAL vs STRICT FAIR contracts.
Quantifies how many real datasets are 'contract-ready'. Real data only."""
import json, pathlib, datetime
import requests
from rdflib import Graph
from pyshacl import validate

ROOT = pathlib.Path(__file__).parent.parent
EXD = ROOT / "examples_real"; EXD.mkdir(exist_ok=True)
RESD = ROOT / "results_real"; RESD.mkdir(exist_ok=True)
MIN_SHAPES = (ROOT / "shapes" / "dataset-contract.shacl.ttl").read_text()
STRICT_SHAPES = (ROOT / "shapes" / "dataset-contract-strict.shacl.ttl").read_text()

QUERIES = ["single cell immune", "multi-omics", "proteomics", "scRNA-seq",
           "immune profiling", "spatial transcriptomics"]
dois = {}
for q in QUERIES:
    url = f"https://zenodo.org/api/records?q={requests.utils.quote(q)}&size=6&type=dataset"
    try:
        for h in requests.get(url, timeout=40).json().get("hits", {}).get("hits", []):
            if h.get("doi"):
                dois[h["doi"]] = h["metadata"]["title"][:80]
    except Exception as e:
        print("query fail", q, e)
dois = dict(list(dois.items())[:30])
print(f"collected {len(dois)} unique real dataset DOIs")

def conforms(data_graph_ttl_or_jsonld, shapes_ttl, fmt):
    g = Graph().parse(data=data_graph_ttl_or_jsonld, format=fmt)
    conf, _, _ = validate(g, shacl_graph=Graph().parse(data=shapes_ttl, format="turtle"),
                          inference="none")
    return conf

rows = []
FIELDS = ["license","version","variableMeasured","distribution","keywords",
          "creator","datePublished","identifier","description","name"]
missing_tally = {f: 0 for f in FIELDS}
for i, (doi, title) in enumerate(dois.items(), 1):
    try:
        r = requests.get(f"https://doi.org/{doi}",
                         headers={"Accept": "application/vnd.schemaorg.ld+json"},
                         allow_redirects=True, timeout=40)
        jl = r.text
        data = r.json()
        if data.get("@type") != "Dataset":
            continue
        slug = f"s{i:02d}_" + doi.replace("/","_").replace(".","-")
        (EXD / f"{slug}.jsonld").write_text(json.dumps(data, indent=2))
        cmin = conforms(jl, MIN_SHAPES, "json-ld")
        cstr = conforms(jl, STRICT_SHAPES, "json-ld")
        for f in FIELDS:
            if f not in data:
                missing_tally[f] += 1
        rows.append({"doi": doi, "title": title, "minimal": cmin, "strict": cstr})
        print(f"{slug} | min={cmin} strict={cstr} | {title[:45]}")
    except Exception as e:
        print("skip", doi, e)

N = len(rows)
min_ok = sum(1 for r in rows if r["minimal"])
str_ok = sum(1 for r in rows if r["strict"])
summary = {
    "analysed_at": datetime.datetime.now(datetime.UTC).isoformat(),
    "N_real_datasets": N,
    "minimal_conform": min_ok, "minimal_pct": round(100*min_ok/N,1) if N else None,
    "strict_conform": str_ok, "strict_pct": round(100*str_ok/N,1) if N else None,
    "field_missing_counts": missing_tally,
    "field_missing_pct": {f: round(100*c/N,1) for f,c in missing_tally.items()} if N else {},
    "rows": rows,
}
(RESD / "strictness_analysis.json").write_text(json.dumps(summary, indent=2))
print("\n=== HEADLINE ===")
print(f"N={N} real public datasets")
print(f"MINIMAL contract conform: {min_ok}/{N} ({summary['minimal_pct']}%)")
print(f"STRICT (hard-FAIR) contract conform: {str_ok}/{N} ({summary['strict_pct']}%)")
print("Top missing fields:", sorted(summary['field_missing_pct'].items(), key=lambda x:-x[1])[:5])
