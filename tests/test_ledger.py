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

if __name__ == "__main__":
    test_good_record_passes(); test_bad_record_is_caught_three_ways(); test_current_ledger_has_no_blank_cells()
    print("3 tests passed")
