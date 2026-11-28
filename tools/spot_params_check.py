#!/usr/bin/env python3
"""Check the spot model parameter register (plan step M2).

Every row of data/spot_model_params.csv is either QUOTED (its value comes from a
saved source, and its quote must be found word for word in that source) or an
ASSUMPTION (its value or range is ours and is written in [square brackets]).
A row that names a source must carry a quote, whatever its status, and that
quote is checked. No cell that matters may be blank (CLAUDE.md rule 5).

The model reads its inputs only through load_params(), which refuses a register
that fails this check and refuses any parameter that is not in the register.

The contract is the docstring of tests/test_spot_params.py.

Usage: python3 tools/spot_params_check.py [csv_path] [excerpts_dir]
Prints each error; exit 0 when there are none, 1 otherwise.
"""
import csv
import re
import sys
from pathlib import Path

COLUMNS = ("name", "symbol", "unit", "value_or_range", "status", "pmid",
           "source_file", "quote", "used_in", "upgrade_by")
STATUSES = frozenset({"QUOTED", "ASSUMPTION"})
DEFAULT_REGISTER = Path(__file__).resolve().parent.parent / "data" / "spot_model_params.csv"
DEFAULT_EXCERPTS = Path("/mnt/project-files/papers/excerpts/")

REQUIRED = ("name", "unit", "value_or_range", "status", "used_in", "upgrade_by")
PMID_FILE = re.compile(r"pmid_(\d+)\.txt")


def _norm(text):
    """Collapse runs of whitespace to one space and strip the ends. Case is kept."""
    return re.sub(r"\s+", " ", text).strip()


def _cell(row, col):
    value = row.get(col)
    return "" if value is None else value


def _bracketed(value):
    v = value.strip()
    return len(v) >= 2 and v.startswith("[") and v.endswith("]")


def _source_errors(label, row, excerpts_dir, cache):
    """Checks for a row that carries a quote: pmid, file name, file, quote."""
    errs = []
    pmid = _cell(row, "pmid").strip()
    source_file = _cell(row, "source_file").strip()
    quote = _norm(_cell(row, "quote"))

    if not pmid:
        errs.append(f"{label}: has a quote but no pmid")
    elif not pmid.isdigit():
        errs.append(f"{label}: pmid {pmid!r} is not digits only")

    if not source_file:
        errs.append(f"{label}: has a quote but no source_file")
        return errs
    if "/" in source_file or "\\" in source_file or source_file in (".", ".."):
        errs.append(f"{label}: source_file {source_file!r} is not a bare file name")
        return errs
    m = PMID_FILE.fullmatch(source_file)
    if m and m.group(1) != pmid:
        errs.append(f"{label}: source_file {source_file} does not match pmid {pmid!r}")

    path = Path(excerpts_dir) / source_file
    if path not in cache:
        cache[path] = _norm(path.read_text(encoding="utf-8", errors="replace")) if path.is_file() else None
    text = cache[path]
    if text is None:
        errs.append(f"{label}: source_file {source_file} not found in {excerpts_dir}")
    elif quote not in text:
        errs.append(f"{label}: quote not found word for word in {source_file}: {quote!r}")
    return errs


def check_rows(rows, excerpts_dir):
    """Return one error string per problem; [] means every row passes."""
    errs = []
    cache = {}
    seen_names, seen_symbols = {}, {}
    for i, row in enumerate(rows, start=1):
        name = _cell(row, "name").strip()
        label = name if name else f"row {i}"

        for col in REQUIRED:
            if not _cell(row, col).strip():
                errs.append(f"{label}: {col} is blank")

        status = _cell(row, "status")
        if status.strip() and status not in STATUSES:
            errs.append(f"{label}: status {status!r} is not exactly one of {sorted(STATUSES)}")

        if name:
            if name in seen_names:
                errs.append(f"{label}: name repeats row {seen_names[name]}")
            else:
                seen_names[name] = i
        symbol = _cell(row, "symbol").strip()
        if symbol:
            if symbol in seen_symbols:
                errs.append(f"{label}: symbol {symbol} repeats row {seen_symbols[symbol]}")
            else:
                seen_symbols[symbol] = i

        has_quote = bool(_cell(row, "quote").strip())
        names_source = bool(_cell(row, "pmid").strip() or _cell(row, "source_file").strip())
        if names_source and not has_quote:
            errs.append(f"{label}: names a source but has no quote")
        if has_quote:
            errs.extend(_source_errors(label, row, excerpts_dir, cache))

        value = _cell(row, "value_or_range")
        if status == "QUOTED":
            if not has_quote and not names_source:
                errs.append(f"{label}: QUOTED but has no quote, pmid or source_file")
            if _bracketed(value):
                errs.append(f"{label}: QUOTED value {value!r} is in [brackets], which mark an inferred value")
        elif status == "ASSUMPTION":
            if value.strip() and not _bracketed(value):
                errs.append(f"{label}: ASSUMPTION value {value!r} is not in [square brackets]")
    return errs


def _read(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    return header, rows


def check_file(csv_path, excerpts_dir):
    try:
        header, rows = _read(csv_path)
    except FileNotFoundError:
        return [f"register {csv_path} not found"]
    if header != COLUMNS:
        return [f"header is {list(header)}, expected exactly {list(COLUMNS)}"]
    if not rows:
        return [f"register {csv_path} has no data rows"]
    return check_rows(rows, excerpts_dir)


def load_params(names, csv_path=DEFAULT_REGISTER, excerpts_dir=DEFAULT_EXCERPTS):
    """Return {name: row} for exactly the requested names, from a register that passes."""
    errs = check_file(csv_path, excerpts_dir)
    if errs:
        raise ValueError(f"parameter register {csv_path} fails the check:\n" + "\n".join(errs))
    _, rows = _read(csv_path)
    by_name = {r["name"].strip(): r for r in rows}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise KeyError(f"not in the parameter register: {', '.join(missing)}")
    return {n: by_name[n] for n in names}


def main(argv):
    csv_path = argv[0] if len(argv) > 0 else DEFAULT_REGISTER
    excerpts_dir = argv[1] if len(argv) > 1 else DEFAULT_EXCERPTS
    errs = check_file(csv_path, excerpts_dir)
    for e in errs:
        print(e)
    if not errs:
        try:
            n = len(_read(csv_path)[1])
        except OSError:
            n = 0
        print(f"OK: {n} rows in {csv_path}, every quote found in {excerpts_dir}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
