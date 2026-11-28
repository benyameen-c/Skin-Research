# Plan: a cell-level model of one IGH white spot

Status: planning document for Ben's review, 28 November 2026. No code exists yet and none is written until Ben has read this plan. Not linked from the site (`site.json` does not list it) and not for publication until Gate B. Research, not medical advice.

SIMULATION ONLY. Synthetic cells on a synthetic grid. No patient images (CLAUDE.md rule 7).

## 1. Purpose, and what the model can and cannot claim

Ben asked to "delve deeper into exact simulations for therapies" (28 November 2026). This plan is the first, deliberately small step: one model of one white spot, built to compare two explanations of why the spot stays white, and to say what each explanation predicts for a cell transplant.

**What the model is for.** IGH papers agree that a spot has fewer pigment cells (melanocytes) than the skin around it. They disagree, or are silent, on why. Two explanations are on the table in the saved sources (section 4): the melanocytes wear out on their own, or the deeper skin layer (the dermis) wears them out. Those two explanations make different predictions about things that can be measured: how the edge of a spot looks, whether a spot grows, whether transplanted melanocytes keep their colour after six months, and which tissue markers should differ between spot and surrounding skin. The model's job is to make those predictions explicit and numerical, so that the cheapest measurement that tells the two apart can be named.

**What the model can claim.**

- "If explanation A is true and these assumptions hold, the model predicts X; under explanation B it predicts Y."
- "Prediction X holds across this range of the unmeasured inputs; prediction Z flips sign inside it, so Z is not a useful test."
- "These are the inputs nobody has measured that the answer depends on most."

**What the model cannot claim.**

- That either explanation is true. A model built on its own assumptions can only show what follows from them.
- That any treatment works, or how well. Output is a ranked list of testable hypotheses, never evidence for the ledger. Nothing it produces enters `data/evidence.csv`.
- Anything about gene therapy or gene editing. Those are out of scope by design (section 2.4).
- Anything numerical about a real person's spot. Every unmeasured input is labelled an assumption, and most inputs are unmeasured (section 3).

**Scope.** Cell behaviour inside and around a single 2 to 5 mm spot, and one intervention: adding melanocytes (cell transplantation, the only direction in `content/frontier-scan.md` with an IGH precedent and long follow-up elsewhere). Every model input is traced to a quoted sentence in a source already saved in `papers/excerpts/` with its PMID, or labelled `ASSUMPTION`. No new literature search was run for this plan.

## 2. Entities and rules

### 2.1 The space

A square patch of skin seen from above, about 8 mm across, with one spot of 2 to 5 mm at its centre ("small 2- to 5-mm achromic or hypopigmented macules", PMID 3805391). Two stacked layers on the same grid:

- **Basal layer of the epidermis**, where melanocytes sit and hand pigment to the skin cells above them.
- **Superficial dermis** directly beneath, where fibroblasts sit.

Grid spacing, the number of keratinocytes each melanocyte supplies, and the layer thicknesses are `ASSUMPTION` (no saved source gives a number; see section 3). Time steps are days, run to at least 2 years so the six-month test can be read off after any simulated final treatment.

### 2.2 Entities and their states

| Entity | States | Where the states come from |
|---|---|---|
| Melanocyte (M) | active, hypoactive (alive, little or no pigment made), senescent, gone | "Depigmentation in IGH seems to occur in two stages, loss of melanogenic activity in certain malanocytes and elimination of inactive melanocytes" (PMID 7377803; spelling as printed). Senescent state: "expression of p16, p21, and hp1 was significantly higher in lesional skin of IGH patient as compared to healthy controls" (PMID 29516488) |
| Keratinocyte column (K) | holds a melanin amount, renewed over time | The pigment seen at the surface is carried by keratinocytes. The renewal time is `ASSUMPTION` (no saved number) |
| Fibroblast (F) | normal, senescent | Title only: "Role of senescent fibroblasts in the development of idiopathic guttate hypomelanosis" (PMID 31823346). The saved copy has no abstract |
| Dermal signal field (D) | a concentration on the grid, made by senescent fibroblasts, spread by diffusion, removed by decay | `ASSUMPTION`. The nearest saved evidence is in vitiligo, not IGH: "higher expression of DKK1 in the dermis induced senescence in melanocytes that may lead to hypopigmentation" (PMID 29442138) |
| Melanocyte reservoir (R) | a source of new melanocytes at fixed points (hair follicles), on or off | Mouse only: micro-injury "induces the hair follicle melanocyte stem cells to migrate upwards to the interfollicular epidermis, activating and giving rise to melanocytes to repopulate the vitiligo lesion" (PMID 35044224). For IGH: `ASSUMPTION` |

### 2.3 Rules

Each rule is applied every time step. "Sourced" means a saved sentence supports the rule's *direction*; in every case the *rate* is an assumption (section 3).

| # | Rule | Status and source |
|---|---|---|
| R1 | An active melanocyte becomes hypoactive at an intrinsic rate `k_int`, which rises with cell age | Direction sourced: "The basic defect in IGH melanocytes may reflect the aging process" (PMID 7377803); "The evidence indicates an age-related somatic mutation of melanocytes" (PMID 6183861). Rate: `ASSUMPTION` |
| R2 | A hypoactive melanocyte becomes senescent or is eliminated | Sourced: the two-stage quote under 2.2 (PMID 7377803) |
| R3 | A melanocyte that fails to hand over pigment accumulates it, and accumulation raises its chance of senescence | Sourced as a hypothesis by the authors: "Accumulation of melanin can lead to the senescence in the melanocytes of IGH patients" (PMID 29516488). Transfer defect seen directly: "In some areas, there was a reduced uptake of melanosomes by the keratinocytes" (PMID 25088925). In UV-aged cells, not IGH: "senescent melanocytes are characterized by melanosome transport dysfunction resulting in melanin accumulation" (PMID 37554281, full text saved as `pmc_37554281.txt`) |
| R4 | The dermal signal D raises a melanocyte's rate of senescence and death, scaled by a coupling `k_derm` | Direction: vitiligo, DKK1 "induced senescence in the treated melanocytes" (PMID 29442138). IGH: title only (PMID 31823346), and "Our results suggest an interaction between melanocytes and the subjacent dermis in IGH" (PMID 35114009). Strength: `ASSUMPTION` |
| R5 | A senescent fibroblast produces D at rate `p_D`; D diffuses with length scale `λ_D` and decays | `ASSUMPTION` entirely. Only the existence of dermal change is sourced: "We found superficial dermal fibrosis in 90% (18/20) of our IGH cases" (PMID 35114009). One study disagrees: "In the dermis, fibroblasts were structurally normal" (PMID 25088925) |
| R6 | A senescent melanocyte slows its neighbours | Sourced outside IGH, in aged human skin: "senescent melanocyte SASP induces telomere dysfunction in paracrine manner and limits proliferation of surrounding cells" (PMID 31633821). Range and strength: `ASSUMPTION`. Optional switch, off in the base runs |
| R7 | A gap left by a lost melanocyte can be filled by a neighbour dividing, or from the reservoir if it is on | `ASSUMPTION`. Melanocyte division rate in adult skin: no saved number |
| R8 | Each keratinocyte column takes pigment from its supplying melanocyte at rate `k_tr` and loses pigment as the column renews | `ASSUMPTION` for both rates. Transfer defect direction: R3 sources |
| R9 | Transplant event: at a chosen day, add a number of healthy melanocytes per mm² to the spot, with age zero and a stated survival fraction | Visible repigmentation timing sourced: "Repigmentation was visible within 7 to 14 days" (PMID 3908515). Survival fraction and how many cells a graft delivers: `ASSUMPTION` |
| R10 | The model never sets the melanocyte count to exactly zero by rule; zero can only arise from the dynamics | Sourced, with a conflict to keep visible: "In no case were melanocytes completely absent, excluding vitiligo" (PMID 6183861) versus "Histochemical studies confirmed the absence of dopa-positive cells in the areas of leukoderma prior to grafting" (PMID 3908515, a mixed leukoderma series) |

### 2.4 What is deliberately left out

- **Genes, mutations and gene therapy or editing.** The model has no genome. "age-related somatic mutation" (PMID 6183861) enters only as a rate in R1. Simulating a gene therapy would need a target gene established in IGH, and the saved sources name none beyond an early drop in one autophagy protein ("ATG7 downregulation emerged as the earliest molecular alteration", PMID 41453137), which the model can carry as a marker (section 5) but not as an intervention.
- **The immune system.** No immune attack is established in IGH (`content/frontier-scan.md`). One saved series reports "One-third of patients had a sparse perivascular lymphocytic infiltrate, whereas the rest had no significant dermal inflammation" (PMID 25484386). Left out of the base model; an open question if Ben wants it.
- **Drugs, lasers, peels, 5-FU.** Only transplantation in the first build. A wounding stimulus that switches the reservoir on is an optional extension (open question 3).
- **Whole-body (systemic) factors.** See section 4.3: one saved result points that way, and the first build cannot represent it.

## 3. Parameters: what has a published value and what does not

Status words: `QUOTED` (a saved source gives the number; quote and PMID in the table), `NOT IN SAVED SOURCES` (the quantity may well be measured somewhere, but no source saved in this project gives it; a logged search could look, and this plan did not run one), `NOT MEASURED IN IGH` (a saved source gives a value in another condition or species only). Every value that is not `QUOTED` enters the model as an `ASSUMPTION` with a range, and is swept in section 7.

### 3.1 Values a saved source gives

| Parameter | Value | Quote | PMID | Caveat |
|---|---|---|---|---|
| Spot diameter | 2 to 5 mm | "small 2- to 5-mm achromic or hypopigmented macules" | 3805391 | clinical description, not a measured distribution |
| Melanocyte density, spot vs surrounding skin | 55.25 vs 220 per mm² | "reduction of the number of melanocytes in the depigmented macula as compared with the surrounding area (55.25 +/- 18.00 mm2 vs 220 +/- 28.28 mm2" | 2508572 | dopa staining, 1989; patient count not in abstract. [Inferred ratio: about 0.25] |
| Melanocyte density after the spot was grafted onto a mouse | 388.75 per mm² | "The number of melanocytes increased significantly (388.75 +/- 213 mm2)" | 2508572 | grafted IGH skin on nude mice; timing of the count not stated in the abstract for IGH |
| Time to repigmentation, IGH skin on mouse | 20 days | "Twenty days after skin transplantation, repigmentation of the area was observed" | 2508572 | mouse host |
| Time to visible repigmentation after melanocyte grafting | 7 to 14 days | "Repigmentation was visible within 7 to 14 days" | 3908515 | mixed leukodermas including IGH; no later follow-up in the abstract |
| Share of spots with superficial dermal fibrosis | 18 of 20 | "We found superficial dermal fibrosis in 90% (18/20) of our IGH cases" | 35114009 | counted per patient's biopsy |
| Share with epidermal atrophy | 5 of 47 | "epidermal atrophy was present in only five cases (10.6%)" | 20465639 | |
| Share with patchy retained pigment ("skip areas") | almost 80% | "small foci of retained melanin in the basal layer (skip areas) alternating with larger areas of melanin loss were present in almost 80% of cases" | 25484386 | 55 biopsies; a spatial pattern the model must be able to reproduce (section 7) |
| Senescence markers, spot vs control | higher, no size given | "expression of p16, p21, and hp1 was significantly higher in lesional skin of IGH patient as compared to healthy controls" | 29516488 | six patients, six controls; direction only |

### 3.2 Values the model needs that no saved source gives

| Parameter | Symbol | Status | Starting range for the sweep (all `ASSUMPTION`) |
|---|---|---|---|
| Intrinsic rate at which an active melanocyte goes hypoactive | `k_int` | NOT IN SAVED SOURCES | chosen so that spot formation takes years, not weeks (to be set in the spec) |
| How that rate rises with cell age | `a_int` | NOT IN SAVED SOURCES | flat to steep |
| Hypoactive to senescent, and senescent to gone | `k_sen`, `k_loss` | NOT IN SAVED SOURCES | months to years |
| Melanocyte division rate in adult skin | `k_div` | NOT IN SAVED SOURCES | near zero to modest |
| Melanin transfer rate to keratinocytes | `k_tr` | NOT IN SAVED SOURCES | normalised to 1 in healthy skin |
| Keratinocyte column renewal time | `T_K` | NOT IN SAVED SOURCES | weeks |
| Keratinocytes supplied per melanocyte | `n_K` | NOT IN SAVED SOURCES (the term "epidermal melanin unit" appears in PMID 29516488 with no number) | fixed; only enters the rendering |
| Share of dermal fibroblasts senescent under a spot vs outside | `f_sen` | NOT IN SAVED SOURCES (only title-level for IGH, PMID 31823346) | 0 to high |
| Dermal signal production, diffusion length, decay | `p_D`, `λ_D`, `μ_D` | NOT MEASURED IN IGH (DKK1 effect on melanocytes reported in vitiligo, PMID 29442138, with no rate) | `λ_D` from 0.05 mm to 2 mm: this one decides how sharp the spot edge is (section 4) |
| Coupling of dermal signal to melanocyte senescence | `k_derm` | NOT MEASURED IN IGH | 0 (H1) to dominant (H2) |
| Paracrine reach of a senescent melanocyte | `λ_M` | NOT MEASURED IN IGH (direction only, PMID 31633821) | off in base runs |
| Reservoir density and output | `ρ_R`, `k_R` | NOT MEASURED IN IGH (mouse, PMID 35044224) | off, or follicles at a set spacing |
| Transplanted cells delivered per mm², and share surviving | `N_tx`, `s_tx` | NOT IN SAVED SOURCES | delivered: up to the surrounding density of 220 per mm²; survival 10% to 90% |
| Rate at which spots grow in diameter | — | NOT IN SAVED SOURCES | none: this is a model *output*, and the plan treats its absence from the literature as a gap (section 5) |
| Melanin-to-lightness mapping | — | NOT IN SAVED SOURCES | monotone, saturating; chosen so the spot reads about +12 L* above skin, the contrast the existing drift simulation uses (`content/measurement-tool-plan.md` 2.1 item 5) |

[Inference: of roughly 20 inputs, about 9 facts have a quoted value and none of them is a *rate*. The model is therefore a tool for comparing shapes of behaviour, not for predicting dates. Section 8 returns to this.]

## 4. The two competing explanations and the predictions that separate them

### 4.1 The explanations

**H1, "the pigment cells wear out on their own."** Melanocytes in the spot run down by their own clock: ageing, accumulated damage, pigment they cannot hand over. The dermis is a bystander. In the model: `k_derm = 0`, R1 to R3 do the work.
Saved support: "The evidence indicates an age-related somatic mutation of melanocytes" (PMID 6183861); "The basic defect in IGH melanocytes may reflect the aging process" (PMID 7377803); "Accumulation of melanin can lead to the senescence in the melanocytes of IGH patients" (PMID 29516488); "ATG7 downregulation emerged as the earliest molecular alteration and was consistently found in senescent melanocytes and idiopathic guttate hypomelanosis skin" (PMID 41453137).

**H2, "the deeper layer wears them out."** A patch of senescent or scarred dermis under the spot sends a signal that pushes the melanocytes above it into senescence and loss. In the model: `k_int` at its healthy-skin value, R4 and R5 do the work.
Saved support: "Our results suggest an interaction between melanocytes and the subjacent dermis in IGH" (PMID 35114009), with "superficial dermal fibrosis in 90% (18/20)" in the same paper; the title of PMID 31823346 (no abstract saved); and, in vitiligo, "higher expression of DKK1 in the dermis induced senescence in melanocytes that may lead to hypopigmentation" (PMID 29442138).

The model also runs **mixtures** (both couplings on), because nothing in the sources says the two are exclusive.

[Note on a lead: the Gemini report saved on another branch (`content/external/gemini-repair-landscape-2026-11-27.md`, PR 17) quotes text it attributes to the full paper of PMID 31823346, including a sentence that medium from senescent fibroblasts caused melanocyte death and senescence (paraphrased here, not quoted, because it is not in a saved source). That would be the strongest single support for H2. The project has only the title saved, so under CLAUDE.md rule 9 those sentences are leads, and this plan does not use them. Getting that full text is open question 4.]

### 4.2 What the facts already measured can and cannot tell apart

[Inference: the two findings every IGH paper agrees on, fewer melanocytes in the spot (PMIDs 9765023, 2508572) and raised senescence markers in lesional skin (PMID 29516488), are predicted by **both** explanations. They cannot decide between them. The predictions below are the ones that differ.]

### 4.3 Predictions that differ

| # | What to look at | H1 (cells wear out alone) | H2 (dermis wears them out) | Already known? |
|---|---|---|---|---|
| P1 | **Edge sharpness**: how wide the band is over which pigment goes from spot to normal | about one to a few melanocyte spacings, the same for every spot | about the signal's reach `λ_D`; wider edges on larger dermal patches | Clinically "sharply demarcated" (PMID 6183861). Under H2 that forces `λ_D` to be short. Never measured as a width in any saved source |
| P2 | **Growth of an untreated spot** over months | no spread from the edge; nearby skin turns white independently, in scattered points | the spot follows its dermal patch; spreads outward only if the patch spreads | No growth rate in any saved source |
| P3 | **Pattern inside the spot** | random loss gives scattered surviving cells, consistent with "skip areas" | loss is strongest where the signal is strongest (spot centre, or over fibroblast clusters); surviving pigment sits at the rim or away from clusters | "skip areas" in almost 80% of biopsies (PMID 25484386); where in the spot they sit is not stated in the abstract |
| P4 | **Transplant of healthy melanocytes, epidermal cells only** | cells persist; colour match holds well past six months, until the new cells' own clock runs (years) | cells meet the same dermal signal and fade; colour returns towards white on a time scale set by `k_derm` | Repigmentation "within 7 to 14 days" with no later follow-up (PMID 3908515) |
| P5 | **Transplant that brings donor dermis with it** (a full-thickness minigraft) versus epidermal cells alone | both hold about equally | the graft with its own healthy dermis holds; epidermal cells alone fade | One saved result, hard to read: "Minigrafts of normal skin implanted in idiopathic guttate hypomelanosis lesions did not modify the achromic defects" (PMID 3805391) |
| P6 | **Tissue markers, spot versus surrounding skin** | p16 raised in melanocytes; dermal p16-positive cells about equal inside and outside; ATG7 low in melanocytes | dermal p16-positive cells clearly higher under the spot than outside; the dermal signal (DKK1 is the saved candidate) higher under the spot; melanocyte loss graded with distance from senescent fibroblasts | Raised p16 in "lesional skin" (PMID 29516488) does not say which cell type; the dermal comparison is in PMID 31823346 (title only saved) |

[Inference: P4 is the prediction that matters most to the project's core question, because it is literally "does the colour match last six months after the final treatment" for the one treatment direction with long follow-up elsewhere. P1 and P2 matter most to Ben, because they can be read from photographs with the measurement tool, without a biopsy.]

### 4.4 A result neither explanation handles: the mouse graft

"Split-thickness skin grafts obtained from patients with vitiligo, acquired hypomelanosis guttata, and tyrosinase-negative albinism were grafted onto nude mice", and the IGH spot repigmented: "Twenty days after skin transplantation, repigmentation of the area was observed" (PMID 2508572). The authors conclude "systemic factors may play a role".

[Inference: if a split-thickness graft carries the superficial dermis with it, as such grafts usually do, then moving the spot moved its dermis too, and it still recovered. That fits neither pure H1 (exhausted cells should not recover) nor pure local H2 (the bad dermis came along). It fits a third explanation, **H3: something from the person's body as a whole**, which this first model cannot represent. Two other readings exist: the graft may have carried little dermis, or the new melanocytes may have come from somewhere other than the spot. The abstract does not settle either.] The model's validation (section 7) treats this result as a target that any accepted parameter set must at least not contradict; open question 1 asks Ben whether H3 should be added.

## 5. How model output maps to things that can be measured

The model keeps cells and melanin internally, but every output it reports is something a camera or a laboratory partner could actually measure. Nothing is reported only as an internal variable.

### 5.1 Readouts from photographs (the measurement tool)

The model renders its melanin map to a synthetic linear-RGB image with the same scene conventions as `experiments/drift_sim.py` (20 px/mm, blur 0.1 mm, ring gap 1.0 mm, ring width 1.5 mm) and then measures it with the quantities defined in `content/measurement-tool-plan.md` section 2.1. That way a model prediction and a real measurement are the same number computed the same way.

| Model output | Measurement-plan quantity | Separates |
|---|---|---|
| Lightness contrast of the spot over time | ΔL* of the fixed inner disc minus the ring, and the residual contrast ratio ρ(t) (plan 2.1 items 5 and 7) | P4 (does a transplant's colour hold at six months after the final treatment) |
| Spot area over time | A(t) by segmentation (plan 2.1 item 8) | P2 (growth of an untreated spot) |
| Edge width | **new quantity**: the distance over which a radial ΔL* profile goes from 10% to 90% of the spot's contrast. Needs adding to the measurement plan, and needs a test of what the camera's blur does to it | P1 |
| Pattern inside the spot | **new quantity**: the share of the inner disc that is darker than its own median by more than a threshold, as a crude "skip area" score | P3 |

Whether a measured change is real is decided by the measurement plan's smallest detectable change (SDC, plan 2.2), not by the model. If a predicted difference between H1 and H2 is smaller than the SDC the tool reaches in phantoms, that prediction is reported as **not testable with this tool**, however clean it looks in the model.

### 5.2 Readouts a laboratory partner could measure

These need biopsies, so they belong to a professional study, not to Ben (CLAUDE.md, Module 5 framing: "a more full study can be performed by professionals"). They are listed so a proposal can name them.

| Model output | Tissue measurement | Saved source showing it has been done in IGH |
|---|---|---|
| Melanocytes per mm², spot vs ring | melanocyte count by dopa staining or melanocyte markers | dopa counts (PMID 2508572); "MART-1" and "NKI/beteb" staining (PMID 20465639) |
| Share of melanocytes senescent | p16, p21, hp1 | PMID 29516488 |
| Senescent fibroblasts under spot vs outside | p16-positive cells in the superficial dermis, by position | title only (PMID 31823346) |
| Dermal fibrosis | routine histology | PMID 35114009 |
| Early autophagy loss | ATG7 | PMID 41453137 |
| Candidate dermal signal | DKK1 in dermis | vitiligo only (PMID 29442138); no saved IGH measurement |
| Melanin retained in melanocytes vs handed over | Fontana-Masson, electron microscopy | PMIDs 25088925, 29516488 |

[Inference: the single most informative biopsy design for this model would sample the spot centre, the spot edge, and skin 2 mm outside it, in the same person, and stain for melanocytes and p16 in **both** layers. That gives P6 directly and the spatial gradient behind P1 and P3. This is a suggestion for a professional protocol, not something the project can do.]

### 5.3 Link to the study proposal

The study proposal (`content/study-proposal.md`, PR 6, open) already compares a treated spot with the same person's untreated spot, six months after the final session. [Inference: under this plan its untreated spot is also the measurement for P2, and its treated spot is P4 if the treatment is a cell transplant. Adding edge width (5.1) to its outcome list would cost nothing extra at capture.]

## 6. Build sequence, tests first

Same pattern as the drift simulation: a written contract, tests from the contract by the `test-author` role before any code, then a builder who may not edit the tests (`git diff --exit-code <tests commit> -- experiments/tests` stays clean). One unit per thread. Nothing in this section starts until Ben has read the plan (open question 6).

| Step | Role | Input | Output path | Done when |
|---|---|---|---|---|
| **M1** Parameter register | main session | sections 2 and 3 of this plan | `data/spot_model_params.csv`: one row per parameter with `name, value_or_range, unit, status (QUOTED / ASSUMPTION), pmid, quote, source_file` | every `QUOTED` row's quote is found word for word in its saved file by a checker (M2); every other row says `ASSUMPTION` and gives a range |
| **M2** Register checker | test-author, then builder | M1 file format | `tests/test_spot_params.py`, `tools/spot_params_check.py` | a row marked `QUOTED` with a quote not in its source fails; a row with a blank status fails; the model refuses to load a parameter that is not in the register |
| **M3** Model contract and tests, well-mixed version (no space): one spot as a set of counts over time | test-author | sections 2.2, 2.3, 4.1 | `experiments/tests/test_spot_model.py` | tests committed and failing (no code yet); each tolerance stated with its reason |
| **M4** Build the well-mixed model | builder | M3 tests | `experiments/spot_model.py` | M3 tests pass unchanged |
| **M5** Contract and tests, spatial version (grid, diffusion, edge, rendering, measurement) | test-author | sections 2, 4.3, 5.1 | `experiments/tests/test_spot_model_grid.py` | as M3 |
| **M6** Build the spatial model | builder | M5 tests | `experiments/spot_model_grid.py` | M5 tests pass unchanged |
| **M7** Validation and sensitivity runs | builder | M4, M6, section 7 | `data/spot_model_validation.csv`, `data/spot_model_sweep.csv` | reproducible from the stated seed; run time stated |
| **M8** Write-up | main session | M7 CSVs | `content/spot-model-results.md` | every number cited by CSV line; output framed as ranked hypotheses (section 8 wording rules) |

Tests the contract must include, at minimum (the test-author decides the rest and states tolerances):

- With every loss rate set to zero, melanocyte counts never change.
- With `k_derm = 0`, outputs do not depend on the fibroblast state at all (H1 is truly dermis-free); with `k_int` at baseline, an absent dermal patch gives no spot (H2 needs its patch).
- Counts never go negative; no rule sets melanocytes to exactly zero (R10).
- Same seed, same output, bit for bit.
- A transplant into skin with no loss pressure keeps its cells indefinitely.
- Edge width under H2 grows with `λ_D` and under H1 does not.
- Rendering: a melanin map equal to the surrounding skin gives ΔL* within noise of zero, measured with the measurement plan's ring geometry.
- A zero-contrast baseline is refused, not divided by (the drift simulation's rule).

[Recommendation: build the well-mixed version first (M3, M4). It answers P4 and the marker predictions (P6) with a few hundred lines and very few parameters, and shows quickly whether the two hypotheses are distinguishable at all. The grid version is only worth building if they are, because P1 to P3 are spatial.]

## 7. Validation and sensitivity analysis

### 7.1 Validation targets

There is no IGH dataset to fit (no public IGH dataset in GEO, BioImage Archive, Zenodo or Figshare, `STATUS.md`). So validation is by **pattern**: a parameter set is accepted only if the model reproduces, at the same time, every qualitative fact below that the saved sources state. A set that reproduces some and contradicts others is rejected.

| Target | Quoted fact | PMID | Pass rule (to be fixed in the M3/M5 contract) |
|---|---|---|---|
| V1 | spot density about a quarter of surrounding: "55.25 +/- 18.00 mm2 vs 220 +/- 28.28 mm2" | 2508572 | steady-state spot/ring density ratio inside the quoted spread [roughly 0.15 to 0.4, inferred from the means and SDs] |
| V2 | "In no case were melanocytes completely absent" | 6183861 | spot density stays above zero at all times in the base runs |
| V3 | two-stage loss: "loss of melanogenic activity in certain malanocytes and elimination of inactive melanocytes" | 7377803 | hypoactive cells appear before cells are lost |
| V4 | "sharply demarcated hypopigmented macules" | 6183861 | edge width (5.1) at most a stated fraction of the spot radius [the fraction is an assumption to be set in the contract] |
| V5 | size: "2- to 5-mm" | 3805391 | spots form in that range without the size being imposed directly |
| V6 | skip areas "in almost 80% of cases" | 25484386 | the grid model shows patchy retained pigment in most simulated spots |
| V7 | short-term graft result: "Repigmentation was visible within 7 to 14 days" | 3908515 | a simulated transplant reaches visible contrast reduction within weeks |
| V8 | mouse graft recovers (section 4.4) | 2508572 | flagged, not scored: no base model can represent a new host. Reported as a known misfit |

Formation time (how many years a spot takes to appear) has no quoted value, so it is not a target. The age pattern ("The prevalence of IGH in the group of patients aged ≥40 years was 87%", PMID 21699514) says spots are common by middle age, which only rules out parameter sets that form spots in weeks.

### 7.2 Sensitivity analysis

1. **One at a time.** Each `ASSUMPTION` parameter moved across its range with the rest fixed; record which predictions (P1 to P6) change size or sign.
2. **Global sweep.** A few thousand parameter sets drawn across all assumption ranges at once (Latin hypercube, fixed seed), for H1, H2 and mixtures. Keep only sets that pass V1 to V7.
3. **For each prediction, report** the share of accepted sets in which H1 and H2 differ in the same direction by more than the measurement tool's SDC. A prediction is called **robust** if that share is at least 90%, **fragile** if it flips sign inside the accepted region, and **untestable** if the difference is below the SDC in most sets.
4. **Rank the unmeasured inputs** by how much each one moves the robust predictions. The top of that list is the model's most useful output for a professional study: it names what should be measured first.
5. **Identifiability check.** If H1 and H2 parameter sets pass V1 to V7 equally well and give the same P1 to P6, the result is "the current evidence cannot tell them apart, and neither can this model". That is a legitimate and likely outcome, and the write-up must say it plainly.

## 8. Risks of over-reading the output

- **Assumptions dominate.** None of the quoted values is a rate (section 3). Any time in the output ("fades after N months") is a consequence of an assumed rate, and must be written as "under assumed rates in range X".
- **A model can be tuned to anything.** With about a dozen free rates, both hypotheses will probably fit the eight validation targets. Fitting is not support. Only predictions that stay robust across the accepted region (7.2) are reported as findings of the model, and even those are hypotheses.
- **Borrowed biology.** Several rules rest on vitiligo (PMID 29442138), mouse (PMID 35044224) or cultured-cell (PMIDs 37554281, 31633821) evidence. Vitiligo is an immune disease and IGH is not known to be. Each such rule is marked in the register, and the write-up lists which outputs depend on borrowed rules.
- **Title-only and secondhand sources.** H2's IGH-specific support rests partly on a title (PMID 31823346) and on quotes in an external chatbot report that the project has not verified. Until the full text is saved, H2 is the weaker-sourced explanation, and the plan says so rather than letting the model's symmetry hide it.
- **The third explanation.** The mouse graft result (4.4) may mean both modelled explanations are wrong. A clean H1-versus-H2 answer could be an answer to the wrong question.
- **It is not a treatment simulator.** The transplant in the model is a number of cells appearing on a day. It has no donor site, no wound, no procedure, no safety. Output says nothing about whether anyone should have a transplant. Research, not medical advice.
- **Wording rules for the write-up (M8).** Never "the model shows that X works" or "X lasts N months". Always "under H1 and the stated assumptions, the model predicts...; this would be tested by...". No model number goes into `data/evidence.csv`, the evidence summary, or the home page. Inferences in `[square brackets]` as elsewhere in the project.
- **Presentability pressure.** A cell simulation with moving pictures looks more authoritative than a table of abstracts, and is less so. Anything public from this module waits for Gate B, and the results page should lead with the limits.

## 9. Open questions for Ben

Each has a recommended answer, so work can go ahead on that answer if Ben prefers not to decide yet.

1. **Add a third explanation ("something from the whole body")?** The 1989 mouse graft result (4.4) fits neither modelled explanation. *Recommended:* not in the first build; keep it as a flagged misfit, and add it only if the first build shows H1 and H2 can be told apart.
2. **Start with the simple version?** A well-mixed model (counts over time, no space) before the grid model. *Recommended:* yes (section 6, M3 and M4). It answers the transplant question and the marker question quickly; the grid is only worth building if the simple one separates the hypotheses.
3. **Model only transplantation, or also a wounding stimulus?** Several ledger treatments (laser, phenol, 5-FU tattooing, cryotherapy) injure the skin, and one mouse paper shows injury calling up follicle pigment stem cells (PMID 35044224). Adding "wounding switches the reservoir on for a while" would let the model ask whether those treatments' colour should last six months under each explanation. *Recommended:* transplant only in the first build, wounding as the first extension, because it ties the model to the ledger's actual treatments.
4. **Can you get the full text of PMID 31823346** (Br J Dermatol 2020;182(6):1481-1482, doi:10.1111/bjd.18801, senescent fibroblasts in IGH)? It is the most load-bearing missing source for H2. Also useful: PMID 36394380 (melanocytes "disappear and are senescent", J Eur Acad Dermatol Venereol 2023). Both are on the paywall-style path: library, author, or pay per article. *Recommended:* yes if it costs little; the model can be built without them, but H2 stays the weaker-sourced side until then.
5. **Add edge width and a "skip area" score to the measurement tool plan** (section 5.1)? They are the two predictions Ben could check from photographs without a biopsy. *Recommended:* yes, as an addition to the placement simulation tests (measurement plan task T2), so blur and misplacement effects on edge width are known before anyone reads meaning into it.
6. **Go ahead with M1 to M4** (parameter register, its checker, tests, simple model) after reading this? *Recommended:* yes. Each is one thread and one pull request for you to read, nothing public.

## Sources used

All saved in the project files excerpts folder as `pmid_<id>.txt` (or `pmc_<id>.txt` where noted). No new search was run for this plan. *Title only* means the saved record has no abstract.

| PMID | What it is | Condition | Used for |
|---|---|---|---|
| 2508572 | IGH and vitiligo skin grafted onto nude mice, 1989 | IGH | melanocyte densities; repigmentation timing; the misfit in 4.4 |
| 3805391 | pathogenesis study, 15 patients and 15 controls | IGH | spot size; histology; minigraft result (P5) |
| 3908515 | blister-roof melanocyte grafting, 1985 | IGH and other leukodermas | transplant timing; absence of dopa-positive cells |
| 6183861 | clinical and microscopic study of 20 cases | IGH | sharp edge; never completely absent; somatic-mutation hypothesis |
| 7377803 | ultrastructure, 3 patients | IGH | two-stage loss; ageing |
| 9765023 | 9 lesions, KIT and differentiation markers | IGH | absolute decrease in melanocyte number |
| 20465639 | 47 patients, histology | IGH | atrophy share; MART-1 staining |
| 21699514 | 1,174 subjects examined | IGH | prevalence with age |
| 25088925 | electron microscopy, 4 patients | IGH | transfer defect; normal fibroblasts |
| 25484386 | 55 biopsies (full text also saved as `pmc_25484386.txt`) | IGH | skip areas; sparse inflammation |
| 29516488 | 6 patients, 6 controls, senescence markers | IGH | p16, p21, hp1; melanin accumulation |
| 31823346 | senescent fibroblasts | IGH | title only |
| 35114009 | 20 patients, histology and electron microscopy | IGH | dermal fibrosis; melanocyte–dermis interaction |
| 36394380 | melanocytes disappear and are senescent | IGH | title only (open question 4) |
| 41453137 | ATG7 in UV-senescent melanocytes, checked in IGH skin | cells, mice, IGH skin | earliest marker |
| 29442138 | DKK1 and melanocyte senescence | vitiligo, cells | candidate dermal signal |
| 31633821 | senescent melanocytes in skin ageing | human skin, 3D model | paracrine rule R6 |
| 37554281 | senescent melanocytes, transport defect (full text `pmc_37554281.txt`) | cells, aged skin | melanin accumulation rule R3 |
| 35044224 | micro-injury and follicle stem cells | vitiligo model mice | reservoir rule |
