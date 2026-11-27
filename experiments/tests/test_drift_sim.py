"""Tests for the simulation extension, written before the code exists.

SIMULATION ONLY. Synthetic disks and synthetic texture. No patient images.

Run:  python3 -m pytest experiments/tests -q

SPECIFICATION (STATUS.md, "Next session": "extend the simulation: lighting and
white-balance drift, brown spot on mottled background, 2 to 8 mm, tests written
before the code"). The builder writes experiments/drift_sim.py to this contract
and may not change this file.

Scene
  DIAMETERS_MM        sorted tuple of spot diameters; first 2.0, last 8.0, >= 4 values.
  SKIN_RGB            linear-RGB triple in (0, 1) for nearby skin.
  WHITE_SPOT_RGB      lighter than skin (IGH white spot).
  BROWN_SPOT_RGB      darker and yellower than skin (solar lentigo).
  render(diameter_mm, *, px_per_mm=20, spot="white" | "brown", contrast_scale=1.0,
         background="uniform" | "mottled", mottle_sd=0.0, mottle_corr_mm=1.0,
         shift_mm=0.0, exposure_gain=1.0, wb_gains=(1.0, 1.0, 1.0),
         noise_sd=0.0, blur_sd_mm=0.0, seed=0)
      -> float ndarray (n, n, 3), linear RGB, square field centred on the outline.
      * contrast_scale scales the spot's departure from skin (0 = invisible spot).
      * mottled: multiplicative luminance texture; mottle_sd is the SD of the
        multiplier (0.05 = 5 %), mottle_corr_mm its correlation length, texture
        fixed by seed. mottle_sd=0 gives exactly the uniform background.
      * shift_mm moves the whole scene (skin texture and spot) along +x
        relative to the fixed measuring outline, as a misplaced capture does.
      * exposure_gain multiplies all channels (lighting drift); wb_gains
        multiplies each channel (white-balance drift).
      * diameter_mm <= 0 raises ValueError.
Measurement
  measure_contrast(img, diameter_mm, px_per_mm, *, correction="none" | "ring_white")
      -> {"L": .., "a": .., "b": ..}: mean CIELAB (D65) inside the centred outline
      minus mean CIELAB in the reference ring (gap 1.0 mm, width 1.5 mm, as in
      alignment_pixel_sim.py). Lab is computed PER PIXEL, then averaged.
      "ring_white" divides each channel by its ring mean before conversion, so the
      result is invariant to any per-channel gain.
  change_pct(base_img, follow_img, diameter_mm, px_per_mm, *, channel="L",
             correction="none") -> 100 * (c_follow - c_base) / c_base.
      Raises ZeroDivisionError when |c_base| < 1e-6 (refused, never divided by).
Experiment
  DRIFTS              dict name -> (exposure_gain, wb_gains); has "none" = (1.0, (1, 1, 1)),
                      at least one exposure-only drift and one white-balance drift.
  run(*, seed, trials, px_per_mm=20, diameters=DIAMETERS_MM, shifts=(0.0, 0.25, 0.5),
      noise_sd=<default>, mottle_sd=<default>) -> list of dict rows.
      Simulates an UNCHANGED spot, so true_change_pct is 0 in every row.
      One row per spot x background x diameter x shift x drift x correction, for
      spots ("white", "brown"), backgrounds ("uniform", "mottled"), corrections
      ("none", "ring_white"), channel "L". Each trial draws one skin texture used
      for both visits; capture noise is drawn independently per visit.
      Row keys include: spot, background, diameter_mm, shift_mm, drift, correction,
      true_change_pct, mean_abs_error_pct_points, trials, rejected.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PX_FAST = 10            # px/mm for property tests where only exactness or order matters
PX_FINE = 40            # px/mm for the closed-form comparison


@pytest.fixture(scope="module")
def sim():
    import drift_sim
    return drift_sim


def closed_form_retained(diameter, shift):
    """Fraction of a uniform disk inside an equal, displaced outline (alignment.py)."""
    s = shift / diameter
    if s >= 1:
        return 0.0
    return 2 * (math.acos(s) - s * math.sqrt(1 - s * s)) / math.pi


def luminance(img):
    return img @ np.array([0.2126, 0.7152, 0.0722])


# ---- scene definition -------------------------------------------------------

def test_diameters_cover_2_to_8_mm(sim):
    d = tuple(sim.DIAMETERS_MM)
    assert d == tuple(sorted(d)) and len(set(d)) == len(d)
    assert d[0] == 2.0 and d[-1] == 8.0 and len(d) >= 4


def test_spot_colours_point_the_right_way(sim):
    skin = sim.measure_contrast(sim.render(8.0, px_per_mm=PX_FAST, spot="white"), 8.0, PX_FAST)
    brown = sim.measure_contrast(sim.render(8.0, px_per_mm=PX_FAST, spot="brown"), 8.0, PX_FAST)
    assert skin["L"] >= 5.0                              # white spot is clearly lighter
    assert brown["L"] <= -5.0 and brown["b"] > 0.0       # brown spot is darker and yellower


def test_render_rejects_nonpositive_diameter(sim):
    for bad in (0.0, -2.0):
        with pytest.raises(ValueError):
            sim.render(bad, px_per_mm=PX_FAST)


def test_zero_mottle_is_exactly_uniform(sim):
    a = sim.render(4.0, px_per_mm=PX_FAST, spot="brown", background="uniform")
    b = sim.render(4.0, px_per_mm=PX_FAST, spot="brown", background="mottled", mottle_sd=0.0, seed=3)
    assert np.array_equal(a, b)


def test_mottle_has_requested_size_and_is_spatially_correlated(sim):
    img = sim.render(2.0, px_per_mm=20, spot="brown", contrast_scale=0.0,
                     background="mottled", mottle_sd=0.05, mottle_corr_mm=1.0, seed=11)
    m = luminance(img) / luminance(np.asarray(sim.SKIN_RGB, float)[None, None, :])[0, 0]
    # Tolerance: a 1 mm correlation length on a field of >= 10 mm gives >= 100
    # independent patches, so the sample SD is within about 10 % of the target;
    # 25 % leaves room for edge handling. Mean within 0.02 of 1 likewise.
    assert abs(m.std() / 0.05 - 1) < 0.25
    assert abs(m.mean() - 1) < 0.02
    # Neighbouring pixels 0.05 mm apart must be strongly correlated (texture, not noise).
    r = np.corrcoef(m[:, :-1].ravel(), m[:, 1:].ravel())[0, 1]
    assert r > 0.5


def test_shift_moves_skin_and_spot_together(sim):
    k = 3                                   # whole pixels; exact for any sensible renderer
    base = sim.render(4.0, px_per_mm=PX_FAST, spot="brown", background="mottled",
                      mottle_sd=0.05, seed=4)
    moved = sim.render(4.0, px_per_mm=PX_FAST, spot="brown", background="mottled",
                       mottle_sd=0.05, seed=4, shift_mm=k / PX_FAST)
    inner = slice(2 * k, -2 * k)            # ignore the edge columns that enter the field
    assert np.allclose(moved[inner, inner.start + k:inner.stop + k],
                       base[inner, inner], atol=1e-6)


# ---- the five required properties ------------------------------------------

@pytest.mark.parametrize("spot", ["white", "brown"])
@pytest.mark.parametrize("background", ["uniform", "mottled"])
@pytest.mark.parametrize("correction", ["none", "ring_white"])
def test_zero_shift_zero_drift_gives_zero_error(sim, spot, background, correction):
    kw = dict(px_per_mm=PX_FAST, spot=spot, background=background, mottle_sd=0.05, seed=9)
    for d in sim.DIAMETERS_MM:
        img = sim.render(d, **kw)
        # Identical inputs must give exactly zero; 1e-9 allows only float round-off.
        assert abs(sim.change_pct(img, sim.render(d, **kw), d, PX_FAST,
                                  correction=correction)) < 1e-9


def test_run_rows_without_shift_or_drift_have_zero_error(sim):
    rows = sim.run(seed=1, trials=2, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   shifts=(0.0,), noise_sd=0.0)
    still = [r for r in rows if r["drift"] == "none" and float(r["shift_mm"]) == 0.0]
    assert still, "run() must include the no-drift, no-shift rows"
    for r in still:
        assert float(r["true_change_pct"]) == 0.0
        assert abs(float(r["mean_abs_error_pct_points"])) < 1e-9


@pytest.mark.parametrize("spot", ["white", "brown"])
def test_matches_closed_form_circle_overlap(sim, spot):
    # Uniform skin, no blur, no noise, no drift. With per-pixel Lab averaging, the
    # contrast inside a displaced outline falls by exactly the uncovered area.
    # Tolerance 1.0 percentage point at 40 px/mm: the pixel model in
    # data/alignment_validation.csv differs from the formula by at most 0.63
    # points at 40 px/mm (2 mm spot, edge pixels that are part spot, part skin).
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE, spot=spot)
        for s in (0.25, 0.5, 0.75):         # <= ring gap, so the ring stays clean
            follow = sim.render(d, px_per_mm=PX_FINE, spot=spot, shift_mm=s)
            got = sim.change_pct(base, follow, d, PX_FINE, channel="L")
            want = 100 * (closed_form_retained(d, s) - 1)
            assert abs(got - want) < 1.0, (d, s, got, want)


def test_error_grows_as_spot_shrinks_uniform(sim):
    errs = []
    for d in sim.DIAMETERS_MM:
        base = sim.render(d, px_per_mm=PX_FINE)
        follow = sim.render(d, px_per_mm=PX_FINE, shift_mm=0.25)
        errs.append(abs(sim.change_pct(base, follow, d, PX_FINE)))
    # Deterministic and strictly ordered: smallest spot, largest false fading.
    assert all(a > b for a, b in zip(errs, errs[1:])), errs


def test_error_grows_as_spot_shrinks_mottled(sim):
    rows = sim.run(seed=2, trials=8, px_per_mm=PX_FAST, diameters=(2.0, 8.0),
                   shifts=(0.25,), noise_sd=0.0)
    pick = {(r["spot"], float(r["diameter_mm"])): float(r["mean_abs_error_pct_points"])
            for r in rows if r["background"] == "mottled" and r["drift"] == "none"
            and r["correction"] == "none"}
    # Geometry alone gives about 16 vs 4 points; the margin of a factor 2 leaves
    # room for texture effects in 8 trials.
    for spot in ("white", "brown"):
        assert pick[(spot, 2.0)] > 2 * pick[(spot, 8.0)], pick


def test_same_seed_reruns_are_identical(sim):
    kw = dict(seed=5, trials=3, px_per_mm=PX_FAST, diameters=(2.0, 8.0), shifts=(0.25,))
    assert sim.run(**kw) == sim.run(**kw)
    img_kw = dict(px_per_mm=PX_FAST, spot="brown", background="mottled",
                  mottle_sd=0.05, noise_sd=0.01, seed=5)
    assert np.array_equal(sim.render(3.0, **img_kw), sim.render(3.0, **img_kw))


def test_different_seeds_give_different_texture(sim):
    kw = dict(px_per_mm=PX_FAST, spot="brown", background="mottled", mottle_sd=0.05)
    assert not np.array_equal(sim.render(3.0, seed=1, **kw), sim.render(3.0, seed=2, **kw))


def test_zero_contrast_baseline_is_refused(sim):
    flat = sim.render(4.0, px_per_mm=PX_FAST, contrast_scale=0.0)
    spot = sim.render(4.0, px_per_mm=PX_FAST)
    with pytest.raises(ZeroDivisionError):
        sim.change_pct(flat, spot, 4.0, PX_FAST)
    with pytest.raises(ZeroDivisionError):
        sim.change_pct(flat, spot, 4.0, PX_FAST, correction="ring_white")


# ---- lighting and white-balance drift ---------------------------------------

def test_drift_table_has_the_required_kinds(sim):
    assert sim.DRIFTS["none"][0] == 1.0 and tuple(sim.DRIFTS["none"][1]) == (1.0, 1.0, 1.0)
    kinds = [(g, tuple(w)) for g, w in sim.DRIFTS.values()]
    assert any(g != 1.0 and w == (1.0, 1.0, 1.0) for g, w in kinds)     # exposure only
    assert any(len(set(w)) > 1 for g, w in kinds)                       # white balance


@pytest.mark.parametrize("spot,channel,drift", [
    ("white", "L", dict(exposure_gain=0.8)),
    ("brown", "L", dict(exposure_gain=1.25)),
    ("brown", "b", dict(wb_gains=(1.0, 1.0, 0.8))),
    ("brown", "b", dict(wb_gains=(1.15, 1.0, 0.9))),
])
def test_uncorrected_drift_fakes_a_change(sim, spot, channel, drift):
    # Lab is nonlinear, so a 20 % gain shifts L* contrast by several percent.
    # Requiring more than 1 point shows the uncorrected method is drift-sensitive.
    d = 4.0
    base = sim.render(d, px_per_mm=PX_FAST, spot=spot)
    follow = sim.render(d, px_per_mm=PX_FAST, spot=spot, **drift)
    assert abs(sim.change_pct(base, follow, d, PX_FAST, channel=channel)) > 1.0


@pytest.mark.parametrize("background", ["uniform", "mottled"])
@pytest.mark.parametrize("drift", [dict(exposure_gain=0.8),
                                   dict(wb_gains=(1.15, 1.0, 0.8)),
                                   dict(exposure_gain=1.2, wb_gains=(0.9, 1.0, 1.1))])
def test_ring_white_correction_cancels_any_channel_gain(sim, background, drift):
    # Per-channel gains cancel exactly in img / ring_mean; 1e-6 points is float round-off.
    for spot, channel in (("white", "L"), ("brown", "L"), ("brown", "b")):
        for d in (2.0, 8.0):
            kw = dict(px_per_mm=PX_FAST, spot=spot, background=background, mottle_sd=0.05, seed=6)
            got = sim.change_pct(sim.render(d, **kw), sim.render(d, **kw, **drift), d, PX_FAST,
                                 channel=channel, correction="ring_white")
            assert abs(got) < 1e-6, (spot, channel, d, got)


def test_run_covers_every_factor(sim):
    rows = sim.run(seed=3, trials=1, px_per_mm=PX_FAST, shifts=(0.0,), noise_sd=0.0)
    need = {"spot", "background", "diameter_mm", "shift_mm", "drift", "correction",
            "true_change_pct", "mean_abs_error_pct_points", "trials", "rejected"}
    assert need <= set(rows[0])
    assert {float(r["diameter_mm"]) for r in rows} == set(map(float, sim.DIAMETERS_MM))
    assert {r["spot"] for r in rows} == {"white", "brown"}
    assert {r["background"] for r in rows} == {"uniform", "mottled"}
    assert {r["correction"] for r in rows} == {"none", "ring_white"}
    assert {r["drift"] for r in rows} == set(sim.DRIFTS)
    corrected = [r for r in rows if r["correction"] == "ring_white"]
    assert all(abs(float(r["mean_abs_error_pct_points"])) < 1e-6 for r in corrected)


# ---- rule 7: synthetic shapes only -----------------------------------------

def test_no_image_file_readers(sim):
    # Guard for CLAUDE.md rule 7: the simulation builds its scenes; it never loads images.
    src = Path(sim.__file__).read_text()
    for banned in ("imread", "Image.open", "import PIL", "from PIL", "import cv2", "imageio"):
        assert banned not in src, banned
