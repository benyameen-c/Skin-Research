#!/usr/bin/env python3
"""Do published percentages match a whole number of the stated units?

CALCULATION ON PUBLISHED NUMBERS. A percentage that no whole count can
produce means the evaluable denominator, or the unit that was rated, differs
from the stated number, or the paper truncated rather than rounded. That is a
question for the full text or the authors, not a judgement of the study.

Inputs: the hand-written CLAIMS list below. Every entry names the ledger
field it comes from and two fragments, one holding the percentage and one
holding the denominator. The script refuses to run unless both fragments occur
in a verbatim quote for that study in data/evidence_quotes.jsonl, and it
records each quote's location. Denominators the ledger marks as bracketed
inferences are not audited; they are listed in NOT_AUDITED with the reason.

Run:  python3 experiments/denominator_audit.py --out data
"""
import argparse, csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUOTES = ROOT / "data" / "evidence_quotes.jsonl"

# study_id, ledger field, quantity, published pct (as printed), stated count or None,
# stated n, unit, fragment quoting the pct, fragment quoting n, note
CLAIMS = (
    ("laosakul2017", "arm_result", ">75% improved, treated", "82.3", None, 43, "lesions treated",
     "82.3% of the treated lesions", "Forty-three lesions were treated", "n printed in words"),
    ("laosakul2017", "arm_result", ">75% improved, control", "2", None, 58, "control lesions",
     "only 2% of the control", "58 lesions were assigned as control", ""),
    ("rerknimitr2013", "arm_result", "physician-graded improvement", "11", None, 26, "patients enrolled",
     "11% of the patients", "Twenty-six patients were included", "n printed in words; evaluable count not in abstract"),
    ("rerknimitr2015", "arm_result", "some improvement, treated", "83.34", None, 120, "lesions treated (abstract)",
     "83.34% of the lesions in treatment group", "A total of 120 lesions from 30 patients", "ledger notes conflict with [60] treated lesions"),
    ("rerknimitr2015", "arm_result", "some improvement, control", "18.34", None, 120, "lesions treated (abstract)",
     "18.34% in the control group", "A total of 120 lesions from 30 patients", "ledger notes conflict with [60] treated lesions"),
    ("chitvanich2016", "arm_result", "improvement, treatment side", "91.67", None, 120, "lesions treated (abstract)",
     "91.67% of the lesions on treatment side", "A total of 120 lesions were treated", "whether 120 includes control lesions is not in abstract"),
    ("shin2013", "arm_result", ">50% improvement at 2 months", "90", 36, 40, "patients enrolled",
     "36 patients (90%)", "A total of 40 patients with IGH were enrolled", ""),
    ("goldust2013", "arm_result", ">75% improvement", "47.9", 115, 240, "patients followed",
     "115 patients (47.9%)", "240 patients (40 men and 200 women) were followed", ""),
    ("goldust2013", "arm_result", "51-75% improvement", "41.6", 100, 240, "patients followed",
     "100 patients (41.6%)", "240 patients (40 men and 200 women) were followed", ""),
    ("goldust2013", "arm_result", "25-50% improvement", "10.3", 25, 240, "patients followed",
     "25 patients (10.3%)", "240 patients (40 men and 200 women) were followed", ""),
    ("goldust2013", "patient_noticeability", "very satisfied", "39.6", 95, 240, "patients",
     "95 of the 240 patients (39.6%)", "95 of the 240 patients", ""),
    ("goldust2013", "patient_noticeability", "satisfied", "42.5", 102, 240, "patients",
     "102 (42.5%)", "95 of the 240 patients", ""),
    ("goldust2013", "patient_noticeability", "slightly satisfied", "17.9", 43, 240, "patients",
     "43 patients (17.9%)", "95 of the 240 patients", ""),
    ("ravikiran2014", "arm_result", "repigmented at 3 months", "64", 89, 139, "macules",
     "89 (64%) showed repigmentation", "Of the 139 IGH macules", ""),
    ("ravikiran2014", "arm_result", "no response at 3 months", "35.9", 50, 139, "macules",
     "50 (35.9%) had no response", "Of the 139 IGH macules", ""),
    ("ravikiran2014", "arm_result", ">75% improvement, of repigmented", "45", None, 89, "repigmented macules",
     "Forty-five percent of the repigmented lesion", "(n = 89)", "pct printed in words"),
    ("ravikiran2014", "arm_result", "50-75% improvement, of repigmented", "41.5", None, 89, "repigmented macules",
     "41.5% showed 50-75% improvement, and", "(n = 89)", ""),
    ("ravikiran2014", "arm_result", "25-50% improvement, of repigmented", "13.4", None, 89, "repigmented macules",
     "13.4% of lesions showed 25-50% response", "(n = 89)", ""),
    ("rajegowda2021", "arm_result", "excellent, cryotherapy", "60", 75, 125, "macules",
     "75 (60%) macules showed excellent", "out of 125 macules treated with short contact cryotherapy", ""),
    ("rajegowda2021", "arm_result", "good, cryotherapy", "16", 20, 125, "macules",
     "20 (16%) macules showed good", "out of 125 macules treated with short contact cryotherapy", ""),
    ("rajegowda2021", "arm_result", "excellent, phenol", "29.6", 37, 125, "macules",
     "37 (29.6%)", "In phenol group, out of 125 macules", ""),
    ("rajegowda2021", "arm_result", "good, phenol", "23.2", 29, 125, "macules",
     "29 (23.2%)", "In phenol group, out of 125 macules", ""),
)

# deoson2025 Table 1 (grades), Table 2 (side effects), Table 3 (patient satisfaction)
_DEOSON = (
    ("arm_result", "G4 >75%, cryotherapy", "38.7", 29, 75, "macules", "G4 29(38.7%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G3, cryotherapy", "24", 18, 75, "macules", "G3 18(24%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G2, cryotherapy", "12", 9, 75, "macules", "G2 9(12%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G1, cryotherapy", "17.3", 13, 75, "macules", "G1 13(17.3%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G0, cryotherapy", "8", 6, 75, "macules", "G0 6(8%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G4 >75%, TCA", "20", 15, 75, "macules", "29(38.7%) 15(20%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G3, TCA", "25.3", 19, 75, "macules", "19(25.3%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G2, TCA", "24", 18, 75, "macules", "9(12%) 18(24%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G1, TCA", "9.3", 7, 75, "macules", "7(9.3%)", "Total(no. of macules) 75 75 150"),
    ("arm_result", "G0, TCA", "21.3", 16, 75, "macules", "16(21.3%)", "Total(no. of macules) 75 75 150"),
    ("dark_overshoot", "PIH, cryotherapy", "4.0", 3, 75, "macules", "PIH 3(4.0%)", "Total(no. of macules) 75 75"),
    ("dark_overshoot", "PIH alone, TCA", "2.7", 2, 75, "macules", "PIH 3(4.0%) 2(2.7%)", "Total(no. of macules) 75 75"),
    ("dark_overshoot", "persistent scabbing and PIH, TCA", "2.7", 2, 75, "macules", "Persistent scabbing, PIH 0 2(2.7%)", "Total(no. of macules) 75 75"),
    ("texture_or_scar", "persistent scabbing, cryotherapy", "5.3", 4, 75, "macules", "Persistent scabbing 4(5.3%)", "Total(no. of macules) 75 75"),
    ("texture_or_scar", "persistent scabbing, TCA", "13.3", 10, 75, "macules", "4(5.3%) 10(13.3%)", "Total(no. of macules) 75 75"),
    ("texture_or_scar", "scarring alone, TCA", "1.3", 1, 75, "macules", "Scarring 0 1(1.3%)", "Total(no. of macules) 75 75"),
    ("texture_or_scar", "persistent scabbing and scarring, TCA", "2.7", 2, 75, "macules", "Persistent scabbing, scarring 0 2(2.7%)", "Total(no. of macules) 75 75"),
    ("texture_or_scar", "no side effects, cryotherapy", "90.7", 68, 75, "macules", "No side effects 68(90.7%)", "Total(no. of macules) 75 75"),
    ("texture_or_scar", "no side effects, TCA", "77.3", 58, 75, "macules", "68(90.7%) 58(77.3%)", "Total(no. of macules) 75 75"),
    ("patient_noticeability", "satisfaction 4, cryotherapy", "66.7", 10, 15, "patients", "4 10 (66.7)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 3, cryotherapy", "20", 3, 15, "patients", "3 3 (20) 3 (20)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 2, cryotherapy", "6.7", 1, 15, "patients", "2 1 (6.7) 7 (46.7)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 1, cryotherapy", "6.7", 1, 15, "patients", "1 1 (6.7) 2 (13.3)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 4, TCA", "20", 3, 15, "patients", "10 (66.7) 3 (20)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 3, TCA", "20", 3, 15, "patients", "3 3 (20) 3 (20)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 2, TCA", "46.7", 7, 15, "patients", "7 (46.7)", "Total 15 (100) 15 (100)"),
    ("patient_noticeability", "satisfaction 1, TCA", "13.3", 2, 15, "patients", "2 (13.3)", "Total 15 (100) 15 (100)"),
)
CLAIMS += tuple(("deoson2025", f, q, p, c, n, u, pf, nf, "") for f, q, p, c, n, u, pf, nf in _DEOSON)

# deepadarshan2023 Table 1 (four visits, grades of 200 macules) and Results text
_DEEPA = (
    ("week 4", "Excellent 0 (0%)", "0", 0), ("week 4", "Good 18 (9%)", "9", 18),
    ("week 4", "Moderate 42 (21%)", "21", 42), ("week 4", "Minimal 140 (70%)", "70", 140),
    ("week 8", "Excellent 24 (12%)", "12", 24), ("week 8", "Good 37 (18.5)", "18.5", 37),
    ("week 8", "Moderate 61 (30.5%)", "30.5", 61), ("week 8", "Minimal 78 (39%)", "39", 78),
    ("week 12", "Excellent 63 (31.5%)", "31.5", 63), ("week 12", "Good 59 (29.5%)", "29.5", 59),
    ("week 12", "Moderate 39 (19.5%) Minimal", "19.5", 39), ("week 12", "Minimal 39 (19.5%)", "19.5", 39),
    ("week 16", "Excellent 83 (41.5%)", "41.5", 83), ("week 16", "Good 62 (31%)", "31", 62),
    ("week 16", "Moderate 42 (21%) Minimal 13", "21", 42), ("week 16", "Minimal 13 (6.5%)", "6.5", 13),
)
CLAIMS += tuple(("deepadarshan2023", "arm_result", f"{pf.split()[0].lower()}, {wk}", p, c, 200, "macules",
                 pf, "Among the 200 macules", "") for wk, pf, p, c in _DEEPA)
CLAIMS += (
    ("deepadarshan2023", "dark_overshoot", "PIH, persisting at 4th month", "9", 18, 200, "macules",
     "18 (9%) macules", "Among the 200 macules", ""),
    ("deepadarshan2023", "patient_noticeability", "satisfied", "37.5", 15, 40, "patients completing",
     "15 (37.5%) patients were satisfied", "40 patients completed the treatment", ""),
    ("deepadarshan2023", "patient_noticeability", "extremely satisfied", "62.5", 25, 40, "patients completing",
     "25 (62.5%) patients were extremely satisfied", "40 patients completed the treatment", ""),
)

# Percentages in the ledger that are NOT audited, and why.
# study_id, ledger field, published pct(s), reason, fragment quoting the pct
NOT_AUDITED = (
    ("rerknimitr2015", "arm_result", "83.34; 18.34", "denominator inferred, not audited: ledger's [60] treated lesions (2 per patient) is a bracketed inference; audited against the stated 120 instead",
     "83.34% of the lesions in treatment group"),
    ("rajegowda2021", "arm_result", "[24]; [47.2]", "percentage and count are bracketed inferences (minimal plus no response combined), not printed in the source",
     "out of 125 macules treated"),
    ("shin2013", "patient_noticeability", "82.5", "denominator inferred, not audited: ledger records '[denominator 40 inferred from 33/40 = 82.5%]'",
     "33 patients (82.5%)"),
    ("ravikiran2014", "dark_overshoot", "11.5", "denominator named in words only ('pigmented lesions'); ledger's note on 89 vs 139 is a bracketed inference",
     "11.5% of pigmented lesions"),
    ("ravikiran2014", "texture_or_scar", "17.2; 17.26", "no number printed with the percentage ('of IGH macules', 'of lesions')",
     "17.2% of IGH macules"),
    ("ravikiran2014", "arm_result", "45; 41.5 (abstract)", "abstract says 'of the total IGH macules' with no number; the Results version with n = 89 is audited",
     "45% of the total IGH macules"),
    ("ravikiran2014", "body_site", "20; 14", "no denominator printed", "shins (20%)"),
    ("deepadarshan2023", "body_site", "72.7; 18.2; 9.1", "denominator not reported; ledger's patient-count fit is a bracketed inference",
     "lower limbs (72.7%)"),
    ("elhoshy2025", "arm_result", "80; 85", "lesion count not in abstract", "80% of lesions"),
    ("elhoshy2025", "arm_result", "37.5; 33.33; 29; 50", "medians of a percentage scale, not proportions of a count", "37.5"),
    ("pagnoni1999", "texture_or_scar", "77; 34", "relative change in an instrument reading, not a proportion of a count", "distensibility-R0 (77%)"),
)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def load_quotes():
    by_study = {}
    with open(QUOTES) as fh:
        for line in fh:
            q = json.loads(line)
            by_study.setdefault(q["study_id"], []).append((norm(q["quote"]), q["location"]))
    return by_study


def locate(quotes, sid, frag):
    f = norm(frag)
    locs = sorted({loc for text, loc in quotes.get(sid, []) if f in text})
    return "; ".join(locs)


def decimals(pct_text):
    return len(pct_text.split(".")[1]) if "." in pct_text else 0


def fits(c, n, pct, dec):
    tol = 0.5 * 10 ** (-dec) + 0.011  # rounding half-width, plus slack for round-up conventions
    return abs(100 * c / n - pct) <= tol


def fits_truncated(c, n, pct, dec):
    """True if cutting (not rounding) 100*c/n to `dec` decimals gives the printed pct."""
    scale = 10 ** dec
    return abs(int(100 * c / n * scale + 1e-9) / scale - pct) < 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    out = Path(ap.parse_args().out)
    quotes = load_quotes()
    rows, missing = [], []
    for sid, field, q, pct_text, count, n, unit, pf, nf, note in CLAIMS:
        ploc, nloc = locate(quotes, sid, pf), locate(quotes, sid, nf)
        if not ploc or not nloc:
            missing.append(f"{sid} {q}: {'pct' if not ploc else 'n'} fragment not in quotes")
            continue
        pct, dec = float(pct_text), decimals(pct_text)
        k = round(pct * n / 100)
        near = sorted({max(0, k - 1), k, min(n, k + 1)}, key=lambda c: abs(100 * c / n - pct))[:2]
        any_fit = any(fits(c, n, pct, dec) for c in range(n + 1))
        rows.append({
            "study_id": sid, "ledger_field": field, "quantity": q, "published_pct": pct_text,
            "stated_count": "not printed" if count is None else count, "stated_n": n, "unit": unit,
            "nearest_whole_counts": "; ".join(f"{c}/{n} = {100 * c / n:.2f}%" for c in sorted(near)),
            "consistent_with_stated_n": "yes" if any_fit else "NO",
            "stated_count_fits": "n/a" if count is None else ("yes" if fits(count, n, pct, dec) else "NO"),
            "fits_if_truncated": "n/a" if any_fit else ("yes" if any(fits_truncated(c, n, pct, dec) for c in range(n + 1)) else "no"),
            "pct_quote_location": ploc, "n_quote_location": nloc, "note": note,
            "source": "data/evidence_quotes.jsonl",
        })
    skipped = []
    for sid, field, pcts, reason, pf in NOT_AUDITED:
        loc = locate(quotes, sid, pf)
        if not loc:
            missing.append(f"{sid} not-audited entry: fragment not in quotes")
            continue
        skipped.append({"study_id": sid, "ledger_field": field, "published_pct": pcts, "reason": reason, "pct_quote_location": loc})
    if missing:
        sys.exit("refusing to write, fragments not found in data/evidence_quotes.jsonl:\n  " + "\n  ".join(missing))
    out.mkdir(parents=True, exist_ok=True)
    for name, data in (("denominator_audit.csv", rows), ("denominator_not_audited.csv", skipped)):
        with open(out / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader(); w.writerows(data)
    for r in rows:
        print(f'{r["study_id"]:17s} {r["published_pct"]:>6}% of {r["stated_n"]:>3} {r["unit"][:10]:10s} -> {r["nearest_whole_counts"]:36s} {r["consistent_with_stated_n"]:3s} count:{r["stated_count_fits"]} trunc:{r["fits_if_truncated"]}')
    bad = [r for r in rows if r["consistent_with_stated_n"] == "NO" or r["stated_count_fits"] == "NO"]
    print(f"\n{len(rows)} pairs audited in {len({r['study_id'] for r in rows})} studies; "
          f"{sum(r['consistent_with_stated_n'] == 'NO' for r in rows)} fit no whole count of n; "
          f"{sum(r['stated_count_fits'] == 'NO' for r in rows)} printed counts do not give the printed pct; "
          f"{sum(r['fits_if_truncated'] == 'yes' for r in rows)} of those fit if the paper truncated instead of rounding; "
          f"{len(bad)} pairs flagged in {len({r['study_id'] for r in bad})} studies; "
          f"{len(skipped)} entries not audited")


if __name__ == "__main__":
    main()
