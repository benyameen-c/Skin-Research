"""Tests for the well-mixed spot model (Module 6, step M3), written before the code exists.

SIMULATION ONLY. Synthetic cell counts. No patient images. Nothing here, and
nothing the model produces, is evidence: no output enters data/evidence.csv.

Run:  python3 -m pytest experiments/tests -q

Until experiments/spot_model.py exists this whole file is SKIPPED (reason
printed). It is not "passing". The builder's done-when check (plan section 6,
M4) is:
    SPOT_MODEL_REQUIRED=1 python3 -m pytest experiments/tests/test_spot_model.py -q
which turns the skip into a hard failure and must show 0 skipped, 0 failed.
A spot_model.py that exists but fails to import is an error, never a skip.

SOURCE OF THIS CONTRACT: content/spot-model-plan.md sections 2.2, 2.3, 4.1,
6 (the minimum test list), 10.4 (claim levels); data/spot_model_params.csv
(the register). It holds the model to what plan section 1 says it may claim:
"If explanation A is true and these assumptions hold, the model predicts X".
It deliberately does NOT test which explanation fits better, or whether a
transplant fades or holds under H1 or H2. Those are the model's outputs; a
test that fixed them would build the answer in.

The builder writes experiments/spot_model.py to this contract and may not
change this file (git diff --exit-code <tests commit> -- experiments/tests).

Out of scope here, deferred to M5 (grid version): edge width and its scaling
with lambda_D, skip-area pattern, image rendering and the ring geometry of the
measurement plan. The well-mixed model has no space.

------------------------------------------------------------------------------
CONTRACT

Module constants
  PARAMS         tuple of str, the parameter symbols run() accepts. Every one is
                 a `symbol` in data/spot_model_params.csv. Must include
                 REQUIRED_PARAMS below. No symbol names a gene, vector or edit.
  KINDS          ("healthy", "H1", "H2", "mixture")
  INTERVENTIONS  ("transplant",)   the only intervention (plan 2.4).
  STATES         ("active", "hypoactive", "senescent")   live melanocyte states;
                 lost cells are counted cumulatively as "gone" (plan 2.2).

default_params(kind) -> new dict {symbol: float} with keys == set(PARAMS).
  * n_M_ring == 220 (QUOTED, PMID 2508572); 2 <= d_spot <= 5 (QUOTED, PMID 3805391).
  * "healthy" is the surrounding skin: f_sen == 0.
  * "H1": differs from "healthy" only in k_int, a_int, k_tr, k_derm; k_derm == 0;
          at least one of k_int, a_int, k_tr differs (plan 4.1: k_derm = 0,
          R1 to R3 do the work).
  * "H2": differs from "healthy" only in f_sen, k_derm, p_D, mu_D; f_sen > 0,
          k_derm > 0, p_D > 0, mu_D > 0 (plan 4.1: k_int at its healthy value,
          R4 and R5 do the work).
  * "mixture": f_sen > 0, k_derm > 0, p_D > 0, and at least one of k_int,
          a_int, k_tr differs from "healthy".
  * unknown kind -> ValueError.

run(params, *, days, seed=0, mode="stochastic" | "expected", transplant_days=())
  -> dict. Simulates ONE patch of skin of diameter d_spot (area pi*d_spot**2/4
  mm2) as counts, one row per day 0..days. Spot and surrounding ring are two
  separate runs (spot params, "healthy" params).
  Refusals (ValueError): a key not in PARAMS (the model never loads a parameter
  that is not in the register); a missing key (no silent defaults); any
  negative rate or count; f_sen or s_tx outside [0, 1]; d_spot <= 0; T_K <= 0;
  days < 1; unknown mode; transplant_days not strictly increasing ints in
  [1, days].
  Day 0: every melanocyte active, count N0 = round(n_M_ring * area); keratinocyte
  melanin at the healthy steady state for N0 active cells.
  Each day, every cell moves at most ONE step along
      active -> hypoactive -> senescent -> gone,  and also  hypoactive -> gone.
  Never backwards, never active -> gone directly (R1, R2; two-stage loss,
  PMID 7377803). A transition with rate r per day has probability
  1 - exp(-r) per day. With a_int == 0 and no dermal signal, active -> hypoactive
  has rate k_int exactly. The age effect MULTIPLIES k_int (factor 1 at age 0,
  non-decreasing in age, larger a_int never lowers it), so k_int == 0 means no
  intrinsic loss at any age.
  Dermal signal D = p_D * f_sen / mu_D (well-mixed steady state of R5) when
  p_D > 0 and f_sen > 0, else exactly 0; k_derm * D is added only to forward
  transition rates, never lowers one (R4). k_div refills only below N0 (R7: fills gaps).
  Only active cells supply melanin (hypoactive: "little or no pigment"), at
  relative rate k_tr; melanin renews with time scale T_K (R8).
  No rule sets the live count to zero (R10); zero can only arise from dynamics.
  Transplant (R9): on each listed day, round(N_tx * area) cells are delivered,
  of which Binomial(that, s_tx) (stochastic) or that * s_tx (expected) join as
  active, age 0, before that day's row is recorded.
  "stochastic": integer counts, reproducible bit for bit from seed.
  "expected": the mean-field version of the same rules, floats.
  Returned keys (arrays have length days + 1):
    day                         0..days
    active, hypoactive, senescent, gone (cumulative)
    melanin                     keratinocyte melanin, relative, >= 0
    D                           dermal signal
    transplanted_alive          live cells that arrived by transplant
    days_since_final_treatment  NaN before the final transplant day, else
                                day - final transplant day (CLAUDE.md rule 2:
                                follow-up from the FINAL treatment)
    meta  {"claim_level": 0, "output_is": "hypothesis", "mode": mode,
           "seed": seed, "assumptions": sorted list of the PARAMS whose register
           status is ASSUMPTION}   (plan 10.4: everything here is level 0)

melanin_to_L(m) -> L*: strictly decreasing in m >= 0, within [0, 100].
lightness_contrast(spot, ring) -> array dL*(day) = L*(spot melanin) - L*(ring
  melanin). ValueError if the two runs have different days.
residual_contrast(base_dL, follow_dL) -> follow_dL / base_dL;
  ZeroDivisionError when |base_dL| < 1e-6 (refused, never divided by).
six_month_readout(spot, ring) -> dict with EXACTLY the keys
  {"baseline_dL", "dL_at_6_months", "rho_at_6_months",
   "day_of_final_treatment", "day_of_readout"}.
  baseline = dL* on the day before the FIRST transplant; readout day = final
  transplant day + 180. ValueError if the spot run had no transplant or ends
  before the readout day (never extrapolated). ZeroDivisionError on a zero
  baseline. It reports a number, not a verdict: whether that number is a
  "lasting match" needs the measurement tool's SDC and Ben's T_match
  (measurement-tool-plan 2.3), which the model does not have.
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

if os.environ.get("SPOT_MODEL_REQUIRED") == "1":
    import spot_model as sm  # noqa: E402  hard failure if missing
else:
    sm = pytest.importorskip(
        "spot_model",
        reason="experiments/spot_model.py not written yet (plan step M4); "
               "tests precede the implementation",
        exc_type=ModuleNotFoundError,
    )

REGISTER = ROOT / "data" / "spot_model_params.csv"

REQUIRED_PARAMS = {
    "k_int", "a_int", "k_sen", "k_loss", "k_div", "k_tr", "T_K",
    "f_sen", "p_D", "mu_D", "k_derm", "N_tx", "s_tx", "n_M_ring", "d_spot",
}
COUNT_KEYS = ("active", "hypoactive", "senescent", "gone")
ARRAY_KEYS = COUNT_KEYS + ("melanin", "D", "transplanted_alive")

# Run lengths. Plan 2.1: "run to at least 2 years". 20 years is used where the
# plan's "years, not weeks" formation rule must be visible.
TWO_YEARS = 730
TWENTY_YEARS = 7300

# Floating-point tolerance for quantities that are exact in the contract
# (closed forms in "expected" mode, constants that must not move). 1e-9
# relative is far above double rounding over 7300 steps (~1e-12) and far below
# any modelled effect.
EXACT_REL = 1e-9


def register_rows():
    with open(REGISTER, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def live(res):
    return res["active"] + res["hypoactive"] + res["senescent"]


def area(params):
    return math.pi * params["d_spot"] ** 2 / 4


def n0(params):
    return round(params["n_M_ring"] * area(params))


def no_loss(params):
    p = dict(params)
    p.update(k_int=0.0, k_sen=0.0, k_loss=0.0, k_derm=0.0)
    return p


def same_run(a, b, keys=ARRAY_KEYS):
    return all(np.array_equal(a[k], b[k]) for k in keys)


# ---------------------------------------------------------------- the register

def test_every_param_is_in_the_register():
    symbols = {r["symbol"] for r in register_rows()}
    missing = set(sm.PARAMS) - symbols
    assert not missing, f"parameters not in data/spot_model_params.csv: {missing}"
    assert REQUIRED_PARAMS <= set(sm.PARAMS)


def test_unknown_parameter_is_refused():
    p = sm.default_params("healthy")
    p["k_unregistered"] = 0.1
    with pytest.raises(ValueError):
        sm.run(p, days=10)


def test_missing_parameter_is_refused():
    p = sm.default_params("healthy")
    del p["k_int"]
    with pytest.raises(ValueError):
        sm.run(p, days=10)


@pytest.mark.parametrize("key,value", [
    ("k_int", -1e-4), ("k_sen", -1e-4), ("k_loss", -1e-4), ("k_derm", -0.1),
    ("k_div", -1e-4), ("p_D", -1.0), ("mu_D", -1.0), ("N_tx", -1.0),
    ("f_sen", 1.5), ("s_tx", 1.5), ("s_tx", -0.1), ("d_spot", 0.0), ("T_K", 0.0),
])
def test_out_of_range_values_are_refused(key, value):
    p = sm.default_params("healthy")
    p[key] = value
    with pytest.raises(ValueError):
        sm.run(p, days=10)


def test_quoted_defaults_match_their_quotes():
    for kind in sm.KINDS:
        p = sm.default_params(kind)
        assert set(p) == set(sm.PARAMS)
        assert all(math.isfinite(float(v)) for v in p.values())
        assert p["n_M_ring"] == 220          # "220 +/- 28.28 mm2", PMID 2508572
        assert 2 <= p["d_spot"] <= 5          # "2- to 5-mm", PMID 3805391
    with pytest.raises(ValueError):
        sm.default_params("H3")


def test_default_params_returns_a_fresh_copy():
    a = sm.default_params("H1")
    a["k_int"] = 999.0
    assert sm.default_params("H1")["k_int"] != 999.0


# --------------------------------------------------- what H1 and H2 mean (4.1)

def changed_keys(kind):
    h, p = sm.default_params("healthy"), sm.default_params(kind)
    return {k for k in p if p[k] != h[k]}


def test_healthy_skin_has_no_senescent_fibroblasts():
    assert sm.default_params("healthy")["f_sen"] == 0


def test_h1_is_intrinsic_only():
    ch = changed_keys("H1")
    assert ch <= {"k_int", "a_int", "k_tr", "k_derm"}
    assert ch & {"k_int", "a_int", "k_tr"}
    assert sm.default_params("H1")["k_derm"] == 0


def test_h2_is_dermal_only():
    ch = changed_keys("H2")
    assert ch <= {"f_sen", "k_derm", "p_D", "mu_D"}
    p = sm.default_params("H2")
    assert p["f_sen"] > 0 and p["k_derm"] > 0 and p["p_D"] > 0 and p["mu_D"] > 0


def test_mixture_has_both():
    p, h = sm.default_params("mixture"), sm.default_params("healthy")
    assert p["f_sen"] > 0 and p["k_derm"] > 0 and p["p_D"] > 0
    assert any(p[k] != h[k] for k in ("k_int", "a_int", "k_tr"))


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_h1_does_not_depend_on_fibroblasts(mode):
    """Plan 6: with k_derm = 0, outputs do not depend on the fibroblast state."""
    base = sm.default_params("H1")
    runs = []
    for f_sen, p_D in [(0.0, 0.0), (0.3, 1.0), (1.0, 50.0)]:
        p = dict(base, f_sen=f_sen, p_D=p_D)
        runs.append(sm.run(p, days=TWO_YEARS, seed=7, mode=mode))
    keys = COUNT_KEYS + ("melanin",)   # D itself may differ; nothing it drives may
    assert same_run(runs[0], runs[1], keys) and same_run(runs[0], runs[2], keys)


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_h2_without_its_dermal_patch_is_healthy_skin(mode):
    """Plan 6: with k_int at baseline, an absent dermal patch gives no spot."""
    h = sm.default_params("healthy")
    p = dict(sm.default_params("H2"), f_sen=h["f_sen"])
    a = sm.run(p, days=TWO_YEARS, seed=3, mode=mode)
    b = sm.run(h, days=TWO_YEARS, seed=3, mode=mode)
    assert same_run(a, b, COUNT_KEYS + ("melanin",))
    assert np.all(a["D"] == 0)


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_h1_without_its_intrinsic_defect_is_healthy_skin(mode):
    """The mirror of the test above, so neither explanation gets a free spot."""
    h = sm.default_params("healthy")
    p = dict(sm.default_params("H1"))
    for k in ("k_int", "a_int", "k_tr"):
        p[k] = h[k]
    a = sm.run(p, days=TWO_YEARS, seed=3, mode=mode)
    b = sm.run(h, days=TWO_YEARS, seed=3, mode=mode)
    assert same_run(a, b, COUNT_KEYS + ("melanin",))


@pytest.mark.parametrize("kind", ["H1", "H2", "mixture"])
def test_each_explanation_can_make_a_spot_but_not_in_weeks(kind):
    """Both explanations must be able to produce a spot, or the comparison is
    empty. Plan 7.1: parameter sets that form spots in weeks are ruled out.
    Thresholds: 0.9 at day 30 allows a few percent loss in a month; the 20-year
    end only requires the spot to be lighter than the ring, not by how much
    (V1's ratio is a validation target for M7, not a contract here)."""
    spot = sm.run(sm.default_params(kind), days=TWENTY_YEARS, mode="expected")
    ring = sm.run(sm.default_params("healthy"), days=TWENTY_YEARS, mode="expected")
    ratio = live(spot) / live(ring)
    assert ratio[30] > 0.9
    assert ratio[-1] < 1
    assert sm.lightness_contrast(spot, ring)[-1] > 0


# ------------------------------------------------------ conservation and sign

@pytest.mark.parametrize("mode", ["stochastic", "expected"])
@pytest.mark.parametrize("kind", ["healthy", "H1", "H2", "mixture"])
def test_zero_loss_rates_freeze_the_counts(kind, mode):
    """Plan 6: with every loss rate zero, melanocyte counts never change. k_div
    stays at its default: division only fills gaps, and there are none."""
    p = no_loss(sm.default_params(kind))
    r = sm.run(p, days=TWO_YEARS, seed=11, mode=mode)
    assert np.all(r["active"] == n0(p))
    assert np.all(r["hypoactive"] == 0)
    assert np.all(r["senescent"] == 0)
    assert np.all(r["gone"] == 0)


def test_zero_loss_keeps_melanin_at_steady_state():
    p = no_loss(sm.default_params("healthy"))
    r = sm.run(p, days=TWO_YEARS, mode="expected")
    assert np.allclose(r["melanin"], r["melanin"][0], rtol=EXACT_REL, atol=0)


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
@pytest.mark.parametrize("kind", ["healthy", "H1", "H2", "mixture"])
def test_counts_never_negative_and_shapes(kind, mode):
    r = sm.run(sm.default_params(kind), days=TWO_YEARS, seed=5, mode=mode)
    assert np.array_equal(r["day"], np.arange(TWO_YEARS + 1))
    for k in ARRAY_KEYS:
        assert len(r[k]) == TWO_YEARS + 1, k
        assert np.all(np.asarray(r[k]) >= 0), k
    assert np.all(np.diff(r["gone"]) >= 0)          # cumulative
    if mode == "stochastic":
        for k in COUNT_KEYS + ("transplanted_alive",):
            assert np.issubdtype(np.asarray(r[k]).dtype, np.integer), k


@pytest.mark.parametrize("kind", ["H1", "H2", "mixture"])
def test_live_melanocytes_never_reach_zero_in_base_runs(kind):
    """R10 and V2 ("In no case were melanocytes completely absent", PMID 6183861):
    no rule zeroes the count, and base runs keep it above zero."""
    r = sm.run(sm.default_params(kind), days=TWENTY_YEARS, seed=1)
    assert np.all(live(r) > 0)


def test_live_count_never_exceeds_capacity_without_transplant():
    p = dict(sm.default_params("H1"))
    p["k_div"] = max(p["k_div"], 0.05)   # fast refilling, still capped at N0
    r = sm.run(p, days=TWO_YEARS, seed=2)
    assert np.all(live(r) <= n0(p))


@pytest.mark.parametrize("kind", ["H1", "H2", "mixture"])
def test_one_step_per_day_and_no_direct_active_loss(kind):
    """R2 / V3 two-stage loss (PMID 7377803): a cell lost on day t was
    hypoactive or senescent on day t-1, so hypoactive cells appear before any
    cell is lost."""
    p = dict(sm.default_params(kind), k_div=0.0)
    r = sm.run(p, days=TWENTY_YEARS, seed=4)
    lost_today = np.diff(r["gone"])
    impaired_yesterday = (r["hypoactive"] + r["senescent"])[:-1]
    assert np.all(lost_today <= impaired_yesterday)
    if r["gone"][-1] > 0:
        first_impaired = np.argmax(r["hypoactive"] + r["senescent"] > 0)
        first_lost = np.argmax(r["gone"] > 0)
        assert first_lost > first_impaired


# --------------------------------------------------- closed form and agreement

def simple_decay_params(k_int):
    p = sm.default_params("healthy")
    p.update(k_int=k_int, a_int=0.0, k_sen=0.0, k_loss=0.0, k_derm=0.0,
             k_div=0.0, f_sen=0.0)
    return p


def test_expected_mode_matches_closed_form():
    """Only active -> hypoactive at constant rate k: active(t) = N0 exp(-k t)."""
    k = 0.002
    p = simple_decay_params(k)
    r = sm.run(p, days=TWO_YEARS, mode="expected")
    t = np.arange(TWO_YEARS + 1)
    want = n0(p) * np.exp(-k * t)
    assert np.allclose(r["active"], want, rtol=EXACT_REL, atol=0)
    assert np.allclose(r["active"] + r["hypoactive"], n0(p), rtol=EXACT_REL, atol=0)


def test_stochastic_mean_matches_expected():
    """Mean of 100 seeds within 4 standard errors of the expected-mode value at
    one year, for every state. 4 SE: a false failure about 1 in 15,000 per
    comparison; a real mismatch between the two modes of even 2% of N0 (~40
    cells, SE ~2 cells here) fails it."""
    p = sm.default_params("healthy")
    p.update(k_int=0.003, a_int=0.0, k_sen=0.01, k_loss=0.004, k_derm=0.0,
             k_div=0.0, f_sen=0.0)
    days = 365
    exp = sm.run(p, days=days, mode="expected")
    draws = {k: [] for k in COUNT_KEYS}
    for seed in range(100):
        r = sm.run(p, days=days, seed=seed)
        for k in COUNT_KEYS:
            draws[k].append(r[k][-1])
    for k in COUNT_KEYS:
        x = np.asarray(draws[k], dtype=float)
        se = max(x.std(ddof=1) / math.sqrt(len(x)), 0.5)
        assert abs(x.mean() - exp[k][-1]) <= 4 * se, k


# ------------------------------------------------ direction of each rule (2.3)

@pytest.mark.parametrize("key,low,high", [
    ("k_int", 1e-4, 1e-3),     # R1
    ("a_int", 0.0, 1.0),       # R1: rate rises with age
    ("k_sen", 1e-4, 1e-2),     # R2
    ("k_loss", 1e-4, 1e-2),    # R2
])
def test_faster_intrinsic_rates_never_leave_more_pigment_cells(key, low, high):
    # k_div = 0: with refilling on, more loss can mean more new active cells,
    # so the direction of a single rule is only clean without it.
    base = dict(sm.default_params("mixture"), k_div=0.0)
    a = sm.run(dict(base, **{key: low}), days=TWENTY_YEARS, mode="expected")
    b = sm.run(dict(base, **{key: high}), days=TWENTY_YEARS, mode="expected")
    assert np.all(b["active"] <= a["active"] * (1 + EXACT_REL))
    assert np.all(live(b) <= live(a) * (1 + EXACT_REL))


@pytest.mark.parametrize("key,low,high", [
    ("k_derm", 0.0, 1.0),      # R4
    ("f_sen", 0.0, 1.0),       # R5
    ("p_D", 0.0, 10.0),        # R5
])
def test_stronger_dermal_signal_never_leaves_more_live_cells(key, low, high):
    base = dict(sm.default_params("mixture"), k_div=0.0)   # as above
    a = sm.run(dict(base, **{key: low}), days=TWENTY_YEARS, mode="expected")
    b = sm.run(dict(base, **{key: high}), days=TWENTY_YEARS, mode="expected")
    assert np.all(live(b) <= live(a) * (1 + EXACT_REL))


def test_dermal_signal_is_zero_without_senescent_fibroblasts_or_production():
    for f_sen, p_D in [(0.0, 5.0), (0.5, 0.0)]:
        p = dict(sm.default_params("H2"), f_sen=f_sen, p_D=p_D)
        assert np.all(sm.run(p, days=30, mode="expected")["D"] == 0)
    assert np.all(sm.run(sm.default_params("H2"), days=30, mode="expected")["D"] > 0)


def test_weaker_transfer_never_gives_more_skin_melanin():
    """R3 / R8: only active cells supply melanin, at rate k_tr."""
    base = sm.default_params("H1")
    a = sm.run(dict(base, k_tr=1.0), days=TWO_YEARS, mode="expected")
    b = sm.run(dict(base, k_tr=0.2), days=TWO_YEARS, mode="expected")
    assert np.all(b["melanin"][1:] <= a["melanin"][1:] * (1 + EXACT_REL))


# ----------------------------------------------------------- reproducibility

def test_same_seed_same_output_bit_for_bit():
    p = sm.default_params("mixture")
    a = sm.run(p, days=TWO_YEARS, seed=42, transplant_days=(100,))
    b = sm.run(p, days=TWO_YEARS, seed=42, transplant_days=(100,))
    assert same_run(a, b)
    assert np.array_equal(a["days_since_final_treatment"],
                          b["days_since_final_treatment"], equal_nan=True)


def test_different_seeds_differ():
    p = sm.default_params("mixture")
    a = sm.run(p, days=TWO_YEARS, seed=1)
    b = sm.run(p, days=TWO_YEARS, seed=2)
    assert not same_run(a, b, COUNT_KEYS)


# ---------------------------------------------------------------- transplant

def test_only_intervention_is_transplant():
    """Plan 2.4: no gene therapy or gene editing is simulated."""
    assert tuple(sm.INTERVENTIONS) == ("transplant",)
    banned = ("gene", "crispr", "vector", "edit", "aav", "mrna")
    assert not [s for s in sm.PARAMS if any(b in s.lower() for b in banned)]
    with pytest.raises((TypeError, ValueError)):
        sm.run(sm.default_params("healthy"), days=10, intervention="gene_therapy")


@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_transplant_without_loss_pressure_keeps_its_cells(mode):
    """Plan 6: a transplant into skin with no loss pressure keeps its cells
    indefinitely (10 years here)."""
    p = no_loss(sm.default_params("H2"))
    p.update(N_tx=100.0, s_tx=0.5)
    sessions = (30, 60)
    r = sm.run(p, days=3650, seed=9, mode=mode, transplant_days=sessions)
    alive = np.asarray(r["transplanted_alive"])
    assert np.all(alive[:sessions[0]] == 0)
    after = alive[sessions[-1]:]
    assert after[0] > 0 and np.all(after == after[0])
    if mode == "expected":
        want = len(sessions) * round(p["N_tx"] * area(p)) * p["s_tx"]
        assert math.isclose(after[0], want, rel_tol=EXACT_REL)


def test_zero_survival_transplant_adds_nothing():
    p = dict(sm.default_params("H1"), N_tx=200.0, s_tx=0.0)
    a = sm.run(p, days=400, seed=6, transplant_days=(50,))
    assert np.all(np.asarray(a["transplanted_alive"]) == 0)


@pytest.mark.parametrize("bad", [(0,), (50, 50), (60, 30), (401,), (10.5,)])
def test_bad_transplant_days_are_refused(bad):
    with pytest.raises(ValueError):
        sm.run(sm.default_params("H1"), days=400, transplant_days=bad)


def test_follow_up_is_counted_from_the_final_treatment():
    """CLAUDE.md rule 2."""
    r = sm.run(sm.default_params("H1"), days=400, transplant_days=(30, 60))
    f = np.asarray(r["days_since_final_treatment"], dtype=float)
    assert np.all(np.isnan(f[:60]))
    assert f[60] == 0 and f[240] == 180 and f[400] == 340
    none = sm.run(sm.default_params("H1"), days=100)
    assert np.all(np.isnan(np.asarray(none["days_since_final_treatment"], dtype=float)))


# ------------------------------------------------- readouts and their limits

def test_lightness_mapping_is_strictly_decreasing_and_bounded():
    m = np.linspace(0, 3, 301)
    L = np.asarray(sm.melanin_to_L(m), dtype=float)
    assert np.all(np.diff(L) < 0)
    assert np.all((L >= 0) & (L <= 100))


def test_identical_skin_has_zero_contrast():
    r = sm.run(sm.default_params("healthy"), days=100, seed=8)
    assert np.all(sm.lightness_contrast(r, r) == 0)


def test_contrast_refuses_runs_of_different_length():
    a = sm.run(sm.default_params("healthy"), days=100)
    b = sm.run(sm.default_params("healthy"), days=120)
    with pytest.raises(ValueError):
        sm.lightness_contrast(a, b)


def test_zero_contrast_baseline_is_refused():
    with pytest.raises(ZeroDivisionError):
        sm.residual_contrast(0.0, 3.0)
    with pytest.raises(ZeroDivisionError):
        sm.residual_contrast(5e-7, 3.0)
    assert sm.residual_contrast(10.0, 4.0) == pytest.approx(0.4, rel=EXACT_REL)


def test_six_month_readout_is_a_number_not_a_verdict():
    spot_p = sm.default_params("mixture")
    ring_p = sm.default_params("healthy")
    days, sessions = TWENTY_YEARS, (TWENTY_YEARS - 400, TWENTY_YEARS - 370)
    spot = sm.run(spot_p, days=days, mode="expected", transplant_days=sessions)
    ring = sm.run(ring_p, days=days, mode="expected")
    out = sm.six_month_readout(spot, ring)
    assert set(out) == {"baseline_dL", "dL_at_6_months", "rho_at_6_months",
                        "day_of_final_treatment", "day_of_readout"}
    assert out["day_of_final_treatment"] == sessions[-1]
    assert out["day_of_readout"] == sessions[-1] + 180
    dL = sm.lightness_contrast(spot, ring)
    assert out["baseline_dL"] == pytest.approx(dL[sessions[0] - 1], rel=EXACT_REL)
    assert out["dL_at_6_months"] == pytest.approx(dL[sessions[-1] + 180], rel=EXACT_REL)
    assert out["rho_at_6_months"] == pytest.approx(
        out["dL_at_6_months"] / out["baseline_dL"], rel=EXACT_REL)


def test_six_month_readout_is_never_extrapolated():
    ring = sm.run(sm.default_params("healthy"), days=400, mode="expected")
    short = sm.run(sm.default_params("H1"), days=400, mode="expected",
                   transplant_days=(300,))
    with pytest.raises(ValueError):
        sm.six_month_readout(short, ring)          # needs day 480
    untreated = sm.run(sm.default_params("H1"), days=400, mode="expected")
    with pytest.raises(ValueError):
        sm.six_month_readout(untreated, ring)      # no treatment, no readout


def test_six_month_readout_refuses_zero_baseline():
    ring = sm.run(sm.default_params("healthy"), days=400, mode="expected")
    same = sm.run(sm.default_params("healthy"), days=400, mode="expected",
                  transplant_days=(100,))
    with pytest.raises(ZeroDivisionError):
        sm.six_month_readout(same, ring)


# ----------------------------------------- what the output is allowed to claim

@pytest.mark.parametrize("mode", ["stochastic", "expected"])
def test_every_run_is_labelled_level_0_hypothesis_with_its_assumptions(mode):
    """Plan 10.4: everything the model says is level 0, model only. Plan 1:
    every unmeasured input is labelled an assumption."""
    r = sm.run(sm.default_params("H2"), days=30, seed=13, mode=mode)
    meta = r["meta"]
    assert meta["claim_level"] == 0
    assert meta["output_is"] == "hypothesis"
    assert meta["mode"] == mode and meta["seed"] == 13
    status = {row["symbol"]: row["status"] for row in register_rows()}
    want = sorted(s for s in sm.PARAMS if status[s] == "ASSUMPTION")
    assert list(meta["assumptions"]) == want
    assert "k_derm" in meta["assumptions"] and "n_M_ring" not in meta["assumptions"]


def test_running_the_model_never_touches_the_ledger():
    """Plan 1: nothing the model produces enters data/evidence.csv."""
    files = [ROOT / "data" / "evidence.csv", ROOT / "data" / "evidence_quotes.jsonl"]

    def digest():
        return [hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
                for f in files]

    before = digest()
    for kind in sm.KINDS:
        spot = sm.run(sm.default_params(kind), days=400, transplant_days=(100,))
        ring = sm.run(sm.default_params("healthy"), days=400)
        sm.lightness_contrast(spot, ring)
    assert digest() == before
