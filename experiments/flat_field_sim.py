#!/usr/bin/env python3
"""Blank-card (flat-field) correction for the registration stress simulation.

SIMULATION ONLY, CERTAINTY LEVEL 0. Synthetic disks, synthetic texture,
synthetic straight "hairs", a synthetic uniform card. No patient data, and no
image file is ever read. It tests the measuring method, not any treatment. Its
output is a hypothesis about the method, not evidence about real skin, real
cameras or any treatment.

Round two (experiments/registration_stress_sim.py, content/experiments.md
section 6) found that light falling off towards the field edges breaks every
placement from 10 %. This module adds one choice to every measurement of round
two, `correction`: "none" (round two unchanged, row for row) or "blank_card":
each session photographs a uniform card of known reflectance CARD_FRAMES times
under its own light, the mean card frame (optionally smoothed) divided by the
card's reflectance is the gain field, and every capture of that session is
divided by it before hair detection, placement and measurement.

The contract is the docstring of experiments/tests/test_flat_field_sim.py,
written before this file and implemented here unchanged.

ASSUMPTIONS taken from the contract (the test author's READINGs, Ben can change
them): the card's reflectance is exactly known; 3 card frames per session (as
many as skin captures, plan 2.2); the card sits where the skin is and sees
exactly the light the skin sees (no change of distance or angle between the
card shot and the skin shot); light is smooth and multiplicative, as round two
models it.

Builder's choices (the tests leave them open):
  CARD_RGB        0.8 on every channel: a white card. A brighter card has less
                  relative noise per pixel than an 18 % grey card under the same
                  capture noise. ASSUMPTION, not a measured card.
  CARD_SMOOTH_MM  0.2 mm Gaussian SD on the mean card frame before it becomes
                  the gain. The lighting fields modelled change over
                  millimetres, so 0.2 mm removes pixel noise from the gain while
                  shifting a pure fall-off field by a near-constant
                  vignetting x 2 s^2 / (W / 2)^2 (under 0.1 % here). At the
                  field border the frame is extended by odd reflection, which
                  keeps a linear ramp exactly linear.
  Card noise      drawn from its own random stream, seeded from the run's seed
                  and never from round two's stream, so the "none" rows are
                  round two's rows exactly. Baseline and follow-up cards, and
                  each of their frames, get independent noise.
  rejected_card   a trial whose baseline or follow-up card is refused by
                  flat_field() is refused for every placement, region and mask
                  of the "blank_card" rows, and counted before anything else.

Run:  python3 experiments/flat_field_sim.py --out data   (about 25 min on 4 cores)
Needs: Python 3.9+, numpy. Reuses registration_stress_sim.py by import, unchanged.
"""
import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registration_stress_sim as rs  # noqa: E402
import placement_sim as p1  # noqa: E402
from registration_stress_sim import (  # noqa: E402,F401
    DIAMETERS_MM, DISTURBANCES, HAIR_MASKS, HAIR_WIDTH_MM, INNER_FRACTION, MOTTLE_CORR_MM,
    PLACEMENTS, REGIONS, SCENARIOS, SHIFT_MM, SPOT_TAN_FRACTION, STICKER_SD_MM, CaptureRefused,
    rgb_to_lab)

# ---- constants --------------------------------------------------------------
CORRECTIONS = ("none", "blank_card")
CARD_RGB = (0.8, 0.8, 0.8)          # builder's choice: a white card (ASSUMPTION)
CARD_FRAMES = 3                     # READING (test author): plan 2.2, k = 3
CARD_SMOOTH_MM = 0.2                # builder's choice
FF_DISTURBANCES = ("none", "gradient_5", "gradient_20", "vignetting_10",
                   "vignetting_20", "combined")
CARD_STREAM = 4243                  # key of the card noise stream (never round two's)


# ---- card and correction -------------------------------------------------------
def _card_capture(diameter_mm, *, px_per_mm, gradient, gradient_dir_deg, vignetting,
                  blur_sd_mm, noise_sd, noise_rng, card_rgb):
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    n = rs.field_size(diameter_mm, px_per_mm)
    scene = np.ones((n, n, 3)) * np.asarray(card_rgb, float)
    return rs._capture(scene, diameter_mm, px_per_mm=px_per_mm, hair_count=0,
                       hair_width_mm=HAIR_WIDTH_MM, hair_seed=0, gradient=gradient,
                       gradient_dir_deg=gradient_dir_deg, vignetting=vignetting,
                       blur_sd_mm=blur_sd_mm, noise_sd=noise_sd, noise_rng=noise_rng)


def render_card(diameter_mm, *, px_per_mm=20, gradient=0.0, gradient_dir_deg=0.0,
                vignetting=0.0, blur_sd_mm=0.0, noise_sd=0.0, seed=0, card_rgb=CARD_RGB):
    """A photograph of the uniform card under round two's lighting, with
    render()'s blur and noise. Linear RGB (n, n, 3)."""
    return _card_capture(diameter_mm, px_per_mm=px_per_mm, gradient=gradient,
                         gradient_dir_deg=gradient_dir_deg, vignetting=vignetting,
                         blur_sd_mm=blur_sd_mm, noise_sd=noise_sd,
                         noise_rng=np.random.default_rng([seed, CARD_STREAM]), card_rgb=card_rgb)


def _smooth(img, px_per_mm, sd_mm):
    """Separable Gaussian of SD sd_mm (in mm), kernel truncated at 4 SD and
    normalised; the border is extended by odd reflection."""
    s = sd_mm * px_per_mm
    r = max(1, int(math.ceil(4 * s)))
    t = np.arange(-r, r + 1)
    k = np.exp(-0.5 * (t / s) ** 2)
    k /= k.sum()
    out = np.asarray(img, float)
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode="reflect", reflect_type="odd")
        n = out.shape[axis]
        acc = np.zeros_like(out)
        for i, w in enumerate(k):
            acc += w * np.take(p, np.arange(i, i + n), axis=axis)
        out = acc
    return out


def flat_field(cards, *, px_per_mm, smooth_mm=CARD_SMOOTH_MM, card_rgb=CARD_RGB):
    """Gain G = smooth(mean of card frames) / card_rgb, per channel. Refused
    (ValueError) for no frames, frames of different shapes, or any G that is
    not finite or not positive (a dark or missing card)."""
    if isinstance(cards, np.ndarray) and cards.ndim == 3:
        cards = [cards]
    frames = [np.asarray(c, float) for c in cards]
    if not frames:
        raise ValueError("no card frames")
    shape = frames[0].shape
    if len(shape) != 3 or shape[2] != 3 or any(f.shape != shape for f in frames):
        raise ValueError("card frames must all be (n, n, 3) arrays of one shape")
    mean = np.mean(frames, axis=0)
    if smooth_mm > 0:
        if not np.all(np.isfinite(mean)):
            raise ValueError("card frame has non-finite values")
        mean = _smooth(mean, px_per_mm, smooth_mm)
    g = mean / np.asarray(card_rgb, float)
    if not np.all(np.isfinite(g)) or np.any(g <= 0):
        raise ValueError("card refused: gain not finite or not positive")
    return g


def correct(img, gain):
    """The capture divided by its own session's gain."""
    img, gain = np.asarray(img, float), np.asarray(gain, float)
    if img.shape != gain.shape:
        raise ValueError(f"capture {img.shape} and gain {gain.shape} differ in shape")
    return img / gain


# ---- experiment ----------------------------------------------------------------
_RENDER_KEYS = rs._RENDER_KEYS


def _new_acc():
    return {"err": [], "chg": [], "dL": [], "rdL": [], "cerr": [], "rex": [], "truth": [],
            "tring": [], "base": [], "rp": 0, "rm": 0, "rc": 0}


def _measure_pair(acc, key_of, base, foll, d, px_per_mm, outer, sh, truth, st_est):
    """Round two's placement and measurement of one pair of captures, appended
    to acc in round two's order."""
    blab, flab = rgb_to_lab(base), rgb_to_lab(foll)
    pre = rs._reg_base(blab[..., 0], outer & ~rs._reg_hair(base, d, px_per_mm), d, px_per_mm)
    fmask = outer & ~rs._reg_hair(foll, d, px_per_mm)
    est = {"none": (0.0, 0.0), "sticker": st_est}
    for p, model in (("ring_registration", "translation"), ("ring_registration_rigid", "rigid")):
        r = rs._register_prepared(pre, flab[..., 0], fmask, d, px_per_mm, model)
        est[p] = None if r is None else (r["dx"], r["dy"])
    excl = {"none": (None, None),
            "detected": (rs.detect_hair(base, d, px_per_mm), rs.detect_hair(foll, d, px_per_mm))}
    for rg in REGIONS:
        for hm in HAIR_MASKS:
            mb = rs._measure_lab(blab, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION, excl[hm][0])
            for p in PLACEMENTS:
                a = acc[key_of(p, rg, hm)]
                a["truth"].append(truth[rg][0])
                a["tring"].append(truth[rg][1])
                if math.isfinite(mb["L"]):
                    a["base"].append(mb["L"])
                e = est[p]
                if e is None:
                    a["rp"] += 1
                    continue
                mf = rs._measure_lab(flab, d, px_per_mm, rg, e, INNER_FRACTION, excl[hm][1])
                try:
                    rs._check(mb)
                    rs._check(mf)
                except CaptureRefused:
                    a["rm"] += 1
                    continue
                chg = p1._pct(mf["L"], mb["L"])
                a["chg"].append(chg)
                a["err"].append(chg - truth[rg][0])
                a["dL"].append(mf["L"] - mb["L"])
                a["rdL"].append(mf["ring_L"] - mb["ring_L"])
                a["cerr"].append(math.hypot(e[0] - sh[0], e[1] - sh[1]))
                a["rex"].append(0.5 * (mb["ring_excluded"] + mf["ring_excluded"]))


def _session_gain(d, *, px_per_mm, card_frames, card_smooth_mm, card_rgb, blur_sd_mm,
                  noise_sd, card_rng, gradient, gradient_dir_deg, vignetting):
    frames = [_card_capture(d, px_per_mm=px_per_mm, gradient=gradient,
                            gradient_dir_deg=gradient_dir_deg, vignetting=vignetting,
                            blur_sd_mm=blur_sd_mm, noise_sd=noise_sd, noise_rng=card_rng,
                            card_rgb=card_rgb)
              for _ in range(int(card_frames))]
    return flat_field(frames, px_per_mm=px_per_mm, smooth_mm=card_smooth_mm, card_rgb=card_rgb)


def run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, disturbances=FF_DISTURBANCES,
        scenarios=tuple(SCENARIOS), corrections=CORRECTIONS, shift_mm=SHIFT_MM,
        noise_sd=rs.NOISE_SD, mottle_sd=rs.MOTTLE_SD, blur_sd_mm=rs.BLUR_SD_MM,
        sticker_sd_mm=STICKER_SD_MM, card_frames=CARD_FRAMES, card_smooth_mm=CARD_SMOOTH_MM,
        card_rgb=CARD_RGB):
    """One row per correction x scenario x disturbance x diameter x placement x
    region x hair_mask. The skin captures, their random draws and the "none"
    rows are exactly registration_stress_sim.run's; the "blank_card" rows
    measure the same captures after each is divided by its session's gain."""
    for c in corrections:
        if c not in CORRECTIONS:
            raise ValueError(f"unknown correction {c!r}")
    for ds in disturbances:
        if ds not in DISTURBANCES:
            raise ValueError(f"unknown disturbance {ds!r}")
    for sc in scenarios:
        if sc not in SCENARIOS:
            raise ValueError(f"unknown scenario {sc!r}")
    if int(card_frames) < 1:
        raise ValueError("card_frames must be at least 1")
    rng = np.random.default_rng(seed)                       # round two's stream, same draws
    card_rng = np.random.default_rng([seed, CARD_STREAM])   # the cards' own stream
    sh = (float(shift_mm), 0.0)
    combos = [(p, rg, hm) for p in PLACEMENTS for rg in REGIONS for hm in HAIR_MASKS]
    acc = {}
    for c in corrections:
        for sc in scenarios:
            for ds in disturbances:
                for d in diameters:
                    for k in combos:
                        acc[(c, sc, ds, d) + k] = _new_acc()
    card_kw = dict(px_per_mm=px_per_mm, card_frames=card_frames, card_smooth_mm=card_smooth_mm,
                   card_rgb=card_rgb, blur_sd_mm=blur_sd_mm, noise_sd=noise_sd, card_rng=card_rng)
    for _ in range(trials):
        tex_seed = int(rng.integers(2 ** 31))
        for d in diameters:
            _, _, _, outer = rs._reg_setup(d, px_per_mm)
            for ds in disturbances:
                w = {k: DISTURBANCES[ds].get(k, 0) for k in _RENDER_KEYS}
                hb_seed, hf_seed, tan_seed, st_seed = (int(v) for v in rng.integers(2 ** 31, size=4))
                g_dir = float(rng.uniform(0.0, 360.0)) if w["gradient"] else 0.0
                st_est = p1._sticker(sh, sticker_sd_mm, st_seed)
                for sc in scenarios:
                    cs, dsc = SCENARIOS[sc]
                    common = dict(px_per_mm=px_per_mm, background="mottled", mottle_sd=mottle_sd,
                                  mottle_corr_mm=MOTTLE_CORR_MM, seed=tex_seed,
                                  spot_tan_fraction=SPOT_TAN_FRACTION)
                    base_scene = rs._scene(d, contrast_scale=1.0, diameter_scale=1.0,
                                           shift_mm=(0.0, 0.0), tan_dL=0.0, tan_texture_sd=0.0,
                                           tan_seed=0, rotation_deg=0.0, **common)
                    tan = dict(tan_dL=w["tan_dL"], tan_texture_sd=w["tan_texture_sd"], tan_seed=tan_seed)
                    true_follow_scene = rs._scene(d, contrast_scale=cs, diameter_scale=dsc,
                                                  shift_mm=sh, rotation_deg=0.0, **tan, **common)
                    follow_scene = true_follow_scene if w["rotation_deg"] == 0 else \
                        rs._scene(d, contrast_scale=cs, diameter_scale=dsc, shift_mm=sh,
                                  rotation_deg=w["rotation_deg"], **tan, **common)
                    nuis0 = dict(hair_width_mm=HAIR_WIDTH_MM, gradient=0.0, gradient_dir_deg=0.0,
                                 vignetting=0.0, blur_sd_mm=blur_sd_mm)
                    # TRUTH: everything real kept, every capture nuisance dropped, no noise.
                    tb = rs._capture(base_scene, d, px_per_mm=px_per_mm, hair_count=0, hair_seed=0,
                                     noise_sd=0.0, noise_rng=None, **nuis0)
                    tf = rs._capture(true_follow_scene, d, px_per_mm=px_per_mm, hair_count=0,
                                     hair_seed=0, noise_sd=0.0, noise_rng=None, **nuis0)
                    tbl, tfl = rgb_to_lab(tb), rgb_to_lab(tf)
                    truth = {}
                    for rg in REGIONS:
                        mb = rs._measure_lab(tbl, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION, None)
                        mf = rs._measure_lab(tfl, d, px_per_mm, rg, sh, INNER_FRACTION, None)
                        truth[rg] = (p1._pct(mf["L"], mb["L"]), mf["ring_L"] - mb["ring_L"])
                    # SKIN CAPTURES: round two's, from round two's stream, in its order.
                    base = rs._capture(base_scene, d, px_per_mm=px_per_mm, hair_count=w["hair_count"],
                                       hair_seed=hb_seed, noise_sd=noise_sd, noise_rng=rng, **nuis0)
                    foll = rs._capture(follow_scene, d, px_per_mm=px_per_mm,
                                       hair_count=w["hair_count"], hair_width_mm=HAIR_WIDTH_MM,
                                       hair_seed=hf_seed, gradient=w["gradient"],
                                       gradient_dir_deg=g_dir, vignetting=w["vignetting"],
                                       blur_sd_mm=blur_sd_mm, noise_sd=noise_sd, noise_rng=rng)
                    for c in corrections:
                        def key_of(p, rg, hm, c=c, sc=sc, ds=ds, d=d):
                            return (c, sc, ds, d, p, rg, hm)
                        if c == "none":
                            _measure_pair(acc, key_of, base, foll, d, px_per_mm, outer, sh,
                                          truth, st_est)
                            continue
                        # BLANK CARD: each session's own cards under its own light.
                        try:
                            gb = _session_gain(d, gradient=0.0, gradient_dir_deg=0.0,
                                               vignetting=0.0, **card_kw)
                            gf = _session_gain(d, gradient=w["gradient"], gradient_dir_deg=g_dir,
                                               vignetting=w["vignetting"], **card_kw)
                        except ValueError:
                            for k in combos:
                                a = acc[key_of(*k)]
                                a["truth"].append(truth[k[1]][0])
                                a["tring"].append(truth[k[1]][1])
                                a["rc"] += 1
                            continue
                        _measure_pair(acc, key_of, correct(base, gb), correct(foll, gf), d,
                                      px_per_mm, outer, sh, truth, st_est)
    _mean, _sd = rs._mean, rs._sd
    rows = []
    for c in corrections:
        for sc in scenarios:
            for ds in disturbances:
                for d in diameters:
                    for p, rg, hm in combos:
                        a = acc[(c, sc, ds, d, p, rg, hm)]
                        rows.append({
                            "correction": c,
                            "scenario": sc, "disturbance": ds,
                            "family": DISTURBANCES[ds]["family"], "level": DISTURBANCES[ds]["level"],
                            "diameter_mm": float(d), "shift_mm": float(shift_mm),
                            "placement": p, "region": rg, "hair_mask": hm,
                            "true_change_pct": _mean(a["truth"]),
                            "mean_change_pct": _mean(a["chg"]), "sd_change_pct": _sd(a["chg"]),
                            "bias_pct_points": _mean(a["err"]), "sd_error_pct_points": _sd(a["err"]),
                            "mean_abs_error_pct_points": _mean(np.abs(a["err"])) if a["err"] else None,
                            "base_contrast_L": _mean(a["base"]),
                            "mean_change_L": _mean(a["dL"]),
                            "true_ring_dL": _mean(a["tring"]), "mean_ring_dL": _mean(a["rdL"]),
                            "mean_centre_error_mm": _mean(a["cerr"]),
                            "mean_ring_excluded": _mean(a["rex"]),
                            "trials": trials, "rejected": a["rc"] + a["rp"] + a["rm"],
                            "rejected_card": a["rc"],
                            "rejected_placement": a["rp"], "rejected_mask": a["rm"],
                            "noise_sd": noise_sd, "mottle_sd": mottle_sd, "blur_sd_mm": blur_sd_mm,
                            "sticker_sd_mm": sticker_sd_mm, "px_per_mm": px_per_mm,
                            # run settings (the "none" rows do not use them)
                            "card_frames": int(card_frames), "card_smooth_mm": float(card_smooth_mm),
                            "card_rgb": float(card_rgb[0]),
                            "certainty_level": 0,
                        })
    return rows


# ---- target -------------------------------------------------------------------------
def evaluate_flat_field_target(rows, *, diameter_mm=2.0):
    """registration_stress_sim.evaluate_stress_target on each correction's rows
    alone, keyed (correction, disturbance, placement, region, hair_mask)."""
    out = {}
    for c in CORRECTIONS:
        mine = [r for r in rows if r["correction"] == c]
        for k, e in rs.evaluate_stress_target(mine, diameter_mm=diameter_mm).items():
            out[(c,) + k] = e
    return out


def target_rows(evaluation):
    out = []
    for c in CORRECTIONS:
        ev = {k[1:]: e for k, e in evaluation.items() if k[0] == c}
        if not ev:
            continue
        for r in rs.target_rows(ev, rs.breaking_levels(ev)):
            out.append({"correction": c, **r, "certainty_level": 0})
    return out


# ---- output --------------------------------------------------------------------------
def _run_one(kw):
    return run(**kw)


def run_parallel(*, seed, disturbances, jobs=1, **kw):
    """run() once per disturbance, each with the same seed (as round two's
    run_parallel, so the "none" rows pair with its published run)."""
    tasks = [dict(kw, seed=seed, disturbances=(ds,)) for ds in disturbances]
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(min(jobs, len(tasks))) as pool:
            parts = pool.map(_run_one, tasks)
    else:
        parts = [_run_one(t) for t in tasks]
    rows = [r for part in parts for r in part]
    co = {c: i for i, c in enumerate(CORRECTIONS)}
    so = {sc: i for i, sc in enumerate(SCENARIOS)}
    do = {ds: i for i, ds in enumerate(disturbances)}
    rows.sort(key=lambda r: (co[r["correction"]], so[r["scenario"]], do[r["disturbance"]]))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="data")
    ap.add_argument("--name", default="flat_field_results.csv")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--diameters", type=float, nargs="+", default=list(DIAMETERS_MM))
    ap.add_argument("--disturbances", nargs="+", default=list(FF_DISTURBANCES))
    ap.add_argument("--card-frames", type=int, default=CARD_FRAMES)
    ap.add_argument("--card-smooth-mm", type=float, default=CARD_SMOOTH_MM)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    t0 = time.perf_counter()
    rows = run_parallel(seed=a.seed, trials=a.trials, px_per_mm=a.px_per_mm,
                        diameters=tuple(a.diameters), disturbances=tuple(a.disturbances),
                        card_frames=a.card_frames, card_smooth_mm=a.card_smooth_mm, jobs=a.jobs)
    out = Path(a.out) / a.name
    rs.write_csv(out, rows)
    tgt = Path(a.out) / a.name.replace("_results.csv", "_target.csv")
    rs.write_csv(tgt, target_rows(evaluate_flat_field_target(rows, diameter_mm=2.0)))
    print(f"flat-field sim (simulation, certainty level 0): {len(rows)} rows, {a.trials} trials, "
          f"{a.px_per_mm} px/mm; {time.perf_counter() - t0:.1f} s; wrote {out} and {tgt}")


if __name__ == "__main__":
    main()
