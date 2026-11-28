#!/usr/bin/env python3
"""Lighting drift, white-balance drift and mottled skin: a measurement simulation.

SIMULATION ONLY. Synthetic disks on synthetic texture. No patient data, and no
image file is ever read. It tests the measuring method, not any treatment.

The spot is identical at both visits, so the true change is 0 % in every row
and every measured change is a false change. Factors:

  spot        white (IGH-like, lighter than skin) or brown (lentigo-like,
              darker and yellower)
  background  uniform skin, or a multiplicative luminance texture (mottle)
  diameter    2 to 8 mm
  shift       outline misplacement at the second visit (0, 0.25, 0.5 mm)
  drift       uniform exposure change (no gradient) or per-channel
              white-balance change at the second visit
  correction  none, or "ring_white": each colour channel divided by its mean
              in the reference ring around the spot before conversion to Lab

Measurement: per-pixel CIELAB (D65, linear sRGB primaries), mean inside the
centred outline minus mean in a reference ring (gap 1.0 mm, width 1.5 mm, as
in alignment_pixel_sim.py). Tests: experiments/tests/test_drift_sim.py.

Run:  python3 experiments/drift_sim.py --out data
Needs: Python 3.9+, numpy.
"""
import argparse
import csv
import math
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

# ---- scene constants (linear RGB, 0..1) -------------------------------------
SKIN_RGB = (0.45, 0.32, 0.25)        # nearby skin
WHITE_SPOT_RGB = (0.62, 0.50, 0.42)  # IGH-like: lighter than skin
BROWN_SPOT_RGB = (0.30, 0.18, 0.10)  # lentigo-like: darker and yellower
DIAMETERS_MM = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0)
SHIFTS = (0.0, 0.25, 0.5)
RING_GAP_MM = 1.0                    # reference ring starts this far outside the outline
RING_WIDTH_MM = 1.5
FIELD_MARGIN_MM = 1.5                # skin beyond the ring's outer edge, each side
MIN_FIELD_MM = 12.8
NOISE_SD = 0.01                      # per-pixel, per-channel capture noise (linear RGB)
BLUR_SD_MM = 0.10                    # optical blur used by run() (Gaussian sigma)
MOTTLE_SD = 0.05                     # SD of the luminance multiplier (5 %)
MOTTLE_CORR_MM = 1.0                 # correlation length of the mottle
MOTTLE_COMPONENTS = 256              # random Fourier components in the texture

# second-visit drift: name -> (exposure_gain, (r, g, b) white-balance gains)
DRIFTS = {
    "none": (1.0, (1.0, 1.0, 1.0)),
    "exposure_minus_20pct": (0.8, (1.0, 1.0, 1.0)),
    "exposure_plus_25pct": (1.25, (1.0, 1.0, 1.0)),
    "wb_warmer": (1.0, (1.10, 1.0, 0.85)),
    "wb_cooler": (1.0, (0.90, 1.0, 1.15)),
}
SPOTS = ("white", "brown")
BACKGROUNDS = ("uniform", "mottled")
CORRECTIONS = ("none", "ring_white")

# linear sRGB -> XYZ (D65) and the D65 white point
_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]])
_WHITE = np.array([0.95047, 1.0, 1.08883])
_LAB_INDEX = {"L": 0, "a": 1, "b": 2}


# ---- geometry ---------------------------------------------------------------
def field_size(diameter_mm, px_per_mm):
    """Pixels per side of the square field for this spot size (even number)."""
    mm = max(MIN_FIELD_MM, diameter_mm + 2 * (RING_GAP_MM + RING_WIDTH_MM + FIELD_MARGIN_MM))
    n = int(math.ceil(mm * px_per_mm))
    return n + (n % 2)


@lru_cache(maxsize=64)
def _geometry(diameter_mm, px_per_mm):
    """Pixel-centre coordinates (mm), field centre, outline and ring weights."""
    n = field_size(diameter_mm, px_per_mm)
    c = (np.arange(n) + 0.5) / px_per_mm
    X, Y = np.meshgrid(c, c)
    c0 = n / px_per_mm / 2
    r = np.hypot(X - c0, Y - c0)
    mask = disk_ramp(r, px_per_mm, diameter_mm)
    r0 = diameter_mm / 2 + RING_GAP_MM
    ring = ((r >= r0) & (r <= r0 + RING_WIDTH_MM)).astype(float)
    for a in (c, mask, ring):
        a.setflags(write=False)
    return c, c0, mask, ring


def disk_ramp(r_mm, px_per_mm, diameter_mm):
    """Anti-aliased disk coverage: one-pixel linear ramp across the edge."""
    return np.clip(0.5 - (r_mm - diameter_mm / 2) * px_per_mm, 0.0, 1.0)


def blur(img, px_per_mm, sd_mm):
    """Gaussian blur per channel by FFT (as in alignment_pixel_sim.py)."""
    if sd_mm <= 0:
        return img
    n = img.shape[0]
    f = np.fft.fftfreq(n, d=1.0 / px_per_mm)
    g = np.exp(-2 * (math.pi * sd_mm) ** 2 * (f[None, :] ** 2 + f[:, None] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(img, axes=(0, 1)) * g[:, :, None], axes=(0, 1)))


# ---- texture ----------------------------------------------------------------
def mottle(diameter_mm, px_per_mm, *, mottle_sd, mottle_corr_mm, shift_mm, seed):
    """Multiplicative luminance texture, fixed to the skin, sampled on the field.

    A sum of random Fourier components with a Gaussian spectrum (covariance
    exp(-r^2 / (2 corr^2))), defined in continuous skin coordinates so that a
    shifted capture samples exactly the same skin. It is scaled to mean 1 and
    SD mottle_sd over the unshifted field; the same scaling is applied to
    every capture of that skin.
    """
    c, _, _, _ = _geometry(diameter_mm, px_per_mm)
    rng = np.random.default_rng([seed, 7])
    k = rng.normal(0.0, 1.0 / mottle_corr_mm, size=(2, MOTTLE_COMPONENTS))
    phase = rng.uniform(0, 2 * math.pi, MOTTLE_COMPONENTS)

    def raw(sx):
        a = np.exp(1j * np.outer(c, k[1]))                                # rows: y
        b = np.exp(1j * (np.outer(k[0], c - sx) + phase[:, None]))        # cols: x
        return np.real(a @ b)

    base = raw(0.0)
    mu, sd = base.mean(), base.std()
    field = base if shift_mm == 0 else raw(shift_mm)
    return 1.0 + mottle_sd * (field - mu) / sd


# ---- scene ------------------------------------------------------------------
def _clean_scene(diameter_mm, *, px_per_mm, spot, contrast_scale, background,
                 mottle_sd, mottle_corr_mm, shift_mm, blur_sd_mm, seed, texture=None):
    """Noise-free capture before drift. texture, if given, overrides the seed."""
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    if spot not in SPOTS:
        raise ValueError(f"spot must be one of {SPOTS}")
    if background not in BACKGROUNDS:
        raise ValueError(f"background must be one of {BACKGROUNDS}")
    c, c0, _, _ = _geometry(diameter_mm, px_per_mm)
    X, Y = np.meshgrid(c, c)
    cov = disk_ramp(np.hypot(X - (c0 + shift_mm), Y - c0), px_per_mm, diameter_mm)
    skin = np.asarray(SKIN_RGB, float)
    target = np.asarray(WHITE_SPOT_RGB if spot == "white" else BROWN_SPOT_RGB, float)
    img = skin + (contrast_scale * cov)[:, :, None] * (target - skin)
    if background == "mottled" and mottle_sd != 0:
        if texture is None:
            texture = mottle(diameter_mm, px_per_mm, mottle_sd=mottle_sd,
                             mottle_corr_mm=mottle_corr_mm, shift_mm=shift_mm, seed=seed)
        img = img * texture[:, :, None]
    return blur(img, px_per_mm, blur_sd_mm)


def _capture(clean, exposure_gain, wb_gains, noise_sd, rng):
    img = clean * (exposure_gain * np.asarray(wb_gains, float))
    if noise_sd > 0:
        img = img + rng.normal(0.0, noise_sd, img.shape)
    return img


def render(diameter_mm, *, px_per_mm=20, spot="white", contrast_scale=1.0,
           background="uniform", mottle_sd=0.0, mottle_corr_mm=1.0, shift_mm=0.0,
           exposure_gain=1.0, wb_gains=(1.0, 1.0, 1.0), noise_sd=0.0, blur_sd_mm=0.0,
           seed=0):
    """Synthetic capture, linear RGB, (n, n, 3), centred on the measuring outline."""
    clean = _clean_scene(diameter_mm, px_per_mm=px_per_mm, spot=spot,
                         contrast_scale=contrast_scale, background=background,
                         mottle_sd=mottle_sd, mottle_corr_mm=mottle_corr_mm,
                         shift_mm=shift_mm, blur_sd_mm=blur_sd_mm, seed=seed)
    return _capture(clean, exposure_gain, wb_gains, noise_sd, np.random.default_rng([seed, 11]))


# ---- measurement ------------------------------------------------------------
def rgb_to_lab(img):
    """Linear sRGB -> CIELAB (D65), per pixel."""
    t = (img @ _M.T) / _WHITE
    d = 6.0 / 29.0
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4.0 / 29.0)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], axis=-1)


def measure_contrast(img, diameter_mm, px_per_mm, *, correction="none"):
    """Mean Lab inside the centred outline minus mean Lab in the reference ring."""
    if correction not in CORRECTIONS:
        raise ValueError(f"correction must be one of {CORRECTIONS}")
    _, _, mask, ring = _geometry(diameter_mm, px_per_mm)
    if img.shape[:2] != mask.shape:
        raise ValueError("image does not match the field for this diameter and px_per_mm")
    if correction == "ring_white":
        img = img / ((img * ring[:, :, None]).sum(axis=(0, 1)) / ring.sum())
    lab = rgb_to_lab(img)
    inside = (lab * mask[:, :, None]).sum(axis=(0, 1)) / mask.sum()
    around = (lab * ring[:, :, None]).sum(axis=(0, 1)) / ring.sum()
    c = inside - around
    return {"L": float(c[0]), "a": float(c[1]), "b": float(c[2])}


def pct_change(c_follow, c_base):
    """Percentage change in signed contrast. Refused at zero baseline."""
    if abs(c_base) < 1e-6:
        raise ZeroDivisionError("percentage change is undefined at zero baseline contrast")
    return 100.0 * (c_follow - c_base) / c_base


def change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, channel="L", correction="none"):
    cb = measure_contrast(base_img, diameter_mm, px_per_mm, correction=correction)[channel]
    cf = measure_contrast(follow_img, diameter_mm, px_per_mm, correction=correction)[channel]
    return pct_change(cf, cb)


# ---- experiment -------------------------------------------------------------
def run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, shifts=SHIFTS,
        noise_sd=NOISE_SD, mottle_sd=MOTTLE_SD, channel="L"):
    """Unchanged spot measured twice. One row per factor combination."""
    rng = np.random.default_rng(seed)
    if channel not in _LAB_INDEX:
        raise ValueError("channel must be L, a or b")
    # errors[(spot, bg, d, shift, drift, corr)] -> list of measured % changes
    errors, rejected = {}, {}
    keys = [(sp, bg, d, s, dr, co) for sp in SPOTS for bg in BACKGROUNDS for d in diameters
            for s in shifts for dr in DRIFTS for co in CORRECTIONS]
    for k in keys:
        errors[k], rejected[k] = [], 0
    for _ in range(trials):
        tex_seed = int(rng.integers(2 ** 31))      # one skin texture per trial
        for d in diameters:
            textures = {s: mottle(d, px_per_mm, mottle_sd=mottle_sd, mottle_corr_mm=MOTTLE_CORR_MM,
                                  shift_mm=s, seed=tex_seed) if mottle_sd != 0 else None
                        for s in set(shifts) | {0.0}}
            for sp in SPOTS:
                for bg in BACKGROUNDS:
                    def scene(s):
                        return _clean_scene(d, px_per_mm=px_per_mm, spot=sp, contrast_scale=1.0,
                                            background=bg, mottle_sd=mottle_sd,
                                            mottle_corr_mm=MOTTLE_CORR_MM, shift_mm=s,
                                            blur_sd_mm=BLUR_SD_MM, seed=tex_seed,
                                            texture=textures[s])
                    base = _capture(scene(0.0), 1.0, (1.0, 1.0, 1.0), noise_sd, rng)
                    cb = {co: measure_contrast(base, d, px_per_mm, correction=co) for co in CORRECTIONS}
                    for s in shifts:
                        clean = scene(s)
                        for dr, (g, wb) in DRIFTS.items():
                            foll = _capture(clean, g, wb, noise_sd, rng)
                            for co in CORRECTIONS:
                                k = (sp, bg, d, s, dr, co)
                                cf = measure_contrast(foll, d, px_per_mm, correction=co)
                                try:
                                    errors[k].append(pct_change(cf[channel], cb[co][channel]))
                                except ZeroDivisionError:
                                    rejected[k] += 1
    rows = []
    for k in keys:
        sp, bg, d, s, dr, co = k
        a = np.array(errors[k])
        ok = len(a) > 0
        g, wb = DRIFTS[dr]
        rows.append({
            "spot": sp, "background": bg, "diameter_mm": d, "shift_mm": s, "drift": dr,
            "exposure_gain": g, "wb_gains": "/".join(f"{x:g}" for x in wb),
            "correction": co, "channel": channel, "true_change_pct": 0.0,
            "measured_mean_pct": round(float(a.mean()), 2) if ok else "",
            "signed_bias_pct_points": round(float(a.mean()), 2) if ok else "",
            "mean_abs_error_pct_points": round(float(np.abs(a).mean()), 2) if ok else "",
            "sd_pct_points": round(float(a.std(ddof=1)), 2) if len(a) > 1 else "",
            "trials": trials, "rejected": rejected[k],
            "mottle_sd": mottle_sd if bg == "mottled" else 0.0,
            "noise_sd": noise_sd, "blur_sd_mm": BLUR_SD_MM, "px_per_mm": px_per_mm,
        })
    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def self_checks():
    lab = rgb_to_lab(np.array([[_WHITE @ np.linalg.inv(_M).T]]))[0, 0]
    assert abs(lab[0] - 100) < 1e-6 and abs(lab[1]) < 1e-6 and abs(lab[2]) < 1e-6
    try:
        pct_change(1.0, 0.0)
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("zero-baseline case must be refused")
    assert pct_change(7.5, 15.0) == -50.0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="data")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261127)
    a = ap.parse_args()
    self_checks()
    t0 = time.perf_counter()
    rows = run(seed=a.seed, trials=a.trials, px_per_mm=a.px_per_mm)
    out = Path(a.out)
    write_csv(out / "drift_sim_results.csv", rows)
    print(f"drift sim: {len(rows)} rows, {a.trials} trials each, {a.px_per_mm} px/mm; "
          f"runtime {time.perf_counter() - t0:.1f} s; wrote {out}/drift_sim_results.csv")


if __name__ == "__main__":
    main()
