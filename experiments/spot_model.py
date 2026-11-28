#!/usr/bin/env python3
"""Well-mixed model of one IGH white spot (Module 6, step M4).

SIMULATION ONLY. Synthetic cell counts, no space, no patient data. Every output
is CLAIM LEVEL 0, A HYPOTHESIS (plan section 10.4): it follows from the rules
and from assumed rates, and it is never evidence. Nothing here writes to
data/evidence.csv or data/evidence_quotes.jsonl.

Contract: the docstring of experiments/tests/test_spot_model.py (step M3).
Plan: content/spot-model-plan.md sections 2.2, 2.3, 4.1, 6, 7, 10.

Inputs are read ONLY through tools/spot_params_check.load_params(), which
refuses a register that fails its quote check and any name not in the register.
Set SPOT_EXCERPTS_DIR to point the check at another copy of the saved excerpts.

What the model is
-----------------
One patch of skin of diameter d_spot, as counts of melanocytes in three live
states (active, hypoactive, senescent) plus a cumulative count of lost cells,
and one number for keratinocyte melanin. One step per day.

  active -> hypoactive          rate k_int * g(age) + k_derm * D
  hypoactive -> gone            rate k_loss + k_derm * D
  hypoactive -> senescent       rate k_sen + k_derm * D
  senescent -> gone             rate k_loss + k_derm * D

A rate r becomes a daily probability 1 - exp(-r). The two exits from the
hypoactive state are taken in turn each day: first loss, with probability
1 - exp(-r_loss), the same daily loss probability a senescent cell has; then,
for the cells not lost, senescence with probability 1 - exp(-r_sen). Each cell
moves at most one step a day. (A first version split the leavers in
proportion to the two rates; in daily steps that gave a cell moving to
senescence about half a day of extra life, so a faster k_sen left slightly
more live cells, which the continuous-time rules do not do. The contract's
direction test caught it.)

Builder's choices the contract leaves open (all ASSUMPTION, listed here so a
reader can see them; none was tuned to separate H1 from H2):

  * Age effect g(age) = (1 + age_in_years) ** a_int. Factor 1 at age 0,
    non-decreasing in age, never lowered by a larger a_int.
  * "Age" is lineage age: cells present on day 0 are age 0 on day 0; each
    transplant session is a new lineage that is age 0 on its day; a daughter
    made by division inherits the lineage age of the cell that made it
    (replicative ageing). Division daughters are shared among lineages in
    proportion to each lineage's active cells.
  * Transplanted cells carry the SAME rates (k_int, a_int, k_tr, k_derm) as
    the resident cells of the run; they differ only in starting at age 0 and
    active. The contract gives one parameter set per run. So under H1 a
    transplant holds better than the resident cells only through a_int.
    Whether donor cells should instead carry healthy-skin rates is an open
    modelling question for Ben and the test-author (it would change P4 under H1).
  * The dermal coupling k_derm * D is added to every forward rate, including
    active -> hypoactive (signal-driven loss of pigment making, the first of
    the two stages in PMID 7377803).
  * Division: gaps below N0 are refilled at a daily per-gap probability
    1 - exp(-k_div * active / N0) (no active cells, no division).
  * Melanin: m(t) = m(t-1) * e + (1 - e) * k_tr * active(t) / N0, with
    e = exp(-1 / T_K). m(0) = 1, the healthy steady state (k_tr = 1, N0 active).
  * Lightness: L* = 50 + 30 * exp(-m). Chosen (plan 3.2, map_L) so a spot at a
    quarter of the ring's melanin reads about +12 L* above it; L*(1) = 61.0,
    L*(0.25) = 73.4. map_L is an ASSUMPTION row in the register but not a run
    parameter, so it is listed with every result in the results CSV.
  * mu_D must be > 0 (D = p_D * f_sen / mu_D would be undefined at 0).

Run the plan's comparisons with experiments/spot_model_compare.py.
Needs: Python 3.9+, numpy.
"""
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import spot_params_check  # noqa: E402

# ---- the parameters run() accepts: register symbol -> register name ---------
SYMBOL_TO_NAME = {
    "k_int": "intrinsic_hypoactivation_rate",
    "a_int": "intrinsic_rate_age_slope",
    "k_sen": "senescence_rate",
    "k_loss": "loss_rate",
    "k_div": "melanocyte_division_rate",
    "k_tr": "melanin_transfer_rate",
    "T_K": "keratinocyte_renewal_time",
    "f_sen": "fibroblast_senescent_share",
    "p_D": "dermal_signal_production",
    "mu_D": "dermal_signal_decay",
    "k_derm": "dermal_coupling",
    "N_tx": "transplant_cells_delivered",
    "s_tx": "transplant_survival",
    "n_M_ring": "melanocyte_density_surround",
    "d_spot": "spot_diameter",
}
PARAMS = tuple(SYMBOL_TO_NAME)
KINDS = ("healthy", "H1", "H2", "mixture")
INTERVENTIONS = ("transplant",)
STATES = ("active", "hypoactive", "senescent")
MODES = ("stochastic", "expected")

DAYS_PER_YEAR = 365.25
L_FLOOR, L_SPAN = 50.0, 30.0          # melanin_to_L: L* = 50 + 30 exp(-m)
READOUT_DAYS = 180                    # six months after the FINAL treatment
ZERO_BASELINE = 1e-6

_REGISTER = None


def register():
    """{symbol: register row}, loaded once through the checker."""
    global _REGISTER
    if _REGISTER is None:
        kwargs = {}
        if os.environ.get("SPOT_EXCERPTS_DIR"):
            kwargs["excerpts_dir"] = os.environ["SPOT_EXCERPTS_DIR"]
        rows = spot_params_check.load_params(list(SYMBOL_TO_NAME.values()), **kwargs)
        out = {}
        for sym, name in SYMBOL_TO_NAME.items():
            row = rows[name]
            if row["symbol"].strip() != sym:
                raise ValueError(f"register row {name} has symbol {row['symbol']!r}, expected {sym!r}")
            out[sym] = row
        _REGISTER = out
    return _REGISTER


def assumptions():
    """Sorted PARAMS whose register status is ASSUMPTION."""
    reg = register()
    return sorted(s for s in PARAMS if reg[s]["status"] == "ASSUMPTION")


def _quoted_number(sym):
    """Leading number of a QUOTED register value, e.g. '220 (SD 28.28)' -> 220."""
    row = register()[sym]
    if row["status"] != "QUOTED":
        raise ValueError(f"{sym} is not QUOTED in the register")
    return float(row["value_or_range"].split()[0])


# ---- default parameter sets (plan 4.1). Rates are per day. -------------------
# All values except n_M_ring and d_spot are ASSUMPTION. They were set so each
# explanation forms a spot over years, at roughly a quarter of the ring's
# melanocytes after 20 years (V1), and not in weeks (plan 7.1).
_HEALTHY = {
    "k_int": 0.0,            # no intrinsic loss in healthy skin
    "a_int": 0.0,
    "k_sen": 1 / 365.0,      # months to years
    "k_loss": 1 / 365.0,
    "k_div": 1e-3,           # near zero to modest; only fills gaps
    "k_tr": 1.0,             # normalised to 1 in healthy skin
    "T_K": 28.0,             # weeks
    "f_sen": 0.0,            # healthy skin: no senescent fibroblasts
    "p_D": 0.0,
    "mu_D": 1.0,
    "k_derm": 0.0,
    "N_tx": 110.0,           # half the ring density
    "s_tx": 0.5,
}
_H1_CHANGES = {"k_int": 5e-5, "a_int": 1.0}
_H2_CHANGES = {"f_sen": 0.5, "p_D": 1.0, "mu_D": 1.0, "k_derm": 1.5e-3}
_MIXTURE_CHANGES = {"k_int": 2.5e-5, "a_int": 1.0,
                    "f_sen": 0.5, "p_D": 1.0, "mu_D": 1.0, "k_derm": 8e-4}


def default_params(kind):
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; expected one of {KINDS}")
    p = dict(_HEALTHY)
    p["n_M_ring"] = _quoted_number("n_M_ring")   # 220, PMID 2508572
    p["d_spot"] = 3.0                            # inside the quoted 2 to 5 mm, PMID 3805391
    p.update({"healthy": {}, "H1": _H1_CHANGES, "H2": _H2_CHANGES,
              "mixture": _MIXTURE_CHANGES}[kind])
    return {k: float(p[k]) for k in PARAMS}


# ---- checks ------------------------------------------------------------------

def _check_params(params):
    keys = set(params)
    extra = keys - set(PARAMS)
    if extra:
        raise ValueError(f"not in the parameter register: {sorted(extra)}")
    missing = set(PARAMS) - keys
    if missing:
        raise ValueError(f"missing parameters (no silent defaults): {sorted(missing)}")
    p = {}
    for k in PARAMS:
        v = float(params[k])
        if not math.isfinite(v):
            raise ValueError(f"{k} = {v} is not finite")
        if v < 0:
            raise ValueError(f"{k} = {v} is negative")
        p[k] = v
    for k in ("f_sen", "s_tx"):
        if p[k] > 1:
            raise ValueError(f"{k} = {p[k]} is outside [0, 1]")
    for k in ("d_spot", "T_K", "mu_D"):
        if p[k] <= 0:
            raise ValueError(f"{k} must be > 0, got {p[k]}")
    return p


def _check_days(days, transplant_days):
    if isinstance(days, bool) or not isinstance(days, (int, np.integer)) or days < 1:
        raise ValueError(f"days must be an int >= 1, got {days!r}")
    tx = tuple(transplant_days)
    for d in tx:
        if isinstance(d, bool) or not isinstance(d, (int, np.integer)):
            raise ValueError(f"transplant day {d!r} is not an int")
        if not 1 <= d <= days:
            raise ValueError(f"transplant day {d} outside [1, {days}]")
    if any(b <= a for a, b in zip(tx, tx[1:])):
        raise ValueError(f"transplant_days {tx} are not strictly increasing")
    return tuple(int(d) for d in tx)


def patch_area(p):
    return math.pi * p["d_spot"] ** 2 / 4


def dermal_signal(p):
    if p["p_D"] > 0 and p["f_sen"] > 0:
        return p["p_D"] * p["f_sen"] / p["mu_D"]
    return 0.0


# ---- the model -----------------------------------------------------------------

def run(params, *, days, seed=0, mode="stochastic", transplant_days=()):
    p = _check_params(params)
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    tx = _check_days(days, transplant_days)
    stochastic = mode == "stochastic"
    rng = np.random.default_rng(seed)

    area = patch_area(p)
    n0 = round(p["n_M_ring"] * area)
    if n0 < 1:
        raise ValueError("patch holds no melanocytes (n_M_ring * area rounds to 0)")
    n_del = round(p["N_tx"] * area)
    D = dermal_signal(p)
    kD = p["k_derm"] * D
    r_sen = p["k_sen"] + kD
    r_loss = p["k_loss"] + kD
    p_hs = -math.expm1(-r_sen)
    p_sl = -math.expm1(-r_loss)
    decay = math.exp(-1.0 / p["T_K"])

    # lineages: 0 = cells present on day 0; 1.. = transplant sessions
    n_lin = 1 + len(tx)
    born = np.array([0] + list(tx), dtype=float)
    dtype = np.int64 if stochastic else float
    A = np.zeros(n_lin, dtype=dtype)
    H = np.zeros(n_lin, dtype=dtype)
    S = np.zeros(n_lin, dtype=dtype)
    A[0] = n0
    gone = 0 if stochastic else 0.0
    tx_index = {d: i + 1 for i, d in enumerate(tx)}

    n = days + 1
    out = {k: np.zeros(n, dtype=dtype) for k in ("active", "hypoactive", "senescent",
                                               "gone", "transplanted_alive")}
    melanin = np.zeros(n)
    m = 1.0

    def record(t):
        out["active"][t] = A.sum()
        out["hypoactive"][t] = H.sum()
        out["senescent"][t] = S.sum()
        out["gone"][t] = gone
        out["transplanted_alive"][t] = (A[1:] + H[1:] + S[1:]).sum()
        melanin[t] = m

    record(0)
    for t in range(1, n):
        age_years = np.maximum(t - 1 - born, 0.0) / DAYS_PER_YEAR
        r_h = p["k_int"] * (1.0 + age_years) ** p["a_int"] + kD
        p_h = -np.expm1(-r_h)
        if stochastic:
            a_h = rng.binomial(A, p_h)
            h_g = rng.binomial(H, p_sl)
            h_s = rng.binomial(H - h_g, p_hs)
            s_g = rng.binomial(S, p_sl)
        else:
            a_h = A * p_h
            h_g = H * p_sl
            h_s = (H - h_g) * p_hs
            s_g = S * p_sl
        A = A - a_h
        H = H + a_h - h_g - h_s
        S = S + h_s - s_g
        gone = gone + h_g.sum() + s_g.sum()

        # R7: division fills gaps below N0 only
        live_total = A.sum() + H.sum() + S.sum()
        a_total = A.sum()
        gap = n0 - live_total
        if p["k_div"] > 0 and gap > 0 and a_total > 0:
            p_b = -math.expm1(-p["k_div"] * a_total / n0)
            if stochastic:
                births = rng.binomial(int(gap), p_b)
                A = A + rng.multinomial(births, A / a_total)
            else:
                A = A + gap * p_b * (A / a_total)

        # R9: transplant, before the day's row is recorded
        if t in tx_index:
            joined = rng.binomial(n_del, p["s_tx"]) if stochastic else n_del * p["s_tx"]
            A[tx_index[t]] += joined

        m = m * decay + (1.0 - decay) * p["k_tr"] * A.sum() / n0
        record(t)

    since = np.full(n, np.nan)
    if tx:
        since[tx[-1]:] = np.arange(n - tx[-1])
    out.update(
        day=np.arange(n),
        melanin=melanin,
        D=np.full(n, D),
        days_since_final_treatment=since,
        transplant_days=tx,
        meta={"claim_level": 0, "output_is": "hypothesis", "mode": mode,
              "seed": seed, "assumptions": assumptions()},
    )
    return out


# ---- readouts --------------------------------------------------------------------

def melanin_to_L(m):
    """L* of skin holding melanin m (relative, healthy = 1). ASSUMPTION mapping."""
    m = np.asarray(m, dtype=float)
    return L_FLOOR + L_SPAN * np.exp(-np.maximum(m, 0.0))


def lightness_contrast(spot, ring):
    """dL*(day) = L*(spot) - L*(ring). Positive means the spot is lighter."""
    a, b = np.asarray(spot["melanin"]), np.asarray(ring["melanin"])
    if a.shape != b.shape or not np.array_equal(spot["day"], ring["day"]):
        raise ValueError("spot and ring runs cover different days")
    return melanin_to_L(a) - melanin_to_L(b)


def residual_contrast(base_dL, follow_dL):
    """follow / base. A baseline within 1e-6 L* of zero is refused."""
    if abs(base_dL) < ZERO_BASELINE:
        raise ZeroDivisionError(f"baseline contrast {base_dL!r} is zero; ratio refused")
    return follow_dL / base_dL


def six_month_readout(spot, ring):
    """Contrast six months after the FINAL transplant session. A number, not a verdict."""
    dL = lightness_contrast(spot, ring)
    tx = tuple(spot.get("transplant_days", ()))
    if not tx:
        raise ValueError("spot run has no transplant; there is no final treatment to count from")
    final = tx[-1]
    readout = final + READOUT_DAYS
    if readout > len(dL) - 1:
        raise ValueError(f"run ends on day {len(dL) - 1}, before the readout day {readout}; "
                         "never extrapolated")
    base = float(dL[tx[0] - 1])
    follow = float(dL[readout])
    rho = residual_contrast(base, follow)
    return {"baseline_dL": base, "dL_at_6_months": follow, "rho_at_6_months": rho,
            "day_of_final_treatment": final, "day_of_readout": readout}
