#!/usr/bin/env python3
"""Deterministic gate for evidence records. A script decides what a script can decide.

  python3 tools/ledger.py validate data/staging/*.json   # structure, vocabulary, quotes
  python3 tools/ledger.py merge    data/staging/*.json   # only PASS records enter the ledger
  python3 tools/ledger.py check                          # whole-ledger consistency

A staging record is one JSON file per study:
  {"study_id": "...", "access": "FULL_TEXT|ABSTRACT_ONLY|BLOCKED",
   "excerpt_file": "papers/excerpts/<study_id>.txt",
   "rows":   [ {<every column of data/evidence.csv>} , ... ],
   "quotes": [ {"row": 0, "field": "arm_result", "quote": "<verbatim>", "location": "Table 1"} ],
   "verifier": {"status": "PENDING|PASS|FAIL", "notes": "", "date": "YYYY-MM-DD (optional)"}}

On merge, each row's verification_status is set from the verifier block:
"PASS (verifier <date>; <access>)". The date is verifier.date, else the first
YYYY-MM-DD in verifier.notes, else "date not recorded".

A record with a top-level "retracted" block (the source was retracted) is never
merged, whatever its verifier status; its rows stay out of the ledger.

Numbers the extractor inferred (not printed in the source) go in [square brackets]
inside the cell and are exempt from the quote check.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER, QUOTES = ROOT / "data" / "evidence.csv", ROOT / "data" / "evidence_quotes.jsonl"
MODULES = {"1-hypopigmentation", "2-hyperpigmentation", "3-dermal-texture", "4-surface-vascular"}
TIERS = {"partial_repigmentation", "complete_area_coverage", "lasting_color_match", "lesion_count",
         "instrument_color", "pigment_clearance", "dermal_thickness", "unquantified", "not_extracted"}
MONTH_TOKENS = {"NOT_APPLICABLE", "NOT_REPORTED", "NOT_DERIVABLE", "NOT_EXTRACTED"}
UNIT_WORDS = ("lesion", "patient", "limb", "side", "not")
QUOTED_FIELDS = ("arm_result", "patients_enrolled", "lesions_enrolled", "dark_overshoot", "texture_or_scar",
                 "time_from_last_treatment")
NUM = re.compile(r"\d+(?:\.\d+)?")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def verification_label(rec):
    v = rec["verifier"]
    date = v.get("date") or next(iter(DATE.findall(v.get("notes", ""))), "date not recorded")
    return f"{v['status']} (verifier {date}; {rec['access']})"


def header():
    with open(LEDGER, newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh))


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def validate_record(rec, cols):
    errs = []
    for key in ("study_id", "access", "rows", "quotes", "verifier"):
        if key not in rec:
            errs.append(f"missing key '{key}'")
    if errs:
        return errs
    if rec["access"] not in ("FULL_TEXT", "ABSTRACT_ONLY", "BLOCKED"):
        errs.append(f"access '{rec['access']}' not allowed")
    excerpt = None
    if rec["access"] != "BLOCKED":
        p = ROOT / rec.get("excerpt_file", "")
        if not rec.get("excerpt_file") or not p.is_file():
            errs.append(f"excerpt_file missing: {rec.get('excerpt_file')}")
        else:
            excerpt = norm(p.read_text(encoding="utf-8", errors="replace"))
    for i, row in enumerate(rec["rows"]):
        tag = f"row {i}"
        missing = [c for c in cols if not str(row.get(c, "")).strip()]
        extra = [c for c in row if c not in cols]
        if missing:
            errs.append(f"{tag}: blank or missing columns {missing}")
        if extra:
            errs.append(f"{tag}: unknown columns {extra}")
        if missing:
            continue
        if row["study_id"] != rec["study_id"]:
            errs.append(f"{tag}: study_id differs from record")
        if row["module"] not in MODULES:
            errs.append(f"{tag}: module '{row['module']}' not allowed")
        if row["outcome_tier"] not in TIERS:
            errs.append(f"{tag}: outcome_tier '{row['outcome_tier']}' not allowed")
        if not row["analysis_unit"].lower().startswith(UNIT_WORDS):
            errs.append(f"{tag}: analysis_unit must start with lesion, patient, limb or side")
        m = row["months_after_final_tx"]
        if m not in MONTH_TOKENS:
            try:
                assert float(m) >= 0
            except (ValueError, AssertionError):
                errs.append(f"{tag}: months_after_final_tx '{m}' is neither a number nor an allowed token")
        if row["outcome_tier"] == "lasting_color_match" and (m in MONTH_TOKENS or float(m) < 6):
            errs.append(f"{tag}: lasting_color_match needs months_after_final_tx >= 6")
        if not row["source_url"].startswith("https://"):
            errs.append(f"{tag}: source_url must be https")
        if rec["access"] == "BLOCKED":
            continue
        for f in QUOTED_FIELDS:
            cell = re.sub(r"\[[^\]]*\]", " ", row[f])
            nums = set(NUM.findall(cell))
            if not nums:
                continue
            qs = [q["quote"] for q in rec["quotes"] if q.get("row") == i and q.get("field") == f]
            if not qs:
                errs.append(f"{tag}: {f} has numbers but no quote")
                continue
            have = set(NUM.findall(" ".join(qs)))
            lost = sorted(nums - have)
            if lost:
                errs.append(f"{tag}: {f} numbers {lost} appear in no quote (put inferred values in [brackets])")
    for j, q in enumerate(rec["quotes"]):
        if not all(k in q for k in ("row", "field", "quote", "location")):
            errs.append(f"quote {j}: needs row, field, quote, location")
            continue
        if len(q["quote"]) > 300:
            errs.append(f"quote {j}: longer than 300 characters")
        if excerpt is not None and norm(q["quote"]) not in excerpt:
            errs.append(f"quote {j}: not found verbatim in {rec['excerpt_file']}")
    if rec["verifier"].get("status") not in ("PENDING", "PASS", "FAIL"):
        errs.append("verifier.status must be PENDING, PASS or FAIL")
    return errs


def cmd_validate(paths, quiet=False):
    cols, bad = header(), 0
    for p in paths:
        errs = validate_record(json.loads(Path(p).read_text(encoding="utf-8")), cols)
        bad += bool(errs)
        if not quiet or errs:
            print(("FAIL " if errs else "ok   ") + str(p))
        for e in errs:
            print("     - " + e)
    return 1 if bad else 0


def cmd_merge(paths):
    cols = header()
    with open(LEDGER, newline="", encoding="utf-8") as fh:
        ledger = list(csv.DictReader(fh))
    quotes = [json.loads(l) for l in QUOTES.read_text(encoding="utf-8").splitlines() if l.strip()] if QUOTES.exists() else []
    merged = 0
    for p in paths:
        rec = json.loads(Path(p).read_text(encoding="utf-8"))
        if rec.get("retracted"):
            print(f"skip  {p} (source retracted: {rec['retracted'].get('notice', 'no notice recorded')})")
            continue
        if validate_record(rec, cols) or rec["verifier"]["status"] != "PASS":
            print(f"skip  {p} (fails validation or verifier status is {rec.get('verifier', {}).get('status')})")
            continue
        sid = rec["study_id"]
        label = verification_label(rec)
        rows = [dict(r, verification_status=label) for r in rec["rows"]]
        ledger = [r for r in ledger if r["study_id"] != sid] + rows   # a study is replaced whole
        quotes = [q for q in quotes if q["study_id"] != sid] + [dict(q, study_id=sid) for q in rec["quotes"]]
        merged += 1
        print(f"merge {p} ({len(rec['rows'])} rows, {len(rec['quotes'])} quotes)")
    with open(LEDGER, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader(); w.writerows(ledger)
    QUOTES.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in quotes), encoding="utf-8")
    print(f"{merged} of {len(paths)} records merged; ledger has {len(ledger)} rows")
    return 0


def cmd_check():
    with open(LEDGER, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    quoted = {json.loads(l)["study_id"] for l in QUOTES.read_text(encoding="utf-8").splitlines() if l.strip()} if QUOTES.exists() else set()
    blanks = sum(1 for r in rows for v in r.values() if not v.strip())
    studies = sorted({r["study_id"] for r in rows})
    unquoted = [s for s in studies if s not in quoted and not next(r for r in rows if r["study_id"] == s)["verification_status"].startswith("lead")]
    igh = [float(r["months_after_final_tx"]) for r in rows
           if r["diagnosis"].startswith("IGH") and r["months_after_final_tx"] not in MONTH_TOKENS]
    print(f"rows {len(rows)} | studies {len(studies)} | blank cells {blanks}")
    print(f"longest months after final treatment, IGH rows: {max(igh) if igh else 'n/a'}")
    print(f"lasting_color_match rows: {sum(r['outcome_tier'] == 'lasting_color_match' for r in rows)}")
    print(f"extracted studies still without verbatim quotes ({len(unquoted)}): {', '.join(unquoted) or 'none'}")
    return 1 if blanks else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["validate"] and len(a) > 1:
        sys.exit(cmd_validate(a[1:]))
    if a[:1] == ["merge"] and len(a) > 1:
        sys.exit(cmd_merge(a[1:]))
    if a == ["check"]:
        sys.exit(cmd_check())
    sys.exit(__doc__)
