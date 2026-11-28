"""Tests for the registration stress simulation (placement round two), written
before the code exists.

SIMULATION ONLY. Synthetic disks, synthetic texture, synthetic straight "hairs".
No patient images.

Run:  python3 -m pytest experiments/tests -q

Until experiments/registration_stress_sim.py exists, every test here is SKIPPED
(see `pytestmark`), so the existing suite stays green. As soon as the builder
adds that file the tests run unchanged; the builder may not edit this file:
`git diff --exit-code <tests commit> -- experiments/tests` must stay clean.

WHY THIS ROUND
  Round one (experiments/placement_sim.py, PR 27, content/experiments.md
  section 5) found that only registration on the surrounding skin meets the
  plan's section 4 target at 2 mm, 0.5 mm misplacement, mottled skin. It tested
  registration in its best case: the skin texture was identical at both visits
  apart from noise. This round adds four disturbances a real follow-up photo
  has, one at a time and combined, and asks at which size each one breaks the
  same target:
    1. hair lying across the spot and the ring (plan 2.1 item 3, C10);
    2. tanning of the surrounding skin between sessions (plan 2.1 item 9, C9);
    3. rotation of the camera about its axis between sessions (plan C6, C7);
    4. uneven lighting: a linear gradient and vignetting (plan C3, rung 1).

SOURCE OF THE SPECIFICATION: content/measurement-tool-plan.md sections 2.1, 3,
4 and 5 (rung 1), and round one's contract in test_placement_sim.py, whose
conventions are kept. Where the plan leaves a choice open, the choice made here
is marked READING and can be changed by Ben. Every disturbance size below is an
ASSUMPTION chosen to bracket plausible conditions; none comes from a quoted
source, so none may be cited as a fact about real skin or real cameras.

This file asserts what the simulation must compute (exact rendering of each
disturbance, what counts as truth, refusals, reproducibility, the bookkeeping
of the target). It does NOT assert whether any placement survives any
disturbance: that is the experiment's result, computed by
`evaluate_stress_target` and `breaking_levels` and reported, not presumed here.
The only accuracy checks on an estimator are on noise-free scenes, where they
test that the estimator does what its name says.

Conventions (as round one)
  Linear RGB in, CIELAB (D65) computed PER PIXEL, then averaged.
  Image axes: x = column index (increasing right), y = row index (increasing down).
  The frame centre, centre_mm = (0, 0), is at pixel ((n - 1) / 2, (n - 1) / 2).
  Angles: positive rotation_deg turns the scene COUNTER-CLOCKWISE as the image
  is displayed (a scene point at (+1, 0) mm moves towards (0, -1) mm), which is
  what numpy.rot90(img, k=1) does for 90 degrees.

Constants
  DIAMETERS_MM   sorted tuple, contains 2.0 (the plan's target size).
  SHIFT_MM = 0.5 follow-up misplacement along x (the plan's section 4 target).
  RING_GAP_MM, RING_WIDTH_MM, INNER_FRACTION, STICKER_SD_MM, SKIN_RGB,
  WHITE_SPOT_RGB: identical to placement_sim's.
  SCENARIOS = {"unchanged": (1, 1), "genuine_fading": (0.5, 1)}, the two the
                 target needs; (contrast_scale, diameter_scale) as round one.
  PLACEMENTS = ("none", "ring_registration", "ring_registration_rigid", "sticker")
  REGIONS    = ("outline", "inner_disc")
  HAIR_MASKS = ("none", "detected")
  HAIR_RGB       linear-RGB triple, darker than SKIN_RGB in every channel.
  HAIR_WIDTH_MM  in [0.03, 0.12]. ASSUMPTION, not from a quoted source.
  SPOT_TAN_FRACTION = 0.0  READING: the spot does not tan with the skin around
                 it. Partial tanning of the spot is a parameter, not modelled
                 by default, because no quoted source gives its size.
  MAX_RING_EXCLUDED = 0.20  plan C10: refuse a capture whose ring is more than
                 20 % masked.
  MAX_REJECTED_FRACTION = 0.10  READING of "a method that refuses too often
                 does not pass": with k = 3 captures per session (plan 2.2)
                 and independent 10 % refusals, a session ends with no usable
                 capture 0.1 % of the time.
  DISTURBANCES   dict name -> dict(family, level, **render kwargs), exactly as
                 in `WANT_DISTURBANCES` below. Levels sort by severity inside a
                 family. "combined" stacks one level of each.

Scene and capture
  field_size(diameter_mm, px_per_mm) -> n (as round one).
  render(diameter_mm, *, px_per_mm=20, contrast_scale=1.0, diameter_scale=1.0,
         background="uniform" | "mottled", mottle_sd=0.0, mottle_corr_mm=1.0,
         shift_mm=(0.0, 0.0), noise_sd=0.0, blur_sd_mm=0.0, seed=0,
         tan_dL=0.0, tan_texture_sd=0.0, tan_seed=0,
         spot_tan_fraction=SPOT_TAN_FRACTION,
         rotation_deg=0.0,
         hair_count=0, hair_width_mm=HAIR_WIDTH_MM, hair_seed=0,
         gradient=0.0, gradient_dir_deg=0.0, vignetting=0.0)
      -> float ndarray (n, n, 3), linear RGB. Order of operations:
      1. SCENE: round one's skin texture and spot (same seed gives the same
         texture). Tanning multiplies the skin: every channel by one gain k,
         chosen so that k * SKIN_RGB has L* exactly L*(SKIN_RGB) + tan_dL;
         with tan_texture_sd > 0 it also multiplies by (1 + t(x)), t a new
         continuous texture of that SD drawn from tan_seed (patchy tanning,
         which changes the texture registration relies on). Inside the spot the
         tanning factor is raised to the power spot_tan_fraction (0 = the spot
         keeps its colour), blended by the spot's edge coverage.
      2. GEOMETRY: a scene point p (mm, base frame) appears at R(rotation) p +
         shift_mm. The spot centre is therefore at shift_mm whatever the
         rotation.
      3. HAIR, in the camera frame (hair is redrawn at each visit): hair_count
         straight strands of width hair_width_mm, each crossing the whole field,
         positions and angles from hair_seed. With coverage c = hair_coverage(..)
         in [0, 1]: img = (1 - c) * img + c * HAIR_RGB.
      4. LIGHTING, in the camera frame, multiplicative on every channel:
         I(x, y) = (1 + gradient * u / W) * (1 - vignetting * (rho / (W / 2))**2),
         u = x cos(gradient_dir_deg) + y sin(gradient_dir_deg) in mm from the
         frame centre (y increasing down), rho = distance from the frame centre
         in mm, W = n / px_per_mm, the field side in mm. So `gradient` is the
         end-to-end light difference across the field and `vignetting` the
         fall-off at the middle of each field edge.
      5. Blur, then noise, as round one.
      With every new parameter at its default, render() equals
      placement_sim.render() with the same arguments (round two extends round
      one; its "none" condition is round one's best case).
  hair_coverage(diameter_mm, *, px_per_mm=20, hair_count=0,
                hair_width_mm=HAIR_WIDTH_MM, hair_seed=0) -> float (n, n) in [0, 1].
  detect_hair(img, diameter_mm, px_per_mm) -> bool (n, n): hair pixels found
      from the image alone. Method is the builder's choice, stated in the module.

Measurement
  measure(img, diameter_mm, px_per_mm, *, region="outline" | "inner_disc",
          centre_mm=(0, 0), inner_fraction=INNER_FRACTION, exclude=None)
      -> {"L", "a", "b": mean Lab(S) - mean Lab(R);
          "ring_L", "ring_a", "ring_b": mean Lab(R), absolute (plan 2.1 item 9);
          "ring_excluded", "spot_excluded": fraction of R and S pixels dropped}.
      exclude: bool (n, n) or None; True pixels are left out of S and R.
      Regions as round one; any other region raises ValueError.
  change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, region="outline",
             base_centre_mm=(0, 0), follow_centre_mm=(0, 0),
             inner_fraction=INNER_FRACTION, base_exclude=None,
             follow_exclude=None, channel="L")
      -> 100 * (c_follow - c_base) / c_base.
      Raises ZeroDivisionError when |c_base| < 1e-6 (refused, never divided by).
      Raises CaptureRefused (an Exception subclass defined in the module) when
      either capture has ring_excluded > MAX_RING_EXCLUDED or spot_excluded == 1.

Placement
  register(base_img, follow_img, diameter_mm, px_per_mm, *,
           model="translation" | "rigid")
      -> {"dx", "dy", "angle_deg", "score"} or None (refused).
      Uses only pixels OUTSIDE radius diameter_mm / 2 + RING_GAP_MM of the frame
      centre (plan 4.2). "translation" always returns angle_deg = 0.0.
      (dx, dy) is the estimated follow-up spot centre in mm. Returns None when
      the masked area has no usable texture (plan C10). Any other model raises
      ValueError. Whether and how it masks hair is the builder's choice, stated
      in the module.
  place(method, base_img, follow_img, diameter_mm, px_per_mm, *,
        true_shift_mm=(0, 0), sticker_sd_mm=STICKER_SD_MM, seed=0)
      -> (dx, dy) or None. "none", "sticker" as round one; "ring_registration"
      = register(model="translation"); "ring_registration_rigid" =
      register(model="rigid"). Registration never reads true_shift_mm. Unknown
      method raises ValueError.

Experiment
  run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM,
      disturbances=tuple(DISTURBANCES), scenarios=tuple(SCENARIOS),
      shift_mm=SHIFT_MM, noise_sd=<default>, mottle_sd=<default>,
      blur_sd_mm=<default>, sticker_sd_mm=STICKER_SD_MM) -> list of dict rows.
      Mottled background only (registration needs texture). One row per
      scenario x disturbance x diameter x placement x region x hair_mask.
      Within one scenario x disturbance x diameter, every placement, region and
      hair mask is measured on the SAME captures (paired comparison).
      Each trial: one skin texture for both visits. Baseline capture: frame
      centre, even light, no rotation, no tanning, hair if the disturbance has
      hair. Follow-up capture: shifted by (shift_mm, 0), with the disturbance's
      tanning, rotation, hair (drawn independently of the baseline's) and
      lighting. If the disturbance has a gradient, gradient_dir_deg is drawn
      uniformly in [0, 360) per trial. Capture noise independent per visit.
      Baseline is measured at the frame centre. Hair mask "detected" passes
      detect_hair() of each capture as that capture's exclude; "none" passes None.
      TRUTH, per trial: change_pct between a noise-free baseline and a noise-free
      follow-up that keeps everything REAL (scenario, texture, tanning, shift,
      blur as in the run) and drops every CAPTURE nuisance (no hair, no
      rotation, even light), measured at the true centres with no exclusion.
      Tanning changes the measurand (contrast against the skin around the spot),
      so it is in the truth; hair, rotation and lighting are not.
      Row keys include: scenario, disturbance, family, level, diameter_mm,
      shift_mm, placement, region, hair_mask, true_change_pct (mean of per-trial
      truths), mean_change_pct, sd_change_pct, bias_pct_points (mean over
      accepted trials of measured - truth), sd_error_pct_points (sample SD,
      ddof = 1, of measured - truth), mean_abs_error_pct_points,
      base_contrast_L, mean_change_L, true_ring_dL, mean_ring_dL (follow-up
      minus baseline absolute ring L*), mean_centre_error_mm,
      mean_ring_excluded, trials, rejected, rejected_placement, rejected_mask.
      * rejected = rejected_placement (place() returned None) + rejected_mask
        (CaptureRefused); a trial is counted once, placement checked first.
      * Means are over accepted trials and None when none is accepted; SD
        fields are None when fewer than 2 are accepted.
  evaluate_stress_target(rows, *, diameter_mm=2.0)
      -> {(disturbance, placement, region, hair_mask): {"bias_ok", "sd_ok",
          "sensitivity_ok", "acceptance_ok", "passes"}}.
      Plan section 4 target, restated on error against truth because tanning
      makes the true change of an unchanged spot non-zero:
      * bias_ok: unchanged row |bias_pct_points| <= 2.
      * sd_ok: unchanged row sd_error_pct_points <= 1.
      * sensitivity_ok: genuine_fading row |bias_pct_points| <= 2.
      * acceptance_ok: rejected <= MAX_REJECTED_FRACTION * trials on both rows.
      * passes: all four. A None value fails its key. Thresholds inclusive.
      A required row that is missing raises ValueError.
  breaking_levels(evaluation)
      -> {(family, placement, region, hair_mask): lowest level whose
          disturbance does not pass, or None when every level passes}.
      Families "none" and "combined" are included like the others.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

pytestmark = pytest.mark.skipif(
    not (EXPERIMENTS / "registration_stress_sim.py").exists(),
    reason="experiments/registration_stress_sim.py not built yet; these tests are its contract",
)

PX_FAST = 10            # px/mm where only exactness or order matters
PX_REG = 20             # px/mm for registration (the plan's C1 minimum)
PX_FINE = 40            # px/mm for the closed-form comparison
MOTTLE = dict(background="mottled", mottle_sd=0.05)

# READING: the disturbance set. Sizes are ASSUMPTIONS (see module docstring).
#   hair: 2 and 8 strands across the field.
#   tan: skin 2 and 5 L* units darker (5 is the size the alignment simulation
#        used, data/alignment_results.csv line 50); "tan_patchy" adds a new 3 %
#        texture so the skin pattern itself changes.
#   rotation: 2, 5 and 10 degrees about the camera axis.
#   gradient: 5 % and 20 % end to end (plan section 5 rung 1).
#   vignetting: 10 % and 20 % fall-off at the edge midpoints.
#   combined: hair 2 + patchy tan 5 + rotation 5 + gradient 20.
WANT_DISTURBANCES = {
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
TRUTH_FREE = ("none", "hair_2", "hair_8", "rotation_2", "rotation_5", "rotation_10",
              "gradient_5", "gradient_20", "vignetting_10", "vignetting_20")


@pytest.fixture(scope="module")
def sim():
    import registration_stress_sim
    return registration_stress_sim


def lens_fraction(a, r, s):
    """Fraction of a disc of radius a inside a disc of radius r, centres s apart."""
    if s >= a + r:
        return 0.0
    if s <= abs(r - a):
        return 1.0 if a <= r else (r * r) / (a * a)
    ca = (s * s + a * a - r * r) / (2 * s * a)
    cr = (s * s + r * r - a * a) / (2 * s * r)
    area = (a * a * math.acos(ca) + r * r * math.acos(cr)
            - 0.5 * math.sqrt((-s + a + r) * (s + a - r) * (s - a + r) * (s + a + r)))
    return area / (math.pi * a * a)


def grid_mm(n, px):
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    return (xx - c) / px, (yy - c) / px


# ---- constants ---------------------------------------------------------------

def test_constants_follow_the_plan_and_round_one(sim):
    import placement_sim as p1
    d = tuple(sim.DIAMETERS_MM)
    assert d == tuple(sorted(d)) and 2.0 in d
    assert sim.SHIFT_MM == 0.5
    for k in ("RING_GAP_MM", "RING_WIDTH_MM", "INNER_FRACTION", "STICKER_SD_MM"):
        assert getattr(sim, k) == getattr(p1, k), k
    assert tuple(sim.SKIN_RGB) == tuple(p1.SKIN_RGB)
    assert tuple(sim.WHITE_SPOT_RGB) == tuple(p1.WHITE_SPOT_RGB)
    assert set(sim.SCENARIOS) == {"unchanged", "genuine_fading"}
    assert tuple(sim.SCENARIOS["unchanged"]) == (1.0, 1.0)
    assert tuple(sim.SCENARIOS["genuine_fading"]) == (0.5, 1.0)
    assert tuple(sim.PLACEMENTS) == ("none", "ring_registration", "ring_registration_rigid", "sticker")
    assert tuple(sim.REGIONS) == ("outline", "inner_disc")
    assert tuple(sim.HAIR_MASKS) == ("none", "detected")
    assert all(h < s for h, s in zip(sim.HAIR_RGB, sim.SKIN_RGB))
    assert 0.03 <= sim.HAIR_WIDTH_MM <= 0.12
    assert sim.SPOT_TAN_FRACTION == 0.0
    assert sim.MAX_RING_EXCLUDED == 0.20
    assert sim.MAX_REJECTED_FRACTION == 0.10
    assert issubclass(sim.CaptureRefused, Exception)


def test_disturbance_set_is_exactly_the_stated_one(sim):
    assert set(sim.DISTURBANCES) == set(WANT_DISTURBANCES)
    for name, want in WANT_DISTURBANCES.items():
        got = dict(sim.DISTURBANCES[name])
        for k, v in want.items():
            assert got.get(k) == v, (name, k, got.get(k), v)
        render_keys = set(got) - {"family", "level"}
        assert render_keys == set(want) - {"family", "level"}, (name, render_keys)


# ---- scene: round one is kept ------------------------------------------------

@pytest.mark.parametrize("kw", [
    dict(px_per_mm=PX_FAST),
    dict(px_per_mm=PX_FAST, seed=3, **MOTTLE),
    dict(px_per_mm=PX_FAST, seed=3, shift_mm=(0.3, -0.2), blur_sd_mm=0.1, **MOTTLE),
    dict(px_per_mm=PX_FAST, seed=4, contrast_scale=0.5, diameter_scale=0.7, **MOTTLE),
])
def test_no_disturbance_reproduces_round_one(sim, kw):
    import placement_sim as p1
    for d in (2.0, 5.0):
        a = sim.render(d, **kw)
        b = p1.render(d, **kw)
        assert a.shape == b.shape and np.allclose(a, b, rtol=0, atol=1e-12)


def test_render_rejects_nonpositive_diameter(sim):
    for bad in (0.0, -2.0):
        with pytest.raises(ValueError):
            sim.render(bad, px_per_mm=PX_FAST)


# ---- disturbance 1: hair ----------------------------------------------------

def test_zero_hair_changes_nothing(sim):
    kw = dict(px_per_mm=PX_FAST, seed=5, **MOTTLE)
    assert np.array_equal(sim.render(3.0, **kw), sim.render(3.0, hair_count=0, hair_seed=9, **kw))
    cov = sim.hair_coverage(3.0, px_per_mm=PX_FAST, hair_count=0, hair_seed=9)
    assert cov.shape == (sim.field_size(3.0, PX_FAST),) * 2 and not cov.any()


def test_hair_is_composited_over_the_scene_then_lit(sim):
    # Step 3 then step 4 of render(), exactly (noise-free, no blur). 1e-9 allows
    # float round-off only.
    d, kw = 3.0, dict(px_per_mm=PX_FAST, seed=6, **MOTTLE)
    hk = dict(hair_count=4, hair_width_mm=0.08, hair_seed=11)
    light = dict(gradient=0.2, gradient_dir_deg=30.0, vignetting=0.1)
    c = sim.hair_coverage(d, px_per_mm=PX_FAST, **hk)[..., None]
    assert c.min() >= 0.0 and c.max() <= 1.0 and c.max() > 0.5
    plain = sim.render(d, **kw)
    lit_plain = sim.render(d, **light, **kw)
    want = (1 - c) * plain + c * np.asarray(sim.HAIR_RGB)
    assert np.allclose(sim.render(d, **hk, **kw), want, rtol=0, atol=1e-9)
    ratio = lit_plain / plain
    assert np.allclose(sim.render(d, **hk, **light, **kw), want * ratio, rtol=0, atol=1e-9)


def test_hair_strands_cross_the_field(sim):
    # One straight strand crossing the whole square field covers between
    # width x side (axis-aligned) and width x side x sqrt(2) (diagonal), in mm^2.
    # 10 % slack each way for anti-aliasing at the strand's edges and ends.
    d, w = 3.0, 0.08
    n = sim.field_size(d, PX_REG)
    side = n / PX_REG
    for s in range(5):
        cov = sim.hair_coverage(d, px_per_mm=PX_REG, hair_count=1, hair_width_mm=w, hair_seed=s)
        area = cov.sum() / PX_REG ** 2
        assert 0.9 * w * side <= area <= 1.1 * w * side * math.sqrt(2), (s, area)


def test_more_hair_covers_more(sim):
    cov = [sim.hair_coverage(3.0, px_per_mm=PX_FAST, hair_count=k, hair_seed=2).sum()
           for k in (1, 2, 8)]
    assert cov[0] < cov[1] < cov[2]


def test_hair_seed_controls_hair_only(sim):
    kw = dict(px_per_mm=PX_FAST, seed=5, hair_count=3, **MOTTLE)
    a, b = sim.render(3.0, hair_seed=1, **kw), sim.render(3.0, hair_seed=2, **kw)
    assert not np.array_equal(a, b)
    ca = sim.hair_coverage(3.0, px_per_mm=PX_FAST, hair_count=3, hair_seed=1)
    cb = sim.hair_coverage(3.0, px_per_mm=PX_FAST, hair_count=3, hair_seed=2)
    untouched = (ca == 0) & (cb == 0)
    assert np.array_equal(a[untouched], b[untouched])


def test_detect_hair_on_a_clean_scene(sim):
    # Correctness on an easy scene, not the experiment: noise-free, no blur, 5 %
    # mottle, hair at HAIR_RGB (far darker than skin). Recall >= 0.9 of pixels at
    # least half covered (edge pixels may be missed); at most 2 % of hair-free
    # pixels flagged; the spot (lighter than skin) is never hair.
    d = 3.0
    hk = dict(hair_count=3, hair_width_mm=0.08, hair_seed=4)
    img = sim.render(d, px_per_mm=PX_REG, seed=7, **hk, **MOTTLE)
    cov = sim.hair_coverage(d, px_per_mm=PX_REG, **hk)
    got = np.asarray(sim.detect_hair(img, d, PX_REG), dtype=bool)
    assert got.shape == cov.shape
    core, free = cov >= 0.5, cov == 0
    assert got[core].mean() >= 0.9
    assert got[free].mean() <= 0.02
    clean = sim.render(d, px_per_mm=PX_REG, seed=7, **MOTTLE)
    x, y = grid_mm(cov.shape[0], PX_REG)
    in_spot = np.hypot(x, y) < d / 2 - 0.1
    assert not np.asarray(sim.detect_hair(clean, d, PX_REG), dtype=bool)[in_spot].any()


# ---- measurement with exclusion ---------------------------------------------

def test_measure_keys_and_no_exclusion_matches_none(sim):
    img = sim.render(3.0, px_per_mm=PX_FAST, seed=2, **MOTTLE)
    a = sim.measure(img, 3.0, PX_FAST)
    b = sim.measure(img, 3.0, PX_FAST, exclude=np.zeros(img.shape[:2], bool))
    need = {"L", "a", "b", "ring_L", "ring_a", "ring_b", "ring_excluded", "spot_excluded"}
    assert need <= set(a)
    for k in need:
        assert abs(a[k] - b[k]) < 1e-12, k
    assert a["ring_excluded"] == 0.0 and a["spot_excluded"] == 0.0


def test_excluding_true_hair_recovers_hair_free_contrast(sim):
    # Uniform skin and spot, noise-free, no blur: every pixel left after the
    # exclusion has exactly its hair-free colour. So the hairy capture measured
    # with the true hair mask equals the clean capture measured with the SAME
    # mask, exactly (1e-9), for both regions. (Fix 2026-11-28: the first version
    # compared against the clean capture with no mask. That is not exact for the
    # outline, whose anti-aliased edge pixels are part spot, part skin, so
    # dropping some of them legitimately moves the mean, by 0.00097 L* in the
    # builder's run. Comparing under the same mask keeps the claim exact.)
    # The ring holds pure skin only, so its absolute colour must also equal the
    # unmasked clean ring exactly. And the hair must matter without the mask,
    # so the test cannot pass on a scene where hair misses S and R.
    d = 4.0
    hk = dict(hair_count=3, hair_width_mm=0.08, hair_seed=6)
    hairy = sim.render(d, px_per_mm=PX_REG, **hk)
    clean = sim.render(d, px_per_mm=PX_REG)
    mask = sim.hair_coverage(d, px_per_mm=PX_REG, **hk) > 0
    hair_mattered = False
    for region in sim.REGIONS:
        m = sim.measure(hairy, d, PX_REG, region=region, exclude=mask)
        if m["spot_excluded"] == 1.0:
            continue
        same = sim.measure(clean, d, PX_REG, region=region, exclude=mask)
        bare = sim.measure(clean, d, PX_REG, region=region)
        for ch in ("L", "a", "b", "ring_L", "ring_a", "ring_b"):
            assert abs(m[ch] - same[ch]) < 1e-9, (region, ch)
        for ch in ("ring_L", "ring_a", "ring_b"):
            assert abs(m[ch] - bare[ch]) < 1e-9, (region, ch)
        assert m["ring_excluded"] == same["ring_excluded"]
        assert m["spot_excluded"] == same["spot_excluded"]
        assert 0.0 <= m["ring_excluded"] < 1.0
        unmasked = sim.measure(hairy, d, PX_REG, region=region)
        hair_mattered |= abs(unmasked["L"] - bare["L"]) > 1e-3
    assert hair_mattered, "hair crossed neither S nor R in this scene; choose another hair_seed"


def test_ring_excluded_fraction_is_reported(sim):
    d = 4.0
    img = sim.render(d, px_per_mm=PX_FAST)
    n = img.shape[0]
    x, _ = grid_mm(n, PX_FAST)
    assert sim.measure(img, d, PX_FAST, exclude=np.ones((n, n), bool))["ring_excluded"] == 1.0
    # Half-plane: about half the ring. 0.05 slack for pixels on the dividing line.
    half = sim.measure(img, d, PX_FAST, exclude=x > 0)["ring_excluded"]
    assert abs(half - 0.5) <= 0.05, half


def test_heavily_masked_capture_is_refused(sim):
    # Plan C10: a ring more than 20 % masked is refused, not measured.
    d = 4.0
    img = sim.render(d, px_per_mm=PX_FAST)
    n = img.shape[0]
    x, y = grid_mm(n, PX_FAST)
    half = x > 0
    thin = (np.abs(y) < 0.15) & (x > 0)        # one narrow strip: well under 20 % of the ring
    assert sim.measure(img, d, PX_FAST, exclude=thin)["ring_excluded"] < sim.MAX_RING_EXCLUDED
    sim.change_pct(img, img, d, PX_FAST, follow_exclude=thin)      # accepted
    with pytest.raises(sim.CaptureRefused):
        sim.change_pct(img, img, d, PX_FAST, follow_exclude=half)
    with pytest.raises(sim.CaptureRefused):
        sim.change_pct(img, img, d, PX_FAST, base_exclude=half)
    spot_only = np.hypot(x, y) < d / 2 + 0.05
    with pytest.raises(sim.CaptureRefused):                       # S entirely excluded
        sim.change_pct(img, img, d, PX_FAST, follow_exclude=spot_only)


def test_segmented_region_is_refused_for_colour(sim):
    img = sim.render(4.0, px_per_mm=PX_FAST)
    for bad in ("segmented", "traced", ""):
        with pytest.raises(ValueError):
            sim.measure(img, 4.0, PX_FAST, region=bad)


@pytest.mark.parametrize("region", ["outline", "inner_disc"])
def test_zero_contrast_baseline_is_refused(sim, region):
    flat = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    spot = sim.render(4.0, px_per_mm=PX_FAST)
    with pytest.raises(ZeroDivisionError):
        sim.change_pct(flat, spot, 4.0, PX_FAST, region=region)


# ---- disturbance 2: tanning --------------------------------------------------

def test_tanning_darkens_skin_by_the_stated_L(sim):
    # Uniform skin, noise-free, no blur, spot does not tan: absolute ring L*
    # moves by exactly tan_dL and the inner disc (wholly inside the spot, so
    # untouched by edge blending) keeps its absolute L*. 1e-6 for round-off in
    # solving for the gain.
    d = 4.0
    for dL in (-2.0, -5.0, 3.0):
        base = sim.measure(sim.render(d, px_per_mm=PX_FAST), d, PX_FAST, region="inner_disc")
        tan = sim.measure(sim.render(d, px_per_mm=PX_FAST, tan_dL=dL), d, PX_FAST, region="inner_disc")
        assert abs((tan["ring_L"] - base["ring_L"]) - dL) < 1e-6, dL
        spot_base = base["L"] + base["ring_L"]
        spot_tan = tan["L"] + tan["ring_L"]
        assert abs(spot_tan - spot_base) < 1e-6, dL


def test_even_tanning_is_one_gain_on_all_skin(sim):
    # Mottled skin, no texture change: outside the spot (beyond 0.1 mm of its
    # edge) every pixel and channel is multiplied by the same k < 1.
    d = 3.0
    kw = dict(px_per_mm=PX_FAST, seed=8, **MOTTLE)
    ratio = sim.render(d, tan_dL=-5.0, **kw) / sim.render(d, **kw)
    x, y = grid_mm(ratio.shape[0], PX_FAST)
    skin = np.hypot(x, y) > d / 2 + 0.1
    k = ratio[skin]
    assert k.max() - k.min() < 1e-9 and k.max() < 1.0


def test_spot_tan_fraction_one_tans_the_spot_too(sim):
    d = 4.0
    kw = dict(px_per_mm=PX_FAST, tan_dL=-5.0)
    ratio = sim.render(d, spot_tan_fraction=1.0, **kw) / sim.render(d, px_per_mm=PX_FAST)
    assert ratio.max() - ratio.min() < 1e-9


def test_patchy_tanning_changes_the_texture(sim):
    d = 3.0
    kw = dict(px_per_mm=PX_FAST, seed=8, tan_dL=-5.0, **MOTTLE)
    even = sim.render(d, **kw)
    a = sim.render(d, tan_texture_sd=0.03, tan_seed=1, **kw)
    b = sim.render(d, tan_texture_sd=0.03, tan_seed=2, **kw)
    assert not np.allclose(a, even) and not np.array_equal(a, b)
    x, y = grid_mm(a.shape[0], PX_FAST)
    skin = np.hypot(x, y) > d / 2 + 0.1
    rel = (a / even)[..., 1][skin]
    # The new texture has SD 0.03 by construction; a finite field of
    # correlated texture is allowed 0.015 to 0.045 (factor 2 either way).
    assert 0.015 <= rel.std() / rel.mean() <= 0.045, rel.std() / rel.mean()


# ---- disturbance 3: rotation -------------------------------------------------

def test_rotation_by_90_degrees_is_rot90(sim):
    # A quarter turn maps pixel centres onto pixel centres, so any correct
    # renderer reproduces numpy.rot90 up to round-off (1e-6).
    for kw in (dict(px_per_mm=PX_FAST, seed=12, **MOTTLE),
               dict(px_per_mm=PX_FAST, seed=12, diameter_scale=0.7, **MOTTLE)):
        base = sim.render(3.0, **kw)
        turned = sim.render(3.0, rotation_deg=90.0, **kw)
        assert np.allclose(turned, np.rot90(base, k=1, axes=(0, 1)), rtol=0, atol=1e-6)


def test_rotation_keeps_the_spot_centre_at_shift(sim):
    # Spot and ring are rotation-invariant discs, so on uniform skin measuring at
    # the true centre (= shift_mm) after any rotation gives the unrotated
    # contrast. Tolerance 0.5 % of the contrast: anti-aliased edge pixels may
    # be resampled differently once the grid is turned.
    d, sh = 3.0, (0.4, -0.2)
    ref = sim.measure(sim.render(d, px_per_mm=PX_REG, shift_mm=sh), d, PX_REG, centre_mm=sh)["L"]
    for ang in (2.0, 7.0, 33.0):
        got = sim.measure(sim.render(d, px_per_mm=PX_REG, shift_mm=sh, rotation_deg=ang),
                          d, PX_REG, centre_mm=sh)["L"]
        assert abs(got / ref - 1) <= 0.005, (ang, got, ref)


def test_rotation_moves_the_texture(sim):
    kw = dict(px_per_mm=PX_FAST, seed=12, **MOTTLE)
    assert not np.allclose(sim.render(3.0, rotation_deg=5.0, **kw), sim.render(3.0, **kw))


# ---- disturbance 4: uneven lighting -----------------------------------------

@pytest.mark.parametrize("g, phi, v", [(0.2, 0.0, 0.0), (0.05, 90.0, 0.0), (0.2, 30.0, 0.0),
                                        (0.0, 0.0, 0.2), (0.2, 135.0, 0.1)])
def test_lighting_field_is_the_stated_formula(sim, g, phi, v):
    # Multiplicative on every channel, camera frame. Exact to 1e-9 relative.
    d = 3.0
    kw = dict(px_per_mm=PX_FAST, seed=3, shift_mm=(0.3, 0.1), rotation_deg=4.0, **MOTTLE)
    flat = sim.render(d, **kw)
    lit = sim.render(d, gradient=g, gradient_dir_deg=phi, vignetting=v, **kw)
    n = flat.shape[0]
    x, y = grid_mm(n, PX_FAST)
    W = n / PX_FAST
    u = x * math.cos(math.radians(phi)) + y * math.sin(math.radians(phi))
    I = (1 + g * u / W) * (1 - v * (np.hypot(x, y) / (W / 2)) ** 2)
    assert np.allclose(lit, flat * I[..., None], rtol=1e-9, atol=0)


def test_opposite_gradients_give_the_same_centred_contrast(sim):
    # Uniform skin, spot at the frame centre: a gradient and its mirror image
    # (direction + 180 degrees) see the same pixels mirrored, so contrast is
    # identical (1e-9, summation order only).
    d = 3.0
    for phi in (0.0, 60.0):
        a = sim.measure(sim.render(d, px_per_mm=PX_FAST, gradient=0.2, gradient_dir_deg=phi), d, PX_FAST)
        b = sim.measure(sim.render(d, px_per_mm=PX_FAST, gradient=0.2, gradient_dir_deg=phi + 180), d, PX_FAST)
        assert abs(a["L"] - b["L"]) < 1e-9


# ---- geometry still matches the closed form ----------------------------------

def test_outline_matches_closed_form_circle_overlap(sim):
    # As round one: uniform skin, no disturbance, placement "none". Tolerance 1.0
    # point at 40 px/mm (round one's allowance for edge pixels).
    for d in (2.0, 8.0):
        base = sim.render(d, px_per_mm=PX_FINE)
        for s in (0.25, 0.5):
            follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=s)
            got = sim.change_pct(base, follow, d, PX_FINE, region="outline")
            want = 100 * (lens_fraction(d / 2, d / 2, s) - 1)
            assert abs(got - want) < 1.0, (d, s, got, want)


def test_error_grows_as_spot_shrinks(sim):
    errs = []
    for d in (2.0, 4.0, 8.0):
        base = sim.render(d, px_per_mm=PX_FINE)
        follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=0.25)
        errs.append(abs(sim.change_pct(base, follow, d, PX_FINE, region="outline")))
    assert errs[0] > errs[1] > errs[2], errs


# ---- registration: definitions, on noise-free scenes -------------------------

@pytest.mark.parametrize("model", ["translation", "rigid"])
def test_register_recovers_whole_pixel_shift(sim, model):
    # Tolerance half a pixel; a rigid model must also report no rotation within
    # 0.5 degree (0.5 degree moves a point 3 mm away by 0.026 mm, half a pixel).
    d, sh = 2.0, (3 / PX_REG, -2 / PX_REG)
    kw = dict(px_per_mm=PX_REG, seed=21, **MOTTLE)
    got = sim.register(sim.render(d, **kw), sim.render(d, shift_mm=sh, **kw), d, PX_REG, model=model)
    assert got is not None
    assert abs(got["dx"] - sh[0]) <= 0.5 / PX_REG and abs(got["dy"] - sh[1]) <= 0.5 / PX_REG, got
    assert abs(got["angle_deg"]) <= 0.5
    if model == "translation":
        assert got["angle_deg"] == 0.0


def test_rigid_register_recovers_a_rotation(sim):
    # What "rigid" means: on noise-free mottled skin turned 5 degrees and moved,
    # it finds the centre within one pixel and the angle within 0.5 degree.
    # This is the estimator's definition, not the plan's target.
    d, sh, ang = 2.0, (0.15, -0.1), 5.0
    kw = dict(px_per_mm=PX_REG, seed=25, **MOTTLE)
    got = sim.register(sim.render(d, **kw), sim.render(d, shift_mm=sh, rotation_deg=ang, **kw),
                       d, PX_REG, model="rigid")
    assert got is not None
    assert abs(got["dx"] - sh[0]) <= 1.0 / PX_REG and abs(got["dy"] - sh[1]) <= 1.0 / PX_REG, got
    assert abs(got["angle_deg"] - ang) <= 0.5, got


@pytest.mark.parametrize("model", ["translation", "rigid"])
def test_register_ignores_the_spot_and_gap(sim, model):
    d, sh = 3.0, (0.25, 0.15)
    kw = dict(px_per_mm=PX_REG, seed=23, **MOTTLE)
    base, follow = sim.render(d, **kw), sim.render(d, shift_mm=sh, rotation_deg=3.0, **kw)
    n = follow.shape[0]
    x, y = grid_mm(n, PX_REG)
    inside = np.hypot(x, y) < d / 2 + sim.RING_GAP_MM - 2 / PX_REG
    vandal = follow.copy()
    vandal[inside] = np.random.default_rng(5).uniform(0.0, 1.0, (int(inside.sum()), 3))
    a = sim.register(base, follow, d, PX_REG, model=model)
    b = sim.register(base, vandal, d, PX_REG, model=model)
    assert a is not None and b is not None
    assert (a["dx"], a["dy"], a["angle_deg"]) == (b["dx"], b["dy"], b["angle_deg"])


@pytest.mark.parametrize("model", ["translation", "rigid"])
def test_register_refuses_without_texture(sim, model):
    base = sim.render(2.0, px_per_mm=PX_REG)
    follow = sim.render(2.0, px_per_mm=PX_REG, shift_mm=0.25)
    assert sim.register(base, follow, 2.0, PX_REG, model=model) is None


def test_register_rejects_unknown_model(sim):
    img = sim.render(3.0, px_per_mm=PX_FAST, seed=1, **MOTTLE)
    for bad in ("affine", ""):
        with pytest.raises(ValueError):
            sim.register(img, img, 3.0, PX_FAST, model=bad)


def test_place_methods(sim):
    d = 2.0
    kw = dict(px_per_mm=PX_REG, seed=24, **MOTTLE)
    base, follow = sim.render(d, **kw), sim.render(d, shift_mm=(0.2, 0.0), **kw)
    assert tuple(sim.place("none", base, follow, d, PX_REG, true_shift_mm=(0.2, 0))) == (0.0, 0.0)
    assert tuple(sim.place("sticker", base, follow, d, PX_REG, true_shift_mm=(0.37, -0.12),
                           sticker_sd_mm=0.0)) == (0.37, -0.12)
    for m, model in (("ring_registration", "translation"), ("ring_registration_rigid", "rigid")):
        r = sim.register(base, follow, d, PX_REG, model=model)
        a = sim.place(m, base, follow, d, PX_REG, true_shift_mm=(0.0, 0.0))
        b = sim.place(m, base, follow, d, PX_REG, true_shift_mm=(9.0, -9.0))
        assert tuple(a) == tuple(b) == (r["dx"], r["dy"])
    for bad in ("segmentation", "rigid", ""):
        with pytest.raises(ValueError):
            sim.place(bad, base, follow, d, PX_REG)


# ---- the experiment ----------------------------------------------------------

SMALL_DIST = ("none", "hair_2", "tan_5", "rotation_5", "gradient_20")


@pytest.fixture(scope="module")
def small_run(sim):
    return sim.run(seed=3, trials=2, px_per_mm=PX_FAST, diameters=(2.0,), disturbances=SMALL_DIST)


def test_run_has_one_row_per_combination(sim, small_run):
    keys = [(r["scenario"], r["disturbance"], float(r["diameter_mm"]), r["placement"],
             r["region"], r["hair_mask"]) for r in small_run]
    assert len(keys) == len(set(keys))
    want = {(sc, ds, 2.0, p, rg, hm) for sc in sim.SCENARIOS for ds in SMALL_DIST
            for p in sim.PLACEMENTS for rg in sim.REGIONS for hm in sim.HAIR_MASKS}
    assert set(keys) == want


def test_run_rows_have_required_keys(sim, small_run):
    need = {"scenario", "disturbance", "family", "level", "diameter_mm", "shift_mm",
            "placement", "region", "hair_mask", "true_change_pct", "mean_change_pct",
            "sd_change_pct", "bias_pct_points", "sd_error_pct_points",
            "mean_abs_error_pct_points", "base_contrast_L", "mean_change_L", "true_ring_dL",
            "mean_ring_dL", "mean_centre_error_mm", "mean_ring_excluded", "trials",
            "rejected", "rejected_placement", "rejected_mask"}
    for r in small_run:
        assert need <= set(r), need - set(r)
        assert float(r["shift_mm"]) == sim.SHIFT_MM
        assert r["family"] == WANT_DISTURBANCES[r["disturbance"]]["family"]
        assert r["level"] == WANT_DISTURBANCES[r["disturbance"]]["level"]
        assert r["trials"] == 2
        assert r["rejected"] == r["rejected_placement"] + r["rejected_mask"]
        assert 0 <= r["rejected"] <= 2


def test_capture_nuisances_are_not_truth(small_run):
    # Hair, rotation and lighting are not changes in the skin: an unchanged spot
    # has a true change of 0 under them. 1e-6 allows only round-off from
    # evaluating the texture at shifted coordinates.
    for r in small_run:
        if r["scenario"] == "unchanged" and r["disturbance"] in TRUTH_FREE:
            assert abs(float(r["true_change_pct"])) < 1e-6, r
            assert abs(float(r["true_ring_dL"])) < 1e-6, r


def test_tanning_is_truth(small_run):
    # The spot keeps its colour while the skin darkens, so the spot-minus-skin
    # lightness contrast of an unchanged white spot really grows (plan 2.1 item
    # 9; alignment CSV line 50 saw +33.3 % for 5 units), and the ring darkens.
    for r in small_run:
        if r["scenario"] == "unchanged" and r["disturbance"] == "tan_5":
            assert float(r["true_change_pct"]) > 0.0, r
            assert float(r["true_ring_dL"]) < 0.0, r


def test_truth_is_shared_by_placements_and_masks(small_run):
    truth, base = {}, {}
    for r in small_run:
        k = (r["scenario"], r["disturbance"], float(r["diameter_mm"]), r["region"])
        truth.setdefault(k, set()).add(r["true_change_pct"])
        base.setdefault(k + (r["hair_mask"],), set()).add(r["base_contrast_L"])
    for k, v in list(truth.items()) + list(base.items()):
        assert len(v) == 1, (k, v)


def test_exact_placement_without_noise_has_zero_error(sim):
    # Sticker with SD 0 places exactly; without noise or hair the only
    # difference between capture and truth is the disturbance's nuisance part.
    # "none" and the tanning conditions have none, so their error is exactly 0
    # (1e-9). This pins that tanning enters the truth, not the error.
    rows = sim.run(seed=1, trials=2, px_per_mm=PX_FAST, diameters=(2.0,),
                   disturbances=("none", "tan_2", "tan_5", "tan_patchy_5"),
                   noise_sd=0.0, sticker_sd_mm=0.0)
    seen = 0
    for r in rows:
        if r["placement"] == "sticker" and r["hair_mask"] == "none":
            seen += 1
            assert r["rejected"] == 0, r
            assert abs(float(r["bias_pct_points"])) < 1e-9, r
            assert abs(float(r["mean_abs_error_pct_points"])) < 1e-9, r
            assert abs(float(r["mean_centre_error_mm"])) < 1e-9, r
            assert abs(float(r["mean_ring_dL"]) - float(r["true_ring_dL"])) < 1e-9, r
    assert seen == 2 * 4 * 2       # scenarios x disturbances x regions


def test_zero_shift_none_condition_has_zero_error(sim):
    rows = sim.run(seed=2, trials=2, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   disturbances=("none",), scenarios=("unchanged",), shift_mm=0.0,
                   noise_sd=0.0, sticker_sd_mm=0.0)
    for r in rows:
        if r["hair_mask"] != "none":
            continue                 # a detector may flag texture: not exact
        assert r["rejected"] == 0, r
        # Round one's precedent: exact (1e-9) for none, sticker and translation
        # registration. A rigid estimator may return a sub-pixel residue on a
        # noise-free scene; 0.1 point is a tenth of the target's SD limit.
        tol = 0.1 if r["placement"] == "ring_registration_rigid" else 1e-9
        assert abs(float(r["mean_abs_error_pct_points"])) < tol, r


def test_same_seed_reruns_are_identical(sim):
    kw = dict(seed=5, trials=2, px_per_mm=PX_FAST, diameters=(2.0,),
              disturbances=("hair_2", "combined"))
    assert sim.run(**kw) == sim.run(**kw)
    img_kw = dict(px_per_mm=PX_FAST, noise_sd=0.01, seed=5, hair_count=2, hair_seed=3,
                  tan_dL=-5.0, tan_texture_sd=0.03, tan_seed=4, rotation_deg=5.0,
                  gradient=0.2, gradient_dir_deg=40.0, **MOTTLE)
    assert np.array_equal(sim.render(3.0, **img_kw), sim.render(3.0, **img_kw))


def test_run_rejects_unknown_names(sim):
    base = dict(seed=1, trials=1, px_per_mm=PX_FAST, diameters=(2.0,))
    with pytest.raises((ValueError, KeyError)):
        sim.run(disturbances=("sunburn",), **base)
    with pytest.raises((ValueError, KeyError)):
        sim.run(disturbances=("none",), scenarios=("invisible",), **base)


# ---- target evaluation (logic only, on hand-made rows) -----------------------

def _rows(override=None, disturbances=tuple(WANT_DISTURBANCES)):
    """Rows for every disturbance x placement x region x mask that meet every
    criterion. override maps (scenario, disturbance, placement, region,
    hair_mask, field) -> value."""
    override = override or {}
    out = []
    for sc, true in (("unchanged", 0.0), ("genuine_fading", -50.0)):
        for ds in disturbances:
            w = WANT_DISTURBANCES[ds]
            for p in ("none", "ring_registration", "ring_registration_rigid", "sticker"):
                for rg in ("outline", "inner_disc"):
                    for hm in ("none", "detected"):
                        r = dict(scenario=sc, disturbance=ds, family=w["family"], level=w["level"],
                                 diameter_mm=2.0, shift_mm=0.5, placement=p, region=rg,
                                 hair_mask=hm, true_change_pct=true, mean_change_pct=true + 0.1,
                                 sd_change_pct=0.5, bias_pct_points=0.1, sd_error_pct_points=0.5,
                                 mean_abs_error_pct_points=0.4, trials=100, rejected=0,
                                 rejected_placement=0, rejected_mask=0)
                        for (o_sc, o_ds, o_p, o_rg, o_hm, field), v in override.items():
                            if (o_sc, o_ds, o_p, o_rg, o_hm) == (sc, ds, p, rg, hm):
                                r[field] = v
                        out.append(r)
    return out


KEY = ("rotation_5", "ring_registration", "inner_disc", "detected")


def test_evaluate_all_pass(sim):
    res = sim.evaluate_stress_target(_rows())
    assert len(res) == len(WANT_DISTURBANCES) * 4 * 2 * 2
    for k, e in res.items():
        assert e["bias_ok"] and e["sd_ok"] and e["sensitivity_ok"] and e["acceptance_ok"]
        assert e["passes"] is True, k


@pytest.mark.parametrize("field, scenario, value, key", [
    ("bias_pct_points", "unchanged", -2.5, "bias_ok"),
    ("sd_error_pct_points", "unchanged", 1.2, "sd_ok"),
    ("bias_pct_points", "genuine_fading", 2.5, "sensitivity_ok"),
    ("rejected", "unchanged", 11, "acceptance_ok"),
    ("rejected", "genuine_fading", 11, "acceptance_ok"),
    ("bias_pct_points", "unchanged", None, "bias_ok"),
    ("sd_error_pct_points", "unchanged", None, "sd_ok"),
])
def test_evaluate_each_criterion_can_fail(sim, field, scenario, value, key):
    o = {(scenario,) + KEY + (field,): value}
    res = sim.evaluate_stress_target(_rows(o))
    assert res[KEY][key] is False and res[KEY]["passes"] is False
    other = ("rotation_5", "ring_registration", "inner_disc", "none")
    assert res[other]["passes"] is True


def test_evaluate_uses_error_not_raw_change(sim):
    # Under tanning an unchanged spot truly changes (say +30 %). A method that
    # reports +30.5 has a 0.5-point error and must pass bias_ok; raw
    # |mean_change_pct| <= 2, round one's form, would wrongly fail it.
    k = ("tan_5", "sticker", "outline", "none")
    o = {("unchanged",) + k + ("true_change_pct",): 30.0,
         ("unchanged",) + k + ("mean_change_pct",): 30.5,
         ("unchanged",) + k + ("bias_pct_points",): 0.5}
    assert sim.evaluate_stress_target(_rows(o))[k]["passes"] is True


def test_evaluate_thresholds_are_inclusive(sim):
    o = {("unchanged",) + KEY + ("bias_pct_points",): -2.0,
         ("unchanged",) + KEY + ("sd_error_pct_points",): 1.0,
         ("genuine_fading",) + KEY + ("bias_pct_points",): 2.0,
         ("unchanged",) + KEY + ("rejected",): 10}
    assert sim.evaluate_stress_target(_rows(o))[KEY]["passes"] is True


def test_evaluate_missing_row_is_an_error(sim):
    rows = [r for r in _rows() if not (r["scenario"] == "genuine_fading"
                                       and r["disturbance"] == "hair_8"
                                       and r["placement"] == "sticker")]
    with pytest.raises(ValueError):
        sim.evaluate_stress_target(rows)


def test_evaluate_reads_only_the_requested_diameter(sim):
    extra = [dict(r, diameter_mm=8.0, bias_pct_points=50.0) for r in _rows()]
    res = sim.evaluate_stress_target(_rows() + extra)
    assert all(e["passes"] for e in res.values())
    assert not any(e["passes"] for e in sim.evaluate_stress_target(_rows() + extra, diameter_mm=8.0).values())


def test_breaking_levels(sim):
    fail = lambda ds, f="bias_pct_points": {("unchanged", ds) + KEY[1:] + (f,): 9.0}
    def bl(o):
        return sim.breaking_levels(sim.evaluate_stress_target(_rows(o)))
    k_rot = ("rotation",) + KEY[1:]
    k_hair = ("hair",) + KEY[1:]
    assert bl({})[k_rot] is None and bl({})[k_hair] is None
    assert bl(fail("rotation_10"))[k_rot] == 10
    assert bl(fail("rotation_5"))[k_rot] == 5
    # The lowest failing level, even if a higher level happens to pass.
    assert bl({**fail("rotation_2"), **fail("rotation_5")})[k_rot] == 2
    assert bl(fail("hair_8"))[k_hair] == 8
    assert bl(fail("combined"))[("combined",) + KEY[1:]] == 1
    assert bl(fail("none"))[("none",) + KEY[1:]] == 0
    fams = {k[0] for k in bl({})}
    assert fams == {w["family"] for w in WANT_DISTURBANCES.values()}
