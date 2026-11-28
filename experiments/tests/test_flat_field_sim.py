"""Tests for the blank-card (flat-field) correction step of the registration
stress simulation, written before the code exists.

SIMULATION ONLY, CERTAINTY LEVEL 0. Synthetic disks, synthetic texture,
synthetic straight "hairs", a synthetic uniform card. No patient images. What
the finished simulation reports is a hypothesis about the measuring method, not
evidence about real skin, real cameras or any treatment.

Run:  python3 -m pytest experiments/tests -q

Until experiments/flat_field_sim.py exists, every test here is SKIPPED (see
`pytestmark`), so the existing suite stays green. As soon as the builder adds
that file the tests run unchanged; the builder may not edit this file:
`git diff --exit-code <tests commit> -- experiments/tests` must stay clean.

WHY THIS STEP
  Round two (experiments/registration_stress_sim.py, content/experiments.md
  section 6) found that fall-off of light towards the field edges breaks every
  placement from 10 %, the smallest size tried, because the ring around the
  spot gets less light than the spot and the contrast itself changes. Its
  write-up names the next step: a flat-field correction, from a photograph of a
  blank card taken in the same session under the same light, tests first
  (plan C3; plan section 5 rung 1, "Lighting gradient ... and vignetting").
  This file is that step's contract. It does not change round two: the new
  module imports registration_stress_sim and adds one choice, `correction`,
  to every measurement.

SOURCE OF THE SPECIFICATION: content/experiments.md section 6 (the suggestion
and the lighting model it found the problem with), content/measurement-tool-plan.md
C3 and section 5 rung 1, and round two's contract in
test_registration_stress_sim.py, whose conventions, names and target are kept.
Where those leave a choice open, the choice made here is marked READING and can
be changed by Ben. No size here comes from a quoted source.

This file asserts what the simulation must compute (the card, the gain field,
the correction, its refusals, that it leaves round two untouched when switched
off, pairing, reproducibility, bookkeeping). It does NOT assert whether the
correction rescues any placement under any disturbance: that is the
experiment's result, computed by `evaluate_flat_field_target` and reported, not
presumed here. The only accuracy checks are on noise-free scenes, where they
test that the correction does what its name says.

THE MODEL (READING)
  The card is a flat, uniform, neutral reflector of known linear reflectance
  CARD_RGB (a measured grey or white card). It is photographed CARD_FRAMES
  times per session, at the same framing and under the same lighting field as
  that session's skin captures (round two's step 4, camera frame). Because the
  card has no texture and no spot, rotation, shift, hair and tanning do not
  apply to it. Blur and noise apply exactly as in render() step 5: blur, then
  additive Gaussian noise per pixel and per channel of SD noise_sd, from seed.
  The gain field is the mean of the frames, optionally smoothed, divided by
  CARD_RGB channel by channel. Correcting divides a capture by the gain of its
  own session. With a known reflectance the noise-free gain equals round two's
  lighting field I(x, y) exactly, so a noise-free, blur-free correction restores
  even light exactly. A card of unknown reflectance would leave one overall
  scale; that is the colour card's job (plan 2.1) and is not tested here.
  LIMITS this contract accepts: the card sits where the skin is and sees the
  same light (no change of distance or angle between card shot and skin shot);
  light is smooth and multiplicative, as round two models it.

Constants
  CORRECTIONS  = ("none", "blank_card").
  CARD_RGB     linear-RGB triple, neutral (all three channels equal), each in
               [0.15, 0.9]. Builder's choice, stated in the module (an 18 %
               grey card is 0.18; a white card about 0.8).
  CARD_FRAMES  = 3. READING: as many card frames as skin captures per session
               (plan 2.2, k = 3).
  CARD_SMOOTH_MM  float in [0.0, 1.0]: SD in mm of the Gaussian smoothing of
               the mean card frame before it becomes the gain. Builder's
               choice, stated in the module; 0.0 means no smoothing.
  FF_DISTURBANCES  default disturbance set of the run:
               ("none", "gradient_5", "gradient_20", "vignetting_10",
                "vignetting_20", "combined"). Every name is a key of
               registration_stress_sim.DISTURBANCES; "none" is there to show
               what the correction costs when the light is already even.

Card and correction
  render_card(diameter_mm, *, px_per_mm=20, gradient=0.0, gradient_dir_deg=0.0,
              vignetting=0.0, blur_sd_mm=0.0, noise_sd=0.0, seed=0,
              card_rgb=CARD_RGB) -> float ndarray (n, n, 3), linear RGB,
      n = registration_stress_sim.field_size(diameter_mm, px_per_mm).
      Noise-free and blur-free it is I(x, y) * card_rgb, with I exactly round
      two's lighting field. Blur, then noise, as render() step 5.
      Non-positive diameter raises ValueError.
  flat_field(cards, *, px_per_mm, smooth_mm=CARD_SMOOTH_MM, card_rgb=CARD_RGB)
      -> float ndarray (n, n, 3), the gain G.
      cards: a non-empty sequence of (n, n, 3) arrays of one shape (a single
      (n, n, 3) array counts as one frame). G = smooth(mean of frames) /
      card_rgb, per channel; smooth_mm = 0 skips smoothing. REFUSED, never
      divided by: ValueError when cards is empty, shapes differ, or any value
      of G is not finite or is <= 0 (a dark or missing card).
  correct(img, gain) -> img / gain, same shape. ValueError on a shape mismatch.

Experiment
  run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM,
      disturbances=FF_DISTURBANCES, scenarios=tuple(SCENARIOS),
      corrections=CORRECTIONS, shift_mm=SHIFT_MM, noise_sd=<default>,
      mottle_sd=<default>, blur_sd_mm=<default>, sticker_sd_mm=STICKER_SD_MM,
      card_frames=CARD_FRAMES, card_smooth_mm=CARD_SMOOTH_MM) -> list of dicts.
      Defaults not stated here are registration_stress_sim.run's. Names,
      scenarios, placements, regions, hair masks, truth, statistics and
      bookkeeping are exactly registration_stress_sim.run's, with one more key,
      `correction`, and one more row dimension: one row per correction x
      scenario x disturbance x diameter x placement x region x hair_mask.
      * "none" rows: every key of registration_stress_sim.run's row for the same
        arguments has the same value. Switching the correction off reproduces
        round two exactly, so the comparison is paired with its published run.
      * "blank_card" rows: the SAME skin captures as the "none" rows (paired).
        Each session (baseline and follow-up) gets its own card_frames card
        captures, under that session's own lighting (baseline: even light;
        follow-up: the disturbance's gradient, its per-trial gradient_dir_deg,
        and vignetting), with the run's blur_sd_mm and noise_sd and noise
        independent of every skin capture and of each other. Each capture is
        divided by its own session's gain BEFORE hair detection, placement and
        measurement; everything after that is round two unchanged.
      * Truth does not depend on the correction (light is a capture nuisance).
      * Extra key rejected_card: trials refused because flat_field refused a
        session's card (counted first). rejected = rejected_card +
        rejected_placement + rejected_mask. 0 on every "none" row.
      Unknown correction, disturbance or scenario raises ValueError or KeyError.
  evaluate_flat_field_target(rows, *, diameter_mm=2.0)
      -> {(correction, disturbance, placement, region, hair_mask): dict} where
      each dict is registration_stress_sim.evaluate_stress_target of that
      correction's rows alone (same keys, same thresholds, same refusals:
      a missing required row raises ValueError).

Outputs (not tested here, for the builder and the write-up): CSVs under data/
for the run and the target, labelled simulation, certainty level 0; every
number in the write-up cited by CSV line.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

pytestmark = pytest.mark.skipif(
    not (EXPERIMENTS / "flat_field_sim.py").exists(),
    reason="experiments/flat_field_sim.py not built yet; these tests are its contract",
)

PX_FAST = 10            # px/mm where only exactness or order matters
PX_REG = 20             # px/mm for statistics of noise (the plan's C1 minimum)
PX_FINE = 40            # px/mm for the closed-form comparison
MOTTLE = dict(background="mottled", mottle_sd=0.05)

WANT_FF_DISTURBANCES = ("none", "gradient_5", "gradient_20", "vignetting_10",
                        "vignetting_20", "combined")
LIGHT_ONLY = ("gradient_5", "gradient_20", "vignetting_10", "vignetting_20")
# Lighting settings used for exactness checks. Sizes bracket round two's.
LIGHTS = [dict(gradient=0.2, gradient_dir_deg=30.0),
          dict(vignetting=0.2),
          dict(vignetting=0.1),
          dict(gradient=0.2, gradient_dir_deg=135.0, vignetting=0.1)]


@pytest.fixture(scope="module")
def sim():
    import flat_field_sim
    return flat_field_sim


@pytest.fixture(scope="module")
def rs():
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


def light_field(n, px, gradient=0.0, gradient_dir_deg=0.0, vignetting=0.0):
    """Round two's lighting field, step 4 of render(), restated independently."""
    x, y = grid_mm(n, px)
    W = n / px
    phi = math.radians(gradient_dir_deg)
    u = x * math.cos(phi) + y * math.sin(phi)
    return (1 + gradient * u / W) * (1 - vignetting * (np.hypot(x, y) / (W / 2)) ** 2)


def noise_free_gain(sim, d, px, **light):
    return sim.flat_field([sim.render_card(d, px_per_mm=px, **light)], px_per_mm=px, smooth_mm=0.0)


# ---- constants ---------------------------------------------------------------

def test_constants(sim, rs):
    assert tuple(sim.CORRECTIONS) == ("none", "blank_card")
    c = tuple(float(v) for v in sim.CARD_RGB)
    assert len(c) == 3 and c[0] == c[1] == c[2], c
    assert 0.15 <= c[0] <= 0.9
    assert sim.CARD_FRAMES == 3 and isinstance(sim.CARD_FRAMES, int)
    assert 0.0 <= float(sim.CARD_SMOOTH_MM) <= 1.0
    assert tuple(sim.FF_DISTURBANCES) == WANT_FF_DISTURBANCES
    assert set(sim.FF_DISTURBANCES) <= set(rs.DISTURBANCES)
    # The correction adds to round two; it does not redefine round two's names.
    for k in ("DIAMETERS_MM", "SHIFT_MM", "SCENARIOS", "PLACEMENTS", "REGIONS",
              "HAIR_MASKS", "STICKER_SD_MM", "DISTURBANCES"):
        assert getattr(sim, k) == getattr(rs, k), k


# ---- the card ----------------------------------------------------------------

@pytest.mark.parametrize("light", LIGHTS + [dict()])
def test_card_is_the_lighting_field_times_its_reflectance(sim, rs, light):
    # Noise-free, blur-free: exactly I(x, y) * CARD_RGB (1e-9 relative, round-off).
    for d in (2.0, 5.0):
        card = sim.render_card(d, px_per_mm=PX_FAST, **light)
        n = rs.field_size(d, PX_FAST)
        assert card.shape == (n, n, 3)
        want = light_field(n, PX_FAST, **light)[..., None] * np.asarray(sim.CARD_RGB, float)
        assert np.allclose(card, want, rtol=1e-9, atol=0)


def test_card_has_the_same_size_as_the_skin_capture(sim, rs):
    for d in (2.0, 3.0, 8.0):
        assert sim.render_card(d, px_per_mm=PX_FAST).shape == rs.render(d, px_per_mm=PX_FAST).shape


@pytest.mark.parametrize("light", LIGHTS)
def test_card_sees_the_same_light_as_the_skin(sim, rs, light):
    # The lighting the card records is the lighting the skin capture got, for any
    # shift, rotation, tan or hair of the skin scene (those live in steps 1 to 3;
    # light is step 4, camera frame). Noise-free, no blur; 1e-9 relative.
    d = 3.0
    kw = dict(px_per_mm=PX_FAST, seed=4, shift_mm=(0.3, -0.1), rotation_deg=6.0,
              tan_dL=-3.0, hair_count=2, hair_seed=5, **MOTTLE)
    ratio = rs.render(d, **light, **kw) / rs.render(d, **kw)
    card_ratio = sim.render_card(d, px_per_mm=PX_FAST, **light) / np.asarray(sim.CARD_RGB, float)
    assert np.allclose(ratio, card_ratio, rtol=1e-9, atol=0)


def test_card_rgb_argument_is_used(sim):
    a = sim.render_card(3.0, px_per_mm=PX_FAST, vignetting=0.1, card_rgb=(0.2, 0.2, 0.2))
    b = sim.render_card(3.0, px_per_mm=PX_FAST, vignetting=0.1, card_rgb=(0.6, 0.6, 0.6))
    assert np.allclose(b, 3.0 * a, rtol=1e-12, atol=0)


def test_card_noise_is_render_noise(sim, rs):
    # render() step 5: additive Gaussian, per pixel and channel, SD noise_sd.
    # Measured SD within 5 % of noise_sd (with n*n*3 >= 10,000 samples the
    # sampling error of an SD is under 1 %). Same seed gives the same card,
    # another seed another card.
    d, sd = 3.0, 0.01
    clean = sim.render_card(d, px_per_mm=PX_REG, vignetting=0.1)
    a = sim.render_card(d, px_per_mm=PX_REG, vignetting=0.1, noise_sd=sd, seed=1)
    b = sim.render_card(d, px_per_mm=PX_REG, vignetting=0.1, noise_sd=sd, seed=1)
    c = sim.render_card(d, px_per_mm=PX_REG, vignetting=0.1, noise_sd=sd, seed=2)
    assert a.size >= 10_000
    assert np.array_equal(a, b) and not np.array_equal(a, c)
    r = (a - clean).ravel()
    assert abs(r.mean()) < 0.05 * sd and abs(r.std(ddof=1) / sd - 1) <= 0.05, r.std(ddof=1)


def test_card_blur_is_render_blur(sim, rs):
    # Same blur as render() step 5: a uniform skin scene with no spot and the
    # card with card_rgb = SKIN_RGB are the same picture, before and after blur,
    # under the same light. 1e-9 absolute.
    d = 3.0
    light = dict(gradient=0.2, gradient_dir_deg=60.0, vignetting=0.2)
    for blur in (0.0, 0.1):
        skin = rs.render(d, px_per_mm=PX_FAST, contrast_scale=0.0, blur_sd_mm=blur, **light)
        card = sim.render_card(d, px_per_mm=PX_FAST, blur_sd_mm=blur, card_rgb=tuple(rs.SKIN_RGB), **light)
        assert np.allclose(card, skin, rtol=0, atol=1e-9), blur


def test_card_rejects_nonpositive_diameter(sim):
    for bad in (0.0, -2.0):
        with pytest.raises(ValueError):
            sim.render_card(bad, px_per_mm=PX_FAST)


# ---- the gain field ----------------------------------------------------------

def test_even_light_gives_unit_gain_and_changes_nothing(sim, rs):
    # Zero drift gives zero correction: noise-free card under even light, no
    # smoothing, gives G = 1 exactly (1e-12), and correcting returns the capture.
    d = 3.0
    g = noise_free_gain(sim, d, PX_FAST)
    assert g.shape == (sim.render_card(d, px_per_mm=PX_FAST).shape)
    assert np.allclose(g, 1.0, rtol=0, atol=1e-12)
    img = rs.render(d, px_per_mm=PX_FAST, seed=3, noise_sd=0.01, **MOTTLE)
    assert np.allclose(sim.correct(img, g), img, rtol=0, atol=1e-12)


@pytest.mark.parametrize("light", LIGHTS)
def test_noise_free_gain_is_the_lighting_field(sim, light):
    d = 3.0
    g = noise_free_gain(sim, d, PX_FAST, **light)
    want = light_field(g.shape[0], PX_FAST, **light)
    for ch in range(3):
        assert np.allclose(g[..., ch], want, rtol=1e-9, atol=0), ch


def test_a_single_array_is_one_frame(sim):
    card = sim.render_card(3.0, px_per_mm=PX_FAST, vignetting=0.2, noise_sd=0.01, seed=3)
    a = sim.flat_field(card, px_per_mm=PX_FAST, smooth_mm=0.0)
    b = sim.flat_field([card], px_per_mm=PX_FAST, smooth_mm=0.0)
    assert np.array_equal(a, b)


def test_gain_is_the_mean_of_the_frames_over_the_reflectance(sim):
    # Definition, with smoothing off: G = mean(frames) / card_rgb, per channel.
    frames = [sim.render_card(3.0, px_per_mm=PX_FAST, vignetting=0.2, noise_sd=0.01, seed=s)
              for s in range(3)]
    g = sim.flat_field(frames, px_per_mm=PX_FAST, smooth_mm=0.0)
    want = np.mean(frames, axis=0) / np.asarray(sim.CARD_RGB, float)
    assert np.allclose(g, want, rtol=1e-12, atol=0)
    rgb = (0.4, 0.5, 0.6)
    g2 = sim.flat_field(frames, px_per_mm=PX_FAST, smooth_mm=0.0, card_rgb=rgb)
    assert np.allclose(g2, np.mean(frames, axis=0) / np.asarray(rgb), rtol=1e-12, atol=0)


def test_more_frames_means_less_noise_in_the_gain(sim):
    # Averaging k independent frames divides the noise SD by sqrt(k): 4 frames
    # against 1 should give a ratio of 0.5. Allowed 0.45 to 0.55 (sampling
    # error of each SD is under 1 % at >= 10,000 samples).
    d, light = 3.0, dict(vignetting=0.2)
    truth = noise_free_gain(sim, d, PX_REG, **light)
    frames = [sim.render_card(d, px_per_mm=PX_REG, noise_sd=0.01, seed=10 + s, **light) for s in range(4)]
    one = sim.flat_field(frames[:1], px_per_mm=PX_REG, smooth_mm=0.0) - truth
    four = sim.flat_field(frames, px_per_mm=PX_REG, smooth_mm=0.0) - truth
    ratio = four.std() / one.std()
    assert 0.45 <= ratio <= 0.55, ratio


def test_smoothing_lowers_gain_noise(sim):
    # A 0.2 mm smoothing spans several pixels at 20 px/mm, so it must cut the
    # residual noise of the gain; the field itself is smooth. Strictly lower,
    # and by at least half (a 2-D Gaussian of SD 4 px averages ~200 pixels).
    d, light = 3.0, dict(vignetting=0.2)
    truth = noise_free_gain(sim, d, PX_REG, **light)
    frame = sim.render_card(d, px_per_mm=PX_REG, noise_sd=0.01, seed=7, **light)
    raw = sim.flat_field(frame, px_per_mm=PX_REG, smooth_mm=0.0) - truth
    smooth = sim.flat_field(frame, px_per_mm=PX_REG, smooth_mm=0.2) - truth
    n = raw.shape[0]
    x, y = grid_mm(n, PX_REG)
    W = n / PX_REG
    inner = (np.abs(x) < W / 2 - 1.0) & (np.abs(y) < W / 2 - 1.0)   # away from the border
    assert smooth[inner].std() <= 0.5 * raw[inner].std(), (smooth[inner].std(), raw[inner].std())


def test_smoothing_is_stated_in_mm(sim, rs):
    # Gaussian smoothing of SD s (mm) adds exactly 2 s^2 to r^2 in the plane, so
    # on a noise-free pure fall-off field it lowers the gain near the frame
    # centre by vignetting * 2 s^2 / (W / 2)^2, at any resolution. A smoothing
    # read in pixels instead of mm would be 10 to 20 times narrower here and
    # 100 to 400 times weaker. Allowed 10 % either way for the sampled,
    # truncated kernel. Checked on the pixels within 0.3 mm of the centre,
    # far (> 3 s) from the field border.
    d, v, s = 3.0, 0.2, 0.3
    for px in (PX_FAST, PX_REG):
        card = sim.render_card(d, px_per_mm=px, vignetting=v)
        raw = sim.flat_field(card, px_per_mm=px, smooth_mm=0.0)
        smooth = sim.flat_field(card, px_per_mm=px, smooth_mm=s)
        n = raw.shape[0]
        W = n / px
        x, y = grid_mm(n, px)
        near = np.hypot(x, y) <= 0.3
        assert W / 2 - 0.3 > 3 * s
        want = v * 2 * s * s / (W / 2) ** 2
        got = (raw - smooth)[near][:, 1]
        assert np.all(np.abs(got / want - 1) <= 0.10), (px, got.min(), got.max(), want)


def test_dark_or_missing_card_is_refused_not_divided_by(sim):
    card = sim.render_card(3.0, px_per_mm=PX_FAST, vignetting=0.1)
    with pytest.raises(ValueError):
        sim.flat_field(np.zeros_like(card), px_per_mm=PX_FAST, smooth_mm=0.0)
    holed = card.copy()
    holed[3, 4, 1] = 0.0
    with pytest.raises(ValueError):
        sim.flat_field(holed, px_per_mm=PX_FAST, smooth_mm=0.0)
    neg = card.copy()
    neg[5, 5, 0] = -0.01
    with pytest.raises(ValueError):
        sim.flat_field(neg, px_per_mm=PX_FAST, smooth_mm=0.0)
    bad = card.copy()
    bad[2, 2, 2] = np.nan
    with pytest.raises(ValueError):
        sim.flat_field(bad, px_per_mm=PX_FAST, smooth_mm=0.0)
    with pytest.raises(ValueError):
        sim.flat_field([], px_per_mm=PX_FAST)
    with pytest.raises(ValueError):
        sim.flat_field([card, sim.render_card(4.0, px_per_mm=PX_FAST)], px_per_mm=PX_FAST)


def test_correct_rejects_a_mismatched_gain(sim, rs):
    img = rs.render(3.0, px_per_mm=PX_FAST)
    with pytest.raises(ValueError):
        sim.correct(img, noise_free_gain(sim, 4.0, PX_FAST))


# ---- the correction on skin captures ----------------------------------------

@pytest.mark.parametrize("light", LIGHTS)
def test_noise_free_correction_restores_even_light(sim, rs, light):
    # Noise-free, no blur: corrected lit capture equals the unlit capture,
    # pixel by pixel (1e-9 relative), with shift, rotation, tan and hair present.
    d = 3.0
    kw = dict(px_per_mm=PX_FAST, seed=9, shift_mm=(0.5, 0.0), rotation_deg=5.0,
              tan_dL=-5.0, tan_texture_sd=0.03, tan_seed=2, hair_count=2, hair_seed=3, **MOTTLE)
    lit = rs.render(d, **light, **kw)
    got = sim.correct(lit, noise_free_gain(sim, d, PX_FAST, **light))
    assert np.allclose(got, rs.render(d, **kw), rtol=1e-9, atol=0)


@pytest.mark.parametrize("light", LIGHTS)
def test_corrected_contrast_with_blur_is_close_to_even_light(sim, rs, light):
    # With the run's kind of blur (0.1 mm) blur and light do not commute
    # exactly, so the correction is close, not exact. Uniform skin, spot at the
    # centre, noise-free: corrected contrast within 0.1 % of the even-light
    # contrast, both regions. The leftover is second order in the blur (light
    # times blur times edge slope); 0.1 % is a fifth of round two's 0.5 %
    # allowance for resampled edge pixels and well under the 4 to 9 % that
    # 10 to 20 % fall-off moves the uncorrected contrast in this scene.
    d = 2.0
    kw = dict(px_per_mm=PX_REG, blur_sd_mm=0.1)
    gain = sim.flat_field(sim.render_card(d, **light, **kw), px_per_mm=PX_REG, smooth_mm=0.0)
    for region in rs.REGIONS:
        ref = rs.measure(rs.render(d, **kw), d, PX_REG, region=region)["L"]
        got = rs.measure(sim.correct(rs.render(d, **light, **kw), gain), d, PX_REG, region=region)["L"]
        assert abs(got / ref - 1) <= 0.001, (region, got, ref)


def test_outline_matches_closed_form_after_correction(sim, rs):
    # As rounds one and two, but photographed under 20 % fall-off and a 20 %
    # ramp and then corrected: uniform skin, placement "none", noise-free, no
    # blur. Tolerance 1.0 point at 40 px/mm (round one's edge-pixel allowance).
    light = dict(gradient=0.2, gradient_dir_deg=45.0, vignetting=0.2)
    for d in (2.0, 8.0):
        base = rs.render(d, px_per_mm=PX_FINE)
        g = noise_free_gain(sim, d, PX_FINE, **light)
        for s in (0.25, 0.5):
            follow = sim.correct(rs.render(d, px_per_mm=PX_FINE, shift_mm=s, **light), g)
            got = rs.change_pct(base, follow, d, PX_FINE, region="outline")
            want = 100 * (lens_fraction(d / 2, d / 2, s) - 1)
            assert abs(got - want) < 1.0, (d, s, got, want)


def test_error_grows_as_spot_shrinks_after_correction(sim, rs):
    light = dict(vignetting=0.2)
    errs = []
    for d in (2.0, 4.0, 8.0):
        base = rs.render(d, px_per_mm=PX_FINE)
        g = noise_free_gain(sim, d, PX_FINE, **light)
        follow = sim.correct(rs.render(d, px_per_mm=PX_FINE, shift_mm=0.25, **light), g)
        errs.append(abs(rs.change_pct(base, follow, d, PX_FINE, region="outline")))
    assert errs[0] > errs[1] > errs[2], errs


@pytest.mark.parametrize("region", ["outline", "inner_disc"])
def test_zero_contrast_baseline_is_still_refused(sim, rs, region):
    g = noise_free_gain(sim, 4.0, PX_FAST, vignetting=0.1)
    flat = sim.correct(rs.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0, vignetting=0.1), g)
    spot = sim.correct(rs.render(4.0, px_per_mm=PX_FAST, vignetting=0.1), g)
    with pytest.raises(ZeroDivisionError):
        rs.change_pct(flat, spot, 4.0, PX_FAST, region=region)


# ---- the experiment ----------------------------------------------------------

SMALL_DIST = ("none", "vignetting_10", "gradient_20", "combined")
SMALL = dict(seed=3, trials=2, px_per_mm=PX_FAST, diameters=(2.0,))


@pytest.fixture(scope="module")
def small_run(sim):
    return sim.run(disturbances=SMALL_DIST, **SMALL)


def test_run_has_one_row_per_combination(sim, small_run):
    keys = [(r["correction"], r["scenario"], r["disturbance"], float(r["diameter_mm"]),
             r["placement"], r["region"], r["hair_mask"]) for r in small_run]
    assert len(keys) == len(set(keys))
    want = {(c, sc, ds, 2.0, p, rg, hm) for c in sim.CORRECTIONS for sc in sim.SCENARIOS
            for ds in SMALL_DIST for p in sim.PLACEMENTS for rg in sim.REGIONS
            for hm in sim.HAIR_MASKS}
    assert set(keys) == want


def test_run_rows_keep_round_two_keys_and_count_card_refusals(sim, small_run):
    need = {"correction", "scenario", "disturbance", "family", "level", "diameter_mm",
            "shift_mm", "placement", "region", "hair_mask", "true_change_pct",
            "mean_change_pct", "sd_change_pct", "bias_pct_points", "sd_error_pct_points",
            "mean_abs_error_pct_points", "base_contrast_L", "mean_change_L", "true_ring_dL",
            "mean_ring_dL", "mean_centre_error_mm", "mean_ring_excluded", "trials",
            "rejected", "rejected_card", "rejected_placement", "rejected_mask"}
    for r in small_run:
        assert need <= set(r), need - set(r)
        assert r["trials"] == 2
        assert r["rejected"] == r["rejected_card"] + r["rejected_placement"] + r["rejected_mask"]
        assert 0 <= r["rejected"] <= 2
        if r["correction"] == "none":
            assert r["rejected_card"] == 0


def test_correction_off_reproduces_round_two_exactly(sim, rs, small_run):
    # Same arguments, same seed: every "none" row carries every key and value of
    # round two's row. This pins that the card captures draw their noise without
    # disturbing round two's random streams, and that rows are paired with the
    # published round-two run.
    ref = rs.run(disturbances=SMALL_DIST, **SMALL)
    def key(r):
        return (r["scenario"], r["disturbance"], float(r["diameter_mm"]), r["placement"],
                r["region"], r["hair_mask"])
    mine = {key(r): r for r in small_run if r["correction"] == "none"}
    assert set(mine) == {key(r) for r in ref}
    for r in ref:
        got = mine[key(r)]
        for k, v in r.items():
            assert got[k] == v, (key(r), k, got[k], v)


def test_truth_does_not_depend_on_the_correction(small_run):
    truth = {}
    for r in small_run:
        k = (r["scenario"], r["disturbance"], float(r["diameter_mm"]), r["region"])
        truth.setdefault(k, set()).add((r["true_change_pct"], r["true_ring_dL"]))
    for k, v in truth.items():
        assert len(v) == 1, (k, v)


def test_under_even_light_without_noise_the_correction_is_paired_and_inert(sim):
    # Noise-free cards under even light give G = 1 exactly, so if the corrected
    # rows use the same skin captures as the uncorrected rows (the pairing the
    # contract asks for) every statistic is identical. Capture noise off too,
    # so a different noise draw would show. Smoothing off.
    rows = sim.run(seed=4, trials=2, px_per_mm=PX_FAST, diameters=(2.0,),
                   disturbances=("none",), noise_sd=0.0, blur_sd_mm=0.0, card_smooth_mm=0.0)
    by = {}
    for r in rows:
        k = (r["scenario"], r["placement"], r["region"], r["hair_mask"])
        by.setdefault(k, {})[r["correction"]] = r
    assert by
    for k, pair in by.items():
        a, b = pair["none"], pair["blank_card"]
        for f in set(a) - {"correction", "rejected_card"}:
            if isinstance(a[f], float) and isinstance(b[f], float):
                assert abs(a[f] - b[f]) < 1e-9, (k, f, a[f], b[f])
            else:
                assert a[f] == b[f], (k, f, a[f], b[f])


def test_exact_placement_without_noise_or_blur_has_zero_error_after_correction(sim):
    # Sticker with SD 0 places exactly. Without noise, blur or hair, the only
    # difference between a capture and the truth is the light, and a noise-free
    # card measured under that same light removes it exactly. So corrected rows
    # for the light-only disturbances have zero error (1e-9). This is the
    # correction's definition on a noise-free scene, not the experiment's result.
    rows = sim.run(seed=1, trials=2, px_per_mm=PX_FAST, diameters=(2.0,),
                   disturbances=("none",) + LIGHT_ONLY, corrections=("blank_card",),
                   noise_sd=0.0, blur_sd_mm=0.0, sticker_sd_mm=0.0, card_smooth_mm=0.0)
    seen = 0
    for r in rows:
        if r["placement"] == "sticker" and r["hair_mask"] == "none":
            seen += 1
            assert r["correction"] == "blank_card"
            assert r["rejected"] == 0, r
            assert abs(float(r["bias_pct_points"])) < 1e-9, r
            assert abs(float(r["mean_abs_error_pct_points"])) < 1e-9, r
            assert abs(float(r["mean_ring_dL"]) - float(r["true_ring_dL"])) < 1e-9, r
    assert seen == 2 * 5 * 2       # scenarios x disturbances x regions


def test_card_frames_are_used(sim):
    # With noise, the number of card frames changes the corrected result (more
    # averaging, different gain) and leaves the uncorrected rows alone.
    kw = dict(seed=6, trials=2, px_per_mm=PX_FAST, diameters=(2.0,),
              disturbances=("vignetting_10",), scenarios=("unchanged",))
    a = sim.run(card_frames=1, **kw)
    b = sim.run(card_frames=5, **kw)
    pick = lambda rows, c: sorted(
        [(r["placement"], r["region"], r["hair_mask"], r["mean_change_pct"]) for r in rows
         if r["correction"] == c], key=lambda t: t[:3])
    assert pick(a, "none") == pick(b, "none")
    assert pick(a, "blank_card") != pick(b, "blank_card")


def test_same_seed_reruns_are_identical(sim):
    kw = dict(seed=5, trials=2, px_per_mm=PX_FAST, diameters=(2.0,),
              disturbances=("vignetting_20", "combined"))
    assert sim.run(**kw) == sim.run(**kw)
    ck = dict(px_per_mm=PX_FAST, gradient=0.2, gradient_dir_deg=40.0, vignetting=0.1,
              blur_sd_mm=0.1, noise_sd=0.01, seed=5)
    assert np.array_equal(sim.render_card(3.0, **ck), sim.render_card(3.0, **ck))


def test_run_rejects_unknown_names(sim):
    base = dict(seed=1, trials=1, px_per_mm=PX_FAST, diameters=(2.0,))
    with pytest.raises((ValueError, KeyError)):
        sim.run(disturbances=("none",), corrections=("white_balance",), **base)
    with pytest.raises((ValueError, KeyError)):
        sim.run(disturbances=("sunburn",), **base)
    with pytest.raises((ValueError, KeyError)):
        sim.run(disturbances=("none",), scenarios=("invisible",), **base)


def test_run_default_disturbances(sim):
    import inspect
    p = inspect.signature(sim.run).parameters
    assert tuple(p["disturbances"].default) == WANT_FF_DISTURBANCES
    assert tuple(p["corrections"].default) == ("none", "blank_card")
    assert p["card_frames"].default == sim.CARD_FRAMES
    assert p["card_smooth_mm"].default == sim.CARD_SMOOTH_MM


# ---- target evaluation (logic only, on hand-made rows) -----------------------

def _rows(override=None, disturbances=None):
    """Rows for every correction x disturbance x placement x region x mask that
    meet every criterion. override maps (correction, scenario, disturbance,
    placement, region, hair_mask, field) -> value."""
    import registration_stress_sim as rs
    override = override or {}
    disturbances = tuple(rs.DISTURBANCES) if disturbances is None else disturbances
    out = []
    for c in ("none", "blank_card"):
        for sc, true in (("unchanged", 0.0), ("genuine_fading", -50.0)):
            for ds in disturbances:
                w = rs.DISTURBANCES[ds]
                for p in ("none", "ring_registration", "ring_registration_rigid", "sticker"):
                    for rg in ("outline", "inner_disc"):
                        for hm in ("none", "detected"):
                            r = dict(correction=c, scenario=sc, disturbance=ds,
                                     family=w["family"], level=w["level"], diameter_mm=2.0,
                                     shift_mm=0.5, placement=p, region=rg, hair_mask=hm,
                                     true_change_pct=true, mean_change_pct=true + 0.1,
                                     sd_change_pct=0.5, bias_pct_points=0.1,
                                     sd_error_pct_points=0.5, mean_abs_error_pct_points=0.4,
                                     trials=100, rejected=0, rejected_card=0,
                                     rejected_placement=0, rejected_mask=0)
                            for (o_c, o_sc, o_ds, o_p, o_rg, o_hm, f), v in override.items():
                                if (o_c, o_sc, o_ds, o_p, o_rg, o_hm) == (c, sc, ds, p, rg, hm):
                                    r[f] = v
                            out.append(r)
    return out


KEY = ("vignetting_10", "ring_registration_rigid", "inner_disc", "detected")


def test_evaluate_is_round_two_per_correction(sim, rs):
    o = {("blank_card", "unchanged") + KEY + ("sd_error_pct_points",): 1.3,
         ("none", "unchanged") + KEY + ("bias_pct_points",): 4.6}
    rows = _rows(o)
    res = sim.evaluate_flat_field_target(rows)
    assert len(res) == 2 * len(rs.DISTURBANCES) * 4 * 2 * 2
    for c in ("none", "blank_card"):
        ref = rs.evaluate_stress_target([r for r in rows if r["correction"] == c])
        for k, e in ref.items():
            assert res[(c,) + k] == e, (c, k)
    assert res[("none",) + KEY]["bias_ok"] is False and res[("none",) + KEY]["passes"] is False
    assert res[("blank_card",) + KEY]["sd_ok"] is False and res[("blank_card",) + KEY]["bias_ok"] is True


def test_evaluate_card_refusals_count_against_acceptance(sim):
    # A card refused in 11 of 100 trials is 11 rejected trials: over 10 %.
    o = {("blank_card", "unchanged") + KEY + ("rejected_card",): 11,
         ("blank_card", "unchanged") + KEY + ("rejected",): 11}
    res = sim.evaluate_flat_field_target(_rows(o))
    assert res[("blank_card",) + KEY]["acceptance_ok"] is False
    assert res[("none",) + KEY]["passes"] is True


def test_evaluate_missing_row_is_an_error(sim):
    rows = [r for r in _rows() if not (r["correction"] == "blank_card"
                                       and r["scenario"] == "genuine_fading"
                                       and r["disturbance"] == "vignetting_20"
                                       and r["placement"] == "sticker")]
    with pytest.raises(ValueError):
        sim.evaluate_flat_field_target(rows)


def test_evaluate_reads_only_the_requested_diameter(sim):
    extra = [dict(r, diameter_mm=8.0, bias_pct_points=50.0) for r in _rows()]
    assert all(e["passes"] for e in sim.evaluate_flat_field_target(_rows() + extra).values())
    assert not any(e["passes"] for e in
                   sim.evaluate_flat_field_target(_rows() + extra, diameter_mm=8.0).values())
