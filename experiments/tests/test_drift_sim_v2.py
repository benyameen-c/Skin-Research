"""Tests for drift simulation v2, written before the code exists (plan task T1).

SIMULATION ONLY. Synthetic disks and synthetic texture. No patient images.

Run:  python3 -m pytest experiments/tests -q

Until experiments/drift_sim_v2.py exists every test here is SKIPPED (the fixture
below checks for the file). Once the file exists the skip switches off and every
test must pass. The builder (plan task T4) writes experiments/drift_sim_v2.py to
this contract and may not change this file:
    git diff --exit-code <commit of this file> -- experiments/tests
must stay clean. experiments/drift_sim.py and its tests stay unchanged; v2 may
import from it.

SOURCE OF THE SPECIFICATION: content/measurement-tool-plan.md, section 5 rung 1
("Case to add" table) and section 6 task T1: lighting gradients and vignetting;
b*, a* and Delta E channels; changed-spot sensitivity; gamma / tone curve; glare.
Section 2.1 items 5 and 6 (absolute L* units, CIEDE2000) and 2.2 (smallest
detectable change) set the reporting. The fixed inner disc and ring-only
registration rows of rung 1 belong to task T2 and are NOT tested here.

The plan's pass criteria (for example "ring-normalised false change <= 1 % at
20 % gradient", "glare mask detects >= 95 % of glare pixels") are RESULTS of the
experiment. The plan says a missed criterion is reported, not hidden, so these
tests check that the numbers needed to judge each criterion are produced, and
never assert which way a criterion comes out.

CONTRACT

Everything in experiments/drift_sim.py's contract (its test file docstring)
holds for v2's render, measure_contrast and change_pct, plus the following.

Constants
  DIAMETERS_MM   as v1: sorted, first 2.0, last 8.0, >= 4 values.
  SKIN_RGB, WHITE_SPOT_RGB, BROWN_SPOT_RGB  as v1. The white spot's b* contrast
                 against skin must be at least 1.0 unit in size (either sign) so
                 the b* channel is not refused.
  DRIFTS         as v1 (has "none", an exposure-only drift, a white-balance drift).
  CHANNELS       ("L", "a", "b", "dE").
  GRADIENTS      sorted floats, includes 0.0, 0.05 and 0.20 (plan: 5 % and 20 %
                 end to end).
  GRADIENT_GRID  sorted floats starting at 0.0 and reaching at least 0.20, used
                 by gradient_limit().
  VIGNETTES      sorted floats, includes 0.0 and at least one value in (0, 1).
  TONES          includes "linear", "gamma22", "srgb".
  CHANGES        exactly {"unchanged": (1.0, 1.0), "half_contrast": (0.5, 1.0),
                 "matched": (0.0, 1.0), "overshoot": (-1/3, 1.0),
                 "shrink": (1.0, 0.7)}; values are (contrast_scale, spot_scale)
                 (plan: contrast x0.5, x0, x-1/3; diameter x0.7).
  GLARE_CASES    dict name -> (where, radius_mm, level) with at least one
                 where == "spot" (radius_mm < 1.0, inside the smallest outline)
                 and one where == "ring" (radius_mm <= 0.75, inside the 1.5 mm
                 ring). No case is named "none".

Coordinates (used by the lighting definitions)
  Field is square, n x n pixels. Pixel (i, j) (row i, column j) has its centre
  at x = (j + 0.5 - n/2) / px_per_mm, y = (i + 0.5 - n/2) / px_per_mm mm from
  the field centre, which is the outline centre. H = n / (2 px_per_mm). +x is
  increasing column index, the direction of shift_mm.

render(diameter_mm, *, every v1 argument, spot_scale=1.0, gradient=0.0,
       vignette=0.0, glare=None, tone="linear", return_glare=False)
  * spot_scale scales the DRAWN spot's diameter; the field size and the skin
    texture stay those of diameter_mm, so a shrunk spot is measured with the
    baseline outline.
  * gradient g: neutral multiplier m(x) = 1 + g x / (2 H) on all channels
    (end to end, left edge 1 - g/2 to right edge 1 + g/2).
  * vignette v: neutral multiplier m(x, y) = 1 - v (x^2 + y^2) / (2 H^2)
    (1 at the centre, 1 - v at the corners).
  * Lighting (exposure_gain, wb_gains, gradient, vignette) and glare belong to
    the capture: they stay fixed in the image frame when shift_mm moves the
    skin and spot.
  * glare (where, radius_mm, level): a flat disc of the given radius, centred at
    the field centre ("spot") or at (+(diameter_mm/2 + 1.0 + 0.75) mm, 0)
    ("ring", the middle of the ring), in which `level` is ADDED to all three
    channels. A pixel is in the disc when its centre is within radius_mm of the
    disc centre.
  * Order: scene (skin, mottle, spot, shift) -> lighting multipliers -> glare
    added -> blur -> capture noise -> clip to [0, 1] -> tone curve.
  * tone "linear": none; "gamma22": v ** (1/2.2); "srgb": IEC 61966-2-1
    encoding, 12.92 v for v <= 0.0031308, else 1.055 v ** (1/2.4) - 0.055.
    Measurement treats every image as linear (as a naive JPEG pipeline would).
  * With noise_sd = 0, glare = None and drift "none", no pixel reaches 1.0 at
    any value in GRADIENTS: only glare saturates.
  * return_glare=True returns (img, truth) where truth is the (n, n) bool array
    of the glare disc (all False when glare is None).

rgb_to_lab(rgb)  linear sRGB (..., 3) -> CIELAB D65 (..., 3).
ciede2000(lab1, lab2) -> float, CIEDE2000 colour difference (kL = kC = kH = 1).

glare_mask(img) -> (n, n) bool, True for pixels judged to be glare. It flags at
  least every pixel at 1.0 in all three channels, and flags nothing in a
  glare-free, noise-free render (it must not mistake the white spot or the
  mottle for glare).

measure_contrast(img, diameter_mm, px_per_mm, *, correction="none" | "ring_white",
                 glare_mask=False) -> dict with keys "L", "a", "b", "dE",
  "spot_excluded_frac", "ring_excluded_frac".
  * L, a, b: mean Lab inside the outline minus mean Lab in the ring, Lab per
    pixel then averaged (v1). dE = ciede2000(mean Lab inside, mean Lab ring).
  * glare_mask=True excludes pixels flagged by glare_mask(img) from both means
    (and from the ring means used by "ring_white"); the excluded fractions say
    how much of each region was dropped (both 0.0 when glare_mask=False).
  * Raises ValueError when ring_excluded_frac > 0.20 (plan C10: refuse, do not
    return a number).

change_units(base, follow, diameter_mm, px_per_mm, *, channel="L",
             correction="none", glare_mask=False) -> c_follow - c_base, in Lab
  (or Delta E) units.
change_pct(..., same arguments) -> 100 * (c_follow - c_base) / c_base; raises
  ZeroDivisionError when |c_base| < 1e-6.

gradient_limit(diameter_mm, px_per_mm=20, *, limit_pct=1.0, grid=GRADIENT_GRID,
               channel="L", correction="ring_white", **render_kw) -> float | None
  The smallest g in grid for which |change_pct(render(d, **render_kw),
  render(d, gradient=g, **render_kw), d, px_per_mm, channel, correction)| >
  limit_pct; None if no g in grid exceeds it. (Plan: "or the gradient size at
  which it exceeds 1 % is reported".)

run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, shifts=(0.0,),
    drifts=tuple(DRIFTS), backgrounds=("uniform", "mottled"), spots=("white",),
    noise_sd=<default>, mottle_sd=<default>, blur_sd_mm=<default>)
  -> list of dict rows.
  Factors varied ONE AT A TIME from the baseline (gradient 0.0, vignette 0.0,
  tone "linear", glare "none", change "unchanged"): every row has at most one
  of those five off baseline. Every level of GRADIENTS, VIGNETTES, TONES,
  GLARE_CASES and CHANGES appears, and each is crossed with every requested
  spot, background, diameter, shift, drift, correction ("none", "ring_white")
  and channel in CHANNELS. Glare rows come with glare_mask False and True;
  rows without glare have glare_mask False.
  Row keys include: spot, background, diameter_mm, shift_mm, drift, gradient,
  vignette, tone, glare, glare_mask (bool), change, correction, channel,
  true_change_pct, mean_measured_change_pct, mean_abs_error_pct_points,
  baseline_contrast_units, mean_change_units, sd_change_units, sdc_units,
  glare_recall, glare_precision, trials, rejected.
  * Each trial draws one skin texture used for both visits; capture noise is
    drawn independently per visit (v1). The follow-up visit carries the change,
    drift, gradient, vignette, tone and glare; the baseline visit is the
    unchanged spot with drift "none" and every other factor at baseline, except
    that tone applies to both visits (a JPEG pipeline encodes both).
  * true_change_pct is the change the ideal instrument would see: change_pct of
    the noise-free, unshifted, undrifted, uniform-background, linear, glare-free
    pair (same diameter, spot, change, channel, blur and px_per_mm), correction
    "none". It is 0.0 for "unchanged".
  * sd_change_units is the SD over accepted trials of the measured change in
    units; since one change is a difference of two sessions, it equals
    sqrt(2) x SEM, so sdc_units = 1.96 x sd_change_units (plan 2.2,
    SDC = 1.96 sqrt(2) SEM).
  * glare_recall and glare_precision: glare_mask(follow image) against the
    render's truth over the whole field, mean over trials, in [0, 1], for rows
    with glare and glare_mask True; NaN in all other rows.
  * rejected counts trials refused (zero baseline contrast or ring > 20 %
    masked). If every trial is refused, the numeric result fields are NaN.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

PX_FAST = 10            # px/mm for property tests where only exactness or order matters
PX_FINE = 40            # px/mm for the closed-form comparison
EXACT = 1e-9            # identical arithmetic: only float round-off allowed
ROUNDOFF = 1e-6         # gains that cancel in img / ring_mean, after Lab conversion


@pytest.fixture(scope="module")
def sim():
    if not (EXPERIMENTS / "drift_sim_v2.py").exists():
        pytest.skip("experiments/drift_sim_v2.py not written yet (plan task T4)")
    import drift_sim_v2           # once the file exists, an import error is a failure
    return drift_sim_v2


def lighting_field(n, gradient=0.0, vignette=0.0):
    """The neutral lighting multiplier of the contract, on pixel centres."""
    c = np.arange(n) + 0.5 - n / 2           # pixel-centre offset, in pixels
    x = c[None, :]
    y = c[:, None]
    m = 1 + gradient * x / n                 # g x / (2H), with x / H = 2 c / n
    m = m * (1 - vignette * (x ** 2 + y ** 2) / (n ** 2 / 2))
    return m


def closed_form_retained_shrink(scale):
    """Contrast fraction left inside a fixed outline when the spot's diameter is
    scaled by `scale` (< 1), uniform skin, Lab averaged per pixel: area ratio."""
    return scale ** 2


def channels_with_contrast(sim, img, d, px, correction="none"):
    c = sim.measure_contrast(img, d, px, correction=correction)
    return [ch for ch in sim.CHANNELS if abs(c[ch]) >= 1e-3]


def is_nan(v):
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False


# ---- constants taken from the plan -----------------------------------------

def test_tables_match_the_plan(sim):
    d = tuple(sim.DIAMETERS_MM)
    assert d == tuple(sorted(d)) and d[0] == 2.0 and d[-1] == 8.0 and len(d) >= 4
    assert tuple(sim.CHANNELS) == ("L", "a", "b", "dE")
    g = tuple(sim.GRADIENTS)
    assert g == tuple(sorted(g)) and {0.0, 0.05, 0.20} <= set(g)
    grid = tuple(sim.GRADIENT_GRID)
    assert grid == tuple(sorted(grid)) and grid[0] == 0.0 and grid[-1] >= 0.20
    v = tuple(sim.VIGNETTES)
    assert v == tuple(sorted(v)) and 0.0 in v and any(0 < x < 1 for x in v)
    assert {"linear", "gamma22", "srgb"} <= set(sim.TONES)
    want = {"unchanged": (1.0, 1.0), "half_contrast": (0.5, 1.0), "matched": (0.0, 1.0),
            "overshoot": (-1 / 3, 1.0), "shrink": (1.0, 0.7)}
    got = {k: tuple(map(float, val)) for k, val in sim.CHANGES.items()}
    assert set(got) == set(want)
    for k in want:
        assert np.allclose(got[k], want[k], atol=1e-12), k


def test_glare_cases_fit_their_regions(sim):
    cases = sim.GLARE_CASES
    assert "none" not in cases
    wheres = {w for w, _, _ in cases.values()}
    assert {"spot", "ring"} <= wheres
    for name, (where, radius, level) in cases.items():
        assert radius > 0 and level > 0, name
        if where == "spot":
            assert radius < 1.0, name          # inside the 2 mm outline
        else:
            assert where == "ring" and radius <= 0.75, name   # inside the 1.5 mm ring


def test_drift_table_has_the_required_kinds(sim):
    assert sim.DRIFTS["none"][0] == 1.0 and tuple(sim.DRIFTS["none"][1]) == (1.0, 1.0, 1.0)
    kinds = [(gain, tuple(w)) for gain, w in sim.DRIFTS.values()]
    assert any(gain != 1.0 and w == (1.0, 1.0, 1.0) for gain, w in kinds)
    assert any(len(set(w)) > 1 for gain, w in kinds)


# ---- scene: new render arguments are defined exactly -----------------------

def test_new_arguments_at_baseline_change_nothing(sim):
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=3)
    a = sim.render(4.0, **kw)
    b = sim.render(4.0, spot_scale=1.0, gradient=0.0, vignette=0.0, glare=None,
                   tone="linear", **kw)
    assert np.array_equal(a, b)


def test_white_spot_contrast_in_lab_units(sim):
    c = sim.measure_contrast(sim.render(8.0, px_per_mm=PX_FAST), 8.0, PX_FAST)
    assert c["L"] >= 5.0                     # white spot is clearly lighter (v1)
    assert abs(c["b"]) >= 1.0                # b* channel is measurable, not refused
    assert c["dE"] > 0.0


@pytest.mark.parametrize("g", [0.05, 0.20])
def test_gradient_is_the_stated_linear_ramp(sim, g):
    base = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    lit = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0, gradient=g)
    n = base.shape[0]
    assert base.shape == lit.shape and base.shape[1] == n
    # Definition, no noise, no blur: the ratio is the multiplier itself.
    assert np.allclose(lit / base, lighting_field(n, gradient=g)[..., None], atol=EXACT)


def test_vignette_is_the_stated_radial_falloff(sim):
    v = max(sim.VIGNETTES)
    base = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    lit = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0, vignette=v)
    n = base.shape[0]
    assert np.allclose(lit / base, lighting_field(n, vignette=v)[..., None], atol=EXACT)


def test_lighting_and_glare_stay_in_the_image_frame_under_shift(sim):
    # The spot and texture move with shift_mm; the light does not. Spot present,
    # mottled skin, no noise, no blur: the ratio is the lighting field exactly.
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=4, shift_mm=0.3)
    plain = sim.render(4.0, **kw)
    lit = sim.render(4.0, gradient=0.2, vignette=max(sim.VIGNETTES), **kw)
    n = plain.shape[0]
    field = lighting_field(n, gradient=0.2, vignette=max(sim.VIGNETTES))
    assert np.allclose(lit / plain, field[..., None], atol=EXACT)
    glare = ("ring", 0.5, 0.3)
    _, t0 = sim.render(4.0, px_per_mm=PX_FAST, glare=glare, return_glare=True)
    _, t1 = sim.render(4.0, glare=glare, return_glare=True, **kw)
    assert np.array_equal(t0, t1)


@pytest.mark.parametrize("where", ["spot", "ring"])
def test_glare_is_an_added_flat_disc_in_the_stated_place(sim, where):
    d, r, level = 4.0, 0.5, 0.3
    px = 20
    base = sim.render(d, px_per_mm=px)
    img, truth = sim.render(d, px_per_mm=px, glare=(where, r, level), return_glare=True)
    n = base.shape[0]
    assert truth.shape == (n, n) and truth.dtype == bool
    want = np.where(truth[..., None], np.minimum(base + level, 1.0), base)
    assert np.allclose(img, want, atol=EXACT)
    # Place: centroid of the truth disc, within one pixel of the stated centre.
    ii, jj = np.nonzero(truth)
    cx = (jj.mean() + 0.5 - n / 2) / px
    cy = (ii.mean() + 0.5 - n / 2) / px
    x0 = 0.0 if where == "spot" else d / 2 + 1.0 + 0.75
    assert abs(cx - x0) <= 1 / px and abs(cy) <= 1 / px, (cx, cy)
    # Size: pixel-centre count of a 10 px radius disc is within 10 % of pi r^2.
    assert abs(truth.sum() / (math.pi * (r * px) ** 2) - 1) < 0.10


def test_no_glare_truth_without_glare(sim):
    img, truth = sim.render(4.0, px_per_mm=PX_FAST, return_glare=True)
    assert not truth.any()
    assert np.array_equal(img, sim.render(4.0, px_per_mm=PX_FAST))


@pytest.mark.parametrize("tone", ["gamma22", "srgb"])
def test_tone_curves_are_the_stated_encodings(sim, tone):
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=7,
              gradient=0.2, exposure_gain=0.8)
    lin = sim.render(4.0, **kw)
    enc = sim.render(4.0, tone=tone, **kw)
    if tone == "gamma22":
        want = lin ** (1 / 2.2)
    else:
        want = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    assert np.allclose(enc, want, atol=1e-12)


def test_output_is_clipped_and_only_glare_saturates(sim):
    for g in sim.GRADIENTS:
        for bg in ("uniform", "mottled"):
            img = sim.render(2.0, px_per_mm=PX_FAST, background=bg, mottle_sd=0.05,
                             seed=8, gradient=g)
            assert img.min() >= 0.0 and img.max() < 1.0, (g, bg)
    hot = sim.render(2.0, px_per_mm=PX_FAST, glare=("spot", 0.5, 1.0), noise_sd=0.05, seed=8)
    assert hot.min() >= 0.0 and hot.max() <= 1.0


def test_spot_scale_shrinks_only_the_drawn_spot(sim):
    a = sim.render(4.0, px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=2)
    b = sim.render(4.0, px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=2,
                   spot_scale=0.7)
    assert a.shape == b.shape
    n = a.shape[0]
    c = np.arange(n) + 0.5 - n / 2
    r_mm = np.hypot(c[None, :], c[:, None]) / PX_FAST
    outside = r_mm > 4.0 / 2 + 2 / PX_FAST           # beyond the baseline spot edge
    assert np.array_equal(a[outside], b[outside])     # same field, same texture
    assert not np.array_equal(a, b)


# ---- colour science --------------------------------------------------------

def test_rgb_to_lab_reference_points(sim):
    white = np.asarray(sim.rgb_to_lab(np.array([1.0, 1.0, 1.0]))).reshape(-1)
    grey = np.asarray(sim.rgb_to_lab(np.array([0.18, 0.18, 0.18]))).reshape(-1)
    # D65 white is L* 100, a* = b* = 0; 0.05 allows 4-digit sRGB matrices.
    assert abs(white[0] - 100) < 0.05 and abs(white[1]) < 0.05 and abs(white[2]) < 0.05
    # Y = 0.18 gives L* = 116 * 0.18^(1/3) - 16 = 49.496.
    assert abs(grey[0] - 49.496) < 0.05


# Sharma, Wu and Dalal (2005), Color Res Appl 30:21-30, Table 1, pairs 1-3, 7, 8,
# 13, 17-20. Given there to 4 decimals, hence the 1e-4 tolerance.
SHARMA = [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
    ((50.0, 2.8361, -74.0200), (50.0, 0.0, -82.7485), 3.4412),
    ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
    ((50.0, -1.0, 2.0), (50.0, 0.0, 0.0), 2.3669),
    ((50.0, 2.4900, -0.0010), (50.0, -2.4900, 0.0009), 7.1792),
    ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
    ((50.0, 2.5, 0.0), (61.0, -5.0, 29.0), 22.8977),
    ((50.0, 2.5, 0.0), (56.0, -27.0, -3.0), 31.9030),
    ((50.0, 2.5, 0.0), (58.0, 24.0, 15.0), 19.4535),
]


@pytest.mark.parametrize("lab1,lab2,want", SHARMA)
def test_ciede2000_matches_published_pairs(sim, lab1, lab2, want):
    assert abs(float(sim.ciede2000(lab1, lab2)) - want) < 1e-4
    assert abs(float(sim.ciede2000(lab2, lab1)) - want) < 1e-4


def test_measured_contrast_matches_lab_difference(sim):
    # Uniform skin, no blur, 8 mm at 40 px/mm: edge pixels are about 1 % of the
    # outline, so the measured means are within 3 % of the pure colours.
    d = 8.0
    c = sim.measure_contrast(sim.render(d, px_per_mm=PX_FINE), d, PX_FINE)
    spot = np.asarray(sim.rgb_to_lab(np.asarray(sim.WHITE_SPOT_RGB, float))).reshape(-1)
    skin = np.asarray(sim.rgb_to_lab(np.asarray(sim.SKIN_RGB, float))).reshape(-1)
    for k, ch in enumerate("Lab"):
        want = spot[k] - skin[k]
        assert abs(c[ch] - want) <= 0.03 * abs(want) + 0.05, (ch, c[ch], want)
    want = float(sim.ciede2000(tuple(spot), tuple(skin)))
    assert abs(c["dE"] - want) <= 0.03 * want + 0.05


# ---- the five required properties, on every new channel and factor --------

@pytest.mark.parametrize("extra", [
    dict(),
    dict(gradient=0.2),
    dict(vignette=0.3),
    dict(tone="gamma22"),
    dict(tone="srgb"),
    dict(glare=("ring", 0.5, 0.3)),
    dict(spot_scale=0.7),
    dict(contrast_scale=-1 / 3),
])
@pytest.mark.parametrize("correction", ["none", "ring_white"])
@pytest.mark.parametrize("masked", [False, True])
def test_zero_shift_zero_drift_gives_zero_error(sim, extra, correction, masked):
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=9, **extra)
    for d in (2.0, 8.0):
        img = sim.render(d, **kw)
        for ch in channels_with_contrast(sim, img, d, PX_FAST, correction):
            got = sim.change_pct(img, sim.render(d, **kw), d, PX_FAST, channel=ch,
                                 correction=correction, glare_mask=masked)
            assert abs(got) < EXACT, (extra, ch, d, got)


@pytest.mark.parametrize("correction", ["none", "ring_white"])
@pytest.mark.parametrize("channel", ["L", "b"])
def test_shrink_matches_closed_form_area_ratio(sim, correction, channel):
    # Uniform skin, no blur, no noise, ring untouched by the change: with Lab
    # averaged per pixel the contrast inside the fixed outline scales by the area
    # ratio 0.7^2 = 0.49, a true change of -51 %. Tolerance 1.0 point at 40 px/mm,
    # as v1: data/alignment_validation.csv line 5 puts the 20 px/mm pixel model
    # 0.008 points from the formula for this case, so 1.0 is generous for edge
    # pixels. ring_white divides both images by the same ring means, so the
    # area argument is unchanged. The dE channel is not linear in area: excluded.
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE)
        follow = sim.render(d, px_per_mm=PX_FINE, spot_scale=0.7)
        got = sim.change_pct(base, follow, d, PX_FINE, channel=channel, correction=correction)
        want = 100 * (closed_form_retained_shrink(0.7) - 1)
        assert abs(got - want) < 1.0, (d, got, want)


def test_matched_spot_reads_minus_100_and_overshoot_crosses_it(sim):
    d = 4.0
    base = sim.render(d, px_per_mm=PX_FAST)
    matched = sim.render(d, px_per_mm=PX_FAST, contrast_scale=0.0)
    over = sim.render(d, px_per_mm=PX_FAST, contrast_scale=-1 / 3)
    for ch in channels_with_contrast(sim, base, d, PX_FAST):
        # Spot identical to skin: contrast exactly 0, so change exactly -100 %.
        assert abs(sim.change_pct(base, matched, d, PX_FAST, channel=ch) + 100) < EXACT, ch
    # Overshoot to darker than skin flips the sign of lightness contrast.
    assert sim.change_pct(base, over, d, PX_FAST, channel="L") < -100


def test_error_grows_as_spot_shrinks_with_misplacement(sim):
    errs = []
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE)
        follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=0.25)
        errs.append(abs(sim.change_pct(base, follow, d, PX_FINE, channel="b")))
    # Same geometry as v1's L test, now on b*: strictly ordered, deterministic.
    assert all(a > b for a, b in zip(errs, errs[1:])), errs


@pytest.mark.parametrize("channel", ["L", "a", "b", "dE"])
def test_zero_contrast_baseline_is_refused(sim, channel):
    flat = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    spot = sim.render(4.0, px_per_mm=PX_FAST)
    for correction in ("none", "ring_white"):
        with pytest.raises(ZeroDivisionError):
            sim.change_pct(flat, spot, 4.0, PX_FAST, channel=channel, correction=correction)


def test_same_seed_reruns_are_identical(sim):
    kw = dict(seed=5, trials=2, px_per_mm=PX_FAST, diameters=(2.0,), shifts=(0.25,),
              drifts=("none",), backgrounds=("mottled",))
    # json with sort_keys compares NaN cells as equal text, which == on dicts does not.
    a = json.dumps(sim.run(**kw), sort_keys=True, default=str)
    b = json.dumps(sim.run(**kw), sort_keys=True, default=str)
    assert a == b
    img_kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, noise_sd=0.01,
                  gradient=0.2, glare=("spot", 0.5, 0.3), tone="srgb", seed=5)
    assert np.array_equal(sim.render(3.0, **img_kw), sim.render(3.0, **img_kw))
    other = dict(img_kw, seed=6)
    assert not np.array_equal(sim.render(3.0, **img_kw), sim.render(3.0, **other))


# ---- corrections, units and refusal ----------------------------------------

@pytest.mark.parametrize("light", [dict(), dict(gradient=0.2), dict(vignette=0.3)])
@pytest.mark.parametrize("drift", [dict(exposure_gain=0.8),
                                   dict(wb_gains=(0.9, 1.0, 0.8)),
                                   dict(exposure_gain=0.9, wb_gains=(0.85, 0.95, 0.9))])
def test_ring_white_cancels_any_channel_gain_on_every_channel(sim, light, drift):
    # A global per-channel gain on top of any fixed lighting field cancels exactly
    # in img / ring_mean, so every channel, dE included, is unchanged. Gains <= 1
    # keep every pixel below clipping. 1e-6 points is float round-off.
    for bg in ("uniform", "mottled"):
        for d in (2.0, 8.0):
            kw = dict(px_per_mm=PX_FAST, background=bg, mottle_sd=0.05, seed=6, **light)
            base = sim.render(d, **kw)
            for ch in channels_with_contrast(sim, base, d, PX_FAST, "ring_white"):
                got = sim.change_pct(base, sim.render(d, **kw, **drift), d, PX_FAST,
                                     channel=ch, correction="ring_white")
                assert abs(got) < ROUNDOFF, (bg, d, ch, got)


def test_change_units_and_change_pct_agree_with_measure_contrast(sim):
    d = 3.0
    base = sim.render(d, px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=1)
    follow = sim.render(d, px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=1,
                        contrast_scale=0.5, gradient=0.05)
    for correction in ("none", "ring_white"):
        cb = sim.measure_contrast(base, d, PX_FAST, correction=correction)
        cf = sim.measure_contrast(follow, d, PX_FAST, correction=correction)
        for ch in channels_with_contrast(sim, base, d, PX_FAST, correction):
            u = sim.change_units(base, follow, d, PX_FAST, channel=ch, correction=correction)
            p = sim.change_pct(base, follow, d, PX_FAST, channel=ch, correction=correction)
            assert abs(u - (cf[ch] - cb[ch])) < EXACT
            assert abs(p - 100 * u / cb[ch]) < 1e-7


def test_glare_mask_flags_saturation_and_nothing_in_a_clean_scene(sim):
    img = sim.render(4.0, px_per_mm=PX_FAST, glare=("spot", 0.8, 1.0))
    sat = (img >= 1.0).all(axis=-1)
    assert sat.any()
    mask = np.asarray(sim.glare_mask(img))
    assert mask.shape == sat.shape and mask[sat].all()
    for g in (0.0, max(sim.GRADIENTS)):
        for bg in ("uniform", "mottled"):
            clean = sim.render(2.0, px_per_mm=PX_FAST, background=bg, mottle_sd=0.05,
                               seed=3, gradient=g)
            assert not np.asarray(sim.glare_mask(clean)).any(), (g, bg)


def test_excluded_fractions_are_reported(sim):
    d = 4.0
    plain = sim.measure_contrast(sim.render(d, px_per_mm=PX_FAST), d, PX_FAST)
    assert plain["spot_excluded_frac"] == 0.0 and plain["ring_excluded_frac"] == 0.0
    in_spot = sim.render(d, px_per_mm=PX_FAST, glare=("spot", 0.8, 1.0))
    c = sim.measure_contrast(in_spot, d, PX_FAST, glare_mask=True)
    assert 0.0 < c["spot_excluded_frac"] < 1.0
    unmasked = sim.measure_contrast(in_spot, d, PX_FAST, glare_mask=False)
    assert unmasked["spot_excluded_frac"] == 0.0 and unmasked["ring_excluded_frac"] == 0.0
    in_ring = sim.render(d, px_per_mm=PX_FAST, glare=("ring", 0.5, 1.0))
    c = sim.measure_contrast(in_ring, d, PX_FAST, glare_mask=True)
    assert 0.0 < c["ring_excluded_frac"] <= 0.20


def test_mostly_masked_ring_is_refused(sim):
    # Plan C10: a ring more than 20 % masked gives no number. A saturated disc
    # reaching past the ring's outer edge masks all of it.
    d = 2.0
    img = sim.render(d, px_per_mm=PX_FAST, glare=("spot", d / 2 + 3.0, 1.0))
    with pytest.raises(ValueError):
        sim.measure_contrast(img, d, PX_FAST, glare_mask=True)


def test_gradient_limit_is_the_first_grid_value_over_the_limit(sim):
    for d in (2.0, 8.0):
        kw = dict(background="mottled", mottle_sd=0.05, seed=2)
        got = sim.gradient_limit(d, PX_FAST, limit_pct=1.0, **kw)
        base = sim.render(d, px_per_mm=PX_FAST, **kw)
        want = None
        for g in sim.GRADIENT_GRID:
            follow = sim.render(d, px_per_mm=PX_FAST, gradient=g, **kw)
            if abs(sim.change_pct(base, follow, d, PX_FAST, correction="ring_white")) > 1.0:
                want = g
                break
        assert got == want, (d, got, want)


# ---- the experiment table --------------------------------------------------

BASELINE = {"gradient": 0.0, "vignette": 0.0, "tone": "linear", "glare": "none",
            "change": "unchanged"}


def off_baseline(r):
    return [k for k, v in BASELINE.items()
            if (float(r[k]) != v if isinstance(v, float) else r[k] != v)]


@pytest.fixture(scope="module")
def small_run(sim):
    return sim.run(seed=3, trials=2, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   shifts=(0.0,), noise_sd=0.0, backgrounds=("uniform", "mottled"))


def test_run_has_every_column(small_run):
    need = {"spot", "background", "diameter_mm", "shift_mm", "drift", "gradient", "vignette",
            "tone", "glare", "glare_mask", "change", "correction", "channel",
            "true_change_pct", "mean_measured_change_pct", "mean_abs_error_pct_points",
            "baseline_contrast_units", "mean_change_units", "sd_change_units", "sdc_units",
            "glare_recall", "glare_precision", "trials", "rejected"}
    for r in small_run:
        assert need <= set(r)


def test_run_varies_one_factor_at_a_time_and_covers_every_level(sim, small_run):
    rows = small_run
    for r in rows:
        assert len(off_baseline(r)) <= 1, r
        assert r["glare_mask"] in (True, False)
        if r["glare"] == "none":
            assert r["glare_mask"] is False
    assert {float(r["gradient"]) for r in rows} == set(map(float, sim.GRADIENTS))
    assert {float(r["vignette"]) for r in rows} == set(map(float, sim.VIGNETTES))
    assert {r["tone"] for r in rows} == set(sim.TONES)
    assert {r["glare"] for r in rows} == set(sim.GLARE_CASES) | {"none"}
    assert {r["change"] for r in rows} == set(sim.CHANGES)
    assert {r["channel"] for r in rows} == set(sim.CHANNELS)
    assert {r["correction"] for r in rows} == {"none", "ring_white"}
    assert {r["drift"] for r in rows} == set(sim.DRIFTS)
    assert {r["background"] for r in rows} == {"uniform", "mottled"}
    assert {float(r["diameter_mm"]) for r in rows} == {2.0, 8.0}
    # Crossing: every factor level meets every drift, channel and correction.
    for key in BASELINE:
        for level in {r[key] for r in rows}:
            sub = [r for r in rows if r[key] == level]
            assert {r["drift"] for r in sub} == set(sim.DRIFTS), (key, level)
            assert {r["channel"] for r in sub} == set(sim.CHANNELS), (key, level)
            assert {r["correction"] for r in sub} == {"none", "ring_white"}, (key, level)
    for name in sim.GLARE_CASES:
        assert {r["glare_mask"] for r in rows if r["glare"] == name} == {True, False}, name


def test_run_rows_count_trials_and_refusals(small_run):
    for r in small_run:
        t, rej = int(r["trials"]), int(r["rejected"])
        assert t == 2 and 0 <= rej <= t
        if rej == t:
            assert is_nan(r["mean_abs_error_pct_points"]), r


def test_run_true_change_is_the_ideal_instrument(small_run):
    for r in small_run:
        if int(r["rejected"]) == int(r["trials"]):
            continue
        if r["change"] == "unchanged":
            assert float(r["true_change_pct"]) == 0.0, r
        if r["change"] == "matched":
            assert abs(float(r["true_change_pct"]) + 100) < EXACT, r


def test_run_ideal_rows_have_zero_error(sim, small_run):
    # Uniform skin, no shift, no drift, no noise, every factor but the change at
    # baseline, correction none: the measurement IS the ideal instrument.
    ideal = [r for r in small_run if r["background"] == "uniform" and r["drift"] == "none"
             and float(r["shift_mm"]) == 0.0 and r["correction"] == "none"
             and off_baseline(r) in ([], ["change"]) and int(r["rejected"]) < int(r["trials"])]
    assert {r["change"] for r in ideal} == set(sim.CHANGES)
    for r in ideal:
        assert abs(float(r["mean_abs_error_pct_points"])) < EXACT, r
        assert abs(float(r["sd_change_units"])) < EXACT, r


def test_run_reports_absolute_units_and_sdc(small_run):
    for r in small_run:
        if int(r["rejected"]) == int(r["trials"]):
            continue
        assert abs(float(r["sdc_units"]) - 1.96 * float(r["sd_change_units"])) < EXACT, r
        assert float(r["sd_change_units"]) >= 0.0
        if r["channel"] == "L" and r["spot"] == "white" and r["drift"] == "none" \
                and off_baseline(r) == []:
            assert float(r["baseline_contrast_units"]) > 0.0      # white spot lighter


def test_run_glare_scores_only_where_they_apply(small_run):
    for r in small_run:
        if r["glare"] != "none" and r["glare_mask"] is True:
            assert 0.0 <= float(r["glare_recall"]) <= 1.0, r
            assert 0.0 <= float(r["glare_precision"]) <= 1.0, r
        else:
            assert is_nan(r["glare_recall"]) and is_nan(r["glare_precision"]), r


def test_run_sd_is_positive_with_noise(sim):
    rows = sim.run(seed=4, trials=4, px_per_mm=PX_FAST, diameters=(2.0,), shifts=(0.0,),
                   drifts=("none",), backgrounds=("uniform",), noise_sd=0.01)
    base = [r for r in rows if off_baseline(r) == [] and r["channel"] == "L"
            and r["correction"] == "none"]
    assert base and all(float(r["sd_change_units"]) > 0.0 for r in base)


# ---- rule 7: synthetic shapes only -----------------------------------------

def test_no_image_file_readers(sim):
    src = Path(sim.__file__).read_text()
    for banned in ("imread", "Image.open", "import PIL", "from PIL", "import cv2", "imageio"):
        assert banned not in src, banned
