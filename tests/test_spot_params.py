"""Tests for the spot model parameter register checker (plan step M2), written
before the checker exists.

Run:  python3 -m pytest tests -q

These tests FAIL until tools/spot_params_check.py is written. That is intended:
the builder writes the checker to this contract and may not change this file
(`git diff --exit-code <tests commit> -- tests/test_spot_params.py` stays clean).
The other tests in tests/ do not import the checker and keep passing.

SPECIFICATION (content/spot-model-plan.md, section 6, M1 and M2 "Done when";
CLAUDE.md rules 1, 5 and 9)

  M1: "every QUOTED row's quote is found word for word in its saved file by a
       checker (M2); every other row says ASSUMPTION and gives a range"
  M2: "a row marked QUOTED with a quote not in its source fails; a row with a
       blank status fails; the model refuses to load a parameter that is not in
       the register"

Register: data/spot_model_params.csv, UTF-8, header exactly
  name,symbol,unit,value_or_range,status,pmid,source_file,quote,used_in,upgrade_by

Module tools/spot_params_check.py provides:

  COLUMNS            tuple of the ten column names above, in that order.
  STATUSES           frozenset({"QUOTED", "ASSUMPTION"}). Nothing else is a status:
                     not blank, not lower case, not "NOT IN SAVED SOURCES" (those
                     plan words describe why a value is an ASSUMPTION; in the
                     register the row still says ASSUMPTION).
  DEFAULT_REGISTER   Path to data/spot_model_params.csv in the repository.
  DEFAULT_EXCERPTS   Path of the saved source texts,
                     /mnt/project-files/papers/excerpts/ (as tools/frontier_check.py).

  check_rows(rows, excerpts_dir) -> list[str]
      rows: list of dicts keyed by COLUMNS (values are strings, as csv.DictReader
      gives them). Returns one error string per problem; [] means the rows pass.
      Every error string contains the offending row's `name` (or "row <i>" when
      the name itself is blank) so a person can find it.

      Every row:
        * name, unit, value_or_range, status, used_in, upgrade_by are not blank
          (whitespace only counts as blank). Rule 5: never leave a cell blank.
        * status is exactly one of STATUSES.
        * name is unique; symbol, when not blank, is unique.
        * a row that names a source (pmid or source_file not blank) must carry a
          quote, and a row with a quote must name both pmid and source_file.
          Whatever a row's status, a source it claims is checked (next block).
        * source checks, for any row with a quote: pmid is digits only;
          source_file is a bare file name (no "/" or "\\" and not ".."), exists
          in excerpts_dir, and when it is named pmid_<digits>.txt those digits
          equal pmid; the quote, with runs of whitespace collapsed to one space
          and ends stripped, occurs in the file text treated the same way.
          The match is case-sensitive ("word for word"). A missing file is an
          error, never a skip.
      QUOTED rows:
        * quote, pmid and source_file are all present.
        * value_or_range is not in [square brackets] (rule 9: brackets mean
          inferred, and an inferred value is not QUOTED).
      ASSUMPTION rows:
        * value_or_range is wrapped in square brackets, "[...]": the range or
          description is ours, not a source's (rule 9; M1 "gives a range").

  check_file(csv_path, excerpts_dir) -> list[str]
      Reads the CSV. A header that is not exactly COLUMNS is an error (and its
      message contains "header"); an empty register (no data rows) is an error.
      Otherwise returns check_rows(...) on its rows.

  load_params(names, csv_path=DEFAULT_REGISTER, excerpts_dir=DEFAULT_EXCERPTS)
      -> dict {name: row dict}
      The only way the model reads its inputs. Checks the whole file first and
      raises ValueError if check_file reports anything (the model refuses a
      register that fails). Raises KeyError naming the parameter if any name in
      `names` is not in the register (the model refuses an input not in the
      register). Returns exactly the requested names.

  main(argv) -> int
      `python3 tools/spot_params_check.py [csv_path] [excerpts_dir]`; prints each
      error, returns 0 when there are none and 1 otherwise.

Tolerances: none. Every check here is exact (string presence, set membership),
so there is nothing numeric to tolerate.
"""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

COLUMNS = ("name", "symbol", "unit", "value_or_range", "status", "pmid",
           "source_file", "quote", "used_in", "upgrade_by")

SOURCE_TEXT = (
    "Synthetic abstract for tests only.\n"
    "The spots measured 2 to 5 mm across\nand were   found on the shins.\n"
    "Melanocytes were reduced (55.25 +/- 18.00 mm2).\n"
)


@pytest.fixture(scope="module")
def chk():
    import spot_params_check
    return spot_params_check


@pytest.fixture
def excerpts(tmp_path):
    d = tmp_path / "excerpts"
    d.mkdir()
    (d / "pmid_111.txt").write_text(SOURCE_TEXT, encoding="utf-8")
    (d / "other_222.txt").write_text("A second source. Twenty days later.\n", encoding="utf-8")
    return d


def quoted(**kw):
    row = {"name": "spot_diameter", "symbol": "d_spot", "unit": "mm",
           "value_or_range": "2 to 5", "status": "QUOTED", "pmid": "111",
           "source_file": "pmid_111.txt",
           "quote": "The spots measured 2 to 5 mm across and were found on the shins.",
           "used_in": "2.1", "upgrade_by": "photo series"}
    row.update(kw)
    return row


def assumption(**kw):
    row = {"name": "loss_rate", "symbol": "k_loss", "unit": "per day",
           "value_or_range": "[months to years]", "status": "ASSUMPTION", "pmid": "",
           "source_file": "", "quote": "", "used_in": "R2", "upgrade_by": "biopsy markers"}
    row.update(kw)
    return row


def write_csv(path, rows, header=COLUMNS):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(c, "") for c in header])
    return path


def errors_for(chk, rows, excerpts):
    errs = chk.check_rows(rows, excerpts)
    assert isinstance(errs, list)
    return errs


# ---------------------------------------------------------------- the module surface

def test_constants(chk):
    assert tuple(chk.COLUMNS) == COLUMNS
    assert set(chk.STATUSES) == {"QUOTED", "ASSUMPTION"}
    assert Path(chk.DEFAULT_REGISTER) == ROOT / "data" / "spot_model_params.csv"


def test_good_rows_pass(chk, excerpts):
    assert errors_for(chk, [quoted(), assumption()], excerpts) == []


def test_whitespace_in_quote_and_source_is_collapsed(chk, excerpts):
    # The source has a line break and three spaces inside the quoted sentence.
    row = quoted(quote="  The spots measured 2 to 5 mm\tacross and were found on the shins. ")
    assert errors_for(chk, [row], excerpts) == []


# ---------------------------------------------------------------- QUOTED rows (M2 test 1)

def test_quoted_row_with_quote_not_in_source_fails(chk, excerpts):
    row = quoted(quote="The spots measured 2 to 8 mm across")
    errs = errors_for(chk, [row], excerpts)
    assert errs and any("spot_diameter" in e for e in errs)


def test_quote_match_is_case_sensitive(chk, excerpts):
    row = quoted(quote="the spots measured 2 to 5 mm across")
    assert errors_for(chk, [row], excerpts)


def test_quote_in_a_different_saved_file_does_not_count(chk, excerpts):
    row = quoted(quote="Twenty days later.")   # in other_222.txt, not in pmid_111.txt
    assert errors_for(chk, [row], excerpts)


@pytest.mark.parametrize("field", ["quote", "pmid", "source_file"])
def test_quoted_row_missing_any_source_field_fails(chk, excerpts, field):
    assert errors_for(chk, [quoted(**{field: ""})], excerpts)


def test_quoted_row_with_whitespace_only_quote_fails(chk, excerpts):
    assert errors_for(chk, [quoted(quote="   ")], excerpts)


def test_missing_source_file_is_an_error_not_a_skip(chk, excerpts):
    assert errors_for(chk, [quoted(source_file="pmid_999.txt", pmid="999")], excerpts)


def test_pmid_must_match_pmid_file_name(chk, excerpts):
    assert errors_for(chk, [quoted(pmid="112")], excerpts)


def test_pmid_must_be_digits(chk, excerpts):
    assert errors_for(chk, [quoted(pmid="PMID 111")], excerpts)


def test_file_not_named_by_pmid_is_allowed_when_quote_matches(chk, excerpts):
    row = quoted(pmid="222", source_file="other_222.txt", quote="Twenty days later.")
    assert errors_for(chk, [row], excerpts) == []


@pytest.mark.parametrize("bad", ["../pmid_111.txt", "sub/pmid_111.txt", "..", "sub\\pmid_111.txt"])
def test_source_file_must_be_a_bare_name(chk, excerpts, bad):
    (excerpts / "sub").mkdir(exist_ok=True)
    (excerpts / "sub" / "pmid_111.txt").write_text(SOURCE_TEXT, encoding="utf-8")
    assert errors_for(chk, [quoted(source_file=bad)], excerpts)


def test_quoted_value_in_brackets_fails(chk, excerpts):
    assert errors_for(chk, [quoted(value_or_range="[2 to 5]")], excerpts)


# ---------------------------------------------------------------- status (M2 test 2)

@pytest.mark.parametrize("status", ["", "   ", "quoted", "Assumption", "NOT IN SAVED SOURCES",
                                    "NOT MEASURED IN IGH", "QUOTED "])
def test_status_must_be_exactly_quoted_or_assumption(chk, excerpts, status):
    row = quoted(status=status) if status.strip().upper().startswith("QUOTED") else assumption(status=status)
    errs = errors_for(chk, [row], excerpts)
    assert errs and any(row["name"] in e for e in errs)


# ---------------------------------------------------------------- ASSUMPTION rows

def test_assumption_without_bracketed_range_fails(chk, excerpts):
    assert errors_for(chk, [assumption(value_or_range="months to years")], excerpts)


def test_assumption_with_blank_range_fails(chk, excerpts):
    assert errors_for(chk, [assumption(value_or_range="")], excerpts)


@pytest.mark.parametrize("field,value", [("pmid", "111"), ("source_file", "pmid_111.txt")])
def test_assumption_claiming_a_source_without_a_quote_fails(chk, excerpts, field, value):
    assert errors_for(chk, [assumption(**{field: value})], excerpts)


def test_assumption_with_quote_but_no_source_fails(chk, excerpts):
    assert errors_for(chk, [assumption(quote="Melanocytes were reduced")], excerpts)


def test_assumption_citing_a_source_has_its_quote_checked(chk, excerpts):
    good = assumption(pmid="111", source_file="pmid_111.txt", quote="Melanocytes were reduced")
    bad = assumption(pmid="111", source_file="pmid_111.txt", quote="Melanocytes divided daily")
    assert errors_for(chk, [good], excerpts) == []
    assert errors_for(chk, [bad], excerpts)


# ---------------------------------------------------------------- every row

@pytest.mark.parametrize("field", ["name", "unit", "used_in", "upgrade_by"])
def test_blank_required_cell_fails(chk, excerpts, field):
    assert errors_for(chk, [assumption(**{field: " "})], excerpts)


def test_duplicate_name_fails(chk, excerpts):
    rows = [assumption(), assumption(symbol="k_other")]
    assert errors_for(chk, rows, excerpts)


def test_duplicate_symbol_fails(chk, excerpts):
    rows = [assumption(), assumption(name="other_rate")]
    assert errors_for(chk, rows, excerpts)


def test_each_bad_row_is_reported(chk, excerpts):
    rows = [quoted(name="a_bad", quote="not in the source"),
            assumption(name="b_bad", symbol="k_b", value_or_range="unbracketed"),
            assumption(name="c_good", symbol="k_c")]
    joined = " | ".join(errors_for(chk, rows, excerpts))
    assert "a_bad" in joined and "b_bad" in joined and "c_good" not in joined


# ---------------------------------------------------------------- the file

def test_check_file_passes_good_file(chk, excerpts, tmp_path):
    p = write_csv(tmp_path / "reg.csv", [quoted(), assumption()])
    assert chk.check_file(p, excerpts) == []


def test_check_file_rejects_wrong_header(chk, excerpts, tmp_path):
    header = tuple(c for c in COLUMNS if c != "upgrade_by")
    p = write_csv(tmp_path / "reg.csv", [quoted(), assumption()], header=header)
    errs = chk.check_file(p, excerpts)
    assert any("header" in e.lower() for e in errs)


def test_check_file_rejects_empty_register(chk, excerpts, tmp_path):
    p = write_csv(tmp_path / "reg.csv", [])
    assert chk.check_file(p, excerpts)


def test_check_file_reports_row_errors(chk, excerpts, tmp_path):
    p = write_csv(tmp_path / "reg.csv", [quoted(quote="invented sentence"), assumption()])
    assert chk.check_file(p, excerpts)


def test_main_exit_codes(chk, excerpts, tmp_path):
    good = write_csv(tmp_path / "good.csv", [quoted(), assumption()])
    bad = write_csv(tmp_path / "bad.csv", [quoted(status="")])
    assert chk.main([str(good), str(excerpts)]) == 0
    assert chk.main([str(bad), str(excerpts)]) == 1


# ---------------------------------------------------------------- loading (M2 test 3)

def test_load_returns_requested_rows(chk, excerpts, tmp_path):
    p = write_csv(tmp_path / "reg.csv", [quoted(), assumption()])
    got = chk.load_params(["loss_rate"], csv_path=p, excerpts_dir=excerpts)
    assert set(got) == {"loss_rate"}
    assert got["loss_rate"]["value_or_range"] == "[months to years]"


def test_load_refuses_parameter_not_in_register(chk, excerpts, tmp_path):
    p = write_csv(tmp_path / "reg.csv", [quoted(), assumption()])
    with pytest.raises(KeyError, match="made_up_rate"):
        chk.load_params(["spot_diameter", "made_up_rate"], csv_path=p, excerpts_dir=excerpts)


def test_load_refuses_a_register_that_fails_the_check(chk, excerpts, tmp_path):
    # The requested row is fine; another row's quote is not in its source.
    p = write_csv(tmp_path / "reg.csv", [quoted(quote="invented sentence"), assumption()])
    with pytest.raises(ValueError):
        chk.load_params(["loss_rate"], csv_path=p, excerpts_dir=excerpts)


# ---------------------------------------------------------------- the real register

REAL_EXCERPTS = Path("/mnt/project-files/papers/excerpts/")


@pytest.mark.skipif(not REAL_EXCERPTS.is_dir(),
                    reason="saved source texts are not in the repository; they live in the project files folder")
def test_real_register_passes(chk):
    assert chk.check_file(chk.DEFAULT_REGISTER, REAL_EXCERPTS) == []


def test_real_register_shape():
    # Holds without the checker: the M1 file has the contracted header and only the two statuses.
    with open(ROOT / "data" / "spot_model_params.csv", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert tuple(reader.fieldnames) == COLUMNS
        statuses = {r["status"] for r in reader}
    assert statuses == {"QUOTED", "ASSUMPTION"}
