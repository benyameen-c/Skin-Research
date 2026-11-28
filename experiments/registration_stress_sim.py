#!/usr/bin/env python3
"""Registration stress test: placement round two (hair, tanning, rotation, light).

SIMULATION ONLY. Synthetic disks, synthetic texture, synthetic straight "hairs".
No patient data, and no image file is ever read. It tests the measuring method,
not any treatment. Its output is a simulation result, not evidence.

Round one (experiments/placement_sim.py, content/experiments.md section 5)
tested lining up on the surrounding skin in its best case, with the skin
texture identical at both visits. This round adds four disturbances between
the two photo sessions, singly and combined, and asks at which size each one
makes each placement method miss the plan's section 4 target at 2 mm and
0.5 mm misplacement on mottled skin.

The contract (constants, rendering order, truth, refusals, row keys, target and
breaking levels) is the docstring of experiments/tests/test_registration_stress_sim.py,
written before this file and implemented here unchanged. EVERY DISTURBANCE SIZE
IS THE TEST AUTHOR'S ASSUMPTION, chosen to bracket plausible conditions; none
comes from a quoted source.

Methods chosen by the builder (the tests leave them open):
  Hair strands  each strand runs from one edge of the square field to the
                opposite edge (left to right or top to bottom, chosen at
                random), with its entry and exit points uniform along those
                edges, so it always crosses the whole field. Coverage of a
                pixel is the overlap of the pixel's width with the strand's
                width, measured across the strand (area-preserving), and
                strands combine as 1 - prod(1 - c_i). HAIR_RGB and
                HAIR_WIDTH_MM are assumptions (a dark strand about 0.08 mm wide).
  detect_hair   luminance Y (linear) of each pixel against its neighbours
                q pixels away on both sides, along each of four directions
                (horizontal, vertical, two diagonals), for q = p, 2p, 3p with
                p = ceil(HAIR_WIDTH_MM x px_per_mm) + 1 (several distances,
                because optical blur widens a strand). A pixel is "strong"
                hair when, along at least one direction and distance, it is
                darker than the darker of its two neighbours by the factor
                HAIR_STRONG_RATIO. The mask then grows, up to p steps, into
                neighbouring pixels that pass the looser HAIR_WEAK_RATIO
                (hysteresis), to catch the blurred fringe of each strand.
                A dark line has skin on both sides; the edge of a lighter spot
                has skin on one side only, so the spot is never taken for hair.
                Ratios of nearby pixels do not change under smooth lighting.
  Tan blending  the spot's own coverage (disk_ramp, before contrast_scale)
                blends the skin's tanning factor T with T ** spot_tan_fraction,
                as the contract states.
  Patchy tan    a second texture made like round one's mottle (random
                Fourier sum, Gaussian spectrum, correlation MOTTLE_CORR_MM),
                drawn from tan_seed, fixed to the skin, scaled to SD
                tan_texture_sd over the unshifted, unrotated field.
  Rotation      the scene is defined in continuous skin coordinates, so a
                rotated capture is rendered exactly (no resampling): each
                Fourier component's wave vector is turned with the scene.
  Registration  masked normalised cross-correlation as round one (Padfield
                2012 form), generalised to a separate mask for each capture.
                Each mask keeps pixels beyond radius diameter / 2 + RING_GAP_MM
                of the frame centre and drops the pixels detect_hair() flags
                in that capture (the detector sees the outer pixels only, so
                nothing inside the gap can change the answer). Refused (None)
                when there is no texture, when the peak score is below
                MIN_REG_SCORE, or when the peak lies on the edge of the search
                window.
                "translation": integer-shift search up to MAX_REG_SHIFT_MM,
                3-point parabola per axis, angle 0.
                "rigid": the follow-up is turned back by a trial angle about
                the frame centre (bilinear resampling, pixels that fall outside
                the field are masked), then searched as "translation"; the
                angle with the highest peak score wins. Angles are searched at
                1 degree steps up to MAX_REG_ANGLE_DEG, then at 0.1 degree
                within 0.6 degree of the best, then a parabola through the
                best fine angle and its neighbours. The translation found on
                the turned image is turned forward to give the spot centre.
                Refused also when the best angle is at the edge of the range.

Run:  python3 experiments/registration_stress_sim.py --out data   (about 25 min on 4 cores)
Needs: Python 3.9+, numpy. Reuses round one (placement_sim.py) and drift_sim.py
by import, unchanged.
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
import placement_sim as p1  # noqa: E402
from drift_sim import _M, SKIN_RGB, WHITE_SPOT_RGB, blur, disk_ramp, rgb_to_lab  # noqa: E402,F401

# ---- constants --------------------------------------------------------------
DIAMETERS_MM = (2.0, 4.0)
SHIFT_MM = 0.5
RING_GAP_MM = p1.RING_GAP_MM
RING_WIDTH_MM = p1.RING_WIDTH_MM
INNER_FRACTION = p1.INNER_FRACTION
STICKER_SD_MM = p1.STICKER_SD_MM
NOISE_SD = p1.NOISE_SD
MOTTLE_SD = p1.MOTTLE_SD
MOTTLE_CORR_MM = p1.MOTTLE_CORR_MM
MOTTLE_COMPONENTS = p1.MOTTLE_COMPONENTS
BLUR_SD_MM = p1.BLUR_SD_MM
MAX_REG_SHIFT_MM = p1.MAX_REG_SHIFT_MM
MIN_REG_SCORE = p1.MIN_REG_SCORE

SCENARIOS = {"unchanged": (1.0, 1.0), "genuine_fading": (0.5, 1.0)}
PLACEMENTS = ("none", "ring_registration", "ring_registration_rigid", "sticker")
REGIONS = p1.REGIONS
HAIR_MASKS = ("none", "detected")

HAIR_RGB = (0.06, 0.045, 0.035)     # ASSUMPTION: a dark strand, far darker than skin
HAIR_WIDTH_MM = 0.08                # ASSUMPTION
SPOT_TAN_FRACTION = 0.0             # READING (test author): the spot does not tan
MAX_RING_EXCLUDED = 0.20            # plan C10
MAX_REJECTED_FRACTION = 0.10        # READING (test author)

HAIR_STRONG_RATIO = 0.85            # builder's detector settings
HAIR_WEAK_RATIO = 0.97
HAIR_GROW_STEPS = 1
MAX_REG_ANGLE_DEG = 12.0            # rigid search range, each way

# Disturbances: sizes are the TEST AUTHOR'S ASSUMPTIONS, not quoted figures.
DISTURBANCES = {
    "none": dict(family="none", level=0),
    "hair_2": dict(family="hair", level=2, hair_count=2),
    "hair_8": dict(family="hair", level=8, hair_count=8),
    "tan_2": dict(family="tan", level=2, tan_dL=-2.0),
    "tan_5": dict(family="tan", level=5, tan_dL=-5.0),
    "tan_patchy_5": dict(family="tan_patchy", level=5, tan_dL=-5.0, tan_texture_sd=0.03),
    "rotation_2": dict(family="rotation", level=2, rotation_deg=2.0),
    "rotation_5": dict(family="rotation", level=5, rotation_deg=5.0),
    "rotation_10": dict(family="rotation", level=10, rotation_deg=10.0),
    "gradient_5": dict(family="gradient", level=5, gradient=0.05),
    "gradient_20": dict(family="gradient", level=20, gradient=0.20),
    "vignetting_10": dict(family="vignetting", level=10, vignetting=0.10),
    "vignetting_20": dict(family="vignetting", level=20, vignetting=0.20),
    "combined": dict(family="combined", level=1, hair_count=2, tan_dL=-5.0,
                     tan_texture_sd=0.03, rotation_deg=5.0, gradient=0.20),
}


class CaptureRefused(Exception):
    """A capture whose reference ring or spot is too heavily masked to measure."""


# ---- geometry ---------------------------------------------------------------
field_size = p1.field_size


def _coords(diameter_mm, px_per_mm):
    return p1._coords(diameter_mm, px_per_mm)


def _grid(diameter_mm, px_per_mm):
    c = _coords(diameter_mm, px_per_mm)
    return c[None, :], c[:, None]           # x (columns), y (rows)


def _rot(theta_deg):
    """R as in the contract: (x, y) -> (x cos + y sin, -x sin + y cos), y down.
    Positive angles turn the scene counter-clockwise as displayed."""
    t = math.radians(theta_deg)
    return math.cos(t), math.sin(t)


# ---- textures in continuous skin coordinates --------------------------------
def _fourier_texture(diameter_mm, px_per_mm, sd, corr_mm, shift_mm, rotation_deg, rng_key):
    """1 + sd * (normalised random Fourier sum). A capture sees skin point
    p = R^-1 (x - shift); k . p = (R k) . (x - shift), so turning the scene turns
    each wave vector and the sum stays separable."""
    c = _coords(diameter_mm, px_per_mm)
    rng = np.random.default_rng(rng_key)
    k = rng.normal(0.0, 1.0 / corr_mm, size=(2, MOTTLE_COMPONENTS))
    phase = rng.uniform(0, 2 * math.pi, MOTTLE_COMPONENTS)

    def raw(kx, ky, sx, sy):
        a = np.exp(1j * np.outer(c - sy, ky))
        b = np.exp(1j * (np.outer(kx, c - sx) + phase[:, None]))
        return np.real(a @ b)

    base = raw(k[0], k[1], 0.0, 0.0)
    mu, s = base.mean(), base.std()
    co, si = _rot(rotation_deg)
    kx, ky = co * k[0] + si * k[1], -si * k[0] + co * k[1]
    sx, sy = p1._xy(shift_mm)
    field = raw(kx, ky, sx, sy)
    return 1.0 + sd * (field - mu) / s


def _mottle(diameter_mm, px_per_mm, mottle_sd, mottle_corr_mm, shift_mm, rotation_deg, seed):
    if rotation_deg == 0:
        return p1._mottle(diameter_mm, px_per_mm, mottle_sd, mottle_corr_mm, p1._xy(shift_mm), seed)
    return _fourier_texture(diameter_mm, px_per_mm, mottle_sd, mottle_corr_mm, shift_mm,
                            rotation_deg, [seed, 7])


def _tan_texture(diameter_mm, px_per_mm, sd, shift_mm, rotation_deg, tan_seed):
    return _fourier_texture(diameter_mm, px_per_mm, sd, MOTTLE_CORR_MM, shift_mm,
                            rotation_deg, [tan_seed, 13])


def _lstar_of_y(y):
    d = 6.0 / 29.0
    f = np.cbrt(y) if y > d ** 3 else y / (3 * d * d) + 4.0 / 29.0
    return 116 * f - 16


def _y_of_lstar(L):
    d = 6.0 / 29.0
    f = (L + 16) / 116
    return f ** 3 if f > d else 3 * d * d * (f - 4.0 / 29.0)


@lru_cache(maxsize=64)
def tan_gain(tan_dL):
    """One gain k on every channel with L*(k * SKIN_RGB) = L*(SKIN_RGB) + tan_dL."""
    y0 = float(_M[1] @ np.asarray(SKIN_RGB, float))
    return _y_of_lstar(_lstar_of_y(y0) + tan_dL) / y0


# ---- hair ---------------------------------------------------------------------
def hair_coverage(diameter_mm, *, px_per_mm=20, hair_count=0, hair_width_mm=HAIR_WIDTH_MM,
                  hair_seed=0):
    """Coverage in [0, 1] of hair_count straight strands crossing the whole field."""
    n = field_size(diameter_mm, px_per_mm)
    if hair_count <= 0:
        return np.zeros((n, n))
    x, y = _grid(diameter_mm, px_per_mm)
    half = n / px_per_mm / 2
    h = 0.5 / px_per_mm
    rng = np.random.default_rng([hair_seed, 17])
    free = np.ones((n, n))
    for _ in range(int(hair_count)):
        across = rng.random() < 0.5                 # left-right, else top-bottom
        a, b = rng.uniform(-half, half, 2)
        if across:
            p0, p1_ = np.array([-half, a]), np.array([half, b])
        else:
            p0, p1_ = np.array([a, -half]), np.array([b, half])
        t = (p1_ - p0) / np.linalg.norm(p1_ - p0)
        u = (x - p0[0]) * (-t[1]) + (y - p0[1]) * t[0]          # signed distance to the line
        w2 = hair_width_mm / 2
        c = np.clip(np.minimum(u + h, w2) - np.maximum(u - h, -w2), 0.0, None) * px_per_mm
        free *= 1.0 - np.clip(c, 0.0, 1.0)
    return 1.0 - free


def _luma(img):
    return img @ _M[1]


def _probe_px(px_per_mm):
    return int(math.ceil(HAIR_WIDTH_MM * px_per_mm)) + 1


def _hair_from_luma(Y, px_per_mm):
    d = _probe_px(px_per_mm)
    probes = (d, 2 * d, 3 * d)           # several distances: blur widens a strand
    P = np.pad(Y, 3 * d, mode="edge")
    n0, n1 = Y.shape
    o = 3 * d

    def at(oy, ox):
        return P[o + oy:o + oy + n0, o + ox:o + ox + n1]

    best = None
    for q in probes:
        for oy, ox in ((0, q), (q, 0), (q, q), (q, -q)):
            m = np.minimum(at(oy, ox), at(-oy, -ox))
            best = m if best is None else np.maximum(best, m)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(best > 0, Y / best, 1.0)
    hair = ratio < HAIR_STRONG_RATIO
    weak = ratio < HAIR_WEAK_RATIO
    for _ in range(HAIR_GROW_STEPS * d):  # hysteresis: grow into weakly dark neighbours
        g = hair.copy()
        g[1:] |= hair[:-1]
        g[:-1] |= hair[1:]
        g[:, 1:] |= hair[:, :-1]
        g[:, :-1] |= hair[:, 1:]
        g &= weak
        if np.array_equal(g, hair):
            break
        hair = g
    return hair


def detect_hair(img, diameter_mm, px_per_mm):
    """Hair pixels found from the image alone (see the module docstring)."""
    Y = _luma(np.asarray(img, float))
    if Y.shape != (field_size(diameter_mm, px_per_mm),) * 2:
        raise ValueError("image does not match the field for this diameter and px_per_mm")
    return _hair_from_luma(Y, px_per_mm)


# ---- scene ----------------------------------------------------------------------
def _scene(diameter_mm, *, px_per_mm, contrast_scale, diameter_scale, background, mottle_sd,
           mottle_corr_mm, shift_mm, seed, tan_dL, tan_texture_sd, tan_seed,
           spot_tan_fraction, rotation_deg, texture=None):
    """Steps 1 and 2 of the contract: the skin, the spot, tanning, geometry. No blur."""
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    if background not in p1.BACKGROUNDS:
        raise ValueError(f"background must be one of {p1.BACKGROUNDS}")
    sh = p1._xy(shift_mm)
    cov = disk_ramp(p1._radius(diameter_mm, px_per_mm, sh), px_per_mm, diameter_mm * diameter_scale)
    skin = np.asarray(SKIN_RGB, float)
    spot = np.asarray(WHITE_SPOT_RGB, float)
    img = skin + (contrast_scale * cov)[:, :, None] * (spot - skin)       # as round one
    if background == "mottled" and mottle_sd != 0:
        if texture is None:
            texture = _mottle(diameter_mm, px_per_mm, mottle_sd, mottle_corr_mm, sh,
                              rotation_deg, seed)
        img = img * texture[:, :, None]
    if tan_dL != 0 or tan_texture_sd != 0:
        T = tan_gain(float(tan_dL)) * np.ones_like(cov)
        if tan_texture_sd != 0:
            T = T * _tan_texture(diameter_mm, px_per_mm, tan_texture_sd, sh, rotation_deg, tan_seed)
        factor = (1.0 - cov) * T + cov * T ** spot_tan_fraction
        img = img * factor[:, :, None]
    return img


def _lighting(diameter_mm, px_per_mm, gradient, gradient_dir_deg, vignetting):
    x, y = _grid(diameter_mm, px_per_mm)
    n = field_size(diameter_mm, px_per_mm)
    W = n / px_per_mm
    phi = math.radians(gradient_dir_deg)
    u = x * math.cos(phi) + y * math.sin(phi)
    return (1 + gradient * u / W) * (1 - vignetting * (np.hypot(x, y) / (W / 2)) ** 2)


def _capture(scene, diameter_mm, *, px_per_mm, hair_count, hair_width_mm, hair_seed,
             gradient, gradient_dir_deg, vignetting, blur_sd_mm, noise_sd, noise_rng):
    img = scene
    if hair_count > 0:
        c = hair_coverage(diameter_mm, px_per_mm=px_per_mm, hair_count=hair_count,
                          hair_width_mm=hair_width_mm, hair_seed=hair_seed)[:, :, None]
        img = (1 - c) * img + c * np.asarray(HAIR_RGB, float)
    if gradient != 0 or vignetting != 0:
        img = img * _lighting(diameter_mm, px_per_mm, gradient, gradient_dir_deg, vignetting)[:, :, None]
    img = blur(img, px_per_mm, blur_sd_mm)
    if noise_sd > 0:
        img = img + noise_rng.normal(0.0, noise_sd, img.shape)
    return img


def render(diameter_mm, *, px_per_mm=20, contrast_scale=1.0, diameter_scale=1.0,
           background="uniform", mottle_sd=0.0, mottle_corr_mm=1.0, shift_mm=(0.0, 0.0),
           noise_sd=0.0, blur_sd_mm=0.0, seed=0,
           tan_dL=0.0, tan_texture_sd=0.0, tan_seed=0,
           spot_tan_fraction=SPOT_TAN_FRACTION,
           rotation_deg=0.0,
           hair_count=0, hair_width_mm=HAIR_WIDTH_MM, hair_seed=0,
           gradient=0.0, gradient_dir_deg=0.0, vignetting=0.0):
    """Synthetic capture, linear RGB (n, n, 3). Order: scene, geometry, hair,
    lighting, blur, noise (contract). Defaults reproduce placement_sim.render()."""
    sc = _scene(diameter_mm, px_per_mm=px_per_mm, contrast_scale=contrast_scale,
                diameter_scale=diameter_scale, background=background, mottle_sd=mottle_sd,
                mottle_corr_mm=mottle_corr_mm, shift_mm=shift_mm, seed=seed, tan_dL=tan_dL,
                tan_texture_sd=tan_texture_sd, tan_seed=tan_seed,
                spot_tan_fraction=spot_tan_fraction, rotation_deg=rotation_deg)
    return _capture(sc, diameter_mm, px_per_mm=px_per_mm, hair_count=hair_count,
                    hair_width_mm=hair_width_mm, hair_seed=hair_seed, gradient=gradient,
                    gradient_dir_deg=gradient_dir_deg, vignetting=vignetting,
                    blur_sd_mm=blur_sd_mm, noise_sd=noise_sd,
                    noise_rng=np.random.default_rng([seed, 11]))


# ---- measurement --------------------------------------------------------------
def _masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction):
    return p1._masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction)


def _measure_lab(lab, diameter_mm, px_per_mm, region, centre_mm, inner_fraction, exclude):
    s, ring = _masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction)
    if lab.shape[:2] != s.shape:
        raise ValueError("image does not match the field for this diameter and px_per_mm")
    if exclude is None:
        ws, wr = s, ring
        ring_ex = spot_ex = 0.0
    else:
        keep = ~np.asarray(exclude, dtype=bool)
        ws, wr = s * keep, ring * keep
        ring_ex = 1.0 - wr.sum() / ring.sum()
        spot_ex = 1.0 - ws.sum() / s.sum()
    out = {"ring_excluded": float(ring_ex), "spot_excluded": float(spot_ex)}
    if wr.sum() > 0:
        around = (lab * wr[:, :, None]).sum(axis=(0, 1)) / wr.sum()
    else:
        around = np.full(3, np.nan)
    if ws.sum() > 0:
        inside = (lab * ws[:, :, None]).sum(axis=(0, 1)) / ws.sum()
    else:
        inside = np.full(3, np.nan)
        out["spot_excluded"] = 1.0
    c = inside - around
    out.update({"L": float(c[0]), "a": float(c[1]), "b": float(c[2]),
                "ring_L": float(around[0]), "ring_a": float(around[1]), "ring_b": float(around[2])})
    return out


def measure(img, diameter_mm, px_per_mm, *, region="outline", centre_mm=(0, 0),
            inner_fraction=INNER_FRACTION, exclude=None):
    """Mean Lab in S minus mean Lab in ring R, absolute ring Lab, and the
    fractions of R and S left out by `exclude`."""
    _masks(diameter_mm, px_per_mm, region, centre_mm, inner_fraction)      # validate first
    return _measure_lab(rgb_to_lab(img), diameter_mm, px_per_mm, region, centre_mm,
                        inner_fraction, exclude)


def _check(m):
    if m["ring_excluded"] > MAX_RING_EXCLUDED or m["spot_excluded"] == 1.0:
        raise CaptureRefused(f"ring {m['ring_excluded']:.3f} masked, spot {m['spot_excluded']:.3f}")


def change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, region="outline",
               base_centre_mm=(0, 0), follow_centre_mm=(0, 0), inner_fraction=INNER_FRACTION,
               base_exclude=None, follow_exclude=None, channel="L"):
    mb = measure(base_img, diameter_mm, px_per_mm, region=region, centre_mm=base_centre_mm,
                 inner_fraction=inner_fraction, exclude=base_exclude)
    mf = measure(follow_img, diameter_mm, px_per_mm, region=region, centre_mm=follow_centre_mm,
                 inner_fraction=inner_fraction, exclude=follow_exclude)
    _check(mb)
    _check(mf)
    return p1._pct(mf[channel], mb[channel])


# ---- registration ---------------------------------------------------------------
@lru_cache(maxsize=64)
def _reg_setup(diameter_mm, px_per_mm):
    n = field_size(diameter_mm, px_per_mm)
    rmax = int(math.ceil(MAX_REG_SHIFT_MM * px_per_mm))
    size = p1._fft_len(n + rmax + 1)
    r = p1._radius(diameter_mm, px_per_mm, (0.0, 0.0))
    outer = r > diameter_mm / 2 + RING_GAP_MM
    outer.setflags(write=False)
    return n, rmax, size, outer


def _reg_hair(img_or_luma, diameter_mm, px_per_mm, *, luma=False):
    """Hair seen in the outer pixels only: the inside is replaced by a constant,
    so nothing within the spot and gap can change the flags."""
    _, _, _, outer = _reg_setup(diameter_mm, px_per_mm)
    Y = img_or_luma if luma else _luma(np.asarray(img_or_luma, float))
    Y = np.where(outer, Y, np.median(Y[outer]))
    return _hair_from_luma(Y, px_per_mm) & outer


def _corr(fu, fv, size):
    return np.fft.irfft2(fu * np.conj(fv), (size, size))


def _reg_base(base_L, base_mask, diameter_mm, px_per_mm):
    n, rmax, size, _ = _reg_setup(diameter_mm, px_per_mm)
    m = base_mask.astype(float)
    a = base_L * m
    ok = m.sum() > 1 and a[m > 0].std() > 1e-9
    return {"ok": ok, "fa": np.fft.rfft2(a, (size, size)),
            "fa2": np.fft.rfft2(a * base_L, (size, size)), "fm": np.fft.rfft2(m, (size, size))}


def _ncc_peak(pre, follow_L, follow_mask, diameter_mm, px_per_mm):
    """(score, iy, ix, ncc) over integer lags -rmax..rmax; ncc sorted by lag."""
    n, rmax, size, _ = _reg_setup(diameter_mm, px_per_mm)
    mb = follow_mask.astype(float)
    b = follow_L * mb
    fb = np.fft.rfft2(b, (size, size))
    fb2 = np.fft.rfft2(b * follow_L, (size, size))
    fmb = np.fft.rfft2(mb, (size, size))
    idx = np.r_[0:rmax + 1, size - rmax:size]
    sel = np.ix_(idx, idx)
    N = np.maximum(_corr(fmb, pre["fm"], size)[sel], 1.0)
    SF = _corr(fmb, pre["fa"], size)[sel]
    SFF = _corr(fmb, pre["fa2"], size)[sel]
    SG = _corr(fb, pre["fm"], size)[sel]
    SGG = _corr(fb2, pre["fm"], size)[sel]
    SFG = _corr(fb, pre["fa"], size)[sel]
    num = SFG - SF * SG / N
    den = (SFF - SF * SF / N) * (SGG - SG * SG / N)
    with np.errstate(invalid="ignore", divide="ignore"):
        ncc = np.where(den > 1e-12 * N * N, num / np.sqrt(np.abs(den)), -np.inf)
    lags = np.r_[0:rmax + 1, -rmax:0]
    order = np.argsort(lags)
    ncc = ncc[np.ix_(order, order)]
    iy, ix = np.unravel_index(np.argmax(ncc), ncc.shape)
    return float(ncc[iy, ix]), int(iy), int(ix), ncc


def _subpixel(ncc, iy, ix, rmax, px_per_mm):
    def vertex(l, c, r):
        d = l - 2 * c + r
        return 0.0 if d >= 0 else 0.5 * (l - r) / d
    peak = ncc[iy, ix]
    dy = iy - rmax + vertex(ncc[iy - 1, ix], peak, ncc[iy + 1, ix])
    dx = ix - rmax + vertex(ncc[iy, ix - 1], peak, ncc[iy, ix + 1])
    return float(dx / px_per_mm), float(dy / px_per_mm)


def _translate(pre, follow_L, follow_mask, diameter_mm, px_per_mm):
    n, rmax, size, _ = _reg_setup(diameter_mm, px_per_mm)
    score, iy, ix, ncc = _ncc_peak(pre, follow_L, follow_mask, diameter_mm, px_per_mm)
    if not math.isfinite(score) or score < MIN_REG_SCORE:
        return None
    if iy in (0, 2 * rmax) or ix in (0, 2 * rmax):
        return None
    dx, dy = _subpixel(ncc, iy, ix, rmax, px_per_mm)
    return {"dx": dx, "dy": dy, "angle_deg": 0.0, "score": score}


def _bilinear(img, py, px):
    """Sample img at fractional pixel indices; also returns which samples fell
    inside the field."""
    n0, n1 = img.shape
    inside = (py >= 0) & (py <= n0 - 1) & (px >= 0) & (px <= n1 - 1)
    y0 = np.clip(np.floor(py).astype(int), 0, n0 - 2)
    x0 = np.clip(np.floor(px).astype(int), 0, n1 - 2)
    fy, fx = np.clip(py - y0, 0, 1), np.clip(px - x0, 0, 1)
    v = (img[y0, x0] * (1 - fy) * (1 - fx) + img[y0, x0 + 1] * (1 - fy) * fx
         + img[y0 + 1, x0] * fy * (1 - fx) + img[y0 + 1, x0 + 1] * fy * fx)
    return v, inside


def _derotate(follow_L, follow_mask, diameter_mm, px_per_mm, angle_deg):
    """g(y) = follow(R y): the follow-up turned back by angle_deg about the frame
    centre. A sample counts only if all four of its source pixels are usable."""
    if angle_deg == 0:
        return follow_L, follow_mask
    _, _, _, outer = _reg_setup(diameter_mm, px_per_mm)
    x, y = _grid(diameter_mm, px_per_mm)
    co, si = _rot(angle_deg)
    X = x * co + y * si                       # R y, x component
    Yc = -x * si + y * co
    n = follow_L.shape[0]
    cpix = (n - 1) / 2.0
    pyi, pxi = Yc * px_per_mm + cpix, X * px_per_mm + cpix
    v, inside = _bilinear(follow_L, pyi, pxi)
    mk, _ = _bilinear(follow_mask.astype(float), pyi, pxi)
    return v, inside & (mk > 1 - 1e-9) & outer


def _rigid(pre, follow_L, follow_mask, diameter_mm, px_per_mm):
    n, rmax, size, _ = _reg_setup(diameter_mm, px_per_mm)
    cache = {}

    def score(a):
        a = round(float(a), 6)
        if a not in cache:
            g, gm = _derotate(follow_L, follow_mask, diameter_mm, px_per_mm, a)
            cache[a] = (_ncc_peak(pre, g, gm, diameter_mm, px_per_mm), g, gm)
        return cache[a][0][0]

    coarse = np.arange(-MAX_REG_ANGLE_DEG, MAX_REG_ANGLE_DEG + 0.5, 1.0)
    s = [score(a) for a in coarse]
    if not np.isfinite(np.max(s)):
        return None
    i = int(np.argmax(s))
    if i in (0, len(coarse) - 1):
        return None
    fine = coarse[i] + np.round(np.arange(-6, 7) * 0.1, 6)
    fs = [score(a) for a in fine]
    j = int(np.argmax(fs))
    best = float(fine[j])
    if 0 < j < len(fine) - 1:
        l, c, r = fs[j - 1], fs[j], fs[j + 1]
        d = l - 2 * c + r
        if d < 0:
            best = float(fine[j] + 0.1 * 0.5 * (l - r) / d)
    sc_best = score(best)
    if sc_best < fs[j]:                       # parabola overshot: keep the grid angle
        best = float(fine[j])
        sc_best = fs[j]
    (sc, iy, ix, ncc), g, gm = cache[round(best, 6)]
    if not math.isfinite(sc) or sc < MIN_REG_SCORE:
        return None
    if iy in (0, 2 * rmax) or ix in (0, 2 * rmax):
        return None
    tx, ty = _subpixel(ncc, iy, ix, rmax, px_per_mm)
    co, si = _rot(best)
    return {"dx": float(tx * co + ty * si), "dy": float(-tx * si + ty * co),
            "angle_deg": float(best), "score": float(sc)}


def _register_prepared(pre, follow_L, follow_mask, diameter_mm, px_per_mm, model):
    if not pre["ok"]:
        return None
    if model == "translation":
        return _translate(pre, follow_L, follow_mask, diameter_mm, px_per_mm)
    return _rigid(pre, follow_L, follow_mask, diameter_mm, px_per_mm)


def _models(model):
    if model not in ("translation", "rigid"):
        raise ValueError('model must be "translation" or "rigid"')


def register(base_img, follow_img, diameter_mm, px_per_mm, *, model="translation"):
    """Follow-up spot centre (dx, dy) in mm, angle and peak score, or None."""
    _models(model)
    _, _, _, outer = _reg_setup(diameter_mm, px_per_mm)
    bL = rgb_to_lab(base_img)[..., 0]
    fL = rgb_to_lab(follow_img)[..., 0]
    pre = _reg_base(bL, outer & ~_reg_hair(base_img, diameter_mm, px_per_mm),
                    diameter_mm, px_per_mm)
    fm = outer & ~_reg_hair(follow_img, diameter_mm, px_per_mm)
    return _register_prepared(pre, fL, fm, diameter_mm, px_per_mm, model)


def place(method, base_img, follow_img, diameter_mm, px_per_mm, *, true_shift_mm=(0, 0),
          sticker_sd_mm=STICKER_SD_MM, seed=0):
    """Estimated follow-up spot centre (dx, dy) in mm, or None when refused."""
    if method == "none":
        return (0.0, 0.0)
    if method == "sticker":
        return p1._sticker(true_shift_mm, sticker_sd_mm, seed)
    if method in ("ring_registration", "ring_registration_rigid"):
        r = register(base_img, follow_img, diameter_mm, px_per_mm,
                     model="translation" if method == "ring_registration" else "rigid")
        return None if r is None else (r["dx"], r["dy"])
    raise ValueError(f"method must be one of {PLACEMENTS}")


# ---- experiment -------------------------------------------------------------------
_RENDER_KEYS = ("hair_count", "tan_dL", "tan_texture_sd", "rotation_deg", "gradient", "vignetting")


def _mean(v):
    return float(np.mean(v)) if len(v) else None


def _sd(v):
    return float(np.std(v, ddof=1)) if len(v) > 1 else None


def run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, disturbances=tuple(DISTURBANCES),
        scenarios=tuple(SCENARIOS), shift_mm=SHIFT_MM, noise_sd=NOISE_SD, mottle_sd=MOTTLE_SD,
        blur_sd_mm=BLUR_SD_MM, sticker_sd_mm=STICKER_SD_MM):
    """One row per scenario x disturbance x diameter x placement x region x hair_mask.
    Mottled skin only. Every placement, region and mask is measured on the same
    captures within a scenario x disturbance x diameter."""
    for ds in disturbances:
        if ds not in DISTURBANCES:
            raise ValueError(f"unknown disturbance {ds!r}")
    for sc in scenarios:
        if sc not in SCENARIOS:
            raise ValueError(f"unknown scenario {sc!r}")
    rng = np.random.default_rng(seed)
    sh = (float(shift_mm), 0.0)
    combos = [(p, rg, hm) for p in PLACEMENTS for rg in REGIONS for hm in HAIR_MASKS]
    acc = {}
    for sc in scenarios:
        for ds in disturbances:
            for d in diameters:
                for c in combos:
                    acc[(sc, ds, d) + c] = {"err": [], "chg": [], "dL": [], "rdL": [], "cerr": [],
                                            "rex": [], "truth": [], "tring": [], "base": [],
                                            "rp": 0, "rm": 0}
    for _ in range(trials):
        tex_seed = int(rng.integers(2 ** 31))
        for d in diameters:
            _, _, _, outer = _reg_setup(d, px_per_mm)
            for ds in disturbances:
                w = {k: DISTURBANCES[ds].get(k, 0) for k in _RENDER_KEYS}
                hb_seed, hf_seed, tan_seed, st_seed = (int(v) for v in rng.integers(2 ** 31, size=4))
                g_dir = float(rng.uniform(0.0, 360.0)) if w["gradient"] else 0.0
                for sc in scenarios:
                    cs, dsc = SCENARIOS[sc]
                    common = dict(px_per_mm=px_per_mm, background="mottled", mottle_sd=mottle_sd,
                                  mottle_corr_mm=MOTTLE_CORR_MM, seed=tex_seed,
                                  spot_tan_fraction=SPOT_TAN_FRACTION)
                    base_scene = _scene(d, contrast_scale=1.0, diameter_scale=1.0,
                                        shift_mm=(0.0, 0.0), tan_dL=0.0, tan_texture_sd=0.0,
                                        tan_seed=0, rotation_deg=0.0, **common)
                    tan = dict(tan_dL=w["tan_dL"], tan_texture_sd=w["tan_texture_sd"], tan_seed=tan_seed)
                    true_follow_scene = _scene(d, contrast_scale=cs, diameter_scale=dsc, shift_mm=sh,
                                               rotation_deg=0.0, **tan, **common)
                    follow_scene = true_follow_scene if w["rotation_deg"] == 0 else \
                        _scene(d, contrast_scale=cs, diameter_scale=dsc, shift_mm=sh,
                               rotation_deg=w["rotation_deg"], **tan, **common)
                    nuis0 = dict(hair_width_mm=HAIR_WIDTH_MM, gradient=0.0, gradient_dir_deg=0.0,
                                 vignetting=0.0, blur_sd_mm=blur_sd_mm)
                    # TRUTH: everything real kept, every capture nuisance dropped, no noise.
                    tb = _capture(base_scene, d, px_per_mm=px_per_mm, hair_count=0, hair_seed=0,
                                  noise_sd=0.0, noise_rng=None, **nuis0)
                    tf = _capture(true_follow_scene, d, px_per_mm=px_per_mm, hair_count=0,
                                  hair_seed=0, noise_sd=0.0, noise_rng=None, **nuis0)
                    tbl, tfl = rgb_to_lab(tb), rgb_to_lab(tf)
                    truth = {}
                    for rg in REGIONS:
                        mb = _measure_lab(tbl, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION, None)
                        mf = _measure_lab(tfl, d, px_per_mm, rg, sh, INNER_FRACTION, None)
                        truth[rg] = (p1._pct(mf["L"], mb["L"]), mf["ring_L"] - mb["ring_L"])
                    # CAPTURES
                    base = _capture(base_scene, d, px_per_mm=px_per_mm, hair_count=w["hair_count"],
                                    hair_seed=hb_seed, noise_sd=noise_sd, noise_rng=rng, **nuis0)
                    foll = _capture(follow_scene, d, px_per_mm=px_per_mm, hair_count=w["hair_count"],
                                    hair_width_mm=HAIR_WIDTH_MM, hair_seed=hf_seed,
                                    gradient=w["gradient"], gradient_dir_deg=g_dir,
                                    vignetting=w["vignetting"], blur_sd_mm=blur_sd_mm,
                                    noise_sd=noise_sd, noise_rng=rng)
                    blab, flab = rgb_to_lab(base), rgb_to_lab(foll)
                    pre = _reg_base(blab[..., 0], outer & ~_reg_hair(base, d, px_per_mm), d, px_per_mm)
                    fmask = outer & ~_reg_hair(foll, d, px_per_mm)
                    est = {"none": (0.0, 0.0), "sticker": p1._sticker(sh, sticker_sd_mm, st_seed)}
                    for p, model in (("ring_registration", "translation"),
                                     ("ring_registration_rigid", "rigid")):
                        r = _register_prepared(pre, flab[..., 0], fmask, d, px_per_mm, model)
                        est[p] = None if r is None else (r["dx"], r["dy"])
                    excl = {"none": (None, None),
                            "detected": (detect_hair(base, d, px_per_mm), detect_hair(foll, d, px_per_mm))}
                    for rg in REGIONS:
                        for hm in HAIR_MASKS:
                            mb = _measure_lab(blab, d, px_per_mm, rg, (0.0, 0.0), INNER_FRACTION,
                                              excl[hm][0])
                            for p in PLACEMENTS:
                                a = acc[(sc, ds, d, p, rg, hm)]
                                a["truth"].append(truth[rg][0])
                                a["tring"].append(truth[rg][1])
                                if math.isfinite(mb["L"]):
                                    a["base"].append(mb["L"])
                                e = est[p]
                                if e is None:
                                    a["rp"] += 1
                                    continue
                                mf = _measure_lab(flab, d, px_per_mm, rg, e, INNER_FRACTION, excl[hm][1])
                                try:
                                    _check(mb)
                                    _check(mf)
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
    rows = []
    for sc in scenarios:
        for ds in disturbances:
            for d in diameters:
                for p, rg, hm in combos:
                    a = acc[(sc, ds, d, p, rg, hm)]
                    rows.append({
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
                        "trials": trials, "rejected": a["rp"] + a["rm"],
                        "rejected_placement": a["rp"], "rejected_mask": a["rm"],
                        "noise_sd": noise_sd, "mottle_sd": mottle_sd, "blur_sd_mm": blur_sd_mm,
                        "sticker_sd_mm": sticker_sd_mm, "px_per_mm": px_per_mm,
                    })
    return rows


# ---- target (plan section 4, on error against truth) -------------------------------
def _num(v):
    if v is None or v == "":
        return None
    return float(v)


def evaluate_stress_target(rows, *, diameter_mm=2.0):
    idx, keys = {}, []
    for r in rows:
        if float(r["diameter_mm"]) != float(diameter_mm):
            continue
        k = (r["disturbance"], r["placement"], r["region"], r["hair_mask"])
        idx[(r["scenario"],) + k] = r
        if k not in keys:
            keys.append(k)

    def get(sc, k):
        if (sc,) + k not in idx:
            raise ValueError(f"required row missing: {sc}, {k} at {diameter_mm} mm")
        return idx[(sc,) + k]

    out = {}
    for k in keys:
        un, gf = get("unchanged", k), get("genuine_fading", k)
        b, s, g = _num(un["bias_pct_points"]), _num(un["sd_error_pct_points"]), _num(gf["bias_pct_points"])
        e = {"bias_ok": b is not None and abs(b) <= 2.0,
             "sd_ok": s is not None and s <= 1.0,
             "sensitivity_ok": g is not None and abs(g) <= 2.0,
             "acceptance_ok": all(_num(r["rejected"]) <= MAX_REJECTED_FRACTION * _num(r["trials"])
                                  for r in (un, gf))}
        e["passes"] = all(e.values())
        out[k] = e
    return out


def breaking_levels(evaluation):
    groups = {}
    for (ds, p, rg, hm), e in evaluation.items():
        w = DISTURBANCES[ds]
        groups.setdefault((w["family"], p, rg, hm), []).append((w["level"], e["passes"]))
    out = {}
    for k, v in groups.items():
        failing = sorted(lv for lv, ok in v if not ok)
        out[k] = failing[0] if failing else None
    return out


# ---- output --------------------------------------------------------------------------
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


def run_parallel(*, seed, disturbances, jobs=1, **kw):
    """run() once per disturbance, each with the same seed, in parallel
    processes; rows in run()'s order. Reproducible whatever the number of jobs."""
    tasks = [dict(kw, seed=seed, disturbances=(ds,)) for ds in disturbances]
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(min(jobs, len(tasks))) as pool:
            parts = pool.map(_run_one, tasks)
    else:
        parts = [_run_one(t) for t in tasks]
    rows = [r for part in parts for r in part]
    so = {sc: i for i, sc in enumerate(SCENARIOS)}
    do = {ds: i for i, ds in enumerate(disturbances)}
    rows.sort(key=lambda r: (so[r["scenario"]], do[r["disturbance"]]))   # stable
    return rows


def target_rows(evaluation, levels):
    out = []
    for (ds, p, rg, hm), e in evaluation.items():
        out.append({"kind": "disturbance", "name": ds, "placement": p, "region": rg,
                    "hair_mask": hm, **{k: e[k] for k in
                                        ("bias_ok", "sd_ok", "sensitivity_ok", "acceptance_ok", "passes")},
                    "breaking_level": ""})
    for (fam, p, rg, hm), lv in levels.items():
        out.append({"kind": "family", "name": fam, "placement": p, "region": rg, "hair_mask": hm,
                    "bias_ok": "", "sd_ok": "", "sensitivity_ok": "", "acceptance_ok": "",
                    "passes": "", "breaking_level": "none_fail" if lv is None else lv})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="data")
    ap.add_argument("--name", default="registration_stress_results.csv")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--diameters", type=float, nargs="+", default=list(DIAMETERS_MM))
    ap.add_argument("--disturbances", nargs="+", default=list(DISTURBANCES))
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    t0 = time.perf_counter()
    rows = run_parallel(seed=a.seed, trials=a.trials, px_per_mm=a.px_per_mm,
                        diameters=tuple(a.diameters), disturbances=tuple(a.disturbances),
                        jobs=a.jobs)
    out = Path(a.out) / a.name
    write_csv(out, rows)
    ev = evaluate_stress_target(rows, diameter_mm=2.0)
    lv = breaking_levels(ev)
    tgt = Path(a.out) / a.name.replace("_results.csv", "_target.csv")
    write_csv(tgt, target_rows(ev, lv))
    print(f"registration stress sim: {len(rows)} rows, {a.trials} trials, {a.px_per_mm} px/mm; "
          f"{time.perf_counter() - t0:.1f} s; wrote {out} and {tgt}")


if __name__ == "__main__":
    main()
