"""Tests for the spatial (grid) spot model (Module 6, step M5), written before the code exists.

SIMULATION ONLY. Synthetic cells on a synthetic lattice, synthetic images. No
patient images (CLAUDE.md rule 7). Nothing here, and nothing the model
produces, is evidence: no output enters data/evidence.csv.

Run:  python3 -m pytest experiments/tests -q

Until experiments/spot_model_grid.py exists this whole file is SKIPPED (reason
printed). It is not "passing". The builder's done-when check (plan section 6,
M6) is:
    SPOT_MODEL_GRID_REQUIRED=1 python3 -m pytest experiments/tests/test_spot_model_grid.py -q
which turns the skip into a hard failure and must show 0 skipped, 0 failed.
A spot_model_grid.py that exists but fails to import is an error, never a skip.
The builder may not change this file (git diff --exit-code <tests commit> --
experiments/tests stays clean).

SOURCE OF THIS CONTRACT: content/spot-model-plan.md sections 2 (space,
entities, rules), 4.3 (P1, P3), 5.1 (rendering and measurement), 6 (minimum
test list), 7.1 (V4, V6), 10.4 (claim levels) and section 11 (this step's
statistics and the predictions written before any grid result);
data/spot_model_params.csv (the register); the well-mixed model's contract
(docstring of experiments/tests/test_spot_model.py), which this model must
reproduce exactly when space is switched off; experiments/drift_sim.py (the
scene and measurement conventions the plan says to reuse).

WHAT IS DELIBERATELY NOT TESTED. Which explanation (H1, H2, mixture) fits the
quoted facts better; whether a transplant holds or fades under either; whether
H2's edge is wider than H1's at default rates; whether either gives "skip
areas". Those are outputs. A test that fixed them would build the answer in.
The tests below pin what the grid model computes, its invariants, and the
statistics that will later be read from it, so that those statistics are fixed
before anyone sees a grid result (plan section 11).

Out of scope for M6 (adding any of them needs a test addendum first): R6
melanocyte paracrine slowing (lambda_M), the R7 reservoir (rho_R, k_R), spot
growth or a moving dermal patch (P2), wounding, any drug, any gene therapy or
gene editing (plan 2.4).

------------------------------------------------------------------------------
CONTRACT

Module constants
  PARAMS         tuple of str == spot_model.PARAMS + GRID_PARAMS. Every one is
                 a `symbol` in data/spot_model_params.csv.
  GRID_PARAMS    ("lambda_D", "tx_site_capacity")   exactly; register rows
                 dermal_signal_reach and transplant_site_capacity.
  KINDS, INTERVENTIONS, STATES   equal to spot_model's.
  PX_PER_MM 20, BLUR_SD_MM 0.10, RING_GAP_MM 1.0, RING_WIDTH_MM 1.5: equal to
                 experiments/drift_sim.py (plan 5.1: same scene conventions).
  SKIP_DL        1.0 (L* units; the skip-area threshold, plan section 11).
  STRUCTURAL_ASSUMPTIONS  tuple, exactly these names (each is an ASSUMPTION
                 with no register row because it is a modelling choice, not a
                 number; plan section 11 states each one):
                   "site_spacing_from_n_M_ring", "one_resident_slot_per_site",
                   "one_fibroblast_per_site", "defect_patch_is_fixed_disc",
                   "daughter_copies_parent_lineage_and_age",
                   "transplant_fills_free_slots_up_to_capacity"

default_params(kind) -> new dict, keys == set(PARAMS). For every key in
  spot_model.PARAMS the value equals spot_model.default_params(kind)[key] (the
  grid is the same model plus space). lambda_D is the same for every kind (it
  is not a defect) and lies in the register range 0.05 to 2 mm.
  tx_site_capacity == 2 for every kind (register: base runs). Unknown kind ->
  ValueError.

geometry(params) -> dict
  field_mm   drift_sim.field_size(d_spot, PX_PER_MM) / PX_PER_MM, so a rendered
             image is exactly drift_sim's measuring field.
  n_side     round(field_mm * sqrt(n_M_ring)): one lattice site per melanocyte
             niche at the QUOTED surrounding density (PMID 2508572).
  h_mm       field_mm / n_side.
  x_mm       site centres along one axis, h_mm * (i + 0.5), i = 0..n_side-1.
  spot_mask  (n_side, n_side) bool: site centre within d_spot/2 of the field
             centre (field_mm/2, field_mm/2), boundary included.
  ring_mask  bool: d_spot/2 + RING_GAP_MM <= r <= d_spot/2 + RING_GAP_MM +
             RING_WIDTH_MM (the measurement plan's reference ring).

dermal_signal(source, h_mm, lambda_D, p_D, mu_D) -> float array, same shape
  Steady state of R5 on the dermal lattice: solves
      D - lambda_D**2 * Lap_h(D) = (p_D / mu_D) * source
  with Lap_h the five-point Laplacian at spacing h_mm and zero-flux
  (reflecting) boundaries, to relative residual below 1e-10.
  lambda_D == 0: D == (p_D / mu_D) * source exactly. p_D == 0 or source all
  zero: D exactly 0. With source == f_sen everywhere it equals the well-mixed
  D = p_D * f_sen / mu_D. Negative lambda_D, p_D or source, or mu_D <= 0 ->
  ValueError.

run(params, *, days, seed=0, mode="stochastic" | "expected", transplant_days=(),
    snapshot_days=None, fibroblasts="random" | "uniform", fibroblast_seed=None)
  -> dict. One square field (geometry(params)), one step per day, days
  0..days. Each lattice point has one dermal fibroblast and C =
  tx_site_capacity melanocyte SLOTS: one resident slot, which every rule below
  may fill, and C - 1 extra slots, which ONLY transplanted cells can take (so a
  transplant can raise density above normal skin, up to C times, as the
  nude-mouse graft's "388.75 +/- 213 mm2" against "220 +/- 28.28" suggests,
  PMID 2508572; C = 1 is single occupancy). Each slot holds at most one cell.
  Refusals (ValueError): everything spot_model.run refuses (unknown or missing
  key, negative rates or counts, f_sen or s_tx outside [0, 1], d_spot <= 0,
  T_K <= 0, days < 1, unknown mode, bad transplant_days, tx_rates not 0 or 1);
  lambda_D < 0; tx_site_capacity not a whole number in 1..3; unknown
  `fibroblasts`; snapshot_days not strictly increasing
  ints in [0, days]. Any other keyword (e.g. intervention=...) -> TypeError.
  snapshot_days None means (0, days).

  The defect patch is the disc spot_mask, fixed for the whole run:
  * Melanocyte lineages. A resident cell whose site is inside the disc carries
    the run's intrinsic values k_int, a_int, k_tr; outside the disc it carries
    default_params("healthy")'s k_int, a_int, k_tr. Transplanted cells carry
    the rates spot_model's tx_rates addendum gives them (tx_rates 0: the run's
    own k_int, a_int, k_tr; 1: k_int_tx, a_int_tx, k_tr_tx). Everything else
    (k_sen, k_loss, k_div, k_derm, T_K) applies everywhere.
  * Fibroblasts. "random": each dermal site inside the disc is senescent with
    probability f_sen (one draw per site from fibroblast_seed, default = seed),
    the same map in both modes; "uniform": every dermal site inside the disc
    has senescent share f_sen. Outside the disc every fibroblast is normal.
    Fibroblast draws never consume the random stream used by melanocytes.
    D_map = dermal_signal(fibroblast_map, h_mm, lambda_D, p_D, mu_D), constant
    in time.
  * Day 0: every site holds one active resident cell, age 0; melanin at every
    site at the healthy steady state (relative melanin 1, as in spot_model).
  * Each day, per cell, exactly spot_model's transition step with the local
    dermal term k_derm * D_map[site] (age multiplies the intrinsic rate; one
    step at most along active -> hypoactive -> senescent -> gone, and
    hypoactive -> gone; never backwards; never active -> gone). A lost cell
    leaves its slot empty. A site is "empty" when it holds no live cell.
  * Then division (R7, fills gaps only): an empty RESIDENT slot is filled with
    probability 1 - exp(-k_div * a / 4), a = number of its 4 neighbours (inside
    the field) holding at least one active cell (expected mode: the sum over
    neighbours of min(1, expected active cells), a mean-field approximation).
    The daughter is active and copies one active neighbouring cell chosen
    uniformly: its lineage (rates), its age clock and its transplant label.
    Division never fills an extra slot.
  * Then transplant (R9), on each listed day: round(N_tx * pi * d_spot**2 / 4)
    cells delivered (the same number as spot_model); Binomial(that, s_tx)
    (stochastic) or that * s_tx (expected) survive; survivors take empty sites
    inside the disc only, chosen uniformly at random, active, age 0,
    transplanted label. Survivors take FREE SLOTS (resident or extra) inside
    the disc, each free slot equally likely, without replacement. Survivors
    beyond the number of free disc slots are not placed and are reported as
    overflow. Expected mode: with E the summed free-slot probability inside the
    disc and S the survivors, every disc slot's free probability moves a share
    min(1, S / E) into a new age-0 active transplanted cohort; overflow
    max(0, S - E). With S <= E nothing overflows, so the grid places exactly
    the cells the well-mixed model adds.
  * Then melanin: each site's keratinocyte melanin follows spot_model's rule,
    with supply summed over the site's active cells, each at its lineage's
    k_tr; renewal time T_K. Only active cells supply. A site with two active
    healthy cells settles at melanin 2 (darker than surrounding skin).
  * Then the day is recorded.
  "stochastic": integer states, reproducible bit for bit from seed and
  fibroblast_seed. "expected": per-site state probabilities (the mean-field
  version of the same rules; exact mean of "stochastic" for a given fibroblast
  map when k_div == 0, because sites are then independent).

  Returned keys
    day               0..days
    spot, ring        dicts of daily arrays (length days + 1) summed over the
                      sites of spot_mask / ring_mask: active, hypoactive,
                      senescent (cell counts, all slots), empty (sites with
                      no live cell), gone (cumulative losses),
                      transplanted_alive; and melanin = MEAN melanin per site.
    n_sites           {"spot": spot_mask.sum(), "ring": ring_mask.sum()}
    fibroblast_map    (n_side, n_side) senescent share per dermal site
    D_map             (n_side, n_side)
    snapshots         {day: {"active", "hypoactive", "senescent", "melanin",
                      "transplanted"}} maps (n_side, n_side) for each snapshot
                      day: cells per site summed over slots (stochastic
                      integers 0..C, expected mode expected counts).
                      "transplanted" = live cells carrying the transplant label.
    transplant_overflow  list, one value per transplant session
    days_since_final_treatment  as spot_model (NaN before the final session;
                      CLAUDE.md rule 2, follow-up from the FINAL treatment)
    geometry          geometry(params)
    meta              {"claim_level": 0, "output_is": "hypothesis", "mode",
                       "seed", "fibroblast_seed", "fibroblasts",
                       "assumptions": sorted PARAMS whose register status is
                       ASSUMPTION, "structural_assumptions":
                       list(STRUCTURAL_ASSUMPTIONS)}

melanin_to_L     is spot_model.melanin_to_L (one mapping for both models).

render(result, day, *, blur_sd_mm=BLUR_SD_MM, noise_sd=0.0, seed=0)
  -> linear RGB float array (n_px, n_px, 3), n_px = drift_sim.field_size(
  d_spot, PX_PER_MM). Each pixel takes the melanin of the lattice site whose
  cell contains the pixel centre (site index floor(x_px_mm / h_mm)); its
  colour has L* = melanin_to_L(melanin) and the a*, b* of drift_sim.SKIN_RGB,
  converted to linear RGB (inverse of drift_sim.rgb_to_lab). Then a Gaussian
  blur of SD blur_sd_mm (FFT, like drift_sim.blur; 0 means none), then
  Gaussian noise of SD noise_sd per pixel and channel from seed. ValueError if
  `day` is not a snapshot day.

measure_dL(img, d_spot) == drift_sim.measure_contrast(img, d_spot, PX_PER_MM)["L"]
  (plan 5.1: a model prediction and a real measurement are the same number
  computed the same way).

six_month_readout(result) -> dict with EXACTLY the keys of spot_model's
  {"baseline_dL", "dL_at_6_months", "rho_at_6_months", "day_of_final_treatment",
   "day_of_readout"}; baseline = measure_dL(render(result, first session - 1))
  and readout = measure_dL(render(result, final session + 180)), both with
  default render options. ValueError if there was no transplant, the run ends
  before the readout day, or either day is not a snapshot day (never
  extrapolated, never interpolated). ZeroDivisionError on |baseline| < 1e-6.

Image statistics (plan section 11; inputs are images in drift_sim's field for
spot diameter d_spot; r is the distance of a pixel centre from the field centre)
  edge_width(img, d_spot) -> mm. L* per pixel; L_ring = mean L* over the ring
  (drift_sim geometry); L_centre = mean L* over r <= d_spot / 4; C = L_centre -
  L_ring, ZeroDivisionError if |C| < 1e-6. Radial profile P = mean L* in bins
  [k/PX_PER_MM, (k+1)/PX_PER_MM), assigned to bin centres; q = (P - L_ring)/C.
  r_t = the first bin centre, going outward, at which q < t, linearly
  interpolated with the previous bin centre. Returns r_0.1 - r_0.9. ValueError
  if q never falls below 0.1.
  edge_midpoint(img, d_spot) -> r_0.5 by the same rule.
  skip_score(img, d_spot) -> share of pixels with r <= 0.6 * d_spot / 2 (the
  measurement plan's inner disc r_S) whose L* is below the median L* of those
  pixels by more than SKIP_DL ("retained pigment" = darker than the spot's own
  median).
  rim_centre_dL(img, d_spot) -> mean L* over r <= 0.3 * d_spot / 2 minus mean
  L* over 0.6 * d_spot / 2 < r <= 0.85 * d_spot / 2. Positive = centre lighter
  than the rim.
------------------------------------------------------------------------------
"""
import csv
import hashlib
import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))

import drift_sim as ds  # noqa: E402  existing, tested scene conventions
import spot_model as sm  # noqa: E402  the well-mixed model this one extends

if os.environ.get("SPOT_MODEL_GRID_REQUIRED") == "1":
    import spot_model_grid as gm  # noqa: E402  hard failure if missing
else:
    gm = pytest.importorskip(
        "spot_model_grid",
        reason="experiments/spot_model_grid.py not written yet (plan step M6); "
               "tests precede the implementation",
        exc_type=ModuleNotFoundError,
    )

REGISTER = ROOT / "data" / "spot_model_params.csv"
COUNT_KEYS = ("active", "hypoactive", "senescent", "empty", "gone")
REGION_KEYS = COUNT_KEYS + ("transplanted_alive", "melanin")
MAP_KEYS = ("active", "hypoactive", "senescent", "melanin", "transplanted")
STRUCTURAL = {
    "site_spacing_from_n_M_ring", "one_resident_slot_per_site",
    "one_fibroblast_per_site", "defect_patch_is_fixed_disc",
    "daughter_copies_parent_lineage_and_age",
    "transplant_fills_free_slots_up_to_capacity",
}

TWO_YEARS = 730
ONE_YEAR = 365

# Tolerance for quantities the contract makes exact (identities, the
# well-mixed limit, constants). 1e-9 relative is far above double rounding over
# 730 daily steps (~1e-13) and far below any modelled effect.
EXACT_REL = 1e-9
# The dermal-signal solver must reach relative residual 1e-10; 1e-6 on sums
# and symmetries leaves four orders of margin for an iterative solver.
SOLVER_REL = 1e-6


def register_rows():
    with open(REGISTER, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def wm_params(p):
    """The well-mixed model's share of a grid parameter dict."""
    return {k: p[k] for k in sm.PARAMS}


def site_r(geom):
    x = np.asarray(geom["x_mm"])
    X, Y = np.meshgrid(x, x)
    c = geom["field_mm"] / 2
    return np.hypot(X - c, Y - c)


def pixel_r(n_px):
    c = (np.arange(n_px) + 0.5) / gm.PX_PER_MM
    X, Y = np.meshgrid(c, c)
    c0 = n_px / gm.PX_PER_MM / 2
    return np.hypot(X - c0, Y - c0)


def local(params):
    """Switch off both couplings between sites: no diffusion, no division."""
    return dict(params, lambda_D=0.0, k_div=0.0)


def h2_strong(**kw):
    """H2 with a dermal coupling strong enough to make a spot within two years,
    so the spatial tests stay fast. The edge tests only need A spot, not the
    default rates' spot."""
    p = dict(gm.default_params("H2"), k_derm=0.01)
    p.update(kw)
    return p


def h1_strong(**kw):
    p = dict(gm.default_params("H1"), k_int=1e-3)
    p.update(kw)
    return p


def same_result(a, b, region_keys=REGION_KEYS):
    for reg in ("spot", "ring"):
        for k in region_keys:
            if not np.array_equal(a[reg][k], b[reg][k]):
                return False
    if set(a["snapshots"]) != set(b["snapshots"]):
        return False
    for d in a["snapshots"]:
        for k in MAP_KEYS:
            if not np.array_equal(a["snapshots"][d][k], b["snapshots"][d][k]):
                return False
    return True


# ---------------------------------------------------------------- the register

def test_params_are_the_well_mixed_params_plus_grid_params_and_all_registered():
    assert tuple(gm.GRID_PARAMS) == ("lambda_D", "tx_site_capacity")
    assert tuple(gm.PARAMS) == tuple(sm.PARAMS) + tuple(gm.GRID_PARAMS)
    symbols = {r["symbol"] for r in register_rows()}
    missing = set(gm.PARAMS) - symbols
    assert not missing, f"parameters not in data/spot_model_params.csv: {missing}"


def test_out_of_scope_rules_are_not_parameters():
    """R6 and the R7 reservoir are off in M6 (plan 2.3: 'off in the base
    runs'); no symbol names a gene, vector or edit (plan 2.4)."""
    assert not {"lambda_M", "rho_R", "k_R"} & set(gm.PARAMS)
    banned = ("gene", "crispr", "vector", "edit", "aav", "mrna")
    assert not [s for s in gm.PARAMS if any(b in s.lower() for b in banned)]
    assert tuple(gm.INTERVENTIONS) == ("transplant",)
    assert tuple(gm.KINDS) == tuple(sm.KINDS)
    assert tuple(gm.STATES) == tuple(sm.STATES)


def test_defaults_are_the_well_mixed_defaults():
    lams = set()
    for kind in gm.KINDS:
        p = gm.default_params(kind)
        assert set(p) == set(gm.PARAMS)
        w = sm.default_params(kind)
        assert {k: p[k] for k in sm.PARAMS} == w
        assert 0.05 <= p["lambda_D"] <= 2.0      # register range
        lams.add(p["lambda_D"])
        assert p["tx_site_capacity"] == 2        # register: base runs
    assert len(lams) == 1                        # signal reach is not a defect
    with pytest.raises(ValueError):
        gm.default_params("H3")
    a = gm.default_params("H1")
    a["lambda_D"] = 99.0
    assert gm.default_params("H1")["lambda_D"] != 99.0


def test_unknown_and_missing_parameters_are_refused():
    p = gm.default_params("healthy")
    with pytest.raises(ValueError):
        gm.run(dict(p, k_unregistered=0.1), days=5)
    q = dict(p)
    del q["lambda_D"]
    with pytest.raises(ValueError):
        gm.run(q, days=5)


@pytest.mark.parametrize("key,value", [
    ("lambda_D", -0.1), ("k_int", -1e-4), ("k_div", -1e-4), ("f_sen", 1.5),
    ("s_tx", -0.1), ("d_spot", 0.0), ("T_K", 0.0), ("tx_rates", 0.5),
    ("tx_site_capacity", 0), ("tx_site_capacity", 1.5), ("tx_site_capacity", 4),
])
def test_out_of_range_values_are_refused(key, value):
    with pytest.raises(ValueError):
        gm.run(dict(gm.default_params("healthy"), **{key: value}), days=5)


@pytest.mark.parametrize("kw", [
    {"days": 0}, {"mode": "mean"}, {"fibroblasts": "clustered"},
    {"snapshot_days": (5, 3)}, {"snapshot_days": (0, 11)}, {"snapshot_days": (2.5,)},
    {"transplant_days": (0,)}, {"transplant_days": (4, 4)},
])
def test_bad_run_options_are_refused(kw):
    args = dict(days=10)
    args.update(kw)
    with pytest.raises(ValueError):
        gm.run(gm.default_params("H1"), **args)


def test_only_intervention_is_transplant():
    with pytest.raises(TypeError):
        gm.run(gm.default_params("healthy"), days=5, intervention="gene_therapy")


# ------------------------------------------------------------------ geometry

@pytest.mark.parametrize("d", [2.0, 3.0, 5.0])
def test_field_is_the_measurement_field_and_lattice_is_the_quoted_density(d):
    p = dict(gm.default_params("healthy"), d_spot=d)
    g = gm.geometry(p)
    n_px = ds.field_size(d, gm.PX_PER_MM)
    assert g["field_mm"] == pytest.approx(n_px / gm.PX_PER_MM, rel=EXACT_REL)
    assert g["n_side"] == round(g["field_mm"] * math.sqrt(p["n_M_ring"]))
    assert g["h_mm"] == pytest.approx(g["field_mm"] / g["n_side"], rel=EXACT_REL)
    want_x = g["h_mm"] * (np.arange(g["n_side"]) + 0.5)
    assert np.allclose(g["x_mm"], want_x, rtol=EXACT_REL, atol=0)
    # Rounding n_side moves the density by at most one site per side:
    density = g["n_side"] ** 2 / g["field_mm"] ** 2
    assert abs(math.sqrt(density) - math.sqrt(220)) <= 0.5 / g["field_mm"] + 1e-12


def test_scene_constants_match_drift_sim():
    assert gm.PX_PER_MM == 20
    assert gm.BLUR_SD_MM == ds.BLUR_SD_MM
    assert gm.RING_GAP_MM == ds.RING_GAP_MM
    assert gm.RING_WIDTH_MM == ds.RING_WIDTH_MM
    assert gm.SKIP_DL == 1.0
    assert set(gm.STRUCTURAL_ASSUMPTIONS) == STRUCTURAL
    assert len(gm.STRUCTURAL_ASSUMPTIONS) == len(STRUCTURAL)


@pytest.mark.parametrize("d", [2.0, 3.0, 5.0])
def test_spot_and_ring_masks_follow_their_definitions(d):
    g = gm.geometry(dict(gm.default_params("healthy"), d_spot=d))
    r = site_r(g)
    assert np.array_equal(g["spot_mask"], r <= d / 2)
    r0 = d / 2 + gm.RING_GAP_MM
    assert np.array_equal(g["ring_mask"], (r >= r0) & (r <= r0 + gm.RING_WIDTH_MM))
    # disc site count matches area x density within the lattice perimeter error
    # (a band one site wide around the edge: 2*pi*(d/2)/h sites)
    want = math.pi * d ** 2 / 4 / g["h_mm"] ** 2
    assert abs(g["spot_mask"].sum() - want) <= math.pi * d / g["h_mm"]


# ------------------------------------------------------------- dermal signal

def test_dermal_signal_zero_without_source_or_production():
    src = np.zeros((40, 40))
    src[10:30, 10:30] = 0.5
    assert np.all(gm.dermal_signal(np.zeros((40, 40)), 0.05, 0.3, 1.0, 1.0) == 0)
    assert np.all(gm.dermal_signal(src, 0.05, 0.3, 0.0, 1.0) == 0)


def test_dermal_signal_local_limit_is_exact():
    rng = np.random.default_rng(0)
    src = (rng.random((30, 30)) < 0.4).astype(float)
    D = gm.dermal_signal(src, 0.05, 0.0, 2.0, 4.0)
    assert np.array_equal(D, 0.5 * src)


@pytest.mark.parametrize("bad", [
    dict(lambda_D=-0.1), dict(p_D=-1.0), dict(mu_D=0.0),
])
def test_dermal_signal_refuses_bad_inputs(bad):
    args = dict(lambda_D=0.3, p_D=1.0, mu_D=1.0)
    args.update(bad)
    with pytest.raises(ValueError):
        gm.dermal_signal(np.ones((10, 10)), 0.05, args["lambda_D"], args["p_D"], args["mu_D"])


def test_dermal_signal_conserves_mass_with_reflecting_boundaries():
    """Summing the equation over a zero-flux field cancels the Laplacian, so
    sum(D) = (p_D / mu_D) * sum(source) exactly."""
    rng = np.random.default_rng(1)
    src = np.zeros((80, 80))
    src[20:60, 25:55] = rng.random((40, 30)) < 0.5
    D = gm.dermal_signal(src, 0.06, 0.4, 3.0, 2.0)
    assert D.sum() == pytest.approx(1.5 * src.sum(), rel=SOLVER_REL)
    assert np.all(D >= -SOLVER_REL * D.max())


@pytest.mark.parametrize("lam", [0.2, 0.5])
def test_dermal_signal_matches_the_straight_edge_closed_form(lam):
    """Source c = 1 for x < x0 across the whole field (a straight edge). The
    continuous solution is D = 1 - exp(-(x0-x)/lam)/2 inside, exp(-(x-x0)/lam)/2
    outside. Grid spacing h = 0.05 keeps lam/h >= 4; the five-point operator's
    error in the decay rate is about (h/lam)^2/24 < 0.3%, so 1% of c on every
    column within 3 lam of the edge is a fair bound. The field is 10 mm wide so
    the reflecting walls (>= 5 mm = 10 lam away) contribute < 1e-4."""
    h, n = 0.05, 200
    src = np.zeros((8, n))
    src[:, : n // 2] = 1.0
    D = gm.dermal_signal(src, h, lam, 1.0, 1.0)
    x = h * (np.arange(n) + 0.5)
    x0 = h * (n // 2)
    want = np.where(x < x0, 1 - 0.5 * np.exp(-(x0 - x) / lam), 0.5 * np.exp(-(x - x0) / lam))
    near = np.abs(x - x0) <= 3 * lam
    for row in D:
        assert np.max(np.abs(row[near] - want[near])) <= 0.01


def test_dermal_signal_of_a_centred_disc_is_symmetric():
    g = gm.geometry(dict(gm.default_params("H2"), d_spot=3.0))
    src = g["spot_mask"].astype(float) * 0.5
    D = gm.dermal_signal(src, g["h_mm"], 0.3, 1.0, 1.0)
    tol = SOLVER_REL * D.max()
    assert np.allclose(D, D.T, rtol=0, atol=tol)
    assert np.allclose(D, D[::-1, :], rtol=0, atol=tol)
    assert np.allclose(D, D[:, ::-1], rtol=0, atol=tol)


def test_run_uses_dermal_signal_on_its_fibroblast_map():
    p = dict(gm.default_params("H2"), lambda_D=0.3)
    for fib in ("random", "uniform"):
        r = gm.run(p, days=3, mode="expected", fibroblasts=fib, fibroblast_seed=4)
        g = r["geometry"]
        want = gm.dermal_signal(r["fibroblast_map"], g["h_mm"], p["lambda_D"], p["p_D"], p["mu_D"])
        assert np.allclose(r["D_map"], want, rtol=EXACT_REL, atol=0)
        assert np.all(r["fibroblast_map"][~g["spot_mask"]] == 0)
    u = gm.run(p, days=3, mode="expected", fibroblasts="uniform")
    assert np.all(u["fibroblast_map"][u["geometry"]["spot_mask"]] == p["f_sen"])


def test_random_fibroblasts_are_bernoulli_and_shared_by_both_modes():
    """Share of senescent dermal sites inside the disc over 20 fibroblast seeds
    within 4 standard errors of f_sen (false failure ~1 in 15,000)."""
    p = gm.default_params("H2")
    shares = []
    for fs in range(20):
        a = gm.run(p, days=2, seed=0, mode="stochastic", fibroblast_seed=fs)
        b = gm.run(p, days=2, seed=9, mode="expected", fibroblast_seed=fs)
        assert np.array_equal(a["fibroblast_map"], b["fibroblast_map"])
        assert np.array_equal(a["D_map"], b["D_map"])
        m = a["geometry"]["spot_mask"]
        vals = a["fibroblast_map"][m]
        assert set(np.unique(vals)) <= {0.0, 1.0}
        shares.append(vals.mean())
    n = m.sum() * len(shares)
    se = math.sqrt(p["f_sen"] * (1 - p["f_sen"]) / n)
    assert abs(np.mean(shares) - p["f_sen"]) <= 4 * se


# ---------------------------------------- the well-mixed limit (space off)

@pytest.mark.parametrize("kind", ["healthy", "H1", "H2", "mixture"])
def test_without_space_the_grid_is_the_well_mixed_model(kind):
    """With no diffusion (lambda_D = 0), no division (k_div = 0) and uniform
    fibroblasts, every site is an independent copy of one well-mixed cell, so
    the spot's per-site fractions and melanin must equal spot_model's expected
    run of the same parameters, and the ring's must equal spot_model's healthy
    run. This pins the grid to the already-tested rules (M3, M4)."""
    p = local(gm.default_params(kind))
    days = TWO_YEARS
    g = gm.run(p, days=days, mode="expected", fibroblasts="uniform")
    w_spot = sm.run(wm_params(p), days=days, mode="expected")
    h = local(gm.default_params("healthy"))
    w_ring = sm.run(wm_params(h), days=days, mode="expected")
    n_wm = w_spot["active"][0]
    ns, nr = g["n_sites"]["spot"], g["n_sites"]["ring"]
    for k in ("active", "hypoactive", "senescent", "gone"):
        assert np.allclose(g["spot"][k] / ns, np.asarray(w_spot[k]) / n_wm, rtol=EXACT_REL, atol=1e-12)
        assert np.allclose(g["ring"][k] / nr, np.asarray(w_ring[k]) / n_wm, rtol=EXACT_REL, atol=1e-12)
    assert np.allclose(g["spot"]["melanin"], w_spot["melanin"], rtol=EXACT_REL, atol=0)
    assert np.allclose(g["ring"]["melanin"], w_ring["melanin"], rtol=EXACT_REL, atol=0)
    m = g["geometry"]["spot_mask"]
    assert np.allclose(g["D_map"][m], w_spot["D"][0], rtol=EXACT_REL, atol=0)
    assert np.all(g["D_map"][~m] == 0)


# --------------------------------------------- what H1 and H2 mean, in space

@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_h1_does_not_depend_on_fibroblasts_or_signal_reach(mode):
    """k_derm = 0: fibroblast state, production and reach change D only. In
    stochastic mode this also checks that fibroblast draws do not consume the
    melanocyte random stream."""
    base = gm.default_params("H1")
    runs = []
    for f_sen, p_D, lam in [(0.0, 0.0, 0.1), (0.4, 1.0, 0.3), (1.0, 50.0, 1.5)]:
        p = dict(base, f_sen=f_sen, p_D=p_D, lambda_D=lam)
        runs.append(gm.run(p, days=ONE_YEAR, seed=7, mode=mode, snapshot_days=(0, 200, ONE_YEAR)))
    assert same_result(runs[0], runs[1]) and same_result(runs[0], runs[2])


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_h2_without_its_dermal_patch_is_healthy_skin(mode):
    h = gm.default_params("healthy")
    p = dict(gm.default_params("H2"), f_sen=0.0)
    a = gm.run(p, days=ONE_YEAR, seed=3, mode=mode)
    b = gm.run(h, days=ONE_YEAR, seed=3, mode=mode)
    assert same_result(a, b)
    assert np.all(a["D_map"] == 0)


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_h1_without_its_intrinsic_defect_is_healthy_skin(mode):
    """The mirror of the test above, so neither explanation gets a free spot."""
    h = gm.default_params("healthy")
    p = dict(gm.default_params("H1"), **{k: h[k] for k in ("k_int", "a_int", "k_tr")})
    a = gm.run(p, days=ONE_YEAR, seed=3, mode=mode)
    b = gm.run(h, days=ONE_YEAR, seed=3, mode=mode)
    assert same_result(a, b)


def test_healthy_skin_is_uniform():
    r = gm.run(gm.default_params("healthy"), days=ONE_YEAR, mode="expected")
    for d, snap in r["snapshots"].items():
        for k in ("active", "melanin"):
            assert np.allclose(snap[k], snap[k].flat[0], rtol=EXACT_REL, atol=0)
    assert np.allclose(r["spot"]["melanin"], r["ring"]["melanin"], rtol=EXACT_REL, atol=0)


def test_h1_defect_stays_inside_its_patch_when_outside_cells_never_leave():
    """Under H1 the dermal term is off and healthy lineages have k_int = 0, so
    no cell outside the disc ever leaves 'active', whatever happens inside,
    including with division on (daughters only fill empty sites)."""
    p = h1_strong(k_div=0.02)
    r = gm.run(p, days=TWO_YEARS, seed=5, mode="stochastic", snapshot_days=(TWO_YEARS,))
    out = ~r["geometry"]["spot_mask"]
    snap = r["snapshots"][TWO_YEARS]
    assert np.all(snap["active"][out] == 1)
    assert r["ring"]["active"][-1] == r["n_sites"]["ring"]


# -------------------------------------------------- conservation and steps

@pytest.mark.parametrize("mode", ["stochastic", "expected"])
@pytest.mark.parametrize("kind", ["healthy", "H1", "H2", "mixture"])
def test_zero_loss_rates_freeze_every_site(kind, mode):
    p = dict(gm.default_params(kind), k_int=0.0, k_sen=0.0, k_loss=0.0, k_derm=0.0)
    r = gm.run(p, days=ONE_YEAR, seed=11, mode=mode, snapshot_days=(0, ONE_YEAR))
    for reg in ("spot", "ring"):
        assert np.all(r[reg]["active"] == r["n_sites"][reg])
        for k in ("hypoactive", "senescent", "empty", "gone"):
            assert np.all(r[reg][k] == 0)
    # The ring is healthy skin, so its melanin stays at the healthy steady
    # state. Inside the spot only if this kind's transfer rate is the healthy
    # one (a lower k_tr legitimately moves spot melanin with no cell lost).
    assert np.allclose(r["ring"]["melanin"], 1.0, rtol=EXACT_REL, atol=0)
    if p["k_tr"] == gm.default_params("healthy")["k_tr"]:
        assert np.allclose(r["spot"]["melanin"], 1.0, rtol=EXACT_REL, atol=0)


@pytest.mark.parametrize("kind", ["H1", "H2", "mixture"])
def test_expected_mode_probabilities_are_a_distribution_per_site(kind):
    p = dict(gm.default_params(kind), k_derm=gm.default_params(kind)["k_derm"] * 5)
    cap = p["tx_site_capacity"]
    r = gm.run(p, days=TWO_YEARS, mode="expected", transplant_days=(400,),
               snapshot_days=(0, 399, 400, TWO_YEARS))
    for snap in r["snapshots"].values():
        live = snap["active"] + snap["hypoactive"] + snap["senescent"]
        for k in ("active", "hypoactive", "senescent", "melanin", "transplanted"):
            assert np.all(snap[k] >= -1e-12)
        assert np.all(live <= cap + 1e-9)
        assert np.all(snap["transplanted"] <= live + 1e-9)
    # extra slots are for transplanted cells only: before the session no site
    # holds more than one cell
    pre = r["snapshots"][399]
    assert np.all(pre["active"] + pre["hypoactive"] + pre["senescent"] <= 1 + 1e-9)
    # Counts are cells over all slots; `empty` counts sites with no live cell.
    # Before the first transplant every site holds at most one cell, so cells
    # + empty sites == sites exactly. From the session on, extra slots can hold
    # donors, and the exact statement is the pair of bounds that one-or-more
    # and at-most-cap cells per occupied site give (they hold in expectation
    # too, by linearity): sites - empty <= cells <= cap * (sites - empty).
    # (Corrected 2026-11-28 after the capacity revision: the earlier version
    # asserted the single-occupancy identity on every day, which is false at
    # capacity 2 once donors fill extra slots.)
    t_tx = 400
    for reg in ("spot", "ring"):
        n = r["n_sites"][reg]
        cells = r[reg]["active"] + r[reg]["hypoactive"] + r[reg]["senescent"]
        occupied = n - np.asarray(r[reg]["empty"], dtype=float)
        assert np.allclose(cells[:t_tx] + r[reg]["empty"][:t_tx], n, rtol=EXACT_REL, atol=0)
        assert np.all(occupied >= -1e-9) and np.all(occupied <= n * (1 + EXACT_REL))
        assert np.all(cells >= occupied * (1 - EXACT_REL) - 1e-9)
        assert np.all(cells <= cap * occupied * (1 + EXACT_REL) + 1e-9)
        assert np.all(np.diff(r[reg]["gone"]) >= -1e-9)
    # The ring receives no transplant, so the identity holds there on every day.
    ring_cells = r["ring"]["active"] + r["ring"]["hypoactive"] + r["ring"]["senescent"]
    assert np.allclose(ring_cells + r["ring"]["empty"], r["n_sites"]["ring"], rtol=EXACT_REL, atol=0)


def test_region_series_agree_with_the_snapshots():
    p = h2_strong(lambda_D=0.3)
    days = 300
    for mode in ("stochastic", "expected"):
        r = gm.run(p, days=days, seed=2, mode=mode, snapshot_days=(0, 150, days))
        g = r["geometry"]
        for d, snap in r["snapshots"].items():
            for reg, mask in (("spot", g["spot_mask"]), ("ring", g["ring_mask"])):
                for k in ("active", "hypoactive", "senescent"):
                    assert snap[k][mask].sum() == pytest.approx(r[reg][k][d], rel=EXACT_REL, abs=1e-9)
                assert snap["melanin"][mask].mean() == pytest.approx(r[reg]["melanin"][d], rel=EXACT_REL)
                assert snap["transplanted"][mask].sum() == pytest.approx(
                    r[reg]["transplanted_alive"][d], rel=EXACT_REL, abs=1e-9)


def test_without_division_or_transplant_every_empty_site_was_a_loss():
    r = gm.run(h2_strong(k_div=0.0), days=TWO_YEARS, seed=1)
    for reg in ("spot", "ring"):
        assert np.array_equal(r[reg]["empty"], r[reg]["gone"])


def state_map(snap):
    """0 empty, 1 active, 2 hypoactive, 3 senescent (stochastic snapshot of a
    single-occupancy run, tx_site_capacity 1)."""
    a, h, s = (np.asarray(snap[k]).astype(int) for k in ("active", "hypoactive", "senescent"))
    assert np.all(a + h + s <= 1)            # one melanocyte per site
    return a * 1 + h * 2 + s * 3


def test_one_step_per_day_and_two_stage_loss_on_every_site():
    """R1, R2, V3 (PMID 7377803) per site: from one day to the next a site may
    go active->hypoactive, hypoactive->senescent, hypoactive->empty,
    senescent->empty, or empty->active (division or transplant). Nothing else:
    no active->empty, no active->senescent, nothing backwards. Fast rates and
    60 days keep 61 daily snapshots small while still giving every allowed
    transition many times. Single occupancy (capacity 1) so a site's state is
    one cell's state; the slot rules are the same for every slot."""
    p = h2_strong(lambda_D=0.2, k_derm=0.05, k_sen=0.02, k_loss=0.05, k_div=0.05,
                  d_spot=2.0, tx_site_capacity=1)
    days = 60
    r = gm.run(p, days=days, seed=4, transplant_days=(30,), snapshot_days=tuple(range(days + 1)))
    allowed = {(1, 1), (2, 2), (3, 3), (0, 0), (1, 2), (2, 3), (2, 0), (3, 0), (0, 1)}
    prev = state_map(r["snapshots"][0])
    for d in range(1, days + 1):
        cur = state_map(r["snapshots"][d])
        pairs = set(zip(prev.ravel().tolist(), cur.ravel().tolist()))
        assert pairs <= allowed, f"day {d}: forbidden transitions {pairs - allowed}"
        prev = cur


def test_division_only_fills_an_empty_site_next_to_an_active_cell():
    """R7: a site that was empty yesterday and is active today, on a day with
    no transplant, had at least one active 4-neighbour yesterday."""
    p = h1_strong(k_int=0.02, k_loss=0.05, k_div=0.05, d_spot=2.0)
    days = 60
    r = gm.run(p, days=days, seed=8, snapshot_days=tuple(range(days + 1)))
    n_born = 0
    for d in range(1, days + 1):
        prev = r["snapshots"][d - 1]
        a0 = np.asarray(prev["active"], dtype=float)
        live0 = a0 + np.asarray(prev["hypoactive"], dtype=float) + np.asarray(prev["senescent"], dtype=float)
        born = (live0 == 0) & (np.asarray(r["snapshots"][d]["active"], dtype=float) == 1)
        n_born += int(born.sum())
        nb = np.zeros_like(a0)
        nb[1:, :] += a0[:-1, :]
        nb[:-1, :] += a0[1:, :]
        nb[:, 1:] += a0[:, :-1]
        nb[:, :-1] += a0[:, 1:]
        assert np.all(nb[born] >= 1)
    assert n_born > 0          # the test saw division happen


# ------------------------------------------------- rule directions, in space

@pytest.mark.parametrize("key,low,high", [
    ("k_derm", 0.002, 0.02), ("p_D", 0.5, 2.0), ("f_sen", 0.2, 0.8),
])
def test_stronger_dermal_signal_never_leaves_more_live_cells(key, low, high):
    """R4: k_derm * D only adds to forward rates. Uniform fibroblasts so the
    two runs differ only in `key`."""
    out = []
    for v in (low, high):
        p = h2_strong(lambda_D=0.3, **{key: v})
        r = gm.run(p, days=TWO_YEARS, mode="expected", fibroblasts="uniform")
        out.append(r["spot"]["active"] + r["spot"]["hypoactive"] + r["spot"]["senescent"])
    assert np.all(out[1] <= out[0] * (1 + EXACT_REL))
    assert out[1][-1] < out[0][-1]


def test_signal_reaches_beyond_the_patch_only_by_diffusion():
    """lambda_D = 0: no D, and so no H2 effect, outside the disc. lambda_D > 0:
    D outside the disc is positive near the edge and falls with distance."""
    p0 = h2_strong(lambda_D=0.0)
    r0 = gm.run(p0, days=2, mode="expected", fibroblasts="uniform")
    m = r0["geometry"]["spot_mask"]
    assert np.all(r0["D_map"][~m] == 0)
    p = h2_strong(lambda_D=0.4)
    r = gm.run(p, days=2, mode="expected", fibroblasts="uniform")
    g = r["geometry"]
    rr = site_r(g)
    R = p["d_spot"] / 2
    bands = [(R + a, R + a + g["h_mm"] * 2) for a in (0.05, 0.3, 0.6, 1.0)]
    means = [r["D_map"][(rr > lo) & (rr <= hi)].mean() for lo, hi in bands]
    assert means[0] > 0
    assert all(x > y for x, y in zip(means, means[1:]))


# ------------------------------------------------------------ reproducibility

def test_same_seeds_same_output_bit_for_bit():
    p = dict(gm.default_params("mixture"), lambda_D=0.3)
    kw = dict(days=300, seed=42, fibroblast_seed=5, transplant_days=(100,),
              snapshot_days=(0, 99, 100, 300))
    a, b = gm.run(p, **kw), gm.run(p, **kw)
    assert same_result(a, b)
    assert np.array_equal(a["D_map"], b["D_map"])
    assert np.array_equal(a["fibroblast_map"], b["fibroblast_map"])
    assert a["transplant_overflow"] == b["transplant_overflow"]
    assert np.array_equal(a["days_since_final_treatment"], b["days_since_final_treatment"], equal_nan=True)


def test_different_seeds_differ():
    p = h2_strong(lambda_D=0.3)
    a = gm.run(p, days=300, seed=1, fibroblast_seed=0)
    b = gm.run(p, days=300, seed=2, fibroblast_seed=0)
    assert np.array_equal(a["fibroblast_map"], b["fibroblast_map"])
    assert not same_result(a, b, ("active", "hypoactive", "senescent"))
    c = gm.run(p, days=300, seed=1, fibroblast_seed=1)
    assert not np.array_equal(a["fibroblast_map"], c["fibroblast_map"])


def test_fibroblast_seed_defaults_to_seed():
    p = gm.default_params("H2")
    a = gm.run(p, days=2, seed=6)
    b = gm.run(p, days=2, seed=6, fibroblast_seed=6)
    assert np.array_equal(a["fibroblast_map"], b["fibroblast_map"])


def test_stochastic_mean_matches_expected_for_a_fixed_fibroblast_map():
    """With k_div = 0 sites are independent given the fibroblast map, so the
    expected mode is the exact mean of the stochastic mode. Mean over 30
    melanocyte seeds (same fibroblast_seed) within 4 standard errors of the
    expected spot counts at one year, per state (false failure ~1 in 15,000
    per comparison; a real mismatch of 2% of the spot's sites fails it)."""
    p = h2_strong(lambda_D=0.25, k_div=0.0)
    exp = gm.run(p, days=ONE_YEAR, mode="expected", fibroblast_seed=3)
    draws = {k: [] for k in ("active", "hypoactive", "senescent")}
    for seed in range(30):
        r = gm.run(p, days=ONE_YEAR, seed=seed, fibroblast_seed=3)
        for k in draws:
            draws[k].append(r["spot"][k][-1])
    for k, xs in draws.items():
        x = np.asarray(xs, dtype=float)
        se = x.std(ddof=1) / math.sqrt(len(x))
        assert abs(x.mean() - exp["spot"][k][-1]) <= 4 * se + 1e-9


# ---------------------------------------------------------------- transplant

def test_single_occupancy_transplant_places_cells_only_on_empty_sites_inside_the_spot():
    p = h1_strong(k_div=0.0, d_spot=2.0, tx_site_capacity=1)
    t = 400
    r = gm.run(p, days=t + 5, seed=3, transplant_days=(t,), snapshot_days=(t - 1, t, t + 5))
    m = r["geometry"]["spot_mask"]
    for d in (t, t + 5):
        tr = np.asarray(r["snapshots"][d]["transplanted"])
        assert np.all(tr[~m] == 0)
    before, after = r["snapshots"][t - 1], r["snapshots"][t]
    # A site active yesterday is still occupied today (active cannot be lost
    # in one step), so it cannot have received a transplanted cell.
    assert np.all(np.asarray(after["transplanted"])[np.asarray(before["active"]) == 1] == 0)
    assert np.all(r["snapshots"][t - 1]["transplanted"] == 0)


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_transplant_survivors_are_placed_or_reported_as_overflow(mode):
    p = dict(h1_strong(k_div=0.0, d_spot=2.0), s_tx=1.0 if mode == "stochastic" else 0.5)
    t = 400
    r = gm.run(p, days=t, seed=3, mode=mode, transplant_days=(t,))
    delivered = round(p["N_tx"] * math.pi * p["d_spot"] ** 2 / 4)
    survivors = delivered * p["s_tx"]
    placed = r["spot"]["transplanted_alive"][t]
    assert placed + r["transplant_overflow"][0] == pytest.approx(survivors, rel=EXACT_REL)
    assert r["transplant_overflow"][0] >= 0
    assert r["ring"]["transplanted_alive"][t] == 0


@pytest.mark.parametrize("cap", [1, 2, 3])
@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_a_large_transplant_fills_every_slot_and_never_exceeds_capacity(mode, cap):
    """Capacity 1: density stops at normal skin. Capacity 2 or 3: a large
    transplant takes the spot above normal density (the mouse graft's
    388.75 vs 220 per mm2, PMID 2508572), up to cap x sites and no further."""
    p = dict(h1_strong(k_div=0.0, d_spot=2.0), N_tx=1e5, s_tx=1.0, tx_site_capacity=cap)
    t = 400
    r = gm.run(p, days=t + 30, seed=3, mode=mode, transplant_days=(t,), snapshot_days=(t,))
    ns = r["n_sites"]["spot"]
    assert r["spot"]["empty"][t] == pytest.approx(0, abs=1e-9)
    live = r["spot"]["active"] + r["spot"]["hypoactive"] + r["spot"]["senescent"]
    assert live[t] == pytest.approx(cap * ns, rel=EXACT_REL)
    assert np.all(live <= cap * ns * (1 + EXACT_REL))
    snap = r["snapshots"][t]
    assert np.all(snap["active"] + snap["hypoactive"] + snap["senescent"] <= cap + 1e-9)
    assert r["transplant_overflow"][0] > 0
    assert r["ring"]["transplanted_alive"][t] == 0


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_donors_without_loss_pressure_keep_their_cells(mode):
    """Plan 6, in space. Donors carry healthy-skin rates (tx_rates 1, k_int_tx
    0) and there is no dermal term (H1, k_derm 0) and no division, so after the
    final session no donor cell can ever leave 'active'. Ten years."""
    p = dict(h1_strong(k_div=0.0, d_spot=2.0), tx_rates=1)
    sessions = (300, 330)
    r = gm.run(p, days=3650, seed=9, mode=mode, transplant_days=sessions)
    alive = np.asarray(r["spot"]["transplanted_alive"])
    assert np.all(alive[: sessions[0]] == 0)
    after = alive[sessions[-1]:]
    assert after[0] > 0 and np.allclose(after, after[0], rtol=EXACT_REL, atol=0)


def no_loss_grid(params):
    return dict(params, k_int=0.0, k_sen=0.0, k_loss=0.0, k_derm=0.0, k_div=0.0)


def overflow_is_zero(res):
    return all(abs(x) <= 1e-9 for x in res["transplant_overflow"])


@pytest.mark.parametrize("cap", [2, 3])
def test_above_normal_transplant_matches_the_well_mixed_model(cap):
    """The reason for extra slots: with free capacity for every survivor, the
    grid places exactly the cells the well-mixed model adds, including above
    normal density, so the two models agree on how many donor cells there are.
    No loss pressure and no division, expected mode, ten years: transplanted
    cells equal, overflow 0, and melanin (supply summed over active cells) in
    the spot settles darker than the ring at (sites + donors) / sites. 1e-6 on
    melanin: after ten years the T_K = 28 day transient is gone (e^-130)."""
    p = no_loss_grid(dict(gm.default_params("healthy"), N_tx=110.0, s_tx=0.5,
                          tx_site_capacity=cap))
    sessions = (30, 60)
    g = gm.run(p, days=3650, mode="expected", transplant_days=sessions)
    w = sm.run(wm_params(p), days=3650, mode="expected", transplant_days=sessions)
    assert overflow_is_zero(g)
    assert np.allclose(g["spot"]["transplanted_alive"], w["transplanted_alive"], rtol=EXACT_REL, atol=1e-9)
    ns = g["n_sites"]["spot"]
    donors = g["spot"]["transplanted_alive"][-1]
    assert donors > 0
    assert g["spot"]["melanin"][-1] == pytest.approx((ns + donors) / ns, rel=1e-6)
    assert g["ring"]["melanin"][-1] == pytest.approx(1.0, rel=EXACT_REL)


def test_single_occupancy_is_the_alternative_with_overflow():
    """The alternative considered (capacity 1): into skin with no free site,
    every survivor overflows and nothing is placed."""
    p = no_loss_grid(dict(gm.default_params("healthy"), tx_site_capacity=1))
    r = gm.run(p, days=100, mode="expected", transplant_days=(50,))
    survivors = round(p["N_tx"] * math.pi * p["d_spot"] ** 2 / 4) * p["s_tx"]
    assert np.all(r["spot"]["transplanted_alive"] == 0)
    assert r["transplant_overflow"][0] == pytest.approx(survivors, rel=EXACT_REL)


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_extra_slots_are_never_used_without_a_transplant(mode):
    """Division only fills gaps (R7): without a transplant no site ever holds
    more than one cell, at any capacity."""
    p = dict(h1_strong(k_div=0.05, d_spot=2.0), tx_site_capacity=3)
    r = gm.run(p, days=400, seed=2, mode=mode, snapshot_days=(100, 400))
    for snap in r["snapshots"].values():
        assert np.all(snap["active"] + snap["hypoactive"] + snap["senescent"] <= 1 + 1e-9)
    live = r["spot"]["active"] + r["spot"]["hypoactive"] + r["spot"]["senescent"]
    assert np.all(live <= r["n_sites"]["spot"] * (1 + EXACT_REL))


def test_capacity_does_nothing_without_a_transplant():
    p = h2_strong(lambda_D=0.3)
    kw = dict(days=400, seed=5, mode="stochastic")
    a = gm.run(dict(p, tx_site_capacity=1), **kw)
    b = gm.run(dict(p, tx_site_capacity=3), **kw)
    assert same_result(a, b)


def test_tx_rates_0_ignores_donor_rates():
    p = h2_strong(lambda_D=0.3, tx_rates=0)
    kw = dict(days=500, mode="expected", transplant_days=(300,), snapshot_days=(500,))
    a = gm.run(p, **kw)
    b = gm.run(dict(p, k_int_tx=0.01, a_int_tx=2.0, k_tr_tx=0.3), **kw)
    assert same_result(a, b)


def test_tx_setting_does_not_change_resident_cells():
    """Under H1 with no division, resident cells are untouched by what donor
    cells do: resident counts = totals minus transplanted, equal across
    settings."""
    p = h1_strong(k_div=0.0)
    kw = dict(days=600, mode="expected", transplant_days=(300,))
    a = gm.run(dict(p, tx_rates=0), **kw)
    b = gm.run(dict(p, tx_rates=1), **kw)
    for res in (a, b):
        res["_resident"] = (res["spot"]["active"] + res["spot"]["hypoactive"]
                            + res["spot"]["senescent"] - res["spot"]["transplanted_alive"])
    assert np.allclose(a["_resident"], b["_resident"], rtol=EXACT_REL, atol=1e-9)


def test_zero_survival_transplant_adds_nothing():
    p = dict(h1_strong(), s_tx=0.0)
    r = gm.run(p, days=400, seed=6, transplant_days=(50,))
    assert np.all(r["spot"]["transplanted_alive"] == 0)
    assert r["transplant_overflow"] == [0]


def test_follow_up_is_counted_from_the_final_treatment():
    """CLAUDE.md rule 2."""
    r = gm.run(gm.default_params("H1"), days=400, transplant_days=(30, 60))
    f = np.asarray(r["days_since_final_treatment"], dtype=float)
    assert np.all(np.isnan(f[:60]))
    assert f[60] == 0 and f[240] == 180 and f[400] == 340
    none = gm.run(gm.default_params("H1"), days=50)
    assert np.all(np.isnan(np.asarray(none["days_since_final_treatment"], dtype=float)))


# -------------------------------------------------- rendering and measurement

def test_render_is_drift_sim_field_and_maps_melanin_to_L_per_site():
    """No blur, no noise: each pixel's L* is melanin_to_L of the site under its
    centre, and its a*, b* are those of drift_sim.SKIN_RGB. 1e-6 L* is far
    below anything measurable and above round-trip rounding (~1e-12)."""
    assert gm.melanin_to_L is sm.melanin_to_L
    p = h2_strong(lambda_D=0.3, d_spot=3.0)
    r = gm.run(p, days=TWO_YEARS, seed=1, snapshot_days=(TWO_YEARS,))
    img = gm.render(r, TWO_YEARS, blur_sd_mm=0.0, noise_sd=0.0)
    n_px = ds.field_size(p["d_spot"], gm.PX_PER_MM)
    assert img.shape == (n_px, n_px, 3)
    lab = ds.rgb_to_lab(img)
    g = r["geometry"]
    c = (np.arange(n_px) + 0.5) / gm.PX_PER_MM
    idx = np.minimum((c / g["h_mm"]).astype(int), g["n_side"] - 1)
    site_m = np.asarray(r["snapshots"][TWO_YEARS]["melanin"])[np.ix_(idx, idx)]
    want_L = np.asarray(sm.melanin_to_L(site_m), dtype=float)
    assert np.max(np.abs(lab[..., 0] - want_L)) <= 1e-6
    skin = ds.rgb_to_lab(np.asarray(ds.SKIN_RGB, dtype=float)[None, None, :])[0, 0]
    assert np.max(np.abs(lab[..., 1] - skin[1])) <= 1e-6
    assert np.max(np.abs(lab[..., 2] - skin[2])) <= 1e-6


def test_render_refuses_a_day_without_a_snapshot():
    r = gm.run(gm.default_params("H1"), days=20, snapshot_days=(0, 20))
    with pytest.raises(ValueError):
        gm.render(r, 10)


def test_blur_preserves_the_mean_colour():
    p = h2_strong(lambda_D=0.3)
    r = gm.run(p, days=400, seed=1, snapshot_days=(400,))
    a = gm.render(r, 400, blur_sd_mm=0.0)
    b = gm.render(r, 400, blur_sd_mm=0.1)
    assert np.allclose(a.mean(axis=(0, 1)), b.mean(axis=(0, 1)), rtol=1e-9, atol=0)
    assert not np.array_equal(a, b)


def test_measure_is_drift_sims_measurement():
    p = h2_strong(lambda_D=0.3)
    r = gm.run(p, days=400, seed=1, snapshot_days=(400,))
    img = gm.render(r, 400)
    want = ds.measure_contrast(img, p["d_spot"], gm.PX_PER_MM)["L"]
    assert gm.measure_dL(img, p["d_spot"]) == pytest.approx(want, rel=1e-12, abs=1e-12)


def test_skin_equal_to_the_surround_measures_zero_within_noise():
    """Plan 6: a melanin map equal to the surrounding skin gives dL* within
    noise of zero with the ring geometry. Noise 0: exactly 0 (1e-9). Capture
    noise at drift_sim.NOISE_SD: each of 5 seeds within 0.2 L*. A check run
    while this test was written (drift_sim's own skin with contrast 0, 200
    noise seeds) gave an SD of 0.017 L* on a 2 mm spot and 0.012 L* on 3 mm,
    so 0.2 L* is over 10 SD for a correct renderer, and a fifth of the
    project's 1.0 L* target, so a renderer that leaks a real offset fails."""
    for d in (2.0, 3.0):
        r = gm.run(dict(gm.default_params("healthy"), d_spot=d), days=30, seed=2)
        assert abs(gm.measure_dL(gm.render(r, 30), d)) <= 1e-9
        for s in range(5):
            img = gm.render(r, 30, noise_sd=ds.NOISE_SD, seed=s)
            assert abs(gm.measure_dL(img, d)) <= 0.2


# --------------------------------------------------- the image statistics

@pytest.mark.parametrize("d", [2.0, 3.0, 5.0])
@pytest.mark.parametrize("sd", [0.1, 0.2, 0.3])
def test_edge_width_matches_the_blurred_step_closed_form(d, sd):
    """A sharp disc blurred by a Gaussian of SD s has a 10-90% width of
    2 * 1.2816 * s. drift_sim's white spot carries a one-pixel anti-aliasing
    ramp and L* is not linear in RGB; together they move the width by under
    0.02 mm in a check run while this test was written (s = 0.1 to 0.3, d = 2
    to 5). Tolerance: one profile bin, 0.05 mm. The midpoint must sit on the
    drawn edge within the same 0.05 mm."""
    img = ds.render(d, px_per_mm=gm.PX_PER_MM, blur_sd_mm=sd)
    assert gm.edge_width(img, d) == pytest.approx(2 * 1.281552 * sd, abs=0.05)
    assert gm.edge_midpoint(img, d) == pytest.approx(d / 2, abs=0.05)


def test_edge_width_refuses_a_spot_with_no_contrast():
    img = ds.render(3.0, contrast_scale=0.0)
    with pytest.raises(ZeroDivisionError):
        gm.edge_width(img, 3.0)


def synthetic_L_image(L_map):
    """Linear RGB with a given L* per pixel and skin's a*, b*, via the model's
    own renderer path is not available here, so build it by bisection on a grey
    scale factor of SKIN_RGB: L* depends on Y only, and Y scales with the
    factor. a*, b* then move slightly; skip_score and rim_centre_dL use L* only."""
    skin = np.asarray(ds.SKIN_RGB, dtype=float)
    lo = np.zeros_like(L_map)
    hi = np.full_like(L_map, 3.0)
    for _ in range(80):
        mid = (lo + hi) / 2
        L = ds.rgb_to_lab(mid[..., None] * skin)[..., 0]
        lo = np.where(L < L_map, mid, lo)
        hi = np.where(L < L_map, hi, mid)
    return ((lo + hi) / 2)[..., None] * skin


def test_skip_score_counts_darker_patches_in_the_inner_disc():
    d = 3.0
    n = ds.field_size(d, gm.PX_PER_MM)
    r = pixel_r(n)
    L = np.full((n, n), 70.0)
    assert gm.skip_score(synthetic_L_image(L), d) == 0
    inner = r <= 0.6 * d / 2
    c = (np.arange(n) + 0.5) / gm.PX_PER_MM - n / gm.PX_PER_MM / 2
    X, Y = np.meshgrid(c, c)
    quarter = inner & (X > 0) & (Y > 0)
    L2 = L.copy()
    L2[quarter] = 65.0                       # 5 L* darker than the rest
    want = quarter.sum() / inner.sum()
    assert gm.skip_score(synthetic_L_image(L2), d) == pytest.approx(want, abs=1e-9)
    L3 = L.copy()
    L3[quarter] = 69.5                       # darker by less than SKIP_DL
    assert gm.skip_score(synthetic_L_image(L3), d) == 0


def test_rim_centre_contrast_sign_and_zero():
    d = 3.0
    n = ds.field_size(d, gm.PX_PER_MM)
    r = pixel_r(n)
    R = d / 2
    flat = np.full((n, n), 70.0)
    assert gm.rim_centre_dL(synthetic_L_image(flat), d) == pytest.approx(0, abs=1e-6)
    graded = np.where(r <= 0.3 * R, 74.0, np.where((r > 0.6 * R) & (r <= 0.85 * R), 68.0, 70.0))
    assert gm.rim_centre_dL(synthetic_L_image(graded), d) == pytest.approx(6.0, abs=1e-6)
    assert gm.rim_centre_dL(synthetic_L_image(-graded + 140), d) == pytest.approx(-6.0, abs=1e-6)


def test_uniform_rendered_skin_has_zero_pattern_scores():
    r = gm.run(gm.default_params("healthy"), days=30)
    img = gm.render(r, 30)
    d = gm.default_params("healthy")["d_spot"]
    assert gm.skip_score(img, d) == 0
    assert abs(gm.rim_centre_dL(img, d)) <= 1e-9


# ------------------------------------- the edge, under each explanation (P1)

def edge_of(params, days=TWO_YEARS):
    r = gm.run(params, days=days, mode="expected", fibroblasts="uniform", snapshot_days=(days,))
    img = gm.render(r, days)
    return gm.edge_width(img, params["d_spot"]), gm.edge_midpoint(img, params["d_spot"])


def test_h2_edge_widens_with_signal_reach():
    """Plan 6: 'Edge width under H2 grows with lambda_D'. A mechanism check,
    not a prediction about real spots: D's profile across a straight edge is a
    function of distance / lambda_D, and every later step is monotone in D, so
    the width must grow with lambda_D. d = 4 mm keeps the radius at least 4
    lambda_D; uniform fibroblasts and expected mode keep the profile smooth."""
    widths = [edge_of(h2_strong(lambda_D=lam, d_spot=4.0))[0] for lam in (0.1, 0.25, 0.5)]
    assert widths[0] < widths[1] < widths[2]


def test_h1_edge_ignores_signal_reach_and_spot_size():
    """Plan 6: '... and under H1 does not'. Under H1 the defect is a property
    of the cells inside the disc, so the reach of a dermal signal cannot move
    the edge at all (exact), and the edge is the disc's own edge seen through
    the blur, the same for every spot size: within 0.1 mm (two profile bins,
    allowing for the lattice's jagged disc boundary differing between sizes)
    of the 2 mm spot's width, with its midpoint within 0.1 mm of d/2."""
    base = h1_strong()
    w = {lam: edge_of(dict(base, lambda_D=lam))[0] for lam in (0.1, 0.5, 1.5)}
    assert w[0.1] == w[0.5] == w[1.5]
    sizes = {}
    for d in (2.0, 3.0, 4.0, 5.0):
        width, mid = edge_of(dict(base, d_spot=d))
        sizes[d] = width
        assert mid == pytest.approx(d / 2, abs=0.1)
    assert max(sizes.values()) - min(sizes.values()) <= 0.1


# ------------------------------------------------------- the six-month readout

def test_six_month_readout_uses_the_measured_image_and_the_final_session():
    p = h2_strong(lambda_D=0.3)
    sessions = (400, 430)
    snaps = (sessions[0] - 1, sessions[-1] + 180)
    r = gm.run(p, days=700, mode="expected", transplant_days=sessions, snapshot_days=snaps)
    out = gm.six_month_readout(r)
    assert set(out) == {"baseline_dL", "dL_at_6_months", "rho_at_6_months",
                        "day_of_final_treatment", "day_of_readout"}
    assert out["day_of_final_treatment"] == sessions[-1]
    assert out["day_of_readout"] == sessions[-1] + 180
    d = p["d_spot"]
    assert out["baseline_dL"] == pytest.approx(gm.measure_dL(gm.render(r, snaps[0]), d), rel=EXACT_REL)
    assert out["dL_at_6_months"] == pytest.approx(gm.measure_dL(gm.render(r, snaps[1]), d), rel=EXACT_REL)
    assert out["rho_at_6_months"] == pytest.approx(out["dL_at_6_months"] / out["baseline_dL"], rel=EXACT_REL)


def test_six_month_readout_is_never_extrapolated_or_interpolated():
    p = h2_strong()
    short = gm.run(p, days=500, mode="expected", transplant_days=(400,), snapshot_days=(399, 500))
    with pytest.raises(ValueError):
        gm.six_month_readout(short)                  # needs day 580
    missing = gm.run(p, days=700, mode="expected", transplant_days=(400,), snapshot_days=(399, 600))
    with pytest.raises(ValueError):
        gm.six_month_readout(missing)                # no snapshot on day 580
    untreated = gm.run(p, days=700, mode="expected", snapshot_days=(399, 580))
    with pytest.raises(ValueError):
        gm.six_month_readout(untreated)              # no treatment, no readout


def test_six_month_readout_refuses_zero_baseline():
    r = gm.run(gm.default_params("healthy"), days=300, mode="expected",
               transplant_days=(100,), snapshot_days=(99, 280))
    with pytest.raises(ZeroDivisionError):
        gm.six_month_readout(r)


# ----------------------------------------- what the output is allowed to claim

@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_every_run_is_labelled_level_0_hypothesis_with_its_assumptions(mode):
    r = gm.run(gm.default_params("H2"), days=10, seed=13, mode=mode, fibroblast_seed=2)
    meta = r["meta"]
    assert meta["claim_level"] == 0
    assert meta["output_is"] == "hypothesis"
    assert meta["mode"] == mode and meta["seed"] == 13 and meta["fibroblast_seed"] == 2
    assert meta["fibroblasts"] == "random"
    status = {row["symbol"]: row["status"] for row in register_rows()}
    want = sorted(s for s in gm.PARAMS if status[s] == "ASSUMPTION")
    assert list(meta["assumptions"]) == want
    assert "lambda_D" in meta["assumptions"] and "n_M_ring" not in meta["assumptions"]
    assert set(meta["structural_assumptions"]) == STRUCTURAL


def test_running_the_model_never_touches_the_ledger():
    files = [ROOT / "data" / "evidence.csv", ROOT / "data" / "evidence_quotes.jsonl"]

    def digest():
        return [hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
                for f in files]

    before = digest()
    for kind in gm.KINDS:
        p = gm.default_params(kind)
        r = gm.run(p, days=200, transplant_days=(100,), snapshot_days=(99, 200))
        gm.measure_dL(gm.render(r, 200), p["d_spot"])
    assert digest() == before
