#!/usr/bin/env python3
"""
fetch_zenodo_supplement.py – Fetch Zenodo records that timed out in build_corpus.py.
Loads existing manifest to avoid duplication, then appends new records.

Run:
    uv run --with requests python src/fetch_zenodo_supplement.py
"""
import json
import pathlib
import datetime
import time
import requests

ROOT = pathlib.Path(__file__).parent.parent
CORPUS = ROOT / "data" / "corpus"
(CORPUS / "zenodo").mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = CORPUS / "manifest.json"
REPORT_PATH = ROOT / "CORPUS_REPORT.md"

UA = {"User-Agent": "fair-scientific-data/2.0 (fabio@thetesseractacademy.com)"}
SESSION = requests.Session()
SESSION.headers.update(UA)

# Load existing manifest + seen set
manifest: list[dict] = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else []
seen: set[str] = set()
for rec in manifest:
    key = rec["doi"] if rec.get("doi") else f"{rec['repo']}:{rec['id']}"
    seen.add(key)

print(f"Loaded {len(manifest)} existing records. Starting Zenodo fetch...", flush=True)

stats = {"fetched": 0, "jsonld": 0, "errors": []}


def _get(url: str, extra_headers: dict | None = None, timeout: int = 80, delay: float = 0.0) -> requests.Response | None:
    if delay:
        time.sleep(delay)
    hdrs = dict(UA)
    if extra_headers:
        hdrs.update(extra_headers)
    try:
        return SESSION.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
    except Exception as exc:
        print(f"  EXC: {exc}", flush=True)
        return None


def _slug(s: str) -> str:
    return s.replace("/", "_").replace(".", "-").replace(":", "_")[:80]


def _save(slug: str, data: dict, ext: str = "json") -> None:
    (CORPUS / "zenodo" / f"{slug}.{ext}").write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _fetch_jsonld(doi: str, slug: str) -> bool:
    url = f"https://doi.org/{doi}"
    r = _get(url, extra_headers={"Accept": "application/vnd.schemaorg.ld+json"}, timeout=20, delay=0.15)
    if r is None or r.status_code != 200:
        return False
    try:
        data = r.json()
    except Exception:
        return False
    if not isinstance(data, dict) or "@type" not in data:
        return False
    _save(slug, data, "jsonld")
    return True


# Simpler single/two-word queries — less likely to hit search timeout
ZENODO_QUERIES = [
    ("genomics", "genomics"),
    ("proteomics", "proteomics"),
    ("metabolomics", "metabolomics"),
    ("transcriptomics", "transcriptomics"),
    ("imaging microscopy", "imaging"),
    ("single-cell", "sc"),
    ("metagenomics", "metagenomics"),
    ("epigenomics", "epigenomics"),
    ("spatial transcriptomics", "spatial-tx"),
    ("clinical sequencing", "clinical"),
]

for qterm, qlabel in ZENODO_QUERIES:
    added_this_query = 0
    for page in range(1, 4):   # up to 3 pages × 50 = 150 per query
        url = (
            f"https://zenodo.org/api/records"
            f"?type=dataset&q={requests.utils.quote(qterm)}&size=50&page={page}"
        )
        print(f"  GET {url}", flush=True)
        r = _get(url, timeout=80, delay=0.5)
        if r is None or r.status_code != 200:
            code = r.status_code if r else "timeout"
            msg = f"q={qlabel!r} page={page}: {code}"
            stats["errors"].append(msg)
            print(f"  FAIL {msg}", flush=True)
            break
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            print(f"  q={qlabel} page={page}: 0 hits — stopping", flush=True)
            break
        print(f"  q={qlabel} page={page}: {len(hits)} hits", flush=True)
        for h in hits:
            doi = h.get("doi") or h.get("conceptdoi")
            id_ = str(h.get("id", ""))
            key = doi if doi else f"zenodo:{id_}"
            if key in seen:
                continue
            seen.add(key)
            slug = _slug(doi if doi else f"zenodo_{id_}")
            _save(slug, h)
            jsonld_ok = _fetch_jsonld(doi, slug) if doi else False
            now = datetime.datetime.utcnow().isoformat() + "Z"
            manifest.append({
                "repo": "zenodo",
                "id": id_,
                "doi": doi,
                "url": f"https://zenodo.org/records/{id_}",
                "http_status": 200,
                "type": "Dataset",
                "jsonld": jsonld_ok,
                "fetched_at": now,
            })
            stats["fetched"] += 1
            if jsonld_ok:
                stats["jsonld"] += 1
            added_this_query += 1
        time.sleep(0.4)
    print(f"  → {qlabel}: {added_this_query} new records added", flush=True)

# Write updated manifest
MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

# Recompute per-repo counts from full manifest
repo_counts: dict[str, dict] = {}
for rec in manifest:
    r = rec["repo"]
    if r not in repo_counts:
        repo_counts[r] = {"fetched": 0, "jsonld": 0}
    repo_counts[r]["fetched"] += 1
    if rec.get("jsonld"):
        repo_counts[r]["jsonld"] += 1

total = len(manifest)
total_jsonld = sum(1 for r in manifest if r.get("jsonld"))

# Update CORPUS_REPORT.md
fetched_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
lines = [
    "# CORPUS REPORT",
    f"\nGenerated: {fetched_at}  |  Total unique records: **{total}**  |  With schema.org JSON-LD: **{total_jsonld}**",
    "",
    "## Per-Repository Counts",
    "",
    "| Repository | Fetched | JSON-LD |",
    "|-----------|---------|---------|",
]
for repo, s in sorted(repo_counts.items()):
    lines.append(f"| {repo} | {s['fetched']} | {s['jsonld']} |")
lines += [
    "",
    f"**Grand total: {total} unique records** ({total_jsonld} with schema.org JSON-LD)",
    "",
    "## Zenodo Supplement Query Coverage",
    "",
]
for qterm, qlabel in ZENODO_QUERIES:
    lines.append(f"- `{qterm}`")
if stats["errors"]:
    lines += ["", "## Failed Zenodo Queries", ""]
    for e in stats["errors"]:
        lines.append(f"- {e}")
REPORT_PATH.write_text("\n".join(lines) + "\n")

print(f"\n{'='*60}")
print(f"Zenodo supplement: {stats['fetched']} new records, {stats['jsonld']} JSON-LD")
print(f"Updated manifest:  {total} total unique records")
print(f"Schema.org JSON-LD: {total_jsonld} total")
print(f"{'='*60}")
