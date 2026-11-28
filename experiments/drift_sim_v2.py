#!/usr/bin/env python3
"""Drift simulation v2: gradients, vignetting, glare, tone curves, changed spots,
and the L*, a*, b* and CIEDE2000 channels in absolute units.

SIMULATION ONLY. Synthetic disks on synthetic texture. No patient data, and no
image file is ever read. It tests the measuring method, not any treatment.

Plan: content/measurement-tool-plan.md, section 5 rung 1 (task T4). Contract and
tests: experiments/tests/test_drift_sim_v2.py (written first, not edited here).
Scene constants, the mottle texture, the reference ring and the Lab conversion
are imported unchanged from experiments/drift_sim.py.

Factors are varied ONE AT A TIME from the baseline (no gradient, no vignette,
linear capture, no glare, unchanged spot); each is crossed with every drift,
background, diameter, correction and channel.

Run:  python3 experiments/drift_sim_v2.py --out data
Needs: Python 3.9+, numpy.
"""
import argparse
import csv
import math
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

import drift_sim as v1
from drift_sim import (BACKGROUNDS, BLUR_SD_MM, BROWN_SPOT_RGB, DIAMETERS_MM, DRIFTS,
                       MOTTLE_CORR_MM, MOTTLE_SD, NOISE_SD, RING_GAP_MM, RING_WIDTH_MM,
                       SKIN_RGB, SPOTS, WHITE_SPOT_RGB, blur, disk_ramp, mottle, pct_change,
                       rgb_to_lab)

__all__ = ["DIAMETERS_MM", "SKIN_RGB", "WHITE_SPOT_RGB", "BROWN_SPOT_RGB", "DRIFTS",
           "CHANNELS", "GRADIENTS", "GRADIENT_GRID", "VIGNETTES", "TONES", "CHANGES",
           "GLARE_CASES", "render", "rgb_to_lab", "ciede2000", "glare_mask",
           "measure_contrast", "change_units", "change_pct", "gradient_limit", "run"]

# ---- tables -----------------------------------------------------------------
CHANNELS = ("L", "a", "b", "dE")
GRADIENTS = (0.0, 0.05, 0.10, 0.20)            # end to end, fraction (plan: 5 % and 20 %)
GRADIENT_GRID = tuple(round(0.01 * k, 2) for k in range(0, 41))   # 0.00 .. 0.40
VIGNETTES = (0.0, 0.10, 0.30)                  # fall-off at the field corners
TONES = ("linear", "gamma22", "srgb")
# change name -> (contrast_scale, spot_scale)
CHANGES = {
    "unchanged": (1.0, 1.0),
    "half_contrast": (0.5, 1.0),
    "matched": (0.0, 1.0),
    "overshoot": (-1 / 3, 1.0),
    "shrink": (1.0, 0.7),
}
# glare name -> (where, radius_mm, level added to every channel). Level 1.0
# saturates: specular reflection from a flash or ring light is brighter than
# any skin. Non-saturating glare is NOT modelled (see glare_mask).
GLARE_CASES = {
    "spot_r0.5mm": ("spot", 0.5, 1.0),
    "ring_r0.5mm": ("ring", 0.5, 1.0),
    "ring_r0.75mm": ("ring", 0.75, 1.0),
}
CORRECTIONS = ("none", "ring_white")
RING_MASK_LIMIT = 0.20                         # plan C10
_LAB_INDEX = {"L": 0, "a": 1, "b": 2}


# ---- geometry ---------------------------------------------------------------
def _coords(n, px_per_mm):
    """Pixel-centre x (columns) and y (rows) in mm from the field centre."""
    c = (np.arange(n) + 0.5 - n / 2) / px_per_mm
    return c[None, :], c[:, None]


def lighting_multiplier(n, px_per_mm, gradient=0.0, vignette=0.0):
    """Neutral lighting field (n, n), fixed in the image frame."""
    x, y = _coords(n, px_per_mm)
    H = n / (2 * px_per_mm)
    m = (1 + gradient * x / (2 * H)) * np.ones((n, 1))
    if vignette:
        m = m * (1 - vignette * (x ** 2 + y ** 2) / (2 * H ** 2))
    return m


def glare_disc(n, px_per_mm, diameter_mm, glare):
    """Bool (n, n): pixel centres within radius_mm of the glare centre."""
    if glare is None:
        return np.zeros((n, n), bool)
    where, radius_mm, _ = glare
    if where == "spot":
        x0 = 0.0
    elif where == "ring":
        x0 = diameter_mm / 2 + RING_GAP_MM + RING_WIDTH_MM / 2
    else:
        raise ValueError("glare 'where' must be 'spot' or 'ring'")
    x, y = _coords(n, px_per_mm)
    return np.hypot(x - x0, y) <= radius_mm


def tone_encode(img, tone):
    if tone == "linear":
        return img
    if tone == "gamma22":
        return img ** (1 / 2.2)
    if tone == "srgb":
        return np.where(img <= 0.0031308, 12.92 * img, 1.055 * img ** (1 / 2.4) - 0.055)
    raise ValueError(f"tone must be one of {TONES}")


# ---- scene ------------------------------------------------------------------
def _scene(diameter_mm, *, px_per_mm, spot, contrast_scale, spot_scale, background,
           mottle_sd, mottle_corr_mm, shift_mm, seed, texture=None):
    """Skin, mottle and spot, moved by shift_mm; no lighting, no blur."""
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    if spot not in SPOTS:
        raise ValueError(f"spot must be one of {SPOTS}")
    if background not in BACKGROUNDS:
        raise ValueError(f"background must be one of {BACKGROUNDS}")
    c, c0, _, _ = v1._geometry(diameter_mm, px_per_mm)
    X, Y = np.meshgrid(c, c)
    cov = disk_ramp(np.hypot(X - (c0 + shift_mm), Y - c0), px_per_mm, diameter_mm * spot_scale)
    skin = np.asarray(SKIN_RGB, float)
    target = np.asarray(WHITE_SPOT_RGB if spot == "white" else BROWN_SPOT_RGB, float)
    img = skin + (contrast_scale * cov)[:, :, None] * (target - skin)
    if background == "mottled" and mottle_sd != 0:
        if texture is None:
            texture = mottle(diameter_mm, px_per_mm, mottle_sd=mottle_sd,
                             mottle_corr_mm=mottle_corr_mm, shift_mm=shift_mm, seed=seed)
        img = img * texture[:, :, None]
    return img


def _finish(img, px_per_mm, blur_sd_mm, noise_sd, rng, tone):
    """blur -> capture noise -> clip to [0, 1] -> tone curve."""
    img = blur(img, px_per_mm, blur_sd_mm)
    if noise_sd > 0:
        img = img + rng.normal(0.0, noise_sd, img.shape)
    return tone_encode(np.clip(img, 0.0, 1.0), tone)


def render(diameter_mm, *, px_per_mm=20, spot="white", contrast_scale=1.0,
           background="uniform", mottle_sd=0.0, mottle_corr_mm=1.0, shift_mm=0.0,
           exposure_gain=1.0, wb_gains=(1.0, 1.0, 1.0), noise_sd=0.0, blur_sd_mm=0.0,
           seed=0, spot_scale=1.0, gradient=0.0, vignette=0.0, glare=None,
           tone="linear", return_glare=False):
    """Synthetic capture (n, n, 3), centred on the measuring outline.

    Order: scene -> lighting (drift gains, gradient, vignette) -> glare added
    -> blur -> noise -> clip -> tone curve.
    """
    if tone not in TONES:
        raise ValueError(f"tone must be one of {TONES}")
    img = _scene(diameter_mm, px_per_mm=px_per_mm, spot=spot, contrast_scale=contrast_scale,
                 spot_scale=spot_scale, background=background, mottle_sd=mottle_sd,
                 mottle_corr_mm=mottle_corr_mm, shift_mm=shift_mm, seed=seed)
    n = img.shape[0]
    gains = exposure_gain * np.asarray(wb_gains, float)
    if gradient or vignette:
        img = img * lighting_multiplier(n, px_per_mm, gradient, vignette)[:, :, None]
    img = img * gains
    truth = glare_disc(n, px_per_mm, diameter_mm, glare)
    if glare is not None:
        img = img + (glare[2] * truth)[:, :, None]
    out = _finish(img, px_per_mm, blur_sd_mm, noise_sd, np.random.default_rng([seed, 11]), tone)
    return (out, truth) if return_glare else out


# ---- colour science ---------------------------------------------------------
def ciede2000(lab1, lab2):
    """CIEDE2000 (kL = kC = kH = 1), after Sharma, Wu and Dalal (2005)."""
    L1, a1, b1 = (float(v) for v in np.asarray(lab1, float).reshape(-1)[:3])
    L2, a2, b2 = (float(v) for v in np.asarray(lab2, float).reshape(-1)[:3])
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cbar7 = ((C1 + C2) / 2) ** 7
    G = 0.5 * (1 - math.sqrt(Cbar7 / (Cbar7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)

    def hue(b, ap):
        return 0.0 if (b == 0 and ap == 0) else math.degrees(math.atan2(b, ap)) % 360

    h1p, h2p = hue(b1, a1p), hue(b2, a2p)
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180:
            dhp -= 360
        elif dhp < -180:
            dhp += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dtheta = 30 * math.exp(-((hbp - 275) / 25) ** 2)
    Cbp7 = Cbp ** 7
    RC = 2 * math.sqrt(Cbp7 / (Cbp7 + 25.0 ** 7))
    SL = 1 + 0.015 * (Lbp - 50) ** 2 / math.sqrt(20 + (Lbp - 50) ** 2)
    SC = 1 + 0.045 * Cbp
    SH = 1 + 0.015 * Cbp * T
    RT = -math.sin(math.radians(2 * dtheta)) * RC
    tL, tC, tH = dLp / SL, dCp / SC, dHp / SH
    return math.sqrt(max(0.0, tL * tL + tC * tC + tH * tH + RT * tC * tH))


# ---- glare mask -------------------------------------------------------------
def glare_mask(img):
    """True where any channel is clipped at 1.0.

    Clipped pixels carry no colour information, and in these renders only glare
    reaches 1.0. This mask cannot see glare that does not saturate.
    """
    return (np.asarray(img) >= 1.0).any(axis=-1)


_glare_mask_fn = glare_mask      # measure_contrast's keyword argument shares the name


# ---- measurement ------------------------------------------------------------
@lru_cache(maxsize=64)
def _measure_box(diameter_mm, px_per_mm):
    _, _, mask, ring = v1._geometry(diameter_mm, px_per_mm)
    rows, cols = np.nonzero((mask > 0) | (ring > 0))
    return (slice(int(rows.min()), int(rows.max()) + 1), slice(int(cols.min()), int(cols.max()) + 1))


def measure_contrast(img, diameter_mm, px_per_mm, *, correction="none", glare_mask=False):
    """Mean Lab inside the centred outline minus mean Lab in the ring, plus dE."""
    if correction not in CORRECTIONS:
        raise ValueError(f"correction must be one of {CORRECTIONS}")
    _, _, mask, ring = v1._geometry(diameter_mm, px_per_mm)
    if img.shape[:2] != mask.shape:
        raise ValueError("image does not match the field for this diameter and px_per_mm")
    # Only the outline and the ring are measured: crop to their bounding box.
    box = _measure_box(diameter_mm, px_per_mm)
    img, mask, ring = img[box], mask[box], ring[box]
    spot_w, ring_w = mask, ring
    spot_ex = ring_ex = 0.0
    if glare_mask:
        keep = ~_glare_mask_fn(img)
        spot_w, ring_w = mask * keep, ring * keep
        ring_ex = 1.0 - ring_w.sum() / ring.sum()
        spot_ex = 1.0 - spot_w.sum() / mask.sum()
        if ring_ex > RING_MASK_LIMIT:
            raise ValueError(f"ring {100 * ring_ex:.1f} % masked (> 20 %): refused (plan C10)")
        if spot_w.sum() <= 0:
            raise ValueError("whole spot masked: refused")
    if correction == "ring_white":
        img = img / ((img * ring_w[:, :, None]).sum(axis=(0, 1)) / ring_w.sum())
    lab = rgb_to_lab(img)
    inside = (lab * spot_w[:, :, None]).sum(axis=(0, 1)) / spot_w.sum()
    around = (lab * ring_w[:, :, None]).sum(axis=(0, 1)) / ring_w.sum()
    c = inside - around
    return {"L": float(c[0]), "a": float(c[1]), "b": float(c[2]),
            "dE": float(ciede2000(inside, around)),
            "spot_excluded_frac": float(spot_ex), "ring_excluded_frac": float(ring_ex)}


def change_units(base_img, follow_img, diameter_mm, px_per_mm, *, channel="L",
                 correction="none", glare_mask=False):
    if channel not in CHANNELS:
        raise ValueError(f"channel must be one of {CHANNELS}")
    cb = measure_contrast(base_img, diameter_mm, px_per_mm, correction=correction,
                          glare_mask=glare_mask)[channel]
    cf = measure_contrast(follow_img, diameter_mm, px_per_mm, correction=correction,
                          glare_mask=glare_mask)[channel]
    return cf - cb


def change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, channel="L",
               correction="none", glare_mask=False):
    if channel not in CHANNELS:
        raise ValueError(f"channel must be one of {CHANNELS}")
    cb = measure_contrast(base_img, diameter_mm, px_per_mm, correction=correction,
                          glare_mask=glare_mask)[channel]
    cf = measure_contrast(follow_img, diameter_mm, px_per_mm, correction=correction,
                          glare_mask=glare_mask)[channel]
    return pct_change(cf, cb)


def gradient_limit(diameter_mm, px_per_mm=20, *, limit_pct=1.0, grid=GRADIENT_GRID,
                   channel="L", correction="ring_white", **render_kw):
    """Smallest gradient in grid whose false change exceeds limit_pct; None if none."""
    base = render(diameter_mm, px_per_mm=px_per_mm, **render_kw)
    for g in grid:
        follow = render(diameter_mm, px_per_mm=px_per_mm, gradient=g, **render_kw)
        if abs(change_pct(base, follow, diameter_mm, px_per_mm, channel=channel,
                          correction=correction)) > limit_pct:
            return g
    return None


# ---- experiment -------------------------------------------------------------
def _settings():
    """(gradient, vignette, tone, glare, change) settings, one factor at a time."""
    base = dict(gradient=0.0, vignette=0.0, tone="linear", glare="none", change="unchanged")
    out = [dict(base)]
    out += [dict(base, gradient=float(g)) for g in GRADIENTS if g != 0.0]
    out += [dict(base, vignette=float(v)) for v in VIGNETTES if v != 0.0]
    out += [dict(base, tone=t) for t in TONES if t != "linear"]
    out += [dict(base, glare=name) for name in GLARE_CASES]
    out += [dict(base, change=c) for c in CHANGES if c != "unchanged"]
    return out


def _nanmean(a):
    return float(np.mean(a)) if len(a) else float("nan")


def _masks_for(st):
    return (False, True) if st["glare"] != "none" else (False,)


def _trial(t, cfg):
    """One trial: its own generator, seeded by (seed, trial index), so trials can
    run in any order or in parallel and give the same result."""
    (seed, px_per_mm, diameters, shifts, drifts, backgrounds, spots, noise_sd,
     mottle_sd, blur_sd_mm) = cfg
    rng = np.random.default_rng([seed, t])
    settings = _settings()
    acc = {}

    def slot(k):
        if k not in acc:
            acc[k] = {"pct": [], "units": [], "base": [], "recall": [], "precision": [],
                      "rejected": 0}
        return acc[k]

    tex_seed = int(rng.integers(2 ** 31))      # one skin texture per trial
    for d in diameters:
        n = v1.field_size(d, px_per_mm)
        light = {(0.0, 0.0): None}
        for g in GRADIENTS:
            light[(float(g), 0.0)] = lighting_multiplier(n, px_per_mm, g, 0.0)
        for v in VIGNETTES:
            light[(0.0, float(v))] = lighting_multiplier(n, px_per_mm, 0.0, v)
        # glare disc, added after lighting and before blur; blur is linear
        glare_truth = {nm: glare_disc(n, px_per_mm, d, gc) for nm, gc in GLARE_CASES.items()}
        glare_add = {nm: blur(np.repeat((GLARE_CASES[nm][2] * t)[:, :, None], 3, axis=2),
                              px_per_mm, blur_sd_mm) for nm, t in glare_truth.items()}
        textures = ({s: mottle(d, px_per_mm, mottle_sd=mottle_sd, mottle_corr_mm=MOTTLE_CORR_MM,
                               shift_mm=s, seed=tex_seed) for s in set(shifts) | {0.0}}
                    if mottle_sd != 0 else {})
        for sp in spots:
            for bg in backgrounds:
                lit_cache = {}

                def lit(s, change, gv):
                    """blur(scene x lighting field), before drift gains and glare."""
                    k = (s, change, gv)
                    if k not in lit_cache:
                        cs, ss = CHANGES[change]
                        img = _scene(d, px_per_mm=px_per_mm, spot=sp, contrast_scale=cs,
                                     spot_scale=ss, background=bg, mottle_sd=mottle_sd,
                                     mottle_corr_mm=MOTTLE_CORR_MM, shift_mm=s, seed=tex_seed,
                                     texture=textures.get(s))
                        m = light[gv]
                        if m is not None:
                            img = img * m[:, :, None]
                        lit_cache[k] = blur(img, px_per_mm, blur_sd_mm)
                    return lit_cache[k]

                base_lin = _finish(lit(0.0, "unchanged", (0.0, 0.0)), px_per_mm, 0.0,
                                   noise_sd, rng, "linear")
                base_tone = {t: tone_encode(base_lin, t) for t in TONES}
                cb_cache = {}

                def cbase(tone, co, gm):
                    k = (tone, co, gm)
                    if k not in cb_cache:
                        cb_cache[k] = measure_contrast(base_tone[tone], d, px_per_mm,
                                                       correction=co, glare_mask=gm)
                    return cb_cache[k]

                for s in shifts:
                    for dr in drifts:
                        gain, wb = DRIFTS[dr]
                        gains = gain * np.asarray(wb, float)
                        for i, st in enumerate(settings):
                            img = lit(s, st["change"], (st["gradient"], st["vignette"])) * gains
                            if st["glare"] != "none":
                                img = img + glare_add[st["glare"]]
                            foll = _finish(img, px_per_mm, 0.0, noise_sd, rng, st["tone"])
                            for gm in _masks_for(st):
                                if gm:
                                    flagged = glare_mask(foll)
                                    truth = glare_truth[st["glare"]]
                                    tp = float((flagged & truth).sum())
                                    rec = tp / truth.sum()
                                    prec = tp / flagged.sum() if flagged.any() else float("nan")
                                for co in CORRECTIONS:
                                    try:
                                        cb = cbase(st["tone"], co, gm)
                                        cf = measure_contrast(foll, d, px_per_mm,
                                                              correction=co, glare_mask=gm)
                                    except ValueError:
                                        cb = cf = None
                                    for ch in CHANNELS:
                                        a = slot((sp, bg, d, s, dr, i, gm, co, ch))
                                        if gm:
                                            a["recall"].append(rec)
                                            a["precision"].append(prec)
                                        if cb is None:
                                            a["rejected"] += 1
                                            continue
                                        try:
                                            p = pct_change(cf[ch], cb[ch])
                                        except ZeroDivisionError:
                                            a["rejected"] += 1
                                            continue
                                        a["pct"].append(p)
                                        a["units"].append(cf[ch] - cb[ch])
                                        a["base"].append(cb[ch])
    return acc


def run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, shifts=(0.0,),
        drifts=tuple(DRIFTS), backgrounds=("uniform", "mottled"), spots=("white",),
        noise_sd=NOISE_SD, mottle_sd=MOTTLE_SD, blur_sd_mm=BLUR_SD_MM, workers=1):
    """One row per spot x background x diameter x shift x drift x setting x
    glare_mask x correction x channel. See the test file for the contract."""
    settings = _settings()
    masks_for = _masks_for

    # true change: noise-free, unshifted, undrifted, uniform, linear, glare-free
    true_pct = {}
    for sp in spots:
        for d in diameters:
            b0 = _finish(_scene(d, px_per_mm=px_per_mm, spot=sp, contrast_scale=1.0,
                                spot_scale=1.0, background="uniform", mottle_sd=0.0,
                                mottle_corr_mm=MOTTLE_CORR_MM, shift_mm=0.0, seed=0),
                         px_per_mm, blur_sd_mm, 0.0, None, "linear")
            cb = measure_contrast(b0, d, px_per_mm)
            for cname, (cs, ss) in CHANGES.items():
                f0 = _finish(_scene(d, px_per_mm=px_per_mm, spot=sp, contrast_scale=cs,
                                    spot_scale=ss, background="uniform", mottle_sd=0.0,
                                    mottle_corr_mm=MOTTLE_CORR_MM, shift_mm=0.0, seed=0),
                             px_per_mm, blur_sd_mm, 0.0, None, "linear")
                cf = measure_contrast(f0, d, px_per_mm)
                for ch in CHANNELS:
                    if cname == "unchanged":
                        true_pct[(sp, d, cname, ch)] = 0.0
                        continue
                    try:
                        true_pct[(sp, d, cname, ch)] = pct_change(cf[ch], cb[ch])
                    except ZeroDivisionError:
                        true_pct[(sp, d, cname, ch)] = float("nan")


    cfg = (seed, px_per_mm, tuple(diameters), tuple(shifts), tuple(drifts),
           tuple(backgrounds), tuple(spots), noise_sd, mottle_sd, blur_sd_mm)
    if workers > 1 and trials > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as ex:
            parts = list(ex.map(_trial, range(trials), [cfg] * trials))
    else:
        parts = [_trial(t, cfg) for t in range(trials)]
    acc = {}
    for part in parts:                     # merged in trial order
        for k, a in part.items():
            m = acc.setdefault(k, {"pct": [], "units": [], "base": [], "recall": [],
                                   "precision": [], "rejected": 0})
            for f in ("pct", "units", "base", "recall", "precision"):
                m[f].extend(a[f])
            m["rejected"] += a["rejected"]

    rows = []
    nan = float("nan")
    for sp in spots:
        for bg in backgrounds:
            for d in diameters:
                for s in shifts:
                    for dr in drifts:
                        for i, st in enumerate(settings):
                            for gm in masks_for(st):
                                for co in CORRECTIONS:
                                    for ch in CHANNELS:
                                        a = acc[(sp, bg, d, s, dr, i, gm, co, ch)]
                                        tp = true_pct[(sp, d, st["change"], ch)]
                                        pct = np.array(a["pct"])
                                        units = np.array(a["units"])
                                        ok = len(pct) > 0
                                        sd = float(units.std(ddof=1)) if len(units) > 1 else nan
                                        rows.append({
                                            "spot": sp, "background": bg, "diameter_mm": float(d),
                                            "shift_mm": float(s), "drift": dr,
                                            "gradient": st["gradient"], "vignette": st["vignette"],
                                            "tone": st["tone"], "glare": st["glare"],
                                            "glare_mask": bool(gm), "change": st["change"],
                                            "correction": co, "channel": ch,
                                            "true_change_pct": tp,
                                            "mean_measured_change_pct": _nanmean(pct),
                                            "signed_bias_pct_points": (float((pct - tp).mean())
                                                                       if ok else nan),
                                            "mean_abs_error_pct_points": (float(np.abs(pct - tp).mean())
                                                                          if ok else nan),
                                            "baseline_contrast_units": _nanmean(a["base"]),
                                            "mean_change_units": _nanmean(units),
                                            "sd_change_units": sd,
                                            "sdc_units": 1.96 * sd,
                                            "glare_recall": (_nanmean(a["recall"]) if gm else nan),
                                            "glare_precision": (float(np.nanmean(a["precision"]))
                                                                if gm and not all(map(math.isnan, a["precision"]))
                                                                else nan),
                                            "trials": int(trials), "rejected": int(a["rejected"]),
                                            "px_per_mm": px_per_mm, "noise_sd": float(noise_sd),
                                            "mottle_sd": float(mottle_sd) if bg == "mottled" else 0.0,
                                            "blur_sd_mm": float(blur_sd_mm),
                                        })
    return rows


def write_csv(path, rows, round_to=4):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (("NaN" if math.isnan(v) else round(v, round_to))
                            if isinstance(v, float) else v) for k, v in r.items()})


def self_checks():
    # run() builds images by linearity of blur; it must match render() exactly.
    d, px = 3.0, 10
    kw = dict(px_per_mm=px, background="mottled", mottle_sd=0.05, seed=1, blur_sd_mm=0.1,
              gradient=0.2, exposure_gain=0.8, wb_gains=(1.1, 1.0, 0.85),
              glare=GLARE_CASES["ring_r0.5mm"], tone="srgb")
    want = render(d, **kw)
    n = want.shape[0]
    tex = mottle(d, px, mottle_sd=0.05, mottle_corr_mm=MOTTLE_CORR_MM, shift_mm=0.0, seed=1)
    img = _scene(d, px_per_mm=px, spot="white", contrast_scale=1.0, spot_scale=1.0,
                 background="mottled", mottle_sd=0.05, mottle_corr_mm=MOTTLE_CORR_MM,
                 shift_mm=0.0, seed=1, texture=tex)
    img = blur(img * lighting_multiplier(n, px, 0.2)[:, :, None], px, 0.1) * (0.8 * np.array([1.1, 1.0, 0.85]))
    t = glare_disc(n, px, d, GLARE_CASES["ring_r0.5mm"])
    img = img + blur(np.repeat(t[:, :, None] * 1.0, 3, axis=2), px, 0.1)
    got = _finish(img, px, 0.0, 0.0, None, "srgb")
    assert np.allclose(got, want, atol=1e-12), float(np.abs(got - want).max())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="data")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--px-per-mm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    self_checks()
    t0 = time.perf_counter()
    rows = run(seed=a.seed, trials=a.trials, px_per_mm=a.px_per_mm, workers=a.workers)
    out = Path(a.out)
    write_csv(out / "drift_sim_v2_results.csv", rows)
    lim_rows = []
    for d in DIAMETERS_MM:
        for bg in ("uniform", "mottled"):
            for ch in ("L", "b"):
                for co in CORRECTIONS:
                    g = gradient_limit(d, a.px_per_mm, channel=ch, correction=co, background=bg,
                                       mottle_sd=MOTTLE_SD if bg == "mottled" else 0.0,
                                       blur_sd_mm=BLUR_SD_MM, seed=a.seed)
                    lim_rows.append({"diameter_mm": d, "background": bg, "channel": ch,
                                     "correction": co, "limit_pct": 1.0,
                                     "first_gradient_over_limit": "none up to 0.40" if g is None else g,
                                     "noise_sd": 0.0, "blur_sd_mm": BLUR_SD_MM,
                                     "px_per_mm": a.px_per_mm, "seed": a.seed})
    write_csv(out / "drift_sim_v2_gradient_limits.csv", lim_rows)
    print(f"drift sim v2: {len(rows)} rows, {a.trials} trials each, {a.px_per_mm} px/mm; "
          f"runtime {time.perf_counter() - t0:.1f} s; wrote {out}/drift_sim_v2_results.csv "
          f"and {out}/drift_sim_v2_gradient_limits.csv")


if __name__ == "__main__":
    main()
