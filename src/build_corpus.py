#!/usr/bin/env python3
"""
build_corpus.py – Acquire ≥400 REAL scientific dataset metadata records across
Zenodo, Dryad, BioStudies, and PRIDE/ProteomeXchange.

Run:
    uv run --with requests python src/build_corpus.py

Saves:
  data/corpus/<repo>/<slug>.json       native metadata
  data/corpus/<repo>/<slug>.jsonld     schema.org JSON-LD (where available via DOI)
  data/corpus/manifest.json            every record
  CORPUS_REPORT.md                     per-repo counts + failures
"""
import json
import pathlib
import datetime
import time
import sys

import requests

ROOT = pathlib.Path(__file__).parent.parent
CORPUS = ROOT / "data" / "corpus"
for _d in ("zenodo", "dryad", "biostudies", "pride"):
    (CORPUS / _d).mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = CORPUS / "manifest.json"
REPORT_PATH = ROOT / "CORPUS_REPORT.md"

UA = {"User-Agent": "fair-scientific-data/2.0 (fabio@thetesseractacademy.com)"}
SESSION = requests.Session()
SESSION.headers.update(UA)

manifest: list[dict] = []
seen: set[str] = set()      # keys: doi or "repo:id"

stats: dict[str, dict] = {
    repo: {"fetched": 0, "jsonld": 0, "failed_api": 0, "errors": []}
    for repo in ("zenodo", "dryad", "biostudies", "pride")
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str, extra_headers: dict | None = None, timeout: int = 35, delay: float = 0.0) -> requests.Response | None:
    if delay:
        time.sleep(delay)
    hdrs = dict(UA)
    if extra_headers:
        hdrs.update(extra_headers)
    try:
        return SESSION.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
    except Exception as exc:
        return None


def _slug(doi_or_id: str) -> str:
    return doi_or_id.replace("/", "_").replace(".", "-").replace(":", "_")[:80]


def _save(repo: str, slug: str, data: dict, ext: str = "json") -> None:
    path = CORPUS / repo / f"{slug}.{ext}"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _fetch_jsonld(doi: str, repo: str, slug: str) -> bool:
    """DOI content-negotiate schema.org JSON-LD. Returns True if saved."""
    url = f"https://doi.org/{doi}"
    r = _get(url, extra_headers={"Accept": "application/vnd.schemaorg.ld+json"}, timeout=20, delay=0.15)
    if r is None:
        return False
    if r.status_code != 200:
        return False
    try:
        data = r.json()
    except Exception:
        return False
    if not isinstance(data, dict) or "@type" not in data:
        return False
    _save(repo, slug, data, "jsonld")
    return True


def _register(repo: str, id_: str, doi: str | None, url: str,
               http_status: int, atype: str, native: dict,
               jsonld_ok: bool) -> bool:
    """Deduplicate + append to manifest. Returns True if new record added."""
    key = doi if doi else f"{repo}:{id_}"
    if key in seen:
        return False
    seen.add(key)
    slug = _slug(doi if doi else f"{repo}_{id_}")
    _save(repo, slug, native)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    manifest.append({
        "repo": repo,
        "id": id_,
        "doi": doi,
        "url": url,
        "http_status": http_status,
        "type": atype,
        "jsonld": jsonld_ok,
        "fetched_at": now,
    })
    stats[repo]["fetched"] += 1
    if jsonld_ok:
        stats[repo]["jsonld"] += 1
    return True


# ---------------------------------------------------------------------------
# ZENODO
# ---------------------------------------------------------------------------
ZENODO_QUERIES = [
    ("single-cell RNA sequencing", "sc-rna"),
    ("proteomics mass spectrometry", "proteomics"),
    ("spatial transcriptomics", "spatial-tx"),
    ("metabolomics NMR", "metabolomics"),
    ("clinical genomics cancer sequencing", "clinical-genomics"),
    ("cryo-EM electron microscopy structure", "cryo-em"),
    ("metagenomics microbiome 16S", "metagenomics"),
    ("epigenomics ChIP-seq ATAC-seq", "epigenomics"),
]

print("\n=== ZENODO ===", flush=True)
for qterm, qlabel in ZENODO_QUERIES:
    added_this_query = 0
    for page in range(1, 4):   # up to 3 pages × 50 = 150 per query
        url = (
            f"https://zenodo.org/api/records"
            f"?type=dataset&q={requests.utils.quote(qterm)}&size=50&page={page}"
        )
        r = _get(url, timeout=45, delay=0.4)
        if r is None or r.status_code != 200:
            code = r.status_code if r else "timeout"
            msg = f"Zenodo q={qlabel!r} page={page}: GET {url} → {code}"
            stats["zenodo"]["errors"].append(msg)
            print(f"  FAIL {msg}", flush=True)
            break
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            break
        print(f"  q={qlabel} page={page}: {len(hits)} hits", flush=True)
        for h in hits:
            doi = h.get("doi") or h.get("conceptdoi")
            id_ = str(h.get("id", ""))
            rec_url = f"https://zenodo.org/records/{id_}"
            key = doi if doi else f"zenodo:{id_}"
            if key in seen:
                continue
            slug = _slug(doi if doi else f"zenodo_{id_}")
            jsonld_ok = _fetch_jsonld(doi, "zenodo", slug) if doi else False
            new = _register("zenodo", id_, doi, rec_url, 200, "Dataset", h, jsonld_ok)
            if new:
                added_this_query += 1
        time.sleep(0.3)
    print(f"  → {qlabel}: {added_this_query} new unique records", flush=True)

print(f"\n  Zenodo total so far: {stats['zenodo']['fetched']}", flush=True)


# ---------------------------------------------------------------------------
# DRYAD
# ---------------------------------------------------------------------------
DRYAD_QUERIES = [
    "ecology evolution phylogenetics",
    "genomics sequencing population",
    "climate ecology biodiversity",
    "neuroscience brain electrophysiology",
    "microbiome diversity metagenomics",
    "cancer clinical biomarker",
    "materials chemistry crystallography",
    "plant genetics agriculture",
]

print("\n=== DRYAD ===", flush=True)
for qterm in DRYAD_QUERIES:
    for page in range(1, 4):   # up to 3 pages × 20 = 60 per query
        url = (
            f"https://datadryad.org/api/v2/search"
            f"?q={requests.utils.quote(qterm)}&per_page=20&page={page}"
        )
        r = _get(url, timeout=45, delay=0.6)
        if r is None or r.status_code != 200:
            code = r.status_code if r else "timeout"
            msg = f"Dryad q={qterm!r} page={page}: GET {url} → {code}"
            stats["dryad"]["errors"].append(msg)
            print(f"  FAIL {msg}", flush=True)
            break
        data = r.json()
        items = data.get("_embedded", {}).get("stash:datasets", [])
        if not items:
            break
        print(f"  q={qterm!r} page={page}: {len(items)} items", flush=True)
        for item in items:
            raw_id = str(item.get("id", ""))
            ident = item.get("identifier", "")
            doi = ident[4:] if ident.startswith("doi:") else (
                ident.replace("https://doi.org/", "") if ident.startswith("https://doi.org/") else None
            )
            self_href = item.get("_links", {}).get("self", {}).get("href", "")
            rec_url = self_href or f"https://datadryad.org/stash/dataset/{ident}"
            slug = _slug(doi if doi else f"dryad_{raw_id}")
            key = doi if doi else f"dryad:{raw_id}"
            if key in seen:
                continue
            jsonld_ok = _fetch_jsonld(doi, "dryad", slug) if doi else False
            _register("dryad", raw_id, doi, rec_url, 200, "Dataset", item, jsonld_ok)
        time.sleep(0.4)

print(f"\n  Dryad total so far: {stats['dryad']['fetched']}", flush=True)


# ---------------------------------------------------------------------------
# EBI BioStudies
# ---------------------------------------------------------------------------
BIOSTUDIES_QUERIES = [
    "genomics",
    "proteomics",
    "metabolomics",
    "transcriptomics",
    "epigenomics",
    "single cell",
    "imaging fluorescence",
    "clinical cohort",
]

print("\n=== BIOSTUDIES ===", flush=True)
for qterm in BIOSTUDIES_QUERIES:
    for page in range(1, 3):   # 2 pages × 50 = 100 per query
        url = (
            f"https://www.ebi.ac.uk/biostudies/api/v1/search"
            f"?query={requests.utils.quote(qterm)}&pageSize=50&page={page}"
        )
        r = _get(url, timeout=45, delay=0.4)
        if r is None or r.status_code != 200:
            code = r.status_code if r else "timeout"
            msg = f"BioStudies q={qterm!r} page={page}: GET {url} → {code}"
            stats["biostudies"]["errors"].append(msg)
            print(f"  FAIL {msg}", flush=True)
            break
        data = r.json()
        hits = data.get("hits", [])
        if not hits:
            break
        print(f"  q={qterm!r} page={page}: {len(hits)} hits (total={data.get('totalHits')})", flush=True)
        for h in hits:
            accession = h.get("accession", "")
            if not accession:
                continue
            atype = h.get("type", "Study")
            rec_url = f"https://www.ebi.ac.uk/biostudies/studies/{accession}"
            key = f"biostudies:{accession}"
            if key in seen:
                continue
            # BioStudies search hits don't carry DOIs; skip JSON-LD attempt
            _register("biostudies", accession, None, rec_url, 200, atype, h, False)
        time.sleep(0.3)

print(f"\n  BioStudies total so far: {stats['biostudies']['fetched']}", flush=True)


# ---------------------------------------------------------------------------
# PRIDE / ProteomeXchange
# ---------------------------------------------------------------------------
print("\n=== PRIDE ===", flush=True)
for page in range(0, 6):   # 6 pages × 100 = 600 max
    url = f"https://www.ebi.ac.uk/pride/ws/archive/v2/projects?pageSize=100&page={page}"
    r = _get(url, timeout=45, delay=0.5)
    if r is None or r.status_code != 200:
        code = r.status_code if r else "timeout"
        msg = f"PRIDE page={page}: GET {url} → {code}"
        stats["pride"]["errors"].append(msg)
        print(f"  FAIL {msg}", flush=True)
        break
    items = r.json()
    if not isinstance(items, list) or not items:
        print(f"  page={page}: empty or unexpected response", flush=True)
        break
    print(f"  page={page}: {len(items)} items", flush=True)
    for item in items:
        accession = item.get("accession", "")
        if not accession:
            continue
        raw_doi = item.get("doi")
        # PRIDE DOIs look like "10.6019/PXD..." — validate
        doi = raw_doi if (raw_doi and raw_doi.startswith("10.")) else None
        rec_url = f"https://www.ebi.ac.uk/pride/archive/projects/{accession}"
        key = doi if doi else f"pride:{accession}"
        if key in seen:
            continue
        slug = _slug(doi if doi else f"pride_{accession}")
        jsonld_ok = _fetch_jsonld(doi, "pride", slug) if doi else False
        _register("pride", accession, doi, rec_url, 200, "Dataset", item, jsonld_ok)
    time.sleep(0.4)

print(f"\n  PRIDE total so far: {stats['pride']['fetched']}", flush=True)


# ---------------------------------------------------------------------------
# Write manifest
# ---------------------------------------------------------------------------
MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"\nManifest written: {len(manifest)} records → {MANIFEST_PATH}", flush=True)


# ---------------------------------------------------------------------------
# Write CORPUS_REPORT.md
# ---------------------------------------------------------------------------
total = sum(s["fetched"] for s in stats.values())
total_jsonld = sum(s["jsonld"] for s in stats.values())

# Data type distribution from manifest
type_counts: dict[str, int] = {}
repo_types: dict[str, dict[str, int]] = {r: {} for r in stats}
for rec in manifest:
    t = rec.get("type") or "unknown"
    type_counts[t] = type_counts.get(t, 0) + 1
    repo = rec["repo"]
    repo_types[repo][t] = repo_types[repo].get(t, 0) + 1

fetched_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

lines = [
    "# CORPUS REPORT",
    f"\nGenerated: {fetched_at}  |  Total unique records: **{total}**  |  With schema.org JSON-LD: **{total_jsonld}**",
    "",
    "## Per-Repository Counts",
    "",
    "| Repository | Fetched | JSON-LD | Failed API calls | Notes |",
    "|-----------|---------|---------|-----------------|-------|",
]
for repo, s in stats.items():
    errs = len(s["errors"])
    notes = s["errors"][0][:80] if s["errors"] else "—"
    lines.append(f"| {repo} | {s['fetched']} | {s['jsonld']} | {errs} | {notes} |")

lines += [
    "",
    f"**Grand total: {total} unique records** ({total_jsonld} with schema.org JSON-LD)",
    "",
    "## Data-Type Distribution",
    "",
    "| @type | Count |",
    "|-------|-------|",
]
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    lines.append(f"| {t} | {c} |")

lines += [
    "",
    "## Zenodo Query Coverage",
    "",
]
for qterm, qlabel in ZENODO_QUERIES:
    lines.append(f"- `{qterm}`")

lines += [
    "",
    "## Failed API Calls",
    "",
]
any_error = False
for repo, s in stats.items():
    for e in s["errors"]:
        lines.append(f"- **{repo}**: {e}")
        any_error = True
if not any_error:
    lines.append("None.")

REPORT_PATH.write_text("\n".join(lines) + "\n")
print(f"Report written → {REPORT_PATH}", flush=True)


# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("FINAL COUNTS")
print("=" * 60)
for repo, s in stats.items():
    print(f"  {repo:12s}: {s['fetched']:4d} records  ({s['jsonld']} JSON-LD)")
print(f"  {'TOTAL':12s}: {total:4d} unique records")
print("=" * 60)
