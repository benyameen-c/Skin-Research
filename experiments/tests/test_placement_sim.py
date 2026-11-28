"""Tests for the placement simulation (plan task T2), written before the code exists.

SIMULATION ONLY. Synthetic disks and synthetic texture. No patient images.

Run:  python3 -m pytest experiments/tests -q

Until experiments/placement_sim.py exists, every test here is SKIPPED (see
`pytestmark` below), so the existing suite stays green. As soon as the builder
adds that file the tests run unchanged; the builder may not edit this file:
`git diff --exit-code <tests commit> -- experiments/tests` must stay clean.

SOURCE OF THE SPECIFICATION: content/measurement-tool-plan.md, sections 2.1 and
4 and task T2 ("fixed inner disc, registration on ring-only texture, sticker
centring with detection noise, segmentation for area"). Where the plan leaves a
choice open, the choice made here is marked READING and can be changed by Ben.
This file asserts properties every correct implementation must have
(exactness on noise-free scenes, the closed-form geometry, refusals,
reproducibility). It does NOT assert whether any strategy meets the plan's
section 4 target: that is the experiment's result, computed by
`evaluate_target` and reported, not presumed here.

Conventions
  Linear RGB in, CIELAB (D65) computed PER PIXEL, then averaged (as drift_sim.py).
  Image axes: x = column index (increasing right), y = row index (increasing down).
  The frame centre, centre_mm = (0, 0), is at pixel ((n - 1) / 2, (n - 1) / 2)
  for an n x n field; pixel centres sit at integer indices.

Scene
  DIAMETERS_MM     sorted tuple; first 2.0, last 8.0, >= 4 values.
  SHIFTS           sorted tuple of misplacement magnitudes (mm); contains 0.0,
                   0.25, 0.3 and 0.5 (0.3 is the plan's 4.4 limit on a 2 mm spot).
  SKIN_RGB, WHITE_SPOT_RGB   linear-RGB triples in (0, 1); the spot is lighter.
  RING_GAP_MM = 1.0, RING_WIDTH_MM = 1.5   reference ring (plan 2.1 item 3).
  INNER_FRACTION = 0.6   inner disc radius / baseline spot radius (plan 2.1 item 2).
  STICKER_SD_MM = 0.1    default per-axis SD of sticker centring error. READING:
                         the plan's pass threshold for sticker reapplication
                         (section 4.1), so the run shows whether that is enough.
  SCENARIOS        dict name -> (contrast_scale, diameter_scale), exactly:
                   unchanged (1, 1), genuine_fading (0.5, 1), invisible (0, 1),
                   dark_overshoot (-1/3, 1), shrinking (1, 0.7)
                   (plan section 5 rung 1 "changed-spot cases").
  field_size(diameter_mm, px_per_mm) -> n, side of the square field in pixels.
      Large enough that the ring's outer edge plus max(SHIFTS) plus a margin
      fits inside the field. Fixed by the BASELINE diameter.
  render(diameter_mm, *, px_per_mm=20, contrast_scale=1.0, diameter_scale=1.0,
         background="uniform" | "mottled", mottle_sd=0.0, mottle_corr_mm=1.0,
         shift_mm=(0.0, 0.0), noise_sd=0.0, blur_sd_mm=0.0, seed=0)
      -> float ndarray (n, n, 3), linear RGB, n = field_size(diameter_mm, px_per_mm).
      * White spot only (Module 1).
      * contrast_scale scales the spot's departure from skin in linear RGB
        (0 = invisible, negative = darker than skin).
      * diameter_scale: the spot drawn has diameter diameter_mm * diameter_scale;
        the field is still sized from diameter_mm.
      * mottled: multiplicative luminance texture, continuous in space, fixed by
        seed; mottle_sd=0 gives exactly the uniform background.
      * shift_mm = (dx, dy), or a float meaning (dx, 0), moves the WHOLE scene
        (texture and spot): the true spot centre is at centre_mm = shift_mm.
      * noise_sd: per-pixel, per-channel Gaussian noise, drawn from seed.
      * diameter_mm <= 0 raises ValueError.
Measurement
  measure_contrast(img, diameter_mm, px_per_mm, *, region="outline" | "inner_disc",
                   centre_mm=(0, 0), inner_fraction=INNER_FRACTION)
      -> {"L": .., "a": .., "b": ..}: mean Lab in region S minus mean Lab in the
      ring R, both centred on centre_mm and sized from the BASELINE diameter_mm.
      S is the disc of radius diameter_mm / 2 ("outline") or
      inner_fraction * diameter_mm / 2 ("inner_disc").
      Any other region (in particular "segmented") raises ValueError: the plan
      (4.3) allows segmentation for area only, never for colour.
      inner_fraction outside (0, 1) raises ValueError.
  change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, region="outline",
             base_centre_mm=(0, 0), follow_centre_mm=(0, 0),
             inner_fraction=INNER_FRACTION, channel="L")
      -> 100 * (c_follow - c_base) / c_base. Raises ZeroDivisionError when
      |c_base| < 1e-6 (refused, never divided by).
  segment_area(img, diameter_mm, px_per_mm) -> area in mm^2 of the spot found
      from the image alone, as the region LIGHTER than the ring, searched inside
      the ring's inner edge around the frame centre (method is the builder's
      choice and must be stated in the module). Returns 0.0 when no lighter
      region is found (invisible spot, or a spot now darker than skin).
Placement
  PLACEMENTS = ("none", "ring_registration", "sticker")
  REGIONS    = ("outline", "inner_disc")
  place(method, base_img, follow_img, diameter_mm, px_per_mm, *,
        true_shift_mm=(0, 0), sticker_sd_mm=STICKER_SD_MM, seed=0)
      -> (dx, dy) in mm, the estimated follow-up spot centre relative to the
      frame centre, or None when the method refuses.
      * "none": (0.0, 0.0), measure where the frame is.
      * "ring_registration": estimate the scene shift between base_img and
        follow_img from pixels OUTSIDE radius diameter_mm / 2 + RING_GAP_MM of
        the frame centre only (plan 4.2: register on the surrounding skin, not
        on the spot). Must not read true_shift_mm. Returns None when the masked
        area has no usable texture (plan C10: refuse rather than guess).
      * "sticker": true_shift_mm plus independent N(0, sticker_sd_mm) noise per
        axis, drawn from seed (plan 4.1: fiducial detection and reapplication
        noise). sticker_sd_mm = 0 returns true_shift_mm exactly.
      * any other method raises ValueError.
Experiment
  run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, shifts=SHIFTS,
      scenarios=tuple(SCENARIOS), noise_sd=<default>, mottle_sd=<default>,
      blur_sd_mm=<default>, sticker_sd_mm=STICKER_SD_MM) -> list of dict rows.
      One row per scenario x background ("uniform", "mottled") x diameter x
      shift x placement x region. Within one scenario x background x diameter x
      shift cell, every placement and region is measured on the SAME captures
      (paired comparison). Each trial draws one skin texture used for both
      visits; capture noise is independent per visit; the follow-up is shifted
      by (shift, 0) mm; the baseline is measured at the frame centre.
      Row keys include: scenario, background, diameter_mm, shift_mm, placement,
      region, true_change_pct, mean_change_pct, sd_change_pct,
      mean_abs_error_pct_points, base_contrast_L, mean_change_L,
      mean_centre_error_mm, area_true_mm2, area_mean_mm2, area_error_pct,
      trials, rejected.
      * true_change_pct: the change the same region reports with exact
        placement (follow-up measured at its true centre), no noise, blur as in
        the run. So unchanged = 0 and invisible = -100 for every region.
      * mean_abs_error_pct_points = mean over accepted trials of
        |measured change - true_change_pct|.
      * mean_change_L: mean follow-up minus baseline contrast in L* units
        (plan 2.1 item 5: report absolute units, not only percent).
      * rejected: trials where place() returned None; means are over accepted
        trials; when every trial is rejected the mean and SD fields are None.
      * area_*: segment_area on every trial's follow-up capture, rejected or
        not (segmentation does not depend on placement); area_error_pct =
        100 * (area_mean_mm2 - area_true_mm2) / area_true_mm2.
  evaluate_target(rows, *, diameter_mm=2.0, shift_mm=0.5, background="mottled")
      -> dict: {(placement, region): {"false_change_ok", "sd_ok",
      "sensitivity_ok", "within_noise_to_0_3mm", "passes"}, "area_ok": bool}.
      Plan section 4 target, at the given diameter, shift and background:
      * false_change_ok: unchanged row |mean_change_pct| <= 2.
      * sd_ok: unchanged row sd_change_pct <= 1.
      * sensitivity_ok: genuine_fading row |mean_change_pct - true_change_pct| <= 2.
      * within_noise_to_0_3mm (inner_disc only, None for outline), plan 4.4.
        READING of "below the noise floor": for every unchanged row with
        0 < shift_mm <= 0.3, |mean_change_pct| <= sd_change_pct of the same
        placement and region at shift 0.
      * passes: all applicable keys True. A row whose means are None counts as
        not passing. A required row that is missing raises ValueError.
      * area_ok: plan 4.3, |area_error_pct| <= 10 on the unchanged and the
        shrinking rows (placement "none", region "outline").
      Reads only: scenario, background, diameter_mm, shift_mm, placement,
      region, true_change_pct, mean_change_pct, sd_change_pct, area_error_pct,
      trials, rejected. Only the "unchanged", "genuine_fading" and "shrinking"
      scenarios are required.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

pytestmark = pytest.mark.skipif(
    not (EXPERIMENTS / "placement_sim.py").exists(),
    reason="experiments/placement_sim.py not built yet (plan task T5); these tests are its contract",
)

PX_FAST = 10            # px/mm for property tests where only exactness or order matters
PX_REG = 20             # px/mm for registration tests (the plan's C1 minimum)
PX_FINE = 40            # px/mm for the closed-form comparison
PX_EXACT = 8            # px/mm where shifts like 0.5 and 0.25 mm are exact in binary


@pytest.fixture(scope="module")
def sim():
    import placement_sim
    return placement_sim


# ---- closed-form helpers (independent of the implementation) --------------

def lens_fraction(a, r, s):
    """Fraction of a disc of radius a lying inside a disc of radius r whose
    centre is a distance s away (standard circle-intersection area)."""
    if s >= a + r:
        return 0.0
    if s <= abs(r - a):
        return 1.0 if a <= r else (r * r) / (a * a)
    ca = (s * s + a * a - r * r) / (2 * s * a)
    cr = (s * s + r * r - a * a) / (2 * s * r)
    area = (a * a * math.acos(ca) + r * r * math.acos(cr)
            - 0.5 * math.sqrt((-s + a + r) * (s + a - r) * (s - a + r) * (s + a + r)))
    return area / (math.pi * a * a)


def test_lens_fraction_reduces_to_equal_circle_formula():
    # Self-check of the helper against alignment.py's equal-circle formula.
    for d in (2.0, 5.0):
        for s in (0.0, 0.25, 0.5, 1.5):
            x = s / d
            want = 2 * (math.acos(x) - x * math.sqrt(1 - x * x)) / math.pi
            assert abs(lens_fraction(d / 2, d / 2, s) - want) < 1e-12


def centre_px(n):
    return (n - 1) / 2.0


# ---- constants and scene ----------------------------------------------------

def test_constants_follow_the_plan(sim):
    d = tuple(sim.DIAMETERS_MM)
    assert d == tuple(sorted(d)) and len(set(d)) == len(d)
    assert d[0] == 2.0 and d[-1] == 8.0 and len(d) >= 4
    s = tuple(sim.SHIFTS)
    assert s == tuple(sorted(s)) and {0.0, 0.25, 0.3, 0.5} <= set(s)
    assert sim.RING_GAP_MM == 1.0 and sim.RING_WIDTH_MM == 1.5
    assert sim.INNER_FRACTION == 0.6
    assert sim.STICKER_SD_MM == 0.1
    assert tuple(sim.PLACEMENTS) == ("none", "ring_registration", "sticker")
    assert tuple(sim.REGIONS) == ("outline", "inner_disc")
    want = {"unchanged": (1.0, 1.0), "genuine_fading": (0.5, 1.0), "invisible": (0.0, 1.0),
            "dark_overshoot": (-1.0 / 3.0, 1.0), "shrinking": (1.0, 0.7)}
    assert set(sim.SCENARIOS) == set(want)
    for k, (c, dscale) in want.items():
        assert sim.SCENARIOS[k][0] == pytest.approx(c, abs=1e-12)
        assert sim.SCENARIOS[k][1] == pytest.approx(dscale, abs=1e-12)


def test_render_shape_and_field_holds_ring_plus_shift(sim):
    for d in (2.0, 8.0):
        n = sim.field_size(d, PX_FAST)
        img = sim.render(d, px_per_mm=PX_FAST)
        assert img.shape == (n, n, 3) and img.dtype.kind == "f"
        outer = d / 2 + sim.RING_GAP_MM + sim.RING_WIDTH_MM + max(sim.SHIFTS)
        assert n / PX_FAST / 2 > outer


def test_white_spot_is_lighter(sim):
    c = sim.measure_contrast(sim.render(8.0, px_per_mm=PX_FAST), 8.0, PX_FAST)
    assert c["L"] >= 5.0


def test_render_rejects_nonpositive_diameter(sim):
    for bad in (0.0, -2.0):
        with pytest.raises(ValueError):
            sim.render(bad, px_per_mm=PX_FAST)


def test_zero_mottle_is_exactly_uniform(sim):
    a = sim.render(4.0, px_per_mm=PX_FAST, background="uniform")
    b = sim.render(4.0, px_per_mm=PX_FAST, background="mottled", mottle_sd=0.0, seed=3)
    assert np.array_equal(a, b)


@pytest.mark.parametrize("axis", ["x", "y"])
def test_shift_moves_skin_and_spot_together(sim, axis):
    k = 3                                   # whole pixels; exact for any sensible renderer
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=4)
    base = sim.render(4.0, **kw)
    sh = (k / PX_FAST, 0.0) if axis == "x" else (0.0, k / PX_FAST)
    moved = sim.render(4.0, shift_mm=sh, **kw)
    i = slice(2 * k, -2 * k)                # ignore the edge pixels that enter the field
    j = slice(2 * k + k, -2 * k + k)
    if axis == "x":
        assert np.allclose(moved[i, j], base[i, i], atol=1e-6)
    else:
        assert np.allclose(moved[j, i], base[i, i], atol=1e-6)


def test_float_shift_means_x_only(sim):
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, seed=4)
    assert np.array_equal(sim.render(4.0, shift_mm=0.3, **kw),
                          sim.render(4.0, shift_mm=(0.3, 0.0), **kw))


def test_invisible_spot_has_no_contrast(sim):
    img = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    for region in sim.REGIONS:
        c = sim.measure_contrast(img, 4.0, PX_FAST, region=region)
        assert max(abs(c["L"]), abs(c["a"]), abs(c["b"])) < 1e-9


def test_measuring_at_the_true_centre_undoes_the_shift(sim):
    # Sign convention: the spot centre after shift_mm is at centre_mm = shift_mm.
    # Whole-pixel shift, noise-free mottled skin: exact up to float round-off.
    # PX_EXACT keeps every mask edge free of float round-off.
    sh = (4 / PX_EXACT, -2 / PX_EXACT)
    kw = dict(px_per_mm=PX_EXACT, background="mottled", mottle_sd=0.05, seed=8)
    base = sim.render(3.0, **kw)
    moved = sim.render(3.0, shift_mm=sh, **kw)
    for region in sim.REGIONS:
        a = sim.measure_contrast(base, 3.0, PX_EXACT, region=region)
        b = sim.measure_contrast(moved, 3.0, PX_EXACT, region=region, centre_mm=sh)
        for ch in "Lab":
            assert abs(a[ch] - b[ch]) < 1e-6


# ---- regions ----------------------------------------------------------------

def test_segmented_region_is_refused_for_colour(sim):
    img = sim.render(4.0, px_per_mm=PX_FAST)
    for bad in ("segmented", "traced", ""):
        with pytest.raises(ValueError):
            sim.measure_contrast(img, 4.0, PX_FAST, region=bad)
        with pytest.raises(ValueError):
            sim.change_pct(img, img, 4.0, PX_FAST, region=bad)


def test_inner_fraction_must_be_inside_zero_one(sim):
    img = sim.render(4.0, px_per_mm=PX_FAST)
    for bad in (0.0, 1.0, 1.2, -0.5):
        with pytest.raises(ValueError):
            sim.measure_contrast(img, 4.0, PX_FAST, region="inner_disc", inner_fraction=bad)


# ---- the five required properties ------------------------------------------

@pytest.mark.parametrize("region", ["outline", "inner_disc"])
@pytest.mark.parametrize("background", ["uniform", "mottled"])
def test_zero_shift_zero_change_gives_zero_error(sim, region, background):
    kw = dict(px_per_mm=PX_FAST, background=background, mottle_sd=0.05, seed=9)
    for d in sim.DIAMETERS_MM:
        # Identical inputs must give exactly zero; 1e-9 allows only float round-off.
        got = sim.change_pct(sim.render(d, **kw), sim.render(d, **kw), d, PX_FAST, region=region)
        assert abs(got) < 1e-9


def test_run_rows_without_shift_or_noise_have_zero_error(sim):
    rows = sim.run(seed=1, trials=2, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   shifts=(0.0,), scenarios=("unchanged",), noise_sd=0.0, sticker_sd_mm=0.0)
    assert rows, "run() returned no rows"
    for r in rows:
        assert float(r["shift_mm"]) == 0.0
        assert float(r["true_change_pct"]) == 0.0
        if r["placement"] == "ring_registration" and r["background"] == "uniform":
            continue                        # no texture to register on: may refuse
        assert r["rejected"] == 0, r
        assert abs(float(r["mean_abs_error_pct_points"])) < 1e-9, r
        assert abs(float(r["mean_change_L"])) < 1e-9, r
        assert abs(float(r["mean_centre_error_mm"])) < 1e-9, r


def test_outline_matches_closed_form_circle_overlap(sim):
    # Uniform skin, no blur, no noise, placement "none". With per-pixel Lab
    # averaging, contrast inside a displaced outline falls by exactly the
    # uncovered fraction. Tolerance 1.0 percentage point at 40 px/mm: the pixel
    # model in data/alignment_validation.csv differs from the formula by at most
    # 0.63 points at 40 px/mm (2 mm spot; edge pixels part spot, part skin).
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE)
        for s in (0.25, 0.5, 0.75):         # <= ring gap, so the ring stays clean
            follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=s)
            got = sim.change_pct(base, follow, d, PX_FINE, region="outline")
            want = 100 * (lens_fraction(d / 2, d / 2, s) - 1)
            assert abs(got - want) < 1.0, (d, s, got, want)


def test_inner_disc_matches_closed_form_lens_overlap(sim):
    # Same scene; S is a disc of radius 0.6 r, the spot a disc of radius r,
    # centres s apart. Retained fraction = lens area / area of S.
    # Tolerance 2.0 points: the 1.0-point edge-pixel allowance above scales with
    # perimeter / area, i.e. 1 / radius, and S has 0.6 of the outline's radius
    # (1.0 / 0.6 = 1.7, rounded up).
    f = sim.INNER_FRACTION
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE)
        for s in (0.25, 0.5, 0.75):
            follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=s)
            got = sim.change_pct(base, follow, d, PX_FINE, region="inner_disc")
            want = 100 * (lens_fraction(f * d / 2, d / 2, s) - 1)
            assert abs(got - want) < 2.0, (d, s, got, want)


def test_inner_disc_unaffected_while_inside_spot(sim):
    # Plan 4.4 geometry: with r_S = 0.6 r and no blur, S stays wholly inside the
    # spot for shifts up to 0.4 r. At 0.25 mm on a 2 mm spot the edge of S is
    # 0.15 mm (6 px at 40 px/mm) inside the spot edge, so only anti-aliasing
    # wider than 6 px could reach it. Tolerance 0.1 point (float and
    # one-pixel anti-aliasing only).
    base = sim.render(2.0, px_per_mm=PX_FINE)
    follow = sim.render(2.0, px_per_mm=PX_FINE, shift_mm=0.25)
    assert abs(sim.change_pct(base, follow, 2.0, PX_FINE, region="inner_disc")) < 0.1


def test_error_grows_as_spot_shrinks_outline(sim):
    errs = []
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE)
        follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=0.25)
        errs.append(abs(sim.change_pct(base, follow, d, PX_FINE, region="outline")))
    # Deterministic and strictly ordered: smallest spot, largest false fading.
    assert all(a > b for a, b in zip(errs, errs[1:])), errs


def test_error_grows_as_spot_shrinks_inner_disc(sim):
    # At 0.5 mm, S on a 2 mm spot crosses the edge (0.4 r = 0.4 mm); on 8 mm it
    # does not (0.4 r = 1.6 mm). Closed form: -5.77 points vs 0. Required
    # margin: at least 2 points between them, a third of the closed-form gap.
    e2 = abs(sim.change_pct(sim.render(2.0, px_per_mm=PX_FINE),
                            sim.render(2.0, px_per_mm=PX_FINE, shift_mm=0.5),
                            2.0, PX_FINE, region="inner_disc"))
    e8 = abs(sim.change_pct(sim.render(8.0, px_per_mm=PX_FINE),
                            sim.render(8.0, px_per_mm=PX_FINE, shift_mm=0.5),
                            8.0, PX_FINE, region="inner_disc"))
    assert e2 > e8 + 2.0, (e2, e8)


def test_error_grows_as_spot_shrinks_in_run_mottled(sim):
    rows = sim.run(seed=2, trials=4, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   shifts=(0.5,), scenarios=("unchanged",), noise_sd=0.0)
    pick = {float(r["diameter_mm"]): float(r["mean_abs_error_pct_points"])
            for r in rows if r["background"] == "mottled" and r["placement"] == "none"
            and r["region"] == "outline"}
    # Geometry alone gives about 26 vs 6 points (drift CSV lines 22 and 172);
    # a factor 2 leaves room for texture effects in 4 trials.
    assert pick[2.0] > 2 * pick[8.0], pick


def test_same_seed_reruns_are_identical(sim):
    kw = dict(seed=5, trials=2, px_per_mm=PX_FAST, diameters=(2.0,), shifts=(0.25,),
              scenarios=("unchanged", "genuine_fading"))
    assert sim.run(**kw) == sim.run(**kw)
    img_kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05, noise_sd=0.01, seed=5)
    assert np.array_equal(sim.render(3.0, **img_kw), sim.render(3.0, **img_kw))
    p = dict(true_shift_mm=(0.2, 0.1), sticker_sd_mm=0.1, seed=7)
    img = sim.render(3.0, px_per_mm=PX_FAST)
    assert sim.place("sticker", img, img, 3.0, PX_FAST, **p) == \
        sim.place("sticker", img, img, 3.0, PX_FAST, **p)


def test_different_seeds_give_different_texture(sim):
    kw = dict(px_per_mm=PX_FAST, background="mottled", mottle_sd=0.05)
    assert not np.array_equal(sim.render(3.0, seed=1, **kw), sim.render(3.0, seed=2, **kw))


@pytest.mark.parametrize("region", ["outline", "inner_disc"])
def test_zero_contrast_baseline_is_refused(sim, region):
    flat = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    spot = sim.render(4.0, px_per_mm=PX_FAST)
    with pytest.raises(ZeroDivisionError):
        sim.change_pct(flat, spot, 4.0, PX_FAST, region=region)
    with pytest.raises(ZeroDivisionError):
        sim.change_pct(flat, flat, 4.0, PX_FAST, region=region)


# ---- placement: none and sticker --------------------------------------------

def test_place_none_is_the_frame_centre(sim):
    img = sim.render(3.0, px_per_mm=PX_FAST)
    assert tuple(sim.place("none", img, img, 3.0, PX_FAST, true_shift_mm=(0.3, 0.2))) == (0.0, 0.0)


def test_place_rejects_unknown_method(sim):
    img = sim.render(3.0, px_per_mm=PX_FAST)
    for bad in ("segmentation", "outline", ""):
        with pytest.raises(ValueError):
            sim.place(bad, img, img, 3.0, PX_FAST)


def test_sticker_without_noise_returns_truth(sim):
    img = sim.render(3.0, px_per_mm=PX_FAST)
    got = sim.place("sticker", img, img, 3.0, PX_FAST, true_shift_mm=(0.37, -0.12),
                    sticker_sd_mm=0.0, seed=1)
    assert tuple(got) == (0.37, -0.12)


def test_sticker_noise_has_requested_size(sim):
    img = sim.render(3.0, px_per_mm=PX_FAST)
    sd, n = 0.1, 2000
    pts = np.array([sim.place("sticker", img, img, 3.0, PX_FAST, true_shift_mm=(0.5, 0.0),
                              sticker_sd_mm=sd, seed=k) for k in range(n)])
    err = pts - np.array([0.5, 0.0])
    # With 2000 draws the sample SD is within about 1.6 % (1 standard error) of
    # the target; 10 % is over 6 standard errors. Mean within 4 standard errors
    # of zero (4 * 0.1 / sqrt(2000) = 0.009 mm), per axis.
    for axis in (0, 1):
        assert abs(err[:, axis].std() / sd - 1) < 0.10
        assert abs(err[:, axis].mean()) < 4 * sd / math.sqrt(n)
    # Axes independent: correlation within 4 standard errors (4 / sqrt(2000)).
    assert abs(np.corrcoef(err[:, 0], err[:, 1])[0, 1]) < 4 / math.sqrt(n)


# ---- placement: registration on the surrounding skin only ------------------

def test_ring_registration_recovers_whole_pixel_shift(sim):
    # Noise-free mottled skin, whole-pixel shift in both axes. Tolerance half a
    # pixel (0.025 mm at 20 px/mm): an integer-pixel estimator recovers an
    # integer shift exactly; a sub-pixel estimator should not do worse.
    d, sh = 2.0, (3 / PX_REG, -2 / PX_REG)
    kw = dict(px_per_mm=PX_REG, background="mottled", mottle_sd=0.05, seed=21)
    base, follow = sim.render(d, **kw), sim.render(d, shift_mm=sh, **kw)
    got = sim.place("ring_registration", base, follow, d, PX_REG)
    assert got is not None
    assert abs(got[0] - sh[0]) <= 0.5 / PX_REG and abs(got[1] - sh[1]) <= 0.5 / PX_REG, got


def test_ring_registration_with_noise_and_subpixel_shift(sim):
    # Capture noise SD 0.01 (drift_sim's default) on 5 % mottle, shift not a
    # whole number of pixels. Tolerance 1 pixel (0.05 mm at 20 px/mm): half a
    # pixel of quantisation plus half a pixel for noise. This is a correctness
    # check of the estimator, not the plan's target: 0.05 mm is well inside the
    # 0.3 mm the inner disc tolerates on a 2 mm spot (plan 4.4).
    # render() draws noise from the same seed as the texture, so both visits
    # are rendered noise-free and independent noise is added here.
    d, sh = 2.0, (0.27, 0.11)
    kw = dict(px_per_mm=PX_REG, background="mottled", mottle_sd=0.05, seed=22)
    rng = np.random.default_rng(99)
    base = sim.render(d, **kw)
    follow = sim.render(d, shift_mm=sh, **kw)
    base = base + rng.normal(0.0, 0.01, base.shape)
    follow = follow + rng.normal(0.0, 0.01, follow.shape)
    got = sim.place("ring_registration", base, follow, d, PX_REG)
    assert got is not None
    assert abs(got[0] - sh[0]) <= 1.0 / PX_REG and abs(got[1] - sh[1]) <= 1.0 / PX_REG, got


def test_ring_registration_ignores_the_spot_and_gap(sim):
    # Plan 4.2: registering on the spot is not acceptable, because a changing
    # spot would move the registration with it. Overwrite everything within
    # r + gap of the frame centre (less 2 px of slack) in the follow-up; the
    # estimate must not change at all.
    d, sh = 3.0, (0.25, 0.15)
    kw = dict(px_per_mm=PX_REG, background="mottled", mottle_sd=0.05, seed=23)
    base, follow = sim.render(d, **kw), sim.render(d, shift_mm=sh, **kw)
    n = follow.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(xx - centre_px(n), yy - centre_px(n)) / PX_REG
    inside = rr < d / 2 + sim.RING_GAP_MM - 2 / PX_REG
    vandal = follow.copy()
    vandal[inside] = np.random.default_rng(5).uniform(0.0, 1.0, (int(inside.sum()), 3))
    a = sim.place("ring_registration", base, follow, d, PX_REG)
    b = sim.place("ring_registration", base, vandal, d, PX_REG)
    assert a is not None and b is not None
    assert tuple(a) == tuple(b)


def test_ring_registration_does_not_read_the_true_shift(sim):
    d, sh = 2.0, (0.2, 0.0)
    kw = dict(px_per_mm=PX_REG, background="mottled", mottle_sd=0.05, seed=24)
    base, follow = sim.render(d, **kw), sim.render(d, shift_mm=sh, **kw)
    a = sim.place("ring_registration", base, follow, d, PX_REG, true_shift_mm=(0.0, 0.0))
    b = sim.place("ring_registration", base, follow, d, PX_REG, true_shift_mm=(9.0, -9.0))
    assert tuple(a) == tuple(b)


def test_ring_registration_refuses_without_texture(sim):
    # Uniform skin, no noise: nothing outside the gap to register on. Plan C10:
    # refuse (None), never return a guess.
    base = sim.render(2.0, px_per_mm=PX_REG)
    follow = sim.render(2.0, px_per_mm=PX_REG, shift_mm=0.25)
    assert sim.place("ring_registration", base, follow, 2.0, PX_REG) is None


# ---- segmentation, for area only -------------------------------------------

def test_segment_area_on_clean_spots(sim):
    # Noise-free, no blur, 40 px/mm. Tolerance 5 %: a half-pixel boundary error
    # on a disc of radius R px changes area by about 2 * 0.5 / R, which is 2.5 %
    # for the 2 mm spot (R = 40 px) and 3.6 % for its shrunken 1.4 mm version
    # (R = 28 px); 5 % leaves margin above both.
    for d in (2.0, 8.0):
        for dscale in (1.0, 0.7):
            img = sim.render(d, px_per_mm=PX_FINE, diameter_scale=dscale)
            want = math.pi * (d * dscale / 2) ** 2
            got = sim.segment_area(img, d, PX_FINE)
            assert abs(got / want - 1) < 0.05, (d, dscale, got, want)


def test_segment_area_is_zero_when_no_lighter_spot(sim):
    for c in (0.0, -1.0 / 3.0):            # invisible; overshoot to darker than skin
        img = sim.render(3.0, px_per_mm=PX_FAST, contrast_scale=c)
        assert sim.segment_area(img, 3.0, PX_FAST) == 0.0


# ---- the experiment ---------------------------------------------------------

@pytest.fixture(scope="module")
def small_run(sim):
    return sim.run(seed=3, trials=2, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   shifts=(0.0, 0.5))


def test_run_has_one_row_per_combination(sim, small_run):
    keys = [(r["scenario"], r["background"], float(r["diameter_mm"]), float(r["shift_mm"]),
             r["placement"], r["region"]) for r in small_run]
    assert len(keys) == len(set(keys))
    want = {(sc, bg, d, s, p, rg) for sc in sim.SCENARIOS for bg in ("uniform", "mottled")
            for d in (2.0, 8.0) for s in (0.0, 0.5) for p in sim.PLACEMENTS for rg in sim.REGIONS}
    assert set(keys) == want


def test_run_rows_have_required_keys(small_run):
    need = {"scenario", "background", "diameter_mm", "shift_mm", "placement", "region",
            "true_change_pct", "mean_change_pct", "sd_change_pct", "mean_abs_error_pct_points",
            "base_contrast_L", "mean_change_L", "mean_centre_error_mm", "area_true_mm2",
            "area_mean_mm2", "area_error_pct", "trials", "rejected"}
    for r in small_run:
        assert need <= set(r), need - set(r)
        assert r["trials"] == 2 and 0 <= r["rejected"] <= 2


def test_true_change_follows_the_scenario(small_run):
    for r in small_run:
        t = float(r["true_change_pct"])
        sc = r["scenario"]
        if sc == "unchanged":
            assert t == 0.0
        elif sc == "invisible":
            assert abs(t + 100.0) < 1e-6
        elif sc == "dark_overshoot":
            assert t < -100.0
        elif sc == "genuine_fading":
            assert -100.0 < t < 0.0
        elif sc == "shrinking" and r["region"] == "outline":
            assert t < 0.0


def test_true_change_does_not_depend_on_shift_or_placement(small_run):
    by = {}
    for r in small_run:
        k = (r["scenario"], r["background"], float(r["diameter_mm"]), r["region"])
        by.setdefault(k, set()).add(round(float(r["true_change_pct"]), 9))
    for k, v in by.items():
        if k[1] == "uniform":               # mottled truth may differ per texture draw
            assert len(v) == 1, (k, v)


def test_placements_share_the_same_captures(small_run):
    # Paired design: area is measured on the follow-up captures independently of
    # placement and region, and the baseline contrast is measured at the frame
    # centre, so both must be identical across placements within a cell.
    area, base = {}, {}
    for r in small_run:
        k = (r["scenario"], r["background"], float(r["diameter_mm"]), float(r["shift_mm"]))
        area.setdefault(k, set()).add(r["area_mean_mm2"])
        base.setdefault(k + (r["region"],), set()).add(r["base_contrast_L"])
    for k, v in list(area.items()) + list(base.items()):
        assert len(v) == 1, (k, v)


def test_uniform_ring_registration_rows_are_rejected_not_guessed(sim):
    rows = sim.run(seed=4, trials=2, px_per_mm=PX_FAST, diameters=(2.0,), shifts=(0.5,),
                   scenarios=("unchanged",), noise_sd=0.0)
    for r in rows:
        if r["placement"] == "ring_registration" and r["background"] == "uniform":
            assert r["rejected"] == r["trials"]
            assert r["mean_change_pct"] is None and r["sd_change_pct"] is None


def test_run_rejects_unknown_scenario(sim):
    with pytest.raises((ValueError, KeyError)):
        sim.run(seed=1, trials=1, px_per_mm=PX_FAST, diameters=(2.0,), shifts=(0.0,),
                scenarios=("brown",))


# ---- target evaluation (logic only, on hand-made rows) ---------------------

def _rows(**override):
    """Rows for one placement x region that meet every criterion; override a
    cell with key (scenario, shift, field) -> value."""
    out = []
    for sc, true in (("unchanged", 0.0), ("genuine_fading", -50.0), ("shrinking", -51.0)):
        for s in (0.0, 0.25, 0.3, 0.5):
            for p in ("none", "ring_registration", "sticker"):
                for rg in ("outline", "inner_disc"):
                    r = dict(scenario=sc, background="mottled", diameter_mm=2.0, shift_mm=s,
                             placement=p, region=rg, true_change_pct=true,
                             mean_change_pct=true + 0.1, sd_change_pct=0.5,
                             mean_abs_error_pct_points=0.4, area_error_pct=3.0,
                             trials=10, rejected=0)
                    for (o_sc, o_s, o_p, o_rg, field), v in override.items():
                        if (o_sc, o_s, o_p, o_rg) == (sc, s, p, rg):
                            r[field] = v
                    out.append(r)
    return out


def test_evaluate_target_all_pass(sim):
    res = sim.evaluate_target(_rows())
    for p in sim.PLACEMENTS:
        for rg in sim.REGIONS:
            e = res[(p, rg)]
            assert e["false_change_ok"] and e["sd_ok"] and e["sensitivity_ok"] and e["passes"]
            if rg == "inner_disc":
                assert e["within_noise_to_0_3mm"] is True
            else:
                assert e["within_noise_to_0_3mm"] is None
    assert res["area_ok"] is True


@pytest.mark.parametrize("override, key", [
    ({("unchanged", 0.5, "sticker", "inner_disc", "mean_change_pct"): -2.5}, "false_change_ok"),
    ({("unchanged", 0.5, "sticker", "inner_disc", "sd_change_pct"): 1.2}, "sd_ok"),
    ({("genuine_fading", 0.5, "sticker", "inner_disc", "mean_change_pct"): -47.5}, "sensitivity_ok"),
    ({("unchanged", 0.3, "sticker", "inner_disc", "mean_change_pct"): 0.8}, "within_noise_to_0_3mm"),
])
def test_evaluate_target_each_criterion_can_fail(sim, override, key):
    e = sim.evaluate_target(_rows(**override))[("sticker", "inner_disc")]
    assert e[key] is False and e["passes"] is False
    assert sim.evaluate_target(_rows(**override))[("none", "inner_disc")]["passes"] is True


def test_evaluate_target_thresholds_are_inclusive(sim):
    # Plan wording is "<= 2 %", "<= 1 point", "within +/- 2 points".
    o = {("unchanged", 0.5, "none", "outline", "mean_change_pct"): 2.0,
         ("unchanged", 0.5, "none", "outline", "sd_change_pct"): 1.0,
         ("genuine_fading", 0.5, "none", "outline", "mean_change_pct"): -48.0}
    assert sim.evaluate_target(_rows(**o))[("none", "outline")]["passes"] is True


def test_evaluate_target_all_rejected_does_not_pass(sim):
    o = {("unchanged", 0.5, "ring_registration", "inner_disc", "mean_change_pct"): None,
         ("unchanged", 0.5, "ring_registration", "inner_disc", "sd_change_pct"): None,
         ("unchanged", 0.5, "ring_registration", "inner_disc", "rejected"): 10}
    assert sim.evaluate_target(_rows(**o))[("ring_registration", "inner_disc")]["passes"] is False


def test_evaluate_target_area_criterion(sim):
    o = {("shrinking", 0.5, "none", "outline", "area_error_pct"): -10.5}
    assert sim.evaluate_target(_rows(**o))["area_ok"] is False
    o = {("shrinking", 0.5, "none", "outline", "area_error_pct"): -10.0}
    assert sim.evaluate_target(_rows(**o))["area_ok"] is True


def test_evaluate_target_missing_row_is_an_error(sim):
    rows = [r for r in _rows() if not (r["scenario"] == "genuine_fading" and r["shift_mm"] == 0.5
                                       and r["placement"] == "sticker")]
    with pytest.raises(ValueError):
        sim.evaluate_target(rows)
