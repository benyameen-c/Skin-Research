"""Run:  python3 -m pytest tests -q     (or: python3 tests/test_ledger.py)"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import ledger

FIX = Path(__file__).resolve().parent / "fixtures"

def load(name):
    return json.loads((FIX / name).read_text())

def test_good_record_passes():
    assert ledger.validate_record(load("example_good.json"), ledger.header()) == []

def test_bad_record_is_caught_three_ways():
    errs = " | ".join(ledger.validate_record(load("example_bad.json"), ledger.header()))
    assert "appear in no quote" in errs          # a number with no supporting quote
    assert "needs months_after_final_tx >= 6" in errs   # endpoint conflated with durability
    assert "not found verbatim" in errs          # quote that is not in the source text

def test_current_ledger_has_no_blank_cells():
    assert ledger.cmd_check() == 0

def _merge_into_tmp(tmp_path, monkeypatch, rec):
    import csv, shutil
    ledger_copy, quotes_copy = tmp_path / "evidence.csv", tmp_path / "evidence_quotes.jsonl"
    shutil.copy(ledger.LEDGER, ledger_copy)
    monkeypatch.setattr(ledger, "LEDGER", ledger_copy)
    monkeypatch.setattr(ledger, "QUOTES", quotes_copy)
    before = list(csv.DictReader(open(ledger_copy, newline="", encoding="utf-8")))
    rp = tmp_path / "rec.json"
    rp.write_text(json.dumps(rec))
    ledger.cmd_merge([str(rp)])
    after = list(csv.DictReader(open(ledger_copy, newline="", encoding="utf-8")))
    return before, after

def test_merge_writes_verifier_status_and_date(tmp_path, monkeypatch):
    rec = load("example_good.json")
    rec["verifier"] = {"status": "PASS", "notes": "Second check, 2026-11-27, no failed cells."}
    before, after = _merge_into_tmp(tmp_path, monkeypatch, rec)
    merged = [r for r in after if r["study_id"] == rec["study_id"]]
    assert merged and all(r["verification_status"].startswith("PASS") for r in merged)
    assert all("2026-11-27" in r["verification_status"] for r in merged)
    # rows of every other study are untouched
    assert [r for r in after if r["study_id"] != rec["study_id"]] == before

def test_merge_prefers_explicit_verifier_date(tmp_path, monkeypatch):
    rec = load("example_good.json")
    rec["verifier"] = {"status": "PASS", "date": "2026-12-01", "notes": "checked 2026-11-27"}
    _, after = _merge_into_tmp(tmp_path, monkeypatch, rec)
    assert all("2026-12-01" in r["verification_status"] for r in after if r["study_id"] == rec["study_id"])

def test_merge_says_when_verifier_date_is_missing(tmp_path, monkeypatch):
    rec = load("example_good.json")
    rec["verifier"] = {"status": "PASS", "notes": "no failed cells"}
    _, after = _merge_into_tmp(tmp_path, monkeypatch, rec)
    assert all("date not recorded" in r["verification_status"] for r in after if r["study_id"] == rec["study_id"])

if __name__ == "__main__":
    test_good_record_passes(); test_bad_record_is_caught_three_ways(); test_current_ledger_has_no_blank_cells()
    print("3 tests passed")
