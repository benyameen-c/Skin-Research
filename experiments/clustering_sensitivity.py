#!/usr/bin/env python3
"""How much do published spot-level results depend on treating spots as independent?

REANALYSIS OF PUBLISHED COUNTS. No new patient data. Spots from one person are
not independent trials. With m spots per patient and within-patient correlation
ICC, the design effect is 1 + (m - 1) * ICC and the effective sample size is
n / design effect. ICC is unknown for IGH, so the whole range 0..1 is shown.

Run:  python3 experiments/clustering_sensitivity.py --out data
"""
import argparse, csv, math
from pathlib import Path

ICCS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)

# (study_id, label, successes_a, n_a, successes_b, n_b, spots_per_patient, source)
COMPARISONS = (
    ("deoson2025", "cryotherapy vs 50% TCA, >75% repigmentation at 4 months",
     29, 75, 15, 75, 5, "Deoson 2025, Table 1"),
)
SINGLE_ARMS = (
    ("deepadarshan2023", "308-nm excimer, >75% improvement at week 16", 83, 200, 5, "Deepadarshan 2023, Table 1"),
    ("deepadarshan2023", "308-nm excimer, persistent post-inflammatory hyperpigmentation", 18, 200, 5,
     "Deepadarshan 2023, adverse effects"),
)


def p_two_sided(z):
    return math.erfc(abs(z) / math.sqrt(2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    out = Path(ap.parse_args().out)
    rows = []
    for sid, label, a, na, b, nb, m, src in COMPARISONS:
        pa, pb = a / na, b / nb
        for icc in ICCS:
            de = 1 + (m - 1) * icc
            se = math.sqrt(pa * (1 - pa) / (na / de) + pb * (1 - pb) / (nb / de))
            diff = pa - pb
            rows.append({
                "study_id": sid, "quantity": label, "kind": "difference_between_arms", "assumed_icc": icc,
                "design_effect": round(de, 2), "effective_spots_per_arm": round(na / de, 1),
                "estimate_pct": round(100 * diff, 1),
                "ci95_low_pct": round(100 * (diff - 1.96 * se), 1),
                "ci95_high_pct": round(100 * (diff + 1.96 * se), 1),
                "p_two_sided": round(p_two_sided(diff / se), 4), "source": src,
            })
    for sid, label, a, n, m, src in SINGLE_ARMS:
        p = a / n
        for icc in ICCS:
            de = 1 + (m - 1) * icc
            se = math.sqrt(p * (1 - p) / (n / de))
            rows.append({
                "study_id": sid, "quantity": label, "kind": "single_arm_proportion", "assumed_icc": icc,
                "design_effect": round(de, 2), "effective_spots_per_arm": round(n / de, 1),
                "estimate_pct": round(100 * p, 1),
                "ci95_low_pct": round(100 * (p - 1.96 * se), 1),
                "ci95_high_pct": round(100 * (p + 1.96 * se), 1),
                "p_two_sided": "", "source": src,
            })
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "clustering_sensitivity.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r["study_id"], r["kind"], "ICC", r["assumed_icc"], "->", r["estimate_pct"],
              f'[{r["ci95_low_pct"]}, {r["ci95_high_pct"]}]', r["p_two_sided"])


if __name__ == "__main__":
    main()
