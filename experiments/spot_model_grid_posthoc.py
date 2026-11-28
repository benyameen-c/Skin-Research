#!/usr/bin/env python3
"""Post-hoc summaries of the M6 grid comparison (data/spot_model_m6_sets.csv).

POST HOC: written AFTER the M6 results were seen, to put the overlap between
H1 and H2 into numbers the write-up can cite by line. Nothing here was
pre-registered, so none of it counts as a test of a prediction (plan 10.1).
CLAIM LEVEL 0, A HYPOTHESIS. Reads only the saved results file; runs no model.

Run:  python3 experiments/spot_model_grid_posthoc.py --data data
Writes data/spot_model_m6_posthoc.csv.
"""
import argparse
import csv
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    d = Path(args.data)
    with open(d / "spot_model_m6_sets.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []

    def add(item, value, note=""):
        out.append({"item": item, "value": value, "note": note,
                    "claim_level": 0, "output_is": "hypothesis", "post_hoc": True})

    for tx in ("0", "1"):
        acc = [r for r in rows if r["tx_rates"] == tx and r["accepted"] == "True"]
        by = {k: [r for r in acc if r["kind"] == k] for k in ("H1", "H2", "mixture")}
        f = lambda rs, q: np.array([float(r[q]) for r in rs])
        h1e, h2e = f(by["H1"], "edge_width_mm"), f(by["H2"], "edge_width_mm")
        add(f"tx{tx}_H1_edge_width_max_mm", f"{h1e.max():.3g}", f"{len(h1e)} accepted H1 sets")
        add(f"tx{tx}_H2_edge_width_min_mm", f"{h2e.min():.3g}", f"{len(h2e)} accepted H2 sets")
        add(f"tx{tx}_H2_sets_wider_than_every_H1_set", int((h2e > h1e.max()).sum()), f"of {len(h2e)}")
        add(f"tx{tx}_H2_sets_wider_than_H1_median_plus_0.1mm",
            int((h2e > np.median(h1e) + 0.1).sum()), f"of {len(h2e)}; 0.1 mm is the provisional threshold")
        for q, thr in (("skip_photo", 0.05), ("rim_centre_dL", 1.0)):
            for k in ("H1", "H2", "mixture"):
                v = f(by[k], q)
                add(f"tx{tx}_{k}_{q}_above_{thr}", int((v > thr).sum()), f"of {len(v)}; provisional threshold")
        for lo, hi in ((2.0, 3.0), (3.0, 4.0), (4.0, 5.01)):
            for k in ("H1", "H2"):
                rs = [r for r in by[k] if lo <= float(r["d_spot"]) < hi]
                v = f(rs, "edge_width_mm")
                add(f"tx{tx}_{k}_edge_width_median_d_{lo:g}_to_{min(hi, 5.0):g}mm",
                    f"{np.median(v):.3g}" if v.size else "none", f"{v.size} accepted sets")
        lam = f(by["H2"], "lambda_D")
        for lo, hi in ((0.05, 0.1), (0.1, 0.2), (0.2, 0.4)):
            m = (lam >= lo) & (lam < hi)
            add(f"tx{tx}_H2_edge_width_median_lambda_D_{lo:g}_to_{hi:g}mm",
                f"{np.median(h2e[m]):.3g}" if m.any() else "none", f"{int(m.sum())} accepted H2 sets")
    with open(d / "spot_model_m6_posthoc.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(f"{r['item']}: {r['value']}  {r['note']}")


if __name__ == "__main__":
    main()
