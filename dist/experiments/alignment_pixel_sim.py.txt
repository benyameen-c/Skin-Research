#!/usr/bin/env python3
"""Pixel-based check and extension of the IGH alignment benchmark.

SIMULATION ONLY. Synthetic disks on a uniform background. No patient data.
It tests the measuring instrument, not any treatment.

Part 1 (validation): an independently built raster model (supersampled
pixels) is compared with the closed-form circle-overlap formula in
alignment.py, for equal circles and for a shrunken spot.

Part 2 (Monte Carlo): five follow-up scenarios are measured with four
outline strategies under pixel noise and blur, for 2, 3 and 5 mm spots.

Run:  python3 experiments/alignment_pixel_sim.py --out data
Needs: Python 3.9+, numpy.
"""
import argparse
import csv
import math
import time
from pathlib import Path

import numpy as np

# ---- scene constants (arbitrary lightness units, think CIELAB L*) ----------
BG_L = 60.0          # nearby skin lightness at baseline
SPOT_DL = 15.0       # spot is 15 units lighter than nearby skin at baseline
NOISE_SD = 1.0       # per-pixel noise
BLUR_SD_MM = 0.10    # optical blur (Gaussian sigma)
RING_GAP_MM = 1.0    # reference ring starts this far outside the outline
RING_WIDTH_MM = 1.5
DIAMETERS = (2.0, 3.0, 5.0)
SHIFTS = (0.0, 0.25, 0.5)

# follow-up scenarios: (name, diameter factor, spot contrast factor, bg delta)
SCENARIOS = (
    ("unchanged", 1.0, 1.0, 0.0),
    ("genuine_fading", 1.0, 0.5, 0.0),            # contrast halves, same area
    ("shrinking", 0.7, 1.0, 0.0),                 # diameter x0.7, same contrast
    ("dark_overshoot", 1.0, -1.0 / 3.0, 0.0),     # spot ends 5 units DARKER
    ("nearby_skin_darkens", 1.0, 1.0, -5.0),      # spot itself unchanged, tan
)


# ---- analytic references ----------------------------------------------------
def lens_area(R, r, s):
    """Overlap area of two circles (radii R >= r) whose centres are s apart."""
    if s >= R + r:
        return 0.0
    if s <= R - r:
        return math.pi * r * r
    a = r * r * math.acos((s * s + r * r - R * R) / (2 * s * r))
    b = R * R * math.acos((s * s + R * R - r * r) / (2 * s * R))
    c = 0.5 * math.sqrt((-s + r + R) * (s + r - R) * (s - r + R) * (s + r + R))
    return a + b - c


def analytic_retained(d_mask, d_spot, shift):
    """Fraction of the baseline outline covered by the (possibly smaller) spot."""
    R, r = d_mask / 2, d_spot / 2
    if r > R:
        R, r = r, R
    return lens_area(R, r, shift) / (math.pi * (d_mask / 2) ** 2)


# ---- raster model -----------------------------------------------------------
def grid(n, px_per_mm):
    c = (np.arange(n) + 0.5) / px_per_mm
    return np.meshgrid(c, c)  # x, y in mm


def disk_supersampled(n, px_per_mm, cx, cy, d, ss=8):
    """Exact-ish pixel coverage by brute-force subpixel counting."""
    m = n * ss
    c = (np.arange(m) + 0.5) / (px_per_mm * ss)
    inside = ((c[None, :] - cx) ** 2 + (c[:, None] - cy) ** 2) <= (d / 2) ** 2
    return inside.reshape(n, ss, n, ss).mean(axis=(1, 3))


def disk_ramp(X, Y, px_per_mm, cx, cy, d):
    """Fast anti-aliased coverage: one-pixel linear ramp across the edge."""
    dist_px = (np.hypot(X - cx, Y - cy) - d / 2) * px_per_mm
    return np.clip(0.5 - dist_px, 0.0, 1.0)


def ring_weights(X, Y, cx, cy, d):
    rr = np.hypot(X - cx, Y - cy)
    r0 = d / 2 + RING_GAP_MM
    return ((rr >= r0) & (rr <= r0 + RING_WIDTH_MM)).astype(float)


def blur(img, px_per_mm, sd_mm):
    if sd_mm <= 0:
        return img
    n = img.shape[0]
    f = np.fft.fftfreq(n, d=1.0 / px_per_mm)  # cycles per mm
    g = np.exp(-2 * (math.pi * sd_mm) ** 2 * (f[None, :] ** 2 + f[:, None] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(img) * g))


def signed_contrast(img, w_mask, w_ring):
    """Mean lightness inside the outline minus mean lightness of the ring."""
    return (img * w_mask).sum() / w_mask.sum() - (img * w_ring).sum() / w_ring.sum()


def pct_change(c_follow, c_base):
    """Percentage change in signed contrast. Undefined at zero baseline."""
    if abs(c_base) < 1e-9:
        raise ZeroDivisionError("percentage change is undefined at zero baseline contrast")
    return 100.0 * (c_follow - c_base) / c_base


# ---- outline strategies -----------------------------------------------------
def estimate_shift(base, follow, px_per_mm, max_mm=1.0, min_score=0.2):
    """Sign-agnostic FFT cross-correlation. Returns (dx_mm, dy_mm) or None."""
    b = base - base.mean()
    f = follow - follow.mean()
    cc = np.real(np.fft.ifft2(np.fft.fft2(f) * np.conj(np.fft.fft2(b))))
    n = cc.shape[0]
    w = int(round(max_mm * px_per_mm))
    cc = np.fft.fftshift(cc)
    c0 = n // 2
    win = np.abs(cc[c0 - w:c0 + w + 1, c0 - w:c0 + w + 1])
    score = win.max() / (np.linalg.norm(b) * np.linalg.norm(f) + 1e-12)
    if score < min_score:
        return None
    iy, ix = np.unravel_index(np.argmax(win), win.shape)

    def sub(v, i):
        if 0 < i < len(v) - 1:
            den = v[i - 1] - 2 * v[i] + v[i + 1]
            if abs(den) > 1e-12:
                return 0.5 * (v[i - 1] - v[i + 1]) / den
        return 0.0

    dx = ix - w + sub(win[iy, :], ix)
    dy = iy - w + sub(win[:, ix], iy)
    return dx / px_per_mm, dy / px_per_mm


def trace(img, X, Y, cx, cy, d, min_peak=3.0):
    """Independent re-outline: pixels lighter than half the local peak.

    Returns (weights, area_mm2-less pixel count) or None when no light spot
    is found. A darker-than-skin spot is therefore a reported failure.
    """
    ring = ring_weights(X, Y, cx, cy, d)
    bg = (img * ring).sum() / ring.sum()
    window = np.hypot(X - cx, Y - cy) <= d / 2 + RING_GAP_MM * 0.9
    c = (img - bg) * window
    peak = np.percentile(c[window], 95)
    if peak < min_peak:
        return None
    w = ((c > 0.5 * peak) & window).astype(float)
    if w.sum() < 4:
        return None
    return w, ring


# ---- experiments ------------------------------------------------------------
def validate(out_dir):
    """Noise-free, blur-free raster against the closed-form overlap formula."""
    rows = []
    for px in (20, 40):
        n = int(16 * px)
        X, Y = grid(n, px)
        c0 = 8.0
        for d in DIAMETERS:
            mask = disk_supersampled(n, px, c0, c0, d)
            ring = ring_weights(X, Y, c0, c0, d)
            base = signed_contrast(BG_L + SPOT_DL * mask, mask, ring) / SPOT_DL
            for factor, label in ((1.0, "equal_circles"), (0.7, "spot_shrunk_to_0.7d")):
                for s in SHIFTS:
                    spot = disk_supersampled(n, px, c0 + s, c0, d * factor)
                    raster = signed_contrast(BG_L + SPOT_DL * spot, mask, ring) / SPOT_DL
                    exact = analytic_retained(d, d * factor, s)
                    rows.append({
                        "check": label, "px_per_mm": px, "diameter_mm": d, "shift_mm": s,
                        "analytic_loss_pct": round(100 * (1 - exact), 3),
                        "raster_loss_pct": round(100 * (1 - raster), 3),
                        "difference_pct_points": round(100 * (exact - raster), 3),
                        # what a pipeline would report: change against its own
                        # rasterised zero-shift baseline (edge pixels dilute it)
                        "raster_change_vs_raster_baseline_pct": round(100 * (raster / base - 1), 3),
                    })
    write_csv(out_dir / "alignment_validation.csv", rows)
    return rows


def monte_carlo(out_dir, trials, px, seed):
    rng = np.random.default_rng(seed)
    n = int(12.8 * px)
    X, Y = grid(n, px)
    c0 = n / px / 2
    rows = []
    for d in DIAMETERS:
        base_clean = blur(BG_L + SPOT_DL * disk_ramp(X, Y, px, c0, c0, d), px, BLUR_SD_MM)
        m_fixed = disk_ramp(X, Y, px, c0, c0, d)
        r_fixed = ring_weights(X, Y, c0, c0, d)
        for name, dfac, cfac, bgd in SCENARIOS:
            dl = SPOT_DL * cfac - bgd  # follow-up spot minus follow-up surroundings
            # measurand: mean signed contrast inside the correctly aligned baseline outline
            true_pct = 100.0 * (dl * dfac ** 2 / SPOT_DL - 1.0)
            for s in SHIFTS:
                follow_clean = blur(
                    (BG_L + bgd) + dl * disk_ramp(X, Y, px, c0 + s, c0, d * dfac), px, BLUR_SD_MM)
                acc = {k: [] for k in ("fixed_misaligned", "registered", "traced_mean", "traced_integrated")}
                rej = {k: 0 for k in acc}
                tsum = {k: 0.0 for k in acc}
                bg_shift = []
                for _ in range(trials):
                    base = base_clean + rng.normal(0, NOISE_SD, base_clean.shape)
                    foll = follow_clean + rng.normal(0, NOISE_SD, follow_clean.shape)
                    cb = signed_contrast(base, m_fixed, r_fixed)
                    bg_shift.append((foll * r_fixed).sum() / r_fixed.sum()
                                    - (base * r_fixed).sum() / r_fixed.sum())

                    t = time.perf_counter()
                    acc["fixed_misaligned"].append(pct_change(signed_contrast(foll, m_fixed, r_fixed), cb))
                    tsum["fixed_misaligned"] += time.perf_counter() - t

                    t = time.perf_counter()
                    est = estimate_shift(base, foll, px)
                    if est is None:
                        rej["registered"] += 1
                    else:
                        m = disk_ramp(X, Y, px, c0 + est[0], c0 + est[1], d)
                        r = ring_weights(X, Y, c0 + est[0], c0 + est[1], d)
                        acc["registered"].append(pct_change(signed_contrast(foll, m, r), cb))
                    tsum["registered"] += time.perf_counter() - t

                    t = time.perf_counter()
                    tb = trace(base, X, Y, c0, c0, d)
                    tf = trace(foll, X, Y, c0, c0, d)
                    if tb is None or tf is None:
                        rej["traced_mean"] += 1
                        rej["traced_integrated"] += 1
                    else:
                        cbt = signed_contrast(base, tb[0], tb[1])
                        cft = signed_contrast(foll, tf[0], tf[1])
                        acc["traced_mean"].append(pct_change(cft, cbt))
                        acc["traced_integrated"].append(
                            pct_change(cft * tf[0].sum(), cbt * tb[0].sum()))
                    dt = time.perf_counter() - t
                    tsum["traced_mean"] += dt
                    tsum["traced_integrated"] += dt
                for k, v in acc.items():
                    a = np.array(v)
                    ok = len(a) > 0
                    rows.append({
                        "scenario": name, "diameter_mm": d, "shift_mm": s, "outline": k,
                        "true_change_pct": round(true_pct, 1),
                        "measured_mean_pct": round(float(a.mean()), 1) if ok else "",
                        "signed_bias_pct_points": round(float(a.mean() - true_pct), 1) if ok else "",
                        "mean_abs_error_pct_points": round(float(np.abs(a - true_pct).mean()), 1) if ok else "",
                        "sd_pct_points": round(float(a.std(ddof=1)), 1) if len(a) > 1 else "",
                        "trials": trials, "rejected": rej[k],
                        "reference_lightness_shift": round(float(np.mean(bg_shift)), 2),
                        "ms_per_measurement": round(1000 * tsum[k] / trials, 2),
                    })
    write_csv(out_dir / "alignment_results.csv", rows)
    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def self_checks():
    assert analytic_retained(2, 2, 0) == 1.0
    assert analytic_retained(2, 2, 2) == 0.0
    assert abs(analytic_retained(2, 1.4, 0.25) - 0.49) < 1e-12  # small spot still inside
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
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261127)
    a = ap.parse_args()
    out = Path(a.out)
    self_checks()
    t0 = time.perf_counter()
    v = validate(out)
    moved = max(abs(r["difference_pct_points"]) for r in v if r["shift_mm"] > 0)
    edge = max(abs(r["difference_pct_points"]) for r in v if r["shift_mm"] == 0 and r["check"] == "equal_circles")
    print(f"validation: {len(v)} comparisons; worst raster-vs-analytic gap at nonzero shift {moved:.3f} points; "
          f"zero-shift edge-pixel dilution up to {edge:.3f} points")
    r = monte_carlo(out, a.trials, a.px_per_mm, a.seed)
    print(f"monte carlo: {len(r)} rows, {a.trials} trials each, {a.px_per_mm} px/mm")
    print(f"total runtime {time.perf_counter() - t0:.1f} s; wrote {out}/alignment_validation.csv and {out}/alignment_results.csv")


if __name__ == "__main__":
    main()
