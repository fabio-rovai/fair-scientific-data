#!/usr/bin/env python3
"""Fetch REAL public dataset metadata (schema.org JSON-LD via DOI content negotiation),
save to examples_real/, and validate each against the SHACL dataset-contract shapes.
Real data only: records exact source URL, HTTP status, and @type for each."""
import json, pathlib, subprocess, sys, datetime
import requests

ROOT = pathlib.Path(__file__).parent.parent
EXD = ROOT / "examples_real"; EXD.mkdir(exist_ok=True)
RESD = ROOT / "results_real"; RESD.mkdir(exist_ok=True)
SHAPES = ROOT / "shapes" / "dataset-contract.shacl.ttl"

# 1) find real DATASET records on Zenodo (immune / single-cell / omics themed)
q = "https://zenodo.org/api/records?q=single%20cell%20immune&size=8&type=dataset"
hits = requests.get(q, timeout=40).json().get("hits", {}).get("hits", [])
dois = [h["doi"] for h in hits if h.get("doi")][:6]

log = []
for i, doi in enumerate(dois, 1):
    slug = f"real{i:02d}_" + doi.replace("/", "_").replace(".", "-")
    url = f"https://doi.org/{doi}"
    try:
        r = requests.get(url, headers={"Accept": "application/vnd.schemaorg.ld+json"},
                         allow_redirects=True, timeout=40)
        status = r.status_code
        data = r.json()
        atype = data.get("@type", "?")
        (EXD / f"{slug}.jsonld").write_text(json.dumps(data, indent=2))
        # validate
        vp = subprocess.run([sys.executable, str(ROOT/"src"/"validate.py"),
                             str(EXD/f"{slug}.jsonld")], capture_output=True, text=True)
        conforms = vp.returncode == 0
        (RESD / f"{slug}.report.txt").write_text(vp.stdout + "\n---STDERR---\n" + vp.stderr)
        log.append({"doi": doi, "source_url": url, "http": status, "type": atype,
                    "conforms": conforms, "exit": vp.returncode})
        print(f"{slug} | @type={atype} | conforms={conforms} (exit {vp.returncode})")
    except Exception as e:
        log.append({"doi": doi, "source_url": url, "error": str(e)})
        print(f"{slug} | ERROR {e}")

(RESD / "fetch_log.json").write_text(json.dumps(
    {"fetched_at": datetime.datetime.utcnow().isoformat()+"Z",
     "search_query": q, "records": log}, indent=2))
print("\nSUMMARY:", sum(1 for x in log if x.get("conforms")), "conform /",
      len([x for x in log if "conforms" in x]), "validated;",
      "real records saved to examples_real/")
