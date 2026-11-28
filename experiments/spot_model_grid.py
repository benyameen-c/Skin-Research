#!/usr/bin/env python3
"""Spatial (grid) model of one IGH white spot (Module 6, step M6).

SIMULATION ONLY. Synthetic cells on a synthetic lattice, synthetic images, no
patient data (CLAUDE.md rule 7). Every output is CLAIM LEVEL 0, A HYPOTHESIS
(plan section 10.4): it follows from the rules and from assumed rates, and it
is never evidence. Nothing here writes to data/evidence.csv or
data/evidence_quotes.jsonl.

Contract: the docstring of experiments/tests/test_spot_model_grid.py (step M5,
tests commit 22ed277). Plan: content/spot-model-plan.md sections 2, 5.1, 6, 7,
10 and 11. Scope: cell behaviour and cell transplantation only. No gene
therapy, no gene editing, no drug, no wounding (plan 2.4).

The grid is the well-mixed model (experiments/spot_model.py) with space added.
With lambda_D = 0, k_div = 0 and uniform fibroblasts every site is an
independent copy of one well-mixed cell, and the expected run equals
spot_model's expected run exactly (a test enforces it). Every rule that is not
spatial is spot_model's rule, applied per cell.

Inputs are read through tools/spot_params_check.load_params (via
spot_model.register and this module's grid_register), which refuses a
register that fails its quote check and any name not in the register.

Builder's choices the contract leaves open (all ASSUMPTION, listed so a reader
can argue with them; none was tuned to separate H1 from H2):

  * Default lambda_D = 0.3 mm for every kind. The register gives a range only
    ([0.05 to 2] mm); 0.3 is about its geometric middle (0.32). It is swept in
    the comparison run.
  * Lineages. 0 = resident cells that start inside the disc (the run's k_int,
    a_int, k_tr); 1 = resident cells that start outside it (healthy k_int,
    a_int, k_tr); 2.. = one lineage per transplant session (rates from
    tx_rates). A lineage's age clock starts on its birth day (0 for residents,
    the session day for transplants); a daughter joins its parent's lineage,
    so it inherits the parent's rates, age clock and transplant label.
  * Random numbers (stochastic mode). Four independent streams spawned from
    `seed` (numpy SeedSequence): resident slots, extra slots, division,
    transplant. The resident stream draws the same two uniform arrays every
    day whatever the parameters, so runs that differ only in rates that do
    not act (for example fibroblast state under H1, or tx_site_capacity
    without a transplant) consume identical numbers. Fibroblast draws use
    their own generator, numpy default_rng(fibroblast_seed).
  * A cell's daily step uses spot_model's probabilities: active -> hypoactive
    with 1 - exp(-(k_int g(age) + k_derm D)); a hypoactive cell is first lost
    with 1 - exp(-(k_loss + k_derm D)), and if not lost becomes senescent with
    1 - exp(-(k_sen + k_derm D)); a senescent cell is lost with
    1 - exp(-(k_loss + k_derm D)).
  * Expected mode "empty" (sites with no live cell) is the product over a
    site's slots of each slot's free probability, treating slots as
    independent (a mean-field approximation, like the division rule). Before
    any transplant the extra slots are empty, so this is exact.
  * Which slots division can fill on a day. Division fills only resident
    slots that were free at the START of the day: a cell lost today leaves
    its slot empty for division from tomorrow, so division never turns a site
    hypoactive or senescent -> gone -> active in a single day (the
    one-step-per-day rule, V3, per site). The well-mixed model counts today's
    losses as gaps; the two agree whenever k_div = 0. Transplant, by
    contrast, fills every slot free after the day's transitions and division
    (the contract's order, and what a large transplant filling every slot
    requires), so on a session day a slot lost that morning can be refilled.
  * Dermal signal solved exactly by a discrete cosine transform (the
    eigenbasis of the five-point Laplacian with reflecting boundaries); the
    relative residual is checked against 1e-10 on every call.
  * Render: pixel colour has the site's L* and drift_sim.SKIN_RGB's a*, b*,
    converted back to linear RGB by the exact inverse of drift_sim.rgb_to_lab.

Run the plan's grid comparisons with experiments/spot_model_grid_compare.py.
Needs: Python 3.9+, numpy.
"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import drift_sim as ds  # noqa: E402
import spot_model as sm  # noqa: E402

GRID_SYMBOL_TO_NAME = {
    "lambda_D": "dermal_signal_reach",
    "tx_site_capacity": "transplant_site_capacity",
}
GRID_PARAMS = tuple(GRID_SYMBOL_TO_NAME)
PARAMS = tuple(sm.PARAMS) + GRID_PARAMS
KINDS = sm.KINDS
INTERVENTIONS = sm.INTERVENTIONS
STATES = sm.STATES
MODES = sm.MODES
FIBROBLASTS = ("random", "uniform")

PX_PER_MM = 20
BLUR_SD_MM = ds.BLUR_SD_MM
RING_GAP_MM = ds.RING_GAP_MM
RING_WIDTH_MM = ds.RING_WIDTH_MM
SKIP_DL = 1.0
READOUT_DAYS = sm.READOUT_DAYS
ZERO_BASELINE = sm.ZERO_BASELINE
SOLVER_RESIDUAL = 1e-10

STRUCTURAL_ASSUMPTIONS = (
    "site_spacing_from_n_M_ring",
    "one_resident_slot_per_site",
    "one_fibroblast_per_site",
    "defect_patch_is_fixed_disc",
    "daughter_copies_parent_lineage_and_age",
    "transplant_fills_free_slots_up_to_capacity",
)

DEFAULT_LAMBDA_D = 0.3        # mm; ASSUMPTION, about the geometric middle of [0.05, 2]
DEFAULT_CAPACITY = 2.0        # register row transplant_site_capacity: base runs

melanin_to_L = sm.melanin_to_L

_GRID_REGISTER = None


def grid_register():
    """{symbol: register row} for the grid's own parameters, via the checker."""
    global _GRID_REGISTER
    if _GRID_REGISTER is None:
        kwargs = {}
        import os
        if os.environ.get("SPOT_EXCERPTS_DIR"):
            kwargs["excerpts_dir"] = os.environ["SPOT_EXCERPTS_DIR"]
        rows = sm.spot_params_check.load_params(list(GRID_SYMBOL_TO_NAME.values()), **kwargs)
        out = {}
        for sym, name in GRID_SYMBOL_TO_NAME.items():
            row = rows[name]
            if row["symbol"].strip() != sym:
                raise ValueError(f"register row {name} has symbol {row['symbol']!r}, expected {sym!r}")
            out[sym] = row
        _GRID_REGISTER = out
    return _GRID_REGISTER


def assumptions():
    """Sorted PARAMS whose register status is ASSUMPTION."""
    reg = dict(sm.register(), **grid_register())
    return sorted(s for s in PARAMS if reg[s]["status"] == "ASSUMPTION")


def default_params(kind):
    p = sm.default_params(kind)          # ValueError on an unknown kind
    grid_register()                      # the grid's rows must exist and pass
    p["lambda_D"] = DEFAULT_LAMBDA_D
    p["tx_site_capacity"] = DEFAULT_CAPACITY
    return p


# ---- checks -------------------------------------------------------------------

def _check_params(params):
    keys = set(params)
    extra = keys - set(PARAMS)
    if extra:
        raise ValueError(f"not in the parameter register: {sorted(extra)}")
    missing = set(PARAMS) - keys
    if missing:
        raise ValueError(f"missing parameters (no silent defaults): {sorted(missing)}")
    p = sm._check_params({k: params[k] for k in sm.PARAMS})
    lam = float(params["lambda_D"])
    if not math.isfinite(lam) or lam < 0:
        raise ValueError(f"lambda_D must be finite and >= 0, got {lam}")
    cap = float(params["tx_site_capacity"])
    if not math.isfinite(cap) or not cap.is_integer() or not 1 <= cap <= 3:
        raise ValueError(f"tx_site_capacity must be a whole number in 1..3, got {params['tx_site_capacity']!r}")
    p["lambda_D"] = lam
    p["tx_site_capacity"] = cap
    return p


def _check_snapshots(snapshot_days, days):
    if snapshot_days is None:
        return (0, days)
    snaps = tuple(snapshot_days)
    for d in snaps:
        if isinstance(d, bool) or not isinstance(d, (int, np.integer)):
            raise ValueError(f"snapshot day {d!r} is not an int")
        if not 0 <= d <= days:
            raise ValueError(f"snapshot day {d} outside [0, {days}]")
    if any(b <= a for a, b in zip(snaps, snaps[1:])):
        raise ValueError(f"snapshot_days {snaps} are not strictly increasing")
    return tuple(int(d) for d in snaps)


# ---- geometry -----------------------------------------------------------------

def geometry(params):
    d = float(params["d_spot"])
    n_px = ds.field_size(d, PX_PER_MM)
    field_mm = n_px / PX_PER_MM
    n_side = int(round(field_mm * math.sqrt(float(params["n_M_ring"]))))
    if n_side < 1:
        raise ValueError("lattice has no sites")
    h = field_mm / n_side
    x = h * (np.arange(n_side) + 0.5)
    X, Y = np.meshgrid(x, x)
    r = np.hypot(X - field_mm / 2, Y - field_mm / 2)
    r0 = d / 2 + RING_GAP_MM
    return {
        "field_mm": field_mm,
        "n_side": n_side,
        "h_mm": h,
        "x_mm": x,
        "spot_mask": r <= d / 2,
        "ring_mask": (r >= r0) & (r <= r0 + RING_WIDTH_MM),
    }


# ---- dermal signal (R5) ---------------------------------------------------------

def _dct_matrix(n):
    """Orthonormal DCT-II matrix; its rows are the eigenvectors of the 1-D
    second difference with reflecting (zero-flux) ends."""
    k = np.arange(n)[:, None]
    j = np.arange(n)[None, :]
    C = np.sqrt(2.0 / n) * np.cos(math.pi * k * (j + 0.5) / n)
    C[0] /= math.sqrt(2.0)
    return C


def _neumann_laplacian(D, h):
    P = np.pad(D, 1, mode="edge")
    return (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:] - 4 * D) / h ** 2


def dermal_signal(source, h_mm, lambda_D, p_D, mu_D):
    """Steady state of R5: D - lambda_D^2 Lap_h(D) = (p_D / mu_D) source."""
    src = np.asarray(source, dtype=float)
    if lambda_D < 0 or p_D < 0 or mu_D <= 0:
        raise ValueError("need lambda_D >= 0, p_D >= 0, mu_D > 0")
    if np.any(src < 0):
        raise ValueError("source must be non-negative")
    if p_D == 0 or not np.any(src):
        return np.zeros_like(src)
    rhs = (p_D / mu_D) * src
    if lambda_D == 0:
        return rhs
    ny, nx = src.shape
    Cy, Cx = _dct_matrix(ny), _dct_matrix(nx)
    ey = (2 - 2 * np.cos(math.pi * np.arange(ny) / ny)) / h_mm ** 2
    ex = (2 - 2 * np.cos(math.pi * np.arange(nx) / nx)) / h_mm ** 2
    hat = Cy @ rhs @ Cx.T
    hat /= 1.0 + lambda_D ** 2 * (ey[:, None] + ex[None, :])
    D = Cy.T @ hat @ Cx
    res = D - lambda_D ** 2 * _neumann_laplacian(D, h_mm) - rhs
    scale = max(np.abs(rhs).max(), 1e-300)
    if np.abs(res).max() / scale > SOLVER_RESIDUAL:
        raise RuntimeError("dermal signal solver did not reach its residual")
    return D


def _neighbour_sum(a):
    """Sum over the 4 neighbours inside the field (no wrap). a: (..., n, n)."""
    out = np.zeros_like(a)
    out[..., 1:, :] += a[..., :-1, :]
    out[..., :-1, :] += a[..., 1:, :]
    out[..., :, 1:] += a[..., :, :-1]
    out[..., :, :-1] += a[..., :, 1:]
    return out


# ---- the model ------------------------------------------------------------------

def run(params, *, days, seed=0, mode="stochastic", transplant_days=(),
        snapshot_days=None, fibroblasts="random", fibroblast_seed=None):
    p = _check_params(params)
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    if fibroblasts not in FIBROBLASTS:
        raise ValueError(f"unknown fibroblasts {fibroblasts!r}; expected one of {FIBROBLASTS}")
    tx = sm._check_days(days, transplant_days)
    snaps = _check_snapshots(snapshot_days, days)
    fseed = seed if fibroblast_seed is None else fibroblast_seed
    stochastic = mode == "stochastic"

    g = geometry(p)
    n = g["n_side"]
    disc = g["spot_mask"]
    C = int(p["tx_site_capacity"])

    # dermis: fixed for the run
    if fibroblasts == "random":
        frng = np.random.default_rng(fseed)
        fib = ((frng.random((n, n)) < p["f_sen"]) & disc).astype(float)
    else:
        fib = np.where(disc, p["f_sen"], 0.0)
    D_map = dermal_signal(fib, g["h_mm"], p["lambda_D"], p["p_D"], p["mu_D"])
    kD = p["k_derm"] * D_map
    p_sl = -np.expm1(-(p["k_loss"] + kD))
    p_hs = -np.expm1(-(p["k_sen"] + kD))
    decay = math.exp(-1.0 / p["T_K"])

    # lineages
    healthy = sm.default_params("healthy")
    donor = p["tx_rates"] == 1.0
    tk = (p["k_int_tx"], p["a_int_tx"], p["k_tr_tx"]) if donor else (p["k_int"], p["a_int"], p["k_tr"])
    lin_k_int = np.array([p["k_int"], healthy["k_int"]] + [tk[0]] * len(tx))
    lin_a_int = np.array([p["a_int"], healthy["a_int"]] + [tk[1]] * len(tx))
    lin_k_tr = np.array([p["k_tr"], healthy["k_tr"]] + [tk[2]] * len(tx))
    born = np.array([0.0, 0.0] + [float(d) for d in tx])
    n_lin = len(born)
    tx_lineage = {d: 2 + i for i, d in enumerate(tx)}
    n_del = round(p["N_tx"] * sm.patch_area(p))

    masks = {"spot": disc, "ring": g["ring_mask"]}
    n_days = days + 1
    series = {reg: {k: np.zeros(n_days) for k in ("active", "hypoactive", "senescent", "empty",
                                                  "gone", "transplanted_alive", "melanin")}
              for reg in masks}
    gone_map = np.zeros((n, n))
    melanin = np.ones((n, n))
    snapshots = {}
    overflow = []

    if stochastic:
        ss = np.random.SeedSequence(seed)
        rng_res, rng_ext, rng_div, rng_tx = (np.random.default_rng(s) for s in ss.spawn(4))
        # state per slot: 0 empty, 1 active, 2 hypoactive, 3 senescent
        st = np.zeros((C, n, n), dtype=np.int8)
        lin = np.zeros((C, n, n), dtype=np.int16)
        st[0] = 1
        lin[0] = np.where(disc, 0, 1)
    else:
        # probabilities per lineage, slot, site
        A = np.zeros((n_lin, C, n, n))
        H = np.zeros_like(A)
        S = np.zeros_like(A)
        A[0, 0][disc] = 1.0
        A[1, 0][~disc] = 1.0
    extra_used = False
    n_live_lin = 2          # lineages that exist so far (expected mode slices to these)

    def maps():
        if stochastic:
            a = (st == 1).sum(0).astype(float)
            hh = (st == 2).sum(0).astype(float)
            s = (st == 3).sum(0).astype(float)
            trm = ((st > 0) & (lin >= 2)).sum(0).astype(float)
            empty = (st == 0).all(0).astype(float)
        else:
            kk = C if extra_used else 1
            Al, Hl, Sl = A[:n_live_lin, :kk], H[:n_live_lin, :kk], S[:n_live_lin, :kk]
            a = Al.sum((0, 1))
            hh = Hl.sum((0, 1))
            s = Sl.sum((0, 1))
            trm = (Al[2:] + Hl[2:] + Sl[2:]).sum((0, 1))
            empty = np.prod(np.clip(1.0 - (Al + Hl + Sl).sum(0), 0.0, 1.0), axis=0)
        return a, hh, s, trm, empty

    def record(t):
        a, hh, s, trm, empty = maps()
        stack = np.stack([a, hh, s, empty, gone_map, trm, melanin]).reshape(7, -1)
        sums = stack @ mask_mat                       # (7, 2): region sums
        for j, reg in enumerate(masks):
            sr = series[reg]
            for i, k in enumerate(("active", "hypoactive", "senescent", "empty", "gone",
                                   "transplanted_alive")):
                sr[k][t] = sums[i, j]
            sr["melanin"][t] = sums[6, j] / mask_n[j]
        if t in snaps_set:
            snapshots[t] = {"active": a, "hypoactive": hh, "senescent": s,
                            "melanin": melanin.copy(), "transplanted": trm}

    snaps_set = set(snaps)
    mask_mat = np.stack([m.ravel() for m in masks.values()], axis=1).astype(float)
    mask_n = mask_mat.sum(0)
    record(0)
    for t in range(1, n_days):
        age_years = np.maximum(t - 1 - born, 0.0) / sm.DAYS_PER_YEAR
        g_lin = lin_k_int * (1.0 + age_years) ** lin_a_int

        # slots free at the start of the day: only these can be filled by
        # division today (a cell lost today leaves its slot empty from tomorrow)
        if p["k_div"] > 0:
            if stochastic:
                was_free = st == 0
            else:
                was_free = np.clip(1.0 - (A[:, :1] + H[:, :1] + S[:, :1]).sum(0), 0.0, 1.0)

        # 1. transitions (R1 to R4)
        if stochastic:
            u1 = rng_res.random((n, n))
            u2 = rng_res.random((n, n))
            slots = [(0, u1, u2)]
            if extra_used:
                for c in range(1, C):
                    if np.any(st[c]):
                        slots.append((c, rng_ext.random((n, n)), rng_ext.random((n, n))))
            for c, v1, v2 in slots:
                sc = st[c]
                p_h = -np.expm1(-(g_lin[lin[c]] + kD))
                act = sc == 1
                hyp = sc == 2
                sen = sc == 3
                to_h = act & (v1 < p_h)
                h_lost = hyp & (v1 < p_sl)
                h_sen = hyp & ~h_lost & (v2 < p_hs)
                s_lost = sen & (v1 < p_sl)
                lost = h_lost | s_lost
                sc[to_h] = 2
                sc[h_sen] = 3
                sc[lost] = 0
                gone_map += lost
        else:
            kk = C if extra_used else 1
            nl = n_live_lin
            p_h = -np.expm1(-(g_lin[:nl, None, None, None] + kD[None, None]))
            a_h = A[:nl, :kk] * p_h
            h_g = H[:nl, :kk] * p_sl
            h_s = (H[:nl, :kk] - h_g) * p_hs
            s_g = S[:nl, :kk] * p_sl
            A[:nl, :kk] -= a_h
            H[:nl, :kk] += a_h - h_g - h_s
            S[:nl, :kk] += h_s - s_g
            gone_map += (h_g + s_g).sum((0, 1))

        # 2. division (R7): fills empty resident slots only
        if p["k_div"] > 0:
            if stochastic:
                act_cells = (st == 1)
                act_any = act_cells.any(0).astype(float)
                a_nb = _neighbour_sum(act_any)
                u = rng_div.random((n, n))
                born_sites = was_free[0] & (a_nb > 0) & (u < -np.expm1(-p["k_div"] * a_nb / 4))
                if born_sites.any():
                    act_n = act_cells.sum(0)
                    for i, j in zip(*np.nonzero(born_sites)):
                        cand = []
                        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            ii, jj = i + di, j + dj
                            if 0 <= ii < n and 0 <= jj < n and act_n[ii, jj]:
                                for c in range(C):
                                    if st[c, ii, jj] == 1:
                                        cand.append(lin[c, ii, jj])
                        st[0, i, j] = 1
                        lin[0, i, j] = cand[int(rng_div.integers(len(cand)))]
            else:
                act_lin = A[:n_live_lin].sum(1)                 # (L, n, n)
                act_site = act_lin.sum(0)
                a_nb = _neighbour_sum(np.minimum(1.0, act_site))
                births = was_free[0] * -np.expm1(-p["k_div"] * a_nb / 4)
                nb_lin = _neighbour_sum(act_lin)
                tot = nb_lin.sum(0)
                w = np.divide(births, tot, out=np.zeros_like(births), where=tot > 0)
                A[:n_live_lin, 0] += nb_lin * w

        # 3. transplant (R9)
        if t in tx_lineage:
            L = tx_lineage[t]
            if stochastic:
                surv = int(rng_tx.binomial(n_del, p["s_tx"]))
                free = (st == 0) & disc[None]
                idx = np.flatnonzero(free)
                k = min(surv, idx.size)
                if k:
                    chosen = idx[rng_tx.choice(idx.size, size=k, replace=False)]
                    st.reshape(-1)[chosen] = 1
                    lin.reshape(-1)[chosen] = L
                overflow.append(surv - k)
            else:
                surv = n_del * p["s_tx"]
                free = np.clip(1.0 - (A + H + S).sum(0), 0.0, 1.0) * disc[None]
                E = free.sum()
                share = min(1.0, surv / E) if E > 0 else 0.0
                A[L] += share * free
                overflow.append(max(0.0, surv - E))
            extra_used = extra_used or C > 1
            n_live_lin = max(n_live_lin, L + 1)

        # 4. melanin (R8): supply summed over the site's active cells
        if stochastic:
            supply = ((st == 1) * lin_k_tr[lin]).sum(0)
        else:
            supply = np.tensordot(lin_k_tr[:n_live_lin], A[:n_live_lin].sum(1), axes=(0, 0))
        melanin = melanin * decay + (1.0 - decay) * supply
        record(t)

    since = np.full(n_days, np.nan)
    if tx:
        since[tx[-1]:] = np.arange(n_days - tx[-1])
    out = {
        "day": np.arange(n_days),
        "spot": series["spot"],
        "ring": series["ring"],
        "n_sites": {"spot": int(disc.sum()), "ring": int(g["ring_mask"].sum())},
        "fibroblast_map": fib,
        "D_map": D_map,
        "snapshots": snapshots,
        "transplant_overflow": overflow,
        "days_since_final_treatment": since,
        "transplant_days": tx,
        "geometry": g,
        "params": dict(p),
        "meta": {"claim_level": 0, "output_is": "hypothesis", "mode": mode,
                 "seed": seed, "fibroblast_seed": fseed, "fibroblasts": fibroblasts,
                 "assumptions": assumptions(),
                 "structural_assumptions": list(STRUCTURAL_ASSUMPTIONS)},
    }
    if stochastic:
        for reg in ("spot", "ring"):
            for k in ("active", "hypoactive", "senescent", "empty", "gone", "transplanted_alive"):
                out[reg][k] = out[reg][k].astype(np.int64)
        for snap in snapshots.values():
            for k in ("active", "hypoactive", "senescent", "transplanted"):
                snap[k] = snap[k].astype(np.int64)
    return out


# ---- rendering and measurement ----------------------------------------------------

_M_INV = np.linalg.inv(ds._M)


def _lab_to_rgb(L, a, b):
    """Exact inverse of drift_sim.rgb_to_lab."""
    d = 6.0 / 29.0
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0

    def finv(f):
        return np.where(f > d, f ** 3, 3 * d * d * (f - 4.0 / 29.0))

    xyz = np.stack([finv(fx), finv(fy), finv(fz)], axis=-1) * ds._WHITE
    return xyz @ _M_INV.T


_SKIN_LAB = ds.rgb_to_lab(np.asarray(ds.SKIN_RGB, dtype=float)[None, None, :])[0, 0]


def render(result, day, *, blur_sd_mm=BLUR_SD_MM, noise_sd=0.0, seed=0):
    if day not in result["snapshots"]:
        raise ValueError(f"day {day} is not a snapshot day of this run")
    g = result["geometry"]
    d = result["params"]["d_spot"]
    n_px = ds.field_size(d, PX_PER_MM)
    c = (np.arange(n_px) + 0.5) / PX_PER_MM
    idx = np.minimum((c / g["h_mm"]).astype(int), g["n_side"] - 1)
    m = np.asarray(result["snapshots"][day]["melanin"], dtype=float)[np.ix_(idx, idx)]
    L = np.asarray(melanin_to_L(m), dtype=float)
    img = _lab_to_rgb(L, np.full_like(L, _SKIN_LAB[1]), np.full_like(L, _SKIN_LAB[2]))
    img = ds.blur(img, PX_PER_MM, blur_sd_mm)
    if noise_sd > 0:
        img = img + np.random.default_rng(seed).normal(0.0, noise_sd, img.shape)
    return img


def measure_dL(img, d_spot):
    return ds.measure_contrast(img, d_spot, PX_PER_MM)["L"]


def six_month_readout(result):
    tx = tuple(result.get("transplant_days", ()))
    if not tx:
        raise ValueError("run has no transplant; there is no final treatment to count from")
    final = tx[-1]
    readout = final + READOUT_DAYS
    last = len(result["day"]) - 1
    if readout > last:
        raise ValueError(f"run ends on day {last}, before the readout day {readout}; never extrapolated")
    base_day = tx[0] - 1
    for dday in (base_day, readout):
        if dday not in result["snapshots"]:
            raise ValueError(f"day {dday} is not a snapshot day; never interpolated")
    d = result["params"]["d_spot"]
    base = measure_dL(render(result, base_day), d)
    follow = measure_dL(render(result, readout), d)
    if abs(base) < ZERO_BASELINE:
        raise ZeroDivisionError(f"baseline contrast {base!r} is zero; ratio refused")
    return {"baseline_dL": base, "dL_at_6_months": follow, "rho_at_6_months": follow / base,
            "day_of_final_treatment": final, "day_of_readout": readout}


# ---- image statistics (plan section 11.3) -------------------------------------------

def _pixel_r(n_px):
    c = (np.arange(n_px) + 0.5) / PX_PER_MM
    X, Y = np.meshgrid(c, c)
    c0 = n_px / PX_PER_MM / 2
    return np.hypot(X - c0, Y - c0)


def _L(img):
    return ds.rgb_to_lab(np.asarray(img, dtype=float))[..., 0]


def _profile(img, d_spot):
    L = _L(img)
    n_px = L.shape[0]
    r = _pixel_r(n_px)
    ring = ds._geometry(d_spot, PX_PER_MM)[3] > 0
    if ring.shape != L.shape:
        raise ValueError("image does not match the field for this spot diameter")
    L_ring = L[ring].mean()
    L_centre = L[r <= d_spot / 4].mean()
    Cn = L_centre - L_ring
    if abs(Cn) < 1e-6:
        raise ZeroDivisionError("spot has no contrast; edge width undefined")
    k = np.floor(r * PX_PER_MM).astype(int).ravel()
    sums = np.bincount(k, weights=L.ravel())
    cnt = np.bincount(k)
    ok = cnt > 0
    centres = (np.arange(len(cnt)) + 0.5) / PX_PER_MM
    q = (sums[ok] / cnt[ok] - L_ring) / Cn
    return centres[ok], q


def _crossing(centres, q, t):
    below = np.nonzero(q < t)[0]
    if below.size == 0:
        raise ValueError(f"radial profile never falls below {t}")
    i = int(below[0])
    if i == 0:
        return float(centres[0])
    q0, q1 = q[i - 1], q[i]
    r0, r1 = centres[i - 1], centres[i]
    return float(r0 + (q0 - t) / (q0 - q1) * (r1 - r0))


def edge_width(img, d_spot):
    c, q = _profile(img, d_spot)
    return _crossing(c, q, 0.1) - _crossing(c, q, 0.9)


def edge_midpoint(img, d_spot):
    c, q = _profile(img, d_spot)
    return _crossing(c, q, 0.5)


def skip_score(img, d_spot):
    L = _L(img)
    r = _pixel_r(L.shape[0])
    vals = L[r <= 0.6 * d_spot / 2]
    return float(np.mean(vals < np.median(vals) - SKIP_DL))


def rim_centre_dL(img, d_spot):
    L = _L(img)
    r = _pixel_r(L.shape[0])
    R = d_spot / 2
    return float(L[r <= 0.3 * R].mean() - L[(r > 0.6 * R) & (r <= 0.85 * R)].mean())
