"""Tests for the edge-width measurement on simulated photographs, written before
the code exists.

SIMULATION ONLY, CERTAINTY LEVEL 0. Synthetic disks, synthetic skin texture,
synthetic straight "hairs". No patient images. Every result this simulation
produces is a hypothesis about the measuring method under the simulation's own
assumptions, not evidence about real skin, real cameras or any treatment.

Run:  python3 -m pytest experiments/tests/test_edge_width_sim.py -q

Until experiments/edge_width_sim.py exists, every test here is SKIPPED (see
`pytestmark`), so the existing suite stays green. As soon as the builder adds
that file the tests run unchanged; the builder may not edit this file:
`git diff --exit-code <tests commit> -- experiments/tests` must stay clean.

WHY
  The grid spot model (PR 46, content/experiments.md section 6 on that branch)
  finds that, in the model, the edge of an untreated spot separates its two
  explanations: H1 edges sit at the blur floor (0.27 / 0.28 / 0.31 mm, 10th /
  50th / 90th percentile), H2 edges are wider (0.36 / 0.50 / 0.89 mm). It
  calls its 0.1 mm edge-width threshold provisional "until the phantom tests
  give a smallest detectable change". Before phantoms, this simulation asks
  the cheaper question: with the photo simulation's existing disturbances
  (experiments/registration_stress_sim.py, PR 43), what is the smallest
  difference in edge width the measurement can resolve on a 2 mm spot?

SOURCES OF THE SPECIFICATION
  * Edge width, as defined in PR 46's spot-model-plan.md section 5.1 ("the
    distance over which a radial dL* profile goes from 10% to 90% of the
    spot's contrast") and in the grid-model test contract
    (experiments/tests/test_spot_model_grid.py, `edge_width`): L* per pixel;
    ring as drift_sim / placement_sim; L_centre = mean L* over r <= d / 4;
    one-pixel radial bins; q = (P - L_ring) / C; r_t = first bin centre going
    outward at which q < t, linearly interpolated with the previous bin
    centre; width = r_0.1 - r_0.9. This file keeps that rule and adds three
    things a real photograph needs: a centre other than the frame centre, an
    exclusion mask (hair), and a search start (see READING 1).
  * Disturbances, scene, hair finder and refusal rules: registration_stress_sim
    as built in PR 43, unchanged and reused, not reimplemented.
  * Smallest detectable change: content/measurement-tool-plan.md 2.2,
    SDC = 1.96 x sqrt(2) x SEM, applied to edge width.
  * Camera: plan C1, at least 20 px/mm and 0.1 mm blur, the defaults of
    registration_stress_sim.run (asserted below, not restated).

READINGS (choices the sources leave open; Ben can change any of them)
  1. Search start. The crossing search starts at the first bin whose centre is
     >= d / 4 (the edge of the centre disc), not at r = 0. The few-pixel bins
     near the centre are noisy and would otherwise give a false 0.9 crossing.
     On a noise-free scene whose q stays >= 0.9 inside d / 4 this is the grid
     model's rule exactly.
  2. Truth. The spot's own edge is the measurand. TRUTH for a trial is the
     edge width measured, at the true centre with no exclusion, on a
     noise-free render on UNIFORM skin with the same diameter, intrinsic edge,
     blur, shift and even tanning. So skin mottle, patchy tanning, hair,
     rotation, uneven light, noise and centring error all count as error.
     (Unlike registration_stress_sim, where mottle is the texture
     registration needs and is kept in the truth.)
  3. Intrinsic edge. A spot's own soft edge is modelled as the hard disc's
     coverage convolved with a Gaussian of SD edge_sd_mm before the scene is
     built, so the seen edge is that Gaussian and the camera blur in series.
     EDGE_SD_MM = (0.0, 0.1, 0.2): with 0.1 mm blur the closed-form widths
     are 0.256, 0.362 and 0.573 mm, bracketing the grid model's H1 floor, the
     H2 10th percentile and about its median. ASSUMPTION; not from a quoted
     source. A Gaussian (erf) edge is not the grid model's H2 profile shape.
  4. Centring. CENTRINGS = ("true", "found", "frame"). "true" uses the known
     spot centre: an oracle, a reference only, not a method Ben can use.
     "found" uses find_spot_centre() on the capture itself (edge width is a
     shape measurement inside one photo, so no between-visit registration is
     needed). "frame" measures about the frame centre (no centring).
  5. Bias limit. BIAS_LIMIT_MM = 0.05, one profile bin at 20 px/mm and half
     of the provisional threshold: the H1 and H2 values in PR 46 are
     absolute, so a measurement that reads every edge 0.1 mm wide cannot be
     compared with them even if its spread is small.
  6. The SDC is computed from single captures (ddof = 1 SD of measured minus
     truth over trials), as the plan computes SDC from SEM between sessions;
     plan 2.2's k = 3 captures per session would shrink it by up to sqrt(3)
     and is left to the write-up.

Conventions as registration_stress_sim (linear RGB in, CIELAB D65 per pixel;
x = column, y = row increasing down; frame centre (0, 0) mm at pixel
((n - 1) / 2, (n - 1) / 2)).

Constants (module edge_width_sim)
  CERTAINTY_LEVEL = 0
  EDGE_SD_MM = (0.0, 0.1, 0.2)                   READING 3
  CENTRINGS = ("true", "found", "frame")         READING 4
  HAIR_MASKS = registration_stress_sim.HAIR_MASKS ("none", "detected")
  EDGE_THRESHOLD_MM = 0.1                        PR 46's provisional threshold
  BIAS_LIMIT_MM = 0.05                           READING 5
  SDC_FACTOR = 1.96 * sqrt(2)                    plan 2.2

Scene
  render(diameter_mm, *, edge_sd_mm=0.0, **kw) -> float (n, n, 3) linear RGB.
      kw: every keyword of registration_stress_sim.render, same meaning and
      defaults. edge_sd_mm = 0 returns registration_stress_sim.render(d, **kw)
      exactly. edge_sd_mm > 0 softens the spot's coverage per READING 3, then
      builds the scene from it exactly as registration_stress_sim does.
      ValueError for edge_sd_mm < 0 and for diameter_mm <= 0.

Measurement
  measure_edge(img, diameter_mm, px_per_mm, *, centre_mm=(0, 0), exclude=None)
      -> {"width_mm", "midpoint_mm", "contrast_L", "L_ring", "ring_excluded",
          "r_mm", "q"}.
      The rule above, about centre_mm. exclude: bool (n, n) or None; True
      pixels are left out of the ring, the centre disc and every bin; a bin
      with no pixel left is dropped from the profile. r_mm, q: the bin centres
      kept and their q, out to the ring's outer edge.
      midpoint_mm = r_0.5 by the same rule.
      Raises registration_stress_sim.CaptureRefused when ring_excluded >
      MAX_RING_EXCLUDED or the centre disc is wholly excluded;
      ZeroDivisionError when |C| < 1e-6 (refused, never divided by);
      ValueError when q never falls below 0.1 inside the profile (a guard;
      with the ring's own bins in the profile it should not arise, so it is
      not tested).
  edge_width(img, diameter_mm, px_per_mm, **same) -> measure_edge(...)["width_mm"].
  find_spot_centre(img, diameter_mm, px_per_mm, *, exclude=None)
      -> (x_mm, y_mm) or None when the image shows no spot. From the image
      alone; method is the builder's choice, stated in the module.

Experiment
  run(*, seed, trials, px_per_mm=20, diameters=rs.DIAMETERS_MM,
      disturbances=tuple(rs.DISTURBANCES), edge_sds=EDGE_SD_MM,
      shift_mm=rs.SHIFT_MM, noise_sd=<rs.run default>,
      mottle_sd=<rs.run default>, blur_sd_mm=<rs.run default>) -> list of rows.
      One row per disturbance x diameter x edge_sd x centring x hair_mask.
      Within one disturbance x diameter x edge_sd, every centring and hair
      mask is measured on the SAME captures (paired). Each trial: one capture,
      mottled skin (new texture per trial), spot at (shift_mm, 0), the
      disturbance's render keywords; if it has a gradient, gradient_dir_deg
      is drawn uniformly in [0, 360) per trial; hair_seed and noise per trial.
      Hair mask "detected" passes rs.detect_hair(capture) as exclude, also to
      find_spot_centre; "none" passes None.
      A group's captures depend only on seed, its disturbance, diameter,
      edge_sd and trial index, never on which other groups are run.
      TRUTH per READING 2. A trial is rejected when find_spot_centre returns
      None (rejected_centre) or measure_edge raises CaptureRefused,
      ZeroDivisionError or ValueError (rejected_measure); counted once,
      centre checked first.
      Row keys include: certainty_level (0), disturbance, family, level,
      diameter_mm, edge_sd_mm, blur_sd_mm, px_per_mm, centring, hair_mask,
      closed_form_width_mm (2 x 1.281552 x sqrt(edge_sd^2 + blur^2)),
      true_width_mm (mean of per-trial truths), mean_width_mm, bias_mm (mean
      over accepted trials of measured - truth), sd_error_mm (ddof = 1),
      sdc_mm (SDC_FACTOR x sd_error_mm), mean_abs_error_mm,
      mean_centre_error_mm (distance of the centre used from the true one),
      trials, rejected, rejected_centre, rejected_measure. Means None when no
      trial is accepted; SD fields None when fewer than 2.
  resolution_summary(rows, *, diameter_mm=2.0, threshold_mm=EDGE_THRESHOLD_MM)
      -> {(disturbance, edge_sd_mm, centring, hair_mask):
          {"sdc_mm", "bias_mm", "sdc_ok", "bias_ok", "acceptance_ok", "resolves"}}
      sdc_ok: sdc_mm <= threshold_mm. bias_ok: |bias_mm| <= BIAS_LIMIT_MM.
      acceptance_ok: rejected <= rs.MAX_REJECTED_FRACTION x trials.
      resolves: all three. A None value fails its key. Thresholds inclusive.
      No row at diameter_mm raises ValueError.
  Command line: python3 experiments/edge_width_sim.py --out DIR [--trials N]
      [--seed S] [--diameters 2.0,4.0] [--disturbances none,hair_2]
      writes DIR/edge_width_results.csv (run rows) and
      DIR/edge_width_resolution.csv (one row per resolution_summary key, with
      the key's fields as columns), both with a certainty_level column of 0.

This file asserts what the simulation must compute. It does NOT assert how
small an edge-width difference any disturbance allows, or whether any
centring resolves the 0.1 mm threshold: that is the result, reported, not
presumed. Accuracy checks on the measurement are on noise-free scenes only.
Tolerances were sized with a throwaway check of the rule on
registration_stress_sim renders while this file was written (not committed):
noise-free widths came within 0.02 mm of the closed form at 20 and 40 px/mm.
"""
import csv
import hashlib
import inspect
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1]
ROOT = EXPERIMENTS.parent
sys.path.insert(0, str(EXPERIMENTS))

pytestmark = pytest.mark.skipif(
    not (EXPERIMENTS / "edge_width_sim.py").exists(),
    reason="experiments/edge_width_sim.py not built yet; these tests are its contract",
)

PX = 20                 # plan C1 minimum, the run default
PX_FINE = 40
BLUR = 0.1              # plan C1
Z90 = 1.281552          # standard normal 90th percentile
MOTTLE = dict(background="mottled", mottle_sd=0.05)


@pytest.fixture(scope="module")
def sim():
    import edge_width_sim
    return edge_width_sim


@pytest.fixture(scope="module")
def rs():
    import registration_stress_sim
    return registration_stress_sim


def closed_form(edge_sd, blur):
    return 2 * Z90 * math.hypot(edge_sd, blur)


def grid_mm(n, px):
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    return (xx - c) / px, (yy - c) / px


def L_of(rs, img):
    return rs.rgb_to_lab(img)[..., 0]


def synthetic_L_image(rs, L_map):
    """Linear RGB whose L* per pixel is L_map, as a grey scale factor of
    SKIN_RGB found by bisection (L* depends on Y only, Y scales with the
    factor). The same helper the grid-model tests use."""
    skin = np.asarray(rs.SKIN_RGB, dtype=float)
    lo = np.zeros_like(L_map)
    hi = np.full_like(L_map, 3.0)
    for _ in range(80):
        mid = (lo + hi) / 2
        L = rs.rgb_to_lab(mid[..., None] * skin)[..., 0]
        lo = np.where(L < L_map, mid, lo)
        hi = np.where(L < L_map, hi, mid)
    return ((lo + hi) / 2)[..., None] * skin


def linear_ramp_image(rs, d, a, b, px=PX, L_skin=None, contrast=12.0, centre=(0.0, 0.0)):
    """Radial L* profile: L_skin + contrast for r <= a, falling linearly to
    L_skin at r = b, L_skin beyond. q is exactly linear on [a, b], so
    r_0.9 = a + 0.1 (b - a), r_0.1 = a + 0.9 (b - a), width 0.8 (b - a)."""
    n = rs.field_size(d, px)
    if L_skin is None:
        L_skin = float(L_of(rs, np.asarray(rs.SKIN_RGB, float)[None, None, :])[0, 0])
    x, y = grid_mm(n, px)
    r = np.hypot(x - centre[0], y - centre[1])
    q = np.clip((b - r) / (b - a), 0.0, 1.0)
    return synthetic_L_image(rs, L_skin + contrast * q), r


# ---- constants -----------------------------------------------------------------

def test_constants(sim, rs):
    assert sim.CERTAINTY_LEVEL == 0
    assert tuple(sim.EDGE_SD_MM) == (0.0, 0.1, 0.2)
    assert tuple(sim.CENTRINGS) == ("true", "found", "frame")
    assert tuple(sim.HAIR_MASKS) == tuple(rs.HAIR_MASKS) == ("none", "detected")
    assert sim.EDGE_THRESHOLD_MM == 0.1
    assert sim.BIAS_LIMIT_MM == 0.05
    assert sim.SDC_FACTOR == pytest.approx(1.96 * math.sqrt(2), abs=1e-12)


def test_run_defaults_are_the_photo_simulations(sim, rs):
    """The camera and skin settings are not restated here: the run uses the
    photo simulation's own defaults (plan C1: 20 px/mm, 0.1 mm blur)."""
    want = inspect.signature(rs.run).parameters
    got = inspect.signature(sim.run).parameters
    for k in ("px_per_mm", "noise_sd", "mottle_sd", "blur_sd_mm", "shift_mm"):
        assert got[k].default == want[k].default, k
    assert tuple(got["diameters"].default) == tuple(rs.DIAMETERS_MM)
    assert tuple(got["disturbances"].default) == tuple(rs.DISTURBANCES)
    assert tuple(got["edge_sds"].default) == tuple(sim.EDGE_SD_MM)
    assert want["blur_sd_mm"].default == BLUR and want["px_per_mm"].default == PX


# ---- scene -----------------------------------------------------------------------

@pytest.mark.parametrize("kw", [
    dict(px_per_mm=PX),
    dict(px_per_mm=PX, seed=3, blur_sd_mm=0.1, noise_sd=0.01, **MOTTLE),
    dict(px_per_mm=PX, seed=4, shift_mm=(0.5, 0.0), hair_count=2, hair_seed=5,
         tan_dL=-5.0, tan_texture_sd=0.03, rotation_deg=5.0, gradient=0.2,
         gradient_dir_deg=40.0, vignetting=0.1, blur_sd_mm=0.1, **MOTTLE),
])
def test_zero_intrinsic_edge_is_the_photo_simulation(sim, rs, kw):
    for d in (2.0, 4.0):
        a = sim.render(d, edge_sd_mm=0.0, **kw)
        b = rs.render(d, **kw)
        assert a.shape == b.shape and np.array_equal(a, b)
    assert np.array_equal(sim.render(2.0, **kw), rs.render(2.0, **kw))


@pytest.mark.parametrize("d, s, b, px", [
    (2.0, 0.05, 0.1, PX), (2.0, 0.2, 0.1, PX), (4.0, 0.2, 0.1, PX), (2.0, 0.1, 0.1, PX_FINE),
])
def test_intrinsic_edge_and_blur_act_in_series(sim, rs, d, s, b, px):
    """READING 3 on uniform skin: softening the coverage by s and blurring by b
    is the same as blurring the hard disc by sqrt(s^2 + b^2). A check while this
    test was written put discrete-kernel differences under 0.001 L*; 0.05 L*
    leaves room for any sound kernel and rejects an analytic erf ring, whose
    curvature error is about s^2 / (2 r) of position (several tenths of L*)."""
    soft = sim.render(d, px_per_mm=px, edge_sd_mm=s, blur_sd_mm=b)
    ref = rs.render(d, px_per_mm=px, blur_sd_mm=math.hypot(s, b))
    assert soft.shape == ref.shape
    assert np.max(np.abs(L_of(rs, soft) - L_of(rs, ref))) <= 0.05


def test_intrinsic_edge_softens_the_spot_not_the_skin(sim, rs):
    """Far from the spot (beyond 7 SD of the edge, where a Gaussian tail is
    about 1e-12) the mottled skin is unchanged
    by edge_sd_mm; inside the soft edge it is not. Noise-free, no blur, so the
    comparison is exact up to round-off."""
    d, s = 2.0, 0.2
    kw = dict(px_per_mm=PX, seed=8, **MOTTLE)
    hard, soft = rs.render(d, **kw), sim.render(d, edge_sd_mm=s, **kw)
    x, y = grid_mm(hard.shape[0], PX)
    r = np.hypot(x, y)
    far = r > d / 2 + 7 * s
    assert np.allclose(hard[far], soft[far], rtol=0, atol=1e-9)
    near = np.abs(r - d / 2) < s
    assert np.max(np.abs(hard[near] - soft[near])) > 1e-3


def test_render_refuses_bad_inputs(sim):
    with pytest.raises(ValueError):
        sim.render(2.0, edge_sd_mm=-0.1)
    for bad in (0.0, -2.0):
        with pytest.raises(ValueError):
            sim.render(bad)


# ---- measurement on noise-free scenes ------------------------------------------

@pytest.mark.parametrize("d", [2.0, 4.0])
@pytest.mark.parametrize("s, b, px", [
    (0.0, 0.1, PX), (0.1, 0.1, PX), (0.2, 0.1, PX), (0.0, 0.2, PX),
    (0.0, 0.1, PX_FINE), (0.2, 0.1, PX_FINE),
])
def test_edge_width_matches_the_closed_form(sim, d, s, b, px):
    """A disc blurred by a Gaussian of total SD t has a 10-90 % width of
    2 x 1.2816 x t. The anti-aliasing ramp and L*'s non-linearity moved the
    width by under 0.02 mm in the check run. Tolerance 0.05 mm, one bin at
    20 px/mm, as the grid-model contract. Midpoint on the drawn edge within the
    same 0.05 mm."""
    img = sim.render(d, px_per_mm=px, edge_sd_mm=s, blur_sd_mm=b)
    m = sim.measure_edge(img, d, px)
    assert m["width_mm"] == pytest.approx(closed_form(s, b), abs=0.05)
    assert m["midpoint_mm"] == pytest.approx(d / 2, abs=0.05)
    assert sim.edge_width(img, d, px) == m["width_mm"]


def test_edge_width_grows_with_the_intrinsic_edge(sim):
    w = [sim.edge_width(sim.render(2.0, edge_sd_mm=s, blur_sd_mm=BLUR), 2.0, PX)
         for s in (0.0, 0.05, 0.1, 0.2)]
    assert w[0] < w[1] < w[2] < w[3]


def test_measure_edge_keys_and_contrast(sim, rs):
    img = sim.render(2.0, blur_sd_mm=BLUR)
    m = sim.measure_edge(img, 2.0, PX)
    assert {"width_mm", "midpoint_mm", "contrast_L", "L_ring", "ring_excluded", "r_mm", "q"} <= set(m)
    L = L_of(rs, img)
    skin_L = float(L_of(rs, np.asarray(rs.SKIN_RGB, float)[None, None, :])[0, 0])
    assert m["L_ring"] == pytest.approx(skin_L, abs=1e-6)       # ring is 1 mm clear of the edge
    assert m["contrast_L"] == pytest.approx(L.max() - skin_L, abs=0.05)
    assert m["contrast_L"] > 0 and m["ring_excluded"] == 0.0
    r, q = np.asarray(m["r_mm"]), np.asarray(m["q"])
    assert r.shape == q.shape and np.all(np.diff(r) > 0)
    assert r[-1] <= 2.0 / 2 + rs.RING_GAP_MM + rs.RING_WIDTH_MM + 1e-9


def test_bins_are_one_pixel_wide(sim):
    for px in (PX, PX_FINE):
        m = sim.measure_edge(sim.render(2.0, px_per_mm=px, blur_sd_mm=BLUR), 2.0, px)
        r = np.asarray(m["r_mm"])
        assert np.allclose(np.diff(r), 1.0 / px, rtol=0, atol=1e-9)
        assert r[0] == pytest.approx(0.5 / px, abs=1e-9)


@pytest.mark.parametrize("a, b", [(0.7, 1.3), (0.8, 1.2), (0.5, 1.4)])
def test_rule_on_a_known_linear_profile(sim, rs, a, b):
    """q linear from 1 at r = a to 0 at r = b: width 0.8 (b - a), midpoint
    (a + b) / 2. The ends are chosen so both crossings and their neighbouring
    bin centres lie inside the ramp, where interpolating between bin means of a
    linear profile is exact up to the bins' pixel layout; 0.01 mm."""
    img, _ = linear_ramp_image(rs, 2.0, a, b)
    m = sim.measure_edge(img, 2.0, PX)
    assert m["width_mm"] == pytest.approx(0.8 * (b - a), abs=0.01)
    assert m["midpoint_mm"] == pytest.approx((a + b) / 2, abs=0.01)


def test_search_starts_at_the_centre_disc_edge(sim, rs):
    """READING 1. A dark speck at the centre (one bin, q = 0) must not be read
    as the 0.9 crossing. The speck lowers L_centre by about 1 % (its area over
    the centre disc's), so the width may move by about 1 % of the ramp; 0.02 mm.
    A search from r = 0 would put r_0.9 at the speck and the width near 1 mm."""
    d, a, b = 2.0, 0.7, 1.3
    clean, r = linear_ramp_image(rs, d, a, b)
    L = L_of(rs, clean)
    skin = L[r > 2.0].mean()
    L_speck = np.where(r < 0.05, skin, L)
    speck = synthetic_L_image(rs, L_speck)
    w_clean = sim.edge_width(clean, d, PX)
    w_speck = sim.edge_width(speck, d, PX)
    assert w_speck == pytest.approx(w_clean, abs=0.02)


def test_profile_is_about_the_given_centre(sim):
    """Spot moved to (0.5, -0.3): measured about its true centre the width is
    the centred spot's (0.02 mm: the pixel grid samples the disc differently);
    about the frame centre the edge is smeared and reads wider."""
    c = (0.5, -0.3)
    centred = sim.edge_width(sim.render(2.0, blur_sd_mm=BLUR), 2.0, PX)
    moved = sim.render(2.0, blur_sd_mm=BLUR, shift_mm=c)
    at_true = sim.edge_width(moved, 2.0, PX, centre_mm=c)
    assert at_true == pytest.approx(centred, abs=0.02)
    assert sim.edge_width(moved, 2.0, PX, centre_mm=(0.0, 0.0)) > at_true + 0.1


def test_rotation_about_the_frame_leaves_the_edge(sim):
    """The spot centre stays at shift_mm whatever the rotation (photo
    simulation's geometry), and a disc's radial profile has no direction:
    uniform skin, noise-free, 10 degrees. 0.01 mm allows interpolation."""
    kw = dict(edge_sd_mm=0.1, blur_sd_mm=BLUR, shift_mm=(0.5, 0.0))
    w0 = sim.edge_width(sim.render(2.0, **kw), 2.0, PX, centre_mm=(0.5, 0.0))
    w10 = sim.edge_width(sim.render(2.0, rotation_deg=10.0, **kw), 2.0, PX, centre_mm=(0.5, 0.0))
    assert w10 == pytest.approx(w0, abs=0.01)


def test_even_tanning_leaves_the_edge(sim):
    """Even tanning of the skin (spot untanned, SPOT_TAN_FRACTION = 0) raises
    the contrast but moves the coverage nowhere; L*'s non-linearity moved the
    width by under 0.001 mm in the check run. 0.01 mm."""
    kw = dict(edge_sd_mm=0.1, blur_sd_mm=BLUR)
    w0 = sim.edge_width(sim.render(2.0, **kw), 2.0, PX)
    w5 = sim.edge_width(sim.render(2.0, tan_dL=-5.0, **kw), 2.0, PX)
    assert w5 == pytest.approx(w0, abs=0.01)


# ---- exclusion and refusals -------------------------------------------------------

def test_no_exclusion_equals_an_empty_mask(sim):
    img = sim.render(2.0, blur_sd_mm=BLUR, seed=2, **MOTTLE)
    a = sim.measure_edge(img, 2.0, PX)
    b = sim.measure_edge(img, 2.0, PX, exclude=np.zeros(img.shape[:2], bool))
    for k in ("width_mm", "midpoint_mm", "contrast_L", "L_ring", "ring_excluded"):
        assert a[k] == pytest.approx(b[k], abs=1e-12), k


def test_excluding_a_wedge_of_a_symmetric_spot_changes_nothing(sim, rs):
    """Uniform skin, centred disc: every direction has the same profile, so
    leaving out a 30-degree wedge (about 8 % of the ring, under the 20 % limit)
    moves the width only by the bins' changed pixel sets; 0.01 mm."""
    img = sim.render(2.0, edge_sd_mm=0.1, blur_sd_mm=BLUR)
    x, y = grid_mm(img.shape[0], PX)
    ang = np.degrees(np.arctan2(y, x))
    wedge = (ang > 10) & (ang < 40)
    m0 = sim.measure_edge(img, 2.0, PX)
    m1 = sim.measure_edge(img, 2.0, PX, exclude=wedge)
    assert m1["width_mm"] == pytest.approx(m0["width_mm"], abs=0.01)
    assert 0.05 < m1["ring_excluded"] < 0.12


def test_masking_true_hair_recovers_the_hair_free_edge(sim, rs):
    """With the hairs' own coverage as the mask (not the builder's detector),
    a uniform-skin spot under two hairs reads as without them, within 0.02 mm
    (edge pixels of a strand are partly covered; any c > 0 is masked)."""
    hk = dict(hair_count=2, hair_seed=3)
    kw = dict(edge_sd_mm=0.1, blur_sd_mm=0.0)
    clean = sim.edge_width(sim.render(2.0, **kw), 2.0, PX)
    cov = rs.hair_coverage(2.0, px_per_mm=PX, **hk)
    img = sim.render(2.0, **hk, **kw)
    try:
        got = sim.edge_width(img, 2.0, PX, exclude=cov > 0)
    except rs.CaptureRefused:
        pytest.skip("this hair draw covers more than 20 % of the ring")
    assert got == pytest.approx(clean, abs=0.02)


def test_ring_mostly_masked_is_refused(sim, rs):
    img = sim.render(2.0, blur_sd_mm=BLUR)
    x, y = grid_mm(img.shape[0], PX)
    left = x < -0.5           # more than a fifth of the ring
    with pytest.raises(rs.CaptureRefused):
        sim.measure_edge(img, 2.0, PX, exclude=left)


def test_centre_wholly_masked_is_refused(sim, rs):
    img = sim.render(2.0, blur_sd_mm=BLUR)
    x, y = grid_mm(img.shape[0], PX)
    with pytest.raises(rs.CaptureRefused):
        sim.measure_edge(img, 2.0, PX, exclude=np.hypot(x, y) <= 2.0 / 4 + 0.05)


def test_zero_contrast_is_refused_not_divided_by(sim):
    img = sim.render(2.0, contrast_scale=0.0, blur_sd_mm=BLUR)
    with pytest.raises(ZeroDivisionError):
        sim.measure_edge(img, 2.0, PX)


def test_bad_diameter_is_refused(sim):
    img = sim.render(2.0)
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError):
            sim.measure_edge(img, bad, PX)


# ---- finding the spot centre -------------------------------------------------------

@pytest.mark.parametrize("c", [(0.0, 0.0), (0.5, 0.0), (0.3, -0.2), (-0.4, 0.35)])
@pytest.mark.parametrize("bg", ["uniform", "mottled"])
def test_find_spot_centre_on_clean_scenes(sim, c, bg):
    """Noise-free, 0.1 mm blur, 5 % mottle or none: within one pixel
    (0.05 mm at 20 px/mm). Correctness on easy scenes, not the experiment."""
    kw = dict(blur_sd_mm=BLUR, shift_mm=c, seed=5)
    if bg == "mottled":
        kw.update(MOTTLE)
    for d in (2.0, 4.0):
        got = sim.find_spot_centre(sim.render(d, edge_sd_mm=0.1, **kw), d, PX)
        assert got is not None
        assert math.hypot(got[0] - c[0], got[1] - c[1]) <= 0.05, (d, got)


def test_find_spot_centre_returns_none_without_a_spot(sim):
    assert sim.find_spot_centre(sim.render(2.0, contrast_scale=0.0), 2.0, PX) is None


def test_find_spot_centre_accepts_a_mask(sim, rs):
    hk = dict(hair_count=2, hair_seed=3)
    img = sim.render(2.0, blur_sd_mm=0.0, shift_mm=(0.5, 0.0), **hk)
    got = sim.find_spot_centre(img, 2.0, PX, exclude=rs.hair_coverage(2.0, px_per_mm=PX, **hk) > 0)
    assert got is not None and math.hypot(got[0] - 0.5, got[1]) <= 0.05


# ---- the experiment ----------------------------------------------------------------

FAST = dict(trials=4, diameters=(2.0,), edge_sds=(0.0, 0.2))


@pytest.fixture(scope="module")
def small_run(sim):
    return sim.run(seed=11, disturbances=("none", "hair_2", "gradient_20", "tan_5"), **FAST)


ROW_KEYS = {
    "certainty_level", "disturbance", "family", "level", "diameter_mm", "edge_sd_mm",
    "blur_sd_mm", "px_per_mm", "centring", "hair_mask", "closed_form_width_mm",
    "true_width_mm", "mean_width_mm", "bias_mm", "sd_error_mm", "sdc_mm",
    "mean_abs_error_mm", "mean_centre_error_mm", "trials", "rejected",
    "rejected_centre", "rejected_measure",
}


def test_run_has_one_row_per_cell(sim, small_run):
    assert len(small_run) == 4 * 1 * 2 * len(sim.CENTRINGS) * len(sim.HAIR_MASKS)
    cells = {(r["disturbance"], r["diameter_mm"], r["edge_sd_mm"], r["centring"], r["hair_mask"])
             for r in small_run}
    assert len(cells) == len(small_run)
    for r in small_run:
        assert ROW_KEYS <= set(r)
        assert r["certainty_level"] == 0
        assert r["trials"] == 4


def test_run_rows_carry_the_disturbance_and_closed_form(sim, rs, small_run):
    for r in small_run:
        dist = rs.DISTURBANCES[r["disturbance"]]
        assert r["family"] == dist["family"] and r["level"] == dist["level"]
        assert r["blur_sd_mm"] == BLUR and r["px_per_mm"] == PX
        assert r["closed_form_width_mm"] == pytest.approx(closed_form(r["edge_sd_mm"], BLUR), abs=1e-9)


def test_run_bookkeeping(sim, small_run):
    for r in small_run:
        assert r["rejected"] == r["rejected_centre"] + r["rejected_measure"]
        assert 0 <= r["rejected"] <= r["trials"]
        acc = r["trials"] - r["rejected"]
        if acc >= 1:
            assert r["bias_mm"] == pytest.approx(r["mean_width_mm"] - r["true_width_mm"], abs=1e-9)
            assert r["mean_abs_error_mm"] >= abs(r["bias_mm"]) - 1e-12
        else:
            assert r["mean_width_mm"] is None and r["bias_mm"] is None
        if acc >= 2:
            assert r["sdc_mm"] == pytest.approx(sim.SDC_FACTOR * r["sd_error_mm"], abs=1e-12)
        else:
            assert r["sd_error_mm"] is None and r["sdc_mm"] is None
        if r["centring"] != "found":
            assert r["rejected_centre"] == 0


def test_truth_is_shared_by_paired_cells(small_run):
    """READING 2: the truth does not depend on centring or hair mask, and for
    'none', 'hair_2' and 'gradient_20' (no tanning) it is the same spot. All
    trials share it here, since truth is on uniform skin."""
    by = {}
    for r in small_run:
        by.setdefault((r["diameter_mm"], r["edge_sd_mm"], r["disturbance"]), set()).add(
            round(r["true_width_mm"], 12))
    for k, v in by.items():
        assert len(v) == 1, k
    for es in (0.0, 0.2):
        t = {next(iter(by[(2.0, es, dist)])) for dist in ("none", "hair_2", "gradient_20")}
        assert len(t) == 1


def test_truth_follows_the_closed_form(small_run):
    for r in small_run:
        assert r["true_width_mm"] == pytest.approx(r["closed_form_width_mm"], abs=0.05)


def test_centre_error_by_centring(sim, rs, small_run):
    for r in small_run:
        if r["centring"] == "true" and r["mean_centre_error_mm"] is not None:
            assert r["mean_centre_error_mm"] == 0.0
        if r["centring"] == "frame" and r["mean_centre_error_mm"] is not None:
            assert r["mean_centre_error_mm"] == pytest.approx(rs.SHIFT_MM, abs=1e-9)


def test_capture_equal_to_truth_gives_zero_error(sim):
    """No noise, no mottle, nothing disturbed, true centre, no mask: the capture
    IS the truth image (mottled skin at SD 0 renders as uniform skin), so every
    trial's error is 0."""
    rows = sim.run(seed=3, trials=3, diameters=(2.0,), edge_sds=(0.0, 0.1),
                   disturbances=("none", "tan_5"), noise_sd=0.0, mottle_sd=0.0)
    for r in rows:
        if r["centring"] == "true" and r["hair_mask"] == "none":
            assert r["rejected"] == 0
            assert abs(r["bias_mm"]) <= 1e-9 and r["sd_error_mm"] <= 1e-9 and r["sdc_mm"] <= 1e-9


def test_rotation_alone_costs_almost_nothing_with_the_true_centre(sim):
    rows = sim.run(seed=3, trials=3, diameters=(2.0,), edge_sds=(0.1,),
                   disturbances=("rotation_10",), noise_sd=0.0, mottle_sd=0.0)
    r = [x for x in rows if x["centring"] == "true" and x["hair_mask"] == "none"][0]
    assert abs(r["bias_mm"]) <= 0.01 and r["sd_error_mm"] <= 0.01


def test_noise_free_found_centre_is_close(sim):
    rows = sim.run(seed=4, trials=3, diameters=(2.0,), edge_sds=(0.1,),
                   disturbances=("none",), noise_sd=0.0, mottle_sd=0.0)
    r = [x for x in rows if x["centring"] == "found" and x["hair_mask"] == "none"][0]
    assert r["rejected"] == 0 and r["mean_centre_error_mm"] <= 0.05
    assert abs(r["bias_mm"]) <= 0.02


def test_run_is_reproducible_and_seeded(sim):
    kw = dict(trials=3, diameters=(2.0,), edge_sds=(0.1,), disturbances=("hair_2", "gradient_5"))
    a = sim.run(seed=21, **kw)
    b = sim.run(seed=21, **kw)
    c = sim.run(seed=22, **kw)
    assert a == b
    key = lambda rows: [(r["mean_width_mm"], r["sd_error_mm"]) for r in rows]
    assert key(a) != key(c)


def test_a_groups_captures_do_not_depend_on_other_groups(sim):
    """Running only 'none' gives the same 'none' rows as running it beside
    another disturbance: a group's captures depend only on the seed, its own
    disturbance, diameter, edge and trial index (see run() in the docstring)."""
    kw = dict(seed=5, trials=3, diameters=(2.0,), edge_sds=(0.1,))
    alone = sim.run(disturbances=("none",), **kw)
    both = [r for r in sim.run(disturbances=("hair_2", "none"), **kw) if r["disturbance"] == "none"]
    assert sorted(alone, key=lambda r: (r["centring"], r["hair_mask"])) == \
        sorted(both, key=lambda r: (r["centring"], r["hair_mask"]))


def test_running_never_touches_the_ledger(sim):
    files = [ROOT / "data" / "evidence.csv", ROOT / "data" / "evidence_quotes.jsonl"]

    def digest():
        return [hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None for f in files]

    before = digest()
    sim.run(seed=1, trials=2, diameters=(2.0,), edge_sds=(0.0,), disturbances=("none",))
    assert digest() == before


# ---- resolution summary ------------------------------------------------------------

def _rows(sim, rs, overrides=None, disturbances=("none", "hair_2"), diameter=2.0):
    """Fabricated rows that pass everything; overrides maps
    (disturbance, edge_sd, centring, hair_mask, field) -> value."""
    overrides = overrides or {}
    out = []
    for dist in disturbances:
        for es in sim.EDGE_SD_MM:
            for c in sim.CENTRINGS:
                for h in sim.HAIR_MASKS:
                    r = dict(certainty_level=0, disturbance=dist,
                             family=rs.DISTURBANCES[dist]["family"],
                             level=rs.DISTURBANCES[dist]["level"], diameter_mm=diameter,
                             edge_sd_mm=es, blur_sd_mm=BLUR, px_per_mm=PX, centring=c,
                             hair_mask=h, closed_form_width_mm=closed_form(es, BLUR),
                             true_width_mm=closed_form(es, BLUR), mean_width_mm=closed_form(es, BLUR),
                             bias_mm=0.0, sd_error_mm=0.02, sdc_mm=sim.SDC_FACTOR * 0.02,
                             mean_abs_error_mm=0.02, mean_centre_error_mm=0.0, trials=100,
                             rejected=0, rejected_centre=0, rejected_measure=0)
                    for f in list(r):
                        k = (dist, es, c, h, f)
                        if k in overrides:
                            r[f] = overrides[k]
                    out.append(r)
    return out


KEY = ("hair_2", 0.1, "found", "detected")


def test_summary_all_resolve(sim, rs):
    res = sim.resolution_summary(_rows(sim, rs))
    assert len(res) == 2 * len(sim.EDGE_SD_MM) * len(sim.CENTRINGS) * len(sim.HAIR_MASKS)
    for k, e in res.items():
        assert {"sdc_mm", "bias_mm", "sdc_ok", "bias_ok", "acceptance_ok", "resolves"} <= set(e)
        assert e["resolves"] is True, k
        assert e["sdc_mm"] == pytest.approx(sim.SDC_FACTOR * 0.02)


@pytest.mark.parametrize("field, value, key", [
    ("sdc_mm", 0.11, "sdc_ok"),
    ("bias_mm", -0.06, "bias_ok"),
    ("bias_mm", 0.06, "bias_ok"),
    ("rejected", 11, "acceptance_ok"),
    ("sdc_mm", None, "sdc_ok"),
    ("bias_mm", None, "bias_ok"),
])
def test_summary_each_criterion_can_fail(sim, rs, field, value, key):
    res = sim.resolution_summary(_rows(sim, rs, {KEY + (field,): value}))
    assert res[KEY][key] is False and res[KEY]["resolves"] is False
    assert res[("none", 0.1, "found", "detected")]["resolves"] is True


def test_summary_thresholds_are_inclusive(sim, rs):
    o = {KEY + ("sdc_mm",): 0.1, KEY + ("bias_mm",): -0.05, KEY + ("rejected",): 10}
    assert sim.resolution_summary(_rows(sim, rs, o))[KEY]["resolves"] is True


def test_summary_threshold_is_a_parameter(sim, rs):
    o = {KEY + ("sdc_mm",): 0.15}
    assert sim.resolution_summary(_rows(sim, rs, o))[KEY]["resolves"] is False
    assert sim.resolution_summary(_rows(sim, rs, o), threshold_mm=0.2)[KEY]["resolves"] is True


def test_summary_reads_only_the_requested_diameter(sim, rs):
    extra = [dict(r, diameter_mm=4.0, sdc_mm=5.0) for r in _rows(sim, rs)]
    res = sim.resolution_summary(_rows(sim, rs) + extra)
    assert all(e["resolves"] for e in res.values())
    assert not any(e["resolves"] for e in sim.resolution_summary(_rows(sim, rs) + extra, diameter_mm=4.0).values())


def test_summary_without_the_diameter_is_an_error(sim, rs):
    with pytest.raises(ValueError):
        sim.resolution_summary(_rows(sim, rs, diameter=4.0))


# ---- command line --------------------------------------------------------------------

def test_command_line_writes_both_files(tmp_path):
    cmd = [sys.executable, str(EXPERIMENTS / "edge_width_sim.py"), "--out", str(tmp_path),
           "--trials", "2", "--seed", "1", "--diameters", "2.0", "--disturbances", "none"]
    subprocess.run(cmd, check=True, cwd=ROOT, timeout=600)
    res = list(csv.DictReader(open(tmp_path / "edge_width_results.csv", newline="")))
    summ = list(csv.DictReader(open(tmp_path / "edge_width_resolution.csv", newline="")))
    assert res and summ
    assert ROW_KEYS <= set(res[0])
    assert {"disturbance", "edge_sd_mm", "centring", "hair_mask", "sdc_mm", "bias_mm",
            "sdc_ok", "bias_ok", "acceptance_ok", "resolves", "certainty_level"} <= set(summ[0])
    assert {r["certainty_level"] for r in res} == {"0"}
    assert {r["certainty_level"] for r in summ} == {"0"}
    assert {r["disturbance"] for r in res} == {"none"}
