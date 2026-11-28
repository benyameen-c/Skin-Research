#!/usr/bin/env python3
"""Counts behind content/evidence-summary.md, and a number check for that page.

  python3 tools/evidence_summary.py                     # print the counts (pasted into the page's appendix)
  python3 tools/evidence_summary.py --check <page.md>   # every number on the page must be quoted

Counts only: studies and rows. It never pools, averages or totals results across
studies, because studies differ in unit (patients, spots, limbs, sides), outcome
tier and timing.

--check rule. Above the first heading that contains "Appendix", each number on a line must appear in a
verbatim quote (data/evidence_quotes.jsonl) of a study_id named on that line.
A line that says "(count, appendix)" is instead checked against the printed
counts. Numbers inside `inline code`, study ids (letters then a year), PMIDs,
"Module N", "CO2" and "5-fluorouracil"
are skipped, and numbers a quote prints in words ("Forty-three", "Two") count.
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER, QUOTES = ROOT / "data" / "evidence.csv", ROOT / "data" / "evidence_quotes.jsonl"
TOKENS = ("NOT_APPLICABLE", "NOT_REPORTED", "NOT_DERIVABLE", "NOT_EXTRACTED")
CONTROL_CLASSES = {"control", "needling_sham"}
NUM = re.compile(r"\d+(?:\.\d+)?")
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen " \
       "sixteen seventeen eighteen nineteen".split()
TENS = dict(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10)))
WORD = re.compile(r"\b(%s)(?:-(%s))?\b" % ("|".join(TENS), "|".join(ONES[1:10])) + r"|\b(%s)\b" % "|".join(ONES), re.I)


def words_to_digits(text):
    """'Forty-three' -> '43', 'Two' -> '2', so a quote printed in words still supports a digit."""
    def sub(m):
        if m.group(1):
            return str(TENS[m.group(1).lower()] + (ONES.index(m.group(2).lower()) if m.group(2) else 0))
        return str(ONES.index(m.group(3).lower()))
    return WORD.sub(sub, text)

# Keyword screens on the free-text fields. Each prints the matching studies so a
# reader can open the rows and judge; a match is a pointer, not a finding.
SCREENS = [
    ("lesions clustered in patients, or analysed as independent",
     ("uncertainty",), r"independent|cluster"),
    ("blinding stated as done in design or assessment",
     ("design", "assessment_method"),
     r"double-blind|single-blinded|evaluator-blinded|blinded observer|blinded dermatologists"),
    ("single treatment session",
     ("intervention",), r"single (treatment )?session"),
    ("face named as a treated site",
     ("body_site", "uncertainty"), r"\bfac(e|ial)\b"),
    ("denominator or count that does not fit, or conflicts",
     ("uncertainty",),
     r"not a whole-number|do not all fit|denominator conflict|count conflict|conflicts with the design|not any whole number"),
]


def load():
    with open(LEDGER, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    quotes = [json.loads(l) for l in QUOTES.read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows, quotes


def dx(r):
    if r["verification_status"].startswith("lead"):
        return "lead"
    d = r["diagnosis"].strip().lower()
    if d.startswith("adjacent"):
        return "adjacent"
    if d.startswith("mixed"):
        return "mixed"
    if d.startswith("igh") or d.startswith("idiopathic guttate"):
        return "IGH"
    return "other"


def access(r):
    a = r["access_level"].lower()
    if a.startswith("abstract"):
        return "ABSTRACT_ONLY"
    if a.startswith("full_text") or a.startswith("full text"):
        return "FULL_TEXT"
    return "lead"


def months(r):
    m = r["months_after_final_tx"].strip()
    return None if m in TOKENS else float(m)


def unit(r):
    return r["analysis_unit"].split()[0].strip("[(;,").lower() if r["analysis_unit"].strip() else "blank"


def report(rows):
    out = []
    p = out.append
    studies = sorted({r["study_id"] for r in rows})
    by_study = defaultdict(list)
    for r in rows:
        by_study[r["study_id"]].append(r)

    p(f"ledger rows: {len(rows)}; studies: {len(studies)}")
    p("")
    p("A. Rows and studies by diagnosis group (a study can sit in more than one group)")
    for g in ("IGH", "mixed", "adjacent", "lead", "other"):
        rs = [r for r in rows if dx(r) == g]
        ss = sorted({r["study_id"] for r in rs})
        if rs:
            p(f"  {g:9s} rows {len(rs):3d}  studies {len(ss):2d}: {', '.join(ss)}")
    p("")
    igh_studies = sorted({r["study_id"] for r in rows if dx(r) == "IGH"})
    p(f"B. Access level of the {len(igh_studies)} studies with IGH rows")
    acc = defaultdict(list)
    for s in igh_studies:
        acc[access(by_study[s][0])].append(s)
    for k in sorted(acc):
        p(f"  {k:13s} {len(acc[k]):2d}: {', '.join(acc[k])}")
    p("")
    igh = [r for r in rows if dx(r) == "IGH"]
    treated = [r for r in igh if r["treatment_class"] not in CONTROL_CLASSES]
    p(f"C. months_after_final_tx on IGH rows ({len(igh)} rows; {len(treated)} treated-arm rows)")
    c_all = Counter(r["months_after_final_tx"] if months(r) is None else "a number" for r in igh)
    c_tr = Counter(r["months_after_final_tx"] if months(r) is None else "a number" for r in treated)
    for k in sorted(c_all):
        p(f"  {k:15s} all IGH rows {c_all[k]:3d} | treated-arm rows {c_tr.get(k, 0):3d}")
    num = sorted(((months(r), r["study_id"]) for r in igh if months(r) is not None), reverse=True)
    p("  rows with a number: " + "; ".join(f"{s} {m:g}" for m, s in num))
    with_num = sorted({s for _, s in num})
    p(f"  IGH studies with at least one row timed from the final treatment: {len(with_num)} of {len(igh_studies)}")
    p(f"  IGH rows at 6 months or more after the final treatment: {sum(1 for m, _ in num if m >= 6)}")
    p("")
    p("D. Outcome tier, IGH rows")
    for k, v in sorted(Counter(r["outcome_tier"] for r in igh).items()):
        p(f"  {k:24s} {v:3d}")
    for t in ("complete_area_coverage", "lasting_color_match"):
        p(f"  {t} rows in the whole ledger: {sum(r['outcome_tier'] == t for r in rows)}")
    p("")
    p("E. Per study (IGH, mixed and adjacent rows; leads left out)")
    p("  study_id | group | access | treatment classes | units | tiers | longest months after final tx")
    for s in studies:
        rs = [r for r in by_study[s] if dx(r) != "lead"]
        if not rs:
            continue
        groups = "+".join(sorted({dx(r) for r in rs}))
        classes = ",".join(sorted({r["treatment_class"] for r in rs}))
        units = ",".join(sorted({unit(r) for r in rs}))
        tiers = ",".join(sorted({r["outcome_tier"] for r in rs}))
        ms = [months(r) for r in rs if months(r) is not None]
        longest = f"{max(ms):g}" if ms else "none"
        p(f"  {s} | {groups} | {access(rs[0])} | {classes} | {units} | {tiers} | {longest}")
    p("")
    p("F. Control and sham arms, all groups (arm_result as recorded)")
    for r in rows:
        if r["treatment_class"] in CONTROL_CLASSES:
            p(f"  {r['study_id']} [{dx(r)}] {r['treatment_class']}: {r['arm_result'][:150]}")
    p("")
    p("G. Keyword screens on IGH studies (pointers to rows, not findings)")
    ctl = re.compile(r"placebo|untreated|control", re.I)
    has_ctl = sorted({r["study_id"] for r in igh
                      if r["treatment_class"] in CONTROL_CLASSES
                      or (ctl.search(r["comparator"]) and not re.match(r"\s*(none|not)", r["comparator"], re.I))})
    no_ctl = [s for s in igh_studies if s not in has_ctl]
    p(f"  untreated, placebo or sham comparison (control or sham row, or comparator names one): "
      f"{len(has_ctl)} of {len(igh_studies)}: {', '.join(has_ctl)}")
    p(f"  no such comparison (single arm, case report, or active treatments only): "
      f"{len(no_ctl)} of {len(igh_studies)}: {', '.join(no_ctl)}")
    for label, fields, pat in SCREENS:
        rx = re.compile(pat, re.I | re.M)
        hit = sorted({r["study_id"] for r in igh if any(rx.search(r[f]) for f in fields)})
        p(f"  {label}: {len(hit)} of {len(igh_studies)}: {', '.join(hit) or 'none'}")
    return "\n".join(out)


def check(page, rows, quotes):
    qnums = defaultdict(set)
    for q in quotes:
        qnums[q["study_id"]].update(NUM.findall(words_to_digits(q["quote"].replace(",", ""))))
    counts = set(NUM.findall(report(rows)))
    ids = sorted({r["study_id"] for r in rows}, key=len, reverse=True)
    bad, in_appendix, in_code = [], False, False
    for n, line in enumerate(Path(page).read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if line.startswith("#") and "appendix" in line.lower():
            in_appendix = True
        if in_appendix or in_code:
            continue
        cited = [s for s in ids if s in line]
        text = line
        for s in ids:
            text = text.replace(s, " ")
        text = re.sub(r"`[^`]*`|\b[A-Za-z]+\d{4,}\b|PMIDs?[ \d,and]+|Module \d|CO2|CO₂|5-fluorouracil|\d{4}-\d{2}-\d{2}|#\w[\w-]*|\]\([^)]*\)", " ", text)
        text = re.sub(r"(?<=\d),(?=\d{3})", "", text)
        is_count = "(count, appendix)" in line.lower()
        for x in NUM.findall(text):
            if is_count:
                ok = x in counts
            else:
                ok = any(x in qnums[s] for s in cited)
            if not ok:
                bad.append(f"line {n}: {x} {'not in the printed counts' if is_count else 'not in a quote of ' + (', '.join(cited) or 'any cited study (none cited)')}")
    print("\n".join(bad) if bad else f"ok: every number in {page} is quoted or counted")
    return 1 if bad else 0


if __name__ == "__main__":
    rows, quotes = load()
    if sys.argv[1:2] == ["--check"] and len(sys.argv) == 3:
        sys.exit(check(sys.argv[2], rows, quotes))
    if len(sys.argv) == 1:
        print(report(rows))
        sys.exit(0)
    sys.exit(__doc__)
