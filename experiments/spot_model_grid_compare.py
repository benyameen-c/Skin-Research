#!/usr/bin/env python3
"""Compare the two explanations of an IGH spot in the GRID model (M6 runs, plan 11.4).

SIMULATION ONLY. Every number this writes is CLAIM LEVEL 0, A HYPOTHESIS: it
follows from the model's rules and assumed rates (plan 10.4). It is not
evidence, says nothing about whether any treatment works or lasts, and nothing
here enters data/evidence.csv.

Everything below was fixed and committed BEFORE the first run. No range,
threshold, set list or seed is changed after seeing output.

Which parameter sets (a choice, stated so it can be argued with)
-----------------------------------------------------------------
A grid run costs about 100 times a well-mixed run, so the 4,000-draw sweep is
NOT rerun. The grid runs every (draw, explanation) that the well-mixed sweep
accepted under either transplanted-cell setting: the same Latin-hypercube
draws (spot_model_compare.lhs, seed 20261128, n 4000), rebuilt exactly with
spot_model_compare.build_sets, and selected from data/spot_model_m4_sweep.csv
and data/spot_model_m4_tx1_sweep.csv (325 sets: H1 43, H2 231, mixture 51).
Each draw also gets a signal reach lambda_D, log-uniform over the register's
[0.05, 2] mm, from its own Latin hypercube (seed [20261128, 6], n 4000,
indexed by draw), and tx_site_capacity 2 (register: base runs).
Consequence: a set the well-mixed sweep rejected is never tried in space, so
"accepted in the grid" means "accepted by M4 AND by the grid's checks". The
grid with space switched off equals M4 (a test enforces it), so the
pre-screen only removes sets that space could have rescued; this is reported
as a limitation, not a finding.

Timeline and readouts: as M4 (spot_model_compare). Spot forms from day 0;
transplant sessions on days 7300 and 7330; follow-up counted from the FINAL
session (CLAUDE.md rule 2): +28, +180, +365 days. Every contrast is measured
from a rendered image with the measurement tool's geometry
(spot_model_grid.measure_dL; default blur 0.1 mm, no noise), not from
internal melanin. Expected mode, random fibroblasts, fibroblast_seed = draw.

Acceptance (plan 7.1 and 11.4). A set is accepted only if all hold:
  F   dL*(day 30) < 1.0 L*                                     (not in weeks)
  V1  per-site live spot / ring melanocytes on day 7299 in [0.15, 0.40]
  V2  at least 1 live melanocyte in the spot on every day before day 7300
  V3  hypoactive cells appear before any cell is lost
  V4  edge width on day 7299 (blur 0.1 mm) <= 0.5 x spot radius
  V7  dL*(day 7328) at least 1.0 L* below the baseline dL* (day 7299)
  V6  skip score >= 0.05 on a blur-0 render of day 7299 in at least half of
      4 stochastic seeds (seeds 0..3, same fibroblast map)
V6 is run only for sets that pass the other checks under at least one
setting (it is the costly stochastic step). V5 (size) is not testable:
the patch is a fixed disc (plan 11.2). V8 is a known misfit, not scored.

Readouts per accepted set and prediction scoring (plan 11.4, 7.2 step 3)
  P1 edge width (mm, day 7299, blur 0.1); P3 rim-centre dL* and photo skip
  score (blur 0.1) and cell-resolution skip score (blur 0); P4 fade from
  final + 28 to final + 180 days, from images, under tx_rates 0 and 1.
  Provisional thresholds (plan 11.4, labelled provisional in every output
  until the phantom SDC exists): 0.1 mm edge width, 1.0 L* rim-centre and P4,
  0.05 skip score. Pairs (same draw, H1 and H2 both accepted) are scored
  robust / fragile / untestable as M4 did. Because M4 had only 3 such pairs,
  the summary also gives each explanation's p10 / p50 / p90 and the share of
  accepted sets beyond each threshold, so the distributions can be compared.

One at a time: lambda_D over 7 log-spaced values in [0.05, 2] at the H2 and
mixture defaults (d_spot 3 mm), expected mode, tx_rates 0 (plan 7.2 step 1).

Builder's expectation, written before the first run (in addition to the
test-author's G1 to G5 in plan 11.5, which stand as written): H1 edge widths
cluster near the blur floor (about 0.26 to 0.35 mm) for every size; most H2
sets with lambda_D above about 0.4 mm fail V4; the accepted H2 edge widths
overlap H1's within 0.1 mm in most sets, so P1 comes out "untestable" at the
provisional threshold; the six-month P4 result matches M4 (untestable at
1.0 L*); overflow is 0 in every accepted set. A result that contradicts any
of these is reported as such.

Run:  python3 experiments/spot_model_grid_compare.py --out data [--workers 4]
Writes data/spot_model_m6_{sets,oat,summary}.csv.
"""
import argparse
import csv
import math
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import spot_model as sm
import spot_model_compare as m4
import spot_model_grid as gm

SEED = m4.SEED
N_DRAWS = 4000
LAMBDA_SEED = [SEED, 6]
LAMBDA_RANGE = (0.05, 2.0)
CAPACITY = 2.0
SESSIONS = m4.SESSIONS
FIRST, FINAL = SESSIONS[0], SESSIONS[-1]
PRE = FIRST - 1
V7_DAY = FIRST + 28
POST, SIX, TWELVE = FINAL + 28, FINAL + 180, FINAL + 365
DAYS = TWELVE
SNAPS = (30, PRE, V7_DAY, POST, SIX, TWELVE)
THRESH_L = 1.0
THRESH_EDGE_MM = 0.1
THRESH_SKIP = 0.05
V1_RANGE = m4.V1_RANGE
V4_FRACTION = 0.5
V6_SEEDS = (0, 1, 2, 3)
V6_SKIP = 0.05
M4_FILES = ("spot_model_m4_sweep.csv", "spot_model_m4_tx1_sweep.csv")
PROVISIONAL = "provisional thresholds (plan 11.4): 0.1 mm edge, 1.0 L*, 0.05 skip; replace with phantom SDC"


def draws_and_lambdas():
    rng = np.random.default_rng(SEED)
    draws = m4.lhs(N_DRAWS, m4.RANGES, rng)
    lam = m4.lhs(N_DRAWS, {"lambda_D": ("log",) + LAMBDA_RANGE}, np.random.default_rng(LAMBDA_SEED))["lambda_D"]
    return draws, lam


def selected_sets(data_dir):
    sel = set()
    for name in M4_FILES:
        with open(Path(data_dir) / name, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["accepted"] == "True":
                    sel.add((int(r["draw"]), r["kind"]))
    return sorted(sel)


def grid_params(wm_p, lam, tx_rates):
    p = dict(gm.default_params("healthy"))
    p.update({k: wm_p[k] for k in sm.PARAMS})
    p.update(lambda_D=float(lam), tx_site_capacity=CAPACITY, tx_rates=float(tx_rates))
    return p


def safe(f, *a):
    try:
        return float(f(*a))
    except (ValueError, ZeroDivisionError):
        return float("nan")


def live(series):
    return np.asarray(series["active"] + series["hypoactive"] + series["senescent"], dtype=float)


def evaluate(r):
    d = r["params"]["d_spot"]
    dL = {t: gm.measure_dL(gm.render(r, t), d) for t in SNAPS}
    img_pre = gm.render(r, PRE)
    img_pre0 = gm.render(r, PRE, blur_sd_mm=0.0)
    ls = live(r["spot"]) / r["n_sites"]["spot"]
    lr = live(r["ring"]) / r["n_sites"]["ring"]
    hyp_sen = r["spot"]["hypoactive"] + r["spot"]["senescent"]
    first_imp = int(np.argmax(hyp_sen > 0)) if np.any(hyp_sen > 0) else -1
    gone = r["spot"]["gone"]
    first_lost = int(np.argmax(gone > 0)) if np.any(gone > 0) else -1
    ew = safe(gm.edge_width, img_pre, d)
    base = dL[PRE]
    out = {
        "density_ratio_pre": ls[PRE] / lr[PRE],
        "dL_day30": dL[30],
        "baseline_dL": base,
        "dL_first_plus_28d": dL[V7_DAY],
        "dL_post_final_28d": dL[POST],
        "dL_6m_after_final": dL[SIX],
        "dL_12m_after_final": dL[TWELVE],
        "fade_6m_L": dL[SIX] - dL[POST],
        "fade_12m_L": dL[TWELVE] - dL[POST],
        "rho_6m": dL[SIX] / base if abs(base) >= gm.ZERO_BASELINE else float("nan"),
        "edge_width_mm": ew,
        "edge_midpoint_mm": safe(gm.edge_midpoint, img_pre, d),
        "edge_over_radius": ew / (d / 2),
        "rim_centre_dL": gm.rim_centre_dL(img_pre, d),
        "skip_photo": gm.skip_score(img_pre, d),
        "skip_cell_expected": gm.skip_score(img_pre0, d),
        "overflow_max": float(max(r["transplant_overflow"])),
        "tx_alive_share_6m": r["spot"]["transplanted_alive"][SIX] / max(r["spot"]["transplanted_alive"][FINAL], 1e-12),
    }
    flags = {
        "F_not_in_weeks": bool(dL[30] < THRESH_L),
        "V1_density_ratio": bool(V1_RANGE[0] <= out["density_ratio_pre"] <= V1_RANGE[1]),
        "V2_never_absent": bool(live(r["spot"])[:FIRST].min() >= 1.0),
        "V3_two_stage": bool(first_lost == -1 or first_lost > first_imp),
        "V4_sharp_edge": bool(math.isfinite(ew) and ew <= V4_FRACTION * d / 2),
        "V7_visible_in_weeks": bool(dL[V7_DAY] <= base - THRESH_L),
    }
    out.update(flags)
    out["pass_without_V6"] = all(flags.values())
    return out


def one_set(args):
    draw_i, kind, wm_p, lam = args
    rows = []
    for tx in (0, 1):
        p = grid_params(wm_p, lam, tx)
        r = gm.run(p, days=DAYS, mode="expected", transplant_days=SESSIONS,
                   snapshot_days=SNAPS, fibroblasts="random", fibroblast_seed=draw_i)
        row = {"draw": draw_i, "kind": kind, "tx_rates": tx}
        row.update({k: p[k] for k in gm.PARAMS})
        row.update(evaluate(r))
        rows.append(row)
    return rows


def v6_set(args):
    draw_i, kind, wm_p, lam = args
    p = grid_params(wm_p, lam, 0)          # V6 is read before any transplant
    scores = []
    for s in V6_SEEDS:
        r = gm.run(p, days=PRE, seed=s, mode="stochastic", snapshot_days=(PRE,),
                   fibroblasts="random", fibroblast_seed=draw_i)
        scores.append(gm.skip_score(gm.render(r, PRE, blur_sd_mm=0.0), p["d_spot"]))
    return draw_i, kind, scores


def oat_rows():
    rows = []
    for kind in ("H2", "mixture"):
        for lam in np.geomspace(*LAMBDA_RANGE, 7):
            p = dict(gm.default_params(kind), lambda_D=float(lam))
            r = gm.run(p, days=DAYS, mode="expected", transplant_days=SESSIONS,
                       snapshot_days=SNAPS, fibroblasts="random", fibroblast_seed=0)
            row = {"kind": kind, "varied": "lambda_D", "value": float(lam)}
            row.update(evaluate(r))
            rows.append(row)
    return rows


def write_csv(path, rows, lead_cols):
    meta = {"claim_level": 0, "output_is": "hypothesis",
            "assumptions": ";".join(gm.assumptions()) + "; structural: " + ";".join(gm.STRUCTURAL_ASSUMPTIONS)
            + "; " + m4.NOT_RUN_PARAMS}
    cols = list(lead_cols) + [c for c in rows[0] if c not in lead_cols] + list(meta)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({**{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()}, **meta})


def pct(v):
    v = np.asarray(v, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return "none"
    return " / ".join(f"{x:.3g}" for x in np.percentile(v, [10, 50, 90]))


def label(diff, thr):
    diff = np.asarray(diff, dtype=float)
    gt, lt = np.mean(diff > thr), np.mean(diff < -thr)
    within = 1 - gt - lt
    lab = []
    if max(gt, lt) >= 0.9:
        lab.append("robust")
    if gt > 0 and lt > 0:
        lab.append("fragile")
    if within > 0.5:
        lab.append("untestable")
    return gt, lt, within, "+".join(lab) or "none"


def summarise(rows, n_sets):
    out = []

    def add(item, value, note=""):
        out.append({"item": item, "value": value, "note": note})

    add("sets_run", n_sets, "M4-accepted (draw, kind) under either tx setting")
    checks = ("F_not_in_weeks", "V1_density_ratio", "V2_never_absent", "V3_two_stage",
              "V4_sharp_edge", "V7_visible_in_weeks", "V6_skip_areas")
    stats = ("edge_width_mm", "edge_over_radius", "rim_centre_dL", "skip_photo", "skip_cell_mean",
             "fade_6m_L", "fade_12m_L", "rho_6m", "tx_alive_share_6m", "lambda_D")
    for tx in (0, 1):
        sub = [r for r in rows if r["tx_rates"] == tx]
        for kind in ("H1", "H2", "mixture"):
            rs = [r for r in sub if r["kind"] == kind]
            acc = [r for r in rs if r["accepted"]]
            tag = f"tx{tx}_{kind}"
            add(f"{tag}_run", len(rs))
            add(f"{tag}_accepted", len(acc), f"of {len(rs)}")
            for f in checks:
                add(f"{tag}_pass_{f}", sum(bool(r[f]) for r in rs), f"of {len(rs)}"
                    + ("; V6 run only for sets passing the rest" if f == "V6_skip_areas" else ""))
            add(f"{tag}_V4_pass_lambda_D_gt_0.4", sum(bool(r["V4_sharp_edge"]) for r in rs if r["lambda_D"] > 0.4),
                f"of {sum(1 for r in rs if r['lambda_D'] > 0.4)} with lambda_D > 0.4 mm")
            if acc:
                for q in stats:
                    add(f"{tag}_{q}_p10_p50_p90", pct([r[q] for r in acc]), "accepted sets")
                add(f"{tag}_share_fading_gt_1L_at_6m", f"{np.mean([r['fade_6m_L'] > THRESH_L for r in acc]):.3f}",
                    "accepted sets; " + PROVISIONAL)
                add(f"{tag}_max_overflow", f"{max(r['overflow_max'] for r in acc):.3g}", "cells, accepted sets")
                add(f"{tag}_max_lambda_D_accepted", f"{max(r['lambda_D'] for r in acc):.3g}", "mm")
        # pairs
        by = {}
        for r in sub:
            by.setdefault(r["draw"], {})[r["kind"]] = r
        pairs = [d for d in by.values() if "H1" in d and "H2" in d and d["H1"]["accepted"] and d["H2"]["accepted"]]
        add(f"tx{tx}_pairs_both_accepted", len(pairs))
        for q, thr in (("edge_width_mm", THRESH_EDGE_MM), ("rim_centre_dL", THRESH_L),
                       ("skip_photo", THRESH_SKIP), ("fade_6m_L", THRESH_L)):
            if pairs:
                diff = [d["H2"][q] - d["H1"][q] for d in pairs]
                gt, lt, within, lab = label(diff, thr)
                add(f"tx{tx}_pairs_{q}_H2_minus_H1_p10_p50_p90", pct(diff))
                add(f"tx{tx}_pairs_{q}_label", lab,
                    f"H2>H1 by > thr {gt:.3f}; H1>H2 {lt:.3f}; within {within:.3f}; " + PROVISIONAL)
        # distribution comparison, accepted sets of each explanation
        h1 = [r for r in sub if r["kind"] == "H1" and r["accepted"]]
        h2 = [r for r in sub if r["kind"] == "H2" and r["accepted"]]
        if h1 and h2:
            for q, thr in (("edge_width_mm", THRESH_EDGE_MM), ("rim_centre_dL", THRESH_L),
                           ("skip_photo", THRESH_SKIP), ("fade_6m_L", THRESH_L)):
                gap = np.median([r[q] for r in h2]) - np.median([r[q] for r in h1])
                add(f"tx{tx}_median_gap_H2_minus_H1_{q}", f"{gap:.3g}",
                    f"beyond provisional threshold {thr}: {abs(gap) > thr}; " + PROVISIONAL)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None, help="first N sets only (smoke test; not for results)")
    args = ap.parse_args()
    out = Path(args.out)
    t0 = time.time()
    draws, lam = draws_and_lambdas()
    sets = selected_sets(out)
    if args.limit:
        sets = sets[: args.limit]
    jobs = []
    for i, kind in sets:
        draw = {k: float(v[i]) for k, v in draws.items()}
        _, kinds = m4.build_sets(draw, 0.0)
        jobs.append((i, kind, kinds[kind], float(lam[i])))
    with Pool(args.workers) as pool:
        rows = [r for rs in pool.imap(one_set, jobs, chunksize=1) for r in rs]
        print(f"expected runs done: {len(rows)} rows, {time.time() - t0:.0f} s", flush=True)
        need = sorted({(r["draw"], r["kind"]) for r in rows if r["pass_without_V6"]})
        v6_jobs = [j for j in jobs if (j[0], j[1]) in need]
        v6 = {(i, k): s for i, k, s in pool.imap(v6_set, v6_jobs, chunksize=1)}
    for r in rows:
        s = v6.get((r["draw"], r["kind"]))
        r["V6_seed_scores"] = ";".join(f"{x:.4g}" for x in s) if s else "not run"
        r["skip_cell_mean"] = float(np.mean(s)) if s else float("nan")
        r["V6_skip_areas"] = bool(s) and sum(x >= V6_SKIP for x in s) >= len(s) / 2
        r["accepted"] = bool(r["pass_without_V6"] and r["V6_skip_areas"])
    print(f"V6 runs done: {len(v6)} sets, {time.time() - t0:.0f} s", flush=True)
    write_csv(out / "spot_model_m6_sets.csv", rows, ["draw", "kind", "tx_rates", "accepted"])
    oat = oat_rows()
    write_csv(out / "spot_model_m6_oat.csv", oat, ["kind", "varied", "value"])
    summary = summarise(rows, len(sets))
    summary.append({"item": "seed", "value": SEED, "note": "M4 Latin hypercube; lambda_D hypercube seed [20261128, 6]"})
    summary.append({"item": "tx_site_capacity", "value": CAPACITY, "note": "register base runs"})
    summary.append({"item": "run_time_s", "value": f"{time.time() - t0:.0f}", "note": f"{args.workers} workers"})
    write_csv(out / "spot_model_m6_summary.csv", summary, ["item", "value", "note"])
    for r in summary:
        print(f"{r['item']}: {r['value']}  {r['note']}")


if __name__ == "__main__":
    main()
