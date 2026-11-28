#!/usr/bin/env python3
"""Placement between sessions: four ways to put the measurement on the same skin.

SIMULATION ONLY. Synthetic disks on synthetic texture. No patient data, and no
image file is ever read. It tests the measuring method, not any treatment.

Plan task T5 (content/measurement-tool-plan.md sections 2.1 and 4). The
contract, tolerances and READING choices are in the docstring of
experiments/tests/test_placement_sim.py; this module implements it unchanged.

The four methods compared:
  * fixed inner disc   region "inner_disc": S is a disc of radius 0.6 x the
                       baseline radius (plan 2.1 item 2, 4.4)
  * surrounding skin   placement "ring_registration": the follow-up centre is
                       found by masked normalised cross-correlation on pixels
                       outside r + RING_GAP_MM only (plan 4.2)
  * sticker ring       placement "sticker": the true centre plus Gaussian
                       centring error, SD STICKER_SD_MM per axis (plan 4.1)
  * outline detection  segment_area(): used for area only (plan 4.3); asking
                       for a segmented colour region raises ValueError
Placement "none" (measure where the frame is) and region "outline" (a disc
of the baseline radius) are the reference cases.

Methods chosen by the builder (the tests leave them open):
  Registration  L* image of each visit, multiplied by a mask that keeps only
                pixels at radius > r + RING_GAP_MM from the frame centre (the
                same mask on both visits), then masked normalised
                cross-correlation (Padfield 2012 form) computed by zero-padded
                FFT over integer shifts up to MAX_REG_SHIFT_MM. The integer
                peak is refined per axis by a 3-point parabola. Refused (None)
                when the masked baseline has no variance (no texture), when
                the peak score is below MIN_REG_SCORE, or when the peak lies
                on the edge of the search window.
  Segmentation  L* of the follow-up capture, smoothed with a Gaussian of
                SEG_SMOOTH_MM. Reference level and spread: mean and SD of L*
                in the ring around the frame centre. A lighter spot is
                declared present when the 95th percentile of L* inside the
                ring's inner edge exceeds the ring mean by more than
                max(3 x ring SD, MIN_SEG_CONTRAST_L); otherwise area 0.0.
                Threshold at half way between the ring mean and that 95th
                percentile; the area is the 4-connected region above the
                threshold that contains the brightest pixel in the search
                disc, counted in pixels and converted to mm^2.
  Truth         true_change_pct is the same region measured on noise-free
                baseline and follow-up captures rendered at zero shift (with
                whole-scene shift, that is exact placement), blur as in the
                run, on UNIFORM skin. On mottled skin the texture alone gives
                the region a small contrast against the ring, so a truth
                measured on mottled skin could not be -100 % for the
                invisible spot, as the contract requires; the texture's
                effect therefore counts as measurement error, not as truth.
                The truth is the same for both backgrounds.

Run:  python3 experiments/placement_sim.py --out data      (about 15 min on 4 cores)
Needs: Python 3.9+, numpy. Reuses rgb_to_lab, blur and disk_ramp from
drift_sim.py (imported, not changed).
"""
import argparse
import csv
import math
import sys
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drift_sim import SKIN_RGB, WHITE_SPOT_RGB, blur, disk_ramp, rgb_to_lab  # noqa: E402

# ---- constants --------------------------------------------------------------
DIAMETERS_MM = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0)
SHIFTS = (0.0, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5)
RING_GAP_MM = 1.0
RING_WIDTH_MM = 1.5
INNER_FRACTION = 0.6
STICKER_SD_MM = 0.1
FIELD_MARGIN_MM = 1.5
MIN_FIELD_MM = 12.8
SCENARIOS = {
    "unchanged": (1.0, 1.0),
    "genuine_fading": (0.5, 1.0),
    "invisible": (0.0, 1.0),
    "dark_overshoot": (-1.0 / 3.0, 1.0),
    "shrinking": (1.0, 0.7),
}
PLACEMENTS = ("none", "ring_registration", "sticker")
REGIONS = ("outline", "inner_disc")
BACKGROUNDS = ("uniform", "mottled")

NOISE_SD = 0.01            # per-pixel, per-channel capture noise (as drift_sim)
MOTTLE_SD = 0.05
MOTTLE_CORR_MM = 1.0
MOTTLE_COMPONENTS = 256
BLUR_SD_MM = 0.10

MAX_REG_SHIFT_MM = 1.0     # registration search window, each axis
MIN_REG_SCORE = 0.3        # refuse below this normalised correlation peak
SEG_SMOOTH_MM = 0.05
MIN_SEG_CONTRAST_L = 0.5


# ---- geometry ---------------------------------------------------------------
def field_size(diameter_mm, px_per_mm):
    """Side of the square field in pixels (even), fixed by the baseline diameter."""
    mm = max(MIN_FIELD_MM,
             diameter_mm + 2 * (RING_GAP_MM + RING_WIDTH_MM + max(SHIFTS) + FIELD_MARGIN_MM))
    n = int(math.ceil(mm * px_per_mm))
    return n + (n % 2)


@lru_cache(maxsize=64)
def _coords(diameter_mm, px_per_mm):
    """Pixel-centre coordinates in mm; the frame centre (0, 0) is at index (n-1)/2."""
    n = field_size(diameter_mm, px_per_mm)
    c = (np.arange(n) - (n - 1) / 2.0) / px_per_mm
    c.setflags(write=False)
    return c


def _radius(diameter_mm, px_per_mm, centre_mm):
    c = _coords(diameter_mm, px_per_mm)
    cx, cy = _xy(centre_mm)
    return np.hypot(c[None, :] - cx, c[:, None] - cy)


def _xy(v):
    if np.isscalar(v):
        return float(v), 0.0
    return float(v[0]), float(v[1])


# ---- texture and scene ------------------------------------------------------
def _mottle(diameter_mm, px_per_mm, mottle_sd, mottle_corr_mm, shift_mm, seed):
    """Multiplicative luminance texture fixed to the skin (random Fourier sum,
    Gaussian spectrum). A shifted capture samples the same skin at x - shift.
    Scaled to mean 1, SD mottle_sd over the unshifted field."""
    c = _coords(diameter_mm, px_per_mm)
    rng = np.random.default_rng([seed, 7])
    k = rng.normal(0.0, 1.0 / mottle_corr_mm, size=(2, MOTTLE_COMPONENTS))
    phase = rng.uniform(0, 2 * math.pi, MOTTLE_COMPONENTS)

    def raw(sx, sy):
        a = np.exp(1j * np.outer(c - sy, k[1]))
        b = np.exp(1j * (np.outer(k[0], c - sx) + phase[:, None]))
        return np.real(a @ b)

    base = raw(0.0, 0.0)
    mu, sd = base.mean(), base.std()
    sx, sy = shift_mm
    field = base if (sx == 0 and sy == 0) else raw(sx, sy)
    return 1.0 + mottle_sd * (field - mu) / sd


def _clean(diameter_mm, *, px_per_mm, contrast_scale, diameter_scale, background,
           mottle_sd, mottle_corr_mm, shift_mm, blur_sd_mm, seed, texture=None):
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    if background not in BACKGROUNDS:
        raise ValueError(f"background must be one of {BACKGROUNDS}")
    sh = _xy(shift_mm)
    cov = disk_ramp(_radius(diameter_mm, px_per_mm, sh), px_per_mm, diameter_mm * diameter_scale)
    skin = np.asarray(SKIN_RGB, float)
    spot = np.asarray(WHITE_SPOT_RGB, float)
    img = skin + (contrast_scale * cov)[:, :, None] * (spot - skin)
    if background == "mottled" and mottle_sd != 0:
        if texture is None:
            texture = _mottle(diameter_mm, px_per_mm, mottle_sd, mottle_corr_mm, sh, seed)
        img = img * texture[:, :, None]
    return blur(img, px_per_mm, blur_sd_mm)


def render(diameter_mm, *, px_per_mm=20, contrast_scale=1.0, diameter_scale=1.0,
           background="uniform", mottle_sd=0.0, mottle_corr_mm=1.0, shift_mm=(0.0, 0.0),
           noise_sd=0.0, blur_sd_mm=0.0, seed=0):
    """Synthetic capture, linear RGB (n, n, 3). White spot centred at shift_mm."""
    img = _clean(diameter_mm, px_per_mm=px_per_mm, contrast_scale=contrast_scale,
                 diameter_scale=diameter_scale, background=background, mottle_sd=mottle_sd,
                 mottle_corr_mm=mottle_corr_mm, shift_mm=shift_mm, blur_sd_mm=blur_sd_mm,
                 seed=seed)
    if noise_sd > 0:
        img = img + np.random.default_rng([seed, 11]).normal(0.0, noise_sd, img.shape)
    return img


# ---- measurement ------------------------------------------------------------
def _masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction):
    if region not in REGIONS:
        raise ValueError(f"region must be one of {REGIONS}; segmentation is for area only")
    if not (0.0 < inner_fraction < 1.0):
        raise ValueError("inner_fraction must lie strictly between 0 and 1")
    r = _radius(diameter_mm, px_per_mm, centre_mm)
    rs = diameter_mm / 2 if region == "outline" else inner_fraction * diameter_mm / 2
    s = disk_ramp(r, px_per_mm, 2 * rs)
    r0 = diameter_mm / 2 + RING_GAP_MM
    ring = ((r >= r0) & (r <= r0 + RING_WIDTH_MM)).astype(float)
    return s, ring


def _contrast_lab(lab, diameter_mm, px_per_mm, region, centre_mm, inner_fraction):
    s, ring = _masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction)
    if lab.shape[:2] != s.shape:
        raise ValueError("image does not match the field for this diameter and px_per_mm")
    inside = (lab * s[:, :, None]).sum(axis=(0, 1)) / s.sum()
    around = (lab * ring[:, :, None]).sum(axis=(0, 1)) / ring.sum()
    c = inside - around
    return {"L": float(c[0]), "a": float(c[1]), "b": float(c[2])}


def measure_contrast(img, diameter_mm, px_per_mm, *, region="outline", centre_mm=(0, 0),
                     inner_fraction=INNER_FRACTION):
    """Mean Lab in S minus mean Lab in ring R, both centred on centre_mm."""
    _masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction)   # validate first
    return _contrast_lab(rgb_to_lab(img), diameter_mm, px_per_mm, region, centre_mm,
                         inner_fraction)


def _pct(cf, cb):
    if abs(cb) < 1e-6:
        raise ZeroDivisionError("percentage change is undefined at zero baseline contrast")
    return 100.0 * (cf - cb) / cb


def change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, region="outline",
               base_centre_mm=(0, 0), follow_centre_mm=(0, 0),
               inner_fraction=INNER_FRACTION, channel="L"):
    cb = measure_contrast(base_img, diameter_mm, px_per_mm, region=region,
                          centre_mm=base_centre_mm, inner_fraction=inner_fraction)[channel]
    cf = measure_contrast(follow_img, diameter_mm, px_per_mm, region=region,
                          centre_mm=follow_centre_mm, inner_fraction=inner_fraction)[channel]
    return _pct(cf, cb)


# ---- segmentation (area only) -------------------------------------------------
def _segment_L(L, diameter_mm, px_per_mm):
    r = _radius(diameter_mm, px_per_mm, (0.0, 0.0))
    r0 = diameter_mm / 2 + RING_GAP_MM
    ring = (r >= r0) & (r <= r0 + RING_WIDTH_MM)
    search = r < r0
    Ls = blur(L[:, :, None], px_per_mm, SEG_SMOOTH_MM)[:, :, 0]
    ref, spread = Ls[ring].mean(), Ls[ring].std()
    top = np.percentile(Ls[search], 95)
    if top - ref <= max(3 * spread, MIN_SEG_CONTRAST_L):
        return 0.0
    above = search & (Ls > (ref + top) / 2)
    seed = np.unravel_index(np.argmax(np.where(search, Ls, -np.inf)), Ls.shape)
    region = np.zeros_like(above)
    region[seed] = True
    while True:                                   # 4-connected flood fill
        grown = region.copy()
        grown[1:] |= region[:-1]
        grown[:-1] |= region[1:]
        grown[:, 1:] |= region[:, :-1]
        grown[:, :-1] |= region[:, 1:]
        grown &= above
        if np.array_equal(grown, region):
            break
        region = grown
    return float(region.sum()) / px_per_mm ** 2


def segment_area(img, diameter_mm, px_per_mm):
    """Area (mm^2) of the region lighter than the ring, found from the image alone."""
    return _segment_L(rgb_to_lab(img)[..., 0], diameter_mm, px_per_mm)


# ---- registration on the surrounding skin -----------------------------------
def _fft_len(n):
    m = n
    while True:
        k = m
        for p in (2, 3, 5):
            while k % p == 0:
                k //= p
        if k == 1:
            return m
        m += 1


@lru_cache(maxsize=64)
def _reg_setup(diameter_mm, px_per_mm):
    n = field_size(diameter_mm, px_per_mm)
    rmax = int(math.ceil(MAX_REG_SHIFT_MM * px_per_mm))
    size = _fft_len(n + rmax + 1)
    r = _radius(diameter_mm, px_per_mm, (0.0, 0.0))
    mask = (r > diameter_mm / 2 + RING_GAP_MM).astype(float)
    return n, rmax, size, mask


def _reg_base(base_L, diameter_mm, px_per_mm):
    """Everything that depends on the baseline only (reused across follow-ups)."""
    n, rmax, size, m = _reg_setup(diameter_mm, px_per_mm)
    a = base_L * m
    fa = np.fft.rfft2(a, (size, size))
    fa2 = np.fft.rfft2(a * base_L, (size, size))
    fm = np.fft.rfft2(m, (size, size))
    ok = a[m > 0].std() > 1e-9

    def corr(fu, fv):            # sum_x u(x) v(x - t), t = (dy, dx), wrapped
        return np.fft.irfft2(fu * np.conj(fv), (size, size))

    return {"fa": fa, "fm": fm, "ok": ok, "corr": corr,
            "N": corr(fm, fm), "SF": corr(fm, fa), "SFF": corr(fm, fa2)}


def _reg_follow(pre, follow_L, diameter_mm, px_per_mm):
    if not pre["ok"]:
        return None
    n, rmax, size, m = _reg_setup(diameter_mm, px_per_mm)
    b = follow_L * m
    fb = np.fft.rfft2(b, (size, size))
    fb2 = np.fft.rfft2(b * follow_L, (size, size))
    corr = pre["corr"]
    SG, SGG, SFG = corr(fb, pre["fm"]), corr(fb2, pre["fm"]), corr(fb, pre["fa"])
    idx = np.r_[0:rmax + 1, size - rmax:size]            # lags -rmax..rmax
    sel = np.ix_(idx, idx)
    N = np.maximum(pre["N"][sel], 1.0)
    SF, SFF = pre["SF"][sel], pre["SFF"][sel]
    SG, SGG, SFG = SG[sel], SGG[sel], SFG[sel]
    num = SFG - SF * SG / N
    den = (SFF - SF * SF / N) * (SGG - SG * SG / N)
    with np.errstate(invalid="ignore", divide="ignore"):
        ncc = np.where(den > 1e-12 * N * N, num / np.sqrt(np.abs(den)), -np.inf)
    lags = np.r_[0:rmax + 1, -rmax:0]
    order = np.argsort(lags)
    ncc = ncc[np.ix_(order, order)]
    iy, ix = np.unravel_index(np.argmax(ncc), ncc.shape)
    peak = ncc[iy, ix]
    if not np.isfinite(peak) or peak < MIN_REG_SCORE:
        return None
    if iy in (0, 2 * rmax) or ix in (0, 2 * rmax):
        return None

    def vertex(l, c, r):
        d = l - 2 * c + r
        return 0.0 if d >= 0 else 0.5 * (l - r) / d

    dy = iy - rmax + vertex(ncc[iy - 1, ix], peak, ncc[iy + 1, ix])
    dx = ix - rmax + vertex(ncc[iy, ix - 1], peak, ncc[iy, ix + 1])
    return (float(dx / px_per_mm), float(dy / px_per_mm))


# ---- placement ----------------------------------------------------------------
def _sticker(true_shift_mm, sticker_sd_mm, seed):
    tx, ty = _xy(true_shift_mm)
    e = np.random.default_rng(seed).normal(0.0, sticker_sd_mm, 2)
    return (float(tx + e[0]), float(ty + e[1]))


def place(method, base_img, follow_img, diameter_mm, px_per_mm, *, true_shift_mm=(0, 0),
          sticker_sd_mm=STICKER_SD_MM, seed=0):
    """Estimated follow-up spot centre (dx, dy) in mm, or None when refused."""
    if method == "none":
        return (0.0, 0.0)
    if method == "sticker":
        return _sticker(true_shift_mm, sticker_sd_mm, seed)
    if method == "ring_registration":
        pre = _reg_base(rgb_to_lab(base_img)[..., 0], diameter_mm, px_per_mm)
        return _reg_follow(pre, rgb_to_lab(follow_img)[..., 0], diameter_mm, px_per_mm)
    raise ValueError(f"method must be one of {PLACEMENTS}")


# ---- experiment -----------------------------------------------------------------
def _stats(vals):
    a = np.asarray(vals, float)
    if a.size == 0:
        return None, None
    return float(a.mean()), (float(a.std(ddof=1)) if a.size > 1 else None)


@lru_cache(maxsize=256)
def _truth(d, px_per_mm, c_scale, d_scale, blur_sd_mm):
    """True % change per region: noise-free, exact placement, blur as in the run,
    on uniform skin, so the number describes the spot alone (texture is part of
    the measurement error, not of the truth)."""
    def lab(cs, ds):
        return rgb_to_lab(_clean(d, px_per_mm=px_per_mm, contrast_scale=cs, diameter_scale=ds,
                                 background="uniform", mottle_sd=0.0, mottle_corr_mm=1.0,
                                 shift_mm=(0.0, 0.0), blur_sd_mm=blur_sd_mm, seed=0))
    b, f = lab(1.0, 1.0), lab(c_scale, d_scale)
    return {rg: _pct(_contrast_lab(f, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION)["L"],
                     _contrast_lab(b, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION)["L"])
            for rg in REGIONS}


def run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, shifts=SHIFTS,
        scenarios=tuple(SCENARIOS), noise_sd=NOISE_SD, mottle_sd=MOTTLE_SD,
        blur_sd_mm=BLUR_SD_MM, sticker_sd_mm=STICKER_SD_MM):
    """One row per scenario x background x diameter x shift x placement x region."""
    for sc in scenarios:
        if sc not in SCENARIOS:
            raise ValueError(f"unknown scenario {sc!r}")
    rng = np.random.default_rng(seed)
    cells = [(sc, bg, d, s) for sc in scenarios for bg in BACKGROUNDS
             for d in diameters for s in shifts]
    acc = {}
    for cell in cells:
        for p in PLACEMENTS:
            for rg in REGIONS:
                acc[cell + (p, rg)] = {"chg": [], "dL": [], "cerr": [], "rej": 0,
                                       "truth": [], "base": []}
    area = {cell: [] for cell in cells}

    for _ in range(trials):
        tex_seed = int(rng.integers(2 ** 31))
        for d in diameters:
            for bg in BACKGROUNDS:
                use_tex = bg == "mottled" and mottle_sd != 0
                tex = {}

                def texture(sh):
                    if not use_tex:
                        return None
                    if sh not in tex:
                        tex[sh] = _mottle(d, px_per_mm, mottle_sd, MOTTLE_CORR_MM, sh, tex_seed)
                    return tex[sh]

                def scene(c_scale, d_scale, sh):
                    return _clean(d, px_per_mm=px_per_mm, contrast_scale=c_scale,
                                  diameter_scale=d_scale, background=bg, mottle_sd=mottle_sd,
                                  mottle_corr_mm=MOTTLE_CORR_MM, shift_mm=sh,
                                  blur_sd_mm=blur_sd_mm, seed=tex_seed, texture=texture(sh))

                base_clean = scene(1.0, 1.0, (0.0, 0.0))
                base = base_clean + rng.normal(0.0, noise_sd, base_clean.shape) \
                    if noise_sd > 0 else base_clean
                base_lab = rgb_to_lab(base)
                cb = {rg: _contrast_lab(base_lab, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION)["L"]
                      for rg in REGIONS}
                pre = _reg_base(base_lab[..., 0], d, px_per_mm)
                for sc in scenarios:
                    c_scale, d_scale = SCENARIOS[sc]
                    truth = _truth(d, px_per_mm, c_scale, d_scale, blur_sd_mm)
                    for s in shifts:
                        sh = (float(s), 0.0)
                        fc = scene(c_scale, d_scale, sh)
                        foll = fc + rng.normal(0.0, noise_sd, fc.shape) if noise_sd > 0 else fc
                        flab = rgb_to_lab(foll)
                        area[(sc, bg, d, s)].append(_segment_L(flab[..., 0], d, px_per_mm))
                        st_seed = int(rng.integers(2 ** 31))
                        est = {"none": (0.0, 0.0),
                               "sticker": _sticker(sh, sticker_sd_mm, st_seed),
                               "ring_registration": _reg_follow(pre, flab[..., 0], d, px_per_mm)}
                        for p in PLACEMENTS:
                            for rg in REGIONS:
                                a = acc[(sc, bg, d, s, p, rg)]
                                a["truth"].append(truth[rg])
                                a["base"].append(cb[rg])
                                e = est[p]
                                if e is None:
                                    a["rej"] += 1
                                    continue
                                cf = _contrast_lab(flab, d, px_per_mm, rg, e, INNER_FRACTION)["L"]
                                a["chg"].append(_pct(cf, cb[rg]))
                                a["dL"].append(cf - cb[rg])
                                a["cerr"].append(math.hypot(e[0] - sh[0], e[1] - sh[1]))

    rows = []
    for cell in cells:
        sc, bg, d, s = cell
        a_true = math.pi * (d * SCENARIOS[sc][1] / 2) ** 2
        a_mean = float(np.mean(area[cell]))
        for p in PLACEMENTS:
            for rg in REGIONS:
                a = acc[cell + (p, rg)]
                truth = float(np.mean(a["truth"]))
                m, sd = _stats(a["chg"])
                ok = len(a["chg"]) > 0
                rows.append({
                    "scenario": sc, "background": bg, "diameter_mm": d, "shift_mm": s,
                    "placement": p, "region": rg,
                    "true_change_pct": truth,
                    "mean_change_pct": m, "sd_change_pct": sd,
                    "mean_abs_error_pct_points":
                        float(np.mean(np.abs(np.asarray(a["chg"]) - truth))) if ok else None,
                    "base_contrast_L": float(np.mean(a["base"])),
                    "mean_change_L": float(np.mean(a["dL"])) if ok else None,
                    "sd_change_L": _stats(a["dL"])[1],
                    "mean_centre_error_mm": float(np.mean(a["cerr"])) if ok else None,
                    "area_true_mm2": a_true, "area_mean_mm2": a_mean,
                    "area_error_pct": 100.0 * (a_mean - a_true) / a_true,
                    "trials": trials, "rejected": a["rej"],
                    "noise_sd": noise_sd, "mottle_sd": mottle_sd if bg == "mottled" else 0.0,
                    "blur_sd_mm": blur_sd_mm, "sticker_sd_mm": sticker_sd_mm,
                    "px_per_mm": px_per_mm,
                })
    return rows


# ---- target (plan section 4) ----------------------------------------------------
def _num(v):
    if v is None or v == "":
        return None
    return float(v)


def evaluate_target(rows, *, diameter_mm=2.0, shift_mm=0.5, background="mottled"):
    """Apply the plan's section 4 target. See the test file's docstring."""
    idx = {}
    for r in rows:
        if r["background"] != background or float(r["diameter_mm"]) != float(diameter_mm):
            continue
        idx[(r["scenario"], float(r["shift_mm"]), r["placement"], r["region"])] = r

    def get(sc, s, p, rg):
        k = (sc, float(s), p, rg)
        if k not in idx:
            raise ValueError(f"required row missing: {k} at {diameter_mm} mm, {background}")
        return idx[k]

    def within(v, lim):
        return v is not None and abs(v) <= lim

    out = {}
    for p in PLACEMENTS:
        for rg in REGIONS:
            un = get("unchanged", shift_mm, p, rg)
            gf = get("genuine_fading", shift_mm, p, rg)
            m_un, sd_un = _num(un["mean_change_pct"]), _num(un["sd_change_pct"])
            m_gf, t_gf = _num(gf["mean_change_pct"]), _num(gf["true_change_pct"])
            e = {"false_change_ok": within(m_un, 2.0),
                 "sd_ok": sd_un is not None and sd_un <= 1.0,
                 "sensitivity_ok": m_gf is not None and abs(m_gf - t_gf) <= 2.0}
            if rg == "inner_disc":
                sd0 = _num(get("unchanged", 0.0, p, rg)["sd_change_pct"])
                near = [r for (sc, s, pp, rr), r in idx.items()
                        if sc == "unchanged" and pp == p and rr == rg and 0 < s <= 0.3]
                if not near:
                    raise ValueError("no unchanged rows with 0 < shift <= 0.3 mm")
                e["within_noise_to_0_3mm"] = sd0 is not None and all(
                    within(_num(r["mean_change_pct"]), sd0) for r in near)
            else:
                e["within_noise_to_0_3mm"] = None
            e["passes"] = all(v for v in e.values() if v is not None)
            out[(p, rg)] = e
    out["area_ok"] = all(
        within(_num(get(sc, shift_mm, "none", "outline")["area_error_pct"]), 10.0)
        for sc in ("unchanged", "shrinking"))
    return out


# ---- output ----------------------------------------------------------------------
def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.4f}"
    return v


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(v) for k, v in r.items()})


def _run_one(kw):
    return run(**kw)


def run_by_diameter(*, seed, diameters, jobs=1, **kw):
    """run() once per diameter, each with the same seed, in parallel processes;
    rows returned in run()'s order. Reproducible for a given seed and diameter
    list whatever the number of jobs."""
    tasks = [dict(kw, seed=seed, diameters=(d,)) for d in diameters]
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(min(jobs, len(tasks))) as pool:
            parts = pool.map(_run_one, tasks)
    else:
        parts = [_run_one(t) for t in tasks]
    order = {d: i for i, d in enumerate(diameters)}
    rows = [r for part in parts for r in part]
    key = {sc: i for i, sc in enumerate(SCENARIOS)}
    rows.sort(key=lambda r: (key[r["scenario"]], BACKGROUNDS.index(r["background"]),
                             order[r["diameter_mm"]]))      # stable: keeps shift/placement order
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="data")
    ap.add_argument("--name", default="placement_sim_results.csv")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--sticker-sd-mm", type=float, default=STICKER_SD_MM)
    ap.add_argument("--diameters", type=float, nargs="+", default=list(DIAMETERS_MM))
    ap.add_argument("--scenarios", nargs="+", default=list(SCENARIOS))
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    t0 = time.perf_counter()
    rows = run_by_diameter(seed=a.seed, trials=a.trials, px_per_mm=a.px_per_mm,
                           diameters=tuple(a.diameters), scenarios=tuple(a.scenarios),
                           sticker_sd_mm=a.sticker_sd_mm, jobs=a.jobs)
    out = Path(a.out) / a.name
    write_csv(out, rows)
    print(f"placement sim: {len(rows)} rows, {a.trials} trials, {a.px_per_mm} px/mm, "
          f"sticker SD {a.sticker_sd_mm} mm; {time.perf_counter() - t0:.1f} s; wrote {out}")


if __name__ == "__main__":
    main()
