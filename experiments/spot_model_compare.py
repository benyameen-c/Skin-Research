#!/usr/bin/env python3
"""Compare the two explanations of an IGH spot in the well-mixed model (M4 runs).

SIMULATION ONLY. Every number this writes is CLAIM LEVEL 0, A HYPOTHESIS: it
follows from the model's rules and from assumed rates (plan 10.4). It is not
evidence, it says nothing about whether any treatment works or lasts, and
nothing here enters data/evidence.csv.

What it runs (content/spot-model-plan.md section 7, the parts that apply to a
model with no space). Everything below was fixed in this file BEFORE the first
run; no range or threshold was changed after seeing output.

Timeline (ASSUMPTION): the spot forms from day 0. Two transplant sessions on
day 7300 (20 years) and day 7330; the FINAL treatment is day 7330, and every
follow-up is counted from it (CLAUDE.md rule 2): settled readout at final + 28
days, six-month readout at final + 180, twelve-month readout at final + 365.
The surrounding skin ("ring") is a "healthy" run with the same shared rates.

Detection threshold: 1.0 L*. This is the project's own target for the
measurement tool on a 2 mm spot (content/measurement-tool-plan.md), NOT a
measured smallest detectable change. Results are also given as raw numbers so
another threshold can be applied.

Acceptance (pattern validation, plan 7.1). A parameter set is accepted only if:
  F   not in weeks:  dL*(day 30) < 1.0 L*                          (plan 7.1)
  V1  live spot / ring melanocytes on the day before the first session in
      [0.15, 0.40]  (plan's inferred spread around 55.25 vs 220, PMID 2508572)
  V2  at least 1 live melanocyte in the spot on every day           (PMID 6183861)
  V3  hypoactive cells appear before any cell is lost (holds by construction;
      checked anyway)                                              (PMID 7377803)
  V7  dL*(first session + 28 days) at least 1.0 L* below the baseline dL*
      (visible within weeks; PMID 3908515)
  V4, V5, V6 need space (edge, size, skip areas): not testable here, M5.
  V8 (mouse graft) is a known misfit, not scored.

Sweep (plan 7.2 steps 2, 3, 5). N Latin-hypercube draws, seed fixed. Each draw
gives shared values (k_sen, k_loss, k_div, T_K, N_tx, s_tx, d_spot) used by
every explanation, plus H1's own (k_int, a_int, k_tr) and H2's own (f_sen,
p_D, mu_D, k_derm). The mixture uses both own sets, with k_int and k_derm
halved. A pair (H1, H2) from the same draw is compared only when both are
accepted.

Ranges (all ASSUMPTION; register wording in brackets; log = log-uniform):
  k_int   log 1e-5 .. 1e-3 per day        [years-scale]
  a_int   0 .. 2                          [flat to steep]
  k_tr    0.1 .. 1                        [1 healthy; 0.1 to 1 in spot]
  k_sen   log 1/1825 .. 1/30 per day      [months to years]
  k_loss  log 1/1825 .. 1/30 per day      [months to years]
  k_div   log 1e-5 .. 1e-2 per day        [near zero to modest]
  T_K     14 .. 56 days                   [weeks]
  f_sen   0.05 .. 0.9                     [0 to high; 0 is healthy skin]
  p_D     log 0.1 .. 10                   [swept]
  mu_D    log 0.1 .. 10 per day           [swept]
  k_derm  log 1e-5 .. 1e-2                [0 (H1) to dominant (H2)]
  N_tx    20 .. 220 cells per mm2         [up to 220]
  s_tx    0.1 .. 0.9                      [0.1 to 0.9]
  d_spot  2 .. 5 mm                       QUOTED range, PMID 3805391
  n_M_ring 220 per mm2                    QUOTED, PMID 2508572

Per prediction (plan 7.2 step 3): share of accepted pairs in which H2's fade
exceeds H1's by more than 1.0 L*, the reverse, and within 1.0 L*. Called
"robust" if one direction holds in at least 90% of accepted pairs, "fragile"
if both directions occur, "untestable" if the difference is within 1.0 L* in
most pairs. (Categories can overlap; all three shares are printed.)

Also: one-at-a-time sweeps at each explanation's defaults (plan 7.2 step 1),
and 20 stochastic seeds at the defaults to show chance variation.

Transplanted-cell rate setting (added 2026-11-28 AFTER the first results were
seen; prediction row P4b). --tx-rates 0 or 1 sets tx_rates in every parameter
set. Under 1 the donor rates k_int_tx, a_int_tx, k_tr_tx are FIXED at the
healthy-skin defaults (0, 0, 1) and not swept; every range above is unchanged,
and the draws are the same (same seed, same order).

Run:  python3 experiments/spot_model_compare.py --out data [--n 4000] [--tx-rates 0|1]
Writes data/spot_model_m4_{sweep,oat,seeds,summary}.csv for the first run
(tx_rates 0, before the setting existed), and with --tx-rates given,
data/spot_model_m4_tx<setting>_{sweep,oat,seeds,summary}.csv.
"""
import argparse
import csv
import math
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import spot_model as sm

SEED = 20261128
SESSIONS = (7300, 7330)
FINAL = SESSIONS[-1]
POST, SIX, TWELVE = FINAL + 28, FINAL + 180, FINAL + 365
DAYS = TWELVE
THRESH_L = 1.0
V1_RANGE = (0.15, 0.40)

SHARED = {
    "k_sen": ("log", 1 / 1825, 1 / 30),
    "k_loss": ("log", 1 / 1825, 1 / 30),
    "k_div": ("log", 1e-5, 1e-2),
    "T_K": ("lin", 14.0, 56.0),
    "N_tx": ("lin", 20.0, 220.0),
    "s_tx": ("lin", 0.1, 0.9),
    "d_spot": ("lin", 2.0, 5.0),
}
OWN_H1 = {
    "k_int": ("log", 1e-5, 1e-3),
    "a_int": ("lin", 0.0, 2.0),
    "k_tr": ("lin", 0.1, 1.0),
}
OWN_H2 = {
    "f_sen": ("lin", 0.05, 0.9),
    "p_D": ("log", 0.1, 10.0),
    "mu_D": ("log", 0.1, 10.0),
    "k_derm": ("log", 1e-5, 1e-2),
}
RANGES = {**SHARED, **OWN_H1, **OWN_H2}
TX_RATES = 0.0   # set by --tx-rates; applied to every parameter set below
NOT_RUN_PARAMS = "map_L (L* = 50 + 30 exp(-m)); session days 7300 and 7330"


def lhs(n, ranges, rng):
    """Latin hypercube: one stratum per draw per dimension, shuffled."""
    out = {}
    for k, (scale, lo, hi) in ranges.items():
        u = (rng.permutation(n) + rng.random(n)) / n
        if scale == "log":
            out[k] = np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo)))
        else:
            out[k] = lo + u * (hi - lo)
    return out


def build_sets(draw, tx_rates):
    """Parameter sets for one draw: ring (healthy), H1, H2, mixture."""
    shared = {k: draw[k] for k in SHARED}
    ring = dict(sm.default_params("healthy"), **shared, tx_rates=tx_rates)
    h1 = dict(ring, **{k: draw[k] for k in OWN_H1})
    h2 = dict(ring, **{k: draw[k] for k in OWN_H2})
    mix = dict(ring, **{k: draw[k] for k in OWN_H1}, **{k: draw[k] for k in OWN_H2})
    mix["k_int"] = draw["k_int"] / 2
    mix["k_derm"] = draw["k_derm"] / 2
    return ring, {"H1": h1, "H2": h2, "mixture": mix}


def live(r):
    return np.asarray(r["active"] + r["hypoactive"] + r["senescent"], dtype=float)


def evaluate(spot, ring):
    """Readouts and acceptance flags for one spot run against its ring run."""
    dL = sm.lightness_contrast(spot, ring)
    ro = sm.six_month_readout(spot, ring)
    base = ro["baseline_dL"]
    ls, lr = live(spot), live(ring)
    pre = SESSIONS[0] - 1
    hyp_sen = spot["hypoactive"] + spot["senescent"]
    first_imp = int(np.argmax(hyp_sen > 0)) if np.any(hyp_sen > 0) else -1
    first_lost = int(np.argmax(spot["gone"] > 0)) if np.any(spot["gone"] > 0) else -1
    flags = {
        "F_not_in_weeks": bool(dL[30] < THRESH_L),
        "V1_density_ratio": bool(V1_RANGE[0] <= ls[pre] / lr[pre] <= V1_RANGE[1]),
        "V2_never_absent": bool(ls[:SESSIONS[0]].min() >= 1.0),
        "V3_two_stage": bool(first_lost == -1 or first_lost > first_imp),
        "V7_visible_in_weeks": bool(dL[SESSIONS[0] + 28] <= base - THRESH_L),
    }
    live_pre = ls[pre]
    out = {
        "density_ratio_pre": ls[pre] / lr[pre],
        "dL_day30": dL[30],
        "baseline_dL": base,
        "dL_post_final_28d": dL[POST],
        "dL_6m_after_final": ro["dL_at_6_months"],
        "dL_12m_after_final": dL[TWELVE],
        "rho_post": sm.residual_contrast(base, dL[POST]),
        "rho_6m": ro["rho_at_6_months"],
        "rho_12m": sm.residual_contrast(base, dL[TWELVE]),
        "fade_6m_L": ro["dL_at_6_months"] - dL[POST],
        "fade_12m_L": dL[TWELVE] - dL[POST],
        "tx_alive_share_6m": spot["transplanted_alive"][SIX] / max(spot["transplanted_alive"][FINAL], 1e-12),
        "share_senescent_pre": spot["senescent"][pre] / live_pre if live_pre > 0 else float("nan"),
        "share_hypoactive_pre": spot["hypoactive"][pre] / live_pre if live_pre > 0 else float("nan"),
    }
    out.update(flags)
    out["accepted"] = all(flags.values())
    return out


def one_draw(args):
    i, draw, tx_rates = args
    ring_p, sets = build_sets(draw, tx_rates)
    ring = sm.run(ring_p, days=DAYS, mode="expected")
    rows = []
    for kind, p in sets.items():
        spot = sm.run(p, days=DAYS, mode="expected", transplant_days=SESSIONS)
        row = {"draw": i, "kind": kind}
        row.update({k: p[k] for k in sm.PARAMS})
        row.update(evaluate(spot, ring))
        rows.append(row)
    return rows


def oat_rows():
    """One parameter at a time across its range, the rest at the kind's defaults."""
    rows = []
    ring_cache = {}
    for kind in ("H1", "H2", "mixture"):
        for key, (scale, lo, hi) in RANGES.items():
            if kind == "H1" and key in OWN_H2:
                continue
            if kind == "H2" and key in OWN_H1:
                continue
            grid = (np.geomspace(lo, hi, 7) if scale == "log" else np.linspace(lo, hi, 7))
            for v in grid:
                p = dict(sm.default_params(kind), **{key: float(v)}, tx_rates=TX_RATES)
                ring_p = dict(sm.default_params("healthy"), **{k: p[k] for k in SHARED})
                rk = tuple(sorted(ring_p.items()))
                if rk not in ring_cache:
                    ring_cache[rk] = sm.run(ring_p, days=DAYS, mode="expected")
                spot = sm.run(p, days=DAYS, mode="expected", transplant_days=SESSIONS)
                row = {"kind": kind, "varied": key, "value": float(v)}
                row.update(evaluate(spot, ring_cache[rk]))
                rows.append(row)
    return rows


def seed_rows(n_seeds=20):
    rows = []
    for kind in ("H1", "H2", "mixture"):
        for seed in range(n_seeds):
            ring = sm.run(dict(sm.default_params("healthy"), tx_rates=TX_RATES), days=DAYS, seed=seed)
            spot = sm.run(dict(sm.default_params(kind), tx_rates=TX_RATES), days=DAYS, seed=seed,
                          transplant_days=SESSIONS)
            row = {"kind": kind, "seed": seed}
            row.update(evaluate(spot, ring))
            rows.append(row)
    return rows


def write_csv(path, rows, lead_cols):
    meta = {"claim_level": 0, "output_is": "hypothesis",
            "assumptions": ";".join(sm.assumptions()) + "; " + NOT_RUN_PARAMS}
    cols = list(lead_cols) + [c for c in rows[0] if c not in lead_cols] + list(meta)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({**{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()}, **meta})


def summarise(sweep):
    by = {}
    for r in sweep:
        by.setdefault(r["draw"], {})[r["kind"]] = r
    out = []

    def add(item, value, note=""):
        out.append({"item": item, "value": value, "note": note})

    n = len(by)
    add("draws", n)
    for kind in ("H1", "H2", "mixture"):
        rs = [d[kind] for d in by.values()]
        acc = [r for r in rs if r["accepted"]]
        add(f"{kind}_accepted", len(acc), f"of {n}")
        for f in ("F_not_in_weeks", "V1_density_ratio", "V2_never_absent", "V3_two_stage", "V7_visible_in_weeks"):
            add(f"{kind}_pass_{f}", sum(r[f] for r in rs), f"of {n}")
        if acc:
            for q in ("fade_6m_L", "rho_post", "rho_6m", "rho_12m", "tx_alive_share_6m", "share_senescent_pre"):
                v = np.array([r[q] for r in acc], dtype=float)
                add(f"{kind}_{q}_p10_p50_p90",
                    " / ".join(f"{x:.3g}" for x in np.percentile(v, [10, 50, 90])),
                    "accepted sets")
            fades = np.array([r["fade_6m_L"] for r in acc])
            add(f"{kind}_share_fading_gt_1L_at_6m", f"{np.mean(fades > THRESH_L):.3f}",
                "share of accepted sets where dL* at 6 months after the final session is more than 1.0 L* above dL* 28 days after it")
    pairs = [d for d in by.values() if d["H1"]["accepted"] and d["H2"]["accepted"]]
    add("pairs_both_accepted", len(pairs), f"of {n}")
    if pairs:
        diff = np.array([d["H2"]["fade_6m_L"] - d["H1"]["fade_6m_L"] for d in pairs])
        gt, lt = np.mean(diff > THRESH_L), np.mean(diff < -THRESH_L)
        within = 1 - gt - lt
        add("P4_pairs_H2_fades_more_by_gt_1L", f"{gt:.3f}")
        add("P4_pairs_H1_fades_more_by_gt_1L", f"{lt:.3f}")
        add("P4_pairs_within_1L", f"{within:.3f}")
        add("P4_diff_H2_minus_H1_fade_p10_p50_p90",
            " / ".join(f"{x:.3g}" for x in np.percentile(diff, [10, 50, 90])), "L*")
        label = []
        if max(gt, lt) >= 0.9:
            label.append("robust")
        if gt > 0 and lt > 0:
            label.append("fragile")
        if within > 0.5:
            label.append("untestable")
        add("P4_label_plan_7.2", "+".join(label) or "none", "robust >=90% one way; fragile both ways occur; untestable within 1 L* in most pairs")
        # does the answer track a_int (H1's age clock)?
        a = np.array([d["H1"]["a_int"] for d in pairs])
        for lo, hi in ((0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.01)):
            m = (a >= lo) & (a < hi)
            if m.any():
                add(f"P4_diff_median_a_int_{lo}_to_{min(hi, 2.0)}",
                    f"{np.median(diff[m]):.3g}", f"{int(m.sum())} pairs; L*")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tx-rates", type=int, choices=(0, 1), default=None)
    args = ap.parse_args()
    out = Path(args.out)
    global TX_RATES
    prefix = "spot_model_m4"
    if args.tx_rates is not None:
        TX_RATES = float(args.tx_rates)
        prefix = f"spot_model_m4_tx{args.tx_rates}"
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    draws = lhs(args.n, RANGES, rng)
    jobs = [(i, {k: float(v[i]) for k, v in draws.items()}, TX_RATES) for i in range(args.n)]
    with Pool(args.workers) as pool:
        sweep = [r for rows in pool.map(one_draw, jobs, chunksize=10) for r in rows]
    write_csv(out / f"{prefix}_sweep.csv", sweep, ["draw", "kind", "accepted"])
    oat = oat_rows()
    write_csv(out / f"{prefix}_oat.csv", oat, ["kind", "varied", "value", "accepted"])
    seeds = seed_rows()
    write_csv(out / f"{prefix}_seeds.csv", seeds, ["kind", "seed", "accepted"])
    summary = summarise(sweep)
    for kind in ("H1", "H2", "mixture"):
        rs = [r for r in seeds if r["kind"] == kind]
        f = np.array([r["fade_6m_L"] for r in rs])
        summary.append({"item": f"{kind}_defaults_20_seeds_fade_6m_L_min_median_max",
                        "value": f"{f.min():.3g} / {np.median(f):.3g} / {f.max():.3g}",
                        "note": "stochastic, d_spot 3 mm"})
    summary.append({"item": "seed", "value": SEED, "note": "Latin hypercube"})
    summary.append({"item": "tx_rates", "value": TX_RATES,
                    "note": "1 = donor cells carry healthy-skin intrinsic rates (k_int_tx 0, a_int_tx 0, k_tr_tx 1)"})
    summary.append({"item": "run_time_s", "value": f"{time.time() - t0:.0f}", "note": f"{args.workers} workers"})
    write_csv(out / f"{prefix}_summary.csv", summary, ["item", "value", "note"])
    for r in summary:
        print(f"{r['item']}: {r['value']}  {r['note']}")


if __name__ == "__main__":
    main()
