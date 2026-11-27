#!/usr/bin/env python3
"""Run a PubMed query through NCBI E-utilities, log it, and save each abstract.

NOT RUN in the session that wrote it: that cloud workspace could not reach NCBI.
Run it on your own machine and treat the first run as its test.

  python3 tools/pubmed.py '"idiopathic guttate hypomelanosis"[tiab] AND 2023/12/01:3000[dp]'

Writes papers/excerpts/pmid_<id>.txt and appends one line to data/search_log.csv.
Standard library only. NCBI asks for no more than 3 requests per second without a key.
"""
import csv, datetime, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def get(endpoint, **params):
    params.setdefault("tool", "igh-repair-notebook")
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    query = sys.argv[1]
    found = json.loads(get("esearch.fcgi", db="pubmed", term=query, retmax=500, retmode="json"))["esearchresult"]
    ids = found["idlist"]
    out = ROOT / "papers" / "excerpts"
    out.mkdir(parents=True, exist_ok=True)
    for pmid in ids:
        target = out / f"pmid_{pmid}.txt"
        if not target.exists():
            time.sleep(0.4)
            target.write_text(get("efetch.fcgi", db="pubmed", id=pmid, rettype="abstract", retmode="text"), encoding="utf-8")
    with open(ROOT / "data" / "search_log.csv", "a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([datetime.date.today().isoformat(), "PubMed E-utilities", query, found["count"],
                                 "0", "abstracts saved; not yet screened", "PMIDs: " + " ".join(ids)])
    print(f"{found['count']} hits; {len(ids)} abstracts in {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
