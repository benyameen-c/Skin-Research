#!/usr/bin/env python3
"""Do published percentages match a whole number of the stated units?

CALCULATION ON PUBLISHED NUMBERS. A percentage that no whole count can
produce means the evaluable denominator, or the unit that was rated, differs
from the number enrolled. That is a question for the full text or the authors.

Run:  python3 experiments/denominator_audit.py --out data
"""
import argparse, csv
from pathlib import Path

# study_id, quantity, published_pct, decimals, stated_n, unit, source
CLAIMS = (
    ("laosakul2017", ">75% improved, treated", 82.3, 1, 43, "lesions", "PubMed abstract, PMID 27494272"),
    ("laosakul2017", ">75% improved, control", 2.0, 0, 58, "lesions", "PubMed abstract, PMID 27494272"),
    ("rerknimitr2015", "some improvement, treated", 83.34, 2, 60, "lesions (inferred 2 per patient x 30)", "PubMed abstract, PMID 25303024"),
    ("rerknimitr2015", "some improvement, control", 18.34, 2, 60, "lesions (inferred)", "PubMed abstract, PMID 25303024"),
    ("rerknimitr2013", "physician-graded improvement", 11.0, 0, 26, "patients", "PubMed abstract, PMID 22324720"),
    ("deoson2025", ">75% repigmentation, cryotherapy", 38.7, 1, 75, "lesions", "Table 1"),
    ("deoson2025", ">75% repigmentation, TCA", 20.0, 1, 75, "lesions", "Table 1"),
    ("deepadarshan2023", ">75% improvement, week 16", 41.5, 1, 200, "lesions", "Table 1"),
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    out = Path(ap.parse_args().out)
    rows = []
    for sid, q, pct, dec, n, unit, src in CLAIMS:
        k = round(pct * n / 100)
        tol = 0.5 * 10 ** (-dec) + 0.011  # rounding half-width, plus slack for round-up conventions
        near = sorted({max(0, k - 1), k, min(n, k + 1)}, key=lambda c: abs(100 * c / n - pct))[:2]
        match = abs(100 * k / n - pct) <= tol
        rows.append({
            "study_id": sid, "quantity": q, "published_pct": pct, "stated_n": n, "unit": unit,
            "nearest_whole_counts": "; ".join(f"{c}/{n} = {100 * c / n:.2f}%" for c in sorted(near)),
            "consistent_with_stated_n": "yes" if match else "NO",
            "source": src,
        })
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "denominator_audit.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f'{r["study_id"]:18s} {r["published_pct"]:>6}% of {r["stated_n"]:>3} {r["unit"][:8]:8s} -> {r["nearest_whole_counts"]:38s} {r["consistent_with_stated_n"]}')


if __name__ == "__main__":
    main()
