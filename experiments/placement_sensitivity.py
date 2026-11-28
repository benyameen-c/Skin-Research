#!/usr/bin/env python3
"""How much the placement result depends on the test author's two READING choices.

SIMULATION ONLY. Synthetic disks, synthetic texture, no images read.

1. Sticker centring SD (default 0.1 mm). The 2 mm comparison is rerun with
   several SDs on the same captures (same seed; the SD changes only the size of
   the sticker draws), and the plan's section 4 target is applied to each.
2. "Below the noise floor" (plan 4.4). Read from the main results CSV: for each
   placement with the inner disc at 2 mm on mottled skin, the largest
   |mean false change| at 0 < shift <= 0.3 mm is compared with several
   possible floors.

Run (after placement_sim.py has written data/placement_sim_results.csv):
  python3 experiments/placement_sensitivity.py --out data
Writes data/placement_sim_target.csv, data/placement_sim_sticker_sensitivity.csv
and data/placement_sim_noise_floor_sensitivity.csv.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import placement_sim as ps  # noqa: E402

STICKER_SDS = (0.0, 0.05, 0.1, 0.15, 0.2, 0.3)
KEYS = ("false_change_ok", "sd_ok", "sensitivity_ok", "within_noise_to_0_3mm", "passes")


def read_rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def pick(rows, **kw):
    out = [r for r in rows if all(str(r[k]) == str(v) for k, v in kw.items())]
    if len(out) != 1:
        raise ValueError(f"expected one row for {kw}, found {len(out)}")
    return out[0]


def f(v):
    return None if v in (None, "") else float(v)


def r4(v):
    return "" if v is None else f"{v:.4f}"


def target_table(rows, diameters):
    """evaluate_target at each diameter (the plan's target is stated at 2 mm)."""
    out = []
    for d in diameters:
        res = ps.evaluate_target(rows, diameter_mm=d)
        for p in ps.PLACEMENTS:
            for rg in ps.REGIONS:
                e = res[(p, rg)]
                un = pick(rows, scenario="unchanged", background="mottled",
                          diameter_mm=f"{d:.4f}", shift_mm="0.5000", placement=p, region=rg)
                gf = pick(rows, scenario="genuine_fading", background="mottled",
                          diameter_mm=f"{d:.4f}", shift_mm="0.5000", placement=p, region=rg)
                out.append({
                    "diameter_mm": d, "shift_mm": 0.5, "background": "mottled",
                    "placement": p, "region": rg,
                    "unchanged_mean_change_pct": un["mean_change_pct"],
                    "unchanged_sd_change_pct": un["sd_change_pct"],
                    "unchanged_mean_change_L": un["mean_change_L"],
                    "unchanged_sd_change_L": un["sd_change_L"],
                    "fading_true_change_pct": gf["true_change_pct"],
                    "fading_mean_change_pct": gf["mean_change_pct"],
                    "rejected_of_trials": f"{un['rejected']}/{un['trials']}",
                    **{k: "" if e[k] is None else e[k] for k in KEYS},
                    "area_ok": res["area_ok"],
                })
    return out


def sticker_table(trials, seed, px_per_mm):
    out = []
    for sd in STICKER_SDS:
        rows = ps.run(seed=seed, trials=trials, px_per_mm=px_per_mm, diameters=(2.0,),
                      scenarios=("unchanged", "genuine_fading", "shrinking"),
                      sticker_sd_mm=sd)
        res = ps.evaluate_target(rows)
        for rg in ps.REGIONS:
            e = res[("sticker", rg)]
            un = [r for r in rows if r["scenario"] == "unchanged" and r["background"] == "mottled"
                  and r["shift_mm"] == 0.5 and r["placement"] == "sticker" and r["region"] == rg][0]
            gf = [r for r in rows if r["scenario"] == "genuine_fading" and r["background"] == "mottled"
                  and r["shift_mm"] == 0.5 and r["placement"] == "sticker" and r["region"] == rg][0]
            out.append({
                "sticker_sd_mm": sd, "diameter_mm": 2.0, "shift_mm": 0.5, "background": "mottled",
                "region": rg,
                "unchanged_mean_change_pct": r4(un["mean_change_pct"]),
                "unchanged_sd_change_pct": r4(un["sd_change_pct"]),
                "fading_true_change_pct": r4(gf["true_change_pct"]),
                "fading_mean_change_pct": r4(gf["mean_change_pct"]),
                "mean_centre_error_mm": r4(un["mean_centre_error_mm"]),
                **{k: "" if e[k] is None else e[k] for k in KEYS},
                "trials": trials, "seed": seed,
            })
    return out


def noise_floor_table(rows, trials):
    out = []
    for p in ps.PLACEMENTS:
        sel = [r for r in rows if r["scenario"] == "unchanged" and r["background"] == "mottled"
               and float(r["diameter_mm"]) == 2.0 and r["placement"] == p
               and r["region"] == "inner_disc"]
        sd0 = f([r for r in sel if float(r["shift_mm"]) == 0.0][0]["sd_change_pct"])
        near = [r for r in sel if 0 < float(r["shift_mm"]) <= 0.3]
        means = [f(r["mean_change_pct"]) for r in near]
        if sd0 is None or any(m is None for m in means):
            worst, at = None, ""
        else:
            i = max(range(len(means)), key=lambda k: abs(means[k]))
            worst, at = abs(means[i]), near[i]["shift_mm"]
        floors = {
            "A_sd_at_zero_shift (test author's reading)": sd0,
            "B_standard_error_sd0_over_sqrt_trials": None if sd0 is None else sd0 / math.sqrt(trials),
            "C_sdc_1.96_sqrt2_sd0 (plan 2.2 form)": None if sd0 is None else 1.96 * math.sqrt(2) * sd0,
            "D_plan_false_change_limit_2pct": 2.0,
        }
        for name, floor in floors.items():
            out.append({
                "placement": p, "region": "inner_disc", "diameter_mm": 2.0,
                "background": "mottled", "shift_range_mm": "0 < shift <= 0.3",
                "worst_abs_mean_change_pct": r4(worst), "worst_at_shift_mm": at,
                "floor_name": name, "floor_pct": r4(floor),
                "below_floor": "" if worst is None or floor is None else worst <= floor,
            })
    return out


def write(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="data")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--skip-sticker", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    rows = read_rows(out / "placement_sim_results.csv")
    trials = int(rows[0]["trials"])
    diameters = sorted({float(r["diameter_mm"]) for r in rows})
    write(out / "placement_sim_target.csv", target_table(rows, diameters))
    write(out / "placement_sim_noise_floor_sensitivity.csv", noise_floor_table(rows, trials))
    if not a.skip_sticker:
        write(out / "placement_sim_sticker_sensitivity.csv",
              sticker_table(a.trials, a.seed, a.px_per_mm))


if __name__ == "__main__":
    main()
